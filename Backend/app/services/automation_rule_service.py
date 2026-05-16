from sqlalchemy.orm import Session

from app.models.automation_rule import AutomationRule
from app.repositories.rule_repository import AutomationRuleRepository
from app.schemas.automation_rule import AutomationRuleCreate, AutomationRuleUpdate
from app.services.automation_rules import validate_rule_payload


class AutomationRuleService:
    def __init__(self, session: Session) -> None:
        self.repo = AutomationRuleRepository(session)

    def list_rules(self) -> list[AutomationRule]:
        return self.repo.list_all()

    def create_rule(self, payload: AutomationRuleCreate) -> AutomationRule:
        errors = validate_rule_payload(payload.trigger_type, payload.condition, payload.action)
        if errors:
            raise ValueError("; ".join(errors))
        return self.repo.create(
            name=payload.name,
            enabled=payload.enabled,
            trigger_type=payload.trigger_type,
            condition=payload.condition,
            action=payload.action,
        )

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
        return self.repo.update(rule_id, **changes)

    def delete_rule(self, rule_id: str) -> bool:
        return self.repo.delete(rule_id)
