from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.schemas.notification import (
    MarkAllNotificationsReadResponse,
    NotificationResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/api/notifications", tags=["notifications"])
SessionDep = Annotated[Session, Depends(get_session)]


@router.get("", response_model=list[NotificationResponse])
def get_notifications(
    session: SessionDep,
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    board_id: str | None = None,
) -> list[NotificationResponse]:
    service = NotificationService(session)
    return [
        NotificationResponse.model_validate(notification)
        for notification in service.list_notifications(
            skip=skip,
            limit=limit,
            unread_only=unread_only,
            board_id=board_id,
        )
    ]


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_as_read(
    notification_id: str,
    session: SessionDep,
) -> NotificationResponse:
    service = NotificationService(session)
    notification = service.mark_as_read(notification_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return NotificationResponse.model_validate(notification)


@router.post("/mark-all-read", response_model=MarkAllNotificationsReadResponse)
def mark_all_as_read(session: SessionDep) -> MarkAllNotificationsReadResponse:
    service = NotificationService(session)
    return MarkAllNotificationsReadResponse(updated=service.mark_all_as_read())
