"""Celery application with the six named queues.

Queue topology (concurrency and retry policy are tuned per queue at the worker
level; tasks land on queues via their `queue=` routing):

- ai_conversations    — lead-facing AI replies; latency-sensitive
- post_publishing     — social platform publish calls; idempotent, retried
- creative_generation — NanoBanana Pro image jobs; slow, low concurrency
- lead_outreach       — follow-ups and outbound messages
- ad_management       — boost/campaign operations
- usage_tracking      — metering writes; high volume, low priority
"""

from celery import Celery, Task
from celery.signals import before_task_publish, task_postrun, task_prerun
from kombu import Queue

from app.core.config import settings
from app.core.context import request_id_var

QUEUE_NAMES = (
    "ai_conversations",
    "post_publishing",
    "creative_generation",
    "lead_outreach",
    "ad_management",
    "usage_tracking",
)

celery_app = Celery(
    "iievi",
    broker=str(settings.redis_url),
    backend=str(settings.redis_url),
)

celery_app.conf.update(
    task_queues=tuple(Queue(name) for name in QUEUE_NAMES),
    task_default_queue="usage_tracking",
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_time_limit=600,
    task_soft_time_limit=540,
    result_expires=3600,
    timezone="UTC",
    broker_connection_retry_on_startup=True,
    beat_schedule={},  # populated in later phases (usage rollups, token refresh)
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
def _restore_request_id(task: Task | None = None, **_kwargs: object) -> None:
    """Worker side: restore the correlation id so all task logs carry it."""
    if task is None:
        return
    request_id = getattr(task.request, "iievi_request_id", None)
    if isinstance(request_id, str):
        request_id_var.set(request_id)


@task_postrun.connect
def _clear_request_id(**_kwargs: object) -> None:
    request_id_var.set(None)
