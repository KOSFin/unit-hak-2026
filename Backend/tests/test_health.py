import socket

import pytest
from sqlalchemy import create_engine

from app.core.health import (
    check_database,
    check_rabbitmq,
    main,
    readiness_status,
    run_worker_healthcheck,
)


@pytest.mark.anyio
async def test_health_endpoint(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "backend-api"}


@pytest.mark.anyio
async def test_ready_endpoint(async_client):
    response = await async_client.get("/ready")
    assert response.status_code == 200
    assert response.json()["ready"] is True


@pytest.mark.anyio
async def test_ready_endpoint_unavailable(async_client, monkeypatch):
    monkeypatch.setattr(
        "app.api.health.readiness_status",
        lambda _engine: {"ready": False, "checks": {}},
    )
    response = await async_client.get("/ready")
    assert response.status_code == 503


def test_check_database_and_readiness_failure(monkeypatch):
    failing_engine = create_engine("sqlite+pysqlite:///:memory:")
    monkeypatch.setattr("app.core.health.check_rabbitmq", lambda *_args: (False, "down"))
    result = readiness_status(failing_engine)
    assert result["ready"] is False
    assert result["checks"]["rabbitmq"]["error"] == "down"


def test_check_database_failure_and_check_rabbitmq_branches(monkeypatch):
    class BrokenEngine:
        def connect(self):
            raise RuntimeError("db down")

    ok, error = check_database(BrokenEngine())
    assert ok is False
    assert "db down" in error

    assert check_rabbitmq(None, 5672) == (True, "")

    class ConnectionStub:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(socket, "create_connection", lambda *_args, **_kwargs: ConnectionStub())
    assert check_rabbitmq("rabbitmq", 5672) == (True, "")

    def raise_socket(*_args, **_kwargs):
        raise OSError("socket failed")

    monkeypatch.setattr(socket, "create_connection", raise_socket)
    ok, error = check_rabbitmq("rabbitmq", 5672)
    assert ok is False
    assert "socket failed" in error


def test_worker_healthcheck_and_main():
    class GoodSettings:
        database_url = "sqlite+pysqlite:///:memory:"

        def resolved_database_url(self):
            return self.database_url

    class BadSettings:
        database_url = ""

        def resolved_database_url(self):
            return self.database_url

    assert run_worker_healthcheck(GoodSettings()) == 0
    assert run_worker_healthcheck(BadSettings()) == 1
    assert main(["worker"]) == 0
    assert main([]) == 0
