"""Weekly performance report — Prompt 7 Step 12.

A Celery Beat job (Mondays 9am IST) that emails each active tenant's owner a
summary of the past week: leads received, AI conversation rate, posts published,
ad spend, and bookings closed. The subject line leads with the number the owner
cares about — "You got 23 leads last week — here's how they converted" — which
is the platform's most effective retention touch.

Tenants with no activity in the week are skipped (an empty report is noise).
"""

import asyncio
import logging
import uuid
from typing import Any

from sqlalchemy import text

from app.db.base import with_tenant_scope
from app.worker.celery_app import celery_app
from app.worker.db import worker_session

logger = logging.getLogger(__name__)


@celery_app.task(
    name="reports.generate_weekly_performance", queue="usage_tracking", ignore_result=True
)
def generate_weekly_performance_reports() -> int:
    """Send the weekly report to every active tenant with activity."""
    count = asyncio.run(_run())
    logger.info("weekly performance reports sent", extra={"count": count})
    return count


async def _run() -> int:
    sent = 0
    async with worker_session() as session:
        tenant_rows = (
            await session.execute(text("SELECT id, name FROM tenants WHERE status = 'active'"))
        ).all()
        for tid_raw, tenant_name in tenant_rows:
            tenant_id = uuid.UUID(str(tid_raw))
            try:
                metrics, owner = await _tenant_week(session, tenant_id)
                if metrics["leads_received"] == 0 and metrics["posts_published"] == 0:
                    continue  # no activity this week — skip the empty report
                if owner is None or not owner["email"]:
                    continue
                await _send_report(tenant_id, str(tenant_name), metrics, owner)
                sent += 1
            except Exception:  # noqa: BLE001 — one tenant's failure must not stop the run
                logger.exception(
                    "weekly report failed for tenant", extra={"tenant_id": str(tenant_id)}
                )
    return sent


async def _tenant_week(
    session: Any,  # noqa: ANN401
    tenant_id: uuid.UUID,
) -> tuple[dict[str, int], dict[str, Any] | None]:
    """Compute one tenant's last-7-day metrics and find its owner."""
    async with with_tenant_scope(session, tenant_id):
        received = await _count(
            session, "SELECT count(*) FROM leads WHERE created_at >= now() - interval '7 days'"
        )
        engaged = await _count(
            session,
            "SELECT count(*) FROM leads WHERE created_at >= now() - interval '7 days' "
            "AND conversation_state <> 'new'",
        )
        posts_published = await _count(
            session,
            "SELECT count(*) FROM posts WHERE status = 'published' "
            "AND published_at >= now() - interval '7 days'",
        )
        bookings = await _count(
            session,
            "SELECT count(*) FROM leads WHERE conversation_state = 'booked' "
            "AND updated_at >= now() - interval '7 days'",
        )
        owner_row = (
            await session.execute(
                text(
                    "SELECT email, full_name FROM users WHERE role = 'owner' "
                    "ORDER BY created_at ASC LIMIT 1"
                )
            )
        ).first()
        await session.commit()

    rate = round(engaged / received * 100) if received else 0
    metrics = {
        "leads_received": received,
        "ai_conversation_rate": rate,
        "posts_published": posts_published,
        # Ad spend is sourced from the ads-insights sync; 0 until that lands.
        "ad_spend_paise": 0,
        "bookings_closed": bookings,
    }
    owner = {"email": owner_row[0], "full_name": owner_row[1]} if owner_row else None
    return metrics, owner


async def _count(session: Any, sql: str) -> int:  # noqa: ANN401
    return int(await session.scalar(text(sql)) or 0)


async def _send_report(
    tenant_id: uuid.UUID,
    business_name: str,
    metrics: dict[str, int],
    owner: dict[str, Any],
) -> None:
    from app.modules.notifications.email_service import WeeklyPerformanceEmail, send_email

    try:
        await send_email(
            WeeklyPerformanceEmail(
                to=str(owner["email"]),
                business_name=business_name,
                leads_received=metrics["leads_received"],
                ai_conversation_rate=metrics["ai_conversation_rate"],
                posts_published=metrics["posts_published"],
                ad_spend_paise=metrics["ad_spend_paise"],
                bookings_closed=metrics["bookings_closed"],
            )
        )
    except Exception:  # noqa: BLE001 — email is best-effort; one failure shouldn't abort the run
        logger.warning("weekly report email failed", extra={"tenant_id": str(tenant_id)})
