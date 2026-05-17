from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AutomationRuleCreate(BaseModel):
    board_id: str | None = Field(
        default=None,
        description="Optional board scope. When omitted, the rule is global.",
    )
    name: str = Field(description="Human-readable rule name.", min_length=1, max_length=200, examples=["Urgent priority"])
    enabled: bool = Field(default=True, description="Whether the rule is active.")
    trigger_type: str = Field(
        description="Event type that activates the rule.",
        examples=["TASK_CREATED"],
    )
    condition: dict[str, Any] = Field(default_factory=dict, description="Trigger condition payload.")
    action: dict[str, Any] = Field(default_factory=dict, description="Action payload applied by the worker.")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "board_id": "board-id",
                "name": "Urgent priority",
                "enabled": True,
                "trigger_type": "TASK_CREATED",
                "condition": {"tag": "urgent"},
                "action": {"set_priority": "HIGH"},
            }
        }
    )


class AutomationRuleUpdate(BaseModel):
    name: str | None = Field(default=None, description="Updated rule name.", min_length=1, max_length=200)
    enabled: bool | None = Field(default=None, description="Updated enabled flag.")
    trigger_type: str | None = Field(default=None, description="Updated trigger event type.")
    condition: dict[str, Any] | None = Field(default=None, description="Updated rule condition payload.")
    action: dict[str, Any] | None = Field(default=None, description="Updated rule action payload.")

    model_config = ConfigDict(json_schema_extra={"example": {"enabled": False}})


class AutomationRuleRead(BaseModel):
    id: str = Field(description="Automation rule identifier.")
    board_id: str | None = Field(default=None, description="Scoped board identifier, if present.")
    name: str = Field(description="Rule name.")
    enabled: bool = Field(description="Whether the rule is active.")
    trigger_type: str = Field(description="Trigger event type.")
    condition: dict[str, Any] = Field(description="Rule condition payload.")
    action: dict[str, Any] = Field(description="Rule action payload.")
    created_at: datetime = Field(description="Rule creation timestamp.")
    updated_at: datetime = Field(description="Rule last update timestamp.")

    model_config = ConfigDict(from_attributes=True)
