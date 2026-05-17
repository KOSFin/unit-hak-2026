from pydantic import BaseModel, ConfigDict, Field, field_validator


class GuestProfileBase(BaseModel):
    display_name: str = Field(description="Guest display name shown in the UI.", min_length=1, max_length=60, examples=["Alex"])
    color: str | None = Field(default=None, description="Optional accent color used in presence UI.", examples=["#0F766E"])
    avatar_url: str | None = Field(default=None, description="Optional uploaded avatar URL.", examples=["/uploads/alex.webp"])

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Display name is required")
        return normalized[:60]


class GuestProfileCreate(GuestProfileBase):
    guest_id: str = Field(description="Stable guest identifier stored on the client.", min_length=1, max_length=64)

    @field_validator("guest_id")
    @classmethod
    def normalize_guest_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Guest id is required")
        return normalized[:64]


class GuestProfileUpdate(GuestProfileBase):
    guest_id: str | None = Field(default=None, description="Optional guest identifier for consistency checks.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "guest_id": "guest-42",
                "display_name": "Alex",
                "color": "#0F766E",
                "avatar_url": "/uploads/alex.webp",
            }
        }
    )


class GuestProfileRead(GuestProfileBase):
    guest_id: str = Field(description="Stable guest identifier.")

    model_config = ConfigDict(from_attributes=True)
