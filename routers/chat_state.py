import secrets
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, Response

from src.security.auth import AuthManager


STAFF_PRESENCE = {
    "admin": {"name": "Administrator", "role": "Administrator", "online": False, "avatar": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=160&auto=format&fit=crop&q=80"},
    "agent": {"name": "Support Agent", "role": "Triage Specialist", "online": False, "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=160&auto=format&fit=crop&q=80"},
    "warranty_manager": {"name": "Warranty Manager", "role": "Warranty Officer", "online": False, "avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=160&auto=format&fit=crop&q=80"},
}

ACTIVE_CALLS: Dict[str, Dict[str, Any]] = {}


def get_call_client_context(request: Request):
    user = AuthManager.get_current_user(request)
    if user:
        return user.get("user_id", "guest"), user.get("display_name") or user.get("username") or "Customer", None
    guest_id = request.cookies.get("supportnova_guest_id")
    new_guest_id = None
    if not guest_id or len(guest_id) > 80:
        guest_id = secrets.token_urlsafe(24)
        new_guest_id = guest_id
    return f"guest:{guest_id}", "Guest customer", new_guest_id


def set_guest_call_cookie(response: Response, guest_id: Optional[str], request: Request):
    if guest_id:
        response.set_cookie(
            "supportnova_guest_id",
            guest_id,
            max_age=60 * 60 * 24 * 365,
            httponly=True,
            secure=request.url.scheme == "https",
            samesite="lax",
            path="/",
        )


def reject_read_only_judge(user):
    if user and user.get("role") == "judge":
        raise HTTPException(status_code=403, detail="Judge access is read-only.")
