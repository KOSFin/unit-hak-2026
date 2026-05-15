from app.core.config import Settings


def test_cors_origins_and_websocket_allowed_origins():
    settings = Settings(
        backend_cors_origins="https://one.example.com, https://two.example.com",
        frontend_public_url="https://one.example.com",
    )

    assert settings.cors_origins() == [
        "https://one.example.com",
        "https://two.example.com",
    ]
    assert settings.websocket_allowed_origins() == {
        "https://one.example.com",
        "https://two.example.com",
    }


def test_resolved_database_url_aliases(monkeypatch):
    settings = Settings(DATABASE_URL="postgres://demo:secret@db:5432/flowboard")
    assert settings.resolved_database_url() == "postgresql://demo:secret@db:5432/flowboard"

    monkeypatch.setattr(
        "app.core.config.find_spec",
        lambda name: object() if name == "psycopg" else None,
    )
    settings = Settings(
        DATABASE_URL="postgresql+psycopg2://demo:secret@db:5432/flowboard",
    )
    assert settings.resolved_database_url() == "postgresql+psycopg://demo:secret@db:5432/flowboard"

    monkeypatch.setattr(
        "app.core.config.find_spec",
        lambda name: object() if name == "psycopg2" else None,
    )
    settings = Settings(
        DATABASE_URL="postgresql+psycopg://demo:secret@db:5432/flowboard",
    )
    assert settings.resolved_database_url() == "postgresql+psycopg2://demo:secret@db:5432/flowboard"


def test_backend_base_url_and_rabbitmq_url_auto_fill():
    settings = Settings(
        rabbitmq_host="rabbitmq",
        rabbitmq_port=5672,
        backend_internal_port=9000,
    )

    assert settings.rabbitmq_url == "amqp://rabbitmq:5672/"
    assert settings.backend_base_url() == "http://127.0.0.1:9000"

    public = Settings(backend_public_url="https://api.flowboard.example.com/")
    assert public.backend_base_url() == "https://api.flowboard.example.com"


def test_resolved_database_url_passthrough_branches(monkeypatch):
    monkeypatch.setattr("app.core.config.find_spec", lambda _name: None)
    settings = Settings(DATABASE_URL="postgresql+psycopg2://demo:secret@db:5432/flowboard")
    assert settings.resolved_database_url() == "postgresql+psycopg2://demo:secret@db:5432/flowboard"

    settings = Settings(DATABASE_URL="postgresql+psycopg://demo:secret@db:5432/flowboard")
    assert settings.resolved_database_url() == "postgresql+psycopg://demo:secret@db:5432/flowboard"
