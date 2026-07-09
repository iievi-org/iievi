"""Typed exception hierarchy and global handlers.

Every error the API emits — custom exceptions, validation errors, bare
HTTPExceptions — is normalised to one JSON shape:

    {"code": "...", "message": "...", "details": {...}}

The frontend must never see two different error response structures.
4xx are logged at WARNING, 5xx at ERROR (Sentry picks those up).
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class IIEVIException(Exception):  # noqa: N818 — project-spec name
    """Base for all application errors. Subclasses fix status_code and code."""

    status_code = 500
    code = "internal_error"

    def __init__(
        self,
        message: str,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details: dict[str, object] = details or {}


class AuthenticationError(IIEVIException):
    status_code = 401
    code = "authentication_failed"


class AuthorizationError(IIEVIException):
    status_code = 403
    code = "forbidden"


class PlanLimitError(IIEVIException):
    status_code = 402
    code = "plan_limit_reached"

    def __init__(self, message: str, *, current_count: int, limit: int, upgrade_to: str) -> None:
        super().__init__(
            message,
            details={"current_count": current_count, "limit": limit, "upgrade_to": upgrade_to},
        )


class BadRequestError(IIEVIException):
    status_code = 400
    code = "bad_request"


class ProfileIncompleteError(IIEVIException):
    status_code = 400
    code = "profile_incomplete"


class CredentialVerificationError(IIEVIException):
    status_code = 400
    code = "credential_verification_failed"


class ResourceNotFoundError(IIEVIException):
    status_code = 404
    code = "not_found"


class AIGenerationError(IIEVIException):
    status_code = 503
    code = "ai_generation_failed"


class ExternalAPIError(IIEVIException):
    status_code = 502
    code = "external_api_error"


class RateLimitError(IIEVIException):
    status_code = 429
    code = "rate_limited"


class WebhookSignatureError(IIEVIException):
    status_code = 401
    code = "webhook_signature_invalid"


def _error_response(
    status_code: int, code: str, message: str, details: dict[str, object]
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "message": message, "details": details},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Install the three handlers that guarantee a single error shape."""

    @app.exception_handler(IIEVIException)
    async def handle_iievi(request: Request, exc: IIEVIException) -> JSONResponse:
        log = logger.error if exc.status_code >= 500 else logger.warning
        log(
            "request failed: %s",
            exc.message,
            extra={"code": exc.code, "path": request.url.path, "status": exc.status_code},
        )
        response = _error_response(exc.status_code, exc.code, exc.message, exc.details)
        if isinstance(exc, RateLimitError):
            for header, value in exc.details.items():
                if header.lower().startswith(("retry-after", "x-ratelimit")):
                    response.headers[str(header)] = str(value)
        return response

    @app.exception_handler(RequestValidationError)
    async def handle_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {
                "field": ".".join(str(loc) for loc in err.get("loc", []) if loc != "body"),
                "message": str(err.get("msg", "invalid")),
            }
            for err in exc.errors()
        ]
        logger.warning("validation failed", extra={"path": request.url.path, "errors": errors})
        return _error_response(
            422, "validation_error", "Request validation failed", {"errors": errors}
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        # A handler that already raised our envelope shape passes through intact
        raw_detail: object = exc.detail
        if isinstance(raw_detail, dict) and {"code", "message"} <= set(raw_detail):
            inner = raw_detail.get("details")
            return _error_response(
                exc.status_code,
                str(raw_detail["code"]),
                str(raw_detail["message"]),
                inner if isinstance(inner, dict) else {},
            )
        log = logger.error if exc.status_code >= 500 else logger.warning
        log("http error", extra={"path": request.url.path, "status": exc.status_code})
        return _error_response(exc.status_code, "http_error", str(exc.detail), {})
