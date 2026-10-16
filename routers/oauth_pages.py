import json
import logging
import secrets
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from config.settings import settings
from src.security.auth import AuthManager

router = APIRouter(tags=["Authentication Pages"])
logger = logging.getLogger("SupportNova.OAuthPages")

@router.get("/auth/google/login")
async def google_oauth_login():
    if settings.GOOGLE_CLIENT_ID:
        import urllib.parse
        state = secrets.token_urlsafe(32)
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": f"{settings.BASE_URL}/auth/google/callback",
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "select_account",
            "state": state
        }
        google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
        response = RedirectResponse(url=google_auth_url, status_code=302)
        response.set_cookie(
            "google_oauth_state", state, httponly=True,
            secure=settings.COOKIE_SECURE, max_age=600, samesite="lax"
        )
        return response
    else:
        return RedirectResponse(url="/login?google_prompt=true", status_code=302)

@router.get("/auth/google/callback")
async def google_oauth_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None
):
    expected_state = request.cookies.get("google_oauth_state", "")
    if not state or not expected_state or not secrets.compare_digest(state, expected_state):
        return RedirectResponse(url="/login?error=Invalid%20Google%20sign-in%20state", status_code=302)
    if error or not code:
        response = RedirectResponse(url="/login?error=Google%20authorization%20cancelled", status_code=302)
        response.delete_cookie("google_oauth_state")
        return response

    try:
        import urllib.request
        import urllib.parse

        token_url = "https://oauth2.googleapis.com/token"
        token_data = urllib.parse.urlencode({
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": f"{settings.BASE_URL}/auth/google/callback",
            "grant_type": "authorization_code"
        }).encode("utf-8")

        req = urllib.request.Request(token_url, data=token_data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

        with urllib.request.urlopen(req) as resp:
            token_json = json.loads(resp.read().decode("utf-8"))
            access_token = token_json.get("access_token")

        if not access_token:
            return RedirectResponse(url="/login?error=Failed to obtain Google access token", status_code=302)

        userinfo_req = urllib.request.Request("https://www.googleapis.com/oauth2/v3/userinfo")
        userinfo_req.add_header("Authorization", f"Bearer {access_token}")

        with urllib.request.urlopen(userinfo_req) as resp:
            userinfo = json.loads(resp.read().decode("utf-8"))

        email = userinfo.get("email")
        if not email or not userinfo.get("email_verified"):
            raise ValueError("Google account email is not verified.")
        name = userinfo.get("name") or email.split("@")[0].title()
        picture = userinfo.get("picture")
        sub = userinfo.get("sub")

        user = AuthManager.authenticate_google_user(
            email=email,
            display_name=name,
            avatar=picture,
            google_id=sub
        )

        token = AuthManager.create_session_token(user)
        target = {"admin": "/admin", "agent": "/agent", "warranty_manager": "/warranty"}.get(user.get("role"), "/")
        response = RedirectResponse(url=target, status_code=302)
        response.set_cookie(key="supportnova_session", value=token, httponly=True, secure=settings.COOKIE_SECURE, max_age=7*86400, samesite="lax")
        response.delete_cookie("google_oauth_state")
        return response

    except Exception as e:
        logger.error(f"Error in Google OAuth callback: {e}")
        logger.warning("Google OAuth callback failed.", exc_info=True)
        response = RedirectResponse(url="/login?error=Google%20sign-in%20failed", status_code=302)
        response.delete_cookie("google_oauth_state")
        return response
