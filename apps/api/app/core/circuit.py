"""Redis-backed circuit breakers for every external API.

State lives in Redis so it is shared across ALL processes — API workers and
every Celery worker see the same circuit. In-process breakers (the
`circuitbreaker` library's default) would let each of N worker processes
independently hammer a dead service five more times; sharing the state means
the platform backs off as one.

Semantics (matching the classic pattern):
- CLOSED: calls pass through; consecutive expected failures are counted.
- OPEN:   after `failure_threshold` consecutive failures the circuit opens
          for `recovery_timeout` seconds; every call fails fast with
          CircuitOpenError (no network I/O at all).
- HALF-OPEN: when the open key expires, the next call is the trial. Success
          resets the failure counter (CLOSED); failure re-opens immediately
          because the counter is still at/above the threshold.

Keys: circuit:{name}:open (TTL = recovery window), circuit:{name}:failures.
Celery tasks that hit an open circuit should retry with a ~60s countdown
rather than queueing calls that are all going to fail.
"""

import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

import httpx

from app.core.exceptions import CircuitOpenError, ExternalAPIError
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

T = TypeVar("T")

FAILURE_THRESHOLD = 5
RECOVERY_TIMEOUT_S = 60

# Exceptions that count as "the service is unhealthy". Anything else (bugs,
# validation errors) propagates without touching the failure counter.
EXPECTED_EXCEPTIONS: tuple[type[Exception], ...] = (
    httpx.ConnectError,
    httpx.TimeoutException,
    ExternalAPIError,
)

# Every external dependency gets exactly one named circuit.
CIRCUIT_NAMES: tuple[str, ...] = (
    "gemini",
    "meta",
    "whatsapp",
    "tiktok",
    "linkedin",
    "razorpay",
    "stripe",
)


class CircuitBreaker:
    """One named, Redis-shared circuit. Use via the module-level registry."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = FAILURE_THRESHOLD,
        recovery_timeout: int = RECOVERY_TIMEOUT_S,
        expected_exception: tuple[type[Exception], ...] = EXPECTED_EXCEPTIONS,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

    @property
    def _open_key(self) -> str:
        return f"circuit:{self.name}:open"

    @property
    def _failures_key(self) -> str:
        return f"circuit:{self.name}:failures"

    async def is_open(self) -> bool:
        return bool(await get_redis().exists(self._open_key))

    async def call(self, fn: Callable[..., Awaitable[T]], *args: object, **kwargs: object) -> T:
        """Run `fn` through the circuit; raise CircuitOpenError when open."""
        redis = get_redis()
        if await redis.exists(self._open_key):
            raise CircuitOpenError(
                f"{self.name} circuit is open — failing fast",
                details={"circuit": self.name, "retry_after_seconds": self.recovery_timeout},
            )
        try:
            result = await fn(*args, **kwargs)
        except self.expected_exception as exc:
            failures = int(await redis.incr(self._failures_key))
            if failures >= self.failure_threshold:
                await redis.set(self._open_key, "1", ex=self.recovery_timeout)
                logger.error(
                    "circuit opened",
                    extra={"circuit": self.name, "consecutive_failures": failures},
                )
            raise ExternalAPIError(
                f"{self.name} call failed", details={"circuit": self.name}
            ) from exc
        await redis.delete(self._failures_key)
        return result

    async def reset(self) -> None:
        """Force-close (operations tooling / tests)."""
        redis = get_redis()
        await redis.delete(self._open_key)
        await redis.delete(self._failures_key)


CIRCUITS: dict[str, CircuitBreaker] = {name: CircuitBreaker(name) for name in CIRCUIT_NAMES}


def get_circuit(name: str) -> CircuitBreaker:
    """Return the shared breaker for `name`; unknown names fail at call time."""
    try:
        return CIRCUITS[name]
    except KeyError as exc:  # a typo here must never silently skip protection
        msg = f"unknown circuit: {name}"
        raise ValueError(msg) from exc


async def open_circuit_names() -> list[str]:
    """Names of currently-open circuits — consumed by the beat monitor."""
    names = []
    for name, breaker in CIRCUITS.items():
        if await breaker.is_open():
            names.append(name)
    return names
