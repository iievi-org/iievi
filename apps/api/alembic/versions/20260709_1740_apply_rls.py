"""apply_rls — enable Row Level Security on every tenant-scoped table.

Policy expression: tenant_id = NULLIF(current_setting('app.current_tenant_id',
true), '')::uuid. The `true` (missing_ok) argument makes an UNSET session
variable evaluate to NULL — the comparison then matches no rows, so a session
without tenant context sees NOTHING rather than erroring.

Deliberately WITHOUT RLS: platform_identifiers, webhook_events (webhook
routing happens before tenant context exists), audit_logs (platform-level
compliance record), feature_flags (global).

Revision ID: a1c3b5d7e9f0
Revises: f68637d74f44
Create Date: 2026-07-09
"""

from collections.abc import Sequence

from alembic import op

revision: str = "a1c3b5d7e9f0"
down_revision: str | None = "f68637d74f44"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Keep in sync with app.db.models.TENANT_SCOPED_TABLES — test_rls.py asserts
# pg_tables.rowsecurity for every entry there.
TENANT_SCOPED_TABLES: tuple[str, ...] = (
    "users",
    "business_profiles",
    "customer_personas",
    "competitor_analysis",
    "marketing_configs",
    "brand_kits",
    "api_credentials",
    "leads",
    "conversations",
    "posts",
    "subscriptions",
    "monthly_usage",
    "notification_preferences",
)

POLICY_EXPR = "tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid"


def upgrade() -> None:
    for table in TENANT_SCOPED_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {table} "
            f"FOR ALL USING ({POLICY_EXPR}) WITH CHECK ({POLICY_EXPR})"
        )


def downgrade() -> None:
    for table in TENANT_SCOPED_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
