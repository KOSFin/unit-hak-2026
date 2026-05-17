from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ValidationErrorItem(BaseModel):
    loc: list[str | int] = Field(description="Location of the invalid field in the request payload.")
    msg: str = Field(description="Human-readable validation error message.")
    type: str = Field(description="Machine-readable validation error code.")
    ctx: dict[str, Any] | None = Field(default=None, description="Additional validator context.")


class ApiErrorResponse(BaseModel):
    detail: str | list[ValidationErrorItem] | dict[str, Any] = Field(
        description="Error details returned by the API.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"detail": "Board not found"},
                {
                    "detail": [
                        {
                            "loc": ["body", "name"],
                            "msg": "Field required",
                            "type": "missing",
                        }
                    ]
                },
            ]
        }
    )


class OperationStatusResponse(BaseModel):
    status: Literal["deleted"] = Field(description="Operation result flag.")

    model_config = ConfigDict(json_schema_extra={"example": {"status": "deleted"}})


class UploadResponse(BaseModel):
    url: str = Field(description="Public URL of the uploaded image asset.", examples=["/uploads/avatar.webp"])
    path: str = Field(description="Stored relative asset path.", examples=["/uploads/avatar.webp"])

    model_config = ConfigDict(
        json_schema_extra={"example": {"url": "/uploads/avatar.webp", "path": "/uploads/avatar.webp"}}
    )


class HealthResponse(BaseModel):
    status: str = Field(description="Overall service health status.", examples=["ok"])
    service: str = Field(description="Service identifier.", examples=["backend-api"])

    model_config = ConfigDict(json_schema_extra={"example": {"status": "ok", "service": "backend-api"}})


class ReadinessCheckResponse(BaseModel):
    ok: bool = Field(description="Whether the dependency check passed.")
    error: str | None = Field(default=None, description="Dependency error message when the check fails.")


class ReadinessChecksResponse(BaseModel):
    database: ReadinessCheckResponse
    rabbitmq: ReadinessCheckResponse


class ReadinessResponse(BaseModel):
    ready: bool = Field(description="Whether the service is ready to receive traffic.")
    checks: ReadinessChecksResponse

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "ready": True,
                    "checks": {
                        "database": {"ok": True, "error": None},
                        "rabbitmq": {"ok": True, "error": None},
                    },
                },
                {
                    "ready": False,
                    "checks": {
                        "database": {"ok": True, "error": None},
                        "rabbitmq": {"ok": False, "error": "socket failed"},
                    },
                },
            ]
        }
    )


class RealtimeUserSnapshot(BaseModel):
    guest_id: str = Field(description="Guest identifier participating in realtime presence.")
    display_name: str = Field(description="Display name shown to other participants.")
    color: str | None = Field(default=None, description="Optional UI accent color for the guest.")
    avatar_url: str | None = Field(default=None, description="Optional avatar asset URL.")
    active_task_id: str | None = Field(
        default=None,
        description="Task currently edited or dragged by the guest, when applicable.",
    )
    connected_at: str | None = Field(default=None, description="UTC timestamp when the guest connected.")
    active_connections: int = Field(description="Number of active websocket connections for the guest.")


class RealtimePresenceSnapshot(BaseModel):
    board_id: str = Field(description="Board identifier for the presence snapshot.")
    users: list[RealtimeUserSnapshot] = Field(default_factory=list, description="Connected users on the board.")
    editing: list[RealtimeUserSnapshot] = Field(
        default_factory=list,
        description="Users currently editing tasks.",
    )
    dragging: list[RealtimeUserSnapshot] = Field(
        default_factory=list,
        description="Users currently dragging tasks.",
    )


class RealtimeEventReference(BaseModel):
    type: str = Field(description="Realtime event type.")
    direction: Literal["client->server", "server->client"] = Field(
        description="Message direction over the websocket channel.",
    )
    description: str = Field(description="What the event is used for.")


class RealtimeReferenceResponse(BaseModel):
    transport: Literal["websocket"] = Field(default="websocket", description="Realtime transport protocol.")
    primary_url: str = Field(description="Primary websocket URL.")
    fallback_urls: list[str] = Field(
        default_factory=list,
        description="Supported websocket URL aliases accepted by the backend.",
    )
    accepted_client_events: list[RealtimeEventReference] = Field(
        default_factory=list,
        description="Client events accepted by the websocket server.",
    )
    emitted_server_events: list[RealtimeEventReference] = Field(
        default_factory=list,
        description="Server events emitted to connected clients.",
    )
    sample_join_message: dict[str, Any] = Field(
        description="Example payload for joining realtime presence on a board.",
    )
    sample_snapshot_message: dict[str, Any] = Field(
        description="Example payload returned by the server after a successful join.",
    )
    sample_error_message: dict[str, Any] = Field(
        description="Example error payload emitted by the server.",
    )
