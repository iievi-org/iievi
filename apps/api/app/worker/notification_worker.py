"""Deferred notification delivery — Prompt 7 Step 10.

When a notification is due inside a user's quiet hours, ``dispatch`` queues this
task with a countdown to the end of the window. When it fires, it delivers to
exactly the channels that were enabled at defer time (already computed against
the user's preferences), so quiet hours delay delivery without changing intent.
"""

import asyncio
import uuid

from app.db.base import with_tenant_scope
from app.db.models import NotificationType
from app.worker.celery_app import celery_app
from app.worker.db import worker_session


@celery_app.task(name="notifications.deliver_deferred", queue="usage_tracking", ignore_result=True)
def deliver_deferred_notification(payload: dict[str, object]) -> None:
    """Deliver a notification that was held back for quiet hours."""
    asyncio.run(_run(payload))


async def _run(payload: dict[str, object]) -> None:
    from app.modules.notifications.service import deliver_channels

    tenant_id = uuid.UUID(str(payload["tenant_id"]))
    user_id = uuid.UUID(str(payload["user_id"]))
    raw_channels = payload.get("channels", [])
    channels = (
        [str(c) for c in raw_channels if isinstance(c, str)]
        if isinstance(raw_channels, list)
        else []
    )
    if not channels:
        return

    async with worker_session() as session:
        async with with_tenant_scope(session, tenant_id):
            await deliver_channels(
                session,
                tenant_id=tenant_id,
                user_id=user_id,
                notif_type=NotificationType(str(payload["type"])),
                title=str(payload["title"]),
                body=str(payload["body"]),
                channels=channels,
                action_url=_opt_str(payload.get("action_url")),
                email_to=_opt_str(payload.get("email_to")),
                whatsapp_to=_opt_str(payload.get("whatsapp_to")),
                business_name=_opt_str(payload.get("business_name")),
            )
            await session.commit()


def _opt_str(value: object) -> str | None:
    return str(value) if isinstance(value, str) and value else None
