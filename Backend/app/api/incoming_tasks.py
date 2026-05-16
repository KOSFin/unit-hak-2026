from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.schemas.incoming_task import IncomingTaskCreate, IncomingTaskResponse
from app.services.incoming_task_service import IncomingTaskService

router = APIRouter(prefix="/api/incoming-tasks", tags=["incoming-tasks"])
SessionDep = Annotated[Session, Depends(get_session)]


@router.get("", response_model=list[IncomingTaskResponse])
def get_incoming_tasks(
    session: SessionDep,
    skip: int = 0,
    limit: int = 50,
    task_status: str | None = None,
    board_id: str | None = None,
) -> list[IncomingTaskResponse]:
    service = IncomingTaskService(session)
    return [
        IncomingTaskResponse.model_validate(task)
        for task in service.list_tasks(skip=skip, limit=limit, status=task_status, board_id=board_id)
    ]


@router.post("", response_model=IncomingTaskResponse, status_code=status.HTTP_201_CREATED)
def create_incoming_task(
    payload: IncomingTaskCreate,
    session: SessionDep,
) -> IncomingTaskResponse:
    service = IncomingTaskService(session)
    task = service.create_task(payload)
    return IncomingTaskResponse.model_validate(task)
