"""Grounded AI conversation engine — Prompt 7 Step 3.

``generate_ai_response`` is the latency-critical task (target: end-to-end under
8 seconds). For one inbound message it:

1. loads the lead and verifies ``manual_mode`` is False (a human owns it otherwise),
2. loads the last 20 turns scoped to this lead only,
3. assembles the tenant context from cache and decrypts the tenant's Gemini key,
4. detects intent from the last 3 turns and decides the next conversation state,
5. builds the grounded, stage-aware system prompt and generates the reply
   (temperature 0.3; a BOOKING_OFFERED turn is rendered by booking_service at 0.1),
6. records the state transition, persists the assistant message, cancels any
   pending outreach (the lead responded),
7. delivers the reply on the lead's channel, emits ``ai_response_sent`` +
   ``new_message`` WebSocket events, and triggers the handoff flow if escalated.

Each step is timed; if the whole turn exceeds 6 seconds a structured warning is
logged (shipped to Axiom) so slow turns are visible before they breach the 8s SLA.
"""

import asyncio
import logging
import time
import uuid
from typing import Any

from app.core.ai import FLASH_LITE_MODEL
from app.core.exceptions import (
    AIGenerationError,
    CredentialVerificationError,
    ExternalAPIError,
    ProfileIncompleteError,
)
from app.db.base import with_tenant_scope
from app.db.models import ConversationState
from app.modules.conversations.delivery import deliver_message, delivery_service_for
from app.worker.celery_app import celery_app
from app.worker.db import worker_session

logger = logging.getLogger(__name__)

SLOW_TURN_THRESHOLD_MS = 6000
HISTORY_LIMIT = 20
TRANSCRIPT_CHAR_CAP = 4000
REPLY_MAX_TOKENS = 500


@celery_app.task(name="messages.generate_ai_response", queue="ai_conversations", ignore_result=True)
def generate_ai_response(payload: dict[str, str]) -> None:
    """Generate, persist, and deliver one grounded AI reply for a lead."""
    asyncio.run(_run(payload))


async def _run(payload: dict[str, str]) -> None:  # noqa: PLR0915 — linear pipeline reads best whole
    tenant_id = uuid.UUID(payload["tenant_id"])
    lead_id = uuid.UUID(payload["lead_id"])
    timings: dict[str, int] = {}
    started = time.perf_counter()

    def mark(step: str, since: float) -> float:
        now = time.perf_counter()
        timings[step] = int((now - since) * 1000)
        return now

    async with worker_session() as session:
        # --- Phase A: load everything the AI calls need, then release the txn ---
        step = time.perf_counter()
        async with with_tenant_scope(session, tenant_id):
            lead = await _load_lead(session, lead_id)
            if lead is None:
                logger.warning("ai response: lead not found", extra={"lead_id": str(lead_id)})
                return
            if lead["manual_mode"]:
                logger.info("ai response skipped: manual mode", extra={"lead_id": str(lead_id)})
                return
            current_state = ConversationState(lead["conversation_state"])
            history = await _load_history(session, lead_id)
            gemini = await _decrypt_or_none(session, tenant_id, "gemini")
            delivery_service = delivery_service_for(lead["platform"])
            delivery_cred = (
                await _decrypt_or_none(session, tenant_id, delivery_service)
                if delivery_service
                else None
            )
            await session.commit()
        step = mark("load", step)

        if gemini is None:
            logger.error("ai response: no gemini credential", extra={"tenant_id": str(tenant_id)})
            _notify_owner(tenant_id, lead_id, "ai_unavailable")
            return
        api_key = str(gemini.fields["api_key"])

        try:
            context = await assemble_context(session, tenant_id)
        except ProfileIncompleteError:
            logger.warning("ai response: profile incomplete", extra={"tenant_id": str(tenant_id)})
            _notify_owner(tenant_id, lead_id, "profile_incomplete")
            return
        step = mark("context", step)

        # --- Phase B: intent -> transition decision -> grounded reply (no DB) ---
        from app.modules.ai.intent_detection_service import detect_intent
        from app.modules.conversations.state_machine import determine_transition

        last_three = [{"role": role, "content": content} for role, content in history[-3:]]
        signals = await detect_intent(last_three, tenant_id, api_key=api_key)
        step = mark("intent", step)

        new_state = determine_transition(current_state, signals)
        target_state = new_state or current_state

        try:
            reply_text, reply_tokens = await _generate_reply(
                context=context,
                target_state=target_state,
                transcript=_transcript(history),
                tenant_id=tenant_id,
                api_key=api_key,
            )
        except (AIGenerationError, ExternalAPIError):
            logger.error("ai response generation failed", extra={"tenant_id": str(tenant_id)})
            _notify_owner(tenant_id, lead_id, "ai_generation_failed")
            return
        if not reply_text.strip():  # defence in depth — traced_ai_call already guards
            _notify_owner(tenant_id, lead_id, "ai_empty_reply")
            return
        step = mark("generate", step)

        # --- Phase C: persist transition + assistant message, cancel outreach ---
        from app.modules.conversations.outreach_service import cancel_outreach_sequence
        from app.modules.conversations.state_machine import record_transition

        async with with_tenant_scope(session, tenant_id):
            if new_state is not None:
                await record_transition(
                    session,
                    lead_id=lead_id,
                    tenant_id=tenant_id,
                    from_state=current_state,
                    to_state=new_state,
                    signals=signals,
                )
            await _save_assistant_message(session, tenant_id, lead_id, reply_text, reply_tokens)
            await cancel_outreach_sequence(session, tenant_id=tenant_id, lead_id=lead_id)
            await session.commit()
        step = mark("persist", step)

        # --- Phase D: deliver + realtime events (best-effort, outside the txn) ---
        delivered = await deliver_message(
            platform=lead["platform"],
            platform_id=lead["platform_id"],
            text=reply_text,
            credential=delivery_cred,
            lead_id=lead_id,
            tenant_id=tenant_id,
            last_inbound_at=lead["last_inbound_at"],
        )
        if not delivered:
            _notify_owner(tenant_id, lead_id, "delivery_failed")
        _emit_events(tenant_id, lead_id, target_state, reply_text)
        step = mark("deliver", step)

        # --- Phase E: handoff side effects ---
        if target_state is ConversationState.HANDED_OFF:
            from app.modules.conversations.booking_service import handle_handoff

            await handle_handoff(
                session, tenant_id=tenant_id, lead_id=lead_id, context=context, api_key=api_key
            )
            mark("handoff", step)

    total_ms = int((time.perf_counter() - started) * 1000)
    if total_ms > SLOW_TURN_THRESHOLD_MS:
        # Structured warning ships to Axiom — visible before it breaches the 8s SLA.
        logger.warning(
            "slow ai response turn",
            extra={
                "tenant_id": str(tenant_id),
                "lead_id": str(lead_id),
                "total_ms": total_ms,
                "step_ms": timings,
            },
        )
    else:
        logger.info(
            "ai response delivered",
            extra={"tenant_id": str(tenant_id), "lead_id": str(lead_id), "total_ms": total_ms},
        )


# ---------------------------------------------------------------------------
# DB helpers (raw SQL — run inside an active tenant scope)
# ---------------------------------------------------------------------------


async def _load_lead(session: Any, lead_id: uuid.UUID) -> dict[str, Any] | None:  # noqa: ANN401
    from sqlalchemy import text

    row = (
        await session.execute(
            text(
                "SELECT conversation_state, manual_mode, platform, platform_id, "
                "last_inbound_at, status FROM leads WHERE id = :id"
            ),
            {"id": lead_id},
        )
    ).first()
    if row is None:
        return None
    return {
        "conversation_state": str(row[0]),
        "manual_mode": bool(row[1]),
        "platform": str(row[2]),
        "platform_id": str(row[3]),
        "last_inbound_at": row[4],
        "status": str(row[5]),
    }


async def _load_history(session: Any, lead_id: uuid.UUID) -> list[tuple[str, str]]:  # noqa: ANN401
    from sqlalchemy import text

    rows = (
        await session.execute(
            text(
                "SELECT role, content FROM conversations "
                "WHERE lead_id = :lid AND role <> 'system' "
                "ORDER BY created_at ASC, id ASC"
            ),
            {"lid": lead_id},
        )
    ).all()
    return [(str(r[0]), str(r[1])) for r in rows][-HISTORY_LIMIT:]


async def _decrypt_or_none(session: Any, tenant_id: uuid.UUID, service: str) -> Any | None:  # noqa: ANN401
    """Fetch+decrypt a credential, or None if the tenant hasn't connected it."""
    from app.modules.credentials.service import get_decrypted_credential

    try:
        return await get_decrypted_credential(tenant_id, service, session)
    except CredentialVerificationError:
        return None


async def assemble_context(session: Any, tenant_id: uuid.UUID) -> Any:  # noqa: ANN401
    from app.modules.ai.context_service import assemble_tenant_context

    return await assemble_tenant_context(tenant_id, session)


async def _save_assistant_message(
    session: Any,  # noqa: ANN401
    tenant_id: uuid.UUID,
    lead_id: uuid.UUID,
    content: str,
    tokens: int,
) -> None:
    from sqlalchemy import text

    await session.execute(
        text(
            "INSERT INTO conversations (tenant_id, lead_id, role, content, tokens_used) "
            "VALUES (:tid, :lid, 'assistant', :content, :tokens)"
        ),
        {"tid": tenant_id, "lid": lead_id, "content": content, "tokens": tokens},
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def _transcript(history: list[tuple[str, str]]) -> str:
    lines = [
        f"{'Customer' if role in ('lead', 'user') else 'Assistant'}: {content}"
        for role, content in history
    ]
    transcript = "\n".join(lines)
    return transcript[-TRANSCRIPT_CHAR_CAP:] if transcript else "(The customer just reached out.)"


async def _generate_reply(
    *,
    context: Any,  # noqa: ANN401 — TenantAIContext, imported lazily to keep this module light
    target_state: ConversationState,
    transcript: str,
    tenant_id: uuid.UUID,
    api_key: str,
) -> tuple[str, int]:
    """Return (reply_text, output_tokens). BOOKING_OFFERED is rendered by
    booking_service at temperature 0.1 so the link and discount are exact."""
    if target_state is ConversationState.BOOKING_OFFERED:
        from app.modules.conversations.booking_service import build_booking_offer

        result = await build_booking_offer(
            context=context, transcript=transcript, tenant_id=tenant_id, api_key=api_key
        )
        return result.text.strip(), result.output_tokens

    from app.modules.ai.langfuse_client import traced_ai_call
    from app.modules.ai.system_prompt_builder import build_system_prompt

    system = build_system_prompt(context, target_state)
    user_message = (
        f"Conversation so far:\n{transcript}\n\n"
        f"Write {context.business_name}'s next reply to the customer as the Assistant. "
        "Reply with ONLY the message text — no labels, no quotes."
    )
    result = await traced_ai_call(
        api_key=api_key,
        system=system,
        user_message=user_message,
        model=FLASH_LITE_MODEL,
        call_type=f"conversation-{target_state.value}",
        tenant_id=tenant_id,
        temperature=0.3,
        max_tokens=REPLY_MAX_TOKENS,
    )
    return result.text.strip(), result.output_tokens


# ---------------------------------------------------------------------------
# Realtime
# ---------------------------------------------------------------------------


def _emit_events(
    tenant_id: uuid.UUID, lead_id: uuid.UUID, state: ConversationState, reply: str
) -> None:
    from app.modules.realtime.events import EventEmitter

    EventEmitter.emit_sync(
        tenant_id,
        "ai_response_sent",
        {"lead_id": str(lead_id), "state": state.value, "preview": reply[:140]},
    )
    EventEmitter.emit_sync(
        tenant_id,
        "new_message",
        {"lead_id": str(lead_id), "role": "assistant", "content": reply},
    )


def _notify_owner(tenant_id: uuid.UUID, lead_id: uuid.UUID, reason: str) -> None:
    from app.modules.realtime.events import EventEmitter

    logger.info("owner notification", extra={"tenant_id": str(tenant_id), "reason": reason})
    EventEmitter.emit_sync(tenant_id, "new_lead", {"reason": reason, "lead_id": str(lead_id)})
