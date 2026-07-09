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

    # --- Observability ----------------------------------------------------
    sentry_dsn: str = Field(default="", alias="SENTRY_DSN")
    axiom_token: str = Field(default="", alias="AXIOM_TOKEN")
    axiom_dataset: str = Field(default="iievi-api", alias="AXIOM_DATASET")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

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
