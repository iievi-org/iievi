"""Circuit breaker DoD: opens after 5 consecutive failures, rejects
subsequent calls immediately (no network I/O), recovers half-open."""

import fakeredis.aioredis
import httpx
import pytest

from app.core import circuit as circuit_module
from app.core.circuit import CircuitBreaker
from app.core.exceptions import CircuitOpenError, ExternalAPIError


@pytest.fixture()
def _fake_redis(monkeypatch: pytest.MonkeyPatch) -> fakeredis.aioredis.FakeRedis:
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(circuit_module, "get_redis", lambda: fake)
    return fake


async def _failing_call() -> None:
    raise httpx.ConnectError("connection refused")


async def test_opens_after_five_consecutive_failures(
    _fake_redis: fakeredis.aioredis.FakeRedis,
) -> None:
    """DoD: the breaker opens after 5 simulated failures and then rejects
    immediately with CircuitOpenError."""
    breaker = CircuitBreaker("gemini")

    for _ in range(5):
        with pytest.raises(ExternalAPIError):
            await breaker.call(_failing_call)

    assert await breaker.is_open()

    calls = 0

    async def _would_succeed() -> str:
        nonlocal calls
        calls += 1
        return "ok"

    with pytest.raises(CircuitOpenError):
        await breaker.call(_would_succeed)
    assert calls == 0  # rejected BEFORE any I/O


async def test_success_resets_failure_counter(
    _fake_redis: fakeredis.aioredis.FakeRedis,
) -> None:
    breaker = CircuitBreaker("meta")
    for _ in range(4):
        with pytest.raises(ExternalAPIError):
            await breaker.call(_failing_call)

    async def _ok() -> str:
        return "ok"

    assert await breaker.call(_ok) == "ok"
    # Counter reset: four more failures still don't open the circuit
    for _ in range(4):
        with pytest.raises(ExternalAPIError):
            await breaker.call(_failing_call)
    assert not await breaker.is_open()


async def test_half_open_trial_after_recovery_window(
    _fake_redis: fakeredis.aioredis.FakeRedis,
) -> None:
    breaker = CircuitBreaker("whatsapp")
    for _ in range(5):
        with pytest.raises(ExternalAPIError):
            await breaker.call(_failing_call)
    assert await breaker.is_open()

    # Simulate the recovery window elapsing (the open key expires)
    await _fake_redis.delete("circuit:whatsapp:open")

    async def _ok() -> str:
        return "ok"

    assert await breaker.call(_ok) == "ok"  # half-open trial succeeds → closed
    assert not await breaker.is_open()
    assert await _fake_redis.get("circuit:whatsapp:failures") is None


async def test_half_open_failure_reopens_immediately(
    _fake_redis: fakeredis.aioredis.FakeRedis,
) -> None:
    breaker = CircuitBreaker("tiktok")
    for _ in range(5):
        with pytest.raises(ExternalAPIError):
            await breaker.call(_failing_call)
    await _fake_redis.delete("circuit:tiktok:open")

    with pytest.raises(ExternalAPIError):  # the trial call fails
        await breaker.call(_failing_call)
    assert await breaker.is_open()  # …and the circuit is open again


async def test_unexpected_exceptions_do_not_trip_the_breaker(
    _fake_redis: fakeredis.aioredis.FakeRedis,
) -> None:
    """Bugs (ValueError etc.) propagate without counting as service failures."""
    breaker = CircuitBreaker("linkedin")

    async def _bug() -> None:
        raise ValueError("programming error")

    for _ in range(6):
        with pytest.raises(ValueError, match="programming error"):
            await breaker.call(_bug)
    assert not await breaker.is_open()


async def test_unknown_circuit_name_is_a_hard_error(
    _fake_redis: fakeredis.aioredis.FakeRedis,
) -> None:
    from app.core.circuit import get_circuit

    with pytest.raises(ValueError, match="unknown circuit"):
        get_circuit("not-a-service")
