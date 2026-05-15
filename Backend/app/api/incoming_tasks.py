from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.schemas.incoming_task import IncomingTaskResponse
from app.services.incoming_task_service import IncomingTaskService

router = APIRouter(prefix="/api/incoming-tasks", tags=["Incoming Tasks"])


@router.get("", response_model=list[IncomingTaskResponse])
def get_incoming_tasks(
    skip: int = 0,
    limit: int = 50,
    task_status: str | None = None,
    session: Session = Depends(get_session),
):
    service = IncomingTaskService(session)
    return service.list_tasks(skip=skip, limit=limit, status=task_status)


@router.patch("/{task_id}/accept", response_model=IncomingTaskResponse)
def accept_incoming_task(
    task_id: str,
    session: Session = Depends(get_session),
):
    service = IncomingTaskService(session)
    task = service.update_status(task_id, "ACCEPTED")
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Incoming task not found"
        )
    return task


@router.patch("/{task_id}/reject", response_model=IncomingTaskResponse)
def reject_incoming_task(
    task_id: str,
    session: Session = Depends(get_session),
):
    service = IncomingTaskService(session)
    task = service.update_status(task_id, "REJECTED")
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Incoming task not found"
        )
    return task

