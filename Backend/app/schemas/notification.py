from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    id: str
    board_id: str | None
    title: str
    message: str
    type: str
    task_id: str | None
    read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MarkAllNotificationsReadResponse(BaseModel):
    updated: int
