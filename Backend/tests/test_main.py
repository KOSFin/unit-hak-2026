from pathlib import Path

import pytest

from app.main import create_app, lifespan


@pytest.mark.anyio
async def test_lifespan_starts_seed_and_relay(monkeypatch):
    calls = []

    class RelayStub:
        def __init__(self, _loop):
            self.started = False
            self.stopped = False

        def start(self):
            self.started = True
            calls.append("start")

        def stop(self):
            self.stopped = True
            calls.append("stop")

        def join(self, timeout):
            calls.append(("join", timeout))

    class SessionStub:
        def close(self):
            calls.append("close")

    monkeypatch.setattr("app.main.Base.metadata.create_all", lambda bind: calls.append(bind))
    monkeypatch.setattr("app.main.RealtimeRelay", RelayStub)
    monkeypatch.setattr("app.main.SessionLocal", lambda: SessionStub())
    monkeypatch.setattr("app.main.seed_demo_data", lambda session: calls.append(session))
    monkeypatch.setattr(
        "app.main.get_settings",
        lambda: type(
            "S",
            (),
            {
                "seed_demo_data": True,
                "log_level": "info",
                "cors_origins": lambda self: ["https://ui.example.com"],
                "uploads_filesystem_path": lambda self: Path("uploads"),
                "uploads_url_path": lambda self: "uploads",
            },
        )(),
    )

    async with lifespan(None):
        pass

    assert "start" in calls
    assert "stop" in calls


@pytest.mark.anyio
async def test_lifespan_without_seed(monkeypatch):
    calls = []

    class RelayStub:
        def __init__(self, _loop):
            return None

        def start(self):
            calls.append("start")

        def stop(self):
            calls.append("stop")

        def join(self, timeout):
            calls.append(timeout)

    monkeypatch.setattr("app.main.Base.metadata.create_all", lambda bind: calls.append(bind))
    monkeypatch.setattr("app.main.RealtimeRelay", RelayStub)
    monkeypatch.setattr(
        "app.main.get_settings",
        lambda: type(
            "S",
            (),
            {
                "seed_demo_data": False,
                "log_level": "info",
                "cors_origins": lambda self: [],
                "uploads_filesystem_path": lambda self: Path("uploads"),
                "uploads_url_path": lambda self: "uploads",
            },
        )(),
    )

    async with lifespan(None):
        pass

    assert "start" in calls


def test_create_app_configures_cors(monkeypatch):
    monkeypatch.setattr(
        "app.main.get_settings",
        lambda: type(
            "S",
            (),
            {
                "seed_demo_data": False,
                "log_level": "info",
                "cors_origins": lambda self: ["https://ui.example.com"],
                "uploads_filesystem_path": lambda self: Path("uploads"),
                "uploads_url_path": lambda self: "uploads",
            },
        )(),
    )
    monkeypatch.setattr("app.main.setup_logging", lambda _level: None)
    app = create_app()
    assert app.title == "FlowBoard API"
    assert app.docs_url == "/api/docs"
    assert app.redoc_url == "/api/redoc"
    assert app.openapi_url == "/api/openapi.json"


def test_create_app_exposes_openapi_docs(monkeypatch):
    monkeypatch.setattr(
        "app.main.get_settings",
        lambda: type(
            "S",
            (),
            {
                "seed_demo_data": False,
                "log_level": "info",
                "backend_public_url": None,
                "backend_base_url": lambda self: "http://127.0.0.1:8000",
                "cors_origins": lambda self: [],
                "uploads_filesystem_path": lambda self: Path("uploads"),
                "uploads_url_path": lambda self: "uploads",
            },
        )(),
    )
    monkeypatch.setattr("app.main.setup_logging", lambda _level: None)
    app = create_app()
    schema = app.openapi()

    assert schema["info"]["title"] == "FlowBoard API"
    assert "/api/incoming-tasks/{incoming_task_id}/reprocess" in schema["paths"]
    assert "/api/realtime" in schema["paths"]
    assert schema["x-websocket-endpoints"]["primary"].endswith("/ws")
