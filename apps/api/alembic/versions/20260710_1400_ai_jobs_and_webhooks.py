"""AI layer, background jobs, and webhook operations (Prompts 5 & 6).

- failed_tasks: operational record for tasks that exhausted retries (no RLS)
- leads.manual_mode: human-takeover flag the AI pipeline checks before replying
- posts.metadata + posts.ad_campaign_id: generation artifacts and ad idempotency
- onboarding_sessions.expires_at: cleanup boundary for the daily sweep

Revision ID: d4f6a8b0c2e4
Revises: 2565fc452a39
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "d4f6a8b0c2e4"
down_revision: str | None = "2565fc452a39"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "failed_tasks",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("task_id", sa.String(155), nullable=False),
        sa.Column("task_name", sa.String(255), nullable=False),
        sa.Column("queue", sa.String(64), nullable=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=True),
        sa.Column("args", JSONB, nullable=False, server_default=sa.text("'{}'")),
        sa.Column("error", sa.Text(), nullable=False),
        sa.Column("retries", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_dlq", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_failed_tasks_task_id", "failed_tasks", ["task_id"])
    op.create_index("ix_failed_tasks_created", "failed_tasks", ["created_at"])

    op.add_column(
        "leads",
        sa.Column("manual_mode", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "posts",
        sa.Column("metadata", JSONB, nullable=False, server_default=sa.text("'{}'")),
    )
    op.add_column("posts", sa.Column("ad_campaign_id", sa.String(255), nullable=True))
    op.add_column(
        "onboarding_sessions",
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.add_column(
        "webhook_events",
        sa.Column("payload", JSONB, nullable=False, server_default=sa.text("'{}'")),
    )

    # Billing webhooks arrive BEFORE tenant context exists; subscriptions is
    # RLS-scoped. Same sanctioned pattern as auth_lookup_user: a SECURITY
    # DEFINER lookup owned by the migration role, EXECUTE granted to the app.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION billing_lookup_subscription(
            p_provider text, p_subscription_id text
        )
        RETURNS TABLE(tenant_id uuid, plan plan)
        LANGUAGE sql SECURITY DEFINER STABLE
        SET search_path = public
        AS $$
            SELECT s.tenant_id, s.plan
            FROM subscriptions s
            WHERE s.provider = p_provider
              AND s.provider_subscription_id = p_subscription_id
            LIMIT 1
        $$;
        """
    )
    op.execute("REVOKE ALL ON FUNCTION billing_lookup_subscription(text, text) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION billing_lookup_subscription(text, text) TO iievi_app")


def downgrade() -> None:
    op.execute("DROP FUNCTION IF EXISTS billing_lookup_subscription(text, text)")
    op.drop_column("webhook_events", "payload")
    op.drop_column("onboarding_sessions", "expires_at")
    op.drop_column("posts", "ad_campaign_id")
    op.drop_column("posts", "metadata")
    op.drop_column("leads", "manual_mode")
    op.drop_index("ix_failed_tasks_created", table_name="failed_tasks")
    op.drop_index("ix_failed_tasks_task_id", table_name="failed_tasks")
    op.drop_table("failed_tasks")
