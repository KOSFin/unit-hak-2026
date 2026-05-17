from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.schemas.board import BoardCreate, BoardCreatedResponse, BoardDetail
from app.schemas.event import ActivityEventRead, ActivityGroupRead
from app.schemas.column import ColumnRead
from app.services.board_service import BoardService
from app.repositories.event_repository import DomainEventRepository

router = APIRouter(prefix="/api/boards", tags=["boards"])
SessionDep = Annotated[Session, Depends(get_session)]


def serialize_board_detail(service: BoardService, board) -> BoardDetail:
    columns = service.list_columns(board.id)
    return BoardDetail(
        id=board.id,
        public_id=board.public_id,
        name=board.name,
        image_path=board.image_path,
        retention_days=board.retention_days,
        expires_after_days=board.expires_after_days,
        last_activity_at=board.last_activity_at,
        archived_at=board.archived_at,
        created_at=board.created_at,
        updated_at=board.updated_at,
        columns=[ColumnRead.model_validate(column) for column in columns],
    )


@router.post("", response_model=BoardCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_board(payload: BoardCreate, session: SessionDep) -> BoardCreatedResponse:
    service = BoardService(session)
    try:
        board = service.create_board(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    detail = serialize_board_detail(service, board)
    return BoardCreatedResponse(
        **detail.model_dump(),
        board_url=service.get_board_url(board.public_id),
    )


@router.get("/default", response_model=BoardDetail)
def get_default_board(session: SessionDep) -> BoardDetail:
    service = BoardService(session)
    board = service.get_default_board()
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    return serialize_board_detail(service, board)


@router.get("/{public_board_id}", response_model=BoardDetail)
def get_board(public_board_id: str, session: SessionDep) -> BoardDetail:
    service = BoardService(session)
    board = service.get_board_by_public_id(public_board_id)
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    return serialize_board_detail(service, board)


@router.get("/{public_board_id}/events", response_model=list[ActivityGroupRead])
def get_board_events(public_board_id: str, session: SessionDep, limit: int = 50) -> list[ActivityGroupRead]:
    service = BoardService(session)
    board = service.get_board_by_public_id(public_board_id)
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    
    events = DomainEventRepository(session).list_recent(board.id, limit=limit)
    
    # Group by correlation_id while preserving order
    groups = []
    current_group = None
    
    for event in events:
        if current_group is None:
            current_group = {"correlation_id": event.correlation_id, "events": [ActivityEventRead.model_validate(event)]}
        elif event.correlation_id == current_group["correlation_id"]:
            current_group["events"].append(ActivityEventRead.model_validate(event))
        else:
            groups.append(ActivityGroupRead(**current_group))
            current_group = {"correlation_id": event.correlation_id, "events": [ActivityEventRead.model_validate(event)]}
            
    if current_group:
        groups.append(ActivityGroupRead(**current_group))
        
    return groups
