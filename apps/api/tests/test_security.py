"""Security primitive tests — encryption (the four required tests), bcrypt, JWT."""

import time

import pytest
from cryptography.exceptions import InvalidTag

from app.core import security
from app.core.security import (
    JWTPayload,
    TokenExpiredError,
    TokenInvalidError,
    TokenMalformedError,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    decrypt_credential,
    encrypt_credential,
    hash_password,
    reencrypt_credential,
    verify_password,
)

# ---------------------------------------------------------------------------
# AES-256-GCM — the four required tests
# ---------------------------------------------------------------------------


def test_encrypt_decrypt_round_trip() -> None:
    plaintext = "sk-ant-api03-a-very-secret-customer-key"
    stored = encrypt_credential(plaintext)
    assert stored != plaintext
    assert ":" in stored
    assert decrypt_credential(stored) == plaintext


def test_same_input_produces_different_ciphertext() -> None:
    """Random IV per call — identical plaintexts must never share ciphertext."""
    a = encrypt_credential("identical-input")
    b = encrypt_credential("identical-input")
    assert a != b
    assert decrypt_credential(a) == decrypt_credential(b) == "identical-input"


def test_tampered_ciphertext_raises_invalid_tag() -> None:
    stored = encrypt_credential("super-secret")
    iv_b64, ct_b64 = stored.split(":", 1)
    # Flip a character in the ciphertext body
    tampered_ct = ("A" if ct_b64[0] != "A" else "B") + ct_b64[1:]
    with pytest.raises(InvalidTag):
        decrypt_credential(f"{iv_b64}:{tampered_ct}")


def test_malformed_key_raises_environment_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeSettings:
        credential_encryption_key = (
            "not-hex-at-all-not-hex-at-all-not-hex-at-all-not-hex-at-all-abc!"
        )

    monkeypatch.setattr(security, "settings", _FakeSettings())
    with pytest.raises(OSError, match="openssl rand -hex 32"):
        encrypt_credential("anything")

    class _ShortKeySettings:
        credential_encryption_key = "aabb" * 8  # valid hex but only 16 bytes

    monkeypatch.setattr(security, "settings", _ShortKeySettings())
    with pytest.raises(OSError, match="32 bytes"):
        encrypt_credential("anything")


def test_key_rotation_reencrypts() -> None:
    old_key = security.settings.credential_encryption_key  # the ACTIVE key
    new_key = "bb" * 32
    stored = encrypt_credential("rotate-me")
    rotated = reencrypt_credential(stored, old_key, new_key)
    assert rotated != stored
    # decrypting the rotated value with the ACTIVE (old) key must fail
    with pytest.raises(InvalidTag):
        decrypt_credential(rotated)
    # and re-rotating back must round-trip
    restored = reencrypt_credential(rotated, new_key, old_key)
    assert decrypt_credential(restored) == "rotate-me"


# ---------------------------------------------------------------------------
# bcrypt
# ---------------------------------------------------------------------------


def test_password_hash_and_verify() -> None:
    started = time.perf_counter()
    hashed = hash_password("s3cure-Passw0rd!")
    elapsed = time.perf_counter() - started
    assert hashed.startswith("$2b$12$")  # bcrypt, cost 12
    assert verify_password("s3cure-Passw0rd!", hashed)
    assert not verify_password("wrong-password", hashed)
    # cost 12 is intentionally slow; sanity-check it's not misconfigured to be instant
    assert elapsed > 0.05


# ---------------------------------------------------------------------------
# JWT round-trip + blacklist
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _fake_redis(monkeypatch: pytest.MonkeyPatch) -> None:
    """Route the blacklist at an in-memory fakeredis instance."""
    import fakeredis.aioredis

    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(security, "get_redis", lambda: fake)


async def test_access_token_round_trip() -> None:
    token = create_access_token(
        {"sub": "user-1", "tid": "tenant-1", "plan": "growth", "admin": False}
    )
    payload = await decode_access_token(token)
    assert isinstance(payload, JWTPayload)
    assert payload.sub == "user-1"
    assert payload.tid == "tenant-1"
    assert payload.plan == "growth"
    assert payload.jti  # every token carries a jti for revocation
    assert payload.type == "access"


async def test_blacklisted_token_treated_as_expired() -> None:
    token = create_access_token({"sub": "u", "tid": "t", "plan": "trial"})
    payload = await decode_access_token(token)
    await security.blacklist_token(payload.jti, ttl_seconds=900)
    assert await security.is_token_blacklisted(payload.jti)
    with pytest.raises(TokenExpiredError, match="revoked"):
        await decode_access_token(token)


async def test_wrong_signature_raises_invalid() -> None:
    import jwt as pyjwt

    forged = pyjwt.encode(
        {
            "sub": "u",
            "tid": "t",
            "plan": "trial",
            "jti": "x",
            "iat": 0,
            "exp": 4102444800,
            "type": "access",
        },
        "attacker-secret-attacker-secret-attacker",
        algorithm="HS256",
    )
    with pytest.raises(TokenInvalidError):
        await decode_access_token(forged)


async def test_garbage_token_raises_malformed() -> None:
    with pytest.raises(TokenMalformedError):
        await decode_access_token("not.a.jwt")


async def test_refresh_token_round_trip_and_type_separation() -> None:
    refresh = create_refresh_token("user-42")
    assert decode_refresh_token(refresh) == "user-42"
    # a refresh token must NOT be accepted as an access token
    with pytest.raises((TokenInvalidError, TokenMalformedError)):
        await decode_access_token(refresh)
