"""Axiom log-query client — powers the admin log-query endpoint (Prompt 7 Step 11).

Queries Axiom's APL endpoint so support can filter a tenant's logs by time and
level from the admin panel, instead of SSHing into the VPS and grepping. Returns
an empty list when Axiom isn't configured (``AXIOM_TOKEN`` unset), so the
endpoint degrades gracefully in dev and test.
"""

import logging
from datetime import datetime
from typing import Any

import httpx

from app.core.circuit import get_circuit
from app.core.config import settings

logger = logging.getLogger(__name__)


def _escape(value: str) -> str:
    """Escape a value for safe interpolation into an APL string literal."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _build_apl(tenant_id: str | None, level: str | None, limit: int) -> str:
    filters: list[str] = []
    if tenant_id:
        filters.append(f'tenant_id == "{_escape(tenant_id)}"')
    if level:
        filters.append(f'level == "{_escape(level.upper())}"')
    where = (" | where " + " and ".join(filters)) if filters else ""
    return f'["{_escape(settings.axiom_dataset)}"]{where} | sort by _time desc | limit {int(limit)}'


def _parse(response_body: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalise Axiom's query response into a flat list of log rows."""
    matches = response_body.get("matches")
    if isinstance(matches, list):
        rows: list[dict[str, Any]] = []
        for match in matches:
            if not isinstance(match, dict):
                continue
            data = match.get("data")
            row = dict(data) if isinstance(data, dict) else {}
            if "_time" in match:
                row.setdefault("_time", match["_time"])
            rows.append(row)
        return rows
    return []


async def query_logs(
    *,
    tenant_id: str | None,
    from_date: datetime,
    to_date: datetime,
    level: str | None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Query Axiom for log rows in a time window, filtered by tenant and level."""
    if not settings.axiom_token:
        logger.info("axiom not configured; log query returns empty")
        return []

    body = {
        "apl": _build_apl(tenant_id, level, limit),
        "startTime": from_date.isoformat(),
        "endTime": to_date.isoformat(),
    }

    async def _run() -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{settings.axiom_url}/v1/datasets/_apl",
                params={"format": "legacy"},
                headers={
                    "Authorization": f"Bearer {settings.axiom_token}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            response.raise_for_status()
            return _parse(response.json())

    return await get_circuit("axiom").call(_run)
