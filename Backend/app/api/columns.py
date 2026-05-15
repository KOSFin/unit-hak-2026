from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.schemas.column import ColumnCreate, ColumnRead, ColumnUpdate
from app.services.column_service import ColumnHasTasksError, ColumnService

router = APIRouter(prefix="/api/columns", tags=["columns"])


@router.post("", response_model=ColumnRead, status_code=status.HTTP_201_CREATED)
def create_column(payload: ColumnCreate, session: Session = Depends(get_session)):
    service = ColumnService(session)
    column = service.create_column(payload)
    return ColumnRead.model_validate(column)


@router.patch("/{column_id}", response_model=ColumnRead)
def update_column(column_id: str, payload: ColumnUpdate, session: Session = Depends(get_session)):
    service = ColumnService(session)
    column = service.update_column(column_id, payload)
    if not column:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Column not found")
    return ColumnRead.model_validate(column)


@router.delete("/{column_id}")
def delete_column(column_id: str, session: Session = Depends(get_session)):
    service = ColumnService(session)
    try:
        deleted = service.delete_column(column_id)
    except ColumnHasTasksError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Column not found")
    return {"status": "deleted"}
