from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.task import Task
from app.queue.message_types import NOTIFICATION_CREATED
from app.repositories.notification_repository import NotificationRepository
from app.repositories.task_repository import TaskRepository
from app.services.event_service import EventService


class NotificationService:
    def __init__(self, session: Session):
        self.repo = NotificationRepository(session)
        self.task_repo = TaskRepository(session)
        self.event_service = EventService(session)

    def list_notifications(
        self,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False,
        board_id: str | None = None,
    ):
        notifications = self.repo.list_all(board_id=board_id)
        if unread_only:
            notifications = [n for n in notifications if not n.read]
        return notifications[skip : skip + limit]

    def mark_as_read(self, notification_id: str, board_id: str | None = None):
        return self.repo.mark_read(notification_id, board_id=board_id)

    def mark_all_as_read(self, board_id: str | None = None) -> int:
        return self.repo.mark_all_read(board_id=board_id)

    def create_notification(
        self,
        title: str,
        message: str,
        type: str,
        task_id: str | None = None,
        board_id: str | None = None,
    ):
        notification = self.repo.create(title, message, type, task_id, board_id=board_id)
        self.event_service.record_event(
            NOTIFICATION_CREATED,
            "notification",
            notification.id,
            self._serialize_payload(notification),
            board_id=board_id,
            source="SYSTEM",
        )
        return notification

    def _serialize_payload(self, notification: Notification) -> dict:
        task: Task | None = None
        if notification.task_id:
            task = self.task_repo.get_by_id(notification.task_id)

        return {
            "notification": {
                "id": notification.id,
                "title": notification.title,
                "message": notification.message,
                "type": notification.type,
                "task_id": notification.task_id,
                "read": notification.read,
                "created_at": notification.created_at.isoformat(),
            },
            "board_id": task.board_id if task else notification.board_id,
        }
