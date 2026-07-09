-- IIEVI database bootstrap — applied automatically on first container start.
-- Ensures every developer's local database enforces Row Level Security from
-- day one, exactly like production (Neon).
--
-- Tenant isolation model:
--   * The API connects as `iievi_app`, a NON-superuser role WITHOUT BYPASSRLS.
--   * At the start of every authenticated request the API runs:
--       SELECT set_config('app.current_tenant_id', '<tenant-uuid>', true);
--   * Every tenant-scoped table (created by Alembic migrations in later
--     phases) attaches the policy:
--       USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
--   * platform_identifiers deliberately has NO RLS (webhook routing happens
--     before tenant context exists).

-- Application role: no superuser, no BYPASSRLS — RLS actually applies to it.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'iievi_app') THEN
        CREATE ROLE iievi_app LOGIN PASSWORD 'iievi_app_dev_only' NOSUPERUSER NOBYPASSRLS;
    END IF;
END
$$;

GRANT CONNECT ON DATABASE iievi TO iievi_app;
GRANT USAGE, CREATE ON SCHEMA public TO iievi_app;

-- Future tables created by migrations are readable/writable by the app role;
-- RLS policies (attached per-table in migrations) constrain which rows.
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO iievi_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO iievi_app;

-- Helper used by RLS policies and by tests: returns the tenant from the
-- session variable, or NULL when no tenant context is set (which makes every
-- tenant-scoped policy deny by default).
CREATE OR REPLACE FUNCTION current_tenant_id() RETURNS uuid
LANGUAGE sql STABLE
AS $$
    SELECT NULLIF(current_setting('app.current_tenant_id', true), '')::uuid;
$$;

COMMENT ON FUNCTION current_tenant_id() IS
    'Tenant from app.current_tenant_id session variable; NULL denies all rows under RLS.';
