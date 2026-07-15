"""Hallucination suite fixtures.

The suite makes REAL provider calls (grounded generation + an LLM judge), so it
requires a live key. It skips cleanly when GEMINI_API_KEY is unset locally, but
is REQUIRED in CI (set REQUIRE_HALLUCINATION_TESTS=1) — a single failing
invariant must block deployment.
"""

import os

import pytest

from app.core.config import settings


@pytest.fixture(autouse=True)
def _require_provider_key() -> None:
    if not settings.gemini_api_key:
        if os.environ.get("REQUIRE_HALLUCINATION_TESTS") == "1":
            pytest.fail("hallucination suite REQUIRED in CI but GEMINI_API_KEY is unset")
        pytest.skip("GEMINI_API_KEY unset — hallucination suite needs a real key")
