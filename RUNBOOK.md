# IIEVI Operations Runbook

## Database backup

- **What:** `infra/scripts/backup-db.sh` — pg_dump over Neon's DIRECT URL
  (never the PgBouncer URL), gzip, upload to the R2 bucket `R2_BACKUP_BUCKET`
  under `backups/YYYY/MM/`, log success/failure to Axiom (`module=backup`).
- **When:** daily 02:00 UTC via cron on the VPS:
  `0 2 * * * cd /srv/iievi && doppler run -- bash infra/scripts/backup-db.sh >> /var/log/iievi/backup.log 2>&1`
- **Retention:** 30 days via an R2 lifecycle rule on the bucket
  (Cloudflare dashboard → R2 → bucket → Settings → Object lifecycle →
  delete objects under `backups/` after 30 days). Set this once.
- **Monitoring:** Axiom query `module == "backup" and status == "failure"`
  should alert; also eyeball `backup.log` during incident response.

## Restore procedure (TESTED — keep it that way)

An untested backup is not a backup. Test this quarterly and after any schema
overhaul. Approximately 10 minutes.

```bash
# 1. Fetch the most recent backup from R2
aws s3 ls "s3://$R2_BACKUP_BUCKET/backups/$(date -u +%Y/%m)/" \
  --endpoint-url "https://$R2_ACCOUNT_ID.r2.cloudflarestorage.com"
aws s3 cp "s3://$R2_BACKUP_BUCKET/backups/YYYY/MM/iievi-....sql.gz" ./restore.sql.gz \
  --endpoint-url "https://$R2_ACCOUNT_ID.r2.cloudflarestorage.com"

# 2. Start a scratch PostgreSQL 16 in podman (never restore onto a live DB)
podman run -d --name iievi-restore-test -e POSTGRES_PASSWORD=restore \
  -e POSTGRES_DB=restore -p 5433:5432 docker.io/library/postgres:16

# 3. Restore
gunzip -c restore.sql.gz | podman exec -i iievi-restore-test \
  psql -U postgres -d restore

# 4. Verify — table count and spot-check row counts
podman exec iievi-restore-test psql -U postgres -d restore -c \
  "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';"
podman exec iievi-restore-test psql -U postgres -d restore -c \
  "SELECT (SELECT count(*) FROM tenants) AS tenants, (SELECT count(*) FROM leads) AS leads, (SELECT count(*) FROM posts) AS posts;"

# 5. Clean up
podman rm -f iievi-restore-test && rm restore.sql.gz
```

Verification criteria: table count matches production (19 including
alembic_version as of the initial schema), tenants/leads counts are plausible
for the backup date, and no errors during psql restore (RLS policies and
enums restore as part of the dump).

Note: the dump is taken with `--no-owner --no-privileges`, so after a restore
to a NEW production database you must re-run `infra/db/init/01-rls.sql` (app
role + grants) and re-point DATABASE_URL. RLS policies themselves are inside
the dump; the `iievi_app` role membership is not.

## Deploy rollback

`git revert` the offending commit and push to main — deploy.yml redeploys the
reverted tree (migrations are forward-only; write a new down-fixing migration
rather than running `alembic downgrade` in production).

## Token/key incidents

- Compromised JWT secret → rotate `JWT_SECRET` in Doppler prd; all sessions
  invalidate on next deploy (tokens are 15-minute anyway).
- Compromised credential key → run the re-encryption rotation
  (`app.core.security.reencrypt_credential` walk — rotation job runbook lands
  with the credentials feature phase) BEFORE removing the old key from Doppler.
