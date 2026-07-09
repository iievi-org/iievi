"""FastAPI application factory.

OpenAPI documentation is the contract between backend and frontend: every route
must carry a summary, description, and response examples. In production, /docs,
/redoc, and /openapi.json require an X-Docs-Key header matching the
Doppler-stored DOCS_KEY secret.
"""

import secrets
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes.health import router as health_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.core.sentry import init_sentry

OPENAPI_DESCRIPTION = """
IIEVI — one AI-powered chat interface for service businesses to run their
entire client acquisition pipeline: social publishing, lead capture, AI
conversations, and bookings.

Authentication uses short-lived JWT Bearer access tokens. Obtain tokens via
the auth endpoints (added in a later phase); pass them as
`Authorization: Bearer <token>`.
"""

DOCS_PATHS = frozenset({"/docs", "/redoc", "/openapi.json"})


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
        contact={
            "name": "IIEVI Engineering",
            "email": "sattvacare.in@gmail.com",
        },
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        max_age=86400,
    )

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
                        content={
                            "code": "not_found",
                            "message": "Not Found",
                            "details": {},
                        },
                    )
            return await call_next(request)

    app.include_router(health_router)

    # JWT Bearer security scheme in the OpenAPI schema so /docs shows the
    # Authorize button; routes opt in via dependencies in later phases.
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
        schema.setdefault("components", {}).setdefault("securitySchemes", {})[
            "BearerAuth"
        ] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Short-lived access token (15 min) issued by the auth endpoints.",
        }
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi  # type: ignore[method-assign]

    return app


app = create_app()
