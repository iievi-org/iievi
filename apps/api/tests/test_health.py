"""Health endpoint behaviour, including the static-key protection on /health/deep."""

import time

from fastapi.testclient import TestClient

from app.api.routes import health as health_module
from app.api.routes.health import DependencyStatus


def test_health_returns_version_and_uptime(client: TestClient) -> None:
    started = time.perf_counter()
    response = client.get("/health")
    elapsed_ms = (time.perf_counter() - started) * 1000

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"]
    assert body["commit"]
    assert body["uptime_seconds"] >= 0
    # DoD: must not touch the database — generous in-process bound
    assert elapsed_ms < 250


def test_health_version_reports_commit_and_timestamp(client: TestClient) -> None:
    response = client.get("/health/version")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"commit", "deployed_at", "version"}


def test_health_deep_rejects_missing_key(client: TestClient) -> None:
    response = client.get("/health/deep")
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "invalid_health_key"


def test_health_deep_rejects_wrong_key(client: TestClient) -> None:
    response = client.get("/health/deep", headers={"X-Health-Key": "wrong"})
    assert response.status_code == 401


def test_health_deep_reports_dependencies(client: TestClient, monkeypatch: object) -> None:
    import pytest

    mp = monkeypatch
    assert isinstance(mp, pytest.MonkeyPatch)

    async def fake_ok() -> DependencyStatus:
        return DependencyStatus(healthy=True, detail="connected")

    async def fake_down() -> DependencyStatus:
        return DependencyStatus(healthy=False, detail="ConnectionRefusedError")

    mp.setattr(health_module, "_check_database", fake_ok)
    mp.setattr(health_module, "_check_redis", fake_ok)
    mp.setattr(health_module, "_check_celery", fake_down)

    response = client.get("/health/deep", headers={"X-Health-Key": "test-health-key-0123456789"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["database"]["healthy"] is True
    assert body["celery"]["healthy"] is False


def test_request_id_header_present(client: TestClient) -> None:
    response = client.get("/health")
    assert response.headers.get("X-Request-ID")
