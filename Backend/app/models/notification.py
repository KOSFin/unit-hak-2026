import uuid

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = sa.Column(sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    board_id = sa.Column(sa.String(36), sa.ForeignKey("boards.id"), nullable=True, index=True)
    title = sa.Column(sa.String(200), nullable=False)
    message = sa.Column(sa.Text, nullable=False)
    type = sa.Column(sa.String(100), nullable=False)
    task_id = sa.Column(sa.String(36), sa.ForeignKey("tasks.id"), nullable=True)
    read = sa.Column(sa.Boolean, nullable=False, default=False)
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)

    task = relationship("Task")
