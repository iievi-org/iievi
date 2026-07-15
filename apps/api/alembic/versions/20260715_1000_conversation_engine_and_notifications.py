"""Conversation engine + notifications (Prompt 7).

- conversation_state enum + leads.conversation_state: the grounded AI state
  machine stage (distinct from leads.status, the CRM pipeline).
- leads.follow_up_task_ids: Celery task IDs for the active outreach sequence,
  revoked when the lead responds or a human takes over.
- business_profiles.booking_url / contact_phone / contact_email: profile-sourced
  facts the AI may surface (absence => it must not invent them).
- users.notification_whatsapp: owner's number for PLATFORM notifications.
- notification_preferences: in_app channel + quiet-hours window.
- notifications table (+ notification_type enum): in-app dashboard bell,
  tenant-scoped with RLS (kept in sync with TENANT_SCOPED_TABLES).

Revision ID: e5a7c9b1d3f6
Revises: d4f6a8b0c2e4
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "e5a7c9b1d3f6"
down_revision: str | None = "d4f6a8b0c2e4"
branch_labels: str | None = None
depends_on: str | None = None

# Same policy expression used by the apply_rls migration: an UNSET session
# variable evaluates to NULL, so a session without tenant context sees nothing.
POLICY_EXPR = "tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid"

_conversation_state = postgresql.ENUM(
    "new",
    "greeted",
    "qualifying",
    "pitch_sent",
    "booking_offered",
    "booked",
    "handed_off",
    "lost",
    name="conversation_state",
    create_type=False,
)
_notification_type = postgresql.ENUM(
    "new_lead",
    "post_published",
    "post_failed",
    "payment_failed",
    "credential_expired",
    "ai_handoff",
    "weekly_summary",
    name="notification_type",
    create_type=False,
)


def upgrade() -> None:
    # --- native enum types ---------------------------------------------------
    op.execute(
        "CREATE TYPE conversation_state AS ENUM "
        "('new','greeted','qualifying','pitch_sent','booking_offered',"
        "'booked','handed_off','lost')"
    )
    op.execute(
        "CREATE TYPE notification_type AS ENUM "
        "('new_lead','post_published','post_failed','payment_failed',"
        "'credential_expired','ai_handoff','weekly_summary')"
    )

    # --- leads: conversation state machine + outreach task tracking ----------
    op.add_column(
        "leads",
        sa.Column(
            "conversation_state",
            _conversation_state,
            nullable=False,
            server_default="new",
        ),
    )
    op.add_column(
        "leads",
        sa.Column(
            "follow_up_task_ids",
            JSONB,
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
    )
    op.create_index(
        "ix_leads_tenant_conversation_state",
        "leads",
        ["tenant_id", "conversation_state"],
    )

    # --- business_profiles: profile-sourced facts the AI may surface ---------
    op.add_column("business_profiles", sa.Column("booking_url", sa.String(1024), nullable=True))
    op.add_column("business_profiles", sa.Column("contact_phone", sa.String(32), nullable=True))
    op.add_column("business_profiles", sa.Column("contact_email", sa.String(320), nullable=True))

    # --- users: owner notification WhatsApp number ---------------------------
    op.add_column("users", sa.Column("notification_whatsapp", sa.String(32), nullable=True))

    # --- notification_preferences: in-app channel + quiet hours --------------
    op.add_column(
        "notification_preferences",
        sa.Column("in_app_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "notification_preferences",
        sa.Column("quiet_hours_start", sa.Time(), nullable=True),
    )
    op.add_column(
        "notification_preferences",
        sa.Column("quiet_hours_end", sa.Time(), nullable=True),
    )
    op.add_column(
        "notification_preferences",
        sa.Column("quiet_hours_days", JSONB, nullable=False, server_default=sa.text("'[]'")),
    )

    # --- notifications table (tenant-scoped, RLS) ----------------------------
    op.create_table(
        "notifications",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", _notification_type, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("action_url", sa.String(1024), nullable=True),
        sa.Column("read_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_notifications_tenant_id", "notifications", ["tenant_id"])
    op.create_index("ix_notifications_user_unread", "notifications", ["user_id", "read_at"])

    op.execute("ALTER TABLE notifications ENABLE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY tenant_isolation ON notifications "
        f"FOR ALL USING ({POLICY_EXPR}) WITH CHECK ({POLICY_EXPR})"
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON notifications")
    op.drop_index("ix_notifications_user_unread", table_name="notifications")
    op.drop_index("ix_notifications_tenant_id", table_name="notifications")
    op.drop_table("notifications")

    op.drop_column("notification_preferences", "quiet_hours_days")
    op.drop_column("notification_preferences", "quiet_hours_end")
    op.drop_column("notification_preferences", "quiet_hours_start")
    op.drop_column("notification_preferences", "in_app_enabled")

    op.drop_column("users", "notification_whatsapp")

    op.drop_column("business_profiles", "contact_email")
    op.drop_column("business_profiles", "contact_phone")
    op.drop_column("business_profiles", "booking_url")

    op.drop_index("ix_leads_tenant_conversation_state", table_name="leads")
    op.drop_column("leads", "follow_up_task_ids")
    op.drop_column("leads", "conversation_state")

    op.execute("DROP TYPE IF EXISTS notification_type")
    op.execute("DROP TYPE IF EXISTS conversation_state")
