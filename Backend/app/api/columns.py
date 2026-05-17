from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.api.openapi import error_response
from app.core.database import get_session
from app.schemas.common import OperationStatusResponse
from app.schemas.column import ColumnCreate, ColumnRead, ColumnUpdate
from app.services.column_service import ColumnHasTasksError, ColumnService

router = APIRouter(prefix="/api/columns", tags=["columns"])
SessionDep = Annotated[Session, Depends(get_session)]


@router.post(
    "",
    response_model=ColumnRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create column",
    description="Creates a new column in the target board.",
    responses={404: error_response("Target board was not found.", "Board not found")},
)
def create_column(payload: ColumnCreate, session: SessionDep) -> ColumnRead:
    service = ColumnService(session)
    try:
        column = service.create_column(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ColumnRead.model_validate(column)


@router.patch(
    "/{column_id}",
    response_model=ColumnRead,
    summary="Update column",
    description="Partially updates column attributes such as title, position, and default status.",
    responses={404: error_response("Column was not found.", "Column not found")},
)
def update_column(
    session: SessionDep,
    payload: ColumnUpdate = ...,
    column_id: str = Path(description="Column identifier.", examples=["column-123"]),
) -> ColumnRead:
    service = ColumnService(session)
    column = service.update_column(column_id, payload)
    if not column:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Column not found")
    return ColumnRead.model_validate(column)


@router.delete(
    "/{column_id}",
    response_model=OperationStatusResponse,
    summary="Delete column",
    description="Deletes a column when it does not contain tasks.",
    responses={
        404: error_response("Column was not found.", "Column not found"),
        409: error_response("Column still contains tasks and cannot be deleted.", "Column has tasks"),
    },
)
def delete_column(
    session: SessionDep,
    column_id: str = Path(description="Column identifier.", examples=["column-123"]),
) -> OperationStatusResponse:
    service = ColumnService(session)
    try:
        deleted = service.delete_column(column_id)
    except ColumnHasTasksError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Column not found")
    return {"status": "deleted"}
