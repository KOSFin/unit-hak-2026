from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IncomingTaskResponse(BaseModel):
    id: str = Field(description="Incoming task record identifier.")
    board_id: str | None = Field(default=None, description="Target board identifier if explicitly provided.")
    external_id: str = Field(description="Upstream unique identifier used for de-duplication.")
    raw_payload: dict[str, Any] = Field(description="Original ingestion payload received by the API.")
    status: str = Field(
        description="Processing state of the incoming task.",
        examples=["RECEIVED", "VALIDATED", "REJECTED", "PROCESSED", "DUPLICATE"],
    )
    validation_error: str | None = Field(default=None, description="Validation failure reason when processing is rejected.")
    created_at: datetime = Field(description="Creation timestamp of the incoming task record.")
    processed_at: datetime | None = Field(default=None, description="Processing completion timestamp when available.")

    model_config = ConfigDict(from_attributes=True)


class IncomingTaskCreate(BaseModel):
    external_id: str = Field(
        description="Unique upstream identifier used to reject duplicates.",
        min_length=1,
        max_length=200,
        examples=["jira-12345"],
    )
    raw_payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Unprocessed payload forwarded to the worker pipeline.",
    )
    board_id: str | None = Field(
        default=None,
        description="Optional board identifier. When omitted, the worker uses the default board.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "external_id": "jira-12345",
                "board_id": "board-id",
                "raw_payload": {
                    "title": "Imported task",
                    "description": "Created from upstream intake",
                    "tags": ["urgent", "api"],
                },
            }
        }
    )
