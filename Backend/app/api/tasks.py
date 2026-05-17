from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.api.openapi import error_response
from app.core.database import get_session
from app.schemas.common import OperationStatusResponse
from app.schemas.task import TaskCreate, TaskMove, TaskRead, TaskUpdate
from app.services.task_service import TaskService, VersionConflictError

router = APIRouter(prefix="/api/tasks", tags=["tasks"])
SessionDep = Annotated[Session, Depends(get_session)]


@router.get(
    "",
    response_model=list[TaskRead],
    summary="List tasks",
    description="Returns tasks for all boards or filters them by `board_id` when provided.",
)
def list_tasks(
    session: SessionDep,
    board_id: str | None = Query(default=None, description="Optional board identifier used to scope the task list."),
) -> list[TaskRead]:
    service = TaskService(session)
    tasks = service.list_tasks(board_id)
    return [TaskRead.model_validate(task) for task in tasks]


@router.post(
    "",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create task",
    description="Creates a task in the specified board and column.",
    responses={404: error_response("Board or column was not found.", "Column not found")},
)
def create_task(payload: TaskCreate, session: SessionDep) -> TaskRead:
    service = TaskService(session)
    try:
        task = service.create_task(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return TaskRead.model_validate(task)


@router.get(
    "/{task_id}",
    response_model=TaskRead,
    summary="Get task",
    description="Returns a single task by identifier.",
    responses={404: error_response("Task was not found.", "Task not found")},
)
def get_task(
    session: SessionDep,
    task_id: str = Path(description="Task identifier.", examples=["task-123"]),
) -> TaskRead:
    service = TaskService(session)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskRead.model_validate(task)


@router.patch(
    "/{task_id}",
    response_model=TaskRead,
    summary="Update task",
    description="Partially updates a task. The current `version` must be supplied for optimistic locking.",
    responses={
        404: error_response("Task was not found.", "Task not found"),
        409: error_response("Task version conflict.", "Task version conflict"),
    },
)
def update_task(
    session: SessionDep,
    task_id: str = Path(description="Task identifier.", examples=["task-123"]),
    payload: TaskUpdate = ...,
) -> TaskRead:
    service = TaskService(session)
    try:
        task = service.update_task(task_id, payload)
    except VersionConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskRead.model_validate(task)


@router.patch(
    "/{task_id}/move",
    response_model=TaskRead,
    summary="Move task",
    description=(
        "Moves a task to another column and optionally to a target position. "
        "The current `version` must be supplied for optimistic locking."
    ),
    responses={
        404: error_response("Task or destination column was not found.", "Column not found"),
        409: error_response("Task version conflict.", "Task version conflict"),
    },
)
def move_task(
    session: SessionDep,
    task_id: str = Path(description="Task identifier.", examples=["task-123"]),
    payload: TaskMove = ...,
) -> TaskRead:
    service = TaskService(session)
    try:
        task = service.move_task(task_id, payload)
    except VersionConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskRead.model_validate(task)


@router.delete(
    "/{task_id}",
    response_model=OperationStatusResponse,
    summary="Delete task",
    description="Deletes a task by identifier.",
    responses={404: error_response("Task was not found.", "Task not found")},
)
def delete_task(
    session: SessionDep,
    task_id: str = Path(description="Task identifier.", examples=["task-123"]),
) -> OperationStatusResponse:
    service = TaskService(session)
    deleted = service.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return {"status": "deleted"}
