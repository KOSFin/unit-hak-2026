from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models.task import Task, TaskPriority
from app.queue.message_types import AUTOMATION_TRIGGERED, TASK_CREATED, TASK_MOVED, TASK_UPDATED
from app.repositories.column_repository import ColumnRepository
from app.repositories.rule_repository import AutomationRuleRepository
from app.repositories.task_repository import TaskRepository
from app.services.automation_rules import ALLOWED_CONDITION_KEYS, ALLOWED_TOAST_TONES, normalize_trigger
from app.services.event_service import EventService
from app.services.notification_service import NotificationService
from app.services.task_service import serialize_task

logger = logging.getLogger(__name__)

TRIGGER_EVENTS = {TASK_CREATED, TASK_UPDATED, TASK_MOVED}


@dataclass
class TaskState:
    column_id: str
    status: str
    priority: TaskPriority
    tags: list[str]
    deadline: datetime | None
    position: int
    desired_position: int | None = None


@dataclass
class RuleEffect:
    rule_id: str
    rule_name: str
    message: str
    toast_tone: str
    changes: dict[str, Any]


class AutomationService:
    def __init__(self, session: Session) -> None:
        self.task_repo = TaskRepository(session)
        self.column_repo = ColumnRepository(session)
        self.rule_repo = AutomationRuleRepository(session)
        self.notification_service = NotificationService(session)
        self.event_service = EventService(session)

    def apply_task_automations(self, task_id: str, source_event: str) -> Task | None:
        task = self.task_repo.get_by_id(task_id)
        if not task:
            return None

        rules = [rule for rule in self.rule_repo.list_all(task.board_id) if rule.enabled]
        if not rules:
            return task

        columns = self.column_repo.list_by_board(task.board_id)
        columns_by_id = {column.id: column for column in columns}
        columns_by_title = {column.title: column for column in columns}

        state = TaskState(
            column_id=task.column_id,
            status=task.status,
            priority=task.priority,
            tags=list(task.tags or []),
            deadline=task.deadline,
            position=task.position,
        )

        triggered: list[RuleEffect] = []
        for rule in rules:
            if not self._match_trigger(rule.trigger_type, source_event):
                continue
            condition = rule.condition if isinstance(rule.condition, dict) else {}
            if not self._match_conditions(condition, state, columns_by_id, columns_by_title):
                continue
            effect = self._apply_actions(rule, state, columns_by_id, columns_by_title)
            if effect:
                triggered.append(effect)

        if not triggered:
            return task

        updated = task
        if self._state_changed(task, state):
            updated = self._apply_state(task, state)
            if not updated:
                return task

            moved = updated.column_id != task.column_id or updated.position != task.position
            event_type = TASK_MOVED if moved else TASK_UPDATED
            self.event_service.record_event(
                event_type,
                "task",
                updated.id,
                {
                    "task": serialize_task(updated),
                    "automation": {"rules": [effect.rule_id for effect in triggered]},
                },
                board_id=updated.board_id,
                source="WORKER",
            )

        for effect in triggered:
            if effect.message:
                self.notification_service.create_notification(
                    title=effect.rule_name,
                    message=effect.message,
                    type="automation",
                    task_id=updated.id,
                    board_id=updated.board_id,
                )
                self.event_service.record_event(
                    AUTOMATION_TRIGGERED,
                    "automation_rule",
                    updated.id,
                    {
                    "board_id": updated.board_id,
                    "task": serialize_task(updated),
                    "rule": {
                        "id": effect.rule_id,
                        "name": effect.rule_name,
                    },
                    "changes": effect.changes,
                    "message": effect.message,
                        "toast": {
                            "message": effect.message,
                            "tone": effect.toast_tone,
                        },
                    },
                    board_id=updated.board_id,
                    source="WORKER",
                )

        return updated

    def _match_trigger(self, trigger_type: str, source_event: str) -> bool:
        normalized = normalize_trigger(trigger_type)
        if normalized == "TASK_ANY":
            return source_event in TRIGGER_EVENTS
        return normalized == source_event

    def _match_conditions(
        self,
        condition: dict[str, Any],
        state: TaskState,
        columns_by_id: dict[str, Any],
        columns_by_title: dict[str, Any],
    ) -> bool:
        tags = set(state.tags)
        column_title = columns_by_id.get(state.column_id).title if state.column_id in columns_by_id else None

        for key, value in condition.items():
            if key not in ALLOWED_CONDITION_KEYS:
                return False
            if key == "tag" and (not isinstance(value, str) or value not in tags):
                return False
            if key == "not_tag" and (not isinstance(value, str) or value in tags):
                return False
            if key == "tags_any":
                if not isinstance(value, list) or not any(tag in tags for tag in value):
                    return False
            if key == "tags_all":
                if not isinstance(value, list) or not all(tag in tags for tag in value):
                    return False
            if key == "priority":
                expected = self._parse_priority(value)
                if not expected or state.priority != expected:
                    return False
            if key == "not_priority":
                expected = self._parse_priority(value)
                if expected and state.priority == expected:
                    return False
            if key == "column":
                if not isinstance(value, str) or column_title != value:
                    return False
            if key == "not_column":
                if not isinstance(value, str) or column_title == value:
                    return False
            if key == "column_id" and (not isinstance(value, str) or state.column_id != value):
                return False
            if key == "not_column_id" and (not isinstance(value, str) or state.column_id == value):
                return False
            if key == "status" and (not isinstance(value, str) or state.status != value):
                return False
            if key == "not_status" and (not isinstance(value, str) or state.status == value):
                return False
            if key in {"deadline_hours_lt", "hours_lt"}:
                if not isinstance(value, (int, float)):
                    return False
                deadline = state.deadline
                if deadline and deadline.tzinfo is None:
                    deadline = deadline.replace(tzinfo=UTC)
                if not deadline:
                    return False
                if deadline > datetime.now(UTC) + timedelta(hours=float(value)):
                    return False
            if key == "deadline_set":
                if not isinstance(value, bool):
                    return False
                if value and not state.deadline:
                    return False
                if not value and state.deadline:
                    return False

        return True

    def _apply_actions(
        self,
        rule,
        state: TaskState,
        columns_by_id: dict[str, Any],
        columns_by_title: dict[str, Any],
    ) -> RuleEffect | None:
        action = rule.action if isinstance(rule.action, dict) else {}
        changes: dict[str, Any] = {}
        tags = list(state.tags)
        tag_set = set(tags)

        if "set_priority" in action:
            new_priority = self._parse_priority(action.get("set_priority"))
            if new_priority and new_priority != state.priority:
                changes["priority"] = {"from": state.priority.value, "to": new_priority.value}
                state.priority = new_priority

        add_tags = []
        if "add_tag" in action and isinstance(action.get("add_tag"), str):
            add_tags.append(action.get("add_tag"))
        if "add_tags" in action and isinstance(action.get("add_tags"), list):
            add_tags.extend([tag for tag in action.get("add_tags") if isinstance(tag, str)])

        added: list[str] = []
        for tag in add_tags:
            if tag not in tag_set:
                tags.append(tag)
                tag_set.add(tag)
                added.append(tag)
        if added:
            changes["tags_added"] = added

        remove_tags = []
        if "remove_tag" in action and isinstance(action.get("remove_tag"), str):
            remove_tags.append(action.get("remove_tag"))
        if "remove_tags" in action and isinstance(action.get("remove_tags"), list):
            remove_tags.extend([tag for tag in action.get("remove_tags") if isinstance(tag, str)])

        removed = []
        if remove_tags:
            for tag in remove_tags:
                if tag in tag_set:
                    tag_set.remove(tag)
                    removed.append(tag)
            if removed:
                tags = [tag for tag in tags if tag not in set(removed)]
                changes["tags_removed"] = removed

        if added or removed:
            state.tags = tags

        target_column = None
        column_changed = False
        if isinstance(action.get("move_to_id"), str):
            target_column = columns_by_id.get(action.get("move_to_id"))
        if target_column is None and isinstance(action.get("move_to"), str):
            target_column = columns_by_title.get(action.get("move_to"))

        if target_column and state.column_id != target_column.id:
            changes["moved_to"] = target_column.title
            state.column_id = target_column.id
            state.status = target_column.title
            column_changed = True
            if "position" not in action:
                state.desired_position = None
        elif target_column is None and ("move_to" in action or "move_to_id" in action):
            logger.warning("Automation rule %s references unknown column", rule.id)

        if isinstance(action.get("position"), int) and action.get("position") > 0:
            desired_position = int(action.get("position"))
            if column_changed or desired_position != state.position:
                state.desired_position = desired_position
                changes["position"] = state.desired_position

        if not changes:
            notify = action.get("notify")
            if not isinstance(notify, str) or not notify.strip():
                return None
            tone = action.get("toast_tone") if action.get("toast_tone") in ALLOWED_TOAST_TONES else "neutral"
            return RuleEffect(
                rule_id=rule.id,
                rule_name=rule.name,
                message=notify.strip(),
                toast_tone=tone,
                changes={},
            )

        message = self._resolve_message(rule.name, action, changes)
        tone = action.get("toast_tone") if action.get("toast_tone") in ALLOWED_TOAST_TONES else "neutral"

        return RuleEffect(
            rule_id=rule.id,
            rule_name=rule.name,
            message=message,
            toast_tone=tone,
            changes=changes,
        )

    def _resolve_message(self, rule_name: str, action: dict[str, Any], changes: dict[str, Any]) -> str:
        notify = action.get("notify")
        if isinstance(notify, str) and notify.strip():
            return notify.strip()

        parts: list[str] = []
        if "moved_to" in changes:
            parts.append(f"moved to {changes['moved_to']}")
        if "priority" in changes:
            parts.append(f"priority set to {changes['priority']['to']}")
        if "tags_added" in changes:
            parts.append("tags added: " + ", ".join(changes["tags_added"]))
        if "tags_removed" in changes:
            parts.append("tags removed: " + ", ".join(changes["tags_removed"]))
        if "position" in changes and "moved_to" not in changes:
            parts.append(f"position set to {changes['position']}")

        if parts:
            return f"{rule_name}: " + "; ".join(parts)
        return f"{rule_name}: rule applied"

    def _apply_state(self, task: Task, state: TaskState) -> Task | None:
        changes: dict[str, Any] = {}
        if task.priority != state.priority:
            changes["priority"] = state.priority
        if list(task.tags or []) != state.tags:
            changes["tags"] = state.tags

        move_requested = task.column_id != state.column_id or (
            state.desired_position is not None and state.desired_position != task.position
        )
        if move_requested:
            return self._apply_move_with_changes(task, state, changes)

        if not changes:
            return task

        changes["version"] = task.version + 1
        return self.task_repo.update(task.id, **changes)

    def _state_changed(self, task: Task, state: TaskState) -> bool:
        if task.column_id != state.column_id:
            return True
        if task.priority != state.priority:
            return True
        if list(task.tags or []) != state.tags:
            return True
        if state.desired_position is not None and state.desired_position != task.position:
            return True
        return False

    def _apply_move_with_changes(self, task: Task, state: TaskState, changes: dict[str, Any]) -> Task | None:
        target_column_id = state.column_id
        target_column = self.column_repo.get_by_id(target_column_id)
        if not target_column:
            logger.warning("Automation attempted to move task to missing column %s", target_column_id)
            return task

        source_column_id = task.column_id
        target_count = self.task_repo.count_by_column(target_column_id)
        if source_column_id == target_column_id:
            max_pos = target_count
        else:
            max_pos = target_count + 1

        desired_position = state.desired_position or max_pos
        desired_position = max(1, min(desired_position, max_pos))

        updates = dict(changes)
        updates.update(
            {
                "column_id": target_column_id,
                "status": target_column.title,
                "position": desired_position,
                "version": task.version + 1,
            }
        )

        updated = self.task_repo.update(task.id, **updates)
        if not updated:
            return None

        if source_column_id != target_column_id:
            self.task_repo.reorder_positions(source_column_id)

        target_tasks = self.task_repo.list_by_column(target_column_id)
        others = [t for t in target_tasks if t.id != task.id]
        moving = next((t for t in target_tasks if t.id == task.id), None)
        if moving:
            insert_idx = min(desired_position - 1, len(others))
            ordered = others[:insert_idx] + [moving] + others[insert_idx:]
            for idx, current in enumerate(ordered, start=1):
                if current.position != idx:
                    current.position = idx
            self.task_repo.session.commit()

        return self.task_repo.get_by_id(task.id) or updated

    def _parse_priority(self, value: Any) -> TaskPriority | None:
        if isinstance(value, TaskPriority):
            return value
        if isinstance(value, str):
            try:
                return TaskPriority(value)
            except ValueError:
                try:
                    return TaskPriority[value]
                except KeyError:
                    return None
        return None
