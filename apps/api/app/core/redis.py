"""Shared Redis clients.

The async client is cached PER EVENT LOOP, not per process: an asyncio Redis
connection is bound to the loop that created it. In the API process there is
exactly one long-lived loop, so this behaves like a process-wide singleton.
In Celery workers every task body runs under its own asyncio.run() loop — a
process-cached client would resurface in the next task bound to a closed
loop and fail with "Event loop is closed". The WeakKeyDictionary drops each
client when its loop is garbage-collected after asyncio.run returns.
"""

import asyncio
import weakref
from functools import lru_cache

import redis as redis_sync
import redis.asyncio as aioredis

from app.core.config import settings

_clients: "weakref.WeakKeyDictionary[asyncio.AbstractEventLoop, aioredis.Redis]" = (
    weakref.WeakKeyDictionary()
)


def get_redis() -> aioredis.Redis:
    """Return the Redis client for the CURRENT event loop (lazy, pooled)."""
    loop = asyncio.get_running_loop()
    client = _clients.get(loop)
    if client is None:
        client = aioredis.from_url(  # type: ignore[no-untyped-call]
            str(settings.redis_url),
            decode_responses=True,
        )
        _clients[loop] = client
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
