"""P4 DoD (DB-backed): full onboarding materialisation populates the profile
tables; cross-tenant profile isolation; completeness scoring on a partial
profile — all through the real API surface.
"""

import os
import uuid

import fakeredis.aioredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core import ratelimit, security
from app.main import app

OWNER_URL = os.environ.get(
    "RLS_TEST_OWNER_URL", "postgresql+asyncpg://iievi:iievi@localhost:5432/iievi"
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
            pytest.fail("profiles DB tests REQUIRED in CI but PostgreSQL is unreachable")
        pytest.skip("PostgreSQL unreachable — start it with `make up`")
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(security, "get_redis", lambda: fake)
    monkeypatch.setattr(ratelimit, "get_redis", lambda: fake)
    from app.core import redis as core_redis
    from app.modules.onboarding import session_service

    core_redis.get_redis.cache_clear()
    from app.modules.onboarding import session_service

    monkeypatch.setattr(session_service, "get_redis", lambda: fake)

    # Onboarding persistence + hooks enqueue Celery tasks; run tests brokerless
    class _NoDelay:
        @staticmethod
        def delay(*_args: object, **_kwargs: object) -> None:
            return None

    from app.worker import tasks as worker_tasks

    monkeypatch.setattr(worker_tasks, "persist_onboarding_session", _NoDelay())
    monkeypatch.setattr(worker_tasks, "compute_nanobanana_style_prompt", _NoDelay())
    monkeypatch.setattr(worker_tasks, "register_platform_identifiers", _NoDelay())


@pytest.fixture()
def client() -> "TestClient":
    with TestClient(app) as c:
        yield c


def _register(client: TestClient, email: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "business_name": "Profile Test Co",
            "full_name": "Profile Tester",
            "email": email,
            "password": "a-strong-password-123",
        },
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def _cleanup(email: str) -> None:
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


def _drive_onboarding(client: TestClient, monkeypatch_extract: object = None) -> None:
    """Walk all 11 collection stages through the real endpoint."""
    answers = [
        "yes let's go",  # WELCOME
        "I run a home cleaning company",  # CATEGORY_SELECT
        "SparkleNest Cleaning, we serve Pune - Baner and Wakad",  # BUSINESS_INFO
        "We do deep cleaning for 2BHK at 2500 to 4500 rupees per job",  # OVERVIEW
        "Young working couples in Pune IT corridor who have no time to clean",  # AUDIENCE
        "About 40 customers a month, mostly from word of mouth and JustDial",  # EXISTING
        "UrbanCompany is the big one; we win on same-day slots and trusted staff",  # COMP
        "Teal and white, friendly and trustworthy style",  # BRAND_IDENTITY
        "Before/after photos work great, no memes please",  # CREATIVE_PREFERENCES
        "More bookings, at least 60 a month by Diwali",  # MARKETING_GOALS
        "I can reply within an hour; hand over price negotiations to me",  # LEAD_MANAGEMENT
    ]
    # First call creates the session and returns the WELCOME question
    first = client.post("/api/v1/onboarding/message", json={"message": "hi"})
    assert first.status_code == 200, first.text
    assert first.json()["stage"] == "welcome"
    for answer in answers:
        response = client.post("/api/v1/onboarding/message", json={"message": answer})
        assert response.status_code == 200, response.text
        assert response.json()["advanced"] is True, f"stuck at: {response.json()}"


async def test_full_onboarding_populates_profile_tables(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DoD: a complete 12-stage conversation populates the profile tables."""
    import json as jsonlib

    from app.modules.onboarding import extraction_service

    async def fake_complete(**kwargs: object) -> str:
        trace = str(kwargs.get("trace_name", ""))
        if "services" in trace:
            return jsonlib.dumps(
                {
                    "services": [
                        {
                            "name": "Deep cleaning 2BHK",
                            "price_min_paise": 250000,
                            "price_max_paise": 450000,
                            "unit": "per job",
                        }
                    ]
                }
            )
        if "target_audience" in trace:
            return jsonlib.dumps(
                {
                    "description": "Young working couples in the Pune IT corridor",
                    "locations": ["Baner", "Wakad"],
                    "pain_points": ["no time to clean"],
                }
            )
        return jsonlib.dumps(
            {"competitors": ["UrbanCompany"], "differentiators": ["same-day slots"]}
        )

    monkeypatch.setattr(extraction_service.ai, "complete", fake_complete)

    email = f"onb-{uuid.uuid4().hex[:10]}@iievi-tests.com"
    try:
        headers = _register(client, email)
        _drive_onboarding(client)
        # Final stage: authenticated confirm
        response = client.post(
            "/api/v1/onboarding/message", json={"message": "confirm"}, headers=headers
        )
        assert response.status_code == 200, response.text
        assert response.json()["completed"] is True

        profile = client.get("/api/v1/profiles", headers=headers).json()
        assert profile["business_profile"]["category"] == "home_cleaning"
        assert "SparkleNest" in profile["business_profile"]["business_name"]
        services = profile["business_profile"]["services"]["items"]
        assert services[0]["name"] == "Deep cleaning 2BHK"
        assert profile["customer_personas"][0]["description"].startswith("Young working")
        assert profile["competitor_analysis"][0]["competitor_name"] == "UrbanCompany"
        assert profile["marketing_config"]["goals"]["raw"].startswith("More bookings")
        assert profile["brand_kit"]["colors"]["raw"].startswith("Teal")

        completeness = client.get("/api/v1/profiles/completeness", headers=headers).json()
        # business_info+services+target_audience+brand+goals = 75; no credentials
        assert completeness["percentage"] == 75
        assert "credentials_connected" in completeness["incomplete_sections"]
        assert "nanobanana_key" in completeness["incomplete_sections"]
    finally:
        await _cleanup(email)


async def test_profile_isolated_across_tenants(client: TestClient) -> None:
    """DoD: Profile A is inaccessible when authenticated as Tenant B."""
    email_a = f"pa-{uuid.uuid4().hex[:10]}@iievi-tests.com"
    email_b = f"pb-{uuid.uuid4().hex[:10]}@iievi-tests.com"
    engine = create_async_engine(OWNER_URL)
    try:
        headers_a = _register(client, email_a)
        headers_b = _register(client, email_b)

        # Seed a profile for A directly (owner bypasses RLS)
        import jwt as pyjwt

        from app.core.config import settings

        token_a = headers_a["Authorization"].split(" ")[1]
        tid_a = pyjwt.decode(token_a, settings.jwt_secret, algorithms=["HS256"])["tid"]
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO business_profiles (tenant_id, category, business_name) "
                    "VALUES (:tid, 'plumbing', 'Secret Plumbing Co')"
                ),
                {"tid": uuid.UUID(tid_a)},
            )

        profile_a = client.get("/api/v1/profiles", headers=headers_a).json()
        profile_b = client.get("/api/v1/profiles", headers=headers_b).json()
        assert profile_a["business_profile"]["business_name"] == "Secret Plumbing Co"
        assert profile_b["business_profile"] is None  # B sees NOTHING of A
    finally:
        await _cleanup(email_a)
        await _cleanup(email_b)
        await engine.dispose()
