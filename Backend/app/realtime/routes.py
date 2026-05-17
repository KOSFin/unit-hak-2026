from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.realtime.connection_manager import manager

router = APIRouter(tags=["realtime"])

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    try:
        while True:
            try:
                message = await websocket.receive_json()
                board_id = str(message.get("board_id") or "")
                event_type = str(message.get("type") or "")
                user = message.get("user") or {}
                if not board_id:
                    continue
                if event_type == "presence.join":
                    snapshot = await manager.connect(board_id, websocket, user)
                    await manager.broadcast(board_id, {"type": "presence.snapshot", "payload": snapshot})
                elif event_type == "presence.update":
                    snapshot = manager.update_presence(board_id, user)
                    await manager.broadcast(board_id, {"type": "presence.updated", "payload": snapshot})
                elif event_type == "editing.started":
                    snapshot = manager.start_editing(board_id, str(user.get("guest_id") or ""), str(user.get("active_task_id") or ""))
                    await manager.broadcast(board_id, {"type": "presence.updated", "payload": snapshot})
                elif event_type == "editing.ended":
                    snapshot = manager.stop_editing(board_id, str(user.get("guest_id") or ""))
                    await manager.broadcast(board_id, {"type": "presence.updated", "payload": snapshot})
                elif event_type == "drag.started":
                    snapshot = manager.start_dragging(board_id, str(user.get("guest_id") or ""), str(user.get("active_task_id") or ""))
                    await manager.broadcast(board_id, {"type": "presence.updated", "payload": snapshot})
                elif event_type == "drag.ended":
                    snapshot = manager.stop_dragging(board_id, str(user.get("guest_id") or ""))
                    await manager.broadcast(board_id, {"type": "presence.updated", "payload": snapshot})
            except RuntimeError:
                break
    except WebSocketDisconnect:
        pass
    finally:
        for board_id in list(manager.boards.keys()):
            snapshot = manager.disconnect(board_id, websocket)
            # await manager.broadcast(board_id, {"type": "presence.updated", "payload": snapshot}) # can't await in finally if loop is closed, ignoring for now or relying on other tasks
