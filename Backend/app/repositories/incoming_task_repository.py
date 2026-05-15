from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.incoming_task import IncomingTask, IncomingTaskStatus


class IncomingTaskRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        external_id: str,
        raw_payload: dict,
        status: IncomingTaskStatus,
    ) -> IncomingTask:
        incoming = IncomingTask(
            external_id=external_id,
            raw_payload=raw_payload,
            status=status,
        )
        self.session.add(incoming)
        self.session.commit()
        self.session.refresh(incoming)
        return incoming

    def get_by_id(self, incoming_id: str) -> IncomingTask | None:
        return self.session.get(IncomingTask, incoming_id)

    def get_by_external_id(self, external_id: str) -> IncomingTask | None:
        stmt = select(IncomingTask).where(IncomingTask.external_id == external_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_all(self) -> list[IncomingTask]:
        stmt = select(IncomingTask).order_by(IncomingTask.created_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def update_status(
        self,
        incoming_id: str,
        status: IncomingTaskStatus,
        validation_error: str | None = None,
        processed_at: datetime | None = None,
    ) -> IncomingTask | None:
        incoming = self.get_by_id(incoming_id)
        if not incoming:
            return None
        incoming.status = status
        incoming.validation_error = validation_error
        incoming.processed_at = processed_at
        self.session.commit()
        self.session.refresh(incoming)
        return incoming
