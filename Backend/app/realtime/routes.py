import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.schemas.common import RealtimeReferenceResponse

from app.realtime.connection_manager import manager

router = APIRouter(tags=["realtime"])
logger = logging.getLogger(__name__)


@router.get(
    "/api/realtime",
    response_model=RealtimeReferenceResponse,
    summary="Realtime contract reference",
    description="Documents websocket URLs, accepted client events, and emitted server events for Swagger consumers.",
)
def realtime_reference() -> RealtimeReferenceResponse:
    return RealtimeReferenceResponse(
        primary_url="/ws",
        fallback_urls=["/api/ws"],
        accepted_client_events=[
            {
                "type": "presence.join",
                "direction": "client->server",
                "description": "Join a board presence channel and receive a snapshot.",
            },
            {
                "type": "presence.update",
                "direction": "client->server",
                "description": "Update guest metadata such as display name, color, or avatar.",
            },
            {
                "type": "editing.started",
                "direction": "client->server",
                "description": "Mark a guest as editing a task.",
            },
            {
                "type": "editing.ended",
                "direction": "client->server",
                "description": "Clear editing state for a guest.",
            },
            {
                "type": "drag.started",
                "direction": "client->server",
                "description": "Mark a guest as dragging a task.",
            },
            {
                "type": "drag.ended",
                "direction": "client->server",
                "description": "Clear dragging state for a guest.",
            },
        ],
        emitted_server_events=[
            {
                "type": "presence.snapshot",
                "direction": "server->client",
                "description": "Full presence snapshot after a successful join.",
            },
            {
                "type": "presence.updated",
                "direction": "server->client",
                "description": "Presence state after an update, edit, drag, or disconnect.",
            },
            {
                "type": "system.error",
                "direction": "server->client",
                "description": "Validation or protocol error emitted by the websocket gateway.",
            },
        ],
        sample_join_message={
            "type": "presence.join",
            "board_id": "board-123",
            "user": {"guest_id": "guest-42", "display_name": "Alex"},
        },
        sample_snapshot_message={
            "type": "presence.snapshot",
            "payload": {"board_id": "board-123", "users": [], "editing": [], "dragging": []},
        },
        sample_error_message={
            "type": "system.error",
            "payload": {"message": "Missing board_id"},
        },
    )


async def _handle_websocket_session(websocket: WebSocket) -> None:
    joined_board_ids: set[str] = set()
    connection_id = hex(id(websocket))
    client_host = getattr(websocket.client, "host", None)
    client_port = getattr(websocket.client, "port", None)
    await websocket.accept()
    logger.info(
        "Realtime websocket accepted connection_id=%s client=%s:%s",
        connection_id,
        client_host,
        client_port,
    )

    try:
        while True:
            message = await websocket.receive_json()
            board_id = str(message.get("board_id") or "")
            event_type = str(message.get("type") or "")
            user = message.get("user") or {}
            guest_id = str(user.get("guest_id") or "")

            if not board_id:
                logger.warning(
                    "Realtime websocket missing board_id connection_id=%s event_type=%s guest_id=%s",
                    connection_id,
                    event_type,
                    guest_id,
                )
                await websocket.send_json(
                    {"type": "system.error", "payload": {"message": "Missing board_id"}}
                )
                continue

            if event_type == "presence.join":
                joined_board_ids.add(board_id)
                logger.info(
                    "Realtime presence join connection_id=%s board_id=%s guest_id=%s",
                    connection_id,
                    board_id,
                    guest_id,
                )
                snapshot = await manager.connect(board_id, websocket, user)
                await manager.broadcast(board_id, {"type": "presence.snapshot", "payload": snapshot})
            elif event_type == "presence.update":
                snapshot = manager.update_presence(board_id, user)
                await manager.broadcast(board_id, {"type": "presence.updated", "payload": snapshot})
            elif event_type == "editing.started":
                snapshot = manager.start_editing(
                    board_id,
                    str(user.get("guest_id") or ""),
                    str(user.get("active_task_id") or ""),
                )
                await manager.broadcast(board_id, {"type": "presence.updated", "payload": snapshot})
            elif event_type == "editing.ended":
                snapshot = manager.stop_editing(board_id, str(user.get("guest_id") or ""))
                await manager.broadcast(board_id, {"type": "presence.updated", "payload": snapshot})
            elif event_type == "drag.started":
                snapshot = manager.start_dragging(
                    board_id,
                    str(user.get("guest_id") or ""),
                    str(user.get("active_task_id") or ""),
                )
                await manager.broadcast(board_id, {"type": "presence.updated", "payload": snapshot})
            elif event_type == "drag.ended":
                snapshot = manager.stop_dragging(board_id, str(user.get("guest_id") or ""))
                await manager.broadcast(board_id, {"type": "presence.updated", "payload": snapshot})
            else:
                logger.warning(
                    "Realtime websocket unsupported event connection_id=%s board_id=%s guest_id=%s event_type=%s",
                    connection_id,
                    board_id,
                    guest_id,
                    event_type,
                )
                await websocket.send_json(
                    {
                        "type": "system.error",
                        "payload": {"message": f"Unsupported realtime event: {event_type}"},
                    }
                )
    except WebSocketDisconnect:
        logger.info(
            "Realtime websocket disconnected connection_id=%s joined_board_ids=%s",
            connection_id,
            sorted(joined_board_ids),
        )
    finally:
        for board_id in joined_board_ids or list(manager.boards.keys()):
            snapshot = manager.disconnect(board_id, websocket)
            await manager.broadcast(board_id, {"type": "presence.updated", "payload": snapshot})


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await _handle_websocket_session(websocket)


@router.websocket("/api/ws")
async def websocket_api_endpoint(websocket: WebSocket) -> None:
    await _handle_websocket_session(websocket)
