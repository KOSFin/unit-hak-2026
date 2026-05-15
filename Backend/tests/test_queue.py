from datetime import datetime
import pytest
from pika.exceptions import AMQPError
from app.models.domain_event import DomainEvent
from app.queue.publisher import MockPublisher, RabbitMQPublisher, EventPublisher
from app.services.event_service import EventService, get_publisher

def test_mock_publisher():
    pub = MockPublisher()
    event = DomainEvent(id="test-id", type="t", entity_type="t", payload={"key": "value"}, created_at=datetime.utcnow(), processed=False)
    pub.publish(event)
    assert len(pub.published_events) == 1

def test_event_service_publish(db_session):
    pub = MockPublisher()
    service = EventService(db_session, publisher=pub)
    event = service.record_event("test_event", "test_entity", "entity-123", {"data": 1})
    assert len(pub.published_events) == 1

def test_rabbitmq_publisher_no_connection(monkeypatch):
    monkeypatch.setattr("app.queue.rabbitmq.get_settings", lambda: type("Settings", (), {"rabbitmq_url": None, "rabbitmq_host": None})())
    pub = RabbitMQPublisher()
    assert pub.connection is None
    pub.publish(DomainEvent(id="test-id", type="t", entity_type="t", payload={}, created_at=datetime.utcnow()))

def test_rabbitmq_publisher_with_connection_and_error(monkeypatch):
    class MockChannel:
        is_closed = False
        def queue_declare(self, *args, **kwargs): pass
        def queue_bind(self, *args, **kwargs): pass
        def basic_publish(self, *args, **kwargs): raise AMQPError("test error")
    class MockConnection:
        is_closed = False
        def channel(self): return MockChannel()
        def close(self): pass
    monkeypatch.setattr("app.queue.publisher.get_rabbitmq_connection", lambda: MockConnection())
    pub = RabbitMQPublisher()
    pub.publish(DomainEvent(id="test-id", type="t", entity_type="t", payload={}, created_at=datetime.utcnow()))
    assert pub.connection is None

def test_rabbitmq_publisher_successful_publish(monkeypatch):
    class MockChannel:
        is_closed = False
        published = False
        def queue_declare(self, *args, **kwargs): pass
        def queue_bind(self, *args, **kwargs): pass
        def basic_publish(self, *args, **kwargs): self.published = True
    class MockConnection:
        is_closed = False
        def __init__(self): self.ch = MockChannel()
        def channel(self): return self.ch
        def close(self): pass
    conn = MockConnection()
    monkeypatch.setattr("app.queue.publisher.get_rabbitmq_connection", lambda: conn)
    pub = RabbitMQPublisher()
    pub.publish(DomainEvent(id="test-id", type="t", entity_type="t", payload={}, created_at=datetime.utcnow()))
    assert conn.ch.published is True

def test_get_rabbitmq_connection_with_url(monkeypatch):
    monkeypatch.setattr("app.queue.rabbitmq.get_settings", lambda: type("Settings", (), {"rabbitmq_url": "amqp://guest:guest@localhost:5672/"})())
    monkeypatch.setattr("app.queue.rabbitmq.pika.BlockingConnection", lambda p: p)
    from app.queue.rabbitmq import get_rabbitmq_connection
    assert get_rabbitmq_connection() is not None

def test_get_rabbitmq_connection_with_host(monkeypatch):
    monkeypatch.setattr("app.queue.rabbitmq.get_settings", lambda: type("Settings", (), {"rabbitmq_url": None, "rabbitmq_host": "localhost", "rabbitmq_port": 5672})())
    monkeypatch.setattr("app.queue.rabbitmq.pika.BlockingConnection", lambda p: p)
    from app.queue.rabbitmq import get_rabbitmq_connection
    assert get_rabbitmq_connection() is not None

def test_event_publisher_abstract():
    class DummyPublisher(EventPublisher):
        def publish(self, event): super().publish(event)
    DummyPublisher().publish(None)

def test_rabbitmq_publisher_connection_error(monkeypatch):
    monkeypatch.setattr("app.queue.publisher.get_rabbitmq_connection", lambda: 1 / 0)
    pub = RabbitMQPublisher()
    assert pub.connection is None

def test_rabbitmq_publisher_close_error(monkeypatch):
    class MockChannel:
        is_closed = False
        published = False
        def queue_declare(self, *args, **kwargs): pass
        def queue_bind(self, *args, **kwargs): pass
        def basic_publish(self, *args, **kwargs): raise AMQPError("test error")
    class MockConnection:
        is_closed = False
        def channel(self): return MockChannel()
        def close(self): raise Exception("Close failed")
    monkeypatch.setattr("app.queue.publisher.get_rabbitmq_connection", lambda: MockConnection())
    pub = RabbitMQPublisher()
    pub.publish(DomainEvent(id="test-id", type="t", entity_type="t", payload={}, created_at=datetime.utcnow()))
    assert pub.connection is None

def test_rabbitmq_publisher_connection_closed_error(monkeypatch):
    class MockChannel:
        is_closed = False
        def queue_declare(self, *args, **kwargs): pass
        def queue_bind(self, *args, **kwargs): pass
        def basic_publish(self, *args, **kwargs): raise AMQPError("test error")
    class MockConnection:
        is_closed = True
        def channel(self): return MockChannel()
        def close(self): pass
    monkeypatch.setattr("app.queue.publisher.get_rabbitmq_connection", lambda: MockConnection())
    pub = RabbitMQPublisher()
    pub.publish(DomainEvent(id="test-id", type="t", entity_type="t", payload={}, created_at=datetime.utcnow()))
    assert pub.connection is None

def test_get_publisher_impl(monkeypatch):
    monkeypatch.setattr("app.services.event_service.get_settings", lambda: type("Settings", (), {"app_env": "test"})())
    import app.services.event_service
    app.services.event_service._publisher = None
    assert isinstance(app.services.event_service.get_publisher(), MockPublisher)

    monkeypatch.setattr("app.services.event_service.get_settings", lambda: type("Settings", (), {"app_env": "prod"})())
    app.services.event_service._publisher = None
    assert isinstance(app.services.event_service.get_publisher(), RabbitMQPublisher)
