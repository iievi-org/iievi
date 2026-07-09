"""performance_indexes — hand-written CONCURRENTLY indexes for hot queries.

CREATE INDEX CONCURRENTLY cannot run inside a transaction, hence the
autocommit block. Safe to run against a live database.

Each index documents the query pattern it serves.

Revision ID: b2d4f6a8c0e2
Revises: a1c3b5d7e9f0
Create Date: 2026-07-09
"""

from collections.abc import Sequence

from alembic import op

revision: str = "b2d4f6a8c0e2"
down_revision: str | None = "a1c3b5d7e9f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INDEXES: tuple[tuple[str, str], ...] = (
    (
        # Publishing scheduler: "SELECT ... FROM posts WHERE status='scheduled'
        # AND scheduled_at <= now()" — partial index keeps it tiny.
        "ix_posts_scheduled_at_pending",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_posts_scheduled_at_pending "
        "ON posts (scheduled_at) WHERE status = 'scheduled'",
    ),
    (
        # WhatsApp 24-hour window check: latest inbound message per tenant's leads.
        "ix_leads_tenant_last_inbound",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_leads_tenant_last_inbound "
        "ON leads (tenant_id, last_inbound_at)",
    ),
    (
        # Conversation history fetch: messages for a lead in chronological order.
        "ix_conversations_lead_created",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_conversations_lead_created "
        "ON conversations (lead_id, created_at)",
    ),
    (
        # Service search inside the AI grounding profile (JSONB containment).
        "ix_business_profiles_services_gin",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_business_profiles_services_gin "
        "ON business_profiles USING gin (services)",
    ),
)


def upgrade() -> None:
    with op.get_context().autocommit_block():
        for _name, ddl in INDEXES:
            op.execute(ddl)


def downgrade() -> None:
    with op.get_context().autocommit_block():
        for name, _ddl in INDEXES:
            op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {name}")
