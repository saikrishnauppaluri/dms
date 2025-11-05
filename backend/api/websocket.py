"""
WebSocket server for real-time telemetry streaming
"""
import asyncio
import json
from typing import Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

from core import get_fleet_manager


class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Accept and add new connection"""
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove connection"""
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return

        message_json = json.dumps(message, default=str)

        # Send to all connections
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception:
                disconnected.add(connection)

        # Remove disconnected clients
        for connection in disconnected:
            self.active_connections.discard(connection)

    async def send_personal(self, message: dict, websocket: WebSocket):
        """Send message to specific client"""
        message_json = json.dumps(message, default=str)
        await websocket.send_text(message_json)


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for telemetry streaming"""
    await manager.connect(websocket)

    try:
        # Send initial connection message
        await manager.send_personal(
            {
                "type": "connected",
                "message": "Connected to DMS telemetry stream",
                "timestamp": datetime.utcnow().isoformat()
            },
            websocket
        )

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=1.0
                )

                # Handle client commands
                try:
                    command = json.loads(data)
                    await handle_client_command(command, websocket)
                except json.JSONDecodeError:
                    await manager.send_personal(
                        {"type": "error", "message": "Invalid JSON"},
                        websocket
                    )

            except asyncio.TimeoutError:
                # No message received, continue
                continue

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def handle_client_command(command: dict, websocket: WebSocket):
    """Handle commands from client"""
    cmd_type = command.get("type")

    if cmd_type == "subscribe":
        # Subscribe to specific drone
        await manager.send_personal(
            {"type": "subscribed", "drone_id": command.get("drone_id")},
            websocket
        )

    elif cmd_type == "unsubscribe":
        # Unsubscribe from drone
        await manager.send_personal(
            {"type": "unsubscribed", "drone_id": command.get("drone_id")},
            websocket
        )

    elif cmd_type == "ping":
        # Health check
        await manager.send_personal(
            {"type": "pong", "timestamp": datetime.utcnow().isoformat()},
            websocket
        )


async def telemetry_broadcaster():
    """Background task to broadcast telemetry"""
    fleet = get_fleet_manager()

    while True:
        try:
            if manager.active_connections:
                # Get telemetry for all drones
                telemetry_dict = await fleet.get_telemetry_all()

                if telemetry_dict:
                    # Broadcast telemetry
                    await manager.broadcast({
                        "type": "telemetry",
                        "timestamp": datetime.utcnow().isoformat(),
                        "data": {str(k): v.dict() for k, v in telemetry_dict.items()}
                    })

            # Update rate: 10 Hz
            await asyncio.sleep(0.1)

        except Exception as e:
            print(f"Telemetry broadcaster error: {e}")
            await asyncio.sleep(1.0)


async def events_broadcaster():
    """Background task to broadcast events and alerts"""
    fleet = get_fleet_manager()
    last_event_count = 0
    last_alert_count = 0

    while True:
        try:
            if manager.active_connections:
                # Check for new events
                if len(fleet.events) > last_event_count:
                    new_events = fleet.events[last_event_count:]
                    for event in new_events:
                        await manager.broadcast({
                            "type": "event",
                            "data": event.dict()
                        })
                    last_event_count = len(fleet.events)

                # Check for new alerts
                if len(fleet.alerts) > last_alert_count:
                    new_alerts = fleet.alerts[last_alert_count:]
                    for alert in new_alerts:
                        await manager.broadcast({
                            "type": "alert",
                            "data": alert.dict()
                        })
                    last_alert_count = len(fleet.alerts)

            await asyncio.sleep(0.5)

        except Exception as e:
            print(f"Events broadcaster error: {e}")
            await asyncio.sleep(1.0)
