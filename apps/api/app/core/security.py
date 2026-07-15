"""Cryptographic primitives — the ONLY file that invokes cryptography directly.

Three responsibilities:
1. AES-256-GCM credential encryption (customer API keys, social tokens).
   Stored format: base64(iv):base64(ciphertext_with_auth_tag).
2. Password hashing: bcrypt via passlib at cost factor 12 (~250ms per hash,
   intentionally slow to resist brute force).
3. JWT issue/verify with per-token jti and a Redis blacklist for revocation.

Tamper detection is load-bearing: InvalidTag from AESGCM.decrypt MUST
propagate — never catch it silently. A tampered credential is a security
incident, not a recoverable error.
"""

import base64
import logging
import os
import uuid
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

IV_BYTES = 12
KEY_BYTES = 32
BCRYPT_ROUNDS = 12

ACCESS_TOKEN_TTL = timedelta(minutes=15)
REFRESH_TOKEN_TTL = timedelta(days=30)
JWT_ALGORITHM = "HS256"

_BLACKLIST_PREFIX = "jwt:blacklist:"


# ---------------------------------------------------------------------------
# AES-256-GCM credential encryption
# ---------------------------------------------------------------------------


def _load_key() -> bytes:
    """Load and validate the 32-byte key from CREDENTIAL_ENCRYPTION_KEY (hex)."""
    raw = settings.credential_encryption_key
    try:
        key = bytes.fromhex(raw)
    except ValueError as exc:
        msg = (
            "CREDENTIAL_ENCRYPTION_KEY is malformed: expected 64 hexadecimal "
            "characters (32 bytes). Generate one with: openssl rand -hex 32"
        )
        raise OSError(msg) from exc
    if len(key) != KEY_BYTES:
        msg = (
            f"CREDENTIAL_ENCRYPTION_KEY must decode to exactly {KEY_BYTES} bytes, "
            f"got {len(key)}. Generate one with: openssl rand -hex 32"
        )
        raise OSError(msg)
    return key


def encrypt_credential(plaintext: str) -> str:
    """Encrypt a credential for storage. Fresh random IV per call."""
    key = _load_key()
    iv = os.urandom(IV_BYTES)
    ciphertext = AESGCM(key).encrypt(iv, plaintext.encode("utf-8"), None)
    return f"{base64.b64encode(iv).decode()}:{base64.b64encode(ciphertext).decode()}"


def decrypt_credential(stored: str) -> str:
    """Decrypt a stored credential.

    Raises cryptography.exceptions.InvalidTag on tampered ciphertext — callers
    must let it propagate (see module docstring).
    """
    key = _load_key()
    iv_b64, _, ct_b64 = stored.partition(":")
    if not ct_b64:
        msg = "stored credential is not in base64(iv):base64(ciphertext) format"
        raise ValueError(msg)
    iv = base64.b64decode(iv_b64)
    ciphertext = base64.b64decode(ct_b64)
    return AESGCM(key).decrypt(iv, ciphertext, None).decode("utf-8")


def reencrypt_credential(stored: str, old_key_hex: str, new_key_hex: str) -> str:
    """Key rotation primitive: decrypt with the old key, encrypt with the new.

    Used by the rotation job that walks api_credentials re-encrypting every
    row. Both keys are passed explicitly so the job can run while the
    environment still holds the old key.
    """
    old_key = bytes.fromhex(old_key_hex)
    new_key = bytes.fromhex(new_key_hex)
    if len(old_key) != KEY_BYTES or len(new_key) != KEY_BYTES:
        msg = f"rotation keys must be {KEY_BYTES} bytes (64 hex chars) each"
        raise OSError(msg)
    iv_b64, _, ct_b64 = stored.partition(":")
    plaintext = AESGCM(old_key).decrypt(base64.b64decode(iv_b64), base64.b64decode(ct_b64), None)
    new_iv = os.urandom(IV_BYTES)
    new_ct = AESGCM(new_key).encrypt(new_iv, plaintext, None)
    return f"{base64.b64encode(new_iv).decode()}:{base64.b64encode(new_ct).decode()}"


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

_pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=BCRYPT_ROUNDS)


def hash_password(plaintext: str) -> str:
    """bcrypt at cost 12 — ~250ms by design."""
    return str(_pwd_context.hash(plaintext))


def verify_password(plaintext: str, hashed: str) -> bool:
    return bool(_pwd_context.verify(plaintext, hashed))


# ---------------------------------------------------------------------------
# JWT service
# ---------------------------------------------------------------------------


class TokenError(Exception):
    """Base class for token failures."""


class TokenExpiredError(TokenError):
    """Token exp is in the past, or the token has been revoked (blacklisted)."""


class TokenInvalidError(TokenError):
    """Signature verification failed."""


class TokenMalformedError(TokenError):
    """Not a decodable JWT, or required claims are missing."""


class JWTPayload(BaseModel):
    """Validated access-token claims."""

    sub: str  # user_id
    tid: str  # tenant_id
    plan: str
    role: str = "owner"  # RBAC role within the tenant
    admin: bool = False  # platform admin (IIEVI staff), NOT tenant admin
    jti: str
    exp: int
    iat: int
    type: str


def create_access_token(payload: dict[str, str | bool]) -> str:
    """15-minute access token. Payload must include sub, tid, plan; admin optional."""
    now = datetime.now(UTC)
    claims: dict[str, str | bool | int] = {
        **payload,
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int((now + ACCESS_TOKEN_TTL).timestamp()),
        "type": "access",
    }
    return pyjwt.encode(claims, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """30-day refresh token, separate secret, minimal claims."""
    now = datetime.now(UTC)
    claims = {
        "sub": user_id,
        "jti": str(uuid.uuid4()),
        "iat": int(now.timestamp()),
        "exp": int((now + REFRESH_TOKEN_TTL).timestamp()),
        "type": "refresh",
    }
    return pyjwt.encode(claims, settings.jwt_refresh_secret, algorithm=JWT_ALGORITHM)


async def decode_access_token(token: str) -> JWTPayload:
    """Decode + validate an access token, including the revocation blacklist.

    Raises TokenExpiredError / TokenInvalidError / TokenMalformedError.
    A blacklisted token raises TokenExpiredError (treated exactly as expired).
    """
    try:
        raw = pyjwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
    except pyjwt.ExpiredSignatureError as exc:
        raise TokenExpiredError("access token expired") from exc
    except pyjwt.InvalidSignatureError as exc:
        raise TokenInvalidError("access token signature invalid") from exc
    except pyjwt.PyJWTError as exc:
        raise TokenMalformedError("access token malformed") from exc

    try:
        payload = JWTPayload.model_validate(raw)
    except ValueError as exc:
        raise TokenMalformedError("access token missing required claims") from exc

    if payload.type != "access":
        raise TokenMalformedError("not an access token")
    if await is_token_blacklisted(payload.jti):
        raise TokenExpiredError("access token revoked")
    return payload


def decode_refresh_token(token: str) -> str:
    """Decode a refresh token and return the user_id (sub claim)."""
    try:
        raw = pyjwt.decode(token, settings.jwt_refresh_secret, algorithms=[JWT_ALGORITHM])
    except pyjwt.ExpiredSignatureError as exc:
        raise TokenExpiredError("refresh token expired") from exc
    except pyjwt.InvalidSignatureError as exc:
        raise TokenInvalidError("refresh token signature invalid") from exc
    except pyjwt.PyJWTError as exc:
        raise TokenMalformedError("refresh token malformed") from exc
    if raw.get("type") != "refresh":
        raise TokenMalformedError("not a refresh token")
    sub = raw.get("sub")
    if not isinstance(sub, str) or not sub:
        raise TokenMalformedError("refresh token missing sub")
    return sub


# ---------------------------------------------------------------------------
# Redis token blacklist (revocation by jti)
# ---------------------------------------------------------------------------


async def blacklist_token(jti: str, ttl_seconds: int) -> None:
    """Revoke a token until its natural expiry (pass remaining TTL)."""
    await get_redis().set(f"{_BLACKLIST_PREFIX}{jti}", "1", ex=max(ttl_seconds, 1))


async def is_token_blacklisted(jti: str) -> bool:
    return bool(await get_redis().exists(f"{_BLACKLIST_PREFIX}{jti}"))
