from sqlalchemy.engine import Engine

from app.core.database import create_db_engine, get_engine, get_session


def test_create_db_engine_returns_engine():
    engine = create_db_engine()
    assert isinstance(engine, Engine)


def test_get_engine_returns_engine():
    engine = get_engine()
    assert isinstance(engine, Engine)


def test_get_session_yields_session():
    generator = get_session()
    session = next(generator)
    assert session is not None
    generator.close()
