import asyncio
from datetime import UTC, datetime

from fastapi import WebSocketDisconnect

from app.realtime import manager as exported_manager
from app.realtime.broadcaster import RealtimeRelay, build_realtime_message
from app.realtime.connection_manager import ConnectionManager
from app.realtime.routes import websocket_endpoint
from app.schemas.event import DomainEventSchema


class WebSocketStub:
    def __init__(self, fail=False):
        self.accepted = False
        self.sent = []
        self.fail = fail

    async def accept(self):
        self.accepted = True

    async def send_json(self, payload):
        if self.fail:
            raise RuntimeError("boom")
        self.sent.append(payload)


def test_connection_manager_broadcasts_and_disconnects():
    manager = ConnectionManager()
    good = WebSocketStub()
    bad = WebSocketStub(fail=True)

    asyncio.run(manager.connect(good))
    asyncio.run(manager.connect(bad))
    asyncio.run(manager.broadcast({"type": "task.created"}))

    assert good.accepted is True
    assert good.sent == [{"type": "task.created"}]
    assert bad not in manager.active_connections

    manager.disconnect(good)
    assert list(manager.snapshot()) == []


def test_build_realtime_message_and_relay_helpers(monkeypatch):
    event = DomainEventSchema(
        id="event-1",
        type="TASK_CREATED",
        entity_type="task",
        payload={"task": {"id": "task-1"}},
        created_at=datetime.now(UTC),
    )
    message = build_realtime_message(event)
    assert message.type == "task.created"

    unknown = DomainEventSchema(
        id="event-2",
        type="BOARD_UPDATED",
        entity_type="board",
        payload={"board": {"id": "board-1"}},
        created_at=datetime.now(UTC),
    )
    assert build_realtime_message(unknown).type == "board.updated"

    loop = asyncio.new_event_loop()
    relay = RealtimeRelay(loop)

    async def fake_broadcast(_payload):
        return None

    monkeypatch.setattr("app.realtime.broadcaster.manager.broadcast", fake_broadcast)
    monkeypatch.setattr(
        "app.realtime.broadcaster.asyncio.run_coroutine_threadsafe",
        lambda coro, _loop: coro.close(),
    )
    relay._on_message(
        None,
        None,
        None,
        b'{"id":"1","type":"TASK_CREATED","entity_type":"task","payload":{},"created_at":"2026-05-16T00:00:00+00:00"}',
    )
    relay._on_message(None, None, None, b"not-json")
    relay.stop()

    closed = False

    class ConnectionStub:
        is_closed = False

        def close(self):
            nonlocal closed
            closed = True

    relay.connection = ConnectionStub()
    relay.close()
    assert closed is True

    class BrokenConnection:
        is_closed = False

        def close(self):
            raise RuntimeError("boom")

    relay.connection = BrokenConnection()
    relay.close()
    loop.close()
    assert exported_manager is not None


def test_realtime_relay_run_and_route(monkeypatch):
    processed = []

    class ChannelStub:
        def exchange_declare(self, **_kwargs):
            return None

        def queue_declare(self, **_kwargs):
            return type("Result", (), {"method": type("Method", (), {"queue": "temp"})()})()

        def queue_bind(self, **_kwargs):
            return None

        def basic_consume(self, **_kwargs):
            return None

    class ConnectionStub:
        is_closed = True

        def channel(self):
            return ChannelStub()

        def process_data_events(self, time_limit):
            processed.append(time_limit)
            relay.stop()

        def close(self):
            return None

    loop = asyncio.new_event_loop()
    relay = RealtimeRelay(loop)
    monkeypatch.setattr("app.realtime.broadcaster.get_rabbitmq_connection", lambda: None)
    relay.run()
    monkeypatch.setattr(
        "app.realtime.broadcaster.get_rabbitmq_connection",
        lambda: ConnectionStub(),
    )
    relay.run()
    assert processed == [1.0]
    loop.close()

    calls = []

    class RouteSocket:
        async def accept(self):
            calls.append("accept")

        async def receive_text(self):
            if len(calls) == 1:
                calls.append("runtime")
                raise RuntimeError("close")
            raise WebSocketDisconnect

    asyncio.run(websocket_endpoint(RouteSocket()))
    assert "accept" in calls

    class DisconnectSocket:
        async def accept(self):
            return None

        async def receive_text(self):
            raise WebSocketDisconnect

    asyncio.run(websocket_endpoint(DisconnectSocket()))
