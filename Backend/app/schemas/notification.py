from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    id: str = Field(description="Notification identifier.")
    board_id: str | None = Field(default=None, description="Related board identifier when scoped to a board.")
    title: str = Field(description="Notification title.")
    message: str = Field(description="Notification body.")
    type: str = Field(description="Notification type.", examples=["incoming-task"])
    task_id: str | None = Field(default=None, description="Related task identifier when applicable.")
    read: bool = Field(description="Whether the notification has been marked as read.")
    created_at: datetime = Field(description="Notification creation timestamp.")

    model_config = ConfigDict(from_attributes=True)


class MarkAllNotificationsReadResponse(BaseModel):
    updated: int = Field(description="Number of notifications marked as read.", examples=[3])
