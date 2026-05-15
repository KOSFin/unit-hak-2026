from sqlalchemy.orm import Session

from app.models.column import Column
from app.repositories.board_repository import BoardRepository
from app.repositories.column_repository import ColumnRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.column import ColumnCreate, ColumnUpdate


class ColumnHasTasksError(Exception):
    pass


class ColumnService:
    def __init__(self, session: Session) -> None:
        self.board_repo = BoardRepository(session)
        self.column_repo = ColumnRepository(session)
        self.task_repo = TaskRepository(session)

    def create_column(self, payload: ColumnCreate) -> Column:
        if not self.board_repo.get_by_id(payload.board_id):
            raise ValueError("Board not found")
        position = payload.position
        if position is None:
            position = self.column_repo.get_max_position(payload.board_id) + 1
        return self.column_repo.create(
            board_id=payload.board_id,
            title=payload.title,
            position=position,
            is_default=payload.is_default,
        )

    def update_column(self, column_id: str, payload: ColumnUpdate) -> Column | None:
        changes = payload.model_dump(exclude_unset=True)
        if not changes:
            return self.column_repo.get_by_id(column_id)
        return self.column_repo.update(column_id, **changes)

    def delete_column(self, column_id: str) -> bool:
        if self.task_repo.count_by_column(column_id) > 0:
            raise ColumnHasTasksError("Column has tasks")
        return self.column_repo.delete(column_id)
