from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
import logging

from src.security.auth import AuthManager
from config.database import get_audit_logs_col, get_rules_col
from routers.common import clean_docs

logger = logging.getLogger("SupportNova.AdminRouter")

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.get("/users")
async def list_admin_users(request: Request):
    user = AuthManager.get_current_user(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin role required.")
    
    users = AuthManager.get_all_users()
    clean_u = []
    for u in users:
        clean_u.append({
            "user_id": u.get("user_id"),
            "username": u.get("username"),
            "email": u.get("email"),
            "display_name": u.get("display_name"),
            "role": u.get("role"),
            "created_at": u.get("created_at"),
            "last_login": u.get("last_login"),
            "auth_provider": u.get("auth_provider", "local")
        })
    return JSONResponse({"success": True, "users": clean_u})

@router.post("/users/{user_id}/role")
async def update_user_role(user_id: str, request: Request):
    user = AuthManager.get_current_user(request)
    if not user or user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin role required.")
    
    try:
        body = await request.json()
        new_role = body.get("role")
    except Exception as e:
        logger.warning(f"Invalid role update JSON: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if new_role not in ["customer", "agent", "warranty", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role specified.")

    updated = AuthManager.update_user_role(user_id, new_role)
    if not updated:
        raise HTTPException(status_code=44, detail="User not found.")

    return JSONResponse({"success": True, "message": f"User role updated to {new_role}", "user": updated})
