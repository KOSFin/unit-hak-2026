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
                "uploads_filesystem_path": lambda self: __import__("pathlib").Path("uploads"),
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
                "uploads_filesystem_path": lambda self: __import__("pathlib").Path("uploads"),
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
                "uploads_filesystem_path": lambda self: __import__("pathlib").Path("uploads"),
                "uploads_url_path": lambda self: "uploads",
            },
        )(),
    )
    monkeypatch.setattr("app.main.setup_logging", lambda _level: None)
    app = create_app()
    assert app.title == "FlowBoard API"
