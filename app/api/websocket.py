import uuid
import json
from datetime import datetime
from typing import Set
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.security import decode_token


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str, session_id: str | None = None):
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = {}

        conn_key = session_id or str(uuid.uuid4())
        self.active_connections[user_id][conn_key] = websocket

    def disconnect(self, user_id: str, session_id: str | None = None):
        if user_id in self.active_connections:
            if session_id and session_id in self.active_connections[user_id]:
                del self.active_connections[user_id][session_id]
            else:
                self.active_connections[user_id].clear()

            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: str, session_id: str | None = None):
        if user_id in self.active_connections:
            if session_id and session_id in self.active_connections[user_id]:
                websocket = self.active_connections[user_id][session_id]
                await websocket.send_json(message)
            else:
                for websocket in self.active_connections[user_id].values():
                    await websocket.send_json(message)

    async def broadcast(self, message: dict):
        for user_connections in self.active_connections.values():
            for websocket in user_connections.values():
                await websocket.send_json(message)

    def get_online_users(self) -> list[str]:
        return list(self.active_connections.keys())

    def is_user_online(self, user_id: str) -> bool:
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0


manager = ConnectionManager()


class WebSocketHandler:
    @staticmethod
    async def authenticate(websocket: WebSocket) -> str | None:
        token = websocket.query_params.get("token")
        if not token:
            return None

        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            return None

        return payload.get("sub")

    @staticmethod
    async def handle_learning_update(user_id: str, data: dict):
        message = {
            "type": "learning_update",
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await manager.send_personal_message(message, user_id)

    @staticmethod
    async def handle_review_reminder(user_id: str, data: dict):
        message = {
            "type": "review_reminder",
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await manager.send_personal_message(message, user_id)

    @staticmethod
    async def handle_achievement(user_id: str, data: dict):
        message = {
            "type": "achievement",
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await manager.send_personal_message(message, user_id)

    @staticmethod
    async def handle_system_broadcast(data: dict):
        message = {
            "type": "system_broadcast",
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await manager.broadcast(message)


class SSEHandler:
    @staticmethod
    async def create_stream(event_type: str, data: dict) -> str:
        return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

    @staticmethod
    async def create_heartbeat() -> str:
        return f": heartbeat\n\n"
