"""Operations-team notification channel.

One function, two sinks: a CRITICAL structured log line (Axiom alert rules
match on "OPS ALERT") and a Sentry message. Email/WhatsApp escalation lands
with the notifications phase; every caller is already wired through here.
"""

import logging

logger = logging.getLogger(__name__)


def notify_ops(message: str) -> None:
    logger.critical("OPS ALERT: %s", message)
    try:
        import sentry_sdk

        sentry_sdk.capture_message(message, level="error")
    except Exception:  # noqa: BLE001 — alerting must never crash the caller
        logger.exception("sentry ops notification failed")
