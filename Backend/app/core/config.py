from functools import lru_cache
from importlib.util import find_spec
from typing import Any

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    log_level: str = "info"
    database_url: str = Field(
        default="sqlite+pysqlite:///:memory:",
        validation_alias=AliasChoices("DATABASE_URL", "database_url"),
    )
    rabbitmq_url: str | None = None
    rabbitmq_host: str | None = None
    rabbitmq_port: int = 5672
    backend_cors_origins: str = ""
    jwt_secret: str = "change_me_even_if_auth_is_simple"
    seed_demo_data: bool = False
    frontend_public_url: str | None = None
    backend_public_url: str | None = None
    backend_internal_port: int = 8000
    uploads_dir: str = "uploads"
    max_upload_size_bytes: int = 5 * 1024 * 1024
    default_board_retention_days: int = 3
    board_cleanup_interval_seconds: int = 3600
    public_board_url_base: str | None = None

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.compose"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
        extra="ignore",
    )

    def cors_origins(self) -> list[str]:
        values = [self.backend_cors_origins]
        if self.frontend_public_url:
            values.append(self.frontend_public_url)

        origins: list[str] = []
        for value in values:
            if not value:
                continue
            for origin in value.split(","):
                normalized = origin.strip()
                if normalized and normalized not in origins:
                    origins.append(normalized)
        return origins

    def websocket_allowed_origins(self) -> set[str]:
        return set(self.cors_origins())

    def resolved_database_url(self) -> str:
        url = self.database_url

        if url.startswith("postgres://"):
            return "postgresql://" + url.removeprefix("postgres://")

        if url.startswith("postgresql+psycopg2://"):
            if find_spec("psycopg2") is None and find_spec("psycopg") is not None:
                return "postgresql+psycopg://" + url.removeprefix("postgresql+psycopg2://")

        if url.startswith("postgresql+psycopg://"):
            if find_spec("psycopg") is None and find_spec("psycopg2") is not None:
                return "postgresql+psycopg2://" + url.removeprefix("postgresql+psycopg://")

        return url

    def backend_base_url(self) -> str:
        if self.backend_public_url:
            return self.backend_public_url.rstrip("/")
        return f"http://127.0.0.1:{self.backend_internal_port}"

    def model_post_init(self, __context: Any) -> None:
        if self.rabbitmq_url is None and self.rabbitmq_host:
            self.rabbitmq_url = f"amqp://{self.rabbitmq_host}:{self.rabbitmq_port}/"


@lru_cache
def get_settings() -> Settings:
    return Settings()
