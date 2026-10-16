import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware

from config.settings import settings
from src.security.auth import AuthManager
from src.project_documentation import PROJECT_DOCUMENTS, PROJECT_FILES, TOPIC_DETAILS, build_document_sections
from src.application_startup import start_background_initialization

from routers import auth, admin, agent, warranty, chat, analytics, knowledge, project_documents
from routers import site_pages, oauth_pages, admin_page, dashboard_pages, triage_socket, chat_socket
from routers.page_support import templates

BASE_DIR = os.path.dirname(__file__)


@asynccontextmanager
async def lifespan(_app):
    start_background_initialization(BASE_DIR)
    yield


app = FastAPI(title=settings.APP_NAME, version=settings.VERSION, lifespan=lifespan)
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.middleware("http")
async def enforce_judge_read_only(request: Request, call_next):
    """Prevent the public judge account from changing any application data."""
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        user = AuthManager.get_current_user(request)
        if user and user.get("role") == "judge":
            return JSONResponse({"detail": "Judge access is read-only."}, status_code=403)
    return await call_next(request)

STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Register Domain APIRouters
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(agent.router)
app.include_router(warranty.router)
app.include_router(chat.router)
app.include_router(analytics.router)
app.include_router(knowledge.router)
app.include_router(project_documents.router)
app.include_router(site_pages.router)
app.include_router(oauth_pages.router)
app.include_router(admin_page.router)
app.include_router(dashboard_pages.router)
app.include_router(triage_socket.router)
app.include_router(chat_socket.router)

# -------------------------------------------------------------
# Health Check (Railway uses this to verify the app is alive)
# -------------------------------------------------------------

@app.get("/health")
async def health_check():
    return JSONResponse({"status": "ok", "app": "SupportNova"})
