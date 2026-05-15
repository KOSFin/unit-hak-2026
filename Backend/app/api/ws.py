from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.ws.manager import manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/{board_id}")
async def websocket_endpoint(
    websocket: WebSocket, board_id: str, token: str | None = Query(None)
):
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Check token logic (mock for now)
    if token != "valid-token":
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, board_id)
    try:
        while True:
            # Receive to keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, board_id)
