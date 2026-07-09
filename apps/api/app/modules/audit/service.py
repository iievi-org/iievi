"""Audit log service.

log_event writes SYNCHRONOUSLY in the caller's transaction — never via
Celery. An async audit write creates the race where the operation committed
but its audit record was lost; atomicity with the operation is the whole
point of the log.

Sensitive values are redacted before storage: any key containing password,
hash, token, key, or secret becomes [REDACTED]. The table itself is
append-only, enforced by a database trigger (see the gateway migration) —
no UPDATE or DELETE will ever succeed, even from a bug or a compromised
app role.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditAction, AuditLog

_SENSITIVE_FRAGMENTS = ("password", "hash", "token", "key", "secret")
REDACTED = "[REDACTED]"


def redact_sensitive(values: dict[str, object] | None) -> dict[str, object] | None:
    """Recursively replace values of sensitive-looking keys."""
    if values is None:
        return None
    result: dict[str, object] = {}
    for key, value in values.items():
        if any(fragment in key.lower() for fragment in _SENSITIVE_FRAGMENTS):
            result[key] = REDACTED
        elif isinstance(value, dict):
            result[key] = redact_sensitive(value)
        else:
            result[key] = value
    return result


async def log_event(
    session: AsyncSession,
    *,
    action: AuditAction,
    resource_type: str,
    resource_id: uuid.UUID | None = None,
    tenant_id: uuid.UUID | None = None,
    actor_user_id: uuid.UUID | None = None,
    actor_ip: str | None = None,
    old_values: dict[str, object] | None = None,
    new_values: dict[str, object] | None = None,
    metadata: dict[str, object] | None = None,
) -> None:
    """Append one audit record in the CURRENT transaction (no commit here —
    the record commits or rolls back together with the operation it records).
    """
    session.add(
        AuditLog(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            actor_ip=actor_ip,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=redact_sensitive(old_values),
            new_values=redact_sensitive(new_values),
            meta=metadata or {},
        )
    )
    await session.flush()
