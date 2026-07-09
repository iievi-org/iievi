"""Alembic environment — async engine, URL from the environment (Doppler).

Migrations run as the database OWNER role (DATABASE_URL_OWNER when set,
else DATABASE_URL): they create tables, RLS policies, and indexes. The
application role (iievi_app) never runs DDL.
"""

import asyncio
import logging
import os
import time
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import ALL models so autogenerate sees the complete schema.
from app.db.models import Base

logger = logging.getLogger("alembic.env")

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

database_url = os.environ.get("DATABASE_URL_OWNER") or os.environ.get("DATABASE_URL")
if not database_url:
    msg = "DATABASE_URL is not set — run migrations via Doppler: make migrate"
    raise RuntimeError(msg)
config.set_main_option("sqlalchemy.url", database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit SQL to stdout without a live connection."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# Objects that exist ONLY in hand-written SQL migrations (CONCURRENTLY
# indexes, expression indexes). Autogenerate must never try to drop them.
_SQL_ONLY_NAMES = {
    "ix_posts_scheduled_at_pending",
    "ix_leads_tenant_last_inbound",
    "ix_conversations_lead_created",
    "ix_business_profiles_services_gin",
    "uq_users_email_global",
}


def _include_object(
    obj: object, name: str | None, type_: str, reflected: bool, compare_to: object
) -> bool:
    if type_ == "index" and name in _SQL_ONLY_NAMES:
        return False
    return True


def _run_sync_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_object=_include_object,
    )
    started = time.perf_counter()
    logger.info("migration run starting")
    with context.begin_transaction():
        context.run_migrations()
    logger.info("migration run finished in %.2fs", time.perf_counter() - started)


async def run_migrations_online() -> None:
    """Run migrations over the async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(_run_sync_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
