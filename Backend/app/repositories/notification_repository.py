from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        title: str,
        message: str,
        type: str,
        task_id: str | None,
        board_id: str | None = None,
    ) -> Notification:
        notification = Notification(
            title=title,
            message=message,
            type=type,
            task_id=task_id,
            board_id=board_id,
        )
        self.session.add(notification)
        self.session.commit()
        self.session.refresh(notification)
        return notification

    def get_by_id(self, notification_id: str) -> Notification | None:
        return self.session.get(Notification, notification_id)

    def list_all(self, board_id: str | None = None) -> list[Notification]:
        stmt = select(Notification)
        if board_id:
            stmt = stmt.where(Notification.board_id == board_id)
        stmt = stmt.order_by(Notification.created_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def mark_read(self, notification_id: str, board_id: str | None = None) -> Notification | None:
        notification = self.get_by_id(notification_id)
        if not notification:
            return None
        if board_id and notification.board_id != board_id:
            return None
        notification.read = True
        self.session.commit()
        self.session.refresh(notification)
        return notification

    def mark_all_read(self, board_id: str | None = None) -> int:
        query = self.session.query(Notification).filter(Notification.read.is_(False))
        if board_id:
            query = query.filter(Notification.board_id == board_id)
        unread = query.update({Notification.read: True})
        self.session.commit()
        return int(unread)
