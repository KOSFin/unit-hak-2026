from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IncomingTaskResponse(BaseModel):
    id: str
    external_id: str
    raw_payload: dict[str, Any]
    status: str
    validation_error: str | None
    created_at: datetime
    processed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class IncomingTaskCreate(BaseModel):
    external_id: str
    raw_payload: dict[str, Any] = Field(default_factory=dict)
