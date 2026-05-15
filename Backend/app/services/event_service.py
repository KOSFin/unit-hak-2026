from sqlalchemy.orm import Session

from app.repositories.event_repository import DomainEventRepository


class EventService:
    def __init__(self, session: Session) -> None:
        self.repo = DomainEventRepository(session)

    def record_event(
        self,
        event_type: str,
        entity_type: str,
        entity_id: str | None,
        payload: dict,
    ):
        return self.repo.create(event_type, entity_type, entity_id, payload)
