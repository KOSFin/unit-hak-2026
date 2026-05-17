from __future__ import annotations

import asyncio
import json
import logging
import threading
from datetime import datetime
from typing import Any

from app.core.config import get_settings
from app.queue.rabbitmq import EVENT_EXCHANGE, get_rabbitmq_connection
from app.realtime.connection_manager import manager
from app.schemas.event import DomainEventSchema, RealtimeEventSchema

logger = logging.getLogger(__name__)

EVENT_TYPE_MAP = {
    "TASK_CREATED": "task.created",
    "TASK_UPDATED": "task.updated",
    "TASK_MOVED": "task.moved",
    "TASK_DELETED": "task.deleted",
    "COLUMN_CREATED": "column.created",
    "COLUMN_UPDATED": "column.updated",
    "COLUMN_DELETED": "column.deleted",
    "AUTOMATION_RULE_CREATED": "automation-rule.created",
    "AUTOMATION_RULE_UPDATED": "automation-rule.updated",
    "AUTOMATION_RULE_DELETED": "automation-rule.deleted",
    "NOTIFICATION_CREATED": "notification.created",
    "AUTOMATION_TRIGGERED": "automation.triggered",
    "INCOMING_TASK_PROCESSED": "incoming-task.processed",
}


def build_realtime_message(event: DomainEventSchema) -> RealtimeEventSchema:
    realtime_type = EVENT_TYPE_MAP.get(event.type, event.type.lower().replace("_", "."))
    payload = event.payload
    return RealtimeEventSchema(
        type=realtime_type,
        payload=payload,
        createdAt=_isoformat(event.created_at),
        boardId=event.board_id,
        correlationId=event.correlation_id,
        source=event.source,
    )


def _isoformat(value: datetime) -> str:
    return value.isoformat()


class RealtimeRelay(threading.Thread):
    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        super().__init__(daemon=True)
        self.loop = loop
        self.connection = None
        self.channel = None
        self._stop_event = threading.Event()

    def run(self) -> None:
        settings = get_settings()
        self.connection = get_rabbitmq_connection(
            max_attempts=settings.rabbitmq_connect_retries,
            retry_delay_seconds=settings.rabbitmq_retry_delay_seconds,
        )
        if not self.connection:
            logger.warning("Realtime relay disabled because RabbitMQ remained unavailable")
            return

        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=EVENT_EXCHANGE, exchange_type="fanout", durable=True)
        result = self.channel.queue_declare(queue="", exclusive=True)
        queue_name = result.method.queue
        self.channel.queue_bind(exchange=EVENT_EXCHANGE, queue=queue_name)
        self.channel.basic_consume(
            queue=queue_name, on_message_callback=self._on_message, auto_ack=True
        )

        while not self._stop_event.is_set():
            self.connection.process_data_events(time_limit=1.0)

        self.close()

    def _on_message(self, _channel: Any, _method: Any, _properties: Any, body: bytes) -> None:
        try:
            payload = json.loads(body)
            event = DomainEventSchema.model_validate(payload)
            message = build_realtime_message(event).model_dump()
        except Exception:
            logger.exception("Failed to decode realtime event")
            return

        board_id = event.board_id
        if board_id:
            asyncio.run_coroutine_threadsafe(manager.broadcast(board_id, message), self.loop)

    def stop(self) -> None:
        self._stop_event.set()

    def close(self) -> None:
        if self.connection and not self.connection.is_closed:
            try:
                self.connection.close()
            except Exception:
                logger.exception("Failed to close realtime relay connection")
