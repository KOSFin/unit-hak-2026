from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.repositories.board_repository import BoardRepository
from app.core.config import get_settings


class CleanupService:
    def __init__(self, session: Session) -> None:
        self.board_repo = BoardRepository(session)
        self.settings = get_settings()

    def cleanup_inactive_boards(self, inactive_days: int) -> int:
        # Override inactive_days with what the board specifies, falling back to 3
        removed = 0
        now = datetime.now(UTC)
        for board in self.board_repo.list_all():
            if board.archived_at:
                continue
                
            expires_after = board.expires_after_days or inactive_days
            cutoff = now - timedelta(days=expires_after)
            
            last_activity = board.last_activity_at
            if last_activity and last_activity < cutoff:
                # Store image_path before deleting to clean up files
                image_path = board.image_path
                
                if self.board_repo.delete(board.id):
                    removed += 1
                    
                    # Also cleanup associated files
                    if image_path and image_path.startswith(f"/{self.settings.uploads_dir}/"):
                        filename = image_path.replace(f"/{self.settings.uploads_dir}/", "")
                        filepath = os.path.join(self.settings.uploads_dir, filename)
                        if os.path.exists(filepath):
                            try:
                                os.remove(filepath)
                            except OSError:
                                pass
                                
        return removed
