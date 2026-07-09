"""Request-scoped context variables.

request_id is generated per request by RequestContextMiddleware; tenant_id is
set by the auth layer once a JWT is validated. Both are picked up by the JSON
log formatter so every log line in a request shares the same identifiers.
"""

from contextvars import ContextVar

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
tenant_id_var: ContextVar[str | None] = ContextVar("tenant_id", default=None)
