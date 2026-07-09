"""FastAPI application factory.

Middleware stack, OUTERMOST first (Starlette runs the last-added middleware
first on the request, so registration order below is the REVERSE):

    Sentry (auto-injected by sentry_sdk init)
      → RequestContextMiddleware (correlation id, access log)
        → SecurityHeadersMiddleware (CSP, no-store)
          → RateLimitMiddleware (IP + tenant tiers)
            → CSRFMiddleware (synchronizer token)
              → CORSMiddleware (strict origin list)
                → DeprecationMiddleware (RFC 8594 v1 sunset headers)
                  → GZipMiddleware (responses > 1024 bytes)
                    → routers

All product routes live under /api/v1/. Health endpoints stay unversioned at
the root — the deploy pipeline and Uptime Robot depend on those exact paths.
In production /docs, /redoc, and /openapi.json require the X-Docs-Key header.
"""

import secrets
from collections.abc import Awaitable, Callable

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.health import router as health_router
from app.core.config import settings
from app.core.csrf import CSRFMiddleware
from app.core.deprecation import DeprecationMiddleware
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.core.ratelimit import RateLimitMiddleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.sentry import init_sentry
from app.modules.auth.router import router as auth_router
from app.modules.billing.router import router as billing_router
from app.modules.flags.router import router as flags_router

OPENAPI_DESCRIPTION = """
IIEVI — one AI-powered chat interface for service businesses to run their
entire client acquisition pipeline: social publishing, lead capture, AI
conversations, and bookings.

Authentication: short-lived JWT Bearer access tokens from `/api/v1/auth/login`,
passed as `Authorization: Bearer <token>`. Refresh happens via the HttpOnly
cookie bound to `/api/v1/auth/refresh`. State-changing requests from browsers
must echo the `csrf_token` cookie in the `X-CSRF-Token` header.
"""

DOCS_PATHS = frozenset({"/docs", "/redoc", "/openapi.json"})

API_V1_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    """Build the configured application instance."""
    configure_logging(settings.log_level)
    init_sentry(
        dsn=settings.sentry_dsn,
        environment=settings.environment.value,
        release=settings.git_commit_sha,
    )

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description=OPENAPI_DESCRIPTION,
        contact={"name": "IIEVI Engineering", "email": "sattvacare.in@gmail.com"},
        docs_url="/docs",
        redoc_url="/redoc",
    )

    register_exception_handlers(app)

    # --- middleware: added INNERMOST-first (LIFO — see module docstring) ---
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.add_middleware(DeprecationMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-CSRF-Token"],
        max_age=86400,
    )
    app.add_middleware(CSRFMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestContextMiddleware)
    # Sentry's ASGI middleware wraps everything via its FastAPI integration.

    if settings.is_production:

        @app.middleware("http")
        async def protect_docs(
            request: Request,
            call_next: Callable[[Request], Awaitable[Response]],
        ) -> Response:
            """In production the API reference requires the X-Docs-Key secret."""
            if request.url.path in DOCS_PATHS:
                provided = request.headers.get("X-Docs-Key", "")
                if not secrets.compare_digest(provided, settings.docs_key):
                    return JSONResponse(
                        status_code=404,
                        content={"code": "not_found", "message": "Not Found", "details": {}},
                    )
            return await call_next(request)

    # --- routes ------------------------------------------------------------
    app.include_router(health_router)  # unversioned: /health*

    v1 = APIRouter(prefix=API_V1_PREFIX)
    v1.include_router(auth_router)
    v1.include_router(billing_router)
    v1.include_router(flags_router)
    app.include_router(v1)

    def custom_openapi() -> dict[str, object]:
        if app.openapi_schema:
            return app.openapi_schema
        from fastapi.openapi.utils import get_openapi

        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            contact=app.contact,
            routes=app.routes,
        )
        schema.setdefault("components", {}).setdefault("securitySchemes", {})["BearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Short-lived access token (15 min) from /api/v1/auth/login.",
        }
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi  # type: ignore[method-assign]

    return app


app = create_app()
