import logging
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from config.settings import settings
from routers.page_support import templates
from src.security.auth import AuthManager

router = APIRouter(tags=["Web Pages"])
logger = logging.getLogger("SupportNova.SitePages")

@router.get("/", response_class=HTMLResponse)
async def customer_portal(request: Request):
    user = AuthManager.get_current_user(request)
    if user and user.get("role") == "judge":
        target = "/agent" if user.get("demo_portal") == "agent" else "/admin"
        return RedirectResponse(url=target, status_code=302)
    return templates.TemplateResponse(request=request, name="customer_portal.html", context={
        "app_name": settings.APP_NAME,
        "current_user": user,
        "is_authenticated": user is not None
    })

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user = AuthManager.get_current_user(request)
    if user:
        target = {"admin": "/admin", "judge": "/admin", "agent": "/agent", "warranty_manager": "/warranty"}.get(user.get("role"), "/")
        if user.get("role") == "judge" and user.get("demo_portal") == "agent":
            target = "/agent"
        return RedirectResponse(url=target, status_code=302)
    return templates.TemplateResponse(request=request, name="login.html", context={
        "app_name": settings.APP_NAME,
        "error": None,
        "mode": "login",
        "demo_mode": settings.DEMO_MODE,
        "public_demo_mode": settings.PUBLIC_DEMO_MODE
    })

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    user = AuthManager.get_current_user(request)
    if user:
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(request=request, name="login.html", context={
        "app_name": settings.APP_NAME,
        "error": None,
        "mode": "register",
        "demo_mode": settings.DEMO_MODE,
        "public_demo_mode": settings.PUBLIC_DEMO_MODE
    })

@router.post("/login", response_class=HTMLResponse)
async def handle_login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = AuthManager.authenticate_user(username, password)
    if not user:
        return templates.TemplateResponse(request=request, name="login.html", context={
            "app_name": settings.APP_NAME,
            "error": "Invalid username or password. Please check your credentials.",
            "mode": "login",
            "demo_mode": settings.DEMO_MODE,
            "public_demo_mode": settings.PUBLIC_DEMO_MODE
        })
    token = AuthManager.create_session_token(user)
    target_url = {
        "admin": "/admin",
        "judge": "/admin",
        "agent": "/agent",
        "warranty_manager": "/warranty",
    }.get(user.get("role"), "/")
    if user.get("role") == "judge" and user.get("demo_portal") == "agent":
        target_url = "/agent"
    response = RedirectResponse(url=target_url, status_code=302)
    response.set_cookie(
        key="supportnova_session",
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        max_age=7 * 86400,
        samesite="lax"
    )
    return response

@router.get("/logout")
async def handle_logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("supportnova_session")
    return response
