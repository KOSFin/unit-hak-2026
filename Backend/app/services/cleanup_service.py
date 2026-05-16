from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.repositories.board_repository import BoardRepository


class CleanupService:
    def __init__(self, session: Session) -> None:
        self.board_repo = BoardRepository(session)

    def cleanup_inactive_boards(self, inactive_days: int) -> int:
        cutoff = datetime.now(UTC) - timedelta(days=inactive_days)
        removed = 0
        for board in self.board_repo.list_all():
            if board.archived_at:
                continue
            last_activity = board.last_activity_at
            if last_activity and last_activity < cutoff:
                if self.board_repo.delete(board.id):
                    removed += 1
        return removed
