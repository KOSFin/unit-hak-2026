from __future__ import annotations

from typing import Any

ALLOWED_TRIGGERS = {"TASK_CREATED", "TASK_UPDATED", "TASK_MOVED", "TASK_ANY"}
TRIGGER_ALIASES = {
    "task.tag": "TASK_ANY",
    "task.deadline": "TASK_ANY",
    "task.moved": "TASK_MOVED",
}

ALLOWED_CONDITION_KEYS = {
    "tag",
    "not_tag",
    "tags_any",
    "tags_all",
    "priority",
    "not_priority",
    "column",
    "column_id",
    "not_column",
    "not_column_id",
    "status",
    "not_status",
    "deadline_hours_lt",
    "hours_lt",
    "deadline_set",
}

ALLOWED_ACTION_KEYS = {
    "set_priority",
    "add_tag",
    "add_tags",
    "remove_tag",
    "remove_tags",
    "move_to",
    "move_to_id",
    "position",
    "notify",
    "toast_tone",
}

ALLOWED_TOAST_TONES = {"neutral", "success", "danger"}


def normalize_trigger(trigger_type: str) -> str:
    return TRIGGER_ALIASES.get(trigger_type, trigger_type)


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def validate_rule_payload(trigger_type: str, condition: dict[str, Any], action: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    normalized = normalize_trigger(trigger_type)
    if normalized not in ALLOWED_TRIGGERS:
        errors.append("Unsupported trigger_type")

    if not isinstance(condition, dict):
        errors.append("Condition must be an object")
    else:
        for key, value in condition.items():
            if key not in ALLOWED_CONDITION_KEYS:
                errors.append(f"Unsupported condition key: {key}")
                continue
            if key in {"tag", "not_tag", "priority", "not_priority", "column", "column_id", "not_column", "not_column_id", "status", "not_status"}:
                if not isinstance(value, str):
                    errors.append(f"Condition '{key}' must be a string")
            if key in {"tags_any", "tags_all"} and not _is_string_list(value):
                errors.append(f"Condition '{key}' must be a list of strings")
            if key in {"deadline_hours_lt", "hours_lt"} and not isinstance(value, (int, float)):
                errors.append("Condition 'deadline_hours_lt' must be a number")
            if key == "deadline_set" and not isinstance(value, bool):
                errors.append("Condition 'deadline_set' must be a boolean")

    if not isinstance(action, dict):
        errors.append("Action must be an object")
    else:
        for key, value in action.items():
            if key not in ALLOWED_ACTION_KEYS:
                errors.append(f"Unsupported action key: {key}")
                continue
            if key in {"set_priority", "move_to", "move_to_id", "notify", "toast_tone"}:
                if not isinstance(value, str):
                    errors.append(f"Action '{key}' must be a string")
            if key in {"add_tag", "remove_tag"}:
                if not isinstance(value, str):
                    errors.append(f"Action '{key}' must be a string")
            if key in {"add_tags", "remove_tags"} and not _is_string_list(value):
                errors.append(f"Action '{key}' must be a list of strings")
            if key == "position":
                if not isinstance(value, int) or value < 1:
                    errors.append("Action 'position' must be a positive integer")
            if key == "toast_tone" and isinstance(value, str) and value not in ALLOWED_TOAST_TONES:
                errors.append("Action 'toast_tone' must be one of: neutral, success, danger")

    return errors
