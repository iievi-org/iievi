"""Webhook operations tooling (platform admin only).

- POST /admin/webhooks/replay — re-enqueue processing for a stored event.
  THE recovery path when a payment webhook was received (and 200'd) but the
  Celery task failed: the raw payload is in webhook_events, replay re-runs it.
- GET /admin/webhooks/failed — failed events from the last 7 days; the
  platform team's daily health check.
"""

import logging
import uuid

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select, text

from app.core.exceptions import BadRequestError, ResourceNotFoundError
from app.db.models import IdempotencyStatus, WebhookEvent
from app.gateway.dependencies import AdminUser, ScopedSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/webhooks", tags=["admin"])


class ReplayRequest(BaseModel):
    webhook_event_id: uuid.UUID


@router.post("/replay", summary="Replay a stored webhook event")
async def replay_webhook(
    body: ReplayRequest, admin: AdminUser, session: ScopedSession
) -> dict[str, str]:
    event = await session.scalar(
        select(WebhookEvent).where(WebhookEvent.id == body.webhook_event_id)
    )
    if event is None:
        raise ResourceNotFoundError(f"No webhook event {body.webhook_event_id}")

    payload = event.payload or {}
    if event.platform in ("razorpay", "stripe"):
        from app.worker.billing_worker import process_billing_event

        result = process_billing_event.delay(
            {
                "provider": event.platform,
                "event_type": event.event_type,
                "event_id": str(event.id),
                "payload": payload,
            }
        )
    elif event.platform == "meta":
        from app.modules.webhooks.meta_router import _route_entry

        entry = payload.get("entry")
        if not isinstance(entry, dict):
            raise BadRequestError("Stored Meta event has no replayable payload")
        _route_entry(str(payload.get("object", "")), str(entry.get("id", "")), entry, str(event.id))
        result = None
    else:
        raise BadRequestError(f"Replay not supported for platform: {event.platform}")

    # Reset status so the replayed processing can mark it again
    await session.execute(
        text("UPDATE webhook_events SET idempotency_status = 'pending' WHERE id = :id"),
        {"id": event.id},
    )
    logger.info(
        "webhook replayed",
        extra={"event_id": str(event.id), "platform": event.platform, "admin": str(admin.user_id)},
    )
    return {
        "webhook_event_id": str(event.id),
        "task_id": str(result.id) if result is not None else "inline",
    }


@router.get("/failed", summary="Failed webhook events (last 7 days)")
async def failed_webhooks(admin: AdminUser, session: ScopedSession) -> dict[str, object]:
    events = (
        await session.scalars(
            select(WebhookEvent)
            .where(
                WebhookEvent.idempotency_status == IdempotencyStatus.FAILED,
                WebhookEvent.received_at > text("now() - interval '7 days'"),
            )
            .order_by(WebhookEvent.received_at.desc())
        )
    ).all()
    return {
        "failed": [
            {
                "id": str(e.id),
                "platform": e.platform,
                "event_type": e.event_type,
                "platform_event_id": e.platform_event_id,
                "received_at": e.received_at.isoformat(),
            }
            for e in events
        ],
        "count": len(events),
    }
