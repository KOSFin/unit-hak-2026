from datetime import UTC, datetime

from app.models.domain_event import DomainEvent
from app.queue.consumer import RabbitMQConsumer
from app.queue.message_types import NOTIFICATION_CREATED, TASK_CREATED
from app.queue.publisher import EventPublisher, MockPublisher, RabbitMQPublisher


def test_mock_and_rabbitmq_publisher(monkeypatch):
    event = DomainEvent(
        id="event-1",
        type=TASK_CREATED,
        entity_type="task",
        entity_id="task-1",
        payload={"task": {"id": "task-1"}},
        created_at=datetime.now(UTC),
    )

    mock = MockPublisher()
    mock.publish(event)
    assert mock.published_events == [event]

    monkeypatch.setattr("app.queue.publisher.get_rabbitmq_connection", lambda: None)
    publisher = RabbitMQPublisher()
    publisher.publish(event)
    assert publisher.channel is None

    publisher = RabbitMQPublisher()
    publisher.connection = type("ClosedConnection", (), {"is_closed": True})()
    publisher.channel = type(
        "Channel",
        (),
        {
            "is_closed": False,
            "basic_publish": lambda self, **_kwargs: (_ for _ in ()).throw(RuntimeError("publish")),
        },
    )()
    publisher.publish(event)
    assert publisher.connection is None

    published = False

    class ChannelStub:
        is_closed = False

        def exchange_declare(self, **_kwargs):
            return None

        def queue_declare(self, **_kwargs):
            return None

        def queue_bind(self, **_kwargs):
            return None

        def basic_publish(self, **_kwargs):
            nonlocal published
            published = True

    class ConnectionStub:
        is_closed = False

        def __init__(self):
            self.channel_instance = ChannelStub()

        def channel(self):
            return self.channel_instance

        def close(self):
            self.is_closed = True

    monkeypatch.setattr("app.queue.publisher.get_rabbitmq_connection", ConnectionStub)
    publisher = RabbitMQPublisher()
    publisher.publish(event)
    assert published is True

    class BrokenChannel(ChannelStub):
        def basic_publish(self, **_kwargs):
            raise RuntimeError("publish failed")

    class BrokenConnection(ConnectionStub):
        def __init__(self):
            self.channel_instance = BrokenChannel()

    monkeypatch.setattr("app.queue.publisher.get_rabbitmq_connection", BrokenConnection)
    publisher = RabbitMQPublisher()
    publisher.publish(event)
    assert publisher.channel is None

    assert NOTIFICATION_CREATED == "NOTIFICATION_CREATED"


def test_rabbitmq_connection_and_consumer(monkeypatch):
    from app.queue.rabbitmq import get_rabbitmq_connection

    monkeypatch.setattr(
        "app.queue.rabbitmq.get_settings",
        lambda: type(
            "S", (), {"rabbitmq_url": None, "rabbitmq_host": None, "rabbitmq_port": 5672}
        )(),
    )
    assert get_rabbitmq_connection() is None

    monkeypatch.setattr(
        "app.queue.rabbitmq.get_settings",
        lambda: type(
            "S",
            (),
            {
                "rabbitmq_url": "amqp://guest:guest@localhost:5672/",
                "rabbitmq_host": None,
                "rabbitmq_port": 5672,
            },
        )(),
    )
    monkeypatch.setattr("app.queue.rabbitmq.pika.BlockingConnection", lambda params: params)
    assert get_rabbitmq_connection() is not None

    monkeypatch.setattr(
        "app.queue.rabbitmq.get_settings",
        lambda: type(
            "S",
            (),
            {
                "rabbitmq_url": None,
                "rabbitmq_host": "rabbitmq",
                "rabbitmq_port": 5672,
            },
        )(),
    )
    assert get_rabbitmq_connection() is not None

    def raise_connection(_params):
        raise RuntimeError("down")

    monkeypatch.setattr("app.queue.rabbitmq.pika.BlockingConnection", raise_connection)
    assert get_rabbitmq_connection() is None

    class ChannelStub:
        def __init__(self):
            self.started = False

        def exchange_declare(self, **_kwargs):
            return None

        def queue_declare(self, **_kwargs):
            return None

        def queue_bind(self, **_kwargs):
            return None

        def basic_qos(self, **_kwargs):
            return None

        def basic_consume(self, **_kwargs):
            return None

        def start_consuming(self):
            self.started = True

    class ConnectionStub:
        is_closed = False

        def __init__(self):
            self.channel_instance = ChannelStub()

        def channel(self):
            return self.channel_instance

        def close(self):
            self.is_closed = True

    monkeypatch.setattr("app.queue.consumer.get_rabbitmq_connection", lambda: None)
    consumer = RabbitMQConsumer("task_events")
    assert consumer.consume(lambda *_args: None) is False
    consumer.close()

    connection = ConnectionStub()
    monkeypatch.setattr("app.queue.consumer.get_rabbitmq_connection", lambda: connection)
    consumer = RabbitMQConsumer("task_events")
    assert consumer.connect() is True
    assert consumer.consume(lambda *_args: None) is True
    consumer.close()
    assert connection.is_closed is True


def test_publisher_connect_and_abstract_publish(monkeypatch):
    class BasePublisher(MockPublisher):
        def publish(self, event):
            super().publish(event)
            return EventPublisher.publish(self, event)

    class BrokenConnection:
        def channel(self):
            raise RuntimeError("no channel")

    monkeypatch.setattr("app.queue.publisher.get_rabbitmq_connection", lambda: BrokenConnection())
    publisher = RabbitMQPublisher()
    assert publisher.connection is None

    event = DomainEvent(
        id="event-2",
        type=TASK_CREATED,
        entity_type="task",
        entity_id="task-2",
        payload={},
        created_at=datetime.now(UTC),
    )
    assert BasePublisher().publish(event) is None

    class ExplodingConnection:
        is_closed = False

        def close(self):
            raise RuntimeError("close failed")

    publisher = RabbitMQPublisher()
    publisher.connection = ExplodingConnection()
    publisher.channel = type(
        "Channel",
        (),
        {
            "is_closed": False,
            "basic_publish": lambda self, **_kwargs: (_ for _ in ()).throw(RuntimeError("publish")),
        },
    )()
    publisher.publish(event)
    assert publisher.channel is None
