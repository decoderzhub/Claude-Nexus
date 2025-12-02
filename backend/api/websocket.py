"""
WebSocket handler for Claude Nexus.

Provides real-time communication for the frontend. Handles streaming
responses and live state updates.
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Optional
import json
import asyncio
from datetime import datetime

from services.world import WorldService
from models.identity import Identity
from config import settings


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.session_map: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: Optional[str] = None):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        if session_id:
            self.session_map[session_id] = websocket

    def disconnect(self, websocket: WebSocket, session_id: Optional[str] = None):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if session_id and session_id in self.session_map:
            del self.session_map[session_id]

    async def send_personal(self, message: dict, websocket: WebSocket):
        """Send a message to a specific connection."""
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        """Send a message to all connections."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Connection may have closed
                pass

    async def send_to_session(self, session_id: str, message: dict):
        """Send a message to a specific session."""
        if session_id in self.session_map:
            try:
                await self.session_map[session_id].send_json(message)
            except Exception:
                pass


# Global connection manager
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint handler.

    Protocol:
    - Client sends JSON messages with "type" field
    - Server responds with JSON messages with "type" field
    - Types: connect, state_update, world_update, heartbeat, etc.
    """
    session_id = None
    world_service = WorldService()

    try:
        # Accept connection
        await manager.connect(websocket)

        # Send initial state
        await send_initial_state(websocket, world_service)

        # Handle messages
        while True:
            try:
                data = await websocket.receive_json()
                await handle_message(websocket, data, world_service, session_id)
            except json.JSONDecodeError:
                await manager.send_personal({
                    "type": "error",
                    "message": "Invalid JSON"
                }, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)


async def send_initial_state(websocket: WebSocket, world_service: WorldService):
    """Send initial state on connection."""
    # Get current identity
    identity = Identity.load(settings.identity_path)

    # Get world state
    world_state = await world_service.get_world_state()

    await manager.send_personal({
        "type": "initial_state",
        "identity": identity.to_dict(),
        "world": world_state.to_dict(),
        "timestamp": datetime.now().isoformat(),
    }, websocket)


async def handle_message(
    websocket: WebSocket,
    data: dict,
    world_service: WorldService,
    session_id: Optional[str]
):
    """Handle incoming WebSocket messages."""
    msg_type = data.get("type", "unknown")

    if msg_type == "connect":
        # Client is registering with a session ID
        session_id = data.get("session_id")
        if session_id:
            manager.session_map[session_id] = websocket
        await manager.send_personal({
            "type": "connected",
            "session_id": session_id,
        }, websocket)

    elif msg_type == "heartbeat":
        # Respond to heartbeat
        await manager.send_personal({
            "type": "heartbeat_ack",
            "timestamp": datetime.now().isoformat(),
        }, websocket)

    elif msg_type == "get_state":
        # Request current state
        await send_initial_state(websocket, world_service)

    elif msg_type == "world_update":
        # Broadcast world update to all clients
        await manager.broadcast({
            "type": "world_update",
            "data": data.get("data", {}),
            "timestamp": datetime.now().isoformat(),
        })

    elif msg_type == "avatar_move":
        # Handle avatar movement
        position = data.get("position", {})
        await world_service.update_world_state(
            avatar_position=position
        )
        await manager.broadcast({
            "type": "avatar_moved",
            "position": position,
            "timestamp": datetime.now().isoformat(),
        })

    elif msg_type == "visit_space":
        # Handle space navigation
        space_name = data.get("space")
        if space_name:
            from models.world import Space
            try:
                space = Space(space_name)
                space_state = await world_service.visit_space(space)
                await manager.broadcast({
                    "type": "space_visited",
                    "space": space_name,
                    "state": space_state.to_dict(),
                    "timestamp": datetime.now().isoformat(),
                })
            except ValueError:
                await manager.send_personal({
                    "type": "error",
                    "message": f"Unknown space: {space_name}"
                }, websocket)

    elif msg_type == "subscribe":
        # Subscribe to specific events (future use)
        events = data.get("events", [])
        await manager.send_personal({
            "type": "subscribed",
            "events": events,
        }, websocket)

    else:
        await manager.send_personal({
            "type": "error",
            "message": f"Unknown message type: {msg_type}"
        }, websocket)


async def broadcast_state_change(event_type: str, data: dict):
    """
    Broadcast a state change to all connected clients.

    Call this from services when state changes occur.
    """
    await manager.broadcast({
        "type": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat(),
    })


async def notify_session(session_id: str, event_type: str, data: dict):
    """
    Send a notification to a specific session.

    Call this for session-specific events.
    """
    await manager.send_to_session(session_id, {
        "type": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat(),
    })
