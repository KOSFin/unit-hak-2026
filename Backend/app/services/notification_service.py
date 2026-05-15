from sqlalchemy.orm import Session

from app.repositories.notification_repository import NotificationRepository


class NotificationService:
    def __init__(self, session: Session):
        self.repo = NotificationRepository(session)

    def list_notifications(self, skip: int = 0, limit: int = 50, unread_only: bool = False):
        notifications = self.repo.list_all()
        if unread_only:
            notifications = [n for n in notifications if not n.read]
        return notifications[skip:skip+limit]

    def mark_as_read(self, notification_id: str):
        return self.repo.mark_read(notification_id)

    def create_notification(self, title: str, message: str, type: str, task_id: str | None = None):
        return self.repo.create(title, message, type, task_id)
