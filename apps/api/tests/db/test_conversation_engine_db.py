"""DB-backed conversation-engine DoD (Prompt 7): state-transition audit trail,
outreach cancellation, handoff side effects, and the notifications API.

Requires the live local PostgreSQL (make up) with migrations at head.
"""

import os
import uuid
from types import SimpleNamespace

import fakeredis.aioredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core import ratelimit, security
from app.db.base import with_tenant_scope
from app.db.models import ConversationState
from app.main import app
from app.modules.ai.context_service import TenantAIContext
from app.modules.conversations import booking_service, outreach_service
from app.modules.conversations import state_machine as sm
from app.modules.notifications import service as notif_service
from app.modules.notifications import whatsapp_channel

OWNER_URL = os.environ.get(
    "RLS_TEST_OWNER_URL", "postgresql+asyncpg://iievi:iievi@localhost:5432/iievi"
)
# App role (NOBYPASSRLS) — used where production code relies on RLS tenant scoping.
APP_URL = os.environ.get(
    "RLS_TEST_APP_URL",
    "postgresql+asyncpg://iievi_app:iievi_app_dev_only@localhost:5432/iievi",
)


def _csrf(client: TestClient) -> dict[str, str]:
    """The X-CSRF-Token header for a state-changing request (synchronizer token)."""
    return {"X-CSRF-Token": client.cookies.get("csrf_token", "")}


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
            pytest.fail("conversation-engine DB tests REQUIRED in CI but PostgreSQL is unreachable")
        pytest.skip("PostgreSQL unreachable — start it with `make up`")
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(security, "get_redis", lambda: fake)
    monkeypatch.setattr(ratelimit, "get_redis", lambda: fake)


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


def _register(client: TestClient, email: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "business_name": "Engine Test Co",
            "full_name": "Engine Tester",
            "email": email,
            "password": "a-strong-password-123",
        },
    )
    assert response.status_code == 201, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def _tenant_and_owner(email: str) -> tuple[uuid.UUID, uuid.UUID]:
    engine = create_async_engine(OWNER_URL)
    try:
        async with AsyncSession(engine) as session:
            row = (
                await session.execute(
                    text("SELECT tenant_id, id FROM users WHERE lower(email) = lower(:email)"),
                    {"email": email},
                )
            ).first()
        assert row is not None
        return uuid.UUID(str(row[0])), uuid.UUID(str(row[1]))
    finally:
        await engine.dispose()


async def _insert_lead(tenant_id: uuid.UUID, *, state: str = "new") -> uuid.UUID:
    engine = create_async_engine(OWNER_URL)
    try:
        async with engine.begin() as conn:
            row = await conn.execute(
                text(
                    "INSERT INTO leads (tenant_id, source, status, platform, platform_id, "
                    "conversation_state, name) VALUES "
                    "(:t, 'whatsapp', 'new', 'whatsapp', :pid, :state, 'Riya') RETURNING id"
                ),
                {"t": tenant_id, "pid": f"lead-{uuid.uuid4().hex[:8]}", "state": state},
            )
            return uuid.UUID(str(row.scalar()))
    finally:
        await engine.dispose()


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


def _sig(**kw: bool) -> SimpleNamespace:
    base = {
        "lead_ready": False,
        "requested_human": False,
        "objection_expressed": False,
        "all_questions_answered": False,
    }
    base.update(kw)
    return SimpleNamespace(**base)


async def test_record_transition_writes_system_event_and_audit(client: TestClient) -> None:
    email = f"tx-{uuid.uuid4().hex[:8]}@iievi-tests.com"
    _register(client, email)
    tenant_id, _owner = await _tenant_and_owner(email)
    lead_id = await _insert_lead(tenant_id, state="new")
    engine = create_async_engine(OWNER_URL)
    try:
        async with AsyncSession(engine) as session, with_tenant_scope(session, tenant_id):
            await sm.record_transition(
                session,
                lead_id=lead_id,
                tenant_id=tenant_id,
                from_state=ConversationState.NEW,
                to_state=ConversationState.GREETED,
                signals=_sig(),
            )
            await session.commit()

        async with AsyncSession(engine) as session:
            event = (
                await session.execute(
                    text(
                        "SELECT content FROM conversations WHERE lead_id = :l AND role = 'system'"
                    ),
                    {"l": lead_id},
                )
            ).scalar()
            assert event is not None and "new -> greeted" in event

            lead = (
                await session.execute(
                    text("SELECT conversation_state, status FROM leads WHERE id = :l"),
                    {"l": lead_id},
                )
            ).first()
            assert lead is not None
            assert str(lead[0]) == "greeted"  # AI state advanced
            assert str(lead[1]) == "engaged"  # CRM status mapped

            audit_count = (
                await session.execute(
                    text(
                        "SELECT count(*) FROM audit_logs WHERE "
                        "resource_type = 'lead_conversation_state' AND resource_id = :l"
                    ),
                    {"l": lead_id},
                )
            ).scalar()
            assert int(audit_count or 0) >= 1
    finally:
        await engine.dispose()
        await _cleanup(email)


async def test_outreach_enqueue_then_cancel_on_response(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    email = f"out-{uuid.uuid4().hex[:8]}@iievi-tests.com"
    _register(client, email)
    tenant_id, _owner = await _tenant_and_owner(email)
    lead_id = await _insert_lead(tenant_id, state="new")

    # Fake the broker: apply_async returns a task id, revoke records the id.
    from app.worker import outreach_worker

    for idx, task in enumerate(
        (
            outreach_worker.send_initial_contact,
            outreach_worker.send_followup_one,
            outreach_worker.send_followup_two,
        )
    ):
        monkeypatch.setattr(
            task, "apply_async", lambda *a, _i=idx, **k: SimpleNamespace(id=f"task-{_i}")
        )
    revoked: list[str] = []
    monkeypatch.setattr(
        outreach_service.celery_app.control, "revoke", lambda tid: revoked.append(tid)
    )

    engine = create_async_engine(OWNER_URL)
    try:
        async with AsyncSession(engine) as session, with_tenant_scope(session, tenant_id):
            ids = await outreach_service.enqueue_outreach_sequence(
                session, tenant_id=tenant_id, lead_id=lead_id
            )
            await session.commit()
        assert ids == ["task-0", "task-1", "task-2"]

        # Stored on the lead
        async with AsyncSession(engine) as session:
            stored = (
                await session.execute(
                    text("SELECT follow_up_task_ids FROM leads WHERE id = :l"), {"l": lead_id}
                )
            ).scalar()
            assert stored == ["task-0", "task-1", "task-2"]

        # Lead responds -> cancel revokes all three and clears the field
        async with AsyncSession(engine) as session, with_tenant_scope(session, tenant_id):
            count = await outreach_service.cancel_outreach_sequence(
                session, tenant_id=tenant_id, lead_id=lead_id
            )
            await session.commit()
        assert count == 3
        assert sorted(revoked) == ["task-0", "task-1", "task-2"]

        async with AsyncSession(engine) as session:
            cleared = (
                await session.execute(
                    text("SELECT follow_up_task_ids FROM leads WHERE id = :l"), {"l": lead_id}
                )
            ).scalar()
            assert cleared == []
    finally:
        await engine.dispose()
        await _cleanup(email)


async def test_handoff_sends_email_and_whatsapp(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    email = f"ho-{uuid.uuid4().hex[:8]}@iievi-tests.com"
    _register(client, email)
    tenant_id, owner_id = await _tenant_and_owner(email)
    lead_id = await _insert_lead(tenant_id, state="qualifying")

    # Owner has a notification WhatsApp number configured.
    engine = create_async_engine(OWNER_URL)
    async with engine.begin() as conn:
        await conn.execute(
            text("UPDATE users SET notification_whatsapp = '+919812345678' WHERE id = :u"),
            {"u": owner_id},
        )
        await conn.execute(
            text(
                "INSERT INTO conversations (tenant_id, lead_id, role, content) "
                "VALUES (:t, :l, 'lead', 'Deep clean this weekend - can I talk to a person?')"
            ),
            {"t": tenant_id, "l": lead_id},
        )

    sent_emails: list[object] = []
    sent_whatsapp: list[tuple[str, str]] = []

    async def _fake_send_email(template: object) -> str:
        sent_emails.append(template)
        return "email-id"

    async def _fake_owner_wa(to_phone: str, message: str) -> bool:
        sent_whatsapp.append((to_phone, message))
        return True

    from app.modules.notifications import email_service

    monkeypatch.setattr(email_service, "send_email", _fake_send_email)
    monkeypatch.setattr(whatsapp_channel, "send_owner_whatsapp", _fake_owner_wa)

    context = TenantAIContext(
        tenant_id=str(tenant_id), business_name="Sparkle Clean", category="home_cleaning"
    )
    # Run through the APP role so RLS scopes _load_owner to THIS tenant (the real
    # production path — workers connect as iievi_app, not the superuser).
    app_engine = create_async_engine(APP_URL)
    try:
        async with AsyncSession(app_engine) as session:
            # api_key=None -> summary uses the transcript tail, no real Gemini call
            await booking_service.handle_handoff(
                session, tenant_id=tenant_id, lead_id=lead_id, context=context, api_key=None
            )

        async with AsyncSession(engine) as session:
            manual = (
                await session.execute(
                    text("SELECT manual_mode FROM leads WHERE id = :l"), {"l": lead_id}
                )
            ).scalar()
            assert manual is True
            notif = (
                await session.execute(
                    text("SELECT type FROM notifications WHERE tenant_id = :t AND user_id = :u"),
                    {"t": tenant_id, "u": owner_id},
                )
            ).scalar()
            assert str(notif) == "ai_handoff"
        assert len(sent_emails) == 1  # LeadHandoffEmail
        assert len(sent_whatsapp) == 1 and sent_whatsapp[0][0] == "+919812345678"
    finally:
        await app_engine.dispose()
        await engine.dispose()
        await _cleanup(email)


async def test_notifications_api_list_and_mark_read(client: TestClient) -> None:
    email = f"nt-{uuid.uuid4().hex[:8]}@iievi-tests.com"
    headers = _register(client, email)
    tenant_id, owner_id = await _tenant_and_owner(email)

    from app.db.models import NotificationType

    engine = create_async_engine(OWNER_URL)
    try:
        async with AsyncSession(engine) as session, with_tenant_scope(session, tenant_id):
            await notif_service.create_notification(
                session,
                tenant_id=tenant_id,
                user_id=owner_id,
                notif_type=NotificationType.NEW_LEAD,
                title="A new lead",
                body="Riya messaged you",
                action_url="/leads/1",
            )
            await session.commit()

        listing = client.get("/api/v1/notifications", headers=headers)
        assert listing.status_code == 200, listing.text
        payload = listing.json()
        assert payload["unread"] == 1
        assert len(payload["notifications"]) == 1
        notif_id = payload["notifications"][0]["id"]

        read = client.patch(
            f"/api/v1/notifications/{notif_id}/read", headers={**headers, **_csrf(client)}
        )
        assert read.status_code == 200 and read.json()["read"] is True

        after = client.get("/api/v1/notifications", headers=headers)
        assert after.json()["unread"] == 0
    finally:
        await engine.dispose()
        await _cleanup(email)


async def test_notification_preferences_update(client: TestClient) -> None:
    email = f"pf-{uuid.uuid4().hex[:8]}@iievi-tests.com"
    headers = _register(client, email)
    try:
        response = client.patch(
            "/api/v1/users/notification-preferences",
            headers={**headers, **_csrf(client)},
            json={
                "whatsapp_enabled": False,
                "quiet_hours_start": "22:00",
                "quiet_hours_end": "07:00",
                "quiet_hours_days": [1, 2, 3, 4, 5],
                "overrides": {"new_lead": {"email": False}},
            },
        )
        assert response.status_code == 200, response.text
        assert "quiet_hours_start" in response.json()["updated"]

        # Invalid weekday rejected
        bad = client.patch(
            "/api/v1/users/notification-preferences",
            headers={**headers, **_csrf(client)},
            json={"quiet_hours_days": [0, 9]},
        )
        assert bad.status_code == 400
    finally:
        await _cleanup(email)
