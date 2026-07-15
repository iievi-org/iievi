"""Application configuration.

All settings are loaded from environment variables (injected by Doppler — never
from committed .env files) and validated at import time. If a required variable
is missing or malformed the process refuses to start with a clear error listing
every offending field, rather than failing later at request time.
"""

import sys
from enum import StrEnum
from functools import lru_cache

from pydantic import Field, PostgresDsn, RedisDsn, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Deployment environment names — must match the Doppler config names."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Validated application settings.

    Every field without a default is required; startup fails if it is absent.
    """

    model_config = SettingsConfigDict(frozen=True)

    # --- Runtime ---------------------------------------------------------
    environment: Environment = Field(alias="ENVIRONMENT")
    app_name: str = Field(default="IIEVI API", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    git_commit_sha: str = Field(default="unknown", alias="GIT_COMMIT_SHA")
    deployed_at: str = Field(default="unknown", alias="DEPLOYED_AT")

    # --- Data stores ------------------------------------------------------
    database_url: PostgresDsn = Field(alias="DATABASE_URL")
    # Neon PgBouncer URL for the app's pooled connections; falls back to
    # DATABASE_URL locally where no PgBouncer exists.
    database_url_pooled: PostgresDsn | None = Field(default=None, alias="DATABASE_URL_POOLED")
    # Direct (non-pooled) URL for pg_dump backups and migrations on Neon.
    database_url_direct: PostgresDsn | None = Field(default=None, alias="DATABASE_URL_DIRECT")
    redis_url: RedisDsn = Field(alias="REDIS_URL")

    # --- Auth & crypto ----------------------------------------------------
    jwt_secret: str = Field(alias="JWT_SECRET", min_length=32)
    jwt_refresh_secret: str = Field(alias="JWT_REFRESH_SECRET", min_length=32)
    # 64 hex chars = 32 bytes; consumed exclusively by app/core/security.py
    credential_encryption_key: str = Field(alias="CREDENTIAL_ENCRYPTION_KEY", min_length=64)

    # --- Operational keys -------------------------------------------------
    health_api_key: str = Field(alias="HEALTH_API_KEY", min_length=16)
    docs_key: str = Field(alias="DOCS_KEY", min_length=16)

    # --- Platform AI (onboarding extraction runs on the PLATFORM's key;
    # customer-facing AI uses each tenant's own stored credential) ----------
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    langfuse_public_key: str = Field(default="", alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field(default="", alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field(default="https://cloud.langfuse.com", alias="LANGFUSE_HOST")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    langfuse_public_key: str = Field(default="", alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field(default="", alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field(default="https://cloud.langfuse.com", alias="LANGFUSE_HOST")
    # Per-tenant daily AI spend ceiling (USD) — exceeded → warn + notify ops
    ai_daily_budget_usd: float = Field(default=5.0, alias="AI_DAILY_BUDGET_USD")

    # --- Webhook signing secrets -------------------------------------------
    meta_app_secret: str = Field(default="", alias="META_APP_SECRET")
    # Echoed back in Meta's GET subscription-verify handshake
    meta_webhook_verify_token: str = Field(default="", alias="META_WEBHOOK_VERIFY_TOKEN")
    razorpay_webhook_secret: str = Field(default="", alias="RAZORPAY_WEBHOOK_SECRET")
    stripe_webhook_secret: str = Field(default="", alias="STRIPE_WEBHOOK_SECRET")

    # --- Cloudflare R2 (S3-compatible media storage) ------------------------
    r2_account_id: str = Field(default="", alias="R2_ACCOUNT_ID")
    r2_access_key_id: str = Field(default="", alias="R2_ACCESS_KEY_ID")
    r2_secret_access_key: str = Field(default="", alias="R2_SECRET_ACCESS_KEY")
    r2_bucket: str = Field(default="iievi-media", alias="R2_BUCKET")

    # --- Observability ----------------------------------------------------
    sentry_dsn: str = Field(default="", alias="SENTRY_DSN")
    axiom_token: str = Field(default="", alias="AXIOM_TOKEN")
    axiom_dataset: str = Field(default="iievi-api", alias="AXIOM_DATASET")
    # Axiom query API base — the admin log-query endpoint hits {url}/v1/datasets.
    axiom_url: str = Field(default="https://api.axiom.co", alias="AXIOM_URL")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # --- Notifications & platform outbound channels -----------------------
    # Transactional email (owner notifications, weekly reports) via Resend.
    resend_api_key: str = Field(default="", alias="RESEND_API_KEY")
    resend_from_email: str = Field(
        default="IIEVI <notifications@iievi.app>", alias="RESEND_FROM_EMAIL"
    )
    # Platform-owned WhatsApp number for OWNER notifications (handoff summaries).
    # Distinct from each tenant's own lead-facing WhatsApp credential.
    platform_whatsapp_token: str = Field(default="", alias="PLATFORM_WHATSAPP_TOKEN")
    platform_whatsapp_phone_id: str = Field(default="", alias="PLATFORM_WHATSAPP_PHONE_ID")
    # Dashboard base URL for notification/email deep links.
    dashboard_url: str = Field(default="http://localhost:3000", alias="DASHBOARD_URL")

    # --- CORS -------------------------------------------------------------
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    @field_validator("database_url")
    @classmethod
    def _require_asyncpg_driver(cls, v: PostgresDsn) -> PostgresDsn:
        """The whole stack is async; a sync driver URL is a misconfiguration."""
        if v.scheme != "postgresql+asyncpg":
            msg = f"DATABASE_URL must use postgresql+asyncpg://, got {v.scheme}://"
            raise ValueError(msg)
        return v

    @property
    def pooled_database_url(self) -> str:
        """Pooled URL for app sessions; plain URL when PgBouncer is absent (local)."""
        return str(self.database_url_pooled or self.database_url)

    @property
    def cors_origin_list(self) -> list[str]:
        """CORS_ORIGINS is a comma-separated string in Doppler."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment is Environment.PRODUCTION


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton settings instance, exiting loudly on invalid config."""
    try:
        return Settings()
    except ValidationError as exc:
        missing = [
            ".".join(str(loc) for loc in err["loc"]) + f": {err['msg']}" for err in exc.errors()
        ]
        sys.stderr.write(
            "FATAL: invalid or missing environment configuration.\n"
            "Are you running under Doppler? (make dev / doppler run -- ...)\n\n"
            + "\n".join(f"  - {m}" for m in missing)
            + "\n"
        )
        raise SystemExit(1) from exc


settings = get_settings()
