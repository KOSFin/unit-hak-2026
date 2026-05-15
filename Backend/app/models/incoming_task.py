import uuid
from enum import Enum

import sqlalchemy as sa

from app.core.database import Base


class IncomingTaskStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class IncomingTask(Base):
    __tablename__ = "incoming_tasks"

    id = sa.Column(sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    external_id = sa.Column(sa.String(200), nullable=False, unique=True)
    raw_payload = sa.Column(sa.JSON, nullable=False, default=dict)
    status = sa.Column(
        sa.Enum(IncomingTaskStatus, name="incoming_task_status", native_enum=False),
        nullable=False,
        default=IncomingTaskStatus.PENDING,
    )
    validation_error = sa.Column(sa.Text, nullable=True)
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    processed_at = sa.Column(sa.DateTime(timezone=True), nullable=True)
