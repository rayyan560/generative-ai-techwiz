from fastapi.testclient import TestClient
from google.oauth2 import id_token

from app import app
from config.settings import settings
from src.security.auth import AuthManager


def test_google_login_uses_only_verified_identity_claims(monkeypatch):
    verified_user = {
        "email": "verified@example.com",
        "email_verified": True,
        "name": "Verified User",
        "picture": "https://example.test/avatar.png",
        "sub": "verified-subject",
    }
    authenticated = {}
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(id_token, "verify_oauth2_token", lambda *args: verified_user)
    monkeypatch.setattr(
        AuthManager,
        "authenticate_google_user",
        staticmethod(lambda **identity: authenticated.update(identity) or {
            "user_id": "verified-user",
            "email": identity["email"],
            "role": "customer",
        }),
    )
    monkeypatch.setattr(AuthManager, "create_session_token", staticmethod(lambda user: "verified-session"))

    response = TestClient(app).post(
        "/api/auth/google",
        json={
            "credential": "provider-signed-token",
            "email": "attacker@example.com",
            "name": "Unverified Name",
            "sub": "unverified-subject",
        },
    )

    assert response.status_code == 200
    assert authenticated == {
        "email": "verified@example.com",
        "display_name": "Verified User",
        "avatar": "https://example.test/avatar.png",
        "google_id": "verified-subject",
    }
    assert response.json()["user"]["email"] == "verified@example.com"
    assert response.cookies["supportnova_session"] == "verified-session"


def test_google_login_rejects_unverified_identity_without_authenticating(monkeypatch):
    authenticated = []
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(id_token, "verify_oauth2_token", lambda *args: {
        "email": "unverified@example.com",
        "email_verified": False,
    })
    monkeypatch.setattr(
        AuthManager,
        "authenticate_google_user",
        staticmethod(lambda **identity: authenticated.append(identity)),
    )

    response = TestClient(app).post(
        "/api/auth/google",
        json={"credential": "provider-signed-token"},
    )

    assert response.status_code == 401
    assert authenticated == []
