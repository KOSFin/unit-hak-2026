from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.queue.publisher import MockPublisher, RabbitMQPublisher
from app.repositories.event_repository import DomainEventRepository

_publisher = None


def get_publisher():
    global _publisher
    if _publisher is None:
        settings = get_settings()
        if settings.app_env == "test":
            _publisher = MockPublisher()
        else:
            _publisher = RabbitMQPublisher()
    return _publisher


class EventService:
    def __init__(self, session: Session, publisher=None) -> None:
        self.repo = DomainEventRepository(session)
        self.publisher = publisher or get_publisher()

    def record_event(
        self,
        event_type: str,
        entity_type: str,
        entity_id: str | None,
        payload: dict,
    ):
        event = self.repo.create(event_type, entity_type, entity_id, payload)
        self.publisher.publish(event)
        return event
