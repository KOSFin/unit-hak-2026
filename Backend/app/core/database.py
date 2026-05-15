from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import get_settings

Base = declarative_base()


def create_db_engine():
    settings = get_settings()
    return create_engine(settings.database_url, pool_pre_ping=True, future=True)


engine = create_db_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_engine():
    return engine


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
