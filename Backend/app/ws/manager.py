import logging
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, board_id: str):
        await websocket.accept()
        if board_id not in self.active_connections:
            self.active_connections[board_id] = []
        self.active_connections[board_id].append(websocket)
        logger.info(f"Client connected to board {board_id}. Total: {len(self.active_connections[board_id])}")

    def disconnect(self, websocket: WebSocket, board_id: str):
        if board_id in self.active_connections:
            if websocket in self.active_connections[board_id]:
                self.active_connections[board_id].remove(websocket)
                logger.info(f"Client disconnected from board {board_id}.")
            if not self.active_connections[board_id]:
                del self.active_connections[board_id]

    async def broadcast_to_board(self, board_id: str, message: str):
        if board_id in self.active_connections:
            for connection in self.active_connections[board_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending message to client on board {board_id}: {e}")

manager = ConnectionManager()
