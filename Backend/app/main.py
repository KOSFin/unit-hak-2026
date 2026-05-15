import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.core.logging import setup_logging
from app.realtime.broadcaster import RealtimeRelay
from app.services.seed_service import seed_demo_data


@asynccontextmanager
async def lifespan(_app: FastAPI):
    loop = asyncio.get_running_loop()
    Base.metadata.create_all(bind=engine)

    settings = get_settings()
    if settings.seed_demo_data:
        session = SessionLocal()
        try:
            seed_demo_data(session)
        finally:
            session.close()

    relay = RealtimeRelay(loop)
    relay.start()
    yield
    relay.stop()
    relay.join(timeout=2.0)


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(title="FlowBoard API", version="0.1.0", lifespan=lifespan)

    cors_origins = settings.cors_origins()
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(api_router)
    return app


app = create_app()
