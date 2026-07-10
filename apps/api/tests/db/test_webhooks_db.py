"""Webhook deduplication against live PostgreSQL.

DoD: a duplicate webhook event (same platform_event_id delivered twice)
processes only once — the second claim returns None. This is the ON CONFLICT
insert-before-process contract, which only PostgreSQL can prove.

Skips locally when PostgreSQL is unreachable (make up to run); CI runs it.
"""

import os
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.modules.webhooks.service import (
    claim_webhook_event,
    mark_event_failed,
    mark_event_processed,
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
async def session():  # noqa: ANN201
    if not await _reachable(APP_URL):
        pytest.skip("PostgreSQL unreachable — run `make up` for DB tests")
    engine = create_async_engine(APP_URL, poolclass=NullPool)
    async with AsyncSession(engine) as db_session:
        yield db_session
    await engine.dispose()


async def test_duplicate_event_claims_only_once(session: AsyncSession) -> None:
    """DoD: same platform_event_id twice → second claim is a no-op."""
    event_key = f"test:{uuid.uuid4()}"
    first = await claim_webhook_event(
        session,
        platform_event_id=event_key,
        platform="meta",
        event_type="page",
        payload={"n": 1},
    )
    second = await claim_webhook_event(
        session,
        platform_event_id=event_key,
        platform="meta",
        event_type="page",
        payload={"n": 2},
    )
    assert first is not None
    assert second is None

    count = await session.scalar(
        text("SELECT count(*) FROM webhook_events WHERE platform_event_id = :k"),
        {"k": event_key},
    )
    assert count == 1

    # cleanup
    await session.execute(
        text("DELETE FROM webhook_events WHERE platform_event_id = :k"), {"k": event_key}
    )
    await session.commit()


async def test_event_status_lifecycle(session: AsyncSession) -> None:
    event_key = f"test:{uuid.uuid4()}"
    event_id = await claim_webhook_event(
        session,
        platform_event_id=event_key,
        platform="stripe",
        event_type="invoice.payment_succeeded",
    )
    assert event_id is not None

    await mark_event_processed(session, event_id)
    status = await session.scalar(
        text("SELECT idempotency_status FROM webhook_events WHERE id = :id"),
        {"id": event_id},
    )
    assert status == "processed"

    await mark_event_failed(session, event_id)
    status = await session.scalar(
        text("SELECT idempotency_status FROM webhook_events WHERE id = :id"),
        {"id": event_id},
    )
    assert status == "failed"

    await session.execute(text("DELETE FROM webhook_events WHERE id = :id"), {"id": event_id})
    await session.commit()
