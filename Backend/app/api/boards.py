from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.schemas.board import BoardDetail
from app.schemas.column import ColumnRead
from app.services.board_service import BoardService

router = APIRouter(prefix="/api/boards", tags=["boards"])
SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/default", response_model=BoardDetail)
def get_default_board(session: SessionDep) -> BoardDetail:
    service = BoardService(session)
    board = service.get_default_board()
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    columns = service.list_columns(board.id)
    return BoardDetail(
        id=board.id,
        name=board.name,
        created_at=board.created_at,
        updated_at=board.updated_at,
        columns=[ColumnRead.model_validate(column) for column in columns],
    )


@router.get("/{board_id}", response_model=BoardDetail)
def get_board(board_id: str, session: SessionDep) -> BoardDetail:
    service = BoardService(session)
    board = service.get_board(board_id)
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    columns = service.list_columns(board.id)
    return BoardDetail(
        id=board.id,
        name=board.name,
        created_at=board.created_at,
        updated_at=board.updated_at,
        columns=[ColumnRead.model_validate(column) for column in columns],
    )
