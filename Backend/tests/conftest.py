import os

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("RABBITMQ_HOST", "")
os.environ.setdefault("SEED_DEMO_DATA", "false")

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.config import get_settings
from app.core.database import Base, get_engine, get_session
from app.main import create_app


@pytest.fixture(autouse=True)
def clear_state():
    get_settings.cache_clear()
    import app.services.event_service

    app.services.event_service._publisher = None
    yield
    get_settings.cache_clear()
    app.services.event_service._publisher = None


@pytest.fixture()
def sqlite_engine():
    return create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )


@pytest.fixture()
def db_session(sqlite_engine):
    Base.metadata.create_all(sqlite_engine)
    session_local = sessionmaker(bind=sqlite_engine, autoflush=False, autocommit=False)
    session = session_local()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(sqlite_engine)


@pytest.fixture()
def app(sqlite_engine, db_session):
    application = create_app()

    def override_get_session():
        yield db_session

    def override_get_engine():
        return sqlite_engine

    application.dependency_overrides[get_session] = override_get_session
    application.dependency_overrides[get_engine] = override_get_engine
    return application


@pytest.fixture()
async def async_client(app):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture()
def sync_client(app):
    with TestClient(app) as client:
        yield client


@pytest.fixture()
def seeded_board(db_session):
    from app.repositories.board_repository import BoardRepository
    from app.repositories.column_repository import ColumnRepository

    board = BoardRepository(db_session).create("FlowBoard")
    column_repo = ColumnRepository(db_session)
    todo = column_repo.create(board.id, "To Do", 1, True)
    in_progress = column_repo.create(board.id, "In Progress", 2, False)
    done = column_repo.create(board.id, "Done", 3, False)
    return {
        "board": board,
        "todo": todo,
        "in_progress": in_progress,
        "done": done,
    }
