from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app import app


def test_admin_chatbot_websocket_rejects_anonymous_clients():
    client = TestClient(app)
    try:
        with client.websocket_connect("/ws/chat?mode=admin"):
            raise AssertionError("Anonymous admin websocket unexpectedly connected")
    except WebSocketDisconnect as error:
        assert error.code == 1008


def test_chatbot_websocket_rejects_unknown_modes():
    client = TestClient(app)
    try:
        with client.websocket_connect("/ws/chat?mode=unknown"):
            raise AssertionError("Unknown chatbot mode unexpectedly connected")
    except WebSocketDisconnect as error:
        assert error.code == 1008
