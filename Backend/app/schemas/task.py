from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.task import TaskPriority


class TaskCreate(BaseModel):
    board_id: str = Field(description="Board identifier containing the task.")
    column_id: str = Field(description="Target column identifier for the new task.")
    title: str = Field(description="Task title.", min_length=1, max_length=200, examples=["Prepare release notes"])
    description: str | None = Field(default=None, description="Optional task description.")
    status: str | None = Field(
        default=None,
        description="Task status label. Defaults to the target column title when omitted.",
        examples=["To Do"],
    )
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority level.")
    tags: list[str] = Field(default_factory=list, description="Task tags used for UI grouping and automation.")
    deadline: datetime | None = Field(default=None, description="Optional deadline timestamp in ISO 8601 format.")
    position: int | None = Field(
        default=None,
        description="Optional 1-based position inside the column. Defaults to append.",
        ge=1,
    )
    correlation_id: str | None = Field(
        default=None,
        description="Optional correlation id used to group related activity events.",
        examples=["corr-release-001"],
    )
    guest_id: str | None = Field(
        default=None,
        description="Guest identifier of the actor creating the task.",
        examples=["guest-42"],
    )
    actor: dict[str, str | None] | None = Field(
        default=None,
        description="Actor metadata included in emitted activity events.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "board_id": "board-id",
                "column_id": "column-id",
                "title": "Prepare release notes",
                "description": "Draft the customer-facing change summary.",
                "status": "To Do",
                "priority": "HIGH",
                "tags": ["release", "docs"],
                "correlation_id": "corr-release-001",
                "guest_id": "guest-42",
                "actor": {
                    "guest_id": "guest-42",
                    "display_name": "Alex",
                    "color": "#0F766E",
                    "avatar_url": "/uploads/alex.webp",
                },
            }
        }
    )


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, description="Updated task title.", min_length=1, max_length=200)
    description: str | None = Field(default=None, description="Updated task description.")
    status: str | None = Field(default=None, description="Updated task status label.")
    priority: TaskPriority | None = Field(default=None, description="Updated task priority.")
    tags: list[str] | None = Field(default=None, description="Updated task tag list.")
    deadline: datetime | None = Field(default=None, description="Updated deadline timestamp.")
    version: int = Field(description="Current persisted task version required for optimistic locking.", ge=1)
    correlation_id: str | None = Field(default=None, description="Optional activity correlation id.")
    guest_id: str | None = Field(default=None, description="Guest identifier of the actor performing the update.")
    actor: dict[str, str | None] | None = Field(default=None, description="Actor metadata forwarded to activity events.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Prepare final release notes",
                "priority": "CRITICAL",
                "version": 3,
                "guest_id": "guest-42",
            }
        }
    )


class TaskMove(BaseModel):
    column_id: str = Field(description="Destination column identifier.")
    status: str | None = Field(
        default=None,
        description="Optional destination status label. Defaults to the destination column title.",
    )
    position: int | None = Field(
        default=None,
        description="Desired 1-based destination position. Defaults to append.",
        ge=1,
    )
    version: int = Field(description="Current persisted task version required for optimistic locking.", ge=1)
    correlation_id: str | None = Field(default=None, description="Optional activity correlation id.")
    guest_id: str | None = Field(default=None, description="Guest identifier of the actor performing the move.")
    actor: dict[str, str | None] | None = Field(default=None, description="Actor metadata forwarded to activity events.")

    model_config = ConfigDict(
        json_schema_extra={"example": {"column_id": "column-id", "position": 1, "version": 3}}
    )


class TaskRead(BaseModel):
    id: str = Field(description="Task identifier.", examples=["af179e6c-80b5-4d0d-bd6d-9eb2d16d59db"])
    board_id: str = Field(description="Board identifier containing the task.")
    column_id: str = Field(description="Column identifier containing the task.")
    title: str = Field(description="Task title.")
    description: str | None = Field(default=None, description="Task description.")
    status: str = Field(description="Task status label.", examples=["In Progress"])
    priority: TaskPriority = Field(description="Task priority level.")
    tags: list[str] = Field(description="Task tags.")
    deadline: datetime | None = Field(default=None, description="Optional deadline timestamp.")
    position: int = Field(description="1-based position inside the column.", examples=[1])
    version: int = Field(description="Optimistic locking version.", examples=[3])
    created_at: datetime = Field(description="Task creation timestamp.")
    updated_at: datetime = Field(description="Task last update timestamp.")
    correlation_id: str | None = Field(default=None, description="Activity correlation id.")
    guest_id: str | None = Field(default=None, description="Guest identifier associated with the latest mutation.")

    model_config = ConfigDict(from_attributes=True)
