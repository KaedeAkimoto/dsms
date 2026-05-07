from fastapi import WebSocket
from typing import Dict, Set
from uuid import UUID
import asyncio
import json
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: UUID):
        await websocket.accept()
        user_id_str = str(user_id)
        if user_id_str not in self.active_connections:
            self.active_connections[user_id_str] = set()
        self.active_connections[user_id_str].add(websocket)
        logger.info(f"WebSocket connected for user {user_id_str}. Total connections: {len(self.active_connections[user_id_str])}")

    def disconnect(self, websocket: WebSocket, user_id: UUID):
        user_id_str = str(user_id)
        if user_id_str in self.active_connections:
            self.active_connections[user_id_str].discard(websocket)
            if not self.active_connections[user_id_str]:
                del self.active_connections[user_id_str]
        logger.info(f"WebSocket disconnected for user {user_id_str}")

    async def send_personal_message(self, message: dict, user_id: UUID):
        user_id_str = str(user_id)
        if user_id_str in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[user_id_str]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.warning(f"Failed to send message to websocket: {e}")
                    disconnected.append(websocket)
            for ws in disconnected:
                self.active_connections[user_id_str].discard(ws)
            if not self.active_connections[user_id_str]:
                del self.active_connections[user_id_str]

    def is_user_online(self, user_id: UUID) -> bool:
        user_id_str = str(user_id)
        return user_id_str in self.active_connections and len(self.active_connections[user_id_str]) > 0

    def get_online_users(self) -> list:
        return list(self.active_connections.keys())

    def get_user_connection_count(self, user_id: UUID) -> int:
        user_id_str = str(user_id)
        if user_id_str in self.active_connections:
            return len(self.active_connections[user_id_str])
        return 0


sse_connection_manager = ConnectionManager()