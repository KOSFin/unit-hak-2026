from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.task import Task, TaskPriority
from app.queue.message_types import AUTOMATION_TRIGGERED, TASK_MOVED, TASK_UPDATED
from app.repositories.column_repository import ColumnRepository
from app.repositories.task_repository import TaskRepository
from app.services.event_service import EventService
from app.services.notification_service import NotificationService
from app.services.task_service import serialize_task


class AutomationService:
    def __init__(self, session: Session) -> None:
        self.task_repo = TaskRepository(session)
        self.column_repo = ColumnRepository(session)
        self.notification_service = NotificationService(session)
        self.event_service = EventService(session)

    def apply_task_automations(self, task_id: str, source_event: str) -> Task | None:
        task = self.task_repo.get_by_id(task_id)
        if not task:
            return None

        changed_fields: dict[str, object] = {}
        notifications: list[tuple[str, str]] = []
        triggered_rules: list[str] = []

        tags = list(task.tags or [])
        if "urgent" in tags and task.priority != TaskPriority.HIGH:
            changed_fields["priority"] = TaskPriority.HIGH
            notifications.append(("Urgent task", "Задача помечена как срочная"))
            triggered_rules.append("urgent-priority")

        deadline = task.deadline
        if deadline and deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=UTC)
        if deadline and deadline <= datetime.now(UTC) + timedelta(hours=24):
            if "deadline-soon" not in tags:
                tags.append("deadline-soon")
                changed_fields["tags"] = tags
                notifications.append(("Deadline soon", "До дедлайна осталось меньше 24 часов"))
                triggered_rules.append("deadline-soon")

        if "auto-progress" in tags:
            in_progress = self.column_repo.get_by_title(task.board_id, "In Progress")
            if in_progress and task.column_id != in_progress.id:
                changed_fields["column_id"] = in_progress.id
                changed_fields["status"] = in_progress.title
                changed_fields["position"] = 1
                notifications.append(
                    ("Auto progress", "Задача автоматически перемещена в In Progress"),
                )
                triggered_rules.append("auto-progress")

        if source_event == TASK_MOVED:
            current_column = self.column_repo.get_by_id(
                str(changed_fields.get("column_id", task.column_id))
            )
            if current_column and current_column.title == "Done":
                notifications.append(("Task done", "Задача завершена"))
                triggered_rules.append("done-notification")

        if changed_fields:
            changed_fields["version"] = task.version + 1
            task = self.task_repo.update(task.id, **changed_fields) or task
            event_type = TASK_MOVED if "column_id" in changed_fields else TASK_UPDATED
            self.event_service.record_event(
                event_type,
                "task",
                task.id,
                {"task": serialize_task(task)},
            )

        for title, message in notifications:
            self.notification_service.create_notification(
                title=title,
                message=message,
                type="automation",
                task_id=task.id,
            )

        for rule_name in triggered_rules:
            self.event_service.record_event(
                AUTOMATION_TRIGGERED,
                "automation_rule",
                task.id,
                {
                    "board_id": task.board_id,
                    "task": serialize_task(task),
                    "rule": rule_name,
                },
            )

        return task
