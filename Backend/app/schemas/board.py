from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.column import ColumnRead


class BoardRead(BaseModel):
    id: str = Field(description="Internal board identifier.", examples=["a3d4a2ba-d4c4-43cc-95ff-fd0b4f6f1ce4"])
    public_id: str = Field(
        description="Public board identifier used in shareable URLs.",
        examples=["4hY6kK4mQ1zvS8L2N0Ab"],
    )
    board_url: str | None = Field(
        default=None,
        description="Resolved public URL to open the board in the client application.",
        examples=["/board/4hY6kK4mQ1zvS8L2N0Ab"],
    )
    name: str = Field(description="Board display name.", examples=["Product Launch"])
    image_path: str | None = Field(
        default=None,
        description="Optional uploaded board cover image path.",
        examples=["/uploads/board-cover.webp"],
    )
    owner_guest_id: str | None = Field(
        default=None,
        description="Guest identifier of the board owner when the board was created by a guest.",
        examples=["guest-42"],
    )
    allow_guest_admin: bool = Field(
        default=False,
        description="Whether guest collaborators may perform admin-level board actions.",
    )
    retention_days: int = Field(description="Configured retention period in days.", examples=[3])
    expires_after_days: int = Field(description="Calculated expiration period in days.", examples=[3])
    last_activity_at: datetime = Field(description="Timestamp of the latest board activity.")
    archived_at: datetime | None = Field(default=None, description="Archive timestamp when the board is archived.")
    created_at: datetime = Field(description="Board creation timestamp.")
    updated_at: datetime = Field(description="Board last update timestamp.")

    model_config = ConfigDict(from_attributes=True)


class BoardDetail(BoardRead):
    columns: list[ColumnRead] = Field(
        default_factory=list,
        description="Columns currently configured for the board in display order.",
    )


class BoardCreate(BaseModel):
    name: str = Field(description="Board name visible in the UI.", min_length=1, max_length=200, examples=["Design QA"])
    retention_days: int = Field(
        default=3,
        description="Requested retention period. Guest boards currently support only 3 days.",
        ge=1,
        examples=[3],
    )
    image_path: str | None = Field(
        default=None,
        description="Optional uploaded cover image path returned by `/api/uploads`.",
        examples=["/uploads/board-cover.webp"],
    )
    creator_guest_id: str | None = Field(
        default=None,
        description="Guest identifier used to associate board ownership.",
        examples=["guest-42"],
    )
    allow_guest_admin: bool = Field(
        default=False,
        description="Whether guest collaborators may update or delete the board.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Design QA",
                "retention_days": 3,
                "image_path": "/uploads/board-cover.webp",
                "creator_guest_id": "guest-42",
                "allow_guest_admin": True,
            }
        }
    )


class BoardUpdate(BaseModel):
    name: str | None = Field(default=None, description="Updated board display name.", min_length=1, max_length=200)
    image_path: str | None = Field(
        default=None,
        description="New uploaded cover image path. Omit the field to preserve the current image.",
    )
    allow_guest_admin: bool | None = Field(
        default=None,
        description="Updated permission flag for guest administrative actions.",
    )

    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "Design QA v2", "allow_guest_admin": True}}
    )


class BoardCreatedResponse(BoardDetail):
    board_url: str = Field(description="Resolved board URL returned immediately after creation.")
