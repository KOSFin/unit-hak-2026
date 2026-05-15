from app.core.config import Settings


def test_cors_origins_parsing():
    settings = Settings(backend_cors_origins="https://a.example, https://b.example")
    assert settings.cors_origins() == ["https://a.example", "https://b.example"]


def test_cors_origins_empty():
    settings = Settings(backend_cors_origins="")
    assert settings.cors_origins() == []


def test_seed_demo_data_parsing(monkeypatch):
    monkeypatch.setenv("SEED_DEMO_DATA", "true")
    settings = Settings()
    assert settings.seed_demo_data is True


def test_database_url_rewrites_to_psycopg_when_psycopg2_missing(monkeypatch):
    def fake_find_spec(name):
        if name == "psycopg2":
            return None
        if name == "psycopg":
            return object()
        return None

    monkeypatch.setattr("app.core.config.find_spec", fake_find_spec)
    settings = Settings(database_url="postgresql+psycopg2://user:pass@db:5432/app")
    assert settings.resolved_database_url() == "postgresql+psycopg://user:pass@db:5432/app"


def test_database_url_rewrites_to_psycopg2_when_psycopg_missing(monkeypatch):
    def fake_find_spec(name):
        if name == "psycopg":
            return None
        if name == "psycopg2":
            return object()
        return None

    monkeypatch.setattr("app.core.config.find_spec", fake_find_spec)
    settings = Settings(database_url="postgresql+psycopg://user:pass@db:5432/app")
    assert settings.resolved_database_url() == "postgresql+psycopg2://user:pass@db:5432/app"


def test_database_url_rewrites_postgres_scheme():
    settings = Settings(database_url="postgres://user:pass@db:5432/app")
    assert settings.resolved_database_url() == "postgresql://user:pass@db:5432/app"
