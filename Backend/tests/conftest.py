import httpx
import pytest
from sqlalchemy import create_engine

from app.core.config import get_settings
from app.main import create_app


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture()
def app():
    return create_app()


@pytest.fixture()
def client(app):
    transport = httpx.ASGITransport(app=app)
    with httpx.Client(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture()
def sqlite_engine():
    return create_engine("sqlite+pysqlite:///:memory:", future=True)
