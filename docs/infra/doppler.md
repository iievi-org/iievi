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
  GEMINI_API_KEY='<from Google AI Studio — see below>' \
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

Webhook and AI-budget variables (added in the AI/webhooks phase; all optional
in dev — webhook receivers reject everything until their secret is set):

```bash
doppler secrets set --project iievi --config dev \
  META_APP_SECRET='<Meta app dashboard → Settings → Basic → App Secret>' \
  META_WEBHOOK_VERIFY_TOKEN="$(openssl rand -hex 16)" \
  RAZORPAY_WEBHOOK_SECRET='<Razorpay dashboard → Webhooks → your endpoint secret>' \
  STRIPE_WEBHOOK_SECRET='<Stripe → Developers → Webhooks → Signing secret (whsec_…)>' \
  AI_DAILY_BUDGET_USD=5.0
```

`META_WEBHOOK_VERIFY_TOKEN` is a value YOU invent — paste the same string
into the Meta app's webhook subscription form; Meta echoes it back in the
GET verification handshake.

## Acquiring each secret for development

Self-generated (no external account — just run the `openssl rand` commands
above): `JWT_SECRET`, `JWT_REFRESH_SECRET`, `CREDENTIAL_ENCRYPTION_KEY`,
`HEALTH_API_KEY`, `DOCS_KEY`.

External services:

| Secret | Where to get it |
|---|---|
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) → sign in with a Google account → **Create API key** (pick or auto-create a Google Cloud project). Free tier is enough for dev. Powers PLATFORM-side text (Gemini 2.5 Flash) **and** image (Gemini 2.5 Flash Image) generation. |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` | [cloud.langfuse.com](https://cloud.langfuse.com) → create org + project → **Settings → API Keys → Create new key** (`pk-lf-…` / `sk-lf-…`). Optional in dev — tracing silently disables when unset. |
| `R2_ACCOUNT_ID` / `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` | [Cloudflare dashboard](https://dash.cloudflare.com) → **R2** → create bucket `iievi-media` → **Manage R2 API Tokens → Create API Token** (Object Read & Write, scoped to the bucket). Account ID is on the R2 overview page. |
| `SENTRY_DSN` | [sentry.io](https://sentry.io) → create project (Python/FastAPI) → **Settings → Client Keys (DSN)**. Optional in dev. |
| `AXIOM_TOKEN` | [axiom.co](https://app.axiom.co) → create dataset `iievi-api` → **Settings → API Tokens** (ingest-only token). Optional in dev. |
| `RESEND_API_KEY` | [resend.com](https://resend.com) → **API Keys → Create API Key**. Placeholder until the email phase. |
| `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` | [dashboard.razorpay.com](https://dashboard.razorpay.com) → **Settings → API Keys** → generate **Test Mode** keys. Placeholder until the billing phase. |
| `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET` | [dashboard.stripe.com](https://dashboard.stripe.com) → **Developers → API keys** (test mode `sk_test_…`); webhook secret from **Developers → Webhooks** after adding an endpoint. Placeholder until the billing phase. |
| `SNYK_TOKEN` (GitHub Actions only) | [app.snyk.io](https://app.snyk.io) → **Account Settings → API Token** → add as a GitHub repo secret. CI skips the Snyk job when absent. |

`DATABASE_URL*` and `REDIS_URL` point at the local podman-compose stack
(`make up`) — the values in the block above work as-is.

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
