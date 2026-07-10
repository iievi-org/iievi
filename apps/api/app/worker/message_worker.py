"""Incoming social message pipeline.

process_incoming_message is the single funnel for every inbound message
(WhatsApp, Messenger, Instagram DM). Order matters:

1. resolve tenant (platform_identifiers — this is why those rows exist)
2. classify intent on the PLATFORM's small AI budget (tenant context does
   not exist yet at this point)
3. upsert the lead (INSERT..ON CONFLICT — concurrent deliveries from the
   same person race, the constraint serialises them)
4. save the inbound message + update last_inbound_at (the 24h window clock)
5. manual_mode check — a human has taken over → notify, do NOT reply
6. enqueue generate_ai_response (ai_conversations queue)
7. mark the webhook event processed

Intent routing: enquiry ≥0.7 → AI replies; enquiry <0.7 → lead flagged for
manual review, no AI; complaint → manual_mode=True immediately; spam →
discarded; is_urgent → owner notified regardless of anything else.
"""

import asyncio
import json
import logging
import uuid
from collections.abc import Awaitable
from datetime import UTC, datetime
from typing import Any, cast

import httpx
from sqlalchemy import text

from app.worker.celery_app import celery_app
from app.worker.db import worker_session

logger = logging.getLogger(__name__)

GRAPH = "https://graph.facebook.com/v20.0"

DEFAULT_COMMENT_REPLY = "Thanks for reaching out! We've sent you a message 👋"

_LEAD_SOURCE_BY_PLATFORM = {
    "whatsapp": "whatsapp",
    "meta": "direct_message",
    "instagram": "direct_message",
}


async def _resolve_tenant(session: Any, platform: str, external_id: str) -> uuid.UUID | None:  # noqa: ANN401
    row = await session.execute(
        text(
            "SELECT tenant_id FROM platform_identifiers "
            "WHERE platform = :platform AND external_id = :ext"
        ),
        {"platform": platform, "ext": external_id},
    )
    result = row.first()
    return uuid.UUID(str(result[0])) if result else None


async def _upsert_lead(
    session: Any,  # noqa: ANN401
    *,
    tenant_id: uuid.UUID,
    platform: str,
    sender_id: str,
    sender_name: str,
    source: str,
) -> uuid.UUID:
    """INSERT..ON CONFLICT handles concurrent delivery of the same person's
    messages; last_inbound_at drives the WhatsApp 24-hour window."""
    row = (
        await session.execute(
            text(
                "INSERT INTO leads "
                "(tenant_id, source, platform, platform_id, name, last_inbound_at, status) "
                "VALUES (:tid, :source, :platform, :pid, nullif(:name, ''), :now, 'new') "
                "ON CONFLICT (tenant_id, platform_id) DO UPDATE SET "
                "updated_at = now(), last_inbound_at = EXCLUDED.last_inbound_at "
                "RETURNING id"
            ),
            {
                "tid": tenant_id,
                "source": source,
                "platform": platform,
                "pid": sender_id,
                "name": sender_name,
                "now": datetime.now(UTC),
            },
        )
    ).first()
    return uuid.UUID(str(row[0]))


async def _save_message(
    session: Any,
    tenant_id: uuid.UUID,
    lead_id: uuid.UUID,
    content: str,  # noqa: ANN401
) -> None:
    await session.execute(
        text(
            "INSERT INTO conversations (tenant_id, lead_id, role, content) "
            "VALUES (:tid, :lid, 'lead', :content)"
        ),
        {"tid": tenant_id, "lid": lead_id, "content": content},
    )


def _notify_owner(tenant_id: str, reason: str, detail: dict[str, object]) -> None:
    """Owner notification: realtime event now; email/WhatsApp channel lands
    with the notifications phase."""
    from app.modules.realtime.events import EventEmitter

    logger.info("owner notification", extra={"tenant_id": tenant_id, "reason": reason})
    EventEmitter.emit_sync(tenant_id, "new_lead", {"reason": reason, **detail})


@celery_app.task(name="messages.process_incoming", queue="ai_conversations", ignore_result=True)
def process_incoming_message(payload: dict[str, str]) -> None:
    """Funnel for every inbound message — see module docstring for the order."""

    async def _run() -> None:
        from app.core.exceptions import AIGenerationError
        from app.db.base import with_tenant_scope
        from app.modules.ai.intent_classification_service import (
            CONFIDENCE_THRESHOLD,
            classify_intent,
        )
        from app.modules.webhooks.service import mark_event_processed

        platform = payload["platform"]
        message_text = payload.get("text", "")

        async with worker_session() as session:
            tenant_id = await _resolve_tenant(session, platform, payload["external_id"])
            if tenant_id is None:
                logger.warning(
                    "no tenant for webhook identifier",
                    extra={"platform": platform, "external_id": payload["external_id"]},
                )
                return

            # 2. intent — before tenant context, message text only
            try:
                intent = await classify_intent(message_text)
            except AIGenerationError:
                intent = None  # classification down → degrade to manual review

            if intent is not None and intent.intent == "spam":
                logger.info("spam discarded", extra={"tenant_id": str(tenant_id)})
                await _finish_event(session, payload)
                return

            async with with_tenant_scope(session, tenant_id):
                lead_id = await _upsert_lead(
                    session,
                    tenant_id=tenant_id,
                    platform=platform,
                    sender_id=payload["sender_id"],
                    sender_name=payload.get("sender_name", ""),
                    source=_LEAD_SOURCE_BY_PLATFORM.get(platform, "direct_message"),
                )
                await _save_message(session, tenant_id, lead_id, message_text)

                needs_review = intent is None or (
                    intent.intent == "enquiry" and intent.confidence < CONFIDENCE_THRESHOLD
                )
                is_complaint = intent is not None and (
                    intent.intent == "complaint" or intent.requires_human
                )
                lead_meta_updates: dict[str, object] = {}
                if intent is not None:
                    lead_meta_updates["last_intent"] = intent.intent
                    if intent.service_interest:
                        lead_meta_updates["service_interest"] = intent.service_interest
                if needs_review:
                    lead_meta_updates["needs_review"] = True

                manual_row = await session.execute(
                    text("SELECT manual_mode, metadata FROM leads WHERE id = :id"),
                    {"id": lead_id},
                )
                manual_mode, existing_meta = manual_row.first() or (False, {})

                if is_complaint:
                    await session.execute(
                        text("UPDATE leads SET manual_mode = true WHERE id = :id"),
                        {"id": lead_id},
                    )
                    manual_mode = True
                if lead_meta_updates:
                    merged = {**(existing_meta or {}), **lead_meta_updates}
                    await session.execute(
                        text("UPDATE leads SET metadata = cast(:meta AS jsonb) WHERE id = :id"),
                        {"id": lead_id, "meta": json.dumps(merged)},
                    )
                await session.commit()

            if intent is not None and intent.is_urgent:
                _notify_owner(
                    str(tenant_id),
                    "urgent_message",
                    {"lead_id": str(lead_id), "preview": message_text[:140]},
                )
            if is_complaint:
                _notify_owner(
                    str(tenant_id),
                    "complaint",
                    {"lead_id": str(lead_id), "preview": message_text[:140]},
                )

            # 5. human has taken over → notify and STOP
            if manual_mode:
                _notify_owner(
                    str(tenant_id),
                    "manual_mode_message",
                    {"lead_id": str(lead_id), "preview": message_text[:140]},
                )
            elif not needs_review and intent is not None and intent.intent == "enquiry":
                # 6. AI replies only to confident enquiries
                generate_ai_response.delay({"tenant_id": str(tenant_id), "lead_id": str(lead_id)})
            else:
                _notify_owner(
                    str(tenant_id),
                    "needs_review",
                    {"lead_id": str(lead_id), "preview": message_text[:140]},
                )

            await _finish_event(session, payload)
        _ = mark_event_processed  # referenced via _finish_event

    asyncio.run(_run())


async def _finish_event(session: Any, payload: dict[str, str]) -> None:  # noqa: ANN401
    from app.modules.webhooks.service import mark_event_processed

    event_id = payload.get("event_id")
    if event_id:
        await mark_event_processed(session, uuid.UUID(event_id))


@celery_app.task(name="messages.generate_ai_response", queue="ai_conversations", ignore_result=True)
def generate_ai_response(payload: dict[str, str]) -> None:
    """Stub: the grounded conversation engine lands with the outreach phase
    (Prompt 7). The queue routing and enqueue contract are already final."""
    logger.info(
        "ai response requested",
        extra={"tenant_id": payload.get("tenant_id"), "lead_id": payload.get("lead_id")},
    )


@celery_app.task(
    name="messages.process_facebook_comment", queue="ai_conversations", ignore_result=True
)
def process_facebook_comment(payload: dict[str, str]) -> None:
    """Two-action comment handler: public reply + private Messenger DM,
    concurrently. The DM matters more — a failed public reply (post too old,
    comments locked) logs a warning and the DM still goes out."""

    async def _run() -> None:
        from app.db.base import with_tenant_scope
        from app.modules.ai.intent_classification_service import classify_intent
        from app.modules.credentials.service import get_decrypted_credential

        async with worker_session() as session:
            tenant_id = await _resolve_tenant(session, "meta", payload["external_id"])
            if tenant_id is None:
                return

            try:
                intent = await classify_intent(payload.get("text", ""))
                if intent.intent != "enquiry":
                    await _finish_event(session, payload)
                    return
            except Exception:  # noqa: BLE001 — classification down → treat as enquiry
                logger.warning("comment intent classification failed; treating as enquiry")

            async with with_tenant_scope(session, tenant_id):
                credential = await get_decrypted_credential(tenant_id, "meta", session)
                reply_text = await _comment_reply_text(session)
                lead_id = await _upsert_lead(
                    session,
                    tenant_id=tenant_id,
                    platform="meta",
                    sender_id=payload["commenter_psid"],
                    sender_name=payload.get("commenter_name", ""),
                    source="comment",
                )
                await _save_message(session, tenant_id, lead_id, payload.get("text", ""))
                await session.commit()

            token = credential.fields["access_token"]
            page_id = credential.fields["page_id"]
            async with httpx.AsyncClient(timeout=30) as client:
                reply_result, dm_result = await asyncio.gather(
                    client.post(
                        f"{GRAPH}/{payload['comment_id']}/comments",
                        data={"message": reply_text, "access_token": token},
                    ),
                    client.post(
                        f"{GRAPH}/{page_id}/messages",
                        params={"access_token": token},
                        json={
                            "recipient": {"id": payload["commenter_psid"]},
                            "message": {"text": reply_text},
                            "messaging_type": "RESPONSE",
                        },
                    ),
                    return_exceptions=True,
                )
            if isinstance(reply_result, BaseException) or (
                not isinstance(reply_result, BaseException) and reply_result.status_code != 200
            ):
                # Public reply failing is survivable (post too old etc.)
                logger.warning(
                    "public comment reply failed",
                    extra={"comment_id": payload["comment_id"], "tenant_id": str(tenant_id)},
                )
            if isinstance(dm_result, BaseException) or (
                not isinstance(dm_result, BaseException) and dm_result.status_code != 200
            ):
                logger.error(
                    "comment DM failed",
                    extra={"comment_id": payload["comment_id"], "tenant_id": str(tenant_id)},
                )
            else:
                generate_ai_response.delay({"tenant_id": str(tenant_id), "lead_id": str(lead_id)})
            _notify_owner(str(tenant_id), "new_lead", {"lead_id": str(lead_id)})
            await _finish_event(session, payload)

    asyncio.run(_run())


async def _comment_reply_text(session: Any) -> str:  # noqa: ANN401
    """Configurable public reply — MarketingConfig goals['comment_reply_text']."""
    row = await session.execute(text("SELECT goals FROM marketing_configs LIMIT 1"))
    result = row.first()
    goals = result[0] if result else {}
    return str((goals or {}).get("comment_reply_text") or DEFAULT_COMMENT_REPLY)


@celery_app.task(name="channels.sync_tiktok_comments", queue="lead_outreach", ignore_result=True)
def sync_tiktok_comments() -> int:
    """Hourly poll — TikTok has no comment webhooks. New enquiry comments get
    a public reply carrying the WhatsApp deep link (TikTok has no business DM
    API; the WhatsApp funnel is the only route) and a lead with
    pending_whatsapp=true for when they make contact."""

    async def _run() -> int:
        from app.core.redis import get_redis
        from app.db.base import with_tenant_scope
        from app.modules.ai.intent_classification_service import classify_intent
        from app.modules.credentials.service import get_decrypted_credential

        processed = 0
        redis = get_redis()
        async with worker_session() as session:
            rows = (
                await session.execute(
                    text("SELECT DISTINCT tenant_id FROM api_credentials WHERE service = 'tiktok'")
                )
            ).all()
            for (raw_tenant_id,) in rows:
                tenant_id = uuid.UUID(str(raw_tenant_id))
                seen_key = f"tiktok_processed:{tenant_id}"
                try:
                    async with with_tenant_scope(session, tenant_id):
                        credential = await get_decrypted_credential(tenant_id, "tiktok", session)
                        await session.commit()
                    comments = await _fetch_recent_tiktok_comments(credential)
                    whatsapp_link = str(credential.fields.get("whatsapp_link", ""))
                    for comment in comments:
                        comment_id = str(comment["id"])
                        already_seen = await cast(
                            "Awaitable[int]", redis.sismember(seen_key, comment_id)
                        )
                        if already_seen:
                            continue
                        intent = await classify_intent(str(comment.get("text", "")))
                        if intent.intent == "enquiry":
                            async with with_tenant_scope(session, tenant_id):
                                lead_id = await _upsert_lead(
                                    session,
                                    tenant_id=tenant_id,
                                    platform="tiktok",
                                    sender_id=str(comment.get("user_id", comment_id)),
                                    sender_name=str(comment.get("username", "")),
                                    source="comment",
                                )
                                await session.execute(
                                    text(
                                        "UPDATE leads SET metadata = metadata || "
                                        "'{\"pending_whatsapp\": true}'::jsonb WHERE id = :id"
                                    ),
                                    {"id": lead_id},
                                )
                                await session.commit()
                            await _reply_tiktok_comment(credential, comment, whatsapp_link)
                        await cast("Awaitable[int]", redis.sadd(seen_key, comment_id))
                        await cast("Awaitable[int]", redis.expire(seen_key, 48 * 3600))
                        processed += 1
                except Exception:  # noqa: BLE001 — one tenant's failure must not stop the sweep
                    logger.exception("tiktok sync failed", extra={"tenant_id": str(tenant_id)})
        return processed

    count = asyncio.run(_run())
    logger.info("tiktok comment sync complete", extra={"processed": count})
    return count


async def _fetch_recent_tiktok_comments(credential: Any) -> list[dict[str, object]]:  # noqa: ANN401
    """Fetch comments from the last 24h across recent posts."""
    from app.core.circuit import get_circuit

    token = credential.fields["access_token"]

    async def _run() -> list[dict[str, object]]:
        comments: list[dict[str, object]] = []
        async with httpx.AsyncClient(timeout=30) as client:
            videos = await client.post(
                "https://open.tiktokapis.com/v2/video/list/",
                headers={"Authorization": f"Bearer {token}"},
                json={"max_count": 10},
            )
            if videos.status_code != 200:
                return comments
            for video in videos.json().get("data", {}).get("videos", []):
                response = await client.post(
                    "https://open.tiktokapis.com/v2/video/comment/list/",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"video_id": video.get("id"), "max_count": 50},
                )
                if response.status_code != 200:
                    continue
                cutoff = datetime.now(UTC).timestamp() - 24 * 3600
                for comment in response.json().get("data", {}).get("comments", []):
                    if float(comment.get("create_time", 0)) >= cutoff:
                        comments.append(comment)
        return comments

    return await get_circuit("tiktok").call(_run)


async def _reply_tiktok_comment(
    credential: Any,
    comment: dict[str, object],
    whatsapp_link: str,  # noqa: ANN401
) -> None:
    from app.core.circuit import get_circuit

    token = credential.fields["access_token"]
    reply = f"Thanks for your interest! Message us on WhatsApp to book: {whatsapp_link}"

    async def _run() -> None:
        async with httpx.AsyncClient(timeout=30) as client:
            await client.post(
                "https://open.tiktokapis.com/v2/video/comment/reply/",
                headers={"Authorization": f"Bearer {token}"},
                json={"comment_id": comment["id"], "text": reply},
            )

    try:
        await get_circuit("tiktok").call(_run)
    except Exception:  # noqa: BLE001 — the lead is captured; the reply is best-effort
        logger.warning("tiktok comment reply failed", extra={"comment_id": str(comment["id"])})
