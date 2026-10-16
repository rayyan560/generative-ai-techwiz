import logging
import time
from typing import Any, Dict, List, Optional

from config.database import get_users_col
from src.security.auth_defaults import JUDGE_DEMO_USER
from src.security.auth_passwords import get_password_hash


logger = logging.getLogger("SupportNova.Auth")


def generate_google_avatar(name: str, email: str) -> str:
    clean_name = (name or email or "User").strip().replace(" ", "+")
    return f"https://ui-avatars.com/api/?name={clean_name}&background=4285F4&color=fff&size=160&bold=true&rounded=true"


def update_user_credentials(
    user_id: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    display_name: Optional[str] = None,
    phone: Optional[str] = None,
    avatar: Optional[str] = None,
) -> Dict[str, Any]:
    users = get_users_col()
    user = users.find_one({"user_id": user_id})
    if not user:
        raise ValueError("User not found.")
    if user_id == JUDGE_DEMO_USER["user_id"]:
        raise ValueError("Judge demo credentials are fixed and read-only.")
    updates = {}
    if username and username.strip():
        clean_username = username.strip().lower()
        if clean_username != user.get("username"):
            if users.find_one({"username": clean_username}):
                raise ValueError(f"Username '{clean_username}' is already taken.")
            updates["username"] = clean_username
    if password and password.strip():
        updates["password"] = get_password_hash(password.strip())
    if display_name and display_name.strip():
        updates["display_name"] = display_name.strip()
    if phone is not None:
        updates["phone"] = phone.strip()
    if avatar and avatar.strip():
        updates["avatar"] = avatar.strip()
    if updates:
        users.update_one({"user_id": user_id}, {"$set": updates})
        user.update(updates)
    return user


def get_all_users() -> List[Dict[str, Any]]:
    from src.security.auth_bootstrap import initialize_default_users

    initialize_default_users()
    cleaned = []
    for user in get_users_col().find():
        profile = dict(user)
        profile.pop("password", None)
        if "_id" in profile:
            profile["_id"] = str(profile["_id"])
        cleaned.append(profile)
    return cleaned
