from __future__ import annotations

import logging
from collections.abc import Iterable

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict) -> None:
        disconnected: list[WebSocket] = []
        for websocket in list(self.active_connections):
            try:
                await websocket.send_json(message)
            except Exception:
                logger.exception("Failed to send realtime message")
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(websocket)

    def snapshot(self) -> Iterable[WebSocket]:
        return tuple(self.active_connections)


manager = ConnectionManager()
