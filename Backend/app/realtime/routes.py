from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.realtime.connection_manager import manager

router = APIRouter(tags=["realtime"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            try:
                await websocket.receive_text()
            except RuntimeError:
                break
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)
