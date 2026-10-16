from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from config.settings import settings
from routers.common import require_page_role
from routers.page_support import templates
from src.security.auth import AuthManager

router = APIRouter(tags=["Administrator Page"])

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, view: Optional[str] = None):
    user = AuthManager.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    require_page_role(user, "admin")

    if view == "communication":
        return templates.TemplateResponse(request=request, name="communication.html", context={
            "request": request,
            "current_user": user,
            "app_name": settings.APP_NAME,
            "org_name": settings.ORG_NAME
        })
    elif view == "refunds":
        return templates.TemplateResponse(request=request, name="refunds.html", context={
            "request": request,
            "current_user": user,
            "app_name": settings.APP_NAME,
            "org_name": settings.ORG_NAME
        })

    return templates.TemplateResponse(request=request, name="admin_dashboard.html", context={
        "request": request,
        "current_user": user,
        "app_name": settings.APP_NAME,
        "org_name": settings.ORG_NAME,
        "departments": settings.DEPARTMENTS,
        "categories": settings.CATEGORIES,
        "urgency_levels": settings.URGENCY_LEVELS
    })

# -------------------------------------------------------------
