from app.core import database


def test_create_db_engine(monkeypatch):
    class SettingsStub:
        def resolved_database_url(self):
            return "sqlite+pysqlite:///:memory:"

    monkeypatch.setattr("app.core.database.get_settings", lambda: SettingsStub())
    engine = database.create_db_engine()
    assert str(engine.url) == "sqlite+pysqlite:///:memory:"


def test_get_session_closes_session(monkeypatch):
    closed = False

    class SessionStub:
        def close(self):
            nonlocal closed
            closed = True

    monkeypatch.setattr("app.core.database.SessionLocal", lambda: SessionStub())

    generator = database.get_session()
    session = next(generator)
    assert isinstance(session, SessionStub)
    generator.close()

    assert closed is True


def test_get_engine_returns_global_engine():
    assert database.get_engine() is database.engine
