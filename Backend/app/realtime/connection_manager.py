from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


@dataclass
class PresenceUser:
    guest_id: str
    display_name: str
    color: str | None = None
    avatar_url: str | None = None
    connected_at: datetime | None = None
    active_connections: int = 0


@dataclass
class BoardPresence:
    connections: dict[WebSocket, PresenceUser] = field(default_factory=dict)
    guests: dict[str, PresenceUser] = field(default_factory=dict)
    editing: dict[str, PresenceUser] = field(default_factory=dict)
    dragging: dict[str, PresenceUser] = field(default_factory=dict)


class ConnectionManager:
    def __init__(self) -> None:
        self.boards: dict[str, BoardPresence] = defaultdict(BoardPresence)

    async def connect(self, board_id: str, websocket: WebSocket, user: dict[str, Any]) -> dict[str, Any]:
        await websocket.accept()
        presence = self._user_from_payload(user)
        board = self.boards[board_id]
        existing = board.guests.get(presence.guest_id)
        if existing:
            existing.active_connections += 1
            existing.display_name = presence.display_name
            existing.color = presence.color
            existing.avatar_url = presence.avatar_url
            board.connections[websocket] = existing
            return self.snapshot(board_id)

        presence.active_connections = 1
        presence.connected_at = datetime.utcnow()
        board.connections[websocket] = presence
        board.guests[presence.guest_id] = presence
        return self.snapshot(board_id)

    def disconnect(self, board_id: str, websocket: WebSocket) -> dict[str, Any]:
        board = self.boards.get(board_id)
        if not board:
            return self.snapshot(board_id)
        presence = board.connections.pop(websocket, None)
        if not presence:
            return self.snapshot(board_id)
        presence.active_connections = max(0, presence.active_connections - 1)
        if presence.active_connections <= 0:
            board.guests.pop(presence.guest_id, None)
            board.editing.pop(presence.guest_id, None)
            board.dragging.pop(presence.guest_id, None)
        return self.snapshot(board_id)

    def update_presence(self, board_id: str, user: dict[str, Any]) -> dict[str, Any]:
        board = self.boards[board_id]
        guest_id = str(user.get("guest_id") or "")
        if not guest_id:
            return self.snapshot(board_id)
        existing = board.guests.get(guest_id)
        if not existing:
            existing = self._user_from_payload(user)
            board.guests[guest_id] = existing
        existing.display_name = str(user.get("display_name") or existing.display_name)
        existing.color = user.get("color") or existing.color
        existing.avatar_url = user.get("avatar_url") or existing.avatar_url
        return self.snapshot(board_id)

    def start_editing(self, board_id: str, guest_id: str) -> dict[str, Any]:
        board = self.boards[board_id]
        if guest_id in board.guests:
            board.editing[guest_id] = board.guests[guest_id]
        return self.snapshot(board_id)

    def stop_editing(self, board_id: str, guest_id: str) -> dict[str, Any]:
        board = self.boards.get(board_id)
        if board:
            board.editing.pop(guest_id, None)
        return self.snapshot(board_id)

    def start_dragging(self, board_id: str, guest_id: str) -> dict[str, Any]:
        board = self.boards[board_id]
        if guest_id in board.guests:
            board.dragging[guest_id] = board.guests[guest_id]
        return self.snapshot(board_id)

    def stop_dragging(self, board_id: str, guest_id: str) -> dict[str, Any]:
        board = self.boards.get(board_id)
        if board:
            board.dragging.pop(guest_id, None)
        return self.snapshot(board_id)

    def snapshot(self, board_id: str) -> dict[str, Any]:
        board = self.boards.get(board_id)
        if not board:
            return {"board_id": board_id, "users": [], "editing": [], "dragging": []}
        users = list(board.guests.values())
        return {
            "board_id": board_id,
            "users": [self._serialize_user(user) for user in users],
            "editing": [self._serialize_user(user) for user in board.editing.values()],
            "dragging": [self._serialize_user(user) for user in board.dragging.values()],
        }

    def _user_from_payload(self, user: dict[str, Any]) -> PresenceUser:
        return PresenceUser(
            guest_id=str(user.get("guest_id") or ""),
            display_name=str(user.get("display_name") or "Guest"),
            color=user.get("color"),
            avatar_url=user.get("avatar_url"),
        )

    def _serialize_user(self, user: PresenceUser) -> dict[str, Any]:
        return {
            "guest_id": user.guest_id,
            "display_name": user.display_name,
            "color": user.color,
            "avatar_url": user.avatar_url,
            "connected_at": user.connected_at.isoformat() if user.connected_at else None,
            "active_connections": user.active_connections,
        }

    async def broadcast(self, board_id: str, message: dict[str, Any]) -> None:
        board = self.boards.get(board_id)
        if not board:
            return
        disconnected: list[WebSocket] = []
        for websocket in list(board.connections):
            try:
                await websocket.send_json(message)
            except Exception:
                logger.exception("Failed to send realtime message")
                disconnected.append(websocket)
        for websocket in disconnected:
            self.disconnect(board_id, websocket)


manager = ConnectionManager()
