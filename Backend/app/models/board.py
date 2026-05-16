import uuid

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from app.core.database import Base


class Board(Base):
    __tablename__ = "boards"

    id = sa.Column(sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    public_id = sa.Column(sa.String(32), nullable=False, unique=True, index=True)
    name = sa.Column(sa.String(200), nullable=False)
    image_path = sa.Column(sa.String(500), nullable=True)
    retention_days = sa.Column(sa.Integer, nullable=False, default=3)
    expires_after_days = sa.Column(sa.Integer, nullable=False, default=3)
    last_activity_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    archived_at = sa.Column(sa.DateTime(timezone=True), nullable=True)
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    updated_at = sa.Column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    columns = relationship("Column", back_populates="board", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="board", cascade="all, delete-orphan")
