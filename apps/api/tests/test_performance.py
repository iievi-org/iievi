"""Performance baselines (P5.13) — checked before every release.

assemble_tenant_context targets: < 50ms on a Redis cache hit, < 200ms on a
cache miss. The cache-hit path is benchmarked here against fakeredis (an
upper bound on the real thing — fakeredis is pure Python); the cache-miss
path needs live PostgreSQL and is asserted in the db suite when available.
"""

import asyncio
import uuid

import fakeredis.aioredis
import pytest

from app.modules.ai import context_service

TENANT_ID = uuid.uuid4()

CACHE_HIT_BUDGET_S = 0.050


def test_context_cache_hit_under_50ms(benchmark: object, monkeypatch: pytest.MonkeyPatch) -> None:
    cached = context_service.TenantAIContext(
        tenant_id=str(TENANT_ID),
        business_name="Sattva Spa",
        category="salon_spa",
        services={"haircut": {"price_min_paise": 50000}},
        faqs={"q1": "We open at 9am"},
    )

    class _ExplodingSession:
        def __getattr__(self, name: str) -> object:
            raise AssertionError("cache hit must not touch the database")

    def _assemble_once() -> context_service.TenantAIContext:
        async def _run() -> context_service.TenantAIContext:
            # Fresh client per loop — fakeredis connections are loop-bound
            fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
            monkeypatch.setattr(context_service, "get_redis", lambda: fake)
            await fake.set(f"ctx:{TENANT_ID}", cached.model_dump_json())
            return await context_service.assemble_tenant_context(
                TENANT_ID,
                _ExplodingSession(),  # type: ignore[arg-type]
            )

        return asyncio.run(_run())

    result = benchmark(_assemble_once)  # type: ignore[operator]
    assert result.business_name == "Sattva Spa"

    mean_seconds = benchmark.stats.stats.mean  # type: ignore[attr-defined]
    assert mean_seconds < CACHE_HIT_BUDGET_S, (
        f"context cache hit took {mean_seconds * 1000:.1f}ms mean; "
        f"budget is {CACHE_HIT_BUDGET_S * 1000:.0f}ms"
    )
