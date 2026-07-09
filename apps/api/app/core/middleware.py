"""ASGI middleware for request-scoped context.

Generates a UUID request_id per request, stores it in a context variable for
the JSON log formatter, and echoes it back as an X-Request-ID response header
so support tickets can be correlated with server logs.
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.context import request_id_var

logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Thread request_id through context variables and log request completion."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers["X-Request-ID"] = request_id
        duration_ms = round((time.perf_counter() - started) * 1000, 1)
        log = logger.warning if response.status_code >= 400 else logger.info
        log(
            "request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                # request_id is injected by the formatter from the contextvar,
                # but the var is already reset here — pass it explicitly.
                "request_id": request_id,
            },
        )
        return response
