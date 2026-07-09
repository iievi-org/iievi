"""Billing surface: the capabilities endpoint the frontend reads.

GET /billing/capabilities is THE single source the frontend uses to decide
which features to render enabled. It merges: plan tier, tenant status,
current month's usage vs limits, and feature-flag overrides.
"""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.core.plans import PLAN_LIMITS
from app.core.redis import get_redis
from app.db.models import MonthlyUsage, Plan, Tenant, TenantStatus
from app.gateway.dependencies import PLAN_HIERARCHY, CurrentUser, ScopedSession
from app.services.feature_flags import FeatureFlagService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


class UsageReport(BaseModel):
    posts_generated: int
    images_generated: int
    ai_messages: int
    leads_captured: int
    limits: dict[str, int | None]


class Capabilities(BaseModel):
    can_generate_posts: bool
    can_create_ads: bool
    can_publish_tiktok: bool
    can_publish_linkedin: bool
    can_use_ai_conversations: bool
    is_suspended: bool
    plan: str
    usage: UsageReport


@router.get(
    "/capabilities",
    summary="Current tenant's feature capabilities",
    description=(
        "The single endpoint the frontend reads to enable/disable features. "
        "Merges plan tier, suspension state, monthly usage, and feature flags."
    ),
    response_model=Capabilities,
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "can_generate_posts": True,
                        "can_create_ads": False,
                        "can_publish_tiktok": False,
                        "can_publish_linkedin": True,
                        "can_use_ai_conversations": True,
                        "is_suspended": False,
                        "plan": "starter",
                        "usage": {
                            "posts_generated": 12,
                            "images_generated": 8,
                            "ai_messages": 240,
                            "leads_captured": 57,
                            "limits": {
                                "posts_generated": 60,
                                "images_generated": 60,
                                "ai_messages": 1000,
                                "leads_captured": 500,
                            },
                        },
                    }
                }
            }
        }
    },
)
async def get_capabilities(user: CurrentUser, session: ScopedSession) -> Capabilities:
    tenant = await session.get(Tenant, user.tenant_id)
    is_suspended = tenant is not None and tenant.status == TenantStatus.SUSPENDED
    plan = Plan(user.plan)
    limits = PLAN_LIMITS[plan]

    month_start = datetime.now(UTC).date().replace(day=1)
    usage_row = await session.scalar(select(MonthlyUsage).where(MonthlyUsage.month == month_start))

    def _used(field: str) -> int:
        return int(getattr(usage_row, field, 0) or 0) if usage_row else 0

    def _under(field: str) -> bool:
        limit = limits[field]
        return limit is None or _used(field) < limit

    flags = FeatureFlagService(session, get_redis())
    tiktok_flag = await flags.is_enabled("publish_tiktok", user.tenant_id, plan)
    linkedin_flag = await flags.is_enabled("publish_linkedin", user.tenant_id, plan)

    plan_rank = PLAN_HIERARCHY[user.plan]
    active = not is_suspended

    return Capabilities(
        can_generate_posts=active and _under("posts_generated"),
        can_create_ads=active and plan_rank >= PLAN_HIERARCHY[Plan.GROWTH.value],
        can_publish_tiktok=active
        and (tiktok_flag or plan_rank >= PLAN_HIERARCHY[Plan.GROWTH.value]),
        can_publish_linkedin=active
        and (linkedin_flag or plan_rank >= PLAN_HIERARCHY[Plan.STARTER.value]),
        can_use_ai_conversations=active and _under("ai_messages"),
        is_suspended=is_suspended,
        plan=user.plan,
        usage=UsageReport(
            posts_generated=_used("posts_generated"),
            images_generated=_used("images_generated"),
            ai_messages=_used("ai_messages"),
            leads_captured=_used("leads_captured"),
            limits=dict(limits),
        ),
    )
