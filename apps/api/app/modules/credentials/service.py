"""Credential management — the SINGLE access point for customer API keys.

Rules enforced here:
- A credential is verified against its platform BEFORE it is stored; a key
  that fails verification is never persisted (CredentialVerificationError).
- Every field is encrypted individually (AES-256-GCM via core.security) and
  the bundle is stored as JSON in api_credentials.encrypted_key.
- Every decrypt is audit-logged (tenant, service, caller — NEVER the value).
"""

import inspect
import json
import logging
import uuid
from dataclasses import dataclass

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CredentialVerificationError
from app.core.security import decrypt_credential, encrypt_credential
from app.db.models import ApiCredential, AuditAction
from app.modules.audit.service import log_event

logger = logging.getLogger(__name__)

VERIFY_TIMEOUT_S = 10.0

# Required fields per service — validation happens before any network call.
REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "anthropic": ("api_key",),
    "nanobanana": ("api_key",),
    "meta": ("access_token", "page_id"),
    "instagram": ("access_token", "business_account_id"),
    "whatsapp": ("access_token", "phone_number_id"),
    "linkedin": ("access_token", "organization_id"),
    "tiktok": ("access_token", "advertiser_id"),
}

_GRAPH = "https://graph.facebook.com/v21.0"


@dataclass(frozen=True)
class DecryptedCredential:
    """Decrypted credential bundle for one service."""

    service: str
    fields: dict[str, str]

    def __repr__(self) -> str:  # never leak values into logs/tracebacks
        return (
            f"DecryptedCredential(service={self.service!r}, fields=<{len(self.fields)} redacted>)"
        )


async def _verify_anthropic(fields: dict[str, str], client: httpx.AsyncClient) -> None:
    response = await client.get(
        "https://api.anthropic.com/v1/models",
        headers={"x-api-key": fields["api_key"], "anthropic-version": "2023-06-01"},
    )
    if response.status_code in (401, 403):
        raise CredentialVerificationError(
            "Anthropic rejected this API key", details={"provider_status": response.status_code}
        )
    response.raise_for_status()


async def _verify_meta(fields: dict[str, str], client: httpx.AsyncClient) -> None:
    response = await client.get(
        f"{_GRAPH}/{fields['page_id']}",
        params={"access_token": fields["access_token"], "fields": "id,name"},
    )
    if response.status_code != 200:
        raise CredentialVerificationError(
            "Meta rejected this access token / page id",
            details={"provider_error": response.json().get("error", {}).get("message", "")},
        )


async def _verify_whatsapp(fields: dict[str, str], client: httpx.AsyncClient) -> None:
    response = await client.get(
        f"{_GRAPH}/{fields['phone_number_id']}",
        params={"access_token": fields["access_token"]},
    )
    if response.status_code != 200:
        raise CredentialVerificationError(
            "WhatsApp rejected this access token / phone number id",
            details={"provider_error": response.json().get("error", {}).get("message", "")},
        )


async def _verify_nanobanana(fields: dict[str, str], client: httpx.AsyncClient) -> None:
    # NanoBanana Pro exposes a key-scoped account endpoint; any 2xx verifies.
    response = await client.get(
        "https://api.nanobanana.pro/v1/account",
        headers={"Authorization": f"Bearer {fields['api_key']}"},
    )
    if response.status_code >= 400:
        raise CredentialVerificationError(
            "NanoBanana Pro rejected this API key",
            details={"provider_status": response.status_code},
        )


async def _verify_instagram(fields: dict[str, str], client: httpx.AsyncClient) -> None:
    response = await client.get(
        f"{_GRAPH}/{fields['business_account_id']}",
        params={"access_token": fields["access_token"], "fields": "id,username"},
    )
    if response.status_code != 200:
        raise CredentialVerificationError(
            "Instagram rejected this access token / account id",
            details={"provider_error": response.json().get("error", {}).get("message", "")},
        )


# linkedin/tiktok verifiers land with their publishing phases; shape
# validation still applies to them via REQUIRED_FIELDS.
_VERIFIERS = {
    "anthropic": _verify_anthropic,
    "nanobanana": _verify_nanobanana,
    "meta": _verify_meta,
    "instagram": _verify_instagram,
    "whatsapp": _verify_whatsapp,
}


async def save_credential(
    tenant_id: uuid.UUID,
    service: str,
    data: dict[str, str],
    session: AsyncSession,
    actor_user_id: uuid.UUID | None = None,
) -> None:
    """Validate shape → verify against the platform → encrypt → upsert."""
    required = REQUIRED_FIELDS.get(service)
    if required is None:
        raise CredentialVerificationError(f"Unknown service: {service}")
    missing = [f for f in required if not data.get(f)]
    if missing:
        raise CredentialVerificationError(
            f"Missing required fields for {service}", details={"missing": missing}
        )

    verifier = _VERIFIERS.get(service)
    if verifier is not None:
        async with httpx.AsyncClient(timeout=VERIFY_TIMEOUT_S) as client:
            try:
                await verifier(data, client)
            except CredentialVerificationError:
                raise
            except httpx.HTTPError as exc:
                raise CredentialVerificationError(
                    f"Could not reach {service} to verify the credential"
                ) from exc

    encrypted_bundle = json.dumps({k: encrypt_credential(v) for k, v in data.items()})

    existing = await session.scalar(select(ApiCredential).where(ApiCredential.service == service))
    if existing is not None:
        existing.encrypted_key = encrypted_bundle
        action = AuditAction.UPDATE
        resource_id = existing.id
    else:
        record = ApiCredential(tenant_id=tenant_id, service=service, encrypted_key=encrypted_bundle)
        session.add(record)
        await session.flush()
        action = AuditAction.CREATE
        resource_id = record.id

    await log_event(
        session,
        action=action,
        resource_type="ApiCredential",
        resource_id=resource_id,
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        new_values={"service": service, "fields": sorted(data)},  # names only, never values
    )


async def get_decrypted_credential(
    tenant_id: uuid.UUID, service: str, session: AsyncSession
) -> DecryptedCredential:
    """Decrypt a stored credential; ALWAYS audit-logged with caller location."""
    record = await session.scalar(select(ApiCredential).where(ApiCredential.service == service))
    if record is None:
        raise CredentialVerificationError(f"No {service} credential is connected")

    bundle: dict[str, str] = json.loads(record.encrypted_key)
    fields = {k: decrypt_credential(v) for k, v in bundle.items()}

    caller = inspect.stack()[1]
    await log_event(
        session,
        action=AuditAction.CREDENTIAL_ACCESS,
        resource_type="ApiCredential",
        resource_id=record.id,
        tenant_id=tenant_id,
        metadata={
            "service": service,
            "caller": f"{caller.filename.rsplit('/', 1)[-1]}:{caller.lineno}",
        },
    )
    return DecryptedCredential(service=service, fields=fields)
