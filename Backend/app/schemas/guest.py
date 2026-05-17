from pydantic import BaseModel, ConfigDict, field_validator


class GuestProfileBase(BaseModel):
    display_name: str
    color: str | None = None
    avatar_url: str | None = None

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Display name is required")
        return normalized[:60]


class GuestProfileCreate(GuestProfileBase):
    guest_id: str

    @field_validator("guest_id")
    @classmethod
    def normalize_guest_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Guest id is required")
        return normalized[:64]


class GuestProfileUpdate(GuestProfileBase):
    guest_id: str | None = None


class GuestProfileRead(GuestProfileBase):
    guest_id: str

    model_config = ConfigDict(from_attributes=True)
