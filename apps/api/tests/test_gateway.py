"""Gateway dependency and middleware tests — the Prompt 3 DoD suite.

Auth failures, plan gating, RBAC, CSRF, error envelope consistency. DB-backed
flows (register/login, RLS scoping, audit trigger) live in tests/db/.
"""

import uuid

import fakeredis.aioredis
import pytest
from fastapi.testclient import TestClient

from app.core import ratelimit, security
from app.core.exceptions import AuthorizationError
from app.core.permissions import Permission, role_has_permission
from app.core.security import create_access_token
from app.db.models import UserRole
from app.gateway.dependencies import (
    AuthenticatedUser,
    check_permission,
    require_admin,
    require_plan,
)
from app.main import app


@pytest.fixture(autouse=True)
def _fake_redis(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(security, "get_redis", lambda: fake)
    monkeypatch.setattr(ratelimit, "get_redis", lambda: fake)


def _token(**overrides: object) -> str:
    claims: dict[str, object] = {
        "sub": str(uuid.uuid4()),
        "tid": str(uuid.uuid4()),
        "plan": "starter",
        "role": "owner",
        "admin": False,
    }
    claims.update(overrides)
    return create_access_token(claims)  # type: ignore[arg-type]


def _user(
    plan: str = "starter", role: UserRole = UserRole.OWNER, admin: bool = False
) -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        plan=plan,
        role=role,
        is_admin=admin,
    )


# ---------------------------------------------------------------------------
# get_current_user — 401 for every broken-token shape (via a live endpoint)
# ---------------------------------------------------------------------------


def test_protected_endpoint_401_without_header(client_gw: TestClient) -> None:
    response = client_gw.get("/api/v1/billing/capabilities")
    assert response.status_code == 401
    body = response.json()
    assert body["code"] == "authentication_failed"
    assert set(body) == {"code", "message", "details"}


def test_protected_endpoint_401_with_garbage_token(client_gw: TestClient) -> None:
    response = client_gw.get(
        "/api/v1/billing/capabilities", headers={"Authorization": "Bearer not.a.jwt"}
    )
    assert response.status_code == 401


def test_protected_endpoint_401_with_tampered_token(client_gw: TestClient) -> None:
    token = _token()
    header, payload, _sig = token.split(".")
    forged = f"{header}.{payload}.AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    response = client_gw.get(
        "/api/v1/billing/capabilities", headers={"Authorization": f"Bearer {forged}"}
    )
    assert response.status_code == 401


async def test_blacklisted_token_is_401(client_gw: TestClient) -> None:
    token = _token()
    payload = await security.decode_access_token(token)
    await security.blacklist_token(payload.jti, ttl_seconds=900)
    response = client_gw.get(
        "/api/v1/billing/capabilities", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


def test_expired_token_is_401(client_gw: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    import jwt as pyjwt

    from app.core.config import settings

    expired = pyjwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "tid": str(uuid.uuid4()),
            "plan": "starter",
            "role": "owner",
            "admin": False,
            "jti": str(uuid.uuid4()),
            "iat": 1000000000,
            "exp": 1000000001,  # long past
            "type": "access",
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    response = client_gw.get(
        "/api/v1/billing/capabilities", headers={"Authorization": f"Bearer {expired}"}
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# require_plan / require_admin / check_permission
# ---------------------------------------------------------------------------


async def test_require_plan_blocks_lower_tier() -> None:
    dep = require_plan("growth")
    with pytest.raises(AuthorizationError) as exc_info:
        await dep(_user(plan="starter"))
    assert exc_info.value.details["code"] == "plan_upgrade_required"
    assert exc_info.value.details["current_plan"] == "starter"
    assert exc_info.value.details["required_plan"] == "growth"


async def test_require_plan_passes_equal_and_higher() -> None:
    dep = require_plan("growth")
    assert (await dep(_user(plan="growth"))).plan == "growth"
    assert (await dep(_user(plan="agency"))).plan == "agency"


def test_require_plan_rejects_unknown_plan_at_definition() -> None:
    with pytest.raises(ValueError, match="unknown plan"):
        require_plan("enterprise")


async def test_require_admin_blocks_non_admin() -> None:
    with pytest.raises(AuthorizationError):
        await require_admin(_user(admin=False))
    assert (await require_admin(_user(admin=True))).is_admin


async def test_check_permission_by_role() -> None:
    dep = check_permission(Permission.ADS_CREATE)
    assert await dep(_user(role=UserRole.OWNER))
    with pytest.raises(AuthorizationError):
        await dep(_user(role=UserRole.MEMBER))


def test_role_permission_matrix() -> None:
    assert role_has_permission(UserRole.OWNER, Permission.BILLING_MANAGE)
    assert not role_has_permission(UserRole.ADMIN, Permission.BILLING_MANAGE)
    assert not role_has_permission(UserRole.ADMIN, Permission.ADMIN_ACCESS)
    assert role_has_permission(UserRole.ADMIN, Permission.POSTS_PUBLISH)
    assert role_has_permission(UserRole.MEMBER, Permission.LEADS_READ)
    assert not role_has_permission(UserRole.MEMBER, Permission.LEADS_WRITE)


# ---------------------------------------------------------------------------
# Admin endpoints reject non-admin tokens
# ---------------------------------------------------------------------------


def test_admin_flags_endpoint_403_for_regular_user(client_gw: TestClient) -> None:
    response = client_gw.get(
        "/api/v1/admin/feature-flags", headers={"Authorization": f"Bearer {_token()}"}
    )
    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"


# ---------------------------------------------------------------------------
# CSRF — cookie-bearing state-changing requests need the header
# ---------------------------------------------------------------------------


def test_csrf_blocks_cookie_request_without_header(client_gw: TestClient) -> None:
    response = client_gw.post(
        "/api/v1/admin/feature-flags",
        headers={"Authorization": f"Bearer {_token(admin=True)}"},
        cookies={"csrf_token": "abc123"},
        json={"flag_key": "x_flag"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == "csrf_verification_failed"


def test_csrf_blocks_mismatched_header(client_gw: TestClient) -> None:
    response = client_gw.post(
        "/api/v1/admin/feature-flags",
        headers={
            "Authorization": f"Bearer {_token(admin=True)}",
            "X-CSRF-Token": "wrong-value",
        },
        cookies={"csrf_token": "abc123"},
        json={"flag_key": "x_flag"},
    )
    assert response.status_code == 403


def test_csrf_exempts_auth_bootstrap(client_gw: TestClient) -> None:
    # /auth/login with cookies but no CSRF header must NOT be blocked by CSRF
    # (it fails with 401/422 from auth logic instead).
    response = client_gw.post(
        "/api/v1/auth/login",
        cookies={"csrf_token": "abc123"},
        json={"email": "nobody@example.com", "password": "wrong-password"},
    )
    assert response.status_code != 403


# ---------------------------------------------------------------------------
# Error envelope consistency — validation and HTTP errors share one shape
# ---------------------------------------------------------------------------


def test_validation_error_uses_standard_envelope(client_gw: TestClient) -> None:
    response = client_gw.post("/api/v1/auth/login", json={"email": "not-an-email"})
    assert response.status_code == 422
    body = response.json()
    assert set(body) == {"code", "message", "details"}
    assert body["code"] == "validation_error"


def test_unknown_route_uses_standard_envelope(client_gw: TestClient) -> None:
    response = client_gw.get("/api/v1/definitely-not-a-route")
    assert response.status_code == 404
    assert set(response.json()) == {"code", "message", "details"}


def test_null_byte_rejected_by_sanitized_model(client_gw: TestClient) -> None:
    response = client_gw.post(
        "/api/v1/auth/login",
        json={"email": "a@b.co", "password": "pass\x00word"},
    )
    assert response.status_code == 422


@pytest.fixture()
def client_gw() -> TestClient:
    return TestClient(app)
