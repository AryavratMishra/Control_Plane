from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.ws.manager import ws_manager

router = APIRouter()


@router.websocket("/control-room")
async def control_room_ws(websocket: WebSocket):
    """
    WebSocket endpoint for the real-time Control Room dashboard.
    Streams risk_event messages as they happen.
    """
    await ws_manager.connect(websocket)
    try:
        # Send welcome message
        await websocket.send_json({
            "event": "connected",
            "message": "ControlPlane Control Room connected",
        })
        # Keep connection alive — receive any pings
        while True:
            try:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_json({"event": "pong"})
            except Exception:
                break
    except WebSocketDisconnect:
        pass
    finally:
        await ws_manager.disconnect(websocket)
