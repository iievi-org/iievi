"""Sentry initialisation with mandatory credential scrubbing.

The before_send hook strips any field whose name matches a sensitive key
(api_key, token, password, encrypted_key, encrypted_token, secret — plus
obvious variants) anywhere in the event payload before it leaves the server.
This is a security requirement with no exceptions.
"""

import logging

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.types import Event, Hint

logger = logging.getLogger(__name__)

SENSITIVE_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "token",
        "access_token",
        "refresh_token",
        "password",
        "encrypted_key",
        "encrypted_token",
        "secret",
        "authorization",
        "cookie",
        "jwt_secret",
        "encryption_master_key",
    }
)

REDACTED = "[REDACTED]"

# SQLAlchemy integration reports queries slower than this as spans/breadcrumbs.
SLOW_QUERY_THRESHOLD_MS = 500


def _scrub(value: object) -> object:
    """Recursively redact sensitive keys in dicts/lists of an event payload."""
    if isinstance(value, dict):
        return {
            k: REDACTED if str(k).lower() in SENSITIVE_KEYS else _scrub(v) for k, v in value.items()
        }
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    return value


def scrub_event(event: Event, _hint: Hint) -> Event | None:
    """before_send hook: scrub credentials, then attach correlation context.

    The request_id/tenant_id tags let a Sentry event be joined against Axiom
    logs and Celery task records for the same request.
    """
    from app.core.context import request_id_var, tenant_id_var

    scrubbed = _scrub(dict(event))
    if not isinstance(scrubbed, dict):
        return None
    tags = scrubbed.setdefault("tags", {})
    if isinstance(tags, dict):
        if request_id_var.get():
            tags.setdefault("request_id", request_id_var.get())
        if tenant_id_var.get():
            tags.setdefault("tenant_id", tenant_id_var.get())
    return scrubbed  # type: ignore[return-value]  # structure preserved by _scrub


def init_sentry(dsn: str, environment: str, release: str) -> None:
    """Initialise Sentry; a missing DSN disables reporting (local development)."""
    if not dsn:
        logger.info("Sentry DSN not set — error reporting disabled")
        return
    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=release,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
            CeleryIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,
        before_send=scrub_event,
    )
