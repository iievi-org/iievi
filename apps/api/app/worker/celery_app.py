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

from celery import Celery
from kombu import Queue

from app.core.config import settings

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
