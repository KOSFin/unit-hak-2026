from fastapi import APIRouter

from app.api.boards import router as boards_router
from app.api.columns import router as columns_router
from app.api.health import router as health_router
from app.api.tasks import router as tasks_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(boards_router)
api_router.include_router(columns_router)
api_router.include_router(tasks_router)
