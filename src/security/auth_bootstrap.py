import logging
import time
from typing import Any, Dict

from config.database import get_users_col
from config.settings import settings
from src.security.auth_defaults import DEFAULT_USERS, JUDGE_DEMO_USER, PUBLIC_DEMO_USERS
from src.security.auth_passwords import get_password_hash


logger = logging.getLogger("SupportNova.Auth")
_USERS_INITIALIZED = False
_DEMO_SEED_USER_IDS = {"USR-ADMIN-001", "USR-AGENT-002", "USR-WARRANTY-003"}


def initialize_default_users() -> None:
    global _USERS_INITIALIZED
    if _USERS_INITIALIZED:
        return
    try:
        users = get_users_col()
        if settings.DEMO_MODE:
            for user in DEFAULT_USERS:
                existing = users.find_one({"username": user["username"]})
                if not existing:
                    profile = dict(user)
                    profile["password"] = get_password_hash(profile["password"])
                    users.insert_one(profile)
                elif not existing.get("password"):
                    users.update_one(
                        {"username": user["username"]},
                        {"$set": {"password": get_password_hash(user["password"])}},
                    )

        judge = dict(JUDGE_DEMO_USER)
        existing_judge = users.find_one({"user_id": judge["user_id"]})
        if not existing_judge:
            judge["password"] = get_password_hash(judge["password"])
            users.insert_one(judge)
        else:
            users.update_one(
                {"user_id": judge["user_id"]},
                {"$set": {
                    "username": judge["username"],
                    "email": judge["email"],
                    "password": get_password_hash(judge["password"]),
                    "role": "judge",
                    "display_name": judge["display_name"],
                }},
            )

        _bootstrap_privileged_user(users, settings.ADMIN_EMAIL, settings.ADMIN_PASSWORD, "admin")
        _bootstrap_privileged_user(users, settings.AGENT_EMAIL, settings.AGENT_PASSWORD, "agent")

        if settings.PUBLIC_DEMO_MODE:
            for user in PUBLIC_DEMO_USERS:
                existing = users.find_one({"user_id": user["user_id"]})
                username_owner = users.find_one({"username": user["username"]})
                if username_owner and username_owner.get("user_id") != user["user_id"]:
                    raise RuntimeError(f"Reserved public demo username is already in use: {user['username']}")
                profile = dict(user)
                profile["password"] = get_password_hash(profile["password"])
                if existing:
                    users.update_one({"user_id": user["user_id"]}, {"$set": profile})
                else:
                    users.insert_one(profile)
        _USERS_INITIALIZED = True
    except Exception as error:
        logger.error("Error initializing default users: %s", error)


def _bootstrap_privileged_user(users, email: str, password: str, role: str) -> None:
    if settings.DEMO_MODE or not email or not password:
        return
    username = email.split("@", 1)[0].replace(".", "_")
    existing = users.find_one({"email": email})
    user_id = (existing or {}).get("user_id")
    if user_id in _DEMO_SEED_USER_IDS:
        user_id = None
    bootstrap_id = "USR-BOOTSTRAP" if role == "admin" else "USR-AGENT-BOOTSTRAP"
    profile: Dict[str, Any] = {
        "user_id": user_id or f"{bootstrap_id}-{int(time.time())}",
        "username": username,
        "email": email,
        "password": get_password_hash(password),
        "role": role,
        "display_name": (existing or {}).get("display_name") or username.replace("_", " ").title(),
        "auth_provider": (existing or {}).get("auth_provider", "local"),
        "phone": (existing or {}).get("phone", ""),
        "created_at": (existing or {}).get("created_at") or time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    if role == "agent":
        profile.update({
            "designation": (existing or {}).get("designation") or "Lead Triage & Hardware Forensic Specialist",
            "avatar": (existing or {}).get("avatar") or "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=160&auto=format&fit=crop&q=80",
        })
    if existing:
        users.update_one({"email": email}, {"$set": profile})
    else:
        users.insert_one(profile)
