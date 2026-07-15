"""Post generation chain DoD:
- the chain runs from topic input to a signed R2 URL
- the chain fails CLEANLY when the monthly image limit is reached
- progress stages are tracked in Redis for the frontend poller
"""

import json
import uuid
from contextlib import asynccontextmanager
from types import SimpleNamespace

import fakeredis
import pytest

from app.core.exceptions import PlanLimitError
from app.db.models import Plan
from app.modules.billing.usage_service import UsageDecision

TENANT_ID = uuid.uuid4()
POST_ID = uuid.uuid4()


class _FakeSession:
    """Just enough session surface for the chain's task bodies."""

    def __init__(self, tenant_plan: Plan = Plan.TRIAL) -> None:
        self.tenant = SimpleNamespace(plan=tenant_plan)
        self.committed = 0

    async def scalar(self, *_a: object, **_k: object) -> object:
        return self.tenant

    async def commit(self) -> None:
        self.committed += 1


@pytest.fixture()
def chain_env(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    """Wire every external surface of the chain to fakes."""
    import app.db.base as db_base
    from app.worker import post_worker

    sync_redis = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(post_worker, "get_sync_redis", lambda: sync_redis)

    post = SimpleNamespace(
        id=POST_ID,
        tenant_id=TENANT_ID,
        content=None,
        status="draft",
        meta={"topic": "monsoon offer", "platform": "instagram", "format": "square"},
        media_urls={},
    )
    session = _FakeSession()

    @asynccontextmanager
    async def _fake_worker_session():  # noqa: ANN202
        yield session

    @asynccontextmanager
    async def _fake_scope(*_a: object, **_k: object):  # noqa: ANN202
        yield session

    async def _fake_load_post(*_a: object, **_k: object) -> object:
        return post

    monkeypatch.setattr(post_worker, "worker_session", _fake_worker_session)
    monkeypatch.setattr(post_worker, "_load_post", _fake_load_post)
    monkeypatch.setattr(db_base, "with_tenant_scope", _fake_scope)

    # Copy generation returns a validated output
    from app.modules.posts import copy_generation_service

    async def _fake_copy(**_k: object) -> object:
        return SimpleNamespace(
            caption="Monsoon special!",
            hashtags=["#salon"],
            call_to_action="Book now",
            image_description="A serene salon",
            template_style="warm",
        )

    monkeypatch.setattr(copy_generation_service, "generate_post_copy", _fake_copy)

    # Usage allowed by default; individual tests flip this
    from app.modules.billing import usage_service

    state: dict[str, object] = {
        "decision": UsageDecision(allowed=True, current=1, limit=5),
        "post": post,
        "session": session,
        "redis": sync_redis,
    }

    async def _fake_usage(*_a: object, **_k: object) -> UsageDecision:
        return state["decision"]  # type: ignore[return-value]

    monkeypatch.setattr(usage_service, "check_and_increment_usage", _fake_usage)

    # Image client and R2
    from app.modules.images import client as image_module

    async def _fake_generate_image(**_k: object) -> tuple[str, str]:
        return "creatives/fake/key.png", "https://r2.example/signed"

    monkeypatch.setattr(image_module.image_client, "generate_image", _fake_generate_image)

    from app.core import r2_service

    async def _fake_signed(_key: str, **_k: object) -> str:
        return "https://r2.example/signed-final"

    monkeypatch.setattr(r2_service.r2_service, "generate_signed_url", _fake_signed)

    # Realtime emitter: capture instead of publish
    from app.modules.realtime import events

    emitted: list[tuple[str, str, dict]] = []
    monkeypatch.setattr(
        events.EventEmitter,
        "emit_sync",
        staticmethod(lambda tid, etype, data: emitted.append((str(tid), etype, data))),
    )
    state["emitted"] = emitted
    return state


def _progress(redis: fakeredis.FakeRedis) -> dict[str, object]:
    raw = redis.get(f"gen_progress:{POST_ID}")
    return json.loads(raw) if raw else {}


def test_chain_runs_topic_to_signed_url(chain_env: dict[str, object]) -> None:
    """DoD: topic input → copy → image → R2 key → signed URL, with progress."""
    from app.worker.post_worker import (
        generate_copy_task,
        generate_image_task,
        notify_completion_task,
        upload_to_r2_task,
    )

    payload = {"post_id": str(POST_ID), "tenant_id": str(TENANT_ID)}
    payload = generate_copy_task(payload)
    assert _progress(chain_env["redis"])["stage"] == "copy_done"  # type: ignore[index]

    payload = generate_image_task(payload)
    assert payload["image_r2_key"] == "creatives/fake/key.png"

    payload = upload_to_r2_task(payload)
    assert payload["signed_url"] == "https://r2.example/signed-final"

    payload = notify_completion_task(payload)
    progress = _progress(chain_env["redis"])  # type: ignore[arg-type]
    assert progress["stage"] == "complete"
    assert progress["signed_url"] == "https://r2.example/signed-final"

    post = chain_env["post"]
    assert post.content == "Monsoon special!"  # type: ignore[union-attr]
    assert post.media_urls["image_r2_key"] == "creatives/fake/key.png"  # type: ignore[union-attr]

    emitted = chain_env["emitted"]
    assert any(e[1] == "post_generated" for e in emitted)  # type: ignore[union-attr]


def test_chain_fails_cleanly_at_usage_limit(chain_env: dict[str, object]) -> None:
    """DoD: images_generated limit reached → PlanLimitError, progress=failed."""
    from app.worker.post_worker import generate_copy_task, generate_image_task

    chain_env["decision"] = UsageDecision(allowed=False, current=5, limit=5)

    payload = {"post_id": str(POST_ID), "tenant_id": str(TENANT_ID)}
    payload = generate_copy_task(payload)
    with pytest.raises(PlanLimitError) as exc_info:
        generate_image_task(payload)
    assert exc_info.value.details["limit"] == 5

    progress = _progress(chain_env["redis"])  # type: ignore[arg-type]
    assert progress["stage"] == "failed"
    assert progress["reason"] == "usage_limit"


def test_copy_failure_marks_progress_failed(
    chain_env: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core.exceptions import AIGenerationError
    from app.modules.posts import copy_generation_service
    from app.worker.post_worker import generate_copy_task

    async def _boom(**_k: object) -> None:
        raise AIGenerationError("model produced garbage twice")

    monkeypatch.setattr(copy_generation_service, "generate_post_copy", _boom)

    with pytest.raises(AIGenerationError):
        generate_copy_task({"post_id": str(POST_ID), "tenant_id": str(TENANT_ID)})
    progress = _progress(chain_env["redis"])  # type: ignore[arg-type]
    assert progress == {"stage": "failed", "failed_stage": "copy"}
