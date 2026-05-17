from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.incoming_task import IncomingTask, IncomingTaskStatus
from app.models.task import TaskPriority
from app.queue.message_types import (
    INCOMING_TASK_PROCESSED,
    INCOMING_TASK_RECEIVED,
    INCOMING_TASK_REJECTED,
    INCOMING_TASK_VALIDATED,
)
from app.repositories.board_repository import BoardRepository
from app.repositories.column_repository import ColumnRepository
from app.repositories.incoming_task_repository import IncomingTaskRepository
from app.schemas.incoming_task import IncomingTaskCreate
from app.schemas.task import TaskCreate
from app.services.event_service import EventService
from app.services.notification_service import NotificationService
from app.services.task_service import TaskService


class IncomingTaskService:
    def __init__(self, session: Session):
        self.repo = IncomingTaskRepository(session)
        self.board_repo = BoardRepository(session)
        self.column_repo = ColumnRepository(session)
        self.task_service = TaskService(session)
        self.notification_service = NotificationService(session)
        self.event_service = EventService(session)

    def list_tasks(
        self,
        skip: int = 0,
        limit: int = 50,
        status: str | None = None,
        board_id: str | None = None,
    ) -> list[IncomingTask]:
        tasks = self.repo.list_all(board_id=board_id)
        if status:
            tasks = [task for task in tasks if task.status.value == status]
        return tasks[skip : skip + limit]

    def create_task(self, payload: IncomingTaskCreate) -> IncomingTask:
        duplicate = self.repo.get_by_external_id(payload.external_id)
        if duplicate:
            updated = self.repo.update_status(
                duplicate.id,
                IncomingTaskStatus.DUPLICATE,
                validation_error="Duplicate external_id",
                processed_at=datetime.now(UTC),
            )
            return updated or duplicate

        incoming = self.repo.create(
            external_id=payload.external_id,
            raw_payload=payload.raw_payload,
            status=IncomingTaskStatus.RECEIVED,
            board_id=payload.board_id,
        )
        if incoming.board_id:
            self.board_repo.update_last_activity(incoming.board_id)
        self.event_service.record_event(
            INCOMING_TASK_RECEIVED,
            "incoming_task",
            incoming.id,
            {"incoming_task": serialize_incoming_task(incoming)},
            board_id=incoming.board_id,
            source="API",
        )
        return incoming

    def process_incoming_task(self, incoming_id: str) -> IncomingTask | None:
        incoming = self.repo.get_by_id(incoming_id)
        if not incoming:
            return None
        if incoming.status in {IncomingTaskStatus.PROCESSED, IncomingTaskStatus.DUPLICATE}:
            return incoming

        raw_payload = incoming.raw_payload or {}
        title = raw_payload.get("title")
        tags = raw_payload.get("tags", [])
        if not title or not isinstance(title, str):
            updated = self.repo.update_status(
                incoming.id,
                IncomingTaskStatus.REJECTED,
                validation_error="Incoming payload must include a string title",
                processed_at=datetime.now(UTC),
            )
            if updated:
                self.event_service.record_event(
                    INCOMING_TASK_REJECTED,
                    "incoming_task",
                    updated.id,
                    {"incoming_task": serialize_incoming_task(updated)},
                    board_id=updated.board_id,
                    source="WORKER",
                )
            return updated

        if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
            updated = self.repo.update_status(
                incoming.id,
                IncomingTaskStatus.REJECTED,
                validation_error="Incoming payload tags must be a list of strings",
                processed_at=datetime.now(UTC),
            )
            if updated:
                self.event_service.record_event(
                    INCOMING_TASK_REJECTED,
                    "incoming_task",
                    updated.id,
                    {"incoming_task": serialize_incoming_task(updated)},
                    board_id=updated.board_id,
                    source="WORKER",
                )
            return updated

        validated = self.repo.update_status(incoming.id, IncomingTaskStatus.VALIDATED)
        if validated:
            self.event_service.record_event(
                INCOMING_TASK_VALIDATED,
                "incoming_task",
                validated.id,
                {"incoming_task": serialize_incoming_task(validated)},
                board_id=validated.board_id,
                source="WORKER",
            )

        board = self.board_repo.get_default()
        if not board and not incoming.board_id:
            raise ValueError("Default board not found")
        board_id = incoming.board_id or board.id
        todo_column = self.column_repo.get_by_title(board_id, "To Do")
        if not todo_column:
            raise ValueError("To Do column not found")

        enriched_tags = list(dict.fromkeys([*tags, "from-api"]))
        priority = TaskPriority.MEDIUM
        task = self.task_service.create_task(
            TaskCreate(
                board_id=board_id,
                column_id=todo_column.id,
                title=title,
                description=raw_payload.get("description"),
                status="To Do",
                priority=priority,
                tags=enriched_tags,
                deadline=raw_payload.get("deadline"),
            )
        )

        processed = self.repo.update_status(
            incoming.id,
            IncomingTaskStatus.PROCESSED,
            processed_at=datetime.now(UTC),
        )
        if processed:
            self.event_service.record_event(
                INCOMING_TASK_PROCESSED,
                "incoming_task",
                processed.id,
                {
                    "incoming_task": serialize_incoming_task(processed),
                    "task": {
                        "id": task.id,
                        "board_id": task.board_id,
                        "column_id": task.column_id,
                        "title": task.title,
                    },
                },
                board_id=task.board_id,
                source="WORKER",
            )

        self.notification_service.create_notification(
            title="Incoming task processed",
            message=f"Task '{task.title}' was created from the API queue.",
            type="incoming-task",
            task_id=task.id,
            board_id=task.board_id,
        )
        return processed


def serialize_incoming_task(task: IncomingTask) -> dict:
    return {
        "id": task.id,
        "external_id": task.external_id,
        "raw_payload": task.raw_payload,
        "status": task.status.value,
        "validation_error": task.validation_error,
        "created_at": task.created_at.isoformat(),
        "processed_at": task.processed_at.isoformat() if task.processed_at else None,
    }
