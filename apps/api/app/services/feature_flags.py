"""Feature flag evaluation with Redis-first caching.

Resolution order for is_enabled(flag_key, tenant_id, plan):
1. tenant in disabled_for_tenants  → False (explicit kill-switch wins)
2. enabled_globally                → True
3. tenant in enabled_for_tenants   → True
4. plan >= minimum_plan            → True
5. otherwise                       → False

Flag rows are cached in Redis as ff:{flag_key} with a 60-second TTL; any
flag mutation must call invalidate(). An unknown flag evaluates to False.
"""

import logging
import uuid

import redis.asyncio as aioredis
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import FeatureFlag, Plan

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 60
_CACHE_PREFIX = "ff:"

# Plan ordering for minimum_plan comparisons
_PLAN_RANK: dict[Plan, int] = {
    Plan.TRIAL: 0,
    Plan.STARTER: 1,
    Plan.GROWTH: 2,
    Plan.AGENCY: 3,
}


class _FlagData(BaseModel):
    """Cached, serializable projection of a FeatureFlag row."""

    enabled_globally: bool
    enabled_for_tenants: list[str]
    disabled_for_tenants: list[str]
    minimum_plan: str | None


class _CachedFlag(BaseModel):
    """Redis cache envelope — also represents a cached miss."""

    missing: bool
    flag: _FlagData | None


class FeatureFlagService:
    """Evaluates feature flags with a Redis cache in front of the database."""

    def __init__(self, session: AsyncSession, redis: aioredis.Redis) -> None:
        self._session = session
        self._redis = redis

    async def is_enabled(self, flag_key: str, tenant_id: uuid.UUID, plan: Plan) -> bool:
        flag = await self._get_flag(flag_key)
        if flag is None:
            return False
        tenant = str(tenant_id)
        if tenant in flag.disabled_for_tenants:
            return False
        if flag.enabled_globally:
            return True
        if tenant in flag.enabled_for_tenants:
            return True
        if flag.minimum_plan is not None:
            return _PLAN_RANK[plan] >= _PLAN_RANK[Plan(flag.minimum_plan)]
        return False

    async def invalidate(self, flag_key: str) -> None:
        """Call after any mutation of the flag row."""
        await self._redis.delete(f"{_CACHE_PREFIX}{flag_key}")

    async def _get_flag(self, flag_key: str) -> "_FlagData | None":
        cache_key = f"{_CACHE_PREFIX}{flag_key}"
        cached = await self._redis.get(cache_key)
        if cached is not None:
            data = _CachedFlag.model_validate_json(cached)
            return None if data.missing else data.flag

        row = await self._session.scalar(
            select(FeatureFlag).where(FeatureFlag.flag_key == flag_key)
        )
        if row is None:
            # Negative caching prevents a missing flag from hammering the DB
            await self._redis.set(
                cache_key,
                _CachedFlag(missing=True, flag=None).model_dump_json(),
                ex=CACHE_TTL_SECONDS,
            )
            return None

        flag = _FlagData(
            enabled_globally=row.enabled_globally,
            enabled_for_tenants=[str(t) for t in row.enabled_for_tenants],
            disabled_for_tenants=[str(t) for t in row.disabled_for_tenants],
            minimum_plan=row.minimum_plan.value if row.minimum_plan else None,
        )
        await self._redis.set(
            cache_key,
            _CachedFlag(missing=False, flag=flag).model_dump_json(),
            ex=CACHE_TTL_SECONDS,
        )
        return flag
