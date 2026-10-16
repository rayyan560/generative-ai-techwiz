import logging
from typing import Any, Dict, Optional

from config.database import get_users_col
from config.settings import settings
from src.security.auth_bootstrap import initialize_default_users
from src.security.auth_defaults import PUBLIC_DEMO_PORTALS, _is_valid_public_demo_user
from src.security.auth_passwords import get_password_hash, verify_password


logger = logging.getLogger("SupportNova.Auth")
_DEMO_SEED_USER_IDS = {"USR-ADMIN-001", "USR-AGENT-002", "USR-WARRANTY-003"}


def get_user_by_identifier(identifier: str) -> Optional[Dict[str, Any]]:
    initialize_default_users()
    users = get_users_col()
    clean_identifier = (identifier or "").strip().lower()
    if not clean_identifier:
        return None
    user = users.find_one({"username": clean_identifier}) or users.find_one({"email": clean_identifier})
    if user:
        return user
    for candidate in users.find():
        if candidate.get("username", "").lower() == clean_identifier or candidate.get("email", "").lower() == clean_identifier:
            return candidate
    return None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    if not user_id:
        return None
    return get_users_col().find_one({"user_id": user_id})


def authenticate_user(identifier: str, password: str) -> Optional[Dict[str, Any]]:
    user = get_user_by_identifier(identifier)
    if user and not settings.DEMO_MODE and user.get("user_id") in _DEMO_SEED_USER_IDS:
        return None
    if user and user.get("user_id") in PUBLIC_DEMO_PORTALS:
        if not _is_valid_public_demo_user(user):
            return None
    elif settings.PUBLIC_DEMO_MODE and user and user.get("role") in {"admin", "agent", "warranty_manager"}:
        if not _is_valid_public_demo_user(user):
            return None
    if user and verify_password(password, user.get("password", "")):
        password_hash = user.get("password", "")
        if not password_hash.startswith(("$2b$", "$2a$")):
            try:
                new_hash = get_password_hash(password)
                get_users_col().update_one({"user_id": user.get("user_id")}, {"$set": {"password": new_hash}})
                user["password"] = new_hash
            except Exception as error:
                logger.warning("Could not update legacy password hash: %s", error)
        return user
    return None
