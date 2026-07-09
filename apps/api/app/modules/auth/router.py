"""Authentication endpoints.

Cookie strategy:
- refresh_token: HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth/refresh
  (the browser sends it ONLY to the refresh endpoint — nowhere else)
- csrf_token: readable by JS (NOT HttpOnly) — the synchronizer token that the
  frontend echoes in X-CSRF-Token on state-changing requests

Access tokens live only in the response body / frontend memory, never in a
cookie.
"""

import ipaddress
import logging

from fastapi import APIRouter, Request, Response, status

from app.core.config import settings
from app.core.csrf import CSRF_COOKIE, issue_csrf_token
from app.core.exceptions import AuthenticationError
from app.core.security import (
    ACCESS_TOKEN_TTL,
    TokenError,
    blacklist_token,
    create_access_token,
    decode_access_token,
    decode_refresh_token,
)
from app.gateway.dependencies import CurrentUser
from app.modules.auth import service
from app.modules.auth.schemas import LoginRequest, RegisterRequest, TokenResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "refresh_token"
REFRESH_COOKIE_PATH = "/api/v1/auth/refresh"
REFRESH_MAX_AGE = 30 * 24 * 3600
_ACCESS_TTL_SECONDS = int(ACCESS_TOKEN_TTL.total_seconds())


def _client_ip(request: Request) -> str | None:
    """Best-effort client IP; None for anything that is not a valid address
    (the audit column is INET — a spoofed X-Real-IP must not break writes)."""
    candidate = request.headers.get("X-Real-IP") or (request.client.host if request.client else "")
    try:
        ipaddress.ip_address(candidate)
    except ValueError:
        return None
    return candidate


def _set_auth_cookies(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        max_age=REFRESH_MAX_AGE,
        httponly=True,
        secure=settings.is_production,
        samesite="strict",
        path=REFRESH_COOKIE_PATH,
    )
    response.set_cookie(
        CSRF_COOKIE,
        issue_csrf_token(),
        max_age=REFRESH_MAX_AGE,
        httponly=False,  # JS must read it to echo the X-CSRF-Token header
        secure=settings.is_production,
        samesite="strict",
        path="/",
    )


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Create a tenant and its owner account",
    description=(
        "Creates the tenant and the owner user in one atomic transaction. "
        "Returns an access token; sets the refresh and CSRF cookies."
    ),
    response_model=TokenResponse,
    responses={201: {"description": "Account created"}, 401: {"description": "Email in use"}},
)
async def register_endpoint(
    body: RegisterRequest, request: Request, response: Response
) -> TokenResponse:
    tokens = await service.register(
        business_name=body.business_name,
        full_name=body.full_name,
        email=body.email,
        password=body.password,
        actor_ip=_client_ip(request),
    )
    _set_auth_cookies(response, tokens.refresh_token)
    return TokenResponse(access_token=tokens.access_token, expires_in=_ACCESS_TTL_SECONDS)


@router.post(
    "/login",
    summary="Exchange email + password for tokens",
    description="Constant-time verification; sets refresh and CSRF cookies.",
    response_model=TokenResponse,
    responses={200: {"description": "Authenticated"}, 401: {"description": "Bad credentials"}},
)
async def login_endpoint(body: LoginRequest, request: Request, response: Response) -> TokenResponse:
    tokens = await service.login(
        email=body.email, password=body.password, actor_ip=_client_ip(request)
    )
    _set_auth_cookies(response, tokens.refresh_token)
    return TokenResponse(access_token=tokens.access_token, expires_in=_ACCESS_TTL_SECONDS)


@router.post(
    "/refresh",
    summary="Mint a new access token from the refresh cookie",
    description=(
        "Reads the HttpOnly refresh cookie (sent only to this path), verifies "
        "it against JWT_REFRESH_SECRET, and returns a fresh access token."
    ),
    response_model=TokenResponse,
    responses={200: {"description": "New access token"}, 401: {"description": "Invalid cookie"}},
)
async def refresh_endpoint(request: Request) -> TokenResponse:
    cookie = request.cookies.get(REFRESH_COOKIE, "")
    if not cookie:
        raise AuthenticationError("Refresh cookie missing")
    try:
        user_id = decode_refresh_token(cookie)
    except TokenError as exc:
        raise AuthenticationError(str(exc)) from exc

    # Claims must reflect CURRENT plan/role/status, not month-old ones.
    row = await service.lookup_claims(user_id)
    access = create_access_token(
        {
            "sub": user_id,
            "tid": str(row.tenant_id),
            "plan": row.plan,
            "role": row.role,
            "admin": False,
        }
    )
    return TokenResponse(access_token=access, expires_in=_ACCESS_TTL_SECONDS)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke the current access token and clear cookies",
    description="Blacklists the token's jti until natural expiry; clears both cookies.",
    responses={204: {"description": "Logged out"}},
)
async def logout_endpoint(request: Request, response: Response, _user: CurrentUser) -> None:
    authorization = request.headers.get("Authorization", "")
    token = authorization.partition(" ")[2]
    payload = await decode_access_token(token)  # already validated by CurrentUser
    await blacklist_token(payload.jti, ttl_seconds=_ACCESS_TTL_SECONDS)
    response.delete_cookie(REFRESH_COOKIE, path=REFRESH_COOKIE_PATH)
    response.delete_cookie(CSRF_COOKIE, path="/")
