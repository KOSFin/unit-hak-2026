import uuid

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.core.database import Base


class Column(Base):
    __tablename__ = "columns"

    id = sa.Column(sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    board_id = sa.Column(sa.String(36), sa.ForeignKey("boards.id"), nullable=False)
    title = sa.Column(sa.String(200), nullable=False)
    position = sa.Column(sa.Integer, nullable=False)
    is_default = sa.Column(sa.Boolean, nullable=False, default=False)
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    updated_at = sa.Column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    board = relationship("Board", back_populates="columns")
    tasks = relationship("Task", back_populates="column", cascade="all, delete-orphan")
