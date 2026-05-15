from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.task import Task
from app.queue.message_types import TASK_CREATED, TASK_DELETED, TASK_MOVED, TASK_UPDATED
from app.repositories.column_repository import ColumnRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate, TaskMove, TaskUpdate
from app.services.event_service import EventService


class VersionConflictError(Exception):
    pass


class TaskService:
    def __init__(self, session: Session) -> None:
        self.task_repo = TaskRepository(session)
        self.column_repo = ColumnRepository(session)
        self.event_service = EventService(session)

    def list_tasks(self, board_id: str | None = None) -> list[Task]:
        if board_id:
            return self.task_repo.list_by_board(board_id)
        return self.task_repo.list_all()

    def get_task(self, task_id: str) -> Task | None:
        return self.task_repo.get_by_id(task_id)

    def create_task(self, payload: TaskCreate) -> Task:
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
        )
        self.event_service.record_event(
            TASK_CREATED,
            "task",
            task.id,
            {"task": serialize_task(task)},
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
            self.event_service.record_event(
                TASK_UPDATED,
                "task",
                task_id,
                {"task": serialize_task(updated)},
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

        status = payload.status or column.title
        position = payload.position if payload.position is not None else task.position

        updated = self.task_repo.update(
            task_id,
            column_id=payload.column_id,
            status=status,
            position=position,
            version=task.version + 1,
        )
        if updated:
            self.event_service.record_event(
                TASK_MOVED,
                "task",
                task_id,
                {"task": serialize_task(updated)},
            )
        return updated

    def delete_task(self, task_id: str) -> bool:
        task = self.task_repo.get_by_id(task_id)
        if not task:
            return False
        deleted = self.task_repo.delete(task_id)
        if deleted:
            self.event_service.record_event(
                TASK_DELETED,
                "task",
                task_id,
                {"task": serialize_task(task)},
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
    }
