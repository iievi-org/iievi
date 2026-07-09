"""gateway_auth_primitives — auth lookups, global email uniqueness, audit immutability.

1. auth_lookup_user(email) / auth_lookup_claims(user_id): SECURITY DEFINER
   functions owned by the migration (owner) role — the ONLY sanctioned way to
   read users before tenant context exists. EXECUTE granted to iievi_app.
2. Global unique index on lower(users.email): login is by email alone, so an
   email may exist in exactly one tenant.
3. audit_logs append-only trigger: UPDATE/DELETE raise, always, for every
   role. Compliance requirement — audit history cannot be rewritten.

Revision ID: c3e5a7b9d1f2
Revises: b2d4f6a8c0e2
Create Date: 2026-07-10
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c3e5a7b9d1f2"
down_revision: str | None = "b2d4f6a8c0e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- 1. SECURITY DEFINER auth lookups ---------------------------------
    op.execute(
        """
        CREATE OR REPLACE FUNCTION auth_lookup_user(p_email text)
        RETURNS TABLE(
            user_id uuid, tenant_id uuid, password_hash text, role user_role,
            is_active boolean, tenant_status tenant_status, plan plan
        )
        LANGUAGE sql SECURITY DEFINER STABLE
        SET search_path = public
        AS $$
            SELECT u.id, u.tenant_id, u.password_hash, u.role,
                   u.is_active, t.status, t.plan
            FROM users u JOIN tenants t ON t.id = u.tenant_id
            WHERE lower(u.email) = lower(p_email)
            LIMIT 1
        $$;
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION auth_lookup_claims(p_user_id uuid)
        RETURNS TABLE(
            tenant_id uuid, plan plan, role user_role,
            is_active boolean, tenant_status tenant_status
        )
        LANGUAGE sql SECURITY DEFINER STABLE
        SET search_path = public
        AS $$
            SELECT u.tenant_id, t.plan, u.role, u.is_active, t.status
            FROM users u JOIN tenants t ON t.id = u.tenant_id
            WHERE u.id = p_user_id
            LIMIT 1
        $$;
        """
    )
    op.execute("REVOKE ALL ON FUNCTION auth_lookup_user(text) FROM PUBLIC")
    op.execute("REVOKE ALL ON FUNCTION auth_lookup_claims(uuid) FROM PUBLIC")
    op.execute("GRANT EXECUTE ON FUNCTION auth_lookup_user(text) TO iievi_app")
    op.execute("GRANT EXECUTE ON FUNCTION auth_lookup_claims(uuid) TO iievi_app")

    # --- 2. Global email uniqueness (login is by email alone) -------------
    op.execute("CREATE UNIQUE INDEX uq_users_email_global ON users (lower(email))")

    # --- 3. audit_logs is append-only, enforced in the database -----------
    # The tenant FK must go first: its ON DELETE SET NULL fires an UPDATE on
    # audit rows, which the append-only trigger below would (correctly)
    # reject — making tenant deletion impossible. Audit rows are immutable
    # history; they reference tenants by bare UUID, not by live FK.
    op.execute("ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS audit_logs_tenant_id_fkey")
    op.execute(
        """
        CREATE OR REPLACE FUNCTION audit_logs_block_mutation()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'audit_logs is append-only: % is not permitted', TG_OP
                USING ERRCODE = 'raise_exception';
        END;
        $$;
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_logs_append_only
        BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION audit_logs_block_mutation();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS audit_logs_append_only ON audit_logs")
    op.execute("DROP FUNCTION IF EXISTS audit_logs_block_mutation()")
    op.execute("DROP INDEX IF EXISTS uq_users_email_global")
    op.execute("DROP FUNCTION IF EXISTS auth_lookup_claims(uuid)")
    op.execute("DROP FUNCTION IF EXISTS auth_lookup_user(text)")
