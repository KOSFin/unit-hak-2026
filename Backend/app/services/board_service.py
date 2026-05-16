from datetime import UTC, datetime
from secrets import token_urlsafe

from sqlalchemy.orm import Session

from app.models.board import Board
from app.models.column import Column
from app.core.config import get_settings
from app.repositories.board_repository import BoardRepository
from app.repositories.column_repository import ColumnRepository
from app.schemas.board import BoardCreate

DEFAULT_COLUMNS = [
    {"title": "To Do", "position": 1, "is_default": True},
    {"title": "In Progress", "position": 2, "is_default": False},
    {"title": "Done", "position": 3, "is_default": False},
]


class BoardService:
    def __init__(self, session: Session) -> None:
        self.board_repo = BoardRepository(session)
        self.column_repo = ColumnRepository(session)
        self.settings = get_settings()

    def get_default_board(self) -> Board | None:
        return self.board_repo.get_default()

    def get_board(self, board_id: str) -> Board | None:
        return self.board_repo.get_by_id(board_id)

    def get_board_by_public_id(self, public_id: str) -> Board | None:
        return self.board_repo.get_by_public_id(public_id)

    def list_columns(self, board_id: str) -> list[Column]:
        return self.column_repo.list_by_board(board_id)

    def create_board(self, payload: BoardCreate, image_path: str | None = None) -> Board:
        retention_days = payload.retention_days
        if retention_days != 3:
            raise ValueError("Long-term boards require an account. Authentication is coming soon.")
        public_id = self._generate_public_id()
        board = self.board_repo.create(
            name=payload.name,
            public_id=public_id,
            retention_days=retention_days,
            image_path=image_path,
        )
        for column in DEFAULT_COLUMNS:
            self.column_repo.create(board.id, column["title"], column["position"], column["is_default"])
        self.board_repo.update_last_activity(board.id, datetime.now(UTC))
        return board

    def touch_board(self, board_id: str) -> Board | None:
        return self.board_repo.update_last_activity(board_id, datetime.now(UTC))

    def get_board_url(self, public_id: str) -> str:
        base = self.settings.public_board_url_base
        if base:
            return f"{base.rstrip('/')}/board/{public_id}"
        return f"/board/{public_id}"

    def _generate_public_id(self) -> str:
        candidate = token_urlsafe(12).replace("-", "").replace("_", "")[:20]
        while self.board_repo.get_by_public_id(candidate):
            candidate = token_urlsafe(12).replace("-", "").replace("_", "")[:20]
        return candidate
