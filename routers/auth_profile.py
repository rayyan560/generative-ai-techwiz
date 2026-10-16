from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from src.security.auth import AuthManager


router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/update-profile")
async def api_update_profile(request: Request):
    user = AuthManager.get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    if user.get("role") == "judge":
        raise HTTPException(status_code=403, detail="Judge access is read-only.")

    try:
        body = await request.json()
        credentials = {
            "username": body.get("username"),
            "password": body.get("password"),
            "display_name": body.get("display_name"),
            "phone": body.get("phone"),
            "avatar": body.get("avatar"),
        }
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    try:
        updated = AuthManager.update_user_credentials(user_id=user["user_id"], **credentials)
        return JSONResponse({"success": True, "message": "Profile updated successfully.", "user": updated})
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
