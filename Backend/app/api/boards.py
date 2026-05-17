from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.api.openapi import error_response
from app.core.database import get_session
from app.schemas.board import BoardCreate, BoardCreatedResponse, BoardDetail, BoardRead, BoardUpdate
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
        board_url=service.get_board_url(board.public_id),
        name=board.name,
        image_path=board.image_path,
        owner_guest_id=board.owner_guest_id,
        allow_guest_admin=board.allow_guest_admin,
        retention_days=board.retention_days,
        expires_after_days=board.expires_after_days,
        last_activity_at=board.last_activity_at,
        archived_at=board.archived_at,
        created_at=board.created_at,
        updated_at=board.updated_at,
        columns=[ColumnRead.model_validate(column) for column in columns],
    )


@router.post(
    "",
    response_model=BoardCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create board",
    description=(
        "Creates a new board with default columns. Guest-created boards currently support "
        "a retention period of 3 days only."
    ),
    responses={422: error_response("Board payload violated a business rule.", "Long-term boards require an account. Authentication is coming soon.")},
)
def create_board(payload: BoardCreate, session: SessionDep) -> BoardCreatedResponse:
    service = BoardService(session)
    try:
        board = service.create_board(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    detail = serialize_board_detail(service, board)
    return BoardCreatedResponse(**detail.model_dump())


@router.get(
    "/default",
    response_model=BoardDetail,
    summary="Get default board",
    description="Returns the default board used by worker-side incoming task processing.",
    responses={404: error_response("Default board was not found.", "Board not found")},
)
def get_default_board(session: SessionDep) -> BoardDetail:
    service = BoardService(session)
    board = service.get_default_board()
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    return serialize_board_detail(service, board)


@router.get(
    "/owned/{owner_guest_id}",
    response_model=list[BoardRead],
    summary="List boards owned by guest",
    description="Returns active boards created by the specified guest owner, ordered by recent activity.",
)
def list_owned_boards(
    session: SessionDep,
    owner_guest_id: str = Path(description="Guest identifier of the board owner.", examples=["guest-42"]),
) -> list[BoardRead]:
    service = BoardService(session)
    boards = service.list_owned_boards(owner_guest_id)
    response = []
    for board in boards:
        payload = BoardRead.model_validate(board).model_dump()
        payload["board_url"] = service.get_board_url(board.public_id)
        response.append(BoardRead(**payload))
    return response


@router.get(
    "/{public_board_id}",
    response_model=BoardDetail,
    summary="Get board by public id",
    description="Returns board details, including ordered columns, by public identifier.",
    responses={404: error_response("Board was not found.", "Board not found")},
)
def get_board(
    session: SessionDep,
    public_board_id: str = Path(description="Public board identifier.", examples=["4hY6kK4mQ1zvS8L2N0Ab"]),
) -> BoardDetail:
    service = BoardService(session)
    board = service.get_board_by_public_id(public_board_id)
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    return serialize_board_detail(service, board)


@router.patch(
    "/{public_board_id}",
    response_model=BoardDetail,
    summary="Update board",
    description="Partially updates board metadata such as name, cover image, and guest-admin permissions.",
    responses={
        404: error_response("Board was not found.", "Board not found"),
        422: error_response("Board payload violated a business rule.", "Board name cannot be empty."),
    },
)
def update_board(
    session: SessionDep,
    public_board_id: str = Path(description="Public board identifier.", examples=["4hY6kK4mQ1zvS8L2N0Ab"]),
    payload: BoardUpdate = ...,
) -> BoardDetail:
    service = BoardService(session)
    try:
        board = service.update_board(public_board_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    return serialize_board_detail(service, board)


@router.delete(
    "/{public_board_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete board",
    description="Deletes a board and its related columns and tasks by public identifier.",
    responses={404: error_response("Board was not found.", "Board not found")},
)
def delete_board(
    session: SessionDep,
    public_board_id: str = Path(description="Public board identifier.", examples=["4hY6kK4mQ1zvS8L2N0Ab"]),
) -> None:
    service = BoardService(session)
    deleted = service.delete_board(public_board_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")


@router.get(
    "/{public_board_id}/events",
    response_model=list[ActivityGroupRead],
    summary="Get board activity timeline",
    description=(
        "Returns recent domain events for the board, grouped by `correlation_id` when present "
        "to simplify frontend activity rendering."
    ),
    responses={404: error_response("Board was not found.", "Board not found")},
)
def get_board_events(
    session: SessionDep,
    public_board_id: str = Path(description="Public board identifier.", examples=["4hY6kK4mQ1zvS8L2N0Ab"]),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of recent domain events to inspect."),
) -> list[ActivityGroupRead]:
    service = BoardService(session)
    board = service.get_board_by_public_id(public_board_id)
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")

    events = DomainEventRepository(session).list_recent(board.id, limit=limit)

    # Group by correlation_id when present; otherwise keep single events isolated
    groups = []
    current_group = None

    for event in events:
        event_key = event.correlation_id or f"event:{event.id}"
        if current_group is None:
            current_group = {
                "group_key": event_key,
                "correlation_id": event.correlation_id,
                "events": [ActivityEventRead.model_validate(event)],
            }
        elif event_key == current_group["group_key"]:
            current_group["events"].append(ActivityEventRead.model_validate(event))
        else:
            groups.append(ActivityGroupRead(
                correlation_id=current_group["correlation_id"],
                events=current_group["events"],
            ))
            current_group = {
                "group_key": event_key,
                "correlation_id": event.correlation_id,
                "events": [ActivityEventRead.model_validate(event)],
            }

    if current_group:
        groups.append(ActivityGroupRead(
            correlation_id=current_group["correlation_id"],
            events=current_group["events"],
        ))

    return groups
