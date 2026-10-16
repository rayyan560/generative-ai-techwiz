import logging
import time
from typing import Any, Dict

from config.database import get_users_col
from src.security.auth_bootstrap import initialize_default_users
from src.security.auth_passwords import get_password_hash
from src.security.auth_profile import generate_google_avatar


logger = logging.getLogger("SupportNova.Auth")


def register_user(
    username: str,
    email: str,
    password: str,
    display_name: str,
    phone: str = "",
    avatar: str = "",
    role: str = "customer",
) -> Dict[str, Any]:
    initialize_default_users()
    users = get_users_col()
    clean_username = username.strip().lower()
    clean_email = email.strip().lower()
    if users.find_one({"username": clean_username}):
        raise ValueError(f"Username '{clean_username}' is already taken.")
    if users.find_one({"email": clean_email}):
        raise ValueError(f"Email '{clean_email}' is already registered.")
    avatar = avatar or generate_google_avatar(display_name, clean_email)
    user = {
        "user_id": f"USR-{int(time.time())}",
        "username": clean_username,
        "email": clean_email,
        "password": get_password_hash(password),
        "role": role,
        "display_name": display_name.strip() or clean_username.title(),
        "avatar": avatar,
        "auth_provider": "local",
        "phone": phone.strip(),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "last_login": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    get_users_col().insert_one(user)
    logger.info("User registered successfully: %s (%s)", clean_username, clean_email)
    return user
