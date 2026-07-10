"""AI layer: traced call cost/budget accounting, context cache behaviour,
copy generation validation-retry contract, intent classification routing."""

import json
import uuid
from types import SimpleNamespace

import fakeredis.aioredis
import pytest

from app.core.exceptions import AIGenerationError

TENANT_ID = uuid.uuid4()


# ---------------------------------------------------------------------------
# Cost estimation + daily budget alarm (DoD: estimated cost is computed and
# the $5/day ceiling triggers the ops warning)
# ---------------------------------------------------------------------------


def test_cost_estimation_uses_model_pricing() -> None:
    from app.modules.ai.langfuse_client import estimate_cost_usd

    # 1M input tokens at $0.30 + 1M output at $2.50
    assert estimate_cost_usd("gemini-2.5-flash", 1_000_000, 1_000_000) == pytest.approx(2.80)
    assert estimate_cost_usd("unknown-model", 1_000_000, 1_000_000) == 0.0


async def test_daily_budget_alarm_fires_over_five_dollars(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.modules.ai import langfuse_client

    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(langfuse_client, "get_redis", lambda: fake)
    alerts: list[str] = []
    monkeypatch.setattr(langfuse_client, "notify_ops", alerts.append)

    await langfuse_client.track_daily_spend(TENANT_ID, 4.99)
    assert alerts == []
    await langfuse_client.track_daily_spend(TENANT_ID, 0.02)
    assert len(alerts) == 1
    assert str(TENANT_ID) in alerts[0]


async def test_traced_ai_call_returns_usage_and_meters_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.core import circuit as circuit_module
    from app.modules.ai import langfuse_client

    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(langfuse_client, "get_redis", lambda: fake)
    monkeypatch.setattr(circuit_module, "get_redis", lambda: fake)

    class _FakeModels:
        async def generate_content(self, **_kwargs: object) -> object:
            return SimpleNamespace(
                text="hello",
                usage_metadata=SimpleNamespace(prompt_token_count=100, candidates_token_count=50),
            )

    class _FakeClient:
        def __init__(self, **_kwargs: object) -> None:
            self.aio = SimpleNamespace(models=_FakeModels())

    monkeypatch.setattr(langfuse_client.genai, "Client", _FakeClient)

    result = await langfuse_client.traced_ai_call(
        api_key="fake-key",
        system="You are helpful",
        user_message="hi",
        call_type="test",
        tenant_id=TENANT_ID,
    )
    assert result.text == "hello"
    assert result.input_tokens == 100
    assert result.output_tokens == 50
    assert result.estimated_cost_usd > 0
    # Budget key was written for today
    keys = await fake.keys(f"ai_cost:{TENANT_ID}:*")
    assert len(keys) == 1


# ---------------------------------------------------------------------------
# Context cache: 5-minute Redis cache, invalidation drops it
# ---------------------------------------------------------------------------


async def test_context_cache_hit_skips_database(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.ai import context_service

    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(context_service, "get_redis", lambda: fake)

    cached = context_service.TenantAIContext(
        tenant_id=str(TENANT_ID), business_name="Sattva Spa", category="salon_spa"
    )
    await fake.set(f"ctx:{TENANT_ID}", cached.model_dump_json())

    class _ExplodingSession:
        def __getattr__(self, name: str) -> object:
            raise AssertionError("DB must not be touched on a cache hit")

    context = await context_service.assemble_tenant_context(
        TENANT_ID,
        _ExplodingSession(),  # type: ignore[arg-type]
    )
    assert context.business_name == "Sattva Spa"


async def test_context_invalidation_deletes_key(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.ai import context_service

    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(context_service, "get_redis", lambda: fake)
    await fake.set(f"ctx:{TENANT_ID}", "{}")
    await context_service.invalidate_tenant_context(TENANT_ID)
    assert await fake.get(f"ctx:{TENANT_ID}") is None


# ---------------------------------------------------------------------------
# Copy generation: platform validation + one correction retry
# ---------------------------------------------------------------------------

_VALID_COPY = {
    "caption": "Monsoon special: 20% off deep-conditioning treatments this week!",
    "hashtags": ["#salon", "#monsoon"],
    "call_to_action": "Book your slot on WhatsApp today",
    "image_description": "A serene salon interior with warm lighting and plants",
    "template_style": "warm-minimal",
}


def _patch_copy_dependencies(monkeypatch: pytest.MonkeyPatch, responses: list[str]) -> list[dict]:
    """Stub context, credential, and the traced call (popping from responses)."""
    from app.modules.ai.context_service import TenantAIContext
    from app.modules.ai.langfuse_client import AICallResult
    from app.modules.credentials.service import DecryptedCredential
    from app.modules.posts import copy_generation_service as svc

    calls: list[dict] = []

    async def _fake_context(*_a: object, **_k: object) -> TenantAIContext:
        return TenantAIContext(
            tenant_id=str(TENANT_ID), business_name="Sattva Spa", category="salon_spa"
        )

    async def _fake_credential(*_a: object, **_k: object) -> DecryptedCredential:
        return DecryptedCredential(service="gemini", fields={"api_key": "fake"})

    async def _fake_traced(**kwargs: object) -> AICallResult:
        calls.append(dict(kwargs))
        return AICallResult(
            text=responses.pop(0),
            input_tokens=10,
            output_tokens=10,
            latency_ms=5,
            model="gemini-2.5-flash",
            estimated_cost_usd=0.0,
        )

    monkeypatch.setattr(svc, "assemble_tenant_context", _fake_context)
    monkeypatch.setattr(svc, "get_decrypted_credential", _fake_credential)
    monkeypatch.setattr(svc, "traced_ai_call", _fake_traced)
    return calls


async def test_copy_generation_valid_first_try(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.posts.copy_generation_service import generate_post_copy

    calls = _patch_copy_dependencies(monkeypatch, [json.dumps(_VALID_COPY)])
    copy = await generate_post_copy(TENANT_ID, "instagram", "monsoon offer", None)  # type: ignore[arg-type]
    assert copy.caption.startswith("Monsoon")
    assert len(calls) == 1
    assert calls[0]["temperature"] == 0.7


async def test_copy_generation_retries_once_with_correction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bad = dict(_VALID_COPY, hashtags=["salon", "monsoon"])  # missing '#'
    calls = _patch_copy_dependencies(monkeypatch, [json.dumps(bad), json.dumps(_VALID_COPY)])
    from app.modules.posts.copy_generation_service import generate_post_copy

    copy = await generate_post_copy(TENANT_ID, "instagram", "monsoon offer", None)  # type: ignore[arg-type]
    assert copy.hashtags == ["#salon", "#monsoon"]
    assert len(calls) == 2
    # The retry carries the validation error as a correction instruction
    assert "failed validation" in str(calls[1]["user_message"])


async def test_copy_generation_fails_after_two_invalid_outputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.modules.posts.copy_generation_service import generate_post_copy

    _patch_copy_dependencies(monkeypatch, ["not json", "still not json"])
    with pytest.raises(AIGenerationError):
        await generate_post_copy(TENANT_ID, "instagram", "monsoon offer", None)  # type: ignore[arg-type]


async def test_tiktok_caption_length_enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    too_long = dict(_VALID_COPY, caption="x" * 200)
    _patch_copy_dependencies(monkeypatch, [json.dumps(too_long), json.dumps(too_long)])
    from app.modules.posts.copy_generation_service import generate_post_copy

    with pytest.raises(AIGenerationError):
        await generate_post_copy(TENANT_ID, "tiktok", "offer", None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Intent classification parsing
# ---------------------------------------------------------------------------


async def test_intent_classification_parses_model_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.modules.ai import intent_classification_service as svc

    async def _fake_complete(**_kwargs: object) -> str:
        return json.dumps(
            {
                "intent": "enquiry",
                "service_interest": "haircut",
                "confidence": 0.92,
                "is_urgent": False,
                "requires_human": False,
            }
        )

    monkeypatch.setattr(svc.ai, "complete", _fake_complete)
    result = await svc.classify_intent("how much for a haircut?")
    assert result.intent == "enquiry"
    assert result.confidence == 0.92


async def test_intent_classification_invalid_output_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.modules.ai import intent_classification_service as svc

    async def _fake_complete(**_kwargs: object) -> str:
        return "definitely an enquiry I think"

    monkeypatch.setattr(svc.ai, "complete", _fake_complete)
    with pytest.raises(AIGenerationError):
        await svc.classify_intent("how much for a haircut?")
