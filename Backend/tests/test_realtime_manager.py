import pytest
from fastapi import WebSocket
from unittest.mock import AsyncMock

from app.realtime.connection_manager import ConnectionManager


@pytest.mark.asyncio
async def test_connect_and_snapshot() -> None:
    manager = ConnectionManager()
    ws = AsyncMock(spec=WebSocket)
    
    snapshot = await manager.connect("board-1", ws, {
        "guest_id": "g1", "display_name": "Guest 1", "color": "#000"
    })
    
    assert snapshot["board_id"] == "board-1"
    assert len(snapshot["users"]) == 1
    assert snapshot["users"][0]["guest_id"] == "g1"
    assert snapshot["users"][0]["display_name"] == "Guest 1"


@pytest.mark.asyncio
async def test_editing_and_dragging() -> None:
    manager = ConnectionManager()
    ws = AsyncMock(spec=WebSocket)
    
    await manager.connect("board-1", ws, {"guest_id": "g1"})
    
    s1 = manager.start_editing("board-1", "g1", "t1")
    assert len(s1["editing"]) == 1
    assert s1["editing"][0]["active_task_id"] == "t1"
    
    s2 = manager.stop_editing("board-1", "g1")
    assert len(s2["editing"]) == 0
    
    s3 = manager.start_dragging("board-1", "g1", "t2")
    assert len(s3["dragging"]) == 1
    assert s3["dragging"][0]["active_task_id"] == "t2"
    
    s4 = manager.stop_dragging("board-1", "g1")
    assert len(s4["dragging"]) == 0

@pytest.mark.asyncio
async def test_disconnect() -> None:
    manager = ConnectionManager()
    ws = AsyncMock(spec=WebSocket)
    
    await manager.connect("board-1", ws, {"guest_id": "g1"})
    manager.start_editing("board-1", "g1", "t1")
    
    snapshot = manager.disconnect("board-1", ws)
    assert len(snapshot["users"]) == 0
    assert len(snapshot["editing"]) == 0
