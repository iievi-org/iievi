# Doppler Secret Management

Doppler is the single source of truth for all secrets. No `.env` files exist
anywhere — local, CI, or production.

## One-time project setup (owner)

```bash
doppler login
doppler projects create iievi
# Doppler creates dev/stg/prd configs by default; they map to our
# development / staging / production environments.
```

## Populate the development config

```bash
doppler secrets set --project iievi --config dev \
  ENVIRONMENT=development \
  DATABASE_URL='postgresql+asyncpg://iievi_app:iievi_app_dev_only@localhost:5432/iievi' \
  DATABASE_URL_OWNER='postgresql+asyncpg://iievi:iievi@localhost:5432/iievi' \
  REDIS_URL='redis://localhost:6379/0' \
  JWT_SECRET="$(openssl rand -hex 32)" \
  JWT_REFRESH_SECRET="$(openssl rand -hex 32)" \
  CREDENTIAL_ENCRYPTION_KEY="$(openssl rand -hex 32)" \
  HEALTH_API_KEY="$(openssl rand -hex 16)" \
  DOCS_KEY="$(openssl rand -hex 16)" \
  CORS_ORIGINS='http://localhost:3000' \
  SENTRY_DSN='' \
  AXIOM_TOKEN='' \
  LOG_LEVEL=INFO
```

Placeholders for services not yet configured (fill in during later phases):

```bash
doppler secrets set --project iievi --config dev \
  RAZORPAY_KEY_ID=placeholder RAZORPAY_KEY_SECRET=placeholder \
  STRIPE_SECRET_KEY=placeholder STRIPE_WEBHOOK_SECRET=placeholder \
  R2_ACCOUNT_ID=placeholder R2_ACCESS_KEY_ID=placeholder R2_SECRET_ACCESS_KEY=placeholder \
  RESEND_API_KEY=placeholder LANGFUSE_PUBLIC_KEY=placeholder LANGFUSE_SECRET_KEY=placeholder
```

Repeat for `--config stg` and `--config prd` with real values (generate
DIFFERENT random keys per environment — never share JWT_SECRET or
CREDENTIAL_ENCRYPTION_KEY across environments).

## Wiring

- **Local dev**: `doppler setup --project iievi --config dev` once per clone;
  the Makefile prefixes every command with `doppler run --`.
- **VPS (production)**: as the deploy user in /srv/iievi run
  `doppler setup --project iievi --config prd` using a service token
  (`doppler configs tokens create prd-vps --config prd`). Supervisor commands
  all run under `doppler run --`.
- **GitHub Actions**: create a service token for `prd`, store it as the
  `DOPPLER_TOKEN` repository secret; deploy.yml fetches secrets with
  dopplerhq/secrets-fetch-action.

## Rules

- `CREDENTIAL_ENCRYPTION_KEY` (AES-256-GCM master key) lives ONLY in Doppler.
  Rotating it requires re-encrypting all stored credentials — see the security
  phase runbook before touching it.
- Adding a variable: set it in all three configs, add the typed field to
  `apps/api/app/core/config.py`, document it here.
