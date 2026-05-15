from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ColumnCreate(BaseModel):
    board_id: str
    title: str
    position: int | None = None
    is_default: bool = False


class ColumnUpdate(BaseModel):
    title: str | None = None
    position: int | None = None
    is_default: bool | None = None


class ColumnRead(BaseModel):
    id: str
    board_id: str
    title: str
    position: int
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
