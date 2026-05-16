from sqlalchemy.orm import Session

from app.models.column import Column
from app.queue.message_types import COLUMN_CREATED, COLUMN_DELETED, COLUMN_UPDATED
from app.repositories.board_repository import BoardRepository
from app.repositories.column_repository import ColumnRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.column import ColumnCreate, ColumnUpdate
from app.services.event_service import EventService


class ColumnHasTasksError(Exception):
    pass


class ColumnService:
    def __init__(self, session: Session) -> None:
        self.board_repo = BoardRepository(session)
        self.column_repo = ColumnRepository(session)
        self.task_repo = TaskRepository(session)
        self.event_service = EventService(session)

    def create_column(self, payload: ColumnCreate) -> Column:
        if not self.board_repo.get_by_id(payload.board_id):
            raise ValueError("Board not found")
        position = payload.position
        if position is None:
            position = self.column_repo.get_max_position(payload.board_id) + 1
        column = self.column_repo.create(
            board_id=payload.board_id,
            title=payload.title,
            position=position,
            is_default=payload.is_default,
        )
        self.board_repo.update_last_activity(column.board_id)
        self.event_service.record_event(
            COLUMN_CREATED,
            "column",
            column.id,
            {"column": serialize_column(column)},
            board_id=column.board_id,
            source="API",
        )
        return column

    def update_column(self, column_id: str, payload: ColumnUpdate) -> Column | None:
        changes = payload.model_dump(exclude_unset=True)
        if not changes:
            return self.column_repo.get_by_id(column_id)
        column = self.column_repo.update(column_id, **changes)
        if column:
            self.board_repo.update_last_activity(column.board_id)
            self.event_service.record_event(
                COLUMN_UPDATED,
                "column",
                column_id,
                {"column": serialize_column(column)},
                board_id=column.board_id,
                source="API",
            )
        return column

    def delete_column(self, column_id: str) -> bool:
        if self.task_repo.count_by_column(column_id) > 0:
            raise ColumnHasTasksError("Column has tasks")
        column = self.column_repo.get_by_id(column_id)
        if not column:
            return False
        deleted = self.column_repo.delete(column_id)
        if deleted:
            self.board_repo.update_last_activity(column.board_id)
            self.event_service.record_event(
                COLUMN_DELETED,
                "column",
                column_id,
                {"column": serialize_column(column)},
                board_id=column.board_id,
                source="API",
            )
        return deleted


def serialize_column(column: Column) -> dict:
    return {
        "id": column.id,
        "board_id": column.board_id,
        "title": column.title,
        "position": column.position,
        "is_default": column.is_default,
        "created_at": column.created_at.isoformat() if column.created_at else None,
        "updated_at": column.updated_at.isoformat() if column.updated_at else None,
    }
