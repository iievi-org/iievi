"""FeatureFlagService evaluation logic and Redis caching behaviour."""

import json
import uuid
from typing import cast

import fakeredis.aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Plan
from app.services.feature_flags import CACHE_TTL_SECONDS, FeatureFlagService

TENANT_A = uuid.uuid4()
TENANT_B = uuid.uuid4()


class _StubSession:
    """Stands in for AsyncSession; returns a preset FeatureFlag row or None."""

    def __init__(self, row: object | None) -> None:
        self.row = row
        self.scalar_calls = 0

    async def scalar(self, _stmt: object) -> object | None:
        self.scalar_calls += 1
        return self.row


class _Row:
    def __init__(
        self,
        *,
        enabled_globally: bool = False,
        enabled_for: list[uuid.UUID] | None = None,
        disabled_for: list[uuid.UUID] | None = None,
        minimum_plan: Plan | None = None,
    ) -> None:
        self.enabled_globally = enabled_globally
        self.enabled_for_tenants = enabled_for or []
        self.disabled_for_tenants = disabled_for or []
        self.minimum_plan = minimum_plan


def _service(
    row: object | None,
) -> tuple[FeatureFlagService, _StubSession, fakeredis.aioredis.FakeRedis]:
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    session = _StubSession(row)
    svc = FeatureFlagService(cast(AsyncSession, session), redis)
    return svc, session, redis


async def test_globally_enabled_flag() -> None:
    svc, _, _ = _service(_Row(enabled_globally=True))
    assert await svc.is_enabled("chat", TENANT_A, Plan.TRIAL) is True


async def test_disabled_list_wins_over_global() -> None:
    svc, _, _ = _service(_Row(enabled_globally=True, disabled_for=[TENANT_A]))
    assert await svc.is_enabled("chat", TENANT_A, Plan.AGENCY) is False
    assert await svc.is_enabled("chat", TENANT_B, Plan.TRIAL) is True


async def test_tenant_allowlist() -> None:
    svc, _, _ = _service(_Row(enabled_for=[TENANT_A]))
    assert await svc.is_enabled("beta", TENANT_A, Plan.TRIAL) is True
    assert await svc.is_enabled("beta", TENANT_B, Plan.TRIAL) is False


async def test_minimum_plan_gate() -> None:
    svc, _, _ = _service(_Row(minimum_plan=Plan.GROWTH))
    assert await svc.is_enabled("ads", TENANT_A, Plan.STARTER) is False
    assert await svc.is_enabled("ads", TENANT_A, Plan.GROWTH) is True
    assert await svc.is_enabled("ads", TENANT_A, Plan.AGENCY) is True


async def test_unknown_flag_is_false() -> None:
    svc, _, _ = _service(None)
    assert await svc.is_enabled("nope", TENANT_A, Plan.AGENCY) is False


async def test_cache_prevents_second_db_hit_and_invalidate_clears() -> None:
    svc, session, redis = _service(_Row(enabled_globally=True))
    await svc.is_enabled("cached", TENANT_A, Plan.TRIAL)
    await svc.is_enabled("cached", TENANT_A, Plan.TRIAL)
    assert session.scalar_calls == 1  # second call served from Redis

    ttl = await redis.ttl("ff:cached")
    assert 0 < ttl <= CACHE_TTL_SECONDS

    await svc.invalidate("cached")
    await svc.is_enabled("cached", TENANT_A, Plan.TRIAL)
    assert session.scalar_calls == 2  # cache was cleared


async def test_negative_cache_for_missing_flag() -> None:
    svc, session, _ = _service(None)
    await svc.is_enabled("ghost", TENANT_A, Plan.TRIAL)
    await svc.is_enabled("ghost", TENANT_A, Plan.TRIAL)
    assert session.scalar_calls == 1  # miss is cached too


async def test_cached_payload_is_plain_json() -> None:
    """The cache must hold JSON (portable across processes), not pickles."""
    svc, _, redis = _service(_Row(enabled_globally=True))
    await svc.is_enabled("json-check", TENANT_A, Plan.TRIAL)
    raw = await redis.get("ff:json-check")
    assert raw is not None
    parsed = json.loads(raw)
    assert parsed["missing"] is False
    assert parsed["flag"]["enabled_globally"] is True
