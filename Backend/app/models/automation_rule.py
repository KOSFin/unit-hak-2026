import uuid

import sqlalchemy as sa

from app.core.database import Base


class AutomationRule(Base):
    __tablename__ = "automation_rules"

    id = sa.Column(sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    board_id = sa.Column(sa.String(36), sa.ForeignKey("boards.id"), nullable=True, index=True)
    name = sa.Column(sa.String(200), nullable=False)
    enabled = sa.Column(sa.Boolean, nullable=False, default=True)
    trigger_type = sa.Column(sa.String(100), nullable=False)
    condition = sa.Column(sa.JSON, nullable=False, default=dict)
    action = sa.Column(sa.JSON, nullable=False, default=dict)
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    updated_at = sa.Column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )
