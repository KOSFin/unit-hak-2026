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
