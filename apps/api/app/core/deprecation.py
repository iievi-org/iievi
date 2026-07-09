"""API version deprecation headers (RFC 8594).

When a v2 equivalent exists for a v1 route, add its path prefix to
DEPRECATED_V1_PREFIXES with the sunset date. Until then this middleware is a
no-op passthrough — but the mechanism exists from day one, so deprecating an
endpoint is a one-line change instead of an architecture project.
"""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# prefix -> sunset date (HTTP-date string), e.g.
# "/api/v1/posts": "Sat, 01 Aug 2026 00:00:00 GMT"
DEPRECATED_V1_PREFIXES: dict[str, str] = {}


class DeprecationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        for prefix, sunset in DEPRECATED_V1_PREFIXES.items():
            if request.url.path.startswith(prefix):
                response.headers["Deprecation"] = "true"
                response.headers["Sunset"] = sunset
                response.headers["Link"] = (
                    f'<{prefix.replace("/v1/", "/v2/")}>; rel="successor-version"'
                )
                break
        return response
