import pytest
from fastapi.testclient import TestClient

from app import app
from config.database import DatabaseManager
from config.settings import AppSettings, settings, validate_public_demo_settings
from src.security import auth as auth_module
from src.security.auth import AuthManager


class MemoryUsersCollection:
    def __init__(self):
        self.documents = []

    def find_one(self, query):
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                return dict(document)
        return None

    def find(self, query=None):
        query = query or {}
        return [
            dict(document)
            for document in self.documents
            if all(document.get(key) == value for key, value in query.items())
        ]

    def insert_one(self, document):
        self.documents.append(dict(document))

    def update_one(self, query, update):
        for document in self.documents:
            if all(document.get(key) == value for key, value in query.items()):
                document.update(update.get("$set", {}))
                return type("UpdateResult", (), {"modified_count": 1})()
        return type("UpdateResult", (), {"modified_count": 0})()


def test_public_demo_configuration_requires_isolation_and_no_live_integrations(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET_KEY", "isolated-review-session-secret-at-least-32")
    config = AppSettings(
        DEMO_MODE=False,
        PUBLIC_DEMO_MODE=True,
        MONGODB_URI="mongodb://demo-database-user",
        DATABASE_NAME="supportnova_demo_public",
        GEMINI_API_KEYS=[],
        GOOGLE_CLIENT_ID="",
        GOOGLE_CLIENT_SECRET="",
        ADMIN_EMAIL="",
        ADMIN_PASSWORD="",
        AGENT_EMAIL="",
        AGENT_PASSWORD="",
    )

    validate_public_demo_settings(config)

    unsafe_config = config.model_copy(update={"DATABASE_NAME": "supportnova_db"})
    with pytest.raises(RuntimeError, match="DATABASE_NAME"):
        validate_public_demo_settings(unsafe_config)


def test_public_demo_never_uses_the_local_json_fallback(monkeypatch):
    monkeypatch.setattr(settings, "PUBLIC_DEMO_MODE", True)
    monkeypatch.setattr(settings, "MONGODB_URI", "")
    manager = object.__new__(DatabaseManager)

    with pytest.raises(RuntimeError, match="local JSON fallback is disabled"):
        manager.connect()


def test_public_demo_credentials_are_only_rendered_when_enabled(monkeypatch):
    monkeypatch.setattr(AuthManager, "get_current_user", staticmethod(lambda request: None))
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    monkeypatch.setattr(settings, "PUBLIC_DEMO_MODE", False)
    client = TestClient(app)

    production_login = client.get("/login")
    assert production_login.status_code == 200
    assert "demo_admin / AdminView2026!" not in production_login.text
    assert "demo_agent / AgentView2026!" not in production_login.text
    assert "admin / admin123" not in production_login.text

    monkeypatch.setattr(settings, "PUBLIC_DEMO_MODE", True)
    preview_login = client.get("/login")
    assert preview_login.status_code == 200
    assert "Admin Portal Preview" in preview_login.text
    assert "demo_admin / AdminView2026!" in preview_login.text
    assert "Agent Dashboard Preview" in preview_login.text
    assert "demo_agent / AgentView2026!" in preview_login.text
    assert "do not grant staff permissions" in preview_login.text


def test_public_demo_accounts_are_read_only_and_redirect_to_their_preview(monkeypatch):
    users = MemoryUsersCollection()
    monkeypatch.setattr(auth_module, "get_users_col", lambda: users)
    monkeypatch.setattr(auth_module, "_USERS_INITIALIZED", False)
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    monkeypatch.setattr(settings, "PUBLIC_DEMO_MODE", True)
    monkeypatch.setattr(settings, "ADMIN_EMAIL", "")
    monkeypatch.setattr(settings, "ADMIN_PASSWORD", "")
    monkeypatch.setattr(settings, "AGENT_EMAIL", "")
    monkeypatch.setattr(settings, "AGENT_PASSWORD", "")

    admin_preview = AuthManager.authenticate_user("demo_admin", "AdminView2026!")
    agent_preview = AuthManager.authenticate_user("demo_agent", "AgentView2026!")

    assert admin_preview["role"] == "judge"
    assert admin_preview["demo_portal"] == "admin"
    assert agent_preview["role"] == "judge"
    assert agent_preview["demo_portal"] == "agent"

    verified = AuthManager.verify_session_token(AuthManager.create_session_token(agent_preview))
    assert verified["role"] == "judge"
    assert verified["demo_portal"] == "agent"

    client = TestClient(app)
    login_response = client.post(
        "/api/auth/login",
        json={"identifier": "demo_agent", "password": "AgentView2026!"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["user"]["demo_portal"] == "agent"
    preview_token = login_response.json()["token"]
    preview_headers = {"Authorization": f"Bearer {preview_token}"}
    assert client.get("/agent", headers=preview_headers).status_code == 200
    blocked_write = client.post(
        "/api/chat/live/send",
        headers=preview_headers,
        json={"message": "This must not be sent."},
    )
    assert blocked_write.status_code == 403

    monkeypatch.setattr(settings, "PUBLIC_DEMO_MODE", False)
    assert AuthManager.authenticate_user("demo_admin", "AdminView2026!") is None
    assert AuthManager.verify_session_token(preview_token) is None


def test_agent_demo_identity_redirects_to_agent_preview(monkeypatch):
    agent_preview = {
        "user_id": "USR-PUBLIC-DEMO-AGENT",
        "username": "demo_agent",
        "role": "judge",
        "demo_portal": "agent",
    }
    monkeypatch.setattr(AuthManager, "get_current_user", staticmethod(lambda request: agent_preview))

    response = TestClient(app).get("/login", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/agent"
