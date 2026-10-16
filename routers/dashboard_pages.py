from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from config.settings import settings
from routers.common import require_page_role
from routers.page_support import templates
from src.security.auth import AuthManager

router = APIRouter(tags=["Dashboard Pages"])


@router.get("/agent", response_class=HTMLResponse)
async def agent_dashboard(request: Request):
    user = AuthManager.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    require_page_role(user, "admin", "agent")
    return templates.TemplateResponse(request=request, name="agent_dashboard.html", context={
        "request": request,
        "current_user": user,
        "app_name": settings.APP_NAME,
        "org_name": settings.ORG_NAME,
        "departments": settings.DEPARTMENTS,
        "categories": settings.CATEGORIES,
        "urgency_levels": settings.URGENCY_LEVELS
    })

@router.get("/warranty", response_class=HTMLResponse)
async def warranty_dashboard(request: Request):
    user = AuthManager.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    require_page_role(user, "admin", "agent", "warranty_manager")
    return templates.TemplateResponse(request=request, name="warranty_dashboard.html", context={
        "request": request,
        "current_user": user,
        "app_name": settings.APP_NAME,
        "org_name": settings.ORG_NAME
    })

@router.get("/communication", response_class=HTMLResponse)
async def communication_portal(request: Request):
    user = AuthManager.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    require_page_role(user, "admin", "agent")
    return templates.TemplateResponse(request=request, name="communication.html", context={
        "request": request,
        "current_user": user,
        "app_name": settings.APP_NAME,
        "org_name": settings.ORG_NAME
    })

@router.get("/refunds", response_class=HTMLResponse)
async def refunds_portal(request: Request):
    user = AuthManager.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    require_page_role(user, "admin", "warranty_manager")
    return templates.TemplateResponse(request=request, name="refunds.html", context={
        "request": request,
        "current_user": user,
        "app_name": settings.APP_NAME,
        "org_name": settings.ORG_NAME
    })

@router.get("/knowledge", response_class=HTMLResponse)
async def knowledge_portal(request: Request):
    user = AuthManager.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    require_page_role(user, "admin", "agent", "warranty_manager")
    return templates.TemplateResponse(request=request, name="knowledge_base.html", context={"request": request, "current_user": user, "app_name": settings.APP_NAME})

@router.get("/rules", response_class=HTMLResponse)
async def rules_portal(request: Request):
    user = AuthManager.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    require_page_role(user, "admin", "agent", "warranty_manager")
    return templates.TemplateResponse(request=request, name="rules_matrix.html", context={"request": request, "current_user": user, "app_name": settings.APP_NAME})

@router.get("/analytics", response_class=HTMLResponse)
async def analytics_portal(request: Request):
    user = AuthManager.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    require_page_role(user, "admin", "warranty_manager")
    return templates.TemplateResponse(request=request, name="analytics_reports.html", context={"request": request, "current_user": user, "app_name": settings.APP_NAME})
