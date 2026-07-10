"""WebSocket server + the short-lived token that authenticates it.

Browsers cannot set an Authorization header on a WebSocket handshake, so the
flow is: the frontend calls GET /auth/ws-token (a NORMAL authenticated
endpoint) → receives a 5-minute single-use token → opens
/ws/{tenant_id}?token=... The token is consumed with GETDEL: replaying a
sniffed token is impossible.

Each accepted socket registers itself in ws_connections:{tenant_id} and
subscribes to the ws:{tenant_id} Redis pub/sub channel — that is how a
Celery worker on another machine reaches this exact browser tab.
"""

import asyncio
import contextlib
import json
import logging
import secrets
import uuid
from collections.abc import Awaitable
from typing import cast

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.redis import get_redis
from app.gateway.dependencies import CurrentUser
from app.modules.realtime.events import CONNECTION_REGISTRY_TTL_S, channel_for, registry_key

logger = logging.getLogger(__name__)

# ws-token is a versioned API route; the WebSocket itself lives at the app
# root (/ws/{tenant_id}) per the realtime spec.
router = APIRouter(tags=["realtime"])
ws_router = APIRouter(tags=["realtime"])

WS_TOKEN_TTL_S = 300


@router.get("/auth/ws-token", summary="Issue a one-time WebSocket token")
async def issue_ws_token(user: CurrentUser) -> dict[str, object]:
    token = secrets.token_urlsafe(32)
    await get_redis().set(
        f"wstok:{token}",
        json.dumps({"tenant_id": str(user.tenant_id), "user_id": str(user.user_id)}),
        ex=WS_TOKEN_TTL_S,
    )
    return {"token": token, "expires_in": WS_TOKEN_TTL_S}


async def _consume_ws_token(token: str) -> dict[str, str] | None:
    """Single-use: GETDEL means a token authenticates exactly one handshake."""
    raw = await get_redis().getdel(f"wstok:{token}")
    if not raw:
        return None
    parsed: dict[str, str] = json.loads(raw)
    return parsed


@ws_router.websocket("/ws/{tenant_id}")
async def websocket_endpoint(websocket: WebSocket, tenant_id: uuid.UUID) -> None:
    token = websocket.query_params.get("token", "")
    claims = await _consume_ws_token(token) if token else None
    if claims is None or claims.get("tenant_id") != str(tenant_id):
        await websocket.close(code=4401, reason="invalid or expired token")
        return

    await websocket.accept()
    redis = get_redis()
    connection_id = secrets.token_hex(8)
    registry = registry_key(tenant_id)
    # redis-py types these as Awaitable[int] | int (shared sync/async stubs);
    # on the async client they are always awaitable
    await cast("Awaitable[int]", redis.sadd(registry, connection_id))
    await cast("Awaitable[int]", redis.expire(registry, CONNECTION_REGISTRY_TTL_S))

    pubsub = redis.pubsub()
    await pubsub.subscribe(channel_for(tenant_id))
    logger.info(
        "websocket connected",
        extra={"tenant_id": str(tenant_id), "connection_id": connection_id},
    )

    async def _forward_events() -> None:
        async for message in pubsub.listen():
            if message.get("type") == "message":
                await websocket.send_text(str(message["data"]))

    forward_task = asyncio.create_task(_forward_events())
    try:
        while True:
            # The client only sends pings; receipt also detects disconnects
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        forward_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await forward_task
        await pubsub.unsubscribe(channel_for(tenant_id))
        # redis-py stubs gap: aclose is untyped on PubSub
        await pubsub.aclose()  # type: ignore[no-untyped-call]
        await cast("Awaitable[int]", redis.srem(registry, connection_id))
        logger.info(
            "websocket disconnected",
            extra={"tenant_id": str(tenant_id), "connection_id": connection_id},
        )
