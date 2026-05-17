from sqlalchemy.orm import Session

from app.models.automation_rule import AutomationRule
from app.queue.message_types import (
    AUTOMATION_RULE_CREATED,
    AUTOMATION_RULE_DELETED,
    AUTOMATION_RULE_UPDATED,
)
from app.repositories.board_repository import BoardRepository
from app.repositories.rule_repository import AutomationRuleRepository
from app.schemas.automation_rule import AutomationRuleCreate, AutomationRuleUpdate
from app.services.automation_rules import validate_rule_payload
from app.services.event_service import EventService


class AutomationRuleService:
    def __init__(self, session: Session) -> None:
        self.repo = AutomationRuleRepository(session)
        self.board_repo = BoardRepository(session)
        self.event_service = EventService(session)

    def list_rules(self, board_id: str | None = None) -> list[AutomationRule]:
        return self.repo.list_all(board_id=board_id)

    def create_rule(self, payload: AutomationRuleCreate) -> AutomationRule:
        errors = validate_rule_payload(payload.trigger_type, payload.condition, payload.action)
        if errors:
            raise ValueError("; ".join(errors))
        rule = self.repo.create(
            name=payload.name,
            enabled=payload.enabled,
            trigger_type=payload.trigger_type,
            condition=payload.condition,
            action=payload.action,
            board_id=getattr(payload, "board_id", None),
        )
        if rule.board_id:
            self.board_repo.update_last_activity(rule.board_id)
        self.event_service.record_event(
            AUTOMATION_RULE_CREATED,
            "automation_rule",
            rule.id,
            {
                "rule": {
                    "id": rule.id,
                    "board_id": rule.board_id,
                    "name": rule.name,
                    "enabled": rule.enabled,
                    "trigger_type": rule.trigger_type,
                    "condition": rule.condition,
                    "action": rule.action,
                }
            },
            board_id=rule.board_id,
            source="API",
        )
        return rule

    def update_rule(
        self,
        rule_id: str,
        payload: AutomationRuleUpdate,
    ) -> AutomationRule | None:
        existing = self.repo.get_by_id(rule_id)
        if not existing:
            return None
        changes = payload.model_dump(exclude_unset=True)
        if not changes:
            return existing
        trigger_type = changes.get("trigger_type", existing.trigger_type)
        condition = changes.get("condition", existing.condition)
        action = changes.get("action", existing.action)
        errors = validate_rule_payload(trigger_type, condition, action)
        if errors:
            raise ValueError("; ".join(errors))
        updated = self.repo.update(rule_id, **changes)
        if not updated:
            return None
        if updated.board_id:
            self.board_repo.update_last_activity(updated.board_id)
        self.event_service.record_event(
            AUTOMATION_RULE_UPDATED,
            "automation_rule",
            updated.id,
            {
                "rule": {
                    "id": updated.id,
                    "board_id": updated.board_id,
                    "name": updated.name,
                    "enabled": updated.enabled,
                    "trigger_type": updated.trigger_type,
                    "condition": updated.condition,
                    "action": updated.action,
                }
            },
            board_id=updated.board_id,
            source="API",
        )
        return updated

    def delete_rule(self, rule_id: str) -> bool:
        existing = self.repo.get_by_id(rule_id)
        if not existing:
            return False
        deleted = self.repo.delete(rule_id)
        if deleted:
            if existing.board_id:
                self.board_repo.update_last_activity(existing.board_id)
            self.event_service.record_event(
                AUTOMATION_RULE_DELETED,
                "automation_rule",
                rule_id,
                {
                    "rule": {
                        "id": existing.id,
                        "board_id": existing.board_id,
                        "name": existing.name,
                        "enabled": existing.enabled,
                        "trigger_type": existing.trigger_type,
                    }
                },
                board_id=existing.board_id,
                source="API",
            )
        return deleted
