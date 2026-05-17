from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.api.openapi import error_response
from app.core.database import get_session
from app.schemas.notification import (
    MarkAllNotificationsReadResponse,
    NotificationResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/api/notifications", tags=["notifications"])
SessionDep = Annotated[Session, Depends(get_session)]


@router.get(
    "",
    response_model=list[NotificationResponse],
    summary="List notifications",
    description="Returns notifications with optional pagination, unread filtering, and board scoping.",
)
def get_notifications(
    session: SessionDep,
    skip: int = Query(default=0, ge=0, description="Number of notifications to skip from the start of the result set."),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of notifications to return."),
    unread_only: bool = Query(default=False, description="When true, only unread notifications are returned."),
    board_id: str | None = Query(default=None, description="Optional board identifier used to scope notifications."),
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


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark notification as read",
    description="Marks a single notification as read, optionally scoped by board identifier.",
    responses={404: error_response("Notification was not found.", "Notification not found")},
)
def mark_notification_as_read(
    session: SessionDep,
    notification_id: str = Path(description="Notification identifier.", examples=["notification-123"]),
    board_id: str | None = Query(default=None, description="Optional board identifier used to scope the mutation."),
) -> NotificationResponse:
    service = NotificationService(session)
    notification = service.mark_as_read(notification_id, board_id=board_id)
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return NotificationResponse.model_validate(notification)


@router.post(
    "/mark-all-read",
    response_model=MarkAllNotificationsReadResponse,
    summary="Mark all notifications as read",
    description="Marks all unread notifications as read, optionally scoped by board identifier.",
)
def mark_all_as_read(
    session: SessionDep,
    board_id: str | None = Query(default=None, description="Optional board identifier used to scope the mutation."),
) -> MarkAllNotificationsReadResponse:
    service = NotificationService(session)
    return MarkAllNotificationsReadResponse(updated=service.mark_all_as_read(board_id=board_id))
