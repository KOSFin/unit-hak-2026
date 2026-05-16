import uuid
from enum import Enum

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.core.database import Base


class TaskPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Task(Base):
    __tablename__ = "tasks"

    id = sa.Column(sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    board_id = sa.Column(sa.String(36), sa.ForeignKey("boards.id"), nullable=False)
    column_id = sa.Column(sa.String(36), sa.ForeignKey("columns.id"), nullable=False)
    title = sa.Column(sa.String(200), nullable=False)
    description = sa.Column(sa.Text, nullable=True)
    status = sa.Column(sa.String(50), nullable=False, default="To Do")
    priority = sa.Column(
        sa.Enum(TaskPriority, name="task_priority", native_enum=False),
        nullable=False,
        default=TaskPriority.MEDIUM,
    )
    tags = sa.Column(sa.JSON, nullable=False, default=list)
    deadline = sa.Column(sa.DateTime(timezone=True), nullable=True)
    position = sa.Column(sa.Integer, nullable=False, default=0)
    version = sa.Column(sa.Integer, nullable=False, default=1)
    correlation_id = sa.Column(sa.String(64), nullable=True, index=True)
    guest_id = sa.Column(sa.String(64), nullable=True, index=True)
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    updated_at = sa.Column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    board = relationship("Board", back_populates="tasks")
    column = relationship("Column", back_populates="tasks")
