"""Shared async Redis client.

One connection pool per process, created lazily. Used by the JWT blacklist,
the feature-flag cache, and (later phases) rate limiting and tenant-context
caching.
"""

from functools import lru_cache

import redis as redis_sync
import redis.asyncio as aioredis

from app.core.config import settings


@lru_cache(maxsize=1)
def get_redis() -> aioredis.Redis:
    """Return the process-wide Redis client (lazy, pooled)."""
    client: aioredis.Redis = aioredis.from_url(  # type: ignore[no-untyped-call]
        str(settings.redis_url),
        decode_responses=True,
    )
    return client


@lru_cache(maxsize=1)
def get_sync_redis() -> redis_sync.Redis:
    """Sync client for contexts with no event loop (Celery signal handlers,
    profile hooks). Keep usage to sub-millisecond operations."""
    client: redis_sync.Redis = redis_sync.from_url(  # type: ignore[no-untyped-call]
        str(settings.redis_url),
        decode_responses=True,
    )
    return client
