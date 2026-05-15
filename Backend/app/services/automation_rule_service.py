from sqlalchemy.orm import Session

from app.models.automation_rule import AutomationRule
from app.repositories.rule_repository import AutomationRuleRepository
from app.schemas.automation_rule import AutomationRuleCreate, AutomationRuleUpdate


class AutomationRuleService:
    def __init__(self, session: Session) -> None:
        self.repo = AutomationRuleRepository(session)

    def list_rules(self) -> list[AutomationRule]:
        return self.repo.list_all()

    def create_rule(self, payload: AutomationRuleCreate) -> AutomationRule:
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
        changes = payload.model_dump(exclude_unset=True)
        if not changes:
            return self.repo.get_by_id(rule_id)
        return self.repo.update(rule_id, **changes)

    def delete_rule(self, rule_id: str) -> bool:
        return self.repo.delete(rule_id)
