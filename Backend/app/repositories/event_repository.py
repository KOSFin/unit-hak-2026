from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain_event import DomainEvent


class DomainEventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        event_type: str,
        entity_type: str,
        entity_id: str | None,
        payload: dict,
    ) -> DomainEvent:
        event = DomainEvent(
            type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
        )
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)
        return event

    def get_by_id(self, event_id: str) -> DomainEvent | None:
        return self.session.get(DomainEvent, event_id)

    def list_unprocessed(self) -> list[DomainEvent]:
        stmt = select(DomainEvent).where(DomainEvent.processed.is_(False))
        return list(self.session.execute(stmt).scalars().all())

    def mark_processed(self, event_id: str) -> DomainEvent | None:
        event = self.get_by_id(event_id)
        if not event:
            return None
        event.processed = True
        event.processed_at = datetime.now(UTC)
        event.error = None
        self.session.commit()
        self.session.refresh(event)
        return event

    def mark_failed(self, event_id: str, error: str) -> DomainEvent | None:
        event = self.get_by_id(event_id)
        if not event:
            return None
        event.processed = False
        event.processed_at = datetime.now(UTC)
        event.error = error
        self.session.commit()
        self.session.refresh(event)
        return event
