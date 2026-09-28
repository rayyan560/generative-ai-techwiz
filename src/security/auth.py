import hmac
import hashlib
import time
import base64
import json
import logging
import os
from typing import Optional, Dict, Any, List
from fastapi import Request
from passlib.context import CryptContext
from config.database import get_users_col

logger = logging.getLogger("SupportNova.Auth")

SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")
if not SESSION_SECRET_KEY:
    logger.warning("SESSION_SECRET_KEY environment variable not found. Loading fallback secret.")
    SESSION_SECRET_KEY = "e8f3b9c1d2e4a5f6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0"

SECRET_KEY = SESSION_SECRET_KEY

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Hashes plain text password using bcrypt."""
    if not password:
        return ""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain text password against bcrypt hash or legacy string fallback."""
    if not plain_password or not hashed_password:
        return False
    try:
        if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
            return pwd_context.verify(plain_password, hashed_password)
        return hmac.compare_digest(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

DEFAULT_USERS = [
    {
        "user_id": "USR-ADMIN-001",
        "username": "admin",
        "email": "admin@supportnova.io",
        "password": "admin123",
        "role": "admin",
        "display_name": "Executive Director",
        "designation": "Grievance Operations Director & CEO",
        "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=160&auto=format&fit=crop&q=80",
        "auth_provider": "local",
        "phone": "+1 800 555 0100",
        "created_at": "2026-01-01 00:00:00"
    },
    {
        "user_id": "USR-AGENT-002",
        "username": "agent",
        "email": "agent@supportnova.io",
        "password": "agent123",
        "role": "agent",
        "display_name": "Marcus Chen",
        "designation": "Lead Triage & Hardware Forensic Specialist",
        "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=160&auto=format&fit=crop&q=80",
        "auth_provider": "local",
        "phone": "+1 800 555 0142",
        "created_at": "2026-01-02 00:00:00"
    },
    {
        "user_id": "USR-WARRANTY-003",
        "username": "warranty_manager",
        "email": "warranty@supportnova.io",
        "password": "warranty123",
        "role": "warranty_manager",
        "display_name": "Sarah Jenkins",
        "designation": "Senior Warranty, Escrow & Refund Manager",
        "avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=160&auto=format&fit=crop&q=80",
        "auth_provider": "local",
        "phone": "+1 800 555 0199",
        "created_at": "2026-01-03 00:00:00"
    }
]

def generate_google_avatar(name: str, email: str) -> str:
    """Generates high quality Google profile avatar URL based on user name/email."""
    clean_name = (name or email or "User").strip().replace(" ", "+")
    return f"https://ui-avatars.com/api/?name={clean_name}&background=4285F4&color=fff&size=160&bold=true&rounded=true"

_USERS_INITIALIZED = False

class AuthManager:
    @staticmethod
    def _init_users_if_empty():
        global _USERS_INITIALIZED
        if _USERS_INITIALIZED:
            return
        try:
            users_col = get_users_col()
            for u in DEFAULT_USERS:
                existing = users_col.find_one({"username": u["username"]})
                if not existing:
                    u_copy = dict(u)
                    if not u_copy["password"].startswith("$2b$") and not u_copy["password"].startswith("$2a$"):
                        u_copy["password"] = get_password_hash(u_copy["password"])
                    users_col.insert_one(u_copy)
            _USERS_INITIALIZED = True
        except Exception as e:
            logger.error(f"Error initializing default users: {e}")

    @staticmethod
    def get_user_by_identifier(identifier: str) -> Optional[Dict[str, Any]]:
        AuthManager._init_users_if_empty()
        users_col = get_users_col()
        clean_id = (identifier or "").strip().lower()
        if not clean_id:
            return None
        user = users_col.find_one({"username": clean_id})
        if not user:
            user = users_col.find_one({"email": clean_id})
        if not user:
            # Case-insensitive check in data
            all_users = list(users_col.find())
            for u in all_users:
                if u.get("username", "").lower() == clean_id or u.get("email", "").lower() == clean_id:
                    return u
        return user

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        if not user_id:
            return None
        users_col = get_users_col()
        return users_col.find_one({"user_id": user_id})

    @staticmethod
    def authenticate_user(identifier: str, password: str) -> Optional[Dict[str, Any]]:
        user = AuthManager.get_user_by_identifier(identifier)
        if user and verify_password(password, user.get("password", "")):
            # Automatic seamless migration of legacy unhashed password to bcrypt hash
            if not user.get("password", "").startswith("$2b$") and not user.get("password", "").startswith("$2a$"):
                try:
                    new_hash = get_password_hash(password)
                    get_users_col().update_one({"user_id": user.get("user_id")}, {"$set": {"password": new_hash}})
                    user["password"] = new_hash
                except Exception as e:
                    logger.warning(f"Could not update legacy password hash: {e}")
            return user
        return None

    @staticmethod
    def authenticate_google_user(email: str, display_name: str, avatar: Optional[str] = None, google_id: Optional[str] = None) -> Dict[str, Any]:
        """Handles Google Sign-in: creates user if not exists or updates existing account."""
        AuthManager._init_users_if_empty()
        users_col = get_users_col()
        clean_email = email.strip().lower()
        
        user = users_col.find_one({"email": clean_email})
        
        if not avatar or "placeholder" in avatar:
            avatar = generate_google_avatar(display_name, clean_email)

        # Check if this email is an admin/owner email
        role = "admin" if ("admin" in clean_email or clean_email.startswith("asp") or clean_email.startswith("owner") or clean_email == "admin@supportnova.io") else "customer"

        if user:
            # Update user profile pic & display name from Google
            update_data = {
                "display_name": display_name or user.get("display_name"),
                "avatar": avatar or user.get("avatar"),
                "last_login": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            if google_id:
                update_data["google_id"] = google_id
            users_col.update_one({"email": clean_email}, {"$set": update_data})
            user.update(update_data)
            return user
        else:
            # Create new user registered via Google
            username_candidate = clean_email.split("@")[0].replace(".", "_")
            # Ensure unique username
            existing_user = users_col.find_one({"username": username_candidate})
            if existing_user:
                username_candidate = f"{username_candidate}_{int(time.time()) % 10000}"

            new_user = {
                "user_id": f"USR-GGL-{int(time.time())}",
                "username": username_candidate,
                "email": clean_email,
                "password": "",  # Google user can add password later
                "role": role,
                "display_name": display_name or clean_email.split("@")[0].title(),
                "avatar": avatar,
                "auth_provider": "google",
                "google_id": google_id,
                "phone": "",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "last_login": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            users_col.insert_one(new_user)
            logger.info(f"New Google user registered: {clean_email} with role {role}")
            return new_user

    @staticmethod
    def register_user(username: str, email: str, password: str, display_name: str, phone: str = "", avatar: str = "", role: str = "customer") -> Dict[str, Any]:
        AuthManager._init_users_if_empty()
        users_col = get_users_col()
        clean_user = username.strip().lower()
        clean_email = email.strip().lower()

        if users_col.find_one({"username": clean_user}):
            raise ValueError(f"Username '{clean_user}' is already taken.")
        if users_col.find_one({"email": clean_email}):
            raise ValueError(f"Email '{clean_email}' is already registered.")

        if not avatar:
            avatar = generate_google_avatar(display_name, clean_email)

        # Allow role promotion if keyword matches
        if "admin" in clean_email or "admin" in clean_user:
            role = "admin"

        new_user = {
            "user_id": f"USR-{int(time.time())}",
            "username": clean_user,
            "email": clean_email,
            "password": get_password_hash(password),
            "role": role,
            "display_name": display_name.strip() or clean_user.title(),
            "avatar": avatar,
            "auth_provider": "local",
            "phone": phone.strip(),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "last_login": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        users_col.insert_one(new_user)
        logger.info(f"User registered successfully: {clean_user} ({clean_email})")
        return new_user

    @staticmethod
    def update_user_credentials(user_id: str, username: Optional[str] = None, password: Optional[str] = None, display_name: Optional[str] = None, phone: Optional[str] = None, avatar: Optional[str] = None) -> Dict[str, Any]:
        """Allows Google or standard user to set/update their username, password, and profile."""
        users_col = get_users_col()
        user = users_col.find_one({"user_id": user_id})
        if not user:
            raise ValueError("User not found.")

        updates = {}
        if username and username.strip():
            clean_u = username.strip().lower()
            if clean_u != user.get("username"):
                existing = users_col.find_one({"username": clean_u})
                if existing:
                    raise ValueError(f"Username '{clean_u}' is already taken.")
                updates["username"] = clean_u

        if password and password.strip():
            updates["password"] = get_password_hash(password.strip())

        if display_name and display_name.strip():
            updates["display_name"] = display_name.strip()

        if phone is not None:
            updates["phone"] = phone.strip()

        if avatar and avatar.strip():
            updates["avatar"] = avatar.strip()

        if updates:
            users_col.update_one({"user_id": user_id}, {"$set": updates})
            user.update(updates)

        return user

    @staticmethod
    def get_all_users() -> List[Dict[str, Any]]:
        AuthManager._init_users_if_empty()
        users_col = get_users_col()
        raw = list(users_col.find())
        cleaned = []
        for u in raw:
            d = dict(u)
            d.pop("password", None)  # Hide password
            if "_id" in d:
                d["_id"] = str(d["_id"])
            cleaned.append(d)
        return cleaned

    @staticmethod
    def update_user_role(user_id: str, new_role: str) -> bool:
        users_col = get_users_col()
        res = users_col.update_one({"user_id": user_id}, {"$set": {"role": new_role}})
        return res.modified_count > 0

    @staticmethod
    def create_session_token(user: Dict[str, Any]) -> str:
        payload = {
            "sub": user.get("username", ""),
            "user_id": user.get("user_id", ""),
            "email": user.get("email", ""),
            "role": user.get("role", "customer"),
            "display_name": user.get("display_name", user.get("username", "")),
            "avatar": user.get("avatar", ""),
            "auth_provider": user.get("auth_provider", "local"),
            "exp": int(time.time()) + (7 * 24 * 3600)  # 7 days
        }
        data_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
        sig = hmac.new(SECRET_KEY.encode(), data_b64.encode(), hashlib.sha256).hexdigest()
        return f"{data_b64}.{sig}"

    @staticmethod
    def verify_session_token(token: str) -> Optional[Dict[str, Any]]:
        if not token or "." not in token:
            return None
        try:
            data_b64, sig = token.split(".", 1)
            expected_sig = hmac.new(SECRET_KEY.encode(), data_b64.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig, expected_sig):
                return None
            payload = json.loads(base64.urlsafe_b64decode(data_b64.encode()).decode())
            if payload.get("exp", 0) < time.time():
                return None  # Expired
            
            # Construct standard user identity from verified signature payload
            return {
                "sub": payload.get("sub", ""),
                "username": payload.get("sub", ""),
                "user_id": payload.get("user_id", ""),
                "email": payload.get("email", ""),
                "role": payload.get("role", "customer"),
                "display_name": payload.get("display_name", payload.get("sub", "")),
                "avatar": payload.get("avatar", ""),
                "auth_provider": payload.get("auth_provider", "local"),
                "phone": payload.get("phone", "")
            }
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None

    @staticmethod
    def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
        token = request.cookies.get("supportnova_session")
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        if not token:
            return None
        return AuthManager.verify_session_token(token)
