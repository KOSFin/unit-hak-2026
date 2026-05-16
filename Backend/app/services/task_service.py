from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.task import Task
from app.queue.message_types import TASK_CREATED, TASK_DELETED, TASK_MOVED, TASK_UPDATED
from app.repositories.board_repository import BoardRepository
from app.repositories.column_repository import ColumnRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate, TaskMove, TaskUpdate
from app.services.event_service import EventService


class VersionConflictError(Exception):
    pass


class TaskService:
    def __init__(self, session: Session) -> None:
        self.board_repo = BoardRepository(session)
        self.task_repo = TaskRepository(session)
        self.column_repo = ColumnRepository(session)
        self.event_service = EventService(session)

    def list_tasks(self, board_id: str | None = None) -> list[Task]:
        if board_id:
            return self.task_repo.list_by_board(board_id)
        return self.task_repo.list_all()

    def get_task(self, task_id: str) -> Task | None:
        return self.task_repo.get_by_id(task_id)

    def touch_board(self, board_id: str) -> None:
        self.board_repo.update_last_activity(board_id)

    def create_task(self, payload: TaskCreate) -> Task:
        if not self.board_repo.get_by_id(payload.board_id):
            raise ValueError("Board not found")
        column = self.column_repo.get_by_id(payload.column_id)
        if not column or column.board_id != payload.board_id:
            raise ValueError("Column not found")

        status = payload.status or column.title
        position = payload.position
        if position is None:
            position = self.task_repo.get_max_position(payload.board_id, payload.column_id) + 1

        task = self.task_repo.create(
            board_id=payload.board_id,
            column_id=payload.column_id,
            title=payload.title,
            description=payload.description,
            status=status,
            priority=payload.priority,
            tags=list(payload.tags),
            deadline=payload.deadline,
            position=position,
            correlation_id=payload.correlation_id,
            guest_id=payload.guest_id,
        )
        self.touch_board(task.board_id)
        self.event_service.record_event(
            TASK_CREATED,
            "task",
            task.id,
            {"task": serialize_task(task)},
            board_id=task.board_id,
            correlation_id=payload.correlation_id,
            source="API",
        )
        return task

    def update_task(self, task_id: str, payload: TaskUpdate) -> Task | None:
        task = self.task_repo.get_by_id(task_id)
        if not task:
            return None
        if payload.version != task.version:
            raise VersionConflictError("Task version conflict")

        changes = payload.model_dump(exclude_unset=True, exclude={"version"})
        if not changes:
            return task
        changes["version"] = task.version + 1
        updated = self.task_repo.update(task_id, **changes)
        if updated:
            self.touch_board(updated.board_id)
            self.event_service.record_event(
                TASK_UPDATED,
                "task",
                task_id,
                {"task": serialize_task(updated)},
                board_id=updated.board_id,
                correlation_id=payload.correlation_id,
                source="API",
            )
        return updated

    def move_task(self, task_id: str, payload: TaskMove) -> Task | None:
        task = self.task_repo.get_by_id(task_id)
        if not task:
            return None
        if payload.version != task.version:
            raise VersionConflictError("Task version conflict")

        column = self.column_repo.get_by_id(payload.column_id)
        if not column:
            raise ValueError("Column not found")

        source_column_id = task.column_id
        target_column_id = payload.column_id
        status = payload.status or column.title

        # Desired 1-based target position; default to end of target column
        desired_position = payload.position
        if desired_position is None:
            desired_position = self.task_repo.count_by_column(target_column_id) + 1

        # Clamp to valid range
        target_count = self.task_repo.count_by_column(target_column_id)
        if source_column_id == target_column_id:
            # Exclude the task itself from the count
            max_pos = target_count
        else:
            max_pos = target_count + 1
        desired_position = max(1, min(desired_position, max_pos))

        # Update column, status, and temporarily put at a high position to avoid
        # conflicts while we renumber — actual position will be set by reorder_positions
        updated = self.task_repo.update(
            task_id,
            column_id=target_column_id,
            status=status,
            position=desired_position,
            version=task.version + 1,
            correlation_id=payload.correlation_id,
            guest_id=payload.guest_id,
        )
        if not updated:
            return None

        # Renumber source column (if different from target, task already left it)
        if source_column_id != target_column_id:
            self.task_repo.reorder_positions(source_column_id)

        # Renumber target column to make positions contiguous and honour desired_position.
        # We need to insert at desired_position: shift others down first, then compact.
        target_tasks = self.task_repo.list_by_column(target_column_id)
        # Build new order: all tasks except moving one, insert moving task at desired_position
        others = [t for t in target_tasks if t.id != task_id]
        moving = next((t for t in target_tasks if t.id == task_id), None)
        if moving:
            insert_idx = min(desired_position - 1, len(others))
            ordered = others[:insert_idx] + [moving] + others[insert_idx:]
            for idx, t in enumerate(ordered, start=1):
                if t.position != idx:
                    t.position = idx
            self.task_repo.session.commit()

        # Refresh and return the moved task
        updated = self.task_repo.get_by_id(task_id)
        if updated:
            self.touch_board(updated.board_id)
            self.event_service.record_event(
                TASK_MOVED,
                "task",
                task_id,
                {"task": serialize_task(updated)},
                board_id=updated.board_id,
                correlation_id=payload.correlation_id,
                source="API",
            )
        return updated

    def delete_task(self, task_id: str) -> bool:
        task = self.task_repo.get_by_id(task_id)
        if not task:
            return False
        deleted = self.task_repo.delete(task_id)
        if deleted:
            self.touch_board(task.board_id)
            self.event_service.record_event(
                TASK_DELETED,
                "task",
                task_id,
                {"task": serialize_task(task)},
                board_id=task.board_id,
                source="API",
            )
        return deleted


def serialize_task(task: Task) -> dict:
    def to_iso(value: datetime | None):
        return value.isoformat() if value else None

    return {
        "id": task.id,
        "board_id": task.board_id,
        "column_id": task.column_id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority.value if hasattr(task.priority, "value") else str(task.priority),
        "tags": list(task.tags),
        "deadline": to_iso(task.deadline),
        "position": task.position,
        "version": task.version,
        "created_at": to_iso(task.created_at),
        "updated_at": to_iso(task.updated_at),
        "correlation_id": getattr(task, "correlation_id", None),
        "guest_id": getattr(task, "guest_id", None),
    }
