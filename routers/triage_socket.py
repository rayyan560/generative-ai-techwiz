import datetime
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from routers.common import ws_manager
from src.security.auth import AuthManager

router = APIRouter(tags=["Live Triage"])
logger = logging.getLogger("SupportNova.TriageSocket")

@router.websocket("/ws/triage")
async def websocket_triage_endpoint(websocket: WebSocket):
    """Real-time bi-directional stream for triage dashboard & multi-agent notifications."""
    token = websocket.cookies.get("supportnova_session")
    user = AuthManager.verify_session_token(token) if token else None
    if not user or user.get("role") not in {"admin", "agent", "warranty_manager"}:
        await websocket.close(code=1008)
        return
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "PING_AGENT_PRESENCE":
                    await ws_manager.broadcast({
                        "type": "AGENT_PRESENCE_UPDATE",
                        "agent": msg.get("agent", "admin"),
                        "active_ticket": msg.get("active_ticket"),
                        "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
                    })
            except Exception as e:
                logger.warning(f"Error handling triage WS message: {e}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)
