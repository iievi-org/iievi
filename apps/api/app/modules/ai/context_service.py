"""Tenant AI context assembly — the grounding source for every AI call.

The context is assembled for EVERY conversation turn, so it is cached in
Redis for 5 minutes (ctx:{tenant_id}, JSON). At 100 tenants with active
conversations that cache eliminates hundreds of database fetches per minute.
The cache MUST be invalidated on any profile change (profiles/hooks.py does
this) — stale context is worse than no cache: the AI would quote old prices.
"""

import logging
import uuid

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ProfileIncompleteError
from app.core.redis import get_redis
from app.db.base import with_tenant_scope
from app.db.models import BrandKit, BusinessProfile, MarketingConfig

logger = logging.getLogger(__name__)

CONTEXT_CACHE_TTL_S = 300


def _cache_key(tenant_id: uuid.UUID) -> str:
    return f"ctx:{tenant_id}"


class TenantAIContext(BaseModel):
    """Strictly-typed grounding context. The AI may ONLY talk about what is
    in here — prompts explicitly prohibit inventing services or prices."""

    model_config = {"extra": "forbid"}

    tenant_id: str
    business_name: str = Field(min_length=1)
    category: str
    description: str | None = None
    services: dict[str, object] = Field(default_factory=dict)
    pricing: dict[str, object] = Field(default_factory=dict)
    hours: dict[str, object] = Field(default_factory=dict)
    locations: dict[str, object] = Field(default_factory=dict)
    faqs: dict[str, object] = Field(default_factory=dict)
    policies: dict[str, object] = Field(default_factory=dict)
    tone: str | None = None
    goals: dict[str, object] = Field(default_factory=dict)
    target_audience: dict[str, object] = Field(default_factory=dict)
    brand_colors: dict[str, object] = Field(default_factory=dict)
    image_style_prompt: str | None = None


async def assemble_tenant_context(tenant_id: uuid.UUID, session: AsyncSession) -> TenantAIContext:
    """Fetch (or cache-hit) the validated AI context for one tenant."""
    redis = get_redis()
    cached = await redis.get(_cache_key(tenant_id))
    if cached:
        try:
            return TenantAIContext.model_validate_json(cached)
        except ValueError:
            # Schema drift between deploys — treat as a miss, rebuild below
            await redis.delete(_cache_key(tenant_id))

    async with with_tenant_scope(session, tenant_id):
        profile = await session.scalar(select(BusinessProfile))
        marketing = await session.scalar(select(MarketingConfig))
        kit = await session.scalar(select(BrandKit))

    if profile is None:
        raise ProfileIncompleteError(
            "Business profile is not set up yet — complete onboarding first"
        )

    context = TenantAIContext(
        tenant_id=str(tenant_id),
        business_name=profile.business_name,
        category=profile.category,
        description=profile.description,
        services=profile.services or {},
        pricing=profile.pricing or {},
        hours=profile.hours or {},
        locations=profile.locations or {},
        faqs=profile.faqs or {},
        policies=profile.policies or {},
        tone=marketing.tone if marketing else None,
        goals=(marketing.goals or {}) if marketing else {},
        target_audience=(marketing.target_audience or {}) if marketing else {},
        brand_colors=(kit.colors or {}) if kit else {},
        image_style_prompt=kit.nanobanana_style_prompt if kit else None,
    )

    await redis.set(_cache_key(tenant_id), context.model_dump_json(), ex=CONTEXT_CACHE_TTL_S)
    return context


async def invalidate_tenant_context(tenant_id: uuid.UUID) -> None:
    """Drop the cached context — called on every profile write."""
    await get_redis().delete(_cache_key(tenant_id))
