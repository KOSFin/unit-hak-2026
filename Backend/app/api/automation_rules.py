from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.schemas.automation_rule import (
    AutomationRuleCreate,
    AutomationRuleRead,
    AutomationRuleUpdate,
)
from app.services.automation_rule_service import AutomationRuleService

router = APIRouter(prefix="/api/automation-rules", tags=["automation-rules"])
SessionDep = Annotated[Session, Depends(get_session)]


@router.get("", response_model=list[AutomationRuleRead])
def list_rules(session: SessionDep, board_id: str | None = None) -> list[AutomationRuleRead]:
    service = AutomationRuleService(session)
    return [AutomationRuleRead.model_validate(rule) for rule in service.list_rules(board_id=board_id)]


@router.post("", response_model=AutomationRuleRead, status_code=status.HTTP_201_CREATED)
def create_rule(payload: AutomationRuleCreate, session: SessionDep) -> AutomationRuleRead:
    service = AutomationRuleService(session)
    try:
        rule = service.create_rule(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return AutomationRuleRead.model_validate(rule)


@router.patch("/{rule_id}", response_model=AutomationRuleRead)
def update_rule(
    rule_id: str,
    payload: AutomationRuleUpdate,
    session: SessionDep,
) -> AutomationRuleRead:
    service = AutomationRuleService(session)
    try:
        rule = service.update_rule(rule_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return AutomationRuleRead.model_validate(rule)


@router.delete("/{rule_id}")
def delete_rule(rule_id: str, session: SessionDep) -> dict[str, str]:
    service = AutomationRuleService(session)
    if not service.delete_rule(rule_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return {"status": "deleted"}
