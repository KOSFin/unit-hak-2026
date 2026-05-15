import httpx
import pytest

from app.core import health as health_module
from app.core.database import get_engine


@pytest.mark.anyio
async def test_health_ok(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "backend-api"}


@pytest.mark.anyio
async def test_ready_ok(app, sqlite_engine):
    app.dependency_overrides[get_engine] = lambda: sqlite_engine
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/ready")
    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["ready"] is True
    assert payload["checks"]["database"]["ok"] is True


@pytest.mark.anyio
async def test_ready_db_failure(app, sqlite_engine, monkeypatch):
    app.dependency_overrides[get_engine] = lambda: sqlite_engine
    monkeypatch.setattr(health_module, "check_database", lambda engine: (False, "down"))
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/ready")
    app.dependency_overrides.clear()

    assert response.status_code == 503
    payload = response.json()["detail"]
    assert payload["ready"] is False
    assert payload["checks"]["database"]["ok"] is False


def test_check_rabbitmq_skips_when_no_host():
    ok, error = health_module.check_rabbitmq(None, 5672)
    assert ok is True
    assert error == ""


def test_check_rabbitmq_ok(monkeypatch):
    class DummySocket:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_create_connection(address, timeout):
        return DummySocket()

    monkeypatch.setattr(health_module.socket, "create_connection", fake_create_connection)
    ok, error = health_module.check_rabbitmq("localhost", 5672)
    assert ok is True
    assert error == ""


def test_check_rabbitmq_failure(monkeypatch):
    def fake_create_connection(address, timeout):
        raise OSError("nope")

    monkeypatch.setattr(health_module.socket, "create_connection", fake_create_connection)
    ok, error = health_module.check_rabbitmq("localhost", 5672)
    assert ok is False
    assert "nope" in error


def test_check_database_failure():
    class DummyEngine:
        def connect(self):
            raise RuntimeError("boom")

    ok, error = health_module.check_database(DummyEngine())
    assert ok is False
    assert "boom" in error


def test_health_main_worker_ok():
    assert health_module.main(["worker"]) == 0


def test_health_main_no_args():
    assert health_module.main([]) == 0


def test_worker_healthcheck_failure():
    from app.core.config import Settings

    settings = Settings(database_url="")
    assert health_module.run_worker_healthcheck(settings) == 1
