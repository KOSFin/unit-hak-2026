import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.openapi import OPENAPI_TAGS, install_openapi
from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine
from app.core.logging import setup_logging
from app.realtime.broadcaster import RealtimeRelay
from app.services.seed_service import seed_demo_data

REDOC_JS_URL = "https://cdn.jsdelivr.net/npm/redoc@2/bundles/redoc.standalone.js"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    loop = asyncio.get_running_loop()

    settings = get_settings()
    if settings.seed_demo_data:
        session = SessionLocal()
        try:
            seed_demo_data(session)
        finally:
            session.close()

    settings.uploads_filesystem_path().mkdir(parents=True, exist_ok=True)

    relay = RealtimeRelay(loop)
    relay.start()
    yield
    relay.stop()
    relay.join(timeout=2.0)


def create_app() -> FastAPI:
    settings = get_settings()
    uploads_dir = settings.uploads_filesystem_path()
    uploads_url_path = settings.uploads_url_path()
    uploads_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(settings.log_level)

    app = FastAPI(
        title="FlowBoard API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
        openapi_tags=OPENAPI_TAGS,
    )
    install_openapi(app, settings)

    @app.get("/api/redoc", include_in_schema=False, response_class=HTMLResponse)
    def redoc() -> HTMLResponse:
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - ReDoc",
            redoc_js_url=REDOC_JS_URL,
            with_google_fonts=False,
        )

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

    uploads_mount_path = f"/{uploads_url_path}"
    app.mount(uploads_mount_path, StaticFiles(directory=str(uploads_dir)), name="uploads")
    app_prefixed_mount_path = (
        uploads_mount_path if uploads_mount_path.startswith("/app/") else f"/app{uploads_mount_path}"
    )
    if app_prefixed_mount_path != uploads_mount_path:
        app.mount(app_prefixed_mount_path, StaticFiles(directory=str(uploads_dir)), name="uploads-app")

    return app


app = create_app()
