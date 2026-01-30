"""WebSocket connection handler with broadcast support."""

import asyncio
import json
from datetime import datetime
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from .models import OutputLineType, WSEvent, WSMessage


class ConnectionManager:
    """Manages WebSocket connections and broadcasts."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast(self, event: WSEvent, data: dict[str, Any]) -> None:
        """Broadcast a message to all connected clients."""
        message = WSMessage(event=event, data=data)
        json_data = message.model_dump_json()

        async with self._lock:
            dead_connections = set()
            for connection in self._connections:
                try:
                    await connection.send_text(json_data)
                except Exception:
                    dead_connections.add(connection)

            # Remove dead connections
            self._connections -= dead_connections

    async def send_personal(self, websocket: WebSocket, event: WSEvent, data: dict[str, Any]) -> None:
        """Send a message to a specific client."""
        message = WSMessage(event=event, data=data)
        try:
            await websocket.send_text(message.model_dump_json())
        except Exception:
            pass

    @property
    def connection_count(self) -> int:
        """Get number of active connections."""
        return len(self._connections)


# Singleton instance
_manager: ConnectionManager | None = None


def get_connection_manager() -> ConnectionManager:
    """Get the singleton connection manager instance."""
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager


def classify_output_line(line: str) -> OutputLineType:
    """Classify an output line by type."""
    line_lower = line.lower()

    if line.startswith("Error:") or line.startswith("ERROR:") or "error" in line_lower:
        return OutputLineType.ERROR

    if "thinking" in line_lower or line.startswith(">"):
        return OutputLineType.THINKING

    if any(tool in line_lower for tool in ["tool:", "using tool", "bash:", "read:", "write:", "edit:"]):
        return OutputLineType.TOOL_USE

    if "result:" in line_lower or "output:" in line_lower:
        return OutputLineType.TOOL_RESULT

    return OutputLineType.TEXT


def create_output_handler(manager: ConnectionManager):
    """Create an output handler that broadcasts to WebSocket clients."""

    def handler(line: str) -> None:
        """Handle an output line from the process."""
        line_type = classify_output_line(line)
        data = {
            "type": line_type.value,
            "content": line,
            "timestamp": datetime.now().isoformat(),
        }

        # Schedule broadcast in the event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(manager.broadcast(WSEvent.OUTPUT_LINE, data))
        except RuntimeError:
            pass

    return handler


async def websocket_endpoint(websocket: WebSocket) -> None:
    """Handle a WebSocket connection."""
    manager = get_connection_manager()
    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                action = message.get("action")

                if action == "ping":
                    await manager.send_personal(websocket, WSEvent.PONG, {"timestamp": datetime.now().isoformat()})

            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)
