"""DB-backed gateway DoD tests: registration/login flow, tenant isolation
through a real endpoint, audit immutability, atomic usage enforcement.

Requires the live local PostgreSQL (make up) with migrations at head.
"""

import os
import uuid

import fakeredis.aioredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core import ratelimit, security
from app.db.base import with_tenant_scope
from app.db.models import Plan
from app.main import app
from app.modules.billing.usage_service import check_and_increment_usage

OWNER_URL = os.environ.get(
    "RLS_TEST_OWNER_URL", "postgresql+asyncpg://iievi:iievi@localhost:5432/iievi"
)
APP_URL = os.environ.get(
    "RLS_TEST_APP_URL",
    "postgresql+asyncpg://iievi_app:iievi_app_dev_only@localhost:5432/iievi",
)


async def _db_available() -> bool:
    engine = create_async_engine(OWNER_URL)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001
        return False
    finally:
        await engine.dispose()


@pytest.fixture(autouse=True)
async def _require_db(monkeypatch: pytest.MonkeyPatch) -> None:
    if not await _db_available():
        if os.environ.get("REQUIRE_RLS_TESTS") == "1":
            pytest.fail("gateway DB tests REQUIRED in CI but PostgreSQL is unreachable")
        pytest.skip("PostgreSQL unreachable — start it with `make up`")
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(security, "get_redis", lambda: fake)
    monkeypatch.setattr(ratelimit, "get_redis", lambda: fake)
    # The shared aioredis client is lru_cached and bound to the event loop
    # that created it; every test gets a fresh TestClient loop, so reset it.
    from app.core import redis as core_redis

    core_redis.get_redis.cache_clear()


@pytest.fixture()
def client() -> "TestClient":
    # Context-managed: ONE portal (event loop) for every request in a test.
    # Without it TestClient spins a new loop per request and the lru_cached
    # engine/redis clients cross loops.
    with TestClient(app) as c:
        yield c


def _register(client: TestClient, email: str) -> tuple[str, dict[str, str]]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "business_name": "Gateway Test Co",
            "full_name": "Gateway Tester",
            "email": email,
            "password": "a-strong-password-123",
        },
    )
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]
    return token, {"Authorization": f"Bearer {token}"}


async def _cleanup_tenant_by_email(email: str) -> None:
    engine = create_async_engine(OWNER_URL)
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "DELETE FROM tenants WHERE id IN "
                "(SELECT tenant_id FROM users WHERE lower(email) = lower(:email))"
            ),
            {"email": email},
        )
    await engine.dispose()


async def test_register_login_capabilities_flow(client: TestClient) -> None:
    email = f"flow-{uuid.uuid4().hex[:10]}@iievi-tests.com"
    try:
        token, headers = _register(client, email)

        # csrf cookie is set and JS-readable (not HttpOnly)
        assert client.cookies.get("csrf_token")

        # duplicate registration is rejected
        dup = client.post(
            "/api/v1/auth/register",
            json={
                "business_name": "Dup Co",
                "full_name": "Dup",
                "email": email,
                "password": "another-strong-pass-1",
            },
        )
        assert dup.status_code == 401

        # wrong password → 401 with the same envelope
        bad = client.post(
            "/api/v1/auth/login", json={"email": email, "password": "wrong-password-x"}
        )
        assert bad.status_code == 401

        # real login works
        good = client.post(
            "/api/v1/auth/login", json={"email": email, "password": "a-strong-password-123"}
        )
        assert good.status_code == 200

        # capabilities: trial plan, zero usage, correct limits
        caps = client.get("/api/v1/billing/capabilities", headers=headers)
        assert caps.status_code == 200, caps.text
        body = caps.json()
        assert body["plan"] == "trial"
        assert body["is_suspended"] is False
        assert body["can_generate_posts"] is True
        assert body["can_create_ads"] is False  # trial < growth
        assert body["usage"]["posts_generated"] == 0
        assert body["usage"]["limits"]["posts_generated"] == 10
    finally:
        await _cleanup_tenant_by_email(email)


async def test_tenant_a_cannot_see_tenant_b_usage(client: TestClient) -> None:
    """DoD: a valid JWT for Tenant A cannot access Tenant B's data."""
    email_a = f"iso-a-{uuid.uuid4().hex[:10]}@iievi-tests.com"
    email_b = f"iso-b-{uuid.uuid4().hex[:10]}@iievi-tests.com"
    try:
        token_a, headers_a = _register(client, email_a)
        token_b, headers_b = _register(client, email_b)

        # Tenant B generates usage (seed via owner into B's monthly_usage)
        import jwt as pyjwt

        from app.core.config import settings

        tid_b = pyjwt.decode(token_b, settings.jwt_secret, algorithms=["HS256"])["tid"]
        engine = create_async_engine(OWNER_URL)
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO monthly_usage (tenant_id, month, posts_generated) "
                    "VALUES (:tid, date_trunc('month', now())::date, 7)"
                ),
                {"tid": uuid.UUID(tid_b)},
            )
        await engine.dispose()

        # B sees its usage; A sees zero — no bleed-through
        caps_b = client.get("/api/v1/billing/capabilities", headers=headers_b).json()
        caps_a = client.get("/api/v1/billing/capabilities", headers=headers_a).json()
        assert caps_b["usage"]["posts_generated"] == 7
        assert caps_a["usage"]["posts_generated"] == 0
    finally:
        await _cleanup_tenant_by_email(email_a)
        await _cleanup_tenant_by_email(email_b)


async def test_registration_writes_audit_log_and_trigger_blocks_delete(
    client: TestClient,
) -> None:
    """DoD: CREATE writes an audit row; the trigger blocks DELETE — even as owner."""
    email = f"audit-{uuid.uuid4().hex[:10]}@iievi-tests.com"
    engine = create_async_engine(OWNER_URL)
    try:
        _register(client, email)
        async with engine.connect() as conn:
            audit_row = (
                await conn.execute(
                    text(
                        "SELECT a.id FROM audit_logs a JOIN users u "
                        "ON u.tenant_id = a.tenant_id "
                        "WHERE lower(u.email) = lower(:email) "
                        "AND a.action = 'create' AND a.resource_type = 'Tenant'"
                    ),
                    {"email": email},
                )
            ).first()
        assert audit_row is not None, "registration must write a CREATE audit record"

        with pytest.raises(DBAPIError, match="append-only"):
            async with engine.begin() as conn:
                await conn.execute(
                    text("DELETE FROM audit_logs WHERE id = :id"), {"id": audit_row.id}
                )
        with pytest.raises(DBAPIError, match="append-only"):
            async with engine.begin() as conn:
                await conn.execute(
                    text("UPDATE audit_logs SET resource_type = 'Hacked' WHERE id = :id"),
                    {"id": audit_row.id},
                )
    finally:
        await _cleanup_tenant_by_email(email)
        await engine.dispose()


async def test_usage_conditional_update_stops_exactly_at_limit() -> None:
    """The conditional UPDATE allows exactly `limit` increments, then refuses."""
    owner = create_async_engine(OWNER_URL)
    app_engine = create_async_engine(APP_URL)
    tenant_id = uuid.uuid4()
    try:
        async with owner.begin() as conn:
            await conn.execute(
                text("INSERT INTO tenants (id, name, plan) VALUES (:tid, 'Usage Test', 'trial')"),
                {"tid": tenant_id},
            )
        async with AsyncSession(app_engine) as session:
            async with with_tenant_scope(session, tenant_id):
                allowed_count = 0
                for _ in range(12):  # trial images_generated limit is 5
                    decision = await check_and_increment_usage(
                        tenant_id, "images_generated", Plan.TRIAL, session
                    )
                    if decision.allowed:
                        allowed_count += 1
                assert allowed_count == 5
                final = await check_and_increment_usage(
                    tenant_id, "images_generated", Plan.TRIAL, session
                )
                assert final.allowed is False
                assert final.current == 5
                # Agency bypasses entirely
                agency = await check_and_increment_usage(
                    tenant_id, "images_generated", Plan.AGENCY, session
                )
                assert agency.allowed is True and agency.limit is None
            await session.commit()
    finally:
        async with owner.begin() as conn:
            await conn.execute(text("DELETE FROM tenants WHERE id = :tid"), {"tid": tenant_id})
        await owner.dispose()
        await app_engine.dispose()
