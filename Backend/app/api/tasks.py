from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.schemas.task import TaskCreate, TaskMove, TaskRead, TaskUpdate
from app.services.task_service import TaskService, VersionConflictError

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
def list_tasks(board_id: str | None = None, session: Session = Depends(get_session)):
    service = TaskService(session)
    tasks = service.list_tasks(board_id)
    return [TaskRead.model_validate(task) for task in tasks]


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, session: Session = Depends(get_session)):
    service = TaskService(session)
    try:
        task = service.create_task(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return TaskRead.model_validate(task)


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: str, session: Session = Depends(get_session)):
    service = TaskService(session)
    task = service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskRead.model_validate(task)


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(task_id: str, payload: TaskUpdate, session: Session = Depends(get_session)):
    service = TaskService(session)
    try:
        task = service.update_task(task_id, payload)
    except VersionConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return TaskRead.model_validate(task)


@router.patch("/{task_id}/move", response_model=TaskRead)
def move_task(task_id: str, payload: TaskMove, session: Session = Depends(get_session)):
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


@router.delete("/{task_id}")
def delete_task(task_id: str, session: Session = Depends(get_session)):
    service = TaskService(session)
    deleted = service.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return {"status": "deleted"}
