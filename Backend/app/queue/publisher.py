import logging
from abc import ABC, abstractmethod

from app.models.domain_event import DomainEvent
from app.queue.rabbitmq import EVENT_EXCHANGE, get_rabbitmq_connection
from app.schemas.event import DomainEventSchema

logger = logging.getLogger(__name__)


class EventPublisher(ABC):
    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        pass


class RabbitMQPublisher(EventPublisher):
    def __init__(self, queue_name: str = "task_events"):
        self.queue_name = queue_name
        self.connection = None
        self.channel = None
        self._connect()

    def _connect(self):
        try:
            self.connection = get_rabbitmq_connection()
            if self.connection:
                self.channel = self.connection.channel()
                self.channel.exchange_declare(
                    exchange=EVENT_EXCHANGE,
                    exchange_type="fanout",
                    durable=True,
                )
                self.channel.queue_declare(queue=self.queue_name, durable=True)
                self.channel.queue_bind(exchange=EVENT_EXCHANGE, queue=self.queue_name)
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            self.connection = None
            self.channel = None

    def publish(self, event: DomainEvent) -> None:
        if not self.channel or self.channel.is_closed:
            self._connect()

        if not self.channel:
            logger.warning("RabbitMQ channel not available, skipping publish")
            return

        try:
            schema = DomainEventSchema(
                id=event.id,
                type=event.type,
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                board_id=event.board_id,
                correlation_id=event.correlation_id,
                source=event.source,
                payload=event.payload,
                processed=event.processed if event.processed is not None else False,
                error=event.error,
                created_at=event.created_at,
                processed_at=event.processed_at,
            )
            message = schema.model_dump_json()

            import pika

            self.channel.basic_publish(
                exchange=EVENT_EXCHANGE,
                routing_key="",
                body=message,
                properties=pika.BasicProperties(delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE),
            )
            logger.info(f"Published event {event.id} of type {event.type}")
        except Exception as e:
            logger.error(f"Failed to publish event {event.id}: {e}")
            # Try to disconnect so it reconnects on next publish
            if self.connection and not self.connection.is_closed:
                try:
                    self.connection.close()
                except Exception:
                    pass
            self.connection = None
            self.channel = None


class MockPublisher(EventPublisher):
    def __init__(self):
        self.published_events = []

    def publish(self, event: DomainEvent) -> None:
        self.published_events.append(event)
        logger.info(f"[Mock] Published event {event.id} of type {event.type}")
