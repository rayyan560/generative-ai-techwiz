import mimetypes
import os

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from config.settings import settings
from routers.common import require_page_role
from src.project_documentation import PROJECT_DOCUMENTS, PROJECT_FILES, build_document_sections
from src.security.auth import AuthManager

router = APIRouter(tags=["Project Documentation"])
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


@router.get("/admin/documents", response_class=HTMLResponse)
async def project_documents_page(request: Request):
    user = AuthManager.get_current_user(request)
    if not user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=302)
    require_page_role(user, "admin", "agent", "warranty_manager")
    return templates.TemplateResponse(request=request, name="project_documents.html", context={
        "request": request,
        "current_user": user,
        "app_name": settings.APP_NAME,
        "org_name": settings.ORG_NAME,
        "documents": PROJECT_DOCUMENTS,
    })


@router.get("/admin/documents/{slug}", response_class=HTMLResponse)
async def project_document_page(request: Request, slug: str):
    user = AuthManager.get_current_user(request)
    if not user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=302)
    require_page_role(user, "admin", "agent", "warranty_manager")
    document = PROJECT_DOCUMENTS.get(slug)
    if not document:
        raise HTTPException(status_code=404, detail="Project document not found")
    return templates.TemplateResponse(request=request, name="project_document_page.html", context={
        "request": request,
        "current_user": user,
        "app_name": settings.APP_NAME,
        "org_name": settings.ORG_NAME,
        "document": build_document_sections(document),
        "slug": slug,
    })


@router.get("/project-docs/file/{filename}")
async def project_document_file(request: Request, filename: str):
    user = AuthManager.get_current_user(request)
    if not user or filename not in PROJECT_FILES:
        raise HTTPException(status_code=404, detail="Project file not found")
    require_page_role(user, "admin", "agent", "warranty_manager")
    file_path = os.path.join(BASE_DIR, PROJECT_FILES[filename])
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Project file is missing")
    media_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
    return FileResponse(file_path, media_type=media_type)
