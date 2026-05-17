from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.api.openapi import error_response
from app.core.database import get_session
from app.schemas.incoming_task import IncomingTaskCreate, IncomingTaskResponse
from app.services.incoming_task_service import IncomingTaskService

router = APIRouter(prefix="/api/incoming-tasks", tags=["incoming-tasks"])
SessionDep = Annotated[Session, Depends(get_session)]


@router.get(
    "",
    response_model=list[IncomingTaskResponse],
    summary="List incoming tasks",
    description="Returns incoming-task ingestion records with optional pagination and filtering.",
)
def get_incoming_tasks(
    session: SessionDep,
    skip: int = Query(default=0, ge=0, description="Number of incoming tasks to skip."),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of incoming tasks to return."),
    task_status: str | None = Query(default=None, description="Optional incoming-task status filter."),
    board_id: str | None = Query(default=None, description="Optional board identifier used to scope results."),
) -> list[IncomingTaskResponse]:
    service = IncomingTaskService(session)
    return [
        IncomingTaskResponse.model_validate(task)
        for task in service.list_tasks(skip=skip, limit=limit, status=task_status, board_id=board_id)
    ]


@router.post(
    "",
    response_model=IncomingTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create incoming task record",
    description=(
        "Creates a raw incoming-task record for asynchronous worker processing. "
        "Duplicate `external_id` values are returned as `DUPLICATE` records."
    ),
)
def create_incoming_task(
    payload: IncomingTaskCreate,
    session: SessionDep,
) -> IncomingTaskResponse:
    service = IncomingTaskService(session)
    task = service.create_task(payload)
    return IncomingTaskResponse.model_validate(task)


@router.post(
    "/{incoming_task_id}/reprocess",
    response_model=IncomingTaskResponse,
    summary="Reprocess incoming task",
    description=(
        "Triggers worker-equivalent processing for an existing incoming-task record. "
        "This endpoint is intended for manual retries from the UI."
    ),
    responses={
        404: error_response("Incoming task was not found or is not visible in the requested board scope.", "Incoming task not found"),
        409: error_response("Incoming task could not be processed because backend prerequisites are missing.", "Default board not found"),
    },
)
def reprocess_incoming_task(
    session: SessionDep,
    incoming_task_id: str = Path(description="Incoming task identifier.", examples=["incoming-123"]),
    board_id: str | None = Query(default=None, description="Optional board identifier used to scope the retry."),
) -> IncomingTaskResponse:
    service = IncomingTaskService(session)
    existing = service.get_task(incoming_task_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incoming task not found")
    if board_id and existing.board_id != board_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incoming task not found")
    try:
        processed = service.process_incoming_task(incoming_task_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if not processed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Incoming task could not be reprocessed")
    return IncomingTaskResponse.model_validate(processed)
