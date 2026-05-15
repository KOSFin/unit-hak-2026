from fastapi import FastAPI

from app.core.config import get_settings
from app.main import create_app


def test_create_app_returns_fastapi():
    app = create_app()
    assert isinstance(app, FastAPI)
    paths = {route.path for route in app.routes}
    assert "/health" in paths
    assert "/ready" in paths


def test_create_app_adds_cors(monkeypatch):
    monkeypatch.setenv("BACKEND_CORS_ORIGINS", "https://flowboard.example.com")
    get_settings.cache_clear()
    app = create_app()
    middleware_names = {middleware.cls.__name__ for middleware in app.user_middleware}
    assert "CORSMiddleware" in middleware_names
