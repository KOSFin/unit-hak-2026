from __future__ import annotations

import logging
import socket
import sys
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.core.config import Settings, get_settings

logger = logging.getLogger("flowboard.health")


def check_database(engine: Engine) -> tuple[bool, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, ""
    except Exception as exc:
        return False, str(exc)


def check_rabbitmq(host: str | None, port: int) -> tuple[bool, str]:
    if not host:
        return True, ""
    try:
        with socket.create_connection((host, port), timeout=2):
            return True, ""
    except Exception as exc:
        return False, str(exc)


def readiness_status(engine: Engine) -> dict[str, Any]:
    settings = get_settings()
    db_ok, db_error = check_database(engine)
    rabbit_ok, rabbit_error = check_rabbitmq(settings.rabbitmq_host, settings.rabbitmq_port)
    return {
        "ready": db_ok and rabbit_ok,
        "checks": {
            "database": {"ok": db_ok, "error": db_error or None},
            "rabbitmq": {"ok": rabbit_ok, "error": rabbit_error or None},
        },
    }


def run_worker_healthcheck(settings: Settings | None = None) -> int:
    try:
        settings = settings or get_settings()
        if not settings.database_url:
            raise ValueError("DATABASE_URL is missing")
        return 0
    except Exception:
        logger.exception("Worker healthcheck failed")
        return 1


def main(args: list[str] | None = None) -> int:
    args = args or []
    if args and args[0] == "worker":
        return run_worker_healthcheck()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
