import hmac
import hashlib
import time
import base64
import json
import logging
import os
import secrets
from typing import Optional, Dict, Any, List
from fastapi import Request
from config.settings import settings
# passlib replaced by direct bcrypt
from config.database import get_users_col

logger = logging.getLogger("SupportNova.Auth")

SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")
if not SESSION_SECRET_KEY:
    if os.getenv("RAILWAY_ENVIRONMENT_ID") or os.getenv("RENDER"):
        raise RuntimeError("SESSION_SECRET_KEY must be configured for hosted deployments.")
    SESSION_SECRET_KEY = secrets.token_urlsafe(48)
    logger.warning("A temporary local session secret was generated; sessions will expire after restart.")

SECRET_KEY = SESSION_SECRET_KEY

import bcrypt

def get_password_hash(password: str) -> str:
    """Hashes plain text password using native bcrypt directly."""
    if not password:
        return ""
    try:
        pw_bytes = password.strip().encode("utf-8")[:72]
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        return hashlib.sha256(password.strip().encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain text password against bcrypt hash, sha256, or plain text fallback."""
    if not plain_password or not hashed_password:
        return False
    clean_p = plain_password.strip()
    clean_h = hashed_password.strip()
    try:
        if clean_h.startswith("$2b$") or clean_h.startswith("$2a$") or clean_h.startswith("$2y$"):
            pw_bytes = clean_p.encode("utf-8")[:72]
            return bcrypt.checkpw(pw_bytes, clean_h.encode("utf-8"))
        if clean_h == hashlib.sha256(clean_p.encode()).hexdigest():
            return True
        return clean_p == clean_h or hmac.compare_digest(clean_p, clean_h)
    except Exception as e:
        logger.error(f"Password verification fallback error: {e}")
        return clean_p == clean_h

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

JUDGE_DEMO_USER = {
    "user_id": "USR-JUDGE-DEMO-001",
    "username": "judge",
    "email": "judge@supportnova.demo",
    "password": "judge2026",
    "role": "judge",
    "display_name": "Competition Judge",
    "designation": "Read-only project review",
    "auth_provider": "local",
    "phone": "",
    "created_at": "2026-10-01 00:00:00",
}

# These public credentials are deliberately non-privileged: both identities are
# judge/read-only users and are available only on an isolated preview service.
PUBLIC_DEMO_USERS = [
    {
        "user_id": "USR-PUBLIC-DEMO-ADMIN",
        "username": "demo_admin",
        "email": "demo_admin@supportnova.demo",
        "password": "AdminView2026!",
        "role": "judge",
        "demo_portal": "admin",
        "display_name": "Admin Portal Preview",
        "designation": "Public read-only demonstration",
        "auth_provider": "local",
        "phone": "",
        "created_at": "2026-10-02 00:00:00",
    },
    {
        "user_id": "USR-PUBLIC-DEMO-AGENT",
        "username": "demo_agent",
        "email": "demo_agent@supportnova.demo",
        "password": "AgentView2026!",
        "role": "judge",
        "demo_portal": "agent",
        "display_name": "Agent Dashboard Preview",
        "designation": "Public read-only demonstration",
        "auth_provider": "local",
        "phone": "",
        "created_at": "2026-10-02 00:00:00",
    },
]

PUBLIC_DEMO_PORTALS = {
    user["user_id"]: user["demo_portal"] for user in PUBLIC_DEMO_USERS
}

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
            if settings.DEMO_MODE:
                for u in DEFAULT_USERS:
                    existing = users_col.find_one({"username": u["username"]})
                    if not existing:
                        u_copy = dict(u)
                        u_copy["password"] = get_password_hash(u_copy["password"])
                        users_col.insert_one(u_copy)
                    elif not existing.get("password"):
                        users_col.update_one({"username": u["username"]}, {"$set": {"password": get_password_hash(u["password"])}})
            judge_copy = dict(JUDGE_DEMO_USER)
            existing_judge = users_col.find_one({"user_id": judge_copy["user_id"]})
            if not existing_judge:
                judge_copy["password"] = get_password_hash(judge_copy["password"])
                users_col.insert_one(judge_copy)
            else:
                users_col.update_one(
                    {"user_id": judge_copy["user_id"]},
                    {"$set": {
                        "username": judge_copy["username"],
                        "email": judge_copy["email"],
                        "password": get_password_hash(judge_copy["password"]),
                        "role": "judge",
                        "display_name": judge_copy["display_name"],
                    }},
                )

            if not settings.DEMO_MODE and settings.ADMIN_EMAIL and settings.ADMIN_PASSWORD:
                username = settings.ADMIN_EMAIL.split("@", 1)[0].replace(".", "_")
                existing = users_col.find_one({"email": settings.ADMIN_EMAIL})
                user_id = (existing or {}).get("user_id")
                if user_id in {"USR-ADMIN-001", "USR-AGENT-002", "USR-WARRANTY-003"}:
                    user_id = None
                profile = {
                    "user_id": user_id or f"USR-BOOTSTRAP-{int(time.time())}",
                    "username": username,
                    "email": settings.ADMIN_EMAIL,
                    "password": get_password_hash(settings.ADMIN_PASSWORD),
                    "role": "admin",
                    "display_name": (existing or {}).get("display_name") or username.replace("_", " ").title(),
                    "auth_provider": (existing or {}).get("auth_provider", "local"),
                    "phone": (existing or {}).get("phone", ""),
                    "created_at": (existing or {}).get("created_at") or time.strftime("%Y-%m-%d %H:%M:%S"),
                }
                if existing:
                    users_col.update_one({"email": settings.ADMIN_EMAIL}, {"$set": profile})
                else:
                    users_col.insert_one(profile)

            if not settings.DEMO_MODE and settings.AGENT_EMAIL and settings.AGENT_PASSWORD:
                username = settings.AGENT_EMAIL.split("@", 1)[0].replace(".", "_")
                existing = users_col.find_one({"email": settings.AGENT_EMAIL})
                user_id = (existing or {}).get("user_id")
                if user_id in {"USR-ADMIN-001", "USR-AGENT-002", "USR-WARRANTY-003"}:
                    user_id = None
                profile = {
                    "user_id": user_id or f"USR-AGENT-BOOTSTRAP-{int(time.time())}",
                    "username": username,
                    "email": settings.AGENT_EMAIL,
                    "password": get_password_hash(settings.AGENT_PASSWORD),
                    "role": "agent",
                    "display_name": (existing or {}).get("display_name") or username.replace("_", " ").title(),
                    "designation": (existing or {}).get("designation") or "Lead Triage & Hardware Forensic Specialist",
                    "avatar": (existing or {}).get("avatar") or "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=160&auto=format&fit=crop&q=80",
                    "auth_provider": (existing or {}).get("auth_provider", "local"),
                    "phone": (existing or {}).get("phone", ""),
                    "created_at": (existing or {}).get("created_at") or time.strftime("%Y-%m-%d %H:%M:%S"),
                }
                if existing:
                    users_col.update_one({"email": settings.AGENT_EMAIL}, {"$set": profile})
                else:
                    users_col.insert_one(profile)

            if settings.PUBLIC_DEMO_MODE:
                for demo_user in PUBLIC_DEMO_USERS:
                    existing = users_col.find_one({"user_id": demo_user["user_id"]})
                    username_owner = users_col.find_one({"username": demo_user["username"]})
                    if username_owner and username_owner.get("user_id") != demo_user["user_id"]:
                        raise RuntimeError(f"Reserved public demo username is already in use: {demo_user['username']}")
                    profile = dict(demo_user)
                    profile["password"] = get_password_hash(profile["password"])
                    if existing:
                        users_col.update_one({"user_id": demo_user["user_id"]}, {"$set": profile})
                    else:
                        users_col.insert_one(profile)
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
        demo_user_ids = {"USR-ADMIN-001", "USR-AGENT-002", "USR-WARRANTY-003"}
        if user and not settings.DEMO_MODE and user.get("user_id") in demo_user_ids:
            return None
        if settings.PUBLIC_DEMO_MODE and user and user.get("role") in {"admin", "agent", "warranty_manager"}:
            return None
        if user and user.get("user_id") in PUBLIC_DEMO_PORTALS:
            if (
                not settings.PUBLIC_DEMO_MODE
                or user.get("role") != "judge"
                or user.get("demo_portal") != PUBLIC_DEMO_PORTALS[user["user_id"]]
            ):
                return None
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
        role = "admin" if settings.ADMIN_EMAIL and clean_email == settings.ADMIN_EMAIL else "customer"

        if user:
            # Update user profile pic & display name from Google
            update_data = {
                "display_name": display_name or user.get("display_name"),
                "avatar": avatar or user.get("avatar"),
                "last_login": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            if google_id:
                update_data["google_id"] = google_id
            if role == "admin":
                update_data["role"] = "admin"
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
        if user_id == JUDGE_DEMO_USER["user_id"]:
            raise ValueError("Judge demo credentials are fixed and read-only.")

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
        if user_id == JUDGE_DEMO_USER["user_id"]:
            return False
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
            "demo_portal": user.get("demo_portal", ""),
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
            user = AuthManager.get_user_by_id(payload.get("user_id", ""))
            if not user:
                return None
            demo_user_ids = {"USR-ADMIN-001", "USR-AGENT-002", "USR-WARRANTY-003"}
            if not settings.DEMO_MODE and user.get("user_id") in demo_user_ids:
                return None
            if settings.PUBLIC_DEMO_MODE and user.get("role") in {"admin", "agent", "warranty_manager"}:
                return None
            if user.get("user_id") in PUBLIC_DEMO_PORTALS and (
                not settings.PUBLIC_DEMO_MODE
                or user.get("role") != "judge"
                or user.get("demo_portal") != PUBLIC_DEMO_PORTALS[user["user_id"]]
            ):
                return None
            return {
                "sub": user.get("username", ""),
                "username": user.get("username", ""),
                "user_id": user.get("user_id", ""),
                "email": user.get("email", ""),
                "role": user.get("role", "customer"),
                "display_name": user.get("display_name", user.get("username", "")),
                "avatar": user.get("avatar", ""),
                "auth_provider": user.get("auth_provider", "local"),
                "demo_portal": user.get("demo_portal", ""),
                "phone": user.get("phone", "")
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
