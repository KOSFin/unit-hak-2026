import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient

from app.main import app
from app.ws.consumer import WSConsumerThread
from app.ws.manager import ConnectionManager


@pytest.mark.anyio
async def test_connection_manager():
    manager = ConnectionManager()
    ws1 = AsyncMock()
    ws2 = AsyncMock()

    await manager.connect(ws1, "board1")
    await manager.connect(ws2, "board1")

    assert len(manager.active_connections["board1"]) == 2

    await manager.broadcast_to_board("board1", "hello")
    ws1.send_text.assert_called_with("hello")
    ws2.send_text.assert_called_with("hello")

    # Broadcast to non-existent board
    await manager.broadcast_to_board("board2", "hello")

    # Broadcast with exception
    ws1.send_text.side_effect = Exception("error")
    await manager.broadcast_to_board("board1", "hello")

    manager.disconnect(ws1, "board1")
    assert len(manager.active_connections["board1"]) == 1

    # Disconnect a ws that is NOT in the list (board exists, ws absent) — covers 19->22 branch
    unregistered_ws = AsyncMock()
    manager.disconnect(unregistered_ws, "board1")
    assert len(manager.active_connections["board1"]) == 1

    manager.disconnect(ws2, "board1")
    assert "board1" not in manager.active_connections

    # Disconnect from non-existent board
    manager.disconnect(ws1, "board1")


def test_ws_endpoint():
    client = TestClient(app)
    
    # Test no token
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws/board1"):
            pass
    assert exc.value.code == 1008

    # Test invalid token
    with pytest.raises(WebSocketDisconnect) as exc:
        with client.websocket_connect("/ws/board1?token=invalid"):
            pass
    assert exc.value.code == 1008

    # Test valid token and disconnect
    with client.websocket_connect("/ws/board1?token=valid-token") as websocket:
        # Just connecting and then closing is a disconnect
        pass


@pytest.mark.anyio
async def test_ws_consumer(monkeypatch):
    class MockChannel:
        def queue_declare(self, *args, **kwargs):
            class Method:
                queue = "test_queue"
            class Result:
                method = Method()
            return Result()
        def queue_bind(self, *args, **kwargs): pass
        def basic_consume(self, *args, **kwargs): pass

    class MockConnection:
        is_closed = False
        def channel(self): return MockChannel()
        def process_data_events(self, *args, **kwargs): pass
        def close(self): pass

    monkeypatch.setattr("app.ws.consumer.get_rabbitmq_connection", lambda: MockConnection())
    
    loop = asyncio.get_running_loop()
    consumer = WSConsumerThread(loop)
    
    # Test _on_message with valid payload
    event = {"payload": {"task": {"board_id": "board1"}}}
    consumer._on_message(None, None, None, json.dumps(event).encode())
    
    # Test _on_message with invalid JSON
    consumer._on_message(None, None, None, b"{invalid")
    
    # Test _on_message without task/board_id to cover false branch
    event_no_task = {"payload": {"other": "data"}}
    consumer._on_message(None, None, None, json.dumps(event_no_task).encode())
    
    # Test run and stop
    import threading
    def stop_later():
        consumer.stop()
    
    threading.Timer(0.1, stop_later).start()
    consumer.run()


def test_ws_consumer_no_connection(monkeypatch):
    monkeypatch.setattr("app.ws.consumer.get_rabbitmq_connection", lambda: None)
    loop = asyncio.new_event_loop()
    consumer = WSConsumerThread(loop)
    consumer.run()


def test_ws_consumer_exception(monkeypatch):
    monkeypatch.setattr("app.ws.consumer.get_rabbitmq_connection", lambda: 1 / 0)
    loop = asyncio.new_event_loop()
    consumer = WSConsumerThread(loop)
    consumer.run()


def test_ws_consumer_stop_exception(monkeypatch):
    class MockConnection:
        is_closed = False
        def close(self): raise Exception("test error")
    
    loop = asyncio.new_event_loop()
    consumer = WSConsumerThread(loop)
    consumer.connection = MockConnection()
    consumer.stop()
