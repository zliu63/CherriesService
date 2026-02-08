from fastapi import WebSocket
from collections import defaultdict
import json


class ConnectionManager:
    """Manages WebSocket connections per quest."""

    def __init__(self):
        # {quest_id: {user_id: WebSocket}}
        self.active_connections: dict[str, dict[str, WebSocket]] = defaultdict(dict)

    def connect(self, quest_id: str, user_id: str, websocket: WebSocket):
        self.active_connections[quest_id][user_id] = websocket

    def disconnect(self, quest_id: str, user_id: str):
        self.active_connections[quest_id].pop(user_id, None)
        if not self.active_connections[quest_id]:
            del self.active_connections[quest_id]

    async def broadcast(self, quest_id: str, message: dict, exclude_user_id: str | None = None):
        connections = self.active_connections.get(quest_id, {})
        payload = json.dumps(message)
        disconnected = []
        for user_id, ws in connections.items():
            if user_id == exclude_user_id:
                continue
            try:
                await ws.send_text(payload)
            except Exception:
                disconnected.append(user_id)
        for user_id in disconnected:
            self.disconnect(quest_id, user_id)


manager = ConnectionManager()
