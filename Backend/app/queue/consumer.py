from __future__ import annotations

import logging
from collections.abc import Callable

from app.core.config import get_settings
from app.queue.rabbitmq import EVENT_EXCHANGE, get_rabbitmq_connection

logger = logging.getLogger(__name__)


class RabbitMQConsumer:
    def __init__(self, queue_name: str) -> None:
        self.queue_name = queue_name
        self.connection = None
        self.channel = None

    def connect(self) -> bool:
        settings = get_settings()
        self.connection = get_rabbitmq_connection(
            max_attempts=settings.rabbitmq_connect_retries,
            retry_delay_seconds=settings.rabbitmq_retry_delay_seconds,
        )
        if not self.connection:
            logger.warning("RabbitMQ consumer connection unavailable")
            return False
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=EVENT_EXCHANGE, exchange_type="fanout", durable=True)
        self.channel.queue_declare(queue=self.queue_name, durable=True)
        self.channel.queue_bind(exchange=EVENT_EXCHANGE, queue=self.queue_name)
        return True

    def consume(self, callback: Callable) -> bool:
        if not self.channel and not self.connect():
            return False
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue=self.queue_name, on_message_callback=callback)
        self.channel.start_consuming()
        return True

    def close(self) -> None:
        if self.connection and not self.connection.is_closed:
            self.connection.close()
