"""Credential endpoints — thin HTTP wrapper over the credential service."""

import logging

from fastapi import APIRouter, status
from pydantic import Field
from sqlalchemy import select

from app.core.exceptions import ResourceNotFoundError
from app.core.schemas import SanitizedModel
from app.db.models import ApiCredential, AuditAction
from app.gateway.dependencies import CurrentUser, ScopedSession
from app.modules.audit.service import log_event
from app.modules.credentials.service import REQUIRED_FIELDS, save_credential
from app.modules.profiles.hooks import after_profile_write

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/credentials", tags=["credentials"])


class CredentialIn(SanitizedModel):
    service: str = Field(min_length=2, max_length=64)
    data: dict[str, str] = Field(min_length=1)


@router.get("", summary="List connected services (names only, never values)")
async def list_credentials(user: CurrentUser, session: ScopedSession) -> dict[str, object]:
    rows = (await session.scalars(select(ApiCredential))).all()
    return {
        "connected": [{"service": r.service, "last_used_at": r.last_used_at} for r in rows],
        "available": sorted(REQUIRED_FIELDS),
    }


@router.post("", status_code=status.HTTP_201_CREATED, summary="Connect or update a credential")
async def save_credential_endpoint(
    body: CredentialIn, user: CurrentUser, session: ScopedSession
) -> dict[str, object]:
    """Verifies against the live platform BEFORE storing (encrypted)."""
    await save_credential(
        tenant_id=user.tenant_id,
        service=body.service,
        data=body.data,
        session=session,
        actor_user_id=user.user_id,
    )
    # Registration of webhook-routing identifiers happens out-of-band
    try:
        from app.worker.tasks import register_platform_identifiers

        register_platform_identifiers.delay(str(user.tenant_id), body.service)
    except Exception:  # noqa: BLE001
        logger.warning("identifier registration enqueue failed")
    return {"service": body.service, "verified": True}


@router.delete("/{service}", status_code=status.HTTP_204_NO_CONTENT, summary="Revoke a credential")
async def revoke_credential(service: str, user: CurrentUser, session: ScopedSession) -> None:
    record = await session.scalar(select(ApiCredential).where(ApiCredential.service == service))
    if record is None:
        raise ResourceNotFoundError(f"No {service} credential is connected")
    await session.delete(record)
    await session.flush()
    await log_event(
        session,
        action=AuditAction.DELETE,
        resource_type="ApiCredential",
        resource_id=record.id,
        tenant_id=user.tenant_id,
        actor_user_id=user.user_id,
        old_values={"service": service},
    )
    after_profile_write(["credential_revoked"], user.tenant_id)
