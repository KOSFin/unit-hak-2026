import json
from datetime import datetime

import httpx
import pytest

from app.models.automation_rule import AutomationRule
from app.schemas.event import DomainEventSchema
from app.worker.main import apply_action, handle_task_moved, process_event, main


def test_apply_action_set_status(monkeypatch):
    called = False

    def mock_patch(url, json, timeout):
        nonlocal called
        called = True
        class MockResponse:
            def raise_for_status(self): pass
        return MockResponse()

    monkeypatch.setattr(httpx, "patch", mock_patch)
    
    apply_action("task-1", 2, {"type": "set_status", "status": "Done"})
    assert called

def test_apply_action_invalid():
    # Should exit early
    apply_action("task-1", 2, {"type": "unknown"})
    apply_action("task-1", 2, {})

def test_apply_action_exception(monkeypatch):
    def mock_patch(*args, **kwargs):
        raise Exception("API error")
    monkeypatch.setattr(httpx, "patch", mock_patch)
    # Should handle exception gracefully
    apply_action("task-1", 2, {"type": "set_status", "status": "Done"})


def test_handle_task_moved(monkeypatch):
    class MockRule1:
        enabled = True
        trigger_type = "TASK_MOVED"
        condition = {"column_id": "col-2"}
        action = {"type": "set_status", "status": "Done"}

    class MockRule2:
        enabled = False
        trigger_type = "TASK_MOVED"
        condition = {"column_id": "col-2"}

    class MockRule3:
        enabled = True
        trigger_type = "UNKNOWN"
        condition = {"column_id": "col-2"}

    class MockRule4:
        enabled = True
        trigger_type = "TASK_MOVED"
        condition = {"column_id": "wrong"}

    class MockRepo:
        def __init__(self, db): pass
        def list_all(self): return [MockRule1(), MockRule2(), MockRule3(), MockRule4()]

    monkeypatch.setattr("app.worker.main.SessionLocal", lambda: type("Session", (), {"close": lambda self: None})())
    monkeypatch.setattr("app.worker.main.AutomationRuleRepository", MockRepo)

    applied_task = None

    def mock_apply_action(task_id, version, action):
        nonlocal applied_task
        applied_task = task_id

    monkeypatch.setattr("app.worker.main.apply_action", mock_apply_action)

    # Valid event
    event = DomainEventSchema(id="evt-1", type="TASK_MOVED", entity_type="task", payload={"task": {"id": "task-1", "column_id": "col-2", "version": 1}}, created_at=datetime.utcnow())
    handle_task_moved(event)
    assert applied_task == "task-1"

    # Missing payload
    event.payload = None
    handle_task_moved(event)

    # Missing task
    event.payload = {}
    handle_task_moved(event)

    # Missing column_id
    event.payload = {"task": {"id": "task-1"}}
    handle_task_moved(event)


def test_process_event(monkeypatch):
    class MockChannel:
        def basic_ack(self, delivery_tag): self.acked = delivery_tag
        def basic_nack(self, delivery_tag, requeue): self.nacked = delivery_tag

    class MockMethod:
        delivery_tag = 1

    ch = MockChannel()
    method = MockMethod()
    
    event = DomainEventSchema(id="evt-1", type="TEST", entity_type="test", payload={}, created_at=datetime.utcnow())
    
    # Valid processing
    process_event(ch, method, None, event.model_dump_json())
    assert getattr(ch, "acked", None) == 1

    # Valid processing with TASK_MOVED
    event.type = "TASK_MOVED"
    event.payload = {"task": {"id": "1", "column_id": "2"}}
    ch.acked = None
    monkeypatch.setattr("app.worker.main.handle_task_moved", lambda e: None)
    process_event(ch, method, None, event.model_dump_json())
    assert getattr(ch, "acked", None) == 1

    # Invalid JSON
    process_event(ch, MockMethod(), None, "{invalid")
    assert getattr(ch, "nacked", None) == 1

    # Exception during processing
    def mock_loads(*args):
        raise Exception("Fatal")
    monkeypatch.setattr("app.worker.main.json.loads", mock_loads)
    ch.nacked = None
    process_event(ch, MockMethod(), None, "{}")
    assert getattr(ch, "nacked", None) == 1


def test_main_no_connection(monkeypatch):
    monkeypatch.setattr("app.worker.main.get_rabbitmq_connection", lambda: None)
    with pytest.raises(SystemExit):
        main()

def test_main_success_and_interrupt(monkeypatch):
    class MockChannel:
        def queue_declare(self, *args, **kwargs): pass
        def queue_bind(self, *args, **kwargs): pass
        def basic_qos(self, *args, **kwargs): pass
        def basic_consume(self, *args, **kwargs): pass
        def start_consuming(self): raise KeyboardInterrupt()
        def stop_consuming(self): self.stopped = True

    class MockConnection:
        def channel(self):
            self.ch = MockChannel()
            return self.ch
        def close(self): self.closed = True

    conn = MockConnection()
    monkeypatch.setattr("app.worker.main.get_rabbitmq_connection", lambda: conn)
    
    main()
    assert conn.ch.stopped is True
    assert conn.closed is True

def test_main_exception(monkeypatch):
    class MockChannel:
        def queue_declare(self, *args, **kwargs): pass
        def queue_bind(self, *args, **kwargs): pass
        def basic_qos(self, *args, **kwargs): pass
        def basic_consume(self, *args, **kwargs): pass
        def start_consuming(self): raise Exception("Crash")

    class MockConnection:
        def channel(self): return MockChannel()
        def close(self): self.closed = True

    conn = MockConnection()
    monkeypatch.setattr("app.worker.main.get_rabbitmq_connection", lambda: conn)
    
    main()
    assert conn.closed is True
