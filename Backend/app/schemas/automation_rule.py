from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AutomationRuleCreate(BaseModel):
    name: str
    enabled: bool = True
    trigger_type: str
    condition: dict[str, Any] = Field(default_factory=dict)
    action: dict[str, Any] = Field(default_factory=dict)


class AutomationRuleUpdate(BaseModel):
    name: str | None = None
    enabled: bool | None = None
    trigger_type: str | None = None
    condition: dict[str, Any] | None = None
    action: dict[str, Any] | None = None


class AutomationRuleRead(BaseModel):
    id: str
    name: str
    enabled: bool
    trigger_type: str
    condition: dict[str, Any]
    action: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
