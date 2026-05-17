from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class DomainEventSchema(BaseModel):
    id: str
    type: str
    entity_type: str
    entity_id: str | None = None
    board_id: str | None = None
    correlation_id: str | None = None
    source: str | None = None
    payload: dict[str, Any]
    processed: bool | None = None
    error: str | None = None
    created_at: datetime
    processed_at: datetime | None = None


class RealtimeEventSchema(BaseModel):
    type: str
    payload: dict[str, Any]
    createdAt: str
    boardId: str | None = None
    correlationId: str | None = None
    source: str | None = None


class ActivityEventRead(BaseModel):
    id: str
    type: str
    entity_type: str
    entity_id: str | None = None
    board_id: str | None = None
    correlation_id: str | None = None
    source: str | None = None
    payload: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ActivityGroupRead(BaseModel):
    correlation_id: str | None
    events: list[ActivityEventRead]
