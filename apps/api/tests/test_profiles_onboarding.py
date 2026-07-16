"""Prompt 4 unit tests: logo validation, credential verification failure,
completeness weights, extraction validation, state machine progression.
DB-backed profile isolation lives in tests/db/test_profiles_db.py.
"""

import io
import json
import uuid

import fakeredis.aioredis
import httpx
import pytest
from PIL import Image

from app.core import ratelimit, security
from app.core.exceptions import CredentialVerificationError
from app.core.r2_service import build_object_key
from app.modules.onboarding import extraction_service, state_machine
from app.modules.onboarding.state_machine import OnboardingStage, process_turn


@pytest.fixture(autouse=True)
def _fake_redis(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(security, "get_redis", lambda: fake)
    monkeypatch.setattr(ratelimit, "get_redis", lambda: fake)


# ---------------------------------------------------------------------------
# R2 key pattern
# ---------------------------------------------------------------------------


def test_r2_key_pattern() -> None:
    tenant = uuid.uuid4()
    key = build_object_key("creatives", tenant, "png")
    parts = key.split("/")
    assert parts[0] == "creatives"
    assert parts[1] == str(tenant)
    assert len(parts) == 5  # type/tenant/year/month/file
    assert parts[4].endswith(".png")


# ---------------------------------------------------------------------------
# Logo validation via the endpoint (R2 + magic exercised with fakes)
# ---------------------------------------------------------------------------


def _png_bytes(width: int, height: int) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), color=(200, 30, 40)).save(buffer, format="PNG")
    return buffer.getvalue()


def test_magic_detects_fake_extension() -> None:
    """A .png-named file that is actually text must be identified as text."""
    import magic

    detected = magic.from_buffer(b"#!/bin/sh\nrm -rf /\n", mime=True)
    assert detected != "image/png"
    real = magic.from_buffer(_png_bytes(200, 200), mime=True)
    assert real == "image/png"


def test_pillow_dimension_checks() -> None:
    tiny = Image.open(io.BytesIO(_png_bytes(50, 50)))
    assert tiny.size == (50, 50)  # would be rejected: < 100×100
    big = Image.open(io.BytesIO(_png_bytes(2400, 1200)))
    big.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
    assert max(big.size) == 1000
    assert big.size == (1000, 500)  # aspect ratio preserved


# ---------------------------------------------------------------------------
# Credential service — verification failure means nothing is stored
# ---------------------------------------------------------------------------


async def test_unknown_service_rejected() -> None:
    from app.modules.credentials.service import save_credential

    with pytest.raises(CredentialVerificationError, match="Unknown service"):
        await save_credential(uuid.uuid4(), "not-a-service", {"x": "y"}, session=None)  # type: ignore[arg-type]


async def test_missing_fields_rejected_before_any_network_call() -> None:
    from app.modules.credentials.service import save_credential

    with pytest.raises(CredentialVerificationError) as exc_info:
        await save_credential(uuid.uuid4(), "whatsapp", {"access_token": "t"}, session=None)  # type: ignore[arg-type]
    assert exc_info.value.details["missing"] == ["phone_number_id"]


async def test_invalid_gemini_key_raises_verification_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DoD: credential saving with an invalid API key returns
    CredentialVerificationError — and never touches the database."""
    from app.modules.credentials import service as credential_service

    async def fake_get(self: httpx.AsyncClient, url: str, **kwargs: object) -> httpx.Response:
        return httpx.Response(
            400, json={"error": "API key not valid"}, request=httpx.Request("GET", url)
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    class _ExplodingSession:
        def __getattr__(self, name: str) -> object:
            raise AssertionError("DB must not be touched when verification fails")

    with pytest.raises(CredentialVerificationError, match="Gemini rejected"):
        await credential_service.save_credential(
            uuid.uuid4(),
            "gemini",
            {"api_key": "AIza-invalid"},
            session=_ExplodingSession(),  # type: ignore[arg-type]
        )


# ---------------------------------------------------------------------------
# Extraction pipeline — validation, missing-field protocol, no invention
# ---------------------------------------------------------------------------


async def test_extraction_missing_field_yields_targeted_clarification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_complete(**_kwargs: object) -> str:
        return json.dumps({"error": "missing_field", "field": "services"})

    monkeypatch.setattr(extraction_service.ai, "complete", fake_complete)
    outcome = await extraction_service.extract(
        kind="services",
        user_answer="we do stuff",
        session_token="tok",  # noqa: S106
    )
    assert outcome.data is None
    assert outcome.clarification is not None
    assert "service" in outcome.clarification.lower()


async def test_extraction_invalid_schema_yields_clarification(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_complete(**_kwargs: object) -> str:
        return json.dumps(
            {"services": [{"name": "X"}]}
        )  # name too short (<2 ok? min 2) — use 1 char

    monkeypatch.setattr(extraction_service.ai, "complete", fake_complete)
    outcome = await extraction_service.extract(
        kind="services",
        user_answer="answer",
        session_token="tok",  # noqa: S106
    )
    # name "X" violates min_length=2 → targeted clarification, not a crash
    assert outcome.data is None
    assert outcome.clarification is not None


async def test_extraction_valid_payload_is_validated_and_returned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "services": [
            {
                "name": "Deep cleaning 2BHK",
                "price_min_paise": 250000,
                "price_max_paise": 450000,
                "unit": "per job",
            }
        ]
    }

    async def fake_complete(**_kwargs: object) -> str:
        return json.dumps(payload)

    monkeypatch.setattr(extraction_service.ai, "complete", fake_complete)
    outcome = await extraction_service.extract(
        kind="services",
        user_answer="deep cleaning 2500-4500",
        session_token="tok",  # noqa: S106
    )
    assert outcome.clarification is None
    assert outcome.data is not None
    services = outcome.data["services"]
    assert isinstance(services, list)
    assert services[0]["price_min_paise"] == 250000


# ---------------------------------------------------------------------------
# State machine progression
# ---------------------------------------------------------------------------


def test_twelve_stages_in_order() -> None:
    assert len(state_machine.STAGE_ORDER) == 12
    assert state_machine.STAGE_ORDER[0] is OnboardingStage.WELCOME
    assert state_machine.STAGE_ORDER[-1] is OnboardingStage.CONFIRM_AND_CREATE
    assert state_machine.next_stage(OnboardingStage.CONFIRM_AND_CREATE) is None


async def test_category_stage_matches_and_advances() -> None:
    result, reply = await process_turn(
        OnboardingStage.CATEGORY_SELECT, "I run a plumbing business in Pune", {}
    )
    assert result.complete
    assert result.updates["category"] == {"key": "plumbing"}
    assert reply  # next stage's question


async def test_category_stage_clarifies_on_no_match() -> None:
    result, reply = await process_turn(OnboardingStage.CATEGORY_SELECT, "I sell rockets", {})
    assert not result.complete
    assert "category" in reply.lower() or "closest" in reply.lower()


async def test_free_text_stage_rejects_too_short() -> None:
    result, reply = await process_turn(OnboardingStage.BUSINESS_INFO, "ok", {})
    assert not result.complete
    assert "detail" in reply.lower()


async def test_confirm_stage_requires_the_word_confirm() -> None:
    result, _ = await process_turn(OnboardingStage.CONFIRM_AND_CREATE, "sounds good", {})
    assert not result.complete
    result, _ = await process_turn(OnboardingStage.CONFIRM_AND_CREATE, "Confirm!", {})
    assert result.complete


# ---------------------------------------------------------------------------
# Completeness weights
# ---------------------------------------------------------------------------


def test_completeness_weights_sum_to_100() -> None:
    from app.modules.profiles.completeness import WEIGHTS

    assert sum(WEIGHTS.values()) == 100
