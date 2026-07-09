"""Async engine, session factory, and tenant scoping.

════════════════════════════════════════════════════════════════════════════
RULE (NOT OPTIONAL): every database operation on a tenant-scoped table must
run inside `with_tenant_scope(session, tenant_id)`. The context manager sets
the `app.current_tenant_id` session variable that every RLS policy filters
on. Without it, RLS returns zero rows — queries silently see nothing. Never
work around that by connecting as a privileged role; fix the call site.
════════════════════════════════════════════════════════════════════════════

The engine connects through DATABASE_URL_POOLED (Neon PgBouncer) in
production and falls back to DATABASE_URL locally. Queries slower than
SLOW_QUERY_THRESHOLD_MS log a WARNING with the SQL and parameters.
"""

import logging
import os
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache

from sqlalchemy import event, text
from sqlalchemy.engine import Connection, ExecutionContext
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings

logger = logging.getLogger(__name__)

SLOW_QUERY_THRESHOLD_MS = 500


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    """Process-wide async engine (created on first use, never at import).

    Under pytest, pooling is disabled: TestClient portals and pytest-asyncio
    run on different event loops, and a pooled asyncpg connection is bound to
    the loop that created it. NullPool opens/closes per operation instead.
    """
    if "PYTEST_VERSION" in os.environ:
        engine = create_async_engine(settings.pooled_database_url, poolclass=NullPool)
    else:
        engine = create_async_engine(
            settings.pooled_database_url,
            pool_size=10,
            max_overflow=5,
            pool_timeout=30,
            pool_pre_ping=True,
        )
    _install_slow_query_logging(engine)
    return engine


def _install_slow_query_logging(engine: AsyncEngine) -> None:
    """WARN on any query exceeding SLOW_QUERY_THRESHOLD_MS with SQL + params."""

    @event.listens_for(engine.sync_engine, "before_cursor_execute")
    def _start_timer(  # noqa: ANN202
        conn: Connection,
        cursor: object,
        statement: str,
        parameters: object,
        context: ExecutionContext | None,
        executemany: bool,
    ) -> None:
        conn.info["query_start"] = time.perf_counter()

    @event.listens_for(engine.sync_engine, "after_cursor_execute")
    def _check_duration(  # noqa: ANN202
        conn: Connection,
        cursor: object,
        statement: str,
        parameters: object,
        context: ExecutionContext | None,
        executemany: bool,
    ) -> None:
        started = conn.info.pop("query_start", None)
        if started is None:
            return
        elapsed_ms = (time.perf_counter() - started) * 1000
        if elapsed_ms >= SLOW_QUERY_THRESHOLD_MS:
            logger.warning(
                "slow query",
                extra={
                    "duration_ms": round(elapsed_ms, 1),
                    "sql": statement,
                    "params": repr(parameters)[:500],
                },
            )


@lru_cache(maxsize=1)
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Session factory bound to the pooled engine."""
    return async_sessionmaker(
        get_engine(),
        expire_on_commit=False,
        autoflush=False,
    )


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: yields a session, commits on clean exit, rolls back on error."""
    session = get_session_factory()()
    try:
        yield session
        await session.commit()
    except BaseException:
        await session.rollback()
        raise
    finally:
        await session.close()


@asynccontextmanager
async def with_tenant_scope(
    session: AsyncSession, tenant_id: uuid.UUID
) -> AsyncIterator[AsyncSession]:
    """Set the RLS tenant context for the current transaction.

    `set_config(..., true)` is transaction-local: the setting evaporates on
    commit/rollback, so a pooled connection can never leak one tenant's
    context to the next request.
    """
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
        {"tenant_id": str(tenant_id)},
    )
    yield session
