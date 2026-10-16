import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from config.settings import settings
from src.security.auth import AuthManager
from routers.auth_sessions import _session_response


logger = logging.getLogger("SupportNova.GoogleAuth")
router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/google")
async def api_google_login(request: Request):
    try:
        body = await request.json()
        credential = body.get("credential")
    except Exception:
        logger.warning("Invalid Google login payload.")
        raise HTTPException(status_code=400, detail="Invalid Google payload")

    if not credential or not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=401, detail="Use the configured Google Sign-In flow. Email-only sign-in is not accepted.")

    try:
        from google.auth.transport.requests import Request as GoogleRequest
        from google.oauth2 import id_token

        verified = id_token.verify_oauth2_token(credential, GoogleRequest(), settings.GOOGLE_CLIENT_ID)
        email = (verified.get("email") or "").strip().lower()
        if not email or not verified.get("email_verified"):
            raise ValueError("Verified Google email is required.")
    except Exception:
        logger.warning("Google ID token verification failed.")
        raise HTTPException(status_code=401, detail="Google identity could not be verified.")

    user = AuthManager.authenticate_google_user(
        email=email,
        display_name=verified.get("name") or email.split("@")[0].title(),
        avatar=verified.get("picture") or None,
        google_id=verified.get("sub"),
    )
    return _session_response(user, f"Successfully authenticated with Google as {user.get('email')}")
