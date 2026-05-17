from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.engine import Engine

from app.api.openapi import error_response
from app.core.database import get_engine
from app.core.health import readiness_status
from app.schemas.common import HealthResponse, ReadinessResponse

router = APIRouter(tags=["health"])
EngineDep = Annotated[Engine, Depends(get_engine)]


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Liveness probe",
    description="Returns a lightweight liveness signal used by orchestration and monitoring.",
)
def health() -> HealthResponse:
    return {"status": "ok", "service": "backend-api"}


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    description="Checks database and RabbitMQ reachability before the service starts receiving traffic.",
    responses={
        503: error_response(
            "One or more readiness checks failed.",
            {
                "ready": False,
                "checks": {
                    "database": {"ok": True, "error": None},
                    "rabbitmq": {"ok": False, "error": "socket failed"},
                },
            },
        )
    },
)
def ready(engine: EngineDep) -> ReadinessResponse:
    status_info = readiness_status(engine)
    if not status_info["ready"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=status_info,
        )
    return status_info
