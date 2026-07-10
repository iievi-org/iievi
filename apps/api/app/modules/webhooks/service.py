"""Webhook event deduplication — insert-BEFORE-process.

The order is the entire point: the row is inserted before any processing
starts, so if processing crashes halfway through, the NEXT delivery of the
same event sees the existing row and is skipped. The alternative
(process-then-insert) re-processes on every crash — duplicate leads,
duplicate messages, duplicate plan activations.

claim_webhook_event returns the new row's id when this delivery is the
first, or None when the event was already claimed (caller returns HTTP 200
immediately — webhook platforms treat anything else as a failure and retry).
"""

import json
import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def claim_webhook_event(
    session: AsyncSession,
    *,
    platform_event_id: str,
    platform: str,
    event_type: str,
    tenant_id: uuid.UUID | None = None,
    payload: dict[str, object] | None = None,
) -> uuid.UUID | None:
    """Insert-before-process claim. None = duplicate delivery, skip processing.

    The raw payload is stored with the claim so the admin replay endpoint can
    re-enqueue processing after a downstream task failure."""
    row = (
        await session.execute(
            text(
                "INSERT INTO webhook_events "
                "(platform_event_id, platform, event_type, tenant_id, payload) "
                "VALUES (:eid, :platform, :etype, :tid, cast(:payload AS jsonb)) "
                "ON CONFLICT (platform_event_id) DO NOTHING "
                "RETURNING id"
            ),
            {
                "eid": platform_event_id,
                "platform": platform,
                "etype": event_type,
                "tid": tenant_id,
                "payload": json.dumps(payload or {}),
            },
        )
    ).first()
    await session.commit()
    if row is None:
        logger.info(
            "duplicate webhook skipped",
            extra={"platform": platform, "platform_event_id": platform_event_id},
        )
        return None
    return uuid.UUID(str(row[0]))


async def mark_event_processed(session: AsyncSession, event_id: uuid.UUID) -> None:
    await session.execute(
        text(
            "UPDATE webhook_events SET idempotency_status = 'processed', "
            "processed_at = :now WHERE id = :id"
        ),
        {"id": event_id, "now": datetime.now(UTC)},
    )
    await session.commit()


async def mark_event_failed(session: AsyncSession, event_id: uuid.UUID) -> None:
    await session.execute(
        text("UPDATE webhook_events SET idempotency_status = 'failed' WHERE id = :id"),
        {"id": event_id},
    )
    await session.commit()
