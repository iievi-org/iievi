# Observability: Sentry, Axiom, Uptime Robot

## Sentry

1. Create org + two projects: `iievi-api` (Python) and `iievi-web` (Next.js).
2. Put the API DSN in Doppler (`SENTRY_DSN`, all three configs — leave dev
   empty to disable locally) and the web DSN in Vercel env
   (`NEXT_PUBLIC_SENTRY_DSN`).
3. Credential scrubbing is enforced in code, not in Sentry settings:
   - API: `apps/api/app/core/sentry.py` (`before_send=scrub_event`)
   - Web: `apps/web/src/lib/sentry-scrub.ts`
   Fields named api_key, token, password, encrypted_key, encrypted_token,
   secret (and variants) are replaced with `[REDACTED]` recursively.
   Covered by `tests/test_observability.py` in CI.
4. Integrations enabled: FastAPI, SQLAlchemy (slow queries surface as spans),
   Celery. `send_default_pii=False` in both apps.
5. **DoD verification**: `curl -H "X-Health-Key: wrong" https://api.<domain>/health/deep`
   → the WARNING log appears; force a test error with
   `doppler run -- uv run python -c "import sentry_sdk; ...; sentry_sdk.capture_message('sentry wiring test')"`
   and confirm the event in Sentry contains no credential values.

## Axiom

1. Create dataset `iievi-api`, generate an ingest token → Doppler `AXIOM_TOKEN`.
2. The API logs one JSON object per line to stdout; Supervisor writes them to
   `/var/log/iievi/*.log`. Ship them with Vector (recommended):

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.vector.dev | bash
```

`/etc/vector/vector.yaml`:

```yaml
sources:
  iievi_logs:
    type: file
    include: ["/var/log/iievi/*.log"]
sinks:
  axiom:
    type: axiom
    inputs: [iievi_logs]
    token: ${AXIOM_TOKEN}
    dataset: iievi-api
```

Run vector under systemd with the token injected by Doppler.

## Uptime Robot

1. Monitor type: HTTPS, URL `https://api.<domain>/health`, interval 5 minutes.
2. Alert when down — Uptime Robot fires after the configured interval;
   set "confirm before alerting" to 2 rechecks so alerts fire after ~3
   consecutive failures, not one blip.
3. Alert contacts: sattvacare.in@gmail.com (add SMS/Telegram later).
4. Optional: a second monitor on the marketing site root.
