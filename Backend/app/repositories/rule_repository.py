from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.automation_rule import AutomationRule


class AutomationRuleRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        name: str,
        enabled: bool,
        trigger_type: str,
        condition: dict,
        action: dict,
        board_id: str | None = None,
    ) -> AutomationRule:
        rule = AutomationRule(
            name=name,
            enabled=enabled,
            trigger_type=trigger_type,
            condition=condition,
            action=action,
            board_id=board_id,
        )
        self.session.add(rule)
        self.session.commit()
        self.session.refresh(rule)
        return rule

    def get_by_id(self, rule_id: str) -> AutomationRule | None:
        return self.session.get(AutomationRule, rule_id)

    def list_all(self, board_id: str | None = None) -> list[AutomationRule]:
        stmt = select(AutomationRule)
        if board_id:
            stmt = stmt.where(AutomationRule.board_id == board_id)
        stmt = stmt.order_by(AutomationRule.created_at)
        return list(self.session.execute(stmt).scalars().all())

    def update(self, rule_id: str, **changes) -> AutomationRule | None:
        rule = self.get_by_id(rule_id)
        if not rule:
            return None
        for field, value in changes.items():
            setattr(rule, field, value)
        self.session.commit()
        self.session.refresh(rule)
        return rule

    def delete(self, rule_id: str) -> bool:
        rule = self.get_by_id(rule_id)
        if not rule:
            return False
        self.session.delete(rule)
        self.session.commit()
        return True
