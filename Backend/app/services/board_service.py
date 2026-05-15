from sqlalchemy.orm import Session

from app.models.board import Board
from app.models.column import Column
from app.repositories.board_repository import BoardRepository
from app.repositories.column_repository import ColumnRepository


class BoardService:
    def __init__(self, session: Session) -> None:
        self.board_repo = BoardRepository(session)
        self.column_repo = ColumnRepository(session)

    def get_default_board(self) -> Board | None:
        return self.board_repo.get_default()

    def get_board(self, board_id: str) -> Board | None:
        return self.board_repo.get_by_id(board_id)

    def list_columns(self, board_id: str) -> list[Column]:
        return self.column_repo.list_by_board(board_id)
