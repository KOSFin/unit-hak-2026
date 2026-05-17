from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.column import ColumnRead


class BoardRead(BaseModel):
    id: str
    public_id: str
    board_url: str | None = None
    name: str
    image_path: str | None = None
    retention_days: int
    expires_after_days: int
    last_activity_at: datetime
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BoardDetail(BoardRead):
    columns: list[ColumnRead] = Field(default_factory=list)


class BoardCreate(BaseModel):
    name: str
    retention_days: int = 3
    image_path: str | None = None


class BoardUpdate(BaseModel):
    name: str | None = None
    image_path: str | None = None


class BoardCreatedResponse(BoardDetail):
    board_url: str
