import json

from fastapi import WebSocket


class ConnectionManager:
    """Tracks connected WebSocket clients and fans out price update events."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, payload: dict) -> None:
        message = json.dumps(payload, default=str)
        dead_connections = []
        for connection in self._connections:
            try:
                await connection.send_text(message)
            except Exception:
                dead_connections.append(connection)
        for connection in dead_connections:
            self.disconnect(connection)


manager = ConnectionManager()
