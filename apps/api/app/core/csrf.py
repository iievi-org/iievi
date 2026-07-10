"""CSRF protection — Synchronizer Token Pattern.

Login/registration set a `csrf_token` cookie that is deliberately NOT
HttpOnly: the frontend JavaScript reads it and repeats it in the
X-CSRF-Token header on every state-changing request. A cross-site attacker
can make the browser SEND our cookies but can never READ them, so it cannot
produce the matching header.

Exempt: /api/v1/auth/* (the bootstrap point — protected instead by the
SameSite=Strict refresh cookie and the fact that login requires the password
in the body), health checks, docs, and incoming platform webhooks (which are
authenticated by signature, not cookies — added in the webhook phase).
"""

import secrets

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

CSRF_COOKIE = "csrf_token"
CSRF_HEADER = "X-CSRF-Token"

_STATE_CHANGING = frozenset({"POST", "PUT", "PATCH", "DELETE"})
# onboarding + its analytics are pre-login (no CSRF cookie exists yet); the
# onboarding session cookie is HttpOnly + SameSite=Lax and path-scoped.
_EXEMPT_PREFIXES = (
    "/api/v1/auth/",
    "/api/v1/onboarding/",
    "/api/v1/analytics/onboarding-event",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/webhooks",
    # Platform webhooks are authenticated by HMAC signature, not cookies
    "/api/v1/webhooks/",
)


def issue_csrf_token() -> str:
    return secrets.token_hex(32)


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method not in _STATE_CHANGING or request.url.path.startswith(_EXEMPT_PREFIXES):
            return await call_next(request)

        # Pure-API clients (no cookies at all) are not CSRF-attackable — the
        # attack requires ambient cookie credentials. Enforce only when the
        # browser sent cookies.
        if "Cookie" not in request.headers:
            return await call_next(request)

        cookie_value = request.cookies.get(CSRF_COOKIE, "")
        header_value = request.headers.get(CSRF_HEADER, "")
        if not cookie_value or not secrets.compare_digest(cookie_value, header_value):
            return JSONResponse(
                status_code=403,
                content={
                    "code": "csrf_verification_failed",
                    "message": "Missing or mismatched X-CSRF-Token header",
                    "details": {},
                },
            )
        return await call_next(request)
