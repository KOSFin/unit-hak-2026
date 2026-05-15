from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    log_level: str = "info"
    database_url: str = "sqlite+pysqlite:///:memory:"
    rabbitmq_url: str | None = None
    rabbitmq_host: str | None = None
    rabbitmq_port: int = 5672
    backend_cors_origins: str = ""
    jwt_secret: str = "change_me_even_if_auth_is_simple"
    seed_demo_data: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    def cors_origins(self) -> list[str]:
        if not self.backend_cors_origins:
            return []
        return [
            origin.strip()
            for origin in self.backend_cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
