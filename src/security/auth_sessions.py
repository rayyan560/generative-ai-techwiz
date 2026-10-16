import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
import time
from typing import Any, Dict, Optional

from fastapi import Request

from config.settings import settings
from src.security.auth_defaults import PUBLIC_DEMO_PORTALS, _is_valid_public_demo_user
from src.security.auth_lookup import get_user_by_id


logger = logging.getLogger("SupportNova.Auth")
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")
if not SESSION_SECRET_KEY:
    if os.getenv("RAILWAY_ENVIRONMENT_ID") or os.getenv("RENDER"):
        raise RuntimeError("SESSION_SECRET_KEY must be configured for hosted deployments.")
    SESSION_SECRET_KEY = secrets.token_urlsafe(48)
    logger.warning("A temporary local session secret was generated; sessions will expire after restart.")
SECRET_KEY = SESSION_SECRET_KEY
_DEMO_SEED_USER_IDS = {"USR-ADMIN-001", "USR-AGENT-002", "USR-WARRANTY-003"}


def create_session_token(user: Dict[str, Any]) -> str:
    payload = {
        "sub": user.get("username", ""),
        "user_id": user.get("user_id", ""),
        "email": user.get("email", ""),
        "role": user.get("role", "customer"),
        "display_name": user.get("display_name", user.get("username", "")),
        "avatar": user.get("avatar", ""),
        "auth_provider": user.get("auth_provider", "local"),
        "demo_portal": user.get("demo_portal", ""),
        "exp": int(time.time()) + (7 * 24 * 3600),
    }
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
    signature = hmac.new(SECRET_KEY.encode(), encoded.encode(), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def verify_session_token(token: str) -> Optional[Dict[str, Any]]:
    if not token or "." not in token:
        return None
    try:
        encoded, signature = token.split(".", 1)
        expected = hmac.new(SECRET_KEY.encode(), encoded.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return None
        payload = json.loads(base64.urlsafe_b64decode(encoded.encode()).decode())
        if payload.get("exp", 0) < time.time():
            return None
        user = get_user_by_id(payload.get("user_id", ""))
        if not user:
            return None
        user_id = user.get("user_id")
        if not settings.DEMO_MODE and user_id in _DEMO_SEED_USER_IDS:
            return None
        if user_id in PUBLIC_DEMO_PORTALS and not _is_valid_public_demo_user(user):
            return None
        if settings.PUBLIC_DEMO_MODE and user.get("role") in {"admin", "agent", "warranty_manager"}:
            if not _is_valid_public_demo_user(user):
                return None
        return {
            "sub": user.get("username", ""),
            "username": user.get("username", ""),
            "user_id": user_id,
            "email": user.get("email", ""),
            "role": user.get("role", "customer"),
            "display_name": user.get("display_name", user.get("username", "")),
            "avatar": user.get("avatar", ""),
            "auth_provider": user.get("auth_provider", "local"),
            "demo_portal": user.get("demo_portal", ""),
            "phone": user.get("phone", ""),
        }
    except Exception as error:
        logger.error("Token verification error: %s", error)
        return None


def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    token = request.cookies.get("supportnova_session")
    if not token:
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
    return verify_session_token(token) if token else None
