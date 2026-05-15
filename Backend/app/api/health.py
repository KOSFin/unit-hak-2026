from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.engine import Engine

from app.core.database import get_engine
from app.core.health import readiness_status

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "service": "backend-api"}


@router.get("/ready")
def ready(engine: Engine = Depends(get_engine)):
    status_info = readiness_status(engine)
    if not status_info["ready"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=status_info,
        )
    return status_info
