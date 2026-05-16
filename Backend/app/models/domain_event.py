import uuid

import sqlalchemy as sa

from app.core.database import Base


class DomainEvent(Base):
    __tablename__ = "domain_events"

    id = sa.Column(sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = sa.Column(sa.String(100), nullable=False)
    entity_type = sa.Column(sa.String(100), nullable=False)
    entity_id = sa.Column(sa.String(36), nullable=True)
    board_id = sa.Column(sa.String(36), sa.ForeignKey("boards.id"), nullable=True, index=True)
    correlation_id = sa.Column(sa.String(64), nullable=True, index=True)
    source = sa.Column(sa.String(50), nullable=True)
    payload = sa.Column(sa.JSON, nullable=False, default=dict)
    processed = sa.Column(sa.Boolean, nullable=False, default=False)
    error = sa.Column(sa.Text, nullable=True)
    created_at = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    processed_at = sa.Column(sa.DateTime(timezone=True), nullable=True)
