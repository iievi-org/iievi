"""Celery application with the six named queues plus the dead letter queue.

Queue topology (concurrency and retry policy are tuned per queue at the worker
level; tasks land on queues via their `queue=` routing):

- ai_conversations    — lead-facing AI replies; latency-sensitive (concurrency 8)
- post_publishing     — social platform publish calls; idempotent, retried (4)
- creative_generation — image generation jobs; slow, low concurrency (3)
- lead_outreach       — follow-ups and outbound messages; NO auto-retry (4)
- ad_management       — boost/campaign operations (2)
- usage_tracking      — metering writes; high volume, low priority (4)
- dlq                 — dead letters; NO worker consumes this queue. Items are
                        parked here by the failure handler and drained only by
                        operations tooling. Its size is the early-warning
                        signal for systemic failures (see ops.check_dlq_size).

Non-negotiable settings (and why):
- json serialiser only — pickle deserialisation can execute arbitrary code
- acks_late — a task is acknowledged AFTER completion, so a worker crash
  requeues it instead of losing it
- prefetch 1 — one slow task can't hold N-1 others hostage in a local buffer
- reject_on_worker_lost — a SIGKILLed worker's task goes back to the queue
- max_tasks_per_child 1000 — worker processes restart periodically so slow
  memory leaks never accumulate into OOM kills
"""

import json
import logging
from typing import Any, cast

from celery import Celery, Task
from celery.signals import before_task_publish, task_failure, task_postrun, task_prerun
from kombu import Queue

from app.core.config import settings
from app.core.context import request_id_var, task_id_var, task_name_var, tenant_id_var
from app.core.ops import notify_ops
from app.core.redis import get_sync_redis

logger = logging.getLogger(__name__)

QUEUE_NAMES = (
    "ai_conversations",
    "post_publishing",
    "creative_generation",
    "lead_outreach",
    "ad_management",
    "usage_tracking",
)

DLQ_NAME = "dlq"
DLQ_ALERT_THRESHOLD = 10

# Worker concurrency per queue — consumed by the supervisor/compose command
# lines (one worker process group per queue in production).
QUEUE_CONCURRENCY: dict[str, int] = {
    "ai_conversations": 8,
    "post_publishing": 4,
    "creative_generation": 3,
    "lead_outreach": 4,
    "ad_management": 2,
    "usage_tracking": 4,
}

celery_app = Celery(
    "iievi",
    broker=str(settings.redis_url),
    backend=str(settings.redis_url),
    include=[
        "app.worker.tasks",
        "app.worker.maintenance",
        "app.worker.post_worker",
        "app.worker.publish_worker",
        "app.worker.message_worker",
        "app.worker.billing_worker",
        "app.worker.ai_worker",
        "app.worker.outreach_worker",
        "app.worker.notification_worker",
        "app.worker.reports_worker",
    ],
)


def _beat_schedule() -> dict[str, dict[str, object]]:
    from app.worker.beat_schedule import BEAT_SCHEDULE

    return BEAT_SCHEDULE


celery_app.conf.update(
    task_queues=tuple(Queue(name) for name in (*QUEUE_NAMES, DLQ_NAME)),
    task_default_queue="usage_tracking",
    # --- serialisation: json ONLY, never pickle ---
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # --- delivery guarantees ---
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_time_limit=600,
    task_soft_time_limit=540,
    result_expires=3600,
    timezone="UTC",
    broker_connection_retry_on_startup=True,
    # Capture stray stdout/stderr (and any leftover print) into the JSON logger
    # so nothing bypasses the structured log pipeline that feeds Axiom.
    worker_redirect_stdouts=True,
    worker_redirect_stdouts_level="WARNING",
    beat_schedule=_beat_schedule(),
)


# ---------------------------------------------------------------------------
# Correlation ID propagation: API request → task headers → worker contextvar.
# A request can be traced end-to-end (API, Celery, logs, Sentry) by its
# request_id.
# ---------------------------------------------------------------------------


@before_task_publish.connect
def _propagate_request_id(headers: dict[str, object] | None = None, **_kwargs: object) -> None:
    """Publisher side: stamp the current request's correlation id on the task."""
    request_id = request_id_var.get()
    if headers is not None and request_id:
        headers["iievi_request_id"] = request_id


@task_prerun.connect
def _restore_request_id(
    task: Task | None = None,
    task_id: str | None = None,
    args: tuple[object, ...] | None = None,
    kwargs: dict[str, object] | None = None,
    **_kwargs: object,
) -> None:
    """Worker side: restore correlation + task identifiers so every task log
    line carries request_id, tenant_id, task_name, and task_id (Prompt 7 Step 11)."""
    if task is not None:
        request_id = getattr(task.request, "iievi_request_id", None)
        if isinstance(request_id, str):
            request_id_var.set(request_id)
        task_name_var.set(task.name)
    if task_id:
        task_id_var.set(str(task_id))
    tenant = _extract_tenant_id(args, kwargs)
    if tenant:
        tenant_id_var.set(tenant)


@task_postrun.connect
def _clear_request_id(**_kwargs: object) -> None:
    request_id_var.set(None)
    tenant_id_var.set(None)
    task_name_var.set(None)
    task_id_var.set(None)


# ---------------------------------------------------------------------------
# Failure handling: every task that exhausts its retries is recorded in the
# failed_tasks table, logged for Axiom, and parked on the DLQ. Sentry's
# Celery integration (initialised in app.core.sentry) captures the exception
# itself — no double-reporting here.
# ---------------------------------------------------------------------------


def _extract_tenant_id(args: tuple[object, ...] | None, kwargs: dict[str, object] | None) -> str:
    """Best-effort tenant extraction — our tasks pass tenant_id either as a
    `tenant_id` kwarg, a first positional UUID string, or a key inside a first
    positional payload dict (the conversation/outreach/notification tasks)."""
    if kwargs and isinstance(kwargs.get("tenant_id"), str):
        return str(kwargs["tenant_id"])
    if args:
        first = args[0]
        if isinstance(first, str) and len(first) == 36:
            return first
        if isinstance(first, dict) and isinstance(first.get("tenant_id"), str):
            return str(first["tenant_id"])
    return ""


@task_failure.connect
def _record_task_failure(
    sender: Task | None = None,
    task_id: str | None = None,
    exception: BaseException | None = None,
    args: tuple[object, ...] | None = None,
    kwargs: dict[str, object] | None = None,
    **_signal_kwargs: object,
) -> None:
    """Terminal-failure hook (does NOT fire on intermediate retries)."""
    task_name = sender.name if sender is not None else "unknown"
    queue = getattr(getattr(sender, "request", None), "delivery_info", None) or {}
    queue_name = str(queue.get("routing_key", "")) or None
    retries = int(getattr(getattr(sender, "request", None), "retries", 0) or 0)
    tenant_id = _extract_tenant_id(args, kwargs)
    error = f"{type(exception).__name__}: {exception}" if exception else "unknown"

    # Structured log → Axiom (the log pipeline ships JSON records)
    logger.error(
        "task failed terminally",
        extra={
            "task_name": task_name,
            "task_id": task_id,
            "tenant_id": tenant_id,
            "queue": queue_name,
            "retries": retries,
            "error": error[:2000],
        },
    )

    record = {
        "task_id": task_id or "",
        "task_name": task_name,
        "queue": queue_name,
        "tenant_id": tenant_id,
        "args": {"args": [repr(a)[:200] for a in (args or ())], "kwargs": list(kwargs or {})},
        "error": error[:4000],
        "retries": retries,
    }

    try:
        redis = get_sync_redis()
        redis.lpush(DLQ_NAME, json.dumps(record))
        # sync client — the Awaitable half of redis-py's union never applies
        dlq_size = int(cast("int", redis.llen(DLQ_NAME)))
        if dlq_size > DLQ_ALERT_THRESHOLD:
            notify_ops(
                f"DLQ above threshold: {dlq_size} items "
                f"(latest: {task_name}) — investigate systemic failure"
            )
    except Exception:  # noqa: BLE001 — never let the failure handler kill the worker
        logger.exception("failed to park task on DLQ")

    try:
        _persist_failed_task(record)
    except Exception:  # noqa: BLE001
        logger.exception("failed to write failed_tasks record")


def _persist_failed_task(record: dict[str, Any]) -> None:
    """Write the investigation record. Runs in its own loop — signal handlers
    are synchronous and the prefork worker has no running event loop."""
    import asyncio

    from sqlalchemy import text as sql_text
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.pool import NullPool

    async def _run() -> None:
        engine = create_async_engine(settings.pooled_database_url, poolclass=NullPool)
        try:
            async with AsyncSession(engine) as session:
                await session.execute(
                    sql_text(
                        "INSERT INTO failed_tasks "
                        "(task_id, task_name, queue, tenant_id, args, error, retries, is_dlq) "
                        "VALUES (:task_id, :task_name, :queue, "
                        "cast(nullif(:tenant_id, '') AS uuid), "
                        "cast(:args AS jsonb), :error, :retries, true)"
                    ),
                    {
                        "task_id": record["task_id"],
                        "task_name": record["task_name"],
                        "queue": record["queue"],
                        "tenant_id": record["tenant_id"],
                        "args": json.dumps(record["args"]),
                        "error": record["error"],
                        "retries": record["retries"],
                    },
                )
                await session.commit()
        finally:
            await engine.dispose()

    asyncio.run(_run())
