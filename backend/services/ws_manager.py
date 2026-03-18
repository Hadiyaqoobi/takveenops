"""WebSocket connection manager for real-time board updates."""

import json
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active_connections:
            self.active_connections.remove(ws)

    async def broadcast(self, event: str, payload: dict):
        message = json.dumps({"event": event, "payload": payload})
        for conn in self.active_connections[:]:
            try:
                await conn.send_text(message)
            except Exception:
                self.active_connections.remove(conn)


manager = ConnectionManager()
