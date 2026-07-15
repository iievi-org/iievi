"""Shared database plumbing for Celery tasks.

Workers are long-lived prefork processes with no shared event loop, so every
task runs its async body via asyncio.run and opens a NullPool engine for the
duration of that body — a pooled asyncpg connection is bound to the loop that
created it and cannot outlive asyncio.run.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings


@asynccontextmanager
async def worker_session() -> AsyncIterator[AsyncSession]:
    """One engine + session for a single task body; disposed on exit."""
    engine = create_async_engine(settings.pooled_database_url, poolclass=NullPool)
    try:
        async with AsyncSession(engine) as session:
            yield session
    finally:
        await engine.dispose()
