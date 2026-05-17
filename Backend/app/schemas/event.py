from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DomainEventSchema(BaseModel):
    id: str = Field(description="Domain event identifier.")
    type: str = Field(description="Domain event type.")
    entity_type: str = Field(description="Domain entity type affected by the event.")
    entity_id: str | None = Field(default=None, description="Identifier of the affected entity.")
    board_id: str | None = Field(default=None, description="Board identifier associated with the event.")
    correlation_id: str | None = Field(default=None, description="Correlation id grouping related events.")
    source: str | None = Field(default=None, description="Origin of the event, for example API or WORKER.")
    payload: dict[str, Any] = Field(description="Event payload.")
    processed: bool | None = Field(default=None, description="Worker processing flag when applicable.")
    error: str | None = Field(default=None, description="Worker processing error when applicable.")
    created_at: datetime = Field(description="Event creation timestamp.")
    processed_at: datetime | None = Field(default=None, description="Worker processing timestamp.")


class RealtimeEventSchema(BaseModel):
    type: str = Field(description="Realtime event type.")
    payload: dict[str, Any] = Field(description="Realtime event payload.")
    createdAt: str = Field(description="Event creation timestamp serialized for clients.")
    boardId: str | None = Field(default=None, description="Board identifier associated with the realtime event.")
    correlationId: str | None = Field(default=None, description="Correlation id grouping related realtime events.")
    source: str | None = Field(default=None, description="Origin of the event.")


class ActivityEventRead(BaseModel):
    id: str = Field(description="Domain event identifier.")
    type: str = Field(description="Activity event type.")
    entity_type: str = Field(description="Affected entity type.")
    entity_id: str | None = Field(default=None, description="Affected entity identifier.")
    board_id: str | None = Field(default=None, description="Board identifier associated with the event.")
    correlation_id: str | None = Field(default=None, description="Correlation id grouping related activity items.")
    source: str | None = Field(default=None, description="Origin of the event.")
    payload: dict[str, Any] = Field(description="Event payload emitted by the backend.")
    created_at: datetime = Field(description="Event creation timestamp.")

    model_config = ConfigDict(from_attributes=True)


class ActivityGroupRead(BaseModel):
    correlation_id: str | None = Field(
        description="Correlation id shared by grouped events. Null when the event is standalone.",
    )
    events: list[ActivityEventRead] = Field(description="Ordered list of grouped activity events.")
