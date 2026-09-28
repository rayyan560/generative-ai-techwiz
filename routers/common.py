from typing import Dict, Any, List, Set
from fastapi import WebSocket
import logging

logger = logging.getLogger("SupportNova.Common")

def clean_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Ensures MongoDB ObjectId is converted to string for clean JSON serialization."""
    if not doc:
        return {}
    d = dict(doc)
    if "_id" in d:
        d["_id"] = str(d["_id"])
    return d

def clean_docs(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [clean_doc(d) for d in docs]

class WebSocketConnectionManager:
    """Manages real-time bidirectional WebSocket connections for live triage & agent presence."""
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        dead_connections = []
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Error sending message to WS connection: {e}")
                dead_connections.append(connection)
        for dead in dead_connections:
            if dead in self.active_connections:
                self.active_connections.remove(dead)

ws_manager = WebSocketConnectionManager()
