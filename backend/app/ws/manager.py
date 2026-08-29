from __future__ import annotations

import asyncio
import json
import logging
from typing import Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages active WebSocket connections for the real-time control room.
    """

    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast a JSON message to all connected clients."""
        if not self.active_connections:
            return

        data = json.dumps(message, default=str)
        disconnected: list[WebSocket] = []

        async with self._lock:
            connections = list(self.active_connections)

        for ws in connections:
            try:
                await ws.send_text(data)
            except Exception:
                disconnected.append(ws)

        for ws in disconnected:
            await self.disconnect(ws)

    async def send_risk_event(
        self,
        incident_id: str | None,
        application: str,
        action: str,
        severity: str,
        reasons: list[str],
        performance_score: float = 0.0,
        cost_score: float = 0.0,
        responsibility_score: float = 0.0,
        overall_score: float = 0.0,
    ) -> None:
        """Send a ControlPlane risk event to all connected dashboards."""
        from datetime import datetime, timezone
        await self.broadcast({
            "event": "risk_event",
            "incident_id": incident_id,
            "application": application,
            "action": action,
            "severity": severity,
            "reasons": reasons[:3],
            "scores": {
                "performance": round(performance_score, 3),
                "cost": round(cost_score, 3),
                "responsibility": round(responsibility_score, 3),
                "overall": round(overall_score, 3),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })


# Global singleton
ws_manager = ConnectionManager()
