from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.queue.consumer import RabbitMQConsumer
from app.queue.message_types import (
    INCOMING_TASK_RECEIVED,
    TASK_CREATED,
    TASK_MOVED,
    TASK_UPDATED,
)
from app.repositories.event_repository import DomainEventRepository
from app.schemas.event import DomainEventSchema
from app.services.automation_service import AutomationService
from app.services.incoming_task_service import IncomingTaskService

logger = logging.getLogger(__name__)


class WorkerEventProcessor:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.event_repo = DomainEventRepository(session)
        self.automation_service = AutomationService(session)
        self.incoming_task_service = IncomingTaskService(session)

    def process_payload(self, body: bytes | str | dict[str, Any]) -> bool:
        event = self._parse_event(body)
        if not event:
            return False

        stored_event = self.event_repo.get_by_id(event.id)
        if not stored_event:
            logger.warning("Received unknown event %s", event.id)
            return False
        if stored_event.processed:
            return True

        try:
            self._dispatch(event)
        except Exception as exc:
            logger.exception("Worker failed to process event %s", event.id)
            self.event_repo.mark_failed(event.id, str(exc))
            return False

        self.event_repo.mark_processed(event.id)
        return True

    def _dispatch(self, event: DomainEventSchema) -> None:
        if event.type in {TASK_CREATED, TASK_UPDATED, TASK_MOVED} and event.entity_id:
            self.automation_service.apply_task_automations(event.entity_id, event.type)
            return
        if event.type == INCOMING_TASK_RECEIVED and event.entity_id:
            self.incoming_task_service.process_incoming_task(event.entity_id)
            return

    def _parse_event(self, body: bytes | str | dict[str, Any]) -> DomainEventSchema | None:
        try:
            if isinstance(body, bytes):
                payload = json.loads(body.decode("utf-8"))
            elif isinstance(body, str):
                payload = json.loads(body)
            else:
                payload = body
            return DomainEventSchema.model_validate(payload)
        except Exception:
            logger.exception("Worker received malformed event payload")
            return None


def process_event(channel: Any, method: Any, _properties: Any, body: bytes) -> None:
    session = SessionLocal()
    try:
        processor = WorkerEventProcessor(session)
        handled = processor.process_payload(body)
        if handled:
            channel.basic_ack(delivery_tag=method.delivery_tag)
        else:
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    finally:
        session.close()


def main() -> int:
    consumer = RabbitMQConsumer("task_events")
    if not consumer.connect():
        return 1

    try:
        consumer.consume(process_event)
    except KeyboardInterrupt:
        consumer.close()
        return 0
    except Exception:
        logger.exception("Worker crashed")
        consumer.close()
        return 1

    consumer.close()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
