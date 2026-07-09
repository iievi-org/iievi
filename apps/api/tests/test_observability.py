"""Log formatter structure and Sentry credential scrubbing (security requirement)."""

import json
import logging

from app.core.context import request_id_var, tenant_id_var
from app.core.logging import JsonFormatter
from app.core.sentry import REDACTED, scrub_event


def test_json_formatter_includes_required_fields() -> None:
    request_token = request_id_var.set("req-123")
    tenant_token = tenant_id_var.set("tenant-456")
    try:
        record = logging.LogRecord(
            name="app.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="hello %s",
            args=("world",),
            exc_info=None,
        )
        entry = json.loads(JsonFormatter().format(record))
    finally:
        request_id_var.reset(request_token)
        tenant_id_var.reset(tenant_token)

    assert entry["level"] == "INFO"
    assert entry["module"] == "app.test"
    assert entry["message"] == "hello world"
    assert entry["request_id"] == "req-123"
    assert entry["tenant_id"] == "tenant-456"
    assert "T" in entry["timestamp"]  # ISO 8601


def test_json_formatter_merges_extra_fields() -> None:
    record = logging.LogRecord(
        name="app.test",
        level=logging.WARNING,
        pathname=__file__,
        lineno=1,
        msg="slow",
        args=None,
        exc_info=None,
    )
    record.duration_ms = 812.5
    entry = json.loads(JsonFormatter().format(record))
    assert entry["duration_ms"] == 812.5


def test_sentry_scrub_removes_credentials_at_any_depth() -> None:
    event = {
        "request": {
            "data": {
                "api_key": "sk-ant-real-key",
                "nested": {"encrypted_token": "abc", "safe": "keep-me"},
                "items": [{"password": "hunter2"}, {"ok": 1}],
            },
            "headers": {"Authorization": "Bearer xyz", "Accept": "application/json"},
        },
        "extra": {"secret": "s3cret", "tenant_id": "t-1"},
    }
    scrubbed = scrub_event(event, {})  # type: ignore[arg-type]

    assert scrubbed is not None
    data = scrubbed["request"]["data"]  # type: ignore[index]
    assert data["api_key"] == REDACTED
    assert data["nested"]["encrypted_token"] == REDACTED
    assert data["nested"]["safe"] == "keep-me"
    assert data["items"][0]["password"] == REDACTED
    assert scrubbed["request"]["headers"]["Authorization"] == REDACTED  # type: ignore[index]
    assert scrubbed["extra"]["secret"] == REDACTED  # type: ignore[index]
    assert scrubbed["extra"]["tenant_id"] == "t-1"  # type: ignore[index]
