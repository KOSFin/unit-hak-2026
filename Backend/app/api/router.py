from fastapi import APIRouter

from app.api.automation_rules import router as automation_rules_router
from app.api.boards import router as boards_router
from app.api.columns import router as columns_router
from app.api.health import router as health_router
from app.api.incoming_tasks import router as incoming_tasks_router
from app.api.notifications import router as notifications_router
from app.api.tasks import router as tasks_router
from app.realtime.routes import router as ws_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(automation_rules_router)
api_router.include_router(boards_router)
api_router.include_router(columns_router)
api_router.include_router(incoming_tasks_router)
api_router.include_router(notifications_router)
api_router.include_router(tasks_router)
api_router.include_router(ws_router)
