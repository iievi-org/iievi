"""Atomic monthly usage enforcement.

check_and_increment_usage uses a single conditional UPDATE:

    UPDATE monthly_usage SET col = col + 1
    WHERE tenant_id = :tid AND month = :month AND col < :limit
    RETURNING col

Zero rows → limit reached. One row → increment succeeded. Two concurrent
requests can never both pass a boundary because the row lock serialises the
condition check with the increment.

Agency tenants bypass entirely. Call this BEFORE every AI call, post
generation, and image generation.
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plans import NEXT_PLAN, PLAN_LIMITS
from app.db.models import Plan

logger = logging.getLogger(__name__)

# Whitelist: usage_type -> monthly_usage column. NEVER interpolate caller
# input into SQL outside this mapping.
_USAGE_COLUMNS: dict[str, str] = {
    "posts_generated": "posts_generated",
    "images_generated": "images_generated",
    "ai_messages": "ai_messages",
    "leads_captured": "leads_captured",
}


@dataclass(frozen=True)
class UsageDecision:
    allowed: bool
    current: int
    limit: int | None  # None = unlimited


def _current_month() -> date:
    return datetime.now(UTC).date().replace(day=1)


async def check_and_increment_usage(
    tenant_id: uuid.UUID, usage_type: str, plan: Plan, session: AsyncSession
) -> UsageDecision:
    """Atomically consume one unit of quota, or report the limit as reached.

    Runs inside the caller's tenant-scoped session (RLS applies to
    monthly_usage, so the row is only visible with tenant context set).
    """
    column = _USAGE_COLUMNS.get(usage_type)
    if column is None:
        msg = f"unknown usage type: {usage_type}"
        raise ValueError(msg)

    limit = PLAN_LIMITS[plan][usage_type]
    if limit is None:  # Agency: unlimited, no counter contention at all
        return UsageDecision(allowed=True, current=0, limit=None)

    month = _current_month()

    # Ensure the month row exists (idempotent; first request of the month)
    await session.execute(
        text(
            "INSERT INTO monthly_usage (tenant_id, month) VALUES (:tid, :month) "
            "ON CONFLICT (tenant_id, month) DO NOTHING"
        ),
        {"tid": tenant_id, "month": month},
    )

    row = (
        await session.execute(
            text(
                f"UPDATE monthly_usage SET {column} = {column} + 1, updated_at = now() "  # noqa: S608 — column is whitelisted above
                f"WHERE tenant_id = :tid AND month = :month AND {column} < :limit "
                f"RETURNING {column}"
            ),
            {"tid": tenant_id, "month": month, "limit": limit},
        )
    ).first()

    if row is None:  # zero rows affected — at or over the limit
        current = await session.scalar(
            text(
                f"SELECT {column} FROM monthly_usage "  # noqa: S608
                "WHERE tenant_id = :tid AND month = :month"
            ),
            {"tid": tenant_id, "month": month},
        )
        return UsageDecision(allowed=False, current=int(current or limit), limit=limit)

    return UsageDecision(allowed=True, current=int(row[0]), limit=limit)


def upgrade_target(plan: Plan) -> str:
    """Which plan the 402 error should suggest."""
    nxt = NEXT_PLAN.get(plan)
    return nxt.value if nxt else plan.value
