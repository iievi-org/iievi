"""Typed event emitter — how Celery tasks reach connected WebSocket clients.

Events flow: task → Redis pub/sub channel ws:{tenant_id} → every API process
whose WebSocket handler is subscribed for that tenant → browser. The
connection registry (ws_connections:{tenant_id}) tracks which tenants have
open sockets so emitters can skip the publish entirely for offline tenants.
"""

import json
import logging
import uuid
from typing import Literal

from app.core.redis import get_redis, get_sync_redis

logger = logging.getLogger(__name__)

EventType = Literal[
    "new_lead",
    "lead_status_changed",
    "ai_typing_started",
    "ai_response_sent",
    "post_generated",
    "post_published",
    "post_failed",
]

CONNECTION_REGISTRY_TTL_S = 24 * 3600


def channel_for(tenant_id: uuid.UUID | str) -> str:
    return f"ws:{tenant_id}"


def registry_key(tenant_id: uuid.UUID | str) -> str:
    return f"ws_connections:{tenant_id}"


class EventEmitter:
    """Emit typed events to a tenant's live WebSocket connections.

    `emit` (async) is for API-process callers; `emit_sync` is for Celery
    tasks, whose bodies run under asyncio.run with no shared loop — a sync
    publish avoids loop-affinity bugs for a sub-millisecond operation.
    """

    @staticmethod
    def _envelope(event_type: EventType, data: dict[str, object]) -> str:
        return json.dumps({"type": event_type, "data": data})

    @staticmethod
    async def emit(
        tenant_id: uuid.UUID | str, event_type: EventType, data: dict[str, object]
    ) -> None:
        try:
            await get_redis().publish(
                channel_for(tenant_id), EventEmitter._envelope(event_type, data)
            )
        except Exception:  # noqa: BLE001 — realtime is best-effort, never break the caller
            logger.warning("event emit failed", extra={"event": event_type})

    @staticmethod
    def emit_sync(
        tenant_id: uuid.UUID | str, event_type: EventType, data: dict[str, object]
    ) -> None:
        try:
            get_sync_redis().publish(
                channel_for(tenant_id), EventEmitter._envelope(event_type, data)
            )
        except Exception:  # noqa: BLE001
            logger.warning("event emit failed", extra={"event": event_type})
