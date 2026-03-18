"""WebSocket route for real-time board updates."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..services.ws_manager import manager

router = APIRouter()


@router.websocket("/ws/board")
async def board_websocket(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
