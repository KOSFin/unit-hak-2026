from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.column import ColumnRead


class BoardRead(BaseModel):
    id: str
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BoardDetail(BoardRead):
    columns: list[ColumnRead] = Field(default_factory=list)
