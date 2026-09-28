from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
import logging

from src.security.auth import AuthManager

logger = logging.getLogger("SupportNova.AuthRouter")

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/login")
async def api_login(request: Request):
    try:
        body = await request.json()
        identifier = body.get("identifier") or body.get("username") or ""
        password = body.get("password") or ""
    except Exception as e:
        logger.warning(f"Invalid login JSON payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    user = AuthManager.authenticate_user(identifier, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = AuthManager.create_session_token(user)
    res = JSONResponse({
        "success": True,
        "user": {
            "user_id": user.get("user_id"),
            "username": user.get("username"),
            "email": user.get("email"),
            "display_name": user.get("display_name"),
            "avatar": user.get("avatar"),
            "role": user.get("role"),
            "auth_provider": user.get("auth_provider")
        },
        "token": token
    })
    res.set_cookie(key="supportnova_session", value=token, httponly=True, max_age=7*86400, samesite="lax")
    return res

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
    except Exception as e:
        logger.warning(f"Invalid registration JSON payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if not username or not email or not password:
        raise HTTPException(status_code=400, detail="Username, email, and password are required.")

    try:
        new_user = AuthManager.register_user(
            username=username,
            email=email,
            password=password,
            display_name=display_name,
            phone=phone,
            avatar=avatar
        )
        token = AuthManager.create_session_token(new_user)
        res = JSONResponse({
            "success": True,
            "message": "Account created successfully.",
            "user": {
                "user_id": new_user.get("user_id"),
                "username": new_user.get("username"),
                "email": new_user.get("email"),
                "display_name": new_user.get("display_name"),
                "avatar": new_user.get("avatar"),
                "role": new_user.get("role")
            },
            "token": token
        })
        res.set_cookie(key="supportnova_session", value=token, httponly=True, max_age=7*86400, samesite="lax")
        return res
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))

@router.post("/google")
async def api_google_login(request: Request):
    try:
        body = await request.json()
        credential = body.get("credential")
        email = body.get("email", "").strip()
        name = body.get("name", "").strip()
        picture = body.get("picture", "").strip()
        google_id = body.get("sub", "").strip()

        if credential:
            try:
                import base64
                parts = credential.split(".")
                if len(parts) >= 2:
                    payload_raw = base64.b64decode(parts[1] + "==").decode("utf-8")
                    import json
                    g_payload = json.loads(payload_raw)
                    email = g_payload.get("email") or email
                    name = g_payload.get("name") or name
                    picture = g_payload.get("picture") or picture
                    google_id = g_payload.get("sub") or google_id
            except Exception as e:
                logger.warning(f"Error parsing Google credential token: {e}")
    except Exception as e:
        logger.warning(f"Invalid Google login payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid Google payload")

    if not email:
        raise HTTPException(status_code=400, detail="Valid Gmail address is required for Google Sign-in.")

    user = AuthManager.authenticate_google_user(
        email=email,
        display_name=name,
        avatar=picture,
        google_id=google_id
    )

    token = AuthManager.create_session_token(user)
    res = JSONResponse({
        "success": True,
        "message": f"Successfully authenticated with Google as {user.get('email')}",
        "user": {
            "user_id": user.get("user_id"),
            "username": user.get("username"),
            "email": user.get("email"),
            "display_name": user.get("display_name"),
            "avatar": user.get("avatar"),
            "role": user.get("role"),
            "auth_provider": user.get("auth_provider")
        },
        "token": token
    })
    res.set_cookie(key="supportnova_session", value=token, httponly=True, max_age=7*86400, samesite="lax")
    return res

@router.post("/update-profile")
async def api_update_profile(request: Request):
    user = AuthManager.get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    
    try:
        body = await request.json()
        username = body.get("username")
        password = body.get("password")
        display_name = body.get("display_name")
        phone = body.get("phone")
        avatar = body.get("avatar")
    except Exception as e:
        logger.warning(f"Invalid update-profile JSON payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    try:
        updated = AuthManager.update_user_credentials(
            user_id=user["user_id"],
            username=username,
            password=password,
            display_name=display_name,
            phone=phone,
            avatar=avatar
        )
        return JSONResponse({"success": True, "message": "Profile updated successfully.", "user": updated})
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))

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
            "auth_provider": user.get("auth_provider")
        }
    })

@router.get("/logout")
async def api_logout():
    res = JSONResponse({"success": True, "message": "Logged out successfully."})
    res.delete_cookie("supportnova_session")
    return res
