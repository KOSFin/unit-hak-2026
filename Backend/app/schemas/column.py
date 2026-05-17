from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic import Field


class ColumnCreate(BaseModel):
    board_id: str = Field(description="Board identifier that owns the column.", examples=["a3d4a2ba-d4c4-43cc-95ff-fd0b4f6f1ce4"])
    title: str = Field(description="Column display name.", min_length=1, max_length=200, examples=["Review"])
    position: int | None = Field(
        default=None,
        description="Optional 1-based insertion position. When omitted, the column is appended to the end.",
        ge=1,
        examples=[4],
    )
    is_default: bool = Field(
        default=False,
        description="Whether the column should be marked as the board default.",
    )

    model_config = ConfigDict(
        json_schema_extra={"example": {"board_id": "board-id", "title": "Review", "position": 4, "is_default": False}}
    )


class ColumnUpdate(BaseModel):
    title: str | None = Field(default=None, description="Updated column display name.", min_length=1, max_length=200)
    position: int | None = Field(default=None, description="Updated 1-based column position.", ge=1)
    is_default: bool | None = Field(default=None, description="Updated default-column flag.")

    model_config = ConfigDict(json_schema_extra={"example": {"title": "QA", "position": 2}})


class ColumnRead(BaseModel):
    id: str = Field(description="Column identifier.", examples=["f6c3f862-c221-4885-bfe6-dfe53dc13df3"])
    board_id: str = Field(description="Board identifier owning the column.")
    title: str = Field(description="Column display name.", examples=["In Progress"])
    position: int = Field(description="1-based column position within the board.", examples=[2])
    is_default: bool = Field(description="Whether the column is marked as default.")
    created_at: datetime = Field(description="Column creation timestamp.")
    updated_at: datetime = Field(description="Column last update timestamp.")

    model_config = ConfigDict(from_attributes=True)
