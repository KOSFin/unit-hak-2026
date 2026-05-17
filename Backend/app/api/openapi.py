from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit, urlunsplit

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.core.config import Settings
from app.schemas.common import ApiErrorResponse

OPENAPI_TAGS = [
    {
        "name": "health",
        "description": "Operational health and readiness probes used by runtime infrastructure.",
    },
    {
        "name": "boards",
        "description": "Board lifecycle management, ownership lookup, and activity timeline retrieval.",
    },
    {
        "name": "columns",
        "description": "Column management within a board, including ordering and deletion safeguards.",
    },
    {
        "name": "tasks",
        "description": "Task CRUD operations, optimistic locking, and cross-column movement.",
    },
    {
        "name": "incoming-tasks",
        "description": "Inbound task ingestion pipeline and manual reprocessing entrypoints.",
    },
    {
        "name": "notifications",
        "description": "Board-scoped notifications and read-state management.",
    },
    {
        "name": "automation-rules",
        "description": "Automation rule definitions evaluated by the worker on task events.",
    },
    {
        "name": "guests",
        "description": "Guest profile payloads used by collaborative board sessions.",
    },
    {
        "name": "uploads",
        "description": "Image upload endpoint for board covers and guest avatars.",
    },
    {
        "name": "realtime",
        "description": "Reference contract for websocket-based presence and collaborative realtime updates.",
    },
]

OPENAPI_DESCRIPTION = """
FlowBoard backend contract for board collaboration, task management, automation, uploads, notifications,
and incoming-task ingestion.

Key conventions:

- All REST endpoints are served under the `/api` namespace.
- Resource identifiers are opaque strings and must be treated as stable backend-issued IDs.
- Task mutation endpoints use optimistic locking through the `version` field.
- Realtime communication is delivered over WebSocket and documented through the `realtime` tag reference endpoint.
- Error responses use the `detail` field for both business-rule failures and validation errors.
""".strip()


def build_openapi_schema(app: FastAPI, settings: Settings) -> dict[str, Any]:
    schema = get_openapi(
        title=app.title,
        version=app.version,
        summary="REST and realtime contract for the FlowBoard collaboration backend.",
        description=OPENAPI_DESCRIPTION,
        routes=app.routes,
        tags=OPENAPI_TAGS,
    )
    schema["info"]["contact"] = {"name": "FlowBoard Backend Team"}
    schema["servers"] = _build_servers(settings)
    schema["x-websocket-endpoints"] = {
        "primary": _to_websocket_url(settings.backend_base_url(), "/ws"),
        "aliases": [
            _to_websocket_url(settings.backend_base_url(), "/ws"),
            _to_websocket_url(settings.backend_base_url(), "/api/ws"),
        ],
    }
    schema.setdefault("components", {}).setdefault("schemas", {})
    schema["components"]["schemas"].setdefault("ApiErrorResponse", ApiErrorResponse.model_json_schema())
    return schema


def install_openapi(app: FastAPI, settings: Settings) -> None:
    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
        app.openapi_schema = build_openapi_schema(app, settings)
        return app.openapi_schema

    app.openapi = custom_openapi


def error_response(description: str, example: Any) -> dict[str, Any]:
    return {
        "model": ApiErrorResponse,
        "description": description,
        "content": {"application/json": {"example": {"detail": example}}},
    }


def _build_servers(settings: Settings) -> list[dict[str, str]]:
    servers = [{"url": "/", "description": "Relative server URL"}]
    public_base = settings.backend_public_url
    if public_base:
        servers.append({"url": public_base.rstrip("/"), "description": "Configured public backend URL"})
    return servers


def _to_websocket_url(base_url: str, path: str) -> str:
    parts = urlsplit(base_url)
    scheme = "wss" if parts.scheme == "https" else "ws"
    return urlunsplit((scheme, parts.netloc, path, "", ""))
