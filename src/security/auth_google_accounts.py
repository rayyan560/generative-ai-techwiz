import logging
import time
from typing import Any, Dict, Optional

from config.database import get_users_col
from config.settings import settings
from src.security.auth_bootstrap import initialize_default_users
from src.security.auth_profile import generate_google_avatar


logger = logging.getLogger("SupportNova.Auth")


def authenticate_google_user(
    email: str,
    display_name: str,
    avatar: Optional[str] = None,
    google_id: Optional[str] = None,
) -> Dict[str, Any]:
    initialize_default_users()
    users = get_users_col()
    clean_email = email.strip().lower()
    user = users.find_one({"email": clean_email})
    if not avatar or "placeholder" in avatar:
        avatar = generate_google_avatar(display_name, clean_email)
    role = "admin" if settings.ADMIN_EMAIL and clean_email == settings.ADMIN_EMAIL else "customer"
    if user:
        updates = {
            "display_name": display_name or user.get("display_name"),
            "avatar": avatar or user.get("avatar"),
            "last_login": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        if google_id:
            updates["google_id"] = google_id
        if role == "admin":
            updates["role"] = "admin"
        users.update_one({"email": clean_email}, {"$set": updates})
        user.update(updates)
        return user
    username = clean_email.split("@", 1)[0].replace(".", "_")
    if users.find_one({"username": username}):
        username = f"{username}_{int(time.time()) % 10000}"
    created_user = {
        "user_id": f"USR-GGL-{int(time.time())}",
        "username": username,
        "email": clean_email,
        "password": "",
        "role": role,
        "display_name": display_name or clean_email.split("@")[0].title(),
        "avatar": avatar,
        "auth_provider": "google",
        "google_id": google_id,
        "phone": "",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "last_login": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    users.insert_one(created_user)
    logger.info("New Google user registered: %s with role %s", clean_email, role)
    return created_user
