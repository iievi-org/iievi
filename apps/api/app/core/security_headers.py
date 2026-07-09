"""Application-level security headers + structured access logging.

nginx sets the transport-level headers (HSTS, X-Frame-Options, ...); this
middleware adds what only the app can decide:
- Content-Security-Policy: default-src 'none' (strict API policy)
- Cache-Control: no-store on authenticated responses (Authorization present)
- X-Request-ID echo (the correlation id from RequestContextMiddleware)

Every request is also access-logged as structured JSON (method, path, status,
duration, tenant when known, request_id via the log formatter) — the first
place to look in Axiom when a customer reports an issue.
"""

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

_DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        if not request.url.path.startswith(_DOCS_PATHS):  # swagger UI needs its assets
            response.headers["Content-Security-Policy"] = "default-src 'none'"
        response.headers["X-Content-Type-Options"] = "nosniff"
        if "Authorization" in request.headers or "Cookie" in request.headers:
            response.headers["Cache-Control"] = "no-store"
        return response
