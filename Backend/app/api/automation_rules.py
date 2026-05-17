from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.api.openapi import error_response
from app.core.database import get_session
from app.schemas.common import OperationStatusResponse
from app.schemas.automation_rule import (
    AutomationRuleCreate,
    AutomationRuleRead,
    AutomationRuleUpdate,
)
from app.services.automation_rule_service import AutomationRuleService

router = APIRouter(prefix="/api/automation-rules", tags=["automation-rules"])
SessionDep = Annotated[Session, Depends(get_session)]


@router.get(
    "",
    response_model=list[AutomationRuleRead],
    summary="List automation rules",
    description="Returns automation rules optionally filtered by board identifier.",
)
def list_rules(
    session: SessionDep,
    board_id: str | None = Query(default=None, description="Optional board identifier used to filter rules."),
) -> list[AutomationRuleRead]:
    service = AutomationRuleService(session)
    return [AutomationRuleRead.model_validate(rule) for rule in service.list_rules(board_id=board_id)]


@router.post(
    "",
    response_model=AutomationRuleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create automation rule",
    description="Creates a worker-evaluated automation rule for task-related events.",
    responses={422: error_response("Rule validation failed.", "Unsupported trigger_type or invalid rule payload")},
)
def create_rule(payload: AutomationRuleCreate, session: SessionDep) -> AutomationRuleRead:
    service = AutomationRuleService(session)
    try:
        rule = service.create_rule(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return AutomationRuleRead.model_validate(rule)


@router.patch(
    "/{rule_id}",
    response_model=AutomationRuleRead,
    summary="Update automation rule",
    description="Partially updates an automation rule and revalidates the resulting payload.",
    responses={
        404: error_response("Automation rule was not found.", "Rule not found"),
        422: error_response("Rule validation failed.", "Unsupported trigger_type or invalid rule payload"),
    },
)
def update_rule(
    session: SessionDep,
    rule_id: str = Path(description="Automation rule identifier.", examples=["rule-123"]),
    payload: AutomationRuleUpdate = ...,
) -> AutomationRuleRead:
    service = AutomationRuleService(session)
    try:
        rule = service.update_rule(rule_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return AutomationRuleRead.model_validate(rule)


@router.delete(
    "/{rule_id}",
    response_model=OperationStatusResponse,
    summary="Delete automation rule",
    description="Deletes an automation rule by identifier.",
    responses={404: error_response("Automation rule was not found.", "Rule not found")},
)
def delete_rule(
    session: SessionDep,
    rule_id: str = Path(description="Automation rule identifier.", examples=["rule-123"]),
) -> OperationStatusResponse:
    service = AutomationRuleService(session)
    if not service.delete_rule(rule_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return {"status": "deleted"}
