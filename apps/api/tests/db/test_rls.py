"""Cross-tenant RLS isolation — the most important test in the repository.

Runs against a live PostgreSQL (local: `make up`; CI: postgres service with
migrations applied). Requires two connections:
- owner (iievi) — seeds and cleans fixtures, bypasses RLS as table owner
- app (iievi_app, NOBYPASSRLS) — the role the API uses; RLS applies

Locally the test SKIPS with a loud warning if PostgreSQL is unreachable.
In CI, REQUIRE_RLS_TESTS=1 turns that skip into a hard failure — this test
runs in CI forever, per the security spec.
"""

import os
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.db.base import with_tenant_scope
from app.db.models import TENANT_SCOPED_TABLES

OWNER_URL = os.environ.get(
    "RLS_TEST_OWNER_URL",
    "postgresql+asyncpg://iievi:iievi@localhost:5432/iievi",
)
APP_URL = os.environ.get(
    "RLS_TEST_APP_URL",
    "postgresql+asyncpg://iievi_app:iievi_app_dev_only@localhost:5432/iievi",
)


async def _reachable(url: str) -> bool:
    engine = create_async_engine(url, pool_pre_ping=True)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001 — any failure means "no database here"
        return False
    finally:
        await engine.dispose()


@pytest.fixture()
async def engines() -> tuple[AsyncEngine, AsyncEngine]:
    if not await _reachable(OWNER_URL):
        if os.environ.get("REQUIRE_RLS_TESTS") == "1":
            pytest.fail("RLS tests are REQUIRED in CI but PostgreSQL is unreachable")
        pytest.skip(
            "PostgreSQL unreachable — start it with `make up`. "
            "RLS isolation is UNVERIFIED for this run."
        )
    owner = create_async_engine(OWNER_URL)
    app = create_async_engine(APP_URL)
    yield owner, app
    await owner.dispose()
    await app.dispose()


@pytest.fixture()
async def two_tenants_with_leads(
    engines: tuple[AsyncEngine, AsyncEngine],
) -> tuple[uuid.UUID, uuid.UUID]:
    """Seed tenants A and B with leads; cascade-delete on teardown."""
    owner, _ = engines
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    async with owner.begin() as conn:
        await conn.execute(
            text("INSERT INTO tenants (id, name) VALUES (:a, 'RLS-A'), (:b, 'RLS-B')"),
            {"a": tenant_a, "b": tenant_b},
        )
        await conn.execute(
            text(
                "INSERT INTO leads (tenant_id, source, platform, platform_id, name) VALUES "
                "(:a, 'whatsapp', 'whatsapp', :pa1, 'Asha A'), "
                "(:a, 'comment', 'instagram', :pa2, 'Arjun A'), "
                "(:b, 'whatsapp', 'whatsapp', :pb1, 'Bala B')"
            ),
            {
                "a": tenant_a,
                "b": tenant_b,
                "pa1": f"wa-{tenant_a}",
                "pa2": f"ig-{tenant_a}",
                "pb1": f"wa-{tenant_b}",
            },
        )
    yield tenant_a, tenant_b
    async with owner.begin() as conn:
        await conn.execute(
            text("DELETE FROM tenants WHERE id IN (:a, :b)"),
            {"a": tenant_a, "b": tenant_b},
        )


async def test_no_session_variable_returns_zero_rows(
    engines: tuple[AsyncEngine, AsyncEngine],
    two_tenants_with_leads: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """DoD: SELECT * FROM leads without tenant context sees NOTHING."""
    _, app = engines
    async with app.connect() as conn:
        count = await conn.scalar(text("SELECT count(*) FROM leads"))
    assert count == 0


async def test_tenant_scope_sees_only_own_rows(
    engines: tuple[AsyncEngine, AsyncEngine],
    two_tenants_with_leads: tuple[uuid.UUID, uuid.UUID],
) -> None:
    tenant_a, _tenant_b = two_tenants_with_leads
    _, app = engines
    from sqlalchemy.ext.asyncio import AsyncSession

    async with AsyncSession(app) as session:
        async with with_tenant_scope(session, tenant_a):
            names = (
                (await session.execute(text("SELECT name FROM leads ORDER BY name")))
                .scalars()
                .all()
            )
    assert names == ["Arjun A", "Asha A"]  # Bala B is invisible


async def test_cross_tenant_insert_is_blocked(
    engines: tuple[AsyncEngine, AsyncEngine],
    two_tenants_with_leads: tuple[uuid.UUID, uuid.UUID],
) -> None:
    tenant_a, tenant_b = two_tenants_with_leads
    _, app = engines
    from sqlalchemy.ext.asyncio import AsyncSession

    async with AsyncSession(app) as session:
        async with with_tenant_scope(session, tenant_a):
            with pytest.raises(DBAPIError, match="row-level security"):
                await session.execute(
                    text(
                        "INSERT INTO leads (tenant_id, source, platform, platform_id) "
                        "VALUES (:b, 'manual', 'whatsapp', 'spoof-attempt')"
                    ),
                    {"b": tenant_b},
                )


async def test_every_tenant_scoped_table_has_rls_enabled(
    engines: tuple[AsyncEngine, AsyncEngine],
) -> None:
    """Catches a future migration that adds a tenant table but forgets RLS."""
    owner, _ = engines
    async with owner.connect() as conn:
        rows = (
            (
                await conn.execute(
                    text(
                        "SELECT tablename FROM pg_tables "
                        "WHERE schemaname = 'public' AND rowsecurity"
                    )
                )
            )
            .scalars()
            .all()
        )
    missing = set(TENANT_SCOPED_TABLES) - set(rows)
    assert not missing, f"tables missing RLS: {sorted(missing)}"


async def test_tenant_context_is_transaction_local(
    engines: tuple[AsyncEngine, AsyncEngine],
    two_tenants_with_leads: tuple[uuid.UUID, uuid.UUID],
) -> None:
    """set_config(..., true) must not leak across transactions on a pooled conn."""
    tenant_a, _ = two_tenants_with_leads
    _, app = engines
    from sqlalchemy.ext.asyncio import AsyncSession

    async with AsyncSession(app) as session:
        async with with_tenant_scope(session, tenant_a):
            in_scope = await session.scalar(text("SELECT count(*) FROM leads"))
        await session.commit()  # ends the transaction — context must evaporate
        after = await session.scalar(text("SELECT count(*) FROM leads"))
    assert in_scope == 2
    assert after == 0
