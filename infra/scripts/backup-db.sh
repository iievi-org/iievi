#!/usr/bin/env bash
# IIEVI daily database backup — runs on the VPS under cron via Doppler:
#   0 2 * * * cd /srv/iievi && doppler run -- bash infra/scripts/backup-db.sh >> /var/log/iievi/backup.log 2>&1
#
# Required environment (Doppler prd config):
#   DATABASE_URL_DIRECT  — Neon DIRECT connection (bypasses PgBouncer; pg_dump
#                          cannot run through transaction-mode pooling)
#   R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BACKUP_BUCKET
#   AXIOM_TOKEN, AXIOM_DATASET (optional — logs success/failure to Axiom)
#
# Retention: objects are uploaded under backups/YYYY/MM/; a bucket lifecycle
# rule on R2_BACKUP_BUCKET deletes objects older than 30 days (set once in the
# Cloudflare dashboard — documented in RUNBOOK.md).

set -euo pipefail

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
PREFIX="backups/$(date -u +%Y/%m)"
FILE="iievi-${STAMP}.sql.gz"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

log_axiom() {
    local status="$1" detail="$2"
    [[ -z "${AXIOM_TOKEN:-}" ]] && return 0
    curl -fsS -X POST "https://api.axiom.co/v1/datasets/${AXIOM_DATASET:-iievi-api}/ingest" \
        -H "Authorization: Bearer ${AXIOM_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "[{\"module\":\"backup\",\"status\":\"${status}\",\"detail\":\"${detail}\",\"file\":\"${FILE}\"}]" \
        >/dev/null || true
}

fail() {
    echo "BACKUP FAILED: $1" >&2
    log_axiom "failure" "$1"
    exit 1
}

[[ -n "${DATABASE_URL_DIRECT:-}" ]] || fail "DATABASE_URL_DIRECT is not set"
[[ -n "${R2_BACKUP_BUCKET:-}" ]] || fail "R2_BACKUP_BUCKET is not set"

# pg_dump understands postgresql:// but not SQLAlchemy's postgresql+asyncpg://
DUMP_URL="${DATABASE_URL_DIRECT/postgresql+asyncpg:\/\//postgresql://}"

echo "[$(date -u +%FT%TZ)] dumping database..."
pg_dump --no-owner --no-privileges "$DUMP_URL" | gzip > "${TMP}/${FILE}" \
    || fail "pg_dump failed"

SIZE=$(wc -c < "${TMP}/${FILE}" | tr -d ' ')
[[ "$SIZE" -gt 1024 ]] || fail "dump suspiciously small (${SIZE} bytes)"

echo "[$(date -u +%FT%TZ)] uploading ${FILE} (${SIZE} bytes) to R2..."
AWS_ACCESS_KEY_ID="$R2_ACCESS_KEY_ID" \
AWS_SECRET_ACCESS_KEY="$R2_SECRET_ACCESS_KEY" \
aws s3 cp "${TMP}/${FILE}" "s3://${R2_BACKUP_BUCKET}/${PREFIX}/${FILE}" \
    --endpoint-url "https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com" \
    --no-progress \
    || fail "R2 upload failed"

echo "[$(date -u +%FT%TZ)] backup complete: ${PREFIX}/${FILE}"
log_axiom "success" "${SIZE} bytes"
