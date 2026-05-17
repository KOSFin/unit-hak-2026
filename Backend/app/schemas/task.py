from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.task import TaskPriority


class TaskCreate(BaseModel):
    board_id: str
    column_id: str
    title: str
    description: str | None = None
    status: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    tags: list[str] = Field(default_factory=list)
    deadline: datetime | None = None
    position: int | None = None
    correlation_id: str | None = None
    guest_id: str | None = None
    actor: dict[str, str | None] | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: TaskPriority | None = None
    tags: list[str] | None = None
    deadline: datetime | None = None
    version: int
    correlation_id: str | None = None
    guest_id: str | None = None
    actor: dict[str, str | None] | None = None


class TaskMove(BaseModel):
    column_id: str
    status: str | None = None
    position: int | None = None
    version: int
    correlation_id: str | None = None
    guest_id: str | None = None
    actor: dict[str, str | None] | None = None


class TaskRead(BaseModel):
    id: str
    board_id: str
    column_id: str
    title: str
    description: str | None
    status: str
    priority: TaskPriority
    tags: list[str]
    deadline: datetime | None
    position: int
    version: int
    created_at: datetime
    updated_at: datetime
    correlation_id: str | None = None
    guest_id: str | None = None

    model_config = ConfigDict(from_attributes=True)
