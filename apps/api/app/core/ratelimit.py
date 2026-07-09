"""Three-tier Redis rate limiting.

Tier 1 (middleware): 200 req/min per IP (X-Real-IP from nginx).
Tier 2 (middleware): 100 req/min per tenant, authenticated requests only.
Tier 3 (dependency): 20 AI calls/hour per tenant, attached to AI endpoints
via `Depends(ai_rate_limit)`.

Keys: ratelimit:{tier}:{identifier}:{window} with TTL = window size, so
counters clean themselves up. Fixed-window is acceptable at these limits.
On Redis outage the limiter FAILS OPEN (availability over throttling) and
logs an error — the global nginx/Cloudflare layers still stand in front.
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.exceptions import RateLimitError
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

GLOBAL_IP_LIMIT = 200  # per minute
TENANT_LIMIT = 100  # per minute
AI_LIMIT = 20  # per hour

_EXEMPT_PATHS = ("/health", "/docs", "/redoc", "/openapi.json")


async def _hit(tier: str, identifier: str, window_seconds: int, limit: int) -> tuple[bool, int]:
    """Increment the counter; returns (allowed, remaining)."""
    window = int(time.time()) // window_seconds
    key = f"ratelimit:{tier}:{identifier}:{window}"
    try:
        redis = get_redis()
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, window_seconds)
    except Exception:  # noqa: BLE001 — fail open, never take the API down
        logger.error("rate limiter Redis unavailable — failing open")
        return True, limit
    return count <= limit, max(0, limit - int(count))


def _limited_response(limit: int, retry_after: int) -> Response:
    return JSONResponse(
        status_code=429,
        content={
            "code": "rate_limited",
            "message": "Too many requests — slow down",
            "details": {"limit": limit},
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": "0",
        },
    )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Tiers 1 and 2. Tier 3 is per-endpoint (see ai_rate_limit)."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path.startswith(_EXEMPT_PATHS):
            return await call_next(request)

        # Tier 1 — per IP. Trust X-Real-IP (nginx) over the socket peer.
        ip = request.headers.get("X-Real-IP") or (
            request.client.host if request.client else "unknown"
        )
        allowed, remaining = await _hit("ip", ip, 60, GLOBAL_IP_LIMIT)
        if not allowed:
            return _limited_response(GLOBAL_IP_LIMIT, 60)

        # Tier 2 — per tenant, BEFORE the handler runs. The token is decoded
        # here only to identify the tenant (cheap HMAC); real authentication
        # still happens in get_current_user. Invalid tokens skip tier 2 and
        # get their 401 from the auth dependency.
        tenant_id = await self._tenant_from_token(request)
        if tenant_id is not None:
            t_allowed, t_remaining = await _hit("tenant", tenant_id, 60, TENANT_LIMIT)
            if not t_allowed:
                return _limited_response(TENANT_LIMIT, 60)
            remaining = min(remaining, t_remaining)

        response = await call_next(request)
        response.headers.setdefault("X-RateLimit-Remaining", str(remaining))
        return response

    @staticmethod
    async def _tenant_from_token(request: Request) -> str | None:
        authorization = request.headers.get("Authorization", "")
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return None
        from app.core.security import TokenError, decode_access_token

        try:
            payload = await decode_access_token(token)
        except TokenError:
            return None
        return payload.tid


async def ai_rate_limit(request: Request) -> None:
    """Tier 3 dependency — 20 AI generations/hour/tenant. Order AFTER auth:

    dependencies=[Depends(get_current_user), Depends(ai_rate_limit)]
    """
    user = getattr(request.state, "user", None)
    if user is None:  # defensive: endpoint forgot get_current_user
        raise RateLimitError("AI endpoints require authentication before rate limiting")
    allowed, remaining = await _hit("ai", str(user.tenant_id), 3600, AI_LIMIT)
    if not allowed:
        raise RateLimitError(
            "AI generation limit reached (20/hour) — try again later",
            details={
                "Retry-After": "3600",
                "X-RateLimit-Limit": str(AI_LIMIT),
                "X-RateLimit-Remaining": "0",
            },
        )
