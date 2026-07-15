"""Booking offer + handoff — Prompt 7 Step 6.

Two responsibilities:

- ``build_booking_offer`` renders the BOOKING_OFFERED message at temperature 0.1
  (very low, so the booking link and any discount are reproduced exactly). It
  always presents exactly two options: self-book now (with the profile's booking
  link + an AI-facilitated discount from the discount policy) and talk to the team.
  If the model drops the link, it's appended verbatim — the URL is never invented.

- ``handle_handoff`` runs the escalation side effects when a conversation reaches
  HANDED_OFF: flip ``manual_mode``, generate a lead summary, email the owner
  (Resend), raise an in-app ``ai_handoff`` notification, emit ``lead_handed_off``,
  and — if the owner has a notification WhatsApp number — send a summary via the
  platform's own WhatsApp channel.
"""

import logging
import uuid
from dataclasses import replace
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ai import FLASH_LITE_MODEL
from app.core.config import settings
from app.core.exceptions import ExternalAPIError
from app.db.base import with_tenant_scope
from app.db.models import ConversationState, NotificationType
from app.modules.ai.langfuse_client import AICallResult, traced_ai_call

logger = logging.getLogger(__name__)

_BOOKING_TEMPERATURE = 0.1
_BOOKING_MAX_TOKENS = 350
_SUMMARY_TEMPERATURE = 0.2
_SUMMARY_MAX_TOKENS = 250


async def build_booking_offer(
    *,
    context: Any,  # noqa: ANN401 — TenantAIContext
    transcript: str,
    tenant_id: uuid.UUID,
    api_key: str,
) -> AICallResult:
    """Render the two-option booking offer at temperature 0.1 (exact link/discount)."""
    from app.modules.ai.system_prompt_builder import build_system_prompt

    system = build_system_prompt(context, ConversationState.BOOKING_OFFERED)
    booking_url = context.booking_url
    if booking_url:
        option_one = (
            f"Option 1 — book instantly yourself using this EXACT link (copy it verbatim, "
            f"never alter it): {booking_url}. Mention any discount from the DISCOUNT POLICY "
            "that applies when booking now."
        )
    else:
        option_one = (
            "Option 1 — book with help: a self-booking link isn't available, so offer to have "
            "the team share booking details. Mention any discount from the DISCOUNT POLICY."
        )
    user_message = (
        f"Conversation so far:\n{transcript}\n\n"
        "Write the booking offer message. Present EXACTLY TWO clear options:\n"
        f"{option_one}\n"
        "Option 2 — talk to our team, who'll help you personally.\n"
        "Keep it warm and concise. Never invent a link, price, or discount not stated above. "
        "Reply with ONLY the message text."
    )
    result = await traced_ai_call(
        api_key=api_key,
        system=system,
        user_message=user_message,
        model=FLASH_LITE_MODEL,
        call_type="booking-offer",
        tenant_id=tenant_id,
        temperature=_BOOKING_TEMPERATURE,
        max_tokens=_BOOKING_MAX_TOKENS,
    )
    body = result.text.strip()
    # Guarantee the exact link is present — the low temperature makes this rare,
    # but a dropped link would break self-booking, so we append it verbatim.
    if booking_url and booking_url not in body:
        body = f"{body}\n\nBook here: {booking_url}"
    return replace(result, text=body)


async def handle_handoff(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    lead_id: uuid.UUID,
    context: Any,  # noqa: ANN401 — TenantAIContext
    api_key: str | None = None,
) -> None:
    """Run the HANDED_OFF side effects: manual mode, summary, email, notification,
    WebSocket event, and (optionally) an owner WhatsApp message."""
    # 1. Flip manual mode + gather lead/owner/transcript in one scoped read-write.
    async with with_tenant_scope(session, tenant_id):
        await session.execute(
            text("UPDATE leads SET manual_mode = true, updated_at = now() WHERE id = :id"),
            {"id": lead_id},
        )
        lead = await _load_lead(session, lead_id)
        owner = await _load_owner(session)
        transcript = await _load_transcript(session, lead_id)
        await session.commit()

    if lead is None:
        return
    lead_name = lead["name"] or "A new lead"

    # 2. Summarise for the owner (best-effort; falls back to the raw transcript tail).
    summary = await _generate_summary(context, transcript, tenant_id, api_key)
    action_url = f"{settings.dashboard_url}/leads/{lead_id}"

    # 3. In-app notification.
    if owner is not None:
        from app.modules.notifications.service import create_notification

        async with with_tenant_scope(session, tenant_id):
            await create_notification(
                session,
                tenant_id=tenant_id,
                user_id=owner["id"],
                notif_type=NotificationType.AI_HANDOFF,
                title=f"{lead_name} needs a human",
                body=summary,
                action_url=action_url,
            )
            await session.commit()

    # 4. Email the owner (Resend).
    if owner is not None and owner["email"]:
        from app.modules.notifications.email_service import LeadHandoffEmail, send_email

        try:
            await send_email(
                LeadHandoffEmail(
                    to=owner["email"],
                    business_name=context.business_name,
                    lead_name=lead_name,
                    lead_summary=summary,
                    conversation_url=action_url,
                )
            )
        except ExternalAPIError:
            logger.warning("handoff email failed", extra={"tenant_id": str(tenant_id)})

    # 5. Realtime event.
    _emit_handed_off(tenant_id, lead_id, lead_name)

    # 6. Owner WhatsApp (platform channel), if configured.
    if owner is not None and owner["notification_whatsapp"]:
        from app.modules.notifications.whatsapp_channel import send_owner_whatsapp

        await send_owner_whatsapp(
            owner["notification_whatsapp"],
            f"🔔 A lead needs you on IIEVI: {lead_name}.\n\n{summary}\n\nOpen: {action_url}",
        )

    logger.info("lead handed off", extra={"tenant_id": str(tenant_id), "lead_id": str(lead_id)})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _generate_summary(
    context: Any,  # noqa: ANN401
    transcript: str,
    tenant_id: uuid.UUID,
    api_key: str | None,
) -> str:
    """A short factual summary for the owner. Degrades to the transcript tail
    if no key is available or generation fails."""
    fallback = transcript[-600:] if transcript else "This lead asked to speak with a person."
    if not api_key:
        return fallback
    system = (
        "You summarise a sales conversation for the business owner who is taking it over. "
        "Be factual and concise (3-4 sentences): what the customer wants, the key details "
        "they shared, and why they need a human. Use ONLY facts stated in the conversation."
    )
    try:
        result = await traced_ai_call(
            api_key=api_key,
            system=system,
            user_message=transcript or "(no messages)",
            model=FLASH_LITE_MODEL,
            call_type="handoff-summary",
            tenant_id=tenant_id,
            temperature=_SUMMARY_TEMPERATURE,
            max_tokens=_SUMMARY_MAX_TOKENS,
        )
        return result.text.strip() or fallback
    except Exception:  # noqa: BLE001 — summary is best-effort; never block the handoff
        logger.warning("handoff summary generation failed", extra={"tenant_id": str(tenant_id)})
        return fallback


async def _load_lead(session: Any, lead_id: uuid.UUID) -> dict[str, Any] | None:  # noqa: ANN401
    row = (
        await session.execute(
            text("SELECT name, phone, platform FROM leads WHERE id = :id"), {"id": lead_id}
        )
    ).first()
    if row is None:
        return None
    return {"name": row[0], "phone": row[1], "platform": str(row[2])}


async def _load_owner(session: Any) -> dict[str, Any] | None:  # noqa: ANN401
    row = (
        await session.execute(
            text(
                "SELECT id, email, full_name, notification_whatsapp FROM users "
                "WHERE role = 'owner' ORDER BY created_at ASC LIMIT 1"
            )
        )
    ).first()
    if row is None:
        return None
    return {
        "id": uuid.UUID(str(row[0])),
        "email": row[1],
        "full_name": row[2],
        "notification_whatsapp": row[3],
    }


async def _load_transcript(session: Any, lead_id: uuid.UUID) -> str:  # noqa: ANN401
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
    lines = [
        f"{'Customer' if str(r[0]) in ('lead', 'user') else 'Assistant'}: {r[1]}" for r in rows
    ]
    return "\n".join(lines)[-4000:]


def _emit_handed_off(tenant_id: uuid.UUID, lead_id: uuid.UUID, lead_name: str) -> None:
    from app.modules.realtime.events import EventEmitter

    EventEmitter.emit_sync(
        tenant_id, "lead_handed_off", {"lead_id": str(lead_id), "lead_name": lead_name}
    )
