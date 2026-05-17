from datetime import UTC, datetime
from secrets import token_urlsafe

import sqlalchemy as sa
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.board import Board

DEFAULT_BOARD_NAME = "FlowBoard"


class BoardRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        name: str,
        public_id: str | None = None,
        retention_days: int = 3,
        image_path: str | None = None,
        owner_guest_id: str | None = None,
        allow_guest_admin: bool = False,
    ) -> Board:
        if not public_id:
            public_id = token_urlsafe(12).replace("-", "").replace("_", "")[:20]
        board = Board(
            name=name,
            public_id=public_id,
            owner_guest_id=owner_guest_id,
            allow_guest_admin=allow_guest_admin,
            retention_days=retention_days,
            expires_after_days=retention_days,
            image_path=image_path,
        )
        self.session.add(board)
        self.session.commit()
        self.session.refresh(board)
        return board

    def get_by_id(self, board_id: str) -> Board | None:
        return self.session.get(Board, board_id)

    def get_by_name(self, name: str) -> Board | None:
        stmt = select(Board).where(Board.name == name)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_public_id(self, public_id: str) -> Board | None:
        stmt = select(Board).where(Board.public_id == public_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_all(self) -> list[Board]:
        stmt = select(Board).order_by(Board.created_at)
        return list(self.session.execute(stmt).scalars().all())

    def get_default(self) -> Board | None:
        return self.get_by_name(DEFAULT_BOARD_NAME)

    def update_name(self, board_id: str, name: str) -> Board | None:
        board = self.get_by_id(board_id)
        if not board:
            return None
        board.name = name
        self.session.commit()
        self.session.refresh(board)
        return board

    def update(
        self,
        board_id: str,
        name: str | None = None,
        image_path: str | None = None,
        allow_guest_admin: bool | None = None,
    ) -> Board | None:
        board = self.get_by_id(board_id)
        if not board:
            return None
        if name is not None:
            board.name = name
        if image_path is not None:
            board.image_path = image_path
        if allow_guest_admin is not None:
            board.allow_guest_admin = allow_guest_admin
        self.session.commit()
        self.session.refresh(board)
        return board

    def delete(self, board_id: str) -> bool:
        board = self.get_by_id(board_id)
        if not board:
            return False
        self.session.delete(board)
        self.session.commit()
        return True

    def update_last_activity(self, board_id: str, at=None) -> Board | None:
        board = self.get_by_id(board_id)
        if not board:
            return None
        board.last_activity_at = at or datetime.now(UTC)
        self.session.commit()
        self.session.refresh(board)
        return board

    def archive(self, board_id: str) -> Board | None:
        board = self.get_by_id(board_id)
        if not board:
            return None
        board.archived_at = datetime.now(UTC)
        self.session.commit()
        self.session.refresh(board)
        return board
