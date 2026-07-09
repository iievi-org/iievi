"""Test fixtures.

Required environment variables are injected BEFORE any app import so that
config validation passes without Doppler. Values are deliberately fake.
"""

import os

_TEST_ENV = {
    "ENVIRONMENT": "development",
    "DATABASE_URL": "postgresql+asyncpg://iievi:iievi@localhost:5432/iievi_test",
    "REDIS_URL": "redis://localhost:6379/1",
    "JWT_SECRET": "test-jwt-secret-0123456789abcdef0123456789abcdef",
    "ENCRYPTION_MASTER_KEY": "test-master-key-0123456789abcdef0123456789abcdef",
    "HEALTH_API_KEY": "test-health-key-0123456789",
    "DOCS_KEY": "test-docs-key-0123456789abc",
    "SENTRY_DSN": "",
}
for _key, _value in _TEST_ENV.items():
    os.environ.setdefault(_key, _value)

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)
