"""Structured JSON logging.

Every log entry is a single JSON object containing timestamp (ISO 8601), level,
module, request_id, tenant_id (when authenticated), and the message. Extra
fields passed via ``logger.info(..., extra={...})`` are merged in. Output goes
to stdout where Supervisor captures it and Axiom ingests it.
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import override

from app.core.context import request_id_var, task_id_var, task_name_var, tenant_id_var

_RESERVED_ATTRS = frozenset(logging.LogRecord("", 0, "", 0, "", None, None).__dict__.keys()) | {
    "message",
    "asctime",
    "taskName",
}


class JsonFormatter(logging.Formatter):
    """Formats every record as one JSON object per line."""

    @override
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "request_id": request_id_var.get(),
            "tenant_id": tenant_id_var.get(),
            "message": record.getMessage(),
        }
        # Task identifiers appear only on worker logs (set by task_prerun), so
        # API log lines aren't cluttered with null task fields.
        task_name = task_name_var.get()
        if task_name is not None:
            entry["task_name"] = task_name
        task_id = task_id_var.get()
        if task_id is not None:
            entry["task_id"] = task_id
        if record.exc_info and record.exc_info[0] is not None:
            entry["exception"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key not in _RESERVED_ATTRS and not key.startswith("_"):
                entry[key] = value
        return json.dumps(entry, default=str)


def configure_logging(level: str = "INFO") -> None:
    """Install the JSON formatter on the root logger (idempotent)."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
    # uvicorn's own loggers should flow through the same JSON pipeline
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True
