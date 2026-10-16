import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from config.settings import settings
from src.security.auth import AuthManager


logger = logging.getLogger("SupportNova.AuthSessions")
router = APIRouter(prefix="/api/auth", tags=["Auth"])


def _session_response(user, message=None):
    response_user = {
        "user_id": user.get("user_id"),
        "username": user.get("username"),
        "email": user.get("email"),
        "display_name": user.get("display_name"),
        "avatar": user.get("avatar"),
        "role": user.get("role"),
        "auth_provider": user.get("auth_provider"),
        "demo_portal": user.get("demo_portal"),
    }
    token = AuthManager.create_session_token(user)
    response = {"success": True, "user": response_user, "token": token}
    if message:
        response["message"] = message
    result = JSONResponse(response)
    result.set_cookie(
        key="supportnova_session",
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        max_age=7 * 86400,
        samesite="lax",
    )
    return result


@router.post("/login")
async def api_login(request: Request):
    try:
        body = await request.json()
        identifier = body.get("identifier") or body.get("username") or ""
        password = body.get("password") or ""
    except Exception:
        logger.warning("Invalid login JSON payload.")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    user = AuthManager.authenticate_user(identifier, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return _session_response(user)


@router.post("/register")
async def api_register(request: Request):
    try:
        body = await request.json()
        username = body.get("username", "").strip()
        email = body.get("email", "").strip()
        password = body.get("password", "").strip()
        display_name = body.get("display_name", "").strip()
        phone = body.get("phone", "").strip()
        avatar = body.get("avatar", "").strip()
    except Exception:
        logger.warning("Invalid registration JSON payload.")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if not username or not email or not password:
        raise HTTPException(status_code=400, detail="Username, email, and password are required.")

    try:
        user = AuthManager.register_user(
            username=username,
            email=email,
            password=password,
            display_name=display_name,
            phone=phone,
            avatar=avatar,
        )
        return _session_response(user, "Account created successfully.")
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.get("/me")
async def api_me(request: Request):
    user = AuthManager.get_current_user(request)
    if not user:
        return JSONResponse({"authenticated": False, "user": None})
    return JSONResponse({
        "authenticated": True,
        "user": {
            "user_id": user.get("user_id"),
            "username": user.get("username"),
            "email": user.get("email"),
            "display_name": user.get("display_name"),
            "avatar": user.get("avatar"),
            "role": user.get("role"),
            "auth_provider": user.get("auth_provider"),
        },
    })


@router.get("/logout")
async def api_logout():
    response = JSONResponse({"success": True, "message": "Logged out successfully."})
    response.delete_cookie("supportnova_session")
    return response
