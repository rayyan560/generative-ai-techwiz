import asyncio
import datetime
import json
import logging
import mimetypes
import os
import secrets
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, Form, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.gzip import GZipMiddleware

from config.settings import settings
from config.database import (
    get_complaints_col, get_knowledge_col
)
from src.knowledge_base.manager import KnowledgeBaseManager, rebuild_vector_index
from src.python_validation.pipeline import python_validation_pipeline
from src.genai_pipeline.pipeline import genai_pipeline
from src.comparison_engine.engine import ComparisonEngine
from src.analytics.sentiment import SentimentTelemetryEngine
from src.security.auth import AuthManager
from src.project_documentation import ADDITIONAL_TOPIC_DETAILS

from routers.common import clean_doc, clean_docs, ws_manager
from routers import auth, admin, agent, warranty, chat, analytics, knowledge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SupportNova.App")

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)
app.add_middleware(GZipMiddleware, minimum_size=1000)

@app.middleware("http")
async def enforce_judge_read_only(request: Request, call_next):
    """Prevent the public judge account from changing any application data."""
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        user = AuthManager.get_current_user(request)
        if user and user.get("role") == "judge":
            return JSONResponse({"detail": "Judge access is read-only."}, status_code=403)
    return await call_next(request)

BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

def require_page_role(user: Dict[str, Any], *allowed_roles: str) -> None:
    if user.get("role") == "judge" and set(allowed_roles).intersection({"admin", "agent", "warranty_manager"}):
        return
    if user.get("role") not in allowed_roles:
        raise HTTPException(status_code=403, detail="Your role cannot access this page.")

# Register Domain APIRouters
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(agent.router)
app.include_router(warranty.router)
app.include_router(chat.router)
app.include_router(analytics.router)
app.include_router(knowledge.router)

@app.on_event("startup")
async def startup_event():
    """Non-blocking instant startup."""
    import threading

    def _background_init():
        try:
            KnowledgeBaseManager.initialize_knowledge_base()
        except Exception as e:
            logger.error(f"[BG] Knowledge base init (non-fatal): {e}")

        try:
            complaints_col = get_complaints_col()
            if complaints_col.count_documents({}) == 0:
                dataset_path = os.path.join(BASE_DIR, "sample_complaints", "complaints_500.json")
                if os.path.exists(dataset_path):
                    with open(dataset_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    complaints_col.insert_many(data)
                    logger.info(f"[BG] Fast seeded {len(data)} complaints.")
        except Exception as e:
            logger.error(f"[BG] Complaint seeding error: {e}")

    logger.info("SupportNova started successfully.")
    threading.Thread(target=_background_init, daemon=True).start()

# -------------------------------------------------------------
# WebSocket Live Streaming & Presence
# -------------------------------------------------------------

@app.websocket("/ws/triage")
async def websocket_triage_endpoint(websocket: WebSocket):
    """Real-time bi-directional stream for triage dashboard & multi-agent notifications."""
    token = websocket.cookies.get("supportnova_session")
    user = AuthManager.verify_session_token(token) if token else None
    if not user or user.get("role") not in {"admin", "agent", "warranty_manager"}:
        await websocket.close(code=1008)
        return
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "PING_AGENT_PRESENCE":
                    await ws_manager.broadcast({
                        "type": "AGENT_PRESENCE_UPDATE",
                        "agent": msg.get("agent", "admin"),
                        "active_ticket": msg.get("active_ticket"),
                        "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
                    })
            except Exception as e:
                logger.warning(f"Error handling triage WS message: {e}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)

# -------------------------------------------------------------
# Health Check (Railway uses this to verify the app is alive)
# -------------------------------------------------------------

@app.get("/health")
async def health_check():
    return JSONResponse({"status": "ok", "app": "SupportNova"})

# -------------------------------------------------------------
# HTML Page Views
# -------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
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

@app.get("/login", response_class=HTMLResponse)
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

@app.get("/register", response_class=HTMLResponse)
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

@app.post("/login", response_class=HTMLResponse)
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

@app.get("/logout")
async def handle_logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("supportnova_session")
    return response

@app.get("/auth/google/login")
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

@app.get("/auth/google/callback")
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

@app.get("/admin", response_class=HTMLResponse)
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
# Project Deliverables / Slide Library
# -------------------------------------------------------------

PROJECT_DOCUMENTS = {
    "srs": {
        "title": "Project Documentation / SRS",
        "subtitle": "Project scope, requirements and Generative AI capabilities",
        "icon": "fa-file-contract",
        "topics": ["Project Introduction", "Problem Statement", "Proposed Solution", "Objectives", "Scope", "Functional Requirements", "Non-Functional Requirements", "User Roles", "AI Features", "Limitations", "Future Enhancements"],
        "files": [("Open SRS PDF", "/project-docs/file/srs.pdf", "fa-file-pdf")],
    },
    "user-guide": {
        "title": "User Manual / User Guide",
        "subtitle": "A practical walkthrough of the SupportNova portal",
        "icon": "fa-book-open-reader",
        "topics": ["Website Access", "Registration and Login", "AI Interface", "Prompt Submission", "File and Data Upload", "AI-Generated Output", "Chat and History", "Download and Export", "Error Handling", "Major Feature Walkthrough"],
        "files": [("Read User Guide", "/project-docs/file/user-guide.html", "fa-arrow-up-right-from-square")],
    },
    "developer-guide": {
        "title": "Developer Guide / Technical Documentation",
        "subtitle": "Architecture, integrations, configuration and operations",
        "icon": "fa-code",
        "topics": ["Project Architecture", "Python Environment", "FastAPI Structure", "Frontend Structure", "AI/API Integration", "MongoDB Integration", "CSV/JSON Processing", "Prompt Handling", "AI Response Processing", "Dependencies", "Configuration", "Error Handling and Logging"],
        "files": [("Read Developer Guide", "/project-docs/file/developer-guide.html", "fa-arrow-up-right-from-square")],
    },
    "architecture": {
        "title": "Architecture, DFD & UML",
        "subtitle": "Visual system design and end-to-end data movement",
        "icon": "fa-diagram-project",
        "topics": ["System Architecture Diagram", "Context Diagram", "Level 0 DFD", "Level 1 DFD", "AI Request Flow", "Authentication Flow", "Use Case Diagram", "Class Diagram", "Sequence Diagram", "Activity Diagram", "Component Diagram", "Deployment Diagram"],
        "files": [("Open Project Documentation", "/project-docs/file/slides.html", "fa-images")],
    },
    "database": {
        "title": "Database Documentation",
        "subtitle": "MongoDB collections, fields, relationships and backups",
        "icon": "fa-database",
        "topics": ["MongoDB Database Design", "Collections", "Documents and Fields", "Relationships and References", "Sample Documents", "Database Schema", "MongoDB Backup", "Database Initialization Script", "Users", "Conversations", "Prompts", "AI Responses", "Uploaded Files", "Feedback and Logs"],
        "files": [("Open Project Documentation", "/project-docs/file/slides.html", "fa-images")],
    },
    "setup": {
        "title": "Installation, Configuration & Test Data",
        "subtitle": "Everything needed to run, configure and verify the project",
        "icon": "fa-screwdriver-wrench",
        "topics": ["Python Installation", "Virtual Environment", "Required Python Version", "Libraries", "MongoDB Setup", "Gemini API Configuration", ".env Configuration", "Running the Application", "Browser Access", "Troubleshooting", "Test Data", "Sample Prompts", "Expected Outputs"],
        "files": [("Open Project Documentation", "/project-docs/file/slides.html", "fa-images")],
    },
    "slides": {
        "title": "Project Presentation Slides",
        "subtitle": "A ready-to-present slide deck covering all project topics",
        "icon": "fa-chalkboard-user",
        "topics": ["Project Overview", "Problem and Solution", "Features", "User Journey", "Technical Architecture", "Data Flow", "AI Pipeline", "Database Design", "Security", "Installation", "Testing", "Limitations", "Future Roadmap"],
        "files": [("Open 50-Slide Deck", "/project-docs/file/slides.html", "fa-play")],
    },
    "demo-videos": {
        "title": "Project Demo Videos",
        "subtitle": "Voice-over browser walkthroughs of the project and its documentation",
        "icon": "fa-circle-play",
        "topics": ["Full Project Walkthrough", "Authentication and Documents Walkthrough"],
        "files": [
            ("Play Full Project Walkthrough", "/project-docs/file/project-walkthrough.mp4", "fa-play"),
            ("Play Authentication & Documents Walkthrough", "/project-docs/file/auth-docs-walkthrough.mp4", "fa-play"),
        ],
    },
}

PROJECT_FILES = {
    "srs.pdf": "SupportNova-Generative AI PowerPlay_SRS.pdf",
    "user-guide.html": "SupportNova_User_Guide.html",
    "developer-guide.html": "SupportNova_Developer_Guide.html",
    "slides.html": "SupportNova_50_Slides_Project_Documentation.html",
    "project-walkthrough.mp4": "video_assets/SupportNova_Project_Walkthrough_VoiceOver.mp4",
    "auth-docs-walkthrough.mp4": "video_assets/SupportNova_Authentication_Documents_VoiceOver.mp4",
}

TOPIC_DETAILS = {
    "Project Introduction": ("SupportNova is a Generative AI powered customer complaint and warranty resolution platform. It combines a customer portal, admin operations dashboard, deterministic rules and AI-assisted analysis in one workflow.", ["Customer complaint intake", "AI-assisted triage and resolution", "Admin oversight and auditability"]),
    "Problem Statement": ("Hardware complaints are often slow to classify, difficult to verify and scattered across manual channels. Support teams need consistent decisions, evidence handling and clear escalation paths.", ["Manual triage causes delays", "Evidence and customer history are fragmented", "Inconsistent decisions create SLA and warranty risk"]),
    "Proposed Solution": ("The platform accepts structured complaints, descriptions and evidence, then combines Python validation, policy knowledge and Generative AI analysis to produce a traceable recommendation for support staff.", ["Single complaint intake workflow", "Dual-pipeline validation: rules plus AI", "Actionable status, priority and escalation output"]),
    "Objectives": ("The project aims to reduce response time, improve warranty decision consistency and give operations teams a real-time view of every case.", ["Automate first-level analysis", "Keep human approval in the loop", "Measure SLA, priority and escalation performance"]),
    "Scope": ("The scope covers customer submission, authentication, complaint tracking, AI analysis, policy knowledge, admin triage, warranty/refund operations and reporting.", ["Included: portal, dashboards, AI pipeline and policy repository", "Included: seeded products, complaints and test flows", "Future external integrations remain optional"]),
    "Functional Requirements": ("Users can submit and track complaints while staff can filter, triage, escalate and resolve cases through role-based dashboards.", ["Authentication and role-aware navigation", "Complaint creation with product and evidence details", "Filtering by urgency, category, department and status", "Triage, communication, refund and closure actions"]),
    "Non-Functional Requirements": ("The application should be secure, responsive, observable and reliable enough for operational use.", ["Fast page responses and background initialization", "Environment-based secrets and configuration", "Responsive glass-style interface for desktop and tablet", "Health endpoint for deployment monitoring"]),
    "User Roles": ("The system separates customer, agent and administrator responsibilities so that each user sees the tools relevant to their work.", ["Customer: submit, chat and track complaints", "Agent: review evidence, triage and communicate", "Admin: oversee queues, rules, analytics and user roles"]),
    "AI Features": ("Generative AI supports complaint summarization, sentiment and urgency analysis, defect interpretation, response drafting and operational recommendations.", ["Prompt-based complaint analysis", "Multimodal evidence context where configured", "Human-readable explanation and recommended next action"]),
    "System Limitations": ("AI recommendations depend on the quality of submitted information and configured services. Final warranty, refund and safety decisions remain subject to staff review.", ["AI can be uncertain with incomplete evidence", "External API availability can affect response generation", "Demo data and metrics are not production audit records"]),
    "Future Enhancements": ("The platform can be extended with richer model evaluation, notification integrations, advanced reporting and deeper workflow automation.", ["Model feedback and evaluation dashboard", "Email, WhatsApp and CRM integrations", "More granular permissions and approval chains"]),
    "Project Architecture": ("FastAPI serves the web application and API routes, Jinja templates provide the UI, Python modules handle validation and AI processing, and MongoDB-backed repositories store operational data.", ["FastAPI route layer", "Jinja templates plus shared CSS/JavaScript", "Python validation, rules and GenAI pipeline", "MongoDB and local sample data"]),
    "Python Environment": ("The project runs in an isolated Python virtual environment and installs its dependencies from requirements.txt.", ["Create a virtual environment", "Install requirements.txt", "Configure environment variables before launch"]),
    "FastAPI Structure": ("The application registers domain routers for authentication, administration, chat, analytics, warranty and knowledge operations. HTML views are rendered through Jinja2Templates.", ["app.py is the application entry point", "routers/ contains domain endpoints", "templates/ contains reusable UI pages"]),
    "Frontend Structure": ("The frontend uses a shared base layout with a consistent sidebar, topbar, theme system and reusable glassmorphism components.", ["templates/base.html provides navigation", "static/css/style.css contains theme tokens", "static/js contains dashboard and widget behavior"]),
    "AI/API Integration": ("AI requests are prepared by the GenAI pipeline with context from the complaint, rules and available knowledge. Responses are converted into operational fields and human-readable guidance.", ["Prompt context is assembled server-side", "AI output is compared with deterministic validation", "Failures return a safe fallback response"]),
    "MongoDB Integration": ("MongoDB stores complaints, knowledge records and operational entities when a configured connection is available. The application also supports seeded sample data for demonstration.", ["Collections are accessed through config/database.py", "Startup initializes knowledge and complaint data", "Secrets stay in environment configuration"]),
    "Prompt Handling": ("Prompts are built with relevant complaint details and policy context rather than sending isolated user text. This keeps results focused and traceable.", ["Normalize and validate user input", "Add product, policy and conversation context", "Limit output to the fields needed by the workflow"]),
    "AI Response Processing": ("The response processor extracts summary, urgency, category, priority, sentiment and escalation signals, then exposes them to dashboard filters and actions.", ["Structured fields support filtering", "Human-readable reasoning supports review", "Rule conflicts can trigger manual review"]),
    "Dependencies": ("The main runtime uses FastAPI, Uvicorn, Pydantic, PyMongo, Jinja2, document parsers, data libraries and AI client packages.", ["requirements.txt is the source of installed packages", "Keep versions compatible with the deployment runtime", "Use the virtual environment for local development"]),
    "Configuration": ("Runtime behavior is controlled by environment variables and config/settings.py. API keys, database URLs and OAuth secrets must never be committed.", ["Use .env.example as a safe template", "Set BASE_URL and deployment settings", "Keep production secrets in Railway variables"]),
    "Error Handling and Logging": ("Routes validate access and input, while the application logger records startup and processing failures without exposing secrets to the user.", ["Use HTTP status codes for invalid requests", "Return user-friendly fallback messages", "Inspect server logs for deployment diagnostics"]),
    "System Architecture Diagram": ("A request flows from the user interface through the web application and Python backend, into AI processing and data storage, before a response is returned to the user.", ["User → Browser → FastAPI", "FastAPI → validation and AI pipeline", "Pipeline → MongoDB/JSON → dashboard response"]),
    "AI Request Flow": ("A complaint is normalized, enriched with product and policy context, analyzed by validation and AI services, and returned as a traceable case recommendation.", ["Receive and validate request", "Run rules and AI analysis", "Compare results and assign next action"]),
    "Authentication Flow": ("Users authenticate through the login page. A session cookie identifies the current user and route guards redirect unauthenticated users to login.", ["Submit username and password", "Create signed session token", "Load role-specific dashboard"]),
    "Database Design": ("The data model is organized around users, complaints, conversations, prompts, AI responses, uploaded files, feedback and logs.", ["Operational records remain queryable", "Embedded analysis supports case review", "Indexes and validation can be added for production scale"]),
    "Collections": ("Core collections represent the main business objects used by the portal and admin workflows.", ["users", "complaints", "conversations", "knowledge", "ai_responses", "logs"]),
    "Installation / Setup": ("Local setup requires Python, a virtual environment, dependencies and configured environment variables before starting the FastAPI server.", ["Install Python and create venv", "Run pip install -r requirements.txt", "Run python app.py or the configured Uvicorn command"]),
    "Running the Application": ("After configuration, start the application and open the local browser URL. Railway uses the /health endpoint to confirm service availability.", ["Start the server", "Open the browser URL", "Verify /health returns status ok"]),
    "Troubleshooting": ("Most setup issues come from missing environment variables, unavailable MongoDB, dependency mismatches or an incorrect start command.", ["Check Railway deployment logs", "Verify environment variables", "Test /health before testing authenticated pages"]),
    "Test Data": ("Sample complaints, products, prompts and user flows are included so the dashboards can be demonstrated without production data.", ["Use demo admin and agent accounts", "Test critical, refund and resolved filters", "Verify complaint submission and tracking flows"]),
    "Project Overview": ("SupportNova demonstrates how Generative AI can be applied to customer support operations while keeping deterministic business rules and human review visible.", ["Portal experience", "Operations intelligence", "AI-assisted resolution"]),
    "Features": ("The presentation highlights complaint intake, product selection, evidence upload, AI triage, admin dashboards, knowledge policies, analytics and communication tools.", ["Customer and staff experiences", "Policy-aware AI analysis", "Real-time operations controls"]),
    "Technical Architecture": ("The technical stack combines FastAPI, Jinja, JavaScript, Python analytics, AI services and MongoDB-oriented data access.", ["Web routes and templates", "Domain modules and pipelines", "Deployment-ready health monitoring"]),
    "Data Flow": ("User input becomes a validated case, is enriched with context, passes through rules and AI analysis, and is stored or displayed as an operational result.", ["Input", "Enrichment and processing", "Decision, storage and response"]),
    "Testing": ("Testing covers route availability, authentication, complaint workflows, document pages, dashboard filters and safe fallback behavior.", ["Verify public and protected routes", "Test representative complaint priorities", "Check deployment health and logs"]),
    "Future Roadmap": ("The roadmap focuses on stronger evaluation, richer integrations, production-grade observability and more configurable workflows.", ["Feedback-driven model improvements", "Enterprise notifications and CRM", "Advanced reporting and governance"]),
}

TOPIC_DETAILS.update(ADDITIONAL_TOPIC_DETAILS)

def build_document_sections(document: Dict[str, Any]) -> Dict[str, Any]:
    """Attach readable project-specific content to every document topic."""
    sections = []
    for topic in document["topics"]:
        if topic not in TOPIC_DETAILS:
            raise ValueError(f"Project documentation is missing content for topic: {topic}")
        summary, points = TOPIC_DETAILS[topic]
        sections.append({"title": topic, "summary": summary, "points": points})
    enriched = dict(document)
    enriched["sections"] = sections
    return enriched

@app.get("/admin/documents", response_class=HTMLResponse)
async def project_documents(request: Request):
    user = AuthManager.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    require_page_role(user, "admin", "agent", "warranty_manager")
    return templates.TemplateResponse(request=request, name="project_documents.html", context={
        "request": request, "current_user": user, "app_name": settings.APP_NAME,
        "org_name": settings.ORG_NAME, "documents": PROJECT_DOCUMENTS,
    })

@app.get("/admin/documents/{slug}", response_class=HTMLResponse)
async def project_document_page(request: Request, slug: str):
    user = AuthManager.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    require_page_role(user, "admin", "agent", "warranty_manager")
    document = PROJECT_DOCUMENTS.get(slug)
    if not document:
        raise HTTPException(status_code=404, detail="Project document not found")
    return templates.TemplateResponse(request=request, name="project_document_page.html", context={
        "request": request, "current_user": user, "app_name": settings.APP_NAME,
        "org_name": settings.ORG_NAME, "document": build_document_sections(document), "slug": slug,
    })

@app.get("/project-docs/file/{filename}")
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

@app.get("/agent", response_class=HTMLResponse)
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

@app.get("/warranty", response_class=HTMLResponse)
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

@app.get("/communication", response_class=HTMLResponse)
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

@app.get("/refunds", response_class=HTMLResponse)
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

@app.get("/knowledge", response_class=HTMLResponse)
async def knowledge_portal(request: Request):
    user = AuthManager.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    require_page_role(user, "admin", "agent", "warranty_manager")
    return templates.TemplateResponse(request=request, name="knowledge_base.html", context={"request": request, "current_user": user, "app_name": settings.APP_NAME})

@app.get("/rules", response_class=HTMLResponse)
async def rules_portal(request: Request):
    user = AuthManager.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    require_page_role(user, "admin", "agent", "warranty_manager")
    return templates.TemplateResponse(request=request, name="rules_matrix.html", context={"request": request, "current_user": user, "app_name": settings.APP_NAME})

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_portal(request: Request):
    user = AuthManager.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    require_page_role(user, "admin", "warranty_manager")
    return templates.TemplateResponse(request=request, name="analytics_reports.html", context={"request": request, "current_user": user, "app_name": settings.APP_NAME})

# -------------------------------------------------------------
# 🤖 Dual-Mode AI Chatbot - WebSocket Endpoint
# -------------------------------------------------------------

def _build_customer_chatbot_system_prompt() -> str:
    return """You are NovAI, a friendly and empathetic AI support assistant for NovaTech Global Commerce & Electronics, powered by SupportNova ResponseX Intelligence.

Your role is to HELP CUSTOMERS:
- Answer questions about their complaints, orders, refunds, and products
- Guide them through the complaint submission process step by step
- Provide estimated resolution timelines based on complaint type
- Explain company policies clearly and in simple language
- Provide emotional support and reassurance for frustrated customers
- Help track complaint status and next steps
- Suggest self-service solutions when applicable

PERSONALITY: Be warm, professional, empathetic, and solution-focused. Always acknowledge the customer's frustration first, then provide help.

RESPONSE FORMAT: Keep responses concise (2-4 short paragraphs max). Use bullet points for steps. End with a follow-up question or offer for more help.

KNOWLEDGE:
- Refund processing: 5-7 business days for approved refunds
- Product defects: 30-day return/replacement window
- Safety hazards (battery swelling, sparks): Immediate priority, stop using device
- Billing disputes: Can be resolved in 2-4 business days
- Delivery issues: Contact logistics team with tracking number

NEVER: Make unauthorized monetary promises, share other customers' data, or escalate without proper verification."""


def _build_admin_chatbot_system_prompt(complaints_summary: str) -> str:
    return f"""You are NovaOps, an advanced AI operations intelligence assistant for SupportNova admin dashboard, designed for support team managers and agents at NovaTech Global Commerce & Electronics.

Your role is to ASSIST ADMIN USERS with:
1. COMPLAINT ANALYTICS: Provide real-time summaries, trends, and statistics from the complaint database
2. SMART FILTERING: Help filter and find specific complaints (by urgency, category, department, customer, date)
3. URGENT ALERTS: Identify and highlight P0/Critical/Safety Hazard complaints requiring immediate action
4. ESCALATION GUIDANCE: Recommend escalation paths based on complaint severity and SLA timelines
5. TRIAGE SUPPORT: Suggest resolution strategies and policy references for complex cases
6. WORKLOAD MANAGEMENT: Help balance complaint workload across departments

CURRENT COMPLAINTS OVERVIEW (Live Data):
{complaints_summary}

RESPONSE FORMAT: Be precise, data-driven, and actionable. Use structured lists and tables when presenting data. Highlight URGENT items in ALL CAPS with 🚨 prefix.

CAPABILITIES:
- Filter complaints by: urgency (Critical/High/Medium/Low), category, department, priority (P0-P3), status, date range
- Count and group complaints for reporting
- Identify SLA breaches and at-risk tickets
- Suggest prioritization order for the triage queue

NEVER: Make unauthorized system changes, promise resolution outcomes, or share customer PII beyond what's necessary for case management."""


def _get_complaints_summary_for_admin() -> str:
    try:
        col = get_complaints_col()
        total = col.count_documents({})
        critical = col.count_documents({"urgency": "Critical"})
        high = col.count_documents({"urgency": "High"})
        p0 = col.count_documents({"priority": "P0"})
        safety = col.count_documents({"category": "Safety Hazard"})
        pending = col.count_documents({"status": {"$in": ["Pending", "Manual Review Required", "New"]}})
        resolved = col.count_documents({"status": {"$in": ["Resolved", "Closed", "Analyzed"]}})
        escalated = col.count_documents({"genai_analysis.escalation_required": True})

        return f"""
- Total Complaints: {total}
- P0 Critical: {p0} | Safety Hazards: {safety}
- Urgency Breakdown: Critical={critical}, High={high}
- Pending/In-Review: {pending} | Resolved: {resolved}
- Escalated Cases: {escalated}
"""
    except Exception as e:
        return f"(Live data unavailable: {e})"


def _call_gemini_chat(api_key: str, model_name: str, system_prompt: str, history: list, user_message: str) -> str:
    from google import genai
    from google.genai import types

    contents = []
    for turn in history:
        role = "model" if turn.get("role") == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": turn.get("content", "")}]})
    contents.append({"role": "user", "parts": [{"text": user_message}]})
    with genai.Client(api_key=api_key) as client:
        response = client.models.generate_content(
            model=model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=600,
            ),
        )
    return response.text.strip()


@app.websocket("/ws/chat")
async def chatbot_websocket(websocket: WebSocket, mode: str = "customer"):
    if mode not in {"customer", "admin"}:
        await websocket.close(code=1008)
        return
    if mode == "admin":
        token = websocket.cookies.get("supportnova_session")
        user = AuthManager.verify_session_token(token) if token else None
        if not user or user.get("role") not in {"admin", "agent", "warranty_manager"}:
            await websocket.close(code=1008)
            return
    await websocket.accept()
    logger.info(f"Chatbot WebSocket connected - mode: {mode}")

    conversation_history: list = []

    if mode == "admin":
        welcome = (
            "👋 Hello! I'm **NovaOps**, your AI complaint intelligence assistant.\n\n"
            "I can help you:\n"
            "• 🚨 Find urgent/critical complaints\n"
            "• 📊 Get live complaint statistics & trends\n"
            "• 🔍 Filter complaints by category, urgency, or department\n"
            "• ⚡ Identify SLA breaches and escalation needs\n\n"
            "What would you like to know?"
        )
    else:
        welcome = (
            "👋 Hi! I'm **NovAI**, your personal support assistant at NovaTech.\n\n"
            "I'm here to help you with:\n"
            "• 📦 Order & delivery issues\n"
            "• 💰 Refunds & billing questions\n"
            "• 🔧 Product defects & warranty claims\n"
            "• 📋 Complaint status & next steps\n\n"
            "How can I assist you today?"
        )

    await websocket.send_json({"type": "welcome", "content": welcome, "mode": mode})

    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            user_message = data.get("message", "").strip()

            if not user_message:
                continue

            await websocket.send_json({"type": "typing", "content": "..."})

            if mode == "admin":
                complaints_summary = await asyncio.get_event_loop().run_in_executor(
                    None, _get_complaints_summary_for_admin
                )
                system_prompt = _build_admin_chatbot_system_prompt(complaints_summary)
            else:
                system_prompt = _build_customer_chatbot_system_prompt()

            bot_response = None
            last_err = None

            for attempt in range(len(settings.GEMINI_API_KEYS)):
                key = settings.GEMINI_API_KEYS[attempt % len(settings.GEMINI_API_KEYS)]
                try:
                    bot_response = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda k=key: _call_gemini_chat(
                            k, settings.DEFAULT_MODEL,
                            system_prompt, conversation_history, user_message
                        )
                    )
                    if bot_response:
                        break
                except Exception as e:
                    last_err = str(e)
                    logger.warning(f"Chatbot Gemini key attempt {attempt+1} failed: {e}")

            if not bot_response:
                logger.warning(f"Chatbot API failed, using fallback. Last error: {last_err}")
                u_lower = user_message.lower()
                if mode == "admin":
                    if any(w in u_lower for w in ["urgent", "critical", "p0", "safety"]):
                        col = get_complaints_col()
                        count = col.count_documents({"urgency": "Critical"})
                        bot_response = f"There are currently **{count} critical complaints**. Please review their individual details and applicable policy before taking action."
                    elif any(w in u_lower for w in ["total", "count", "how many", "statistics", "stats"]):
                        col = get_complaints_col()
                        total = col.count_documents({})
                        bot_response = f"📊 **Live Complaint Statistics:**\n• Total complaints in system: **{total}**\n• Use the dashboard filters to drill down by urgency, category, or department."
                    else:
                        bot_response = "I'm having trouble connecting to the AI service right now. Please use the dashboard filters directly or check back in a moment. Your complaint data is still fully accessible via the table above."
                else:
                    if any(w in u_lower for w in ["refund", "money back"]):
                        bot_response = "Refund eligibility and timing depend on the case and applicable policy. You can review the latest status in 'My Complaints' or contact support for help."
                    elif any(w in u_lower for w in ["delivery", "shipping", "package", "late"]):
                        bot_response = "Please include your order number when submitting a delivery concern so the support team can review its status. You can also track updates in 'My Complaints'."
                    elif any(w in u_lower for w in ["battery", "fire", "smoke", "spark", "swollen"]):
                        bot_response = "If a device is smoking, sparking, unusually hot, or has a swollen battery, stop using or charging it and move away if it is unsafe. Contact local emergency services if there is immediate danger, then submit a safety complaint for staff review."
                    else:
                        bot_response = "Thank you for reaching out! Our AI assistant is momentarily unavailable. Please submit your complaint using the form and our dedicated support team will respond within your SLA window. You can also check your existing complaints in the 'Track My Complaint' section."

            conversation_history.append({"role": "user", "content": user_message})
            conversation_history.append({"role": "model", "content": bot_response})

            if len(conversation_history) > 20:
                conversation_history = conversation_history[-20:]

            await websocket.send_json({
                "type": "response",
                "content": bot_response,
                "mode": mode,
                "timestamp": datetime.datetime.now().strftime("%H:%M")
            })

    except WebSocketDisconnect:
        logger.info(f"Chatbot WebSocket disconnected - mode: {mode}")
    except Exception as e:
        logger.error(f"Chatbot WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "content": "Connection error. Please refresh and try again."})
        except Exception as e:
            logger.warning(f"Error sending WS error frame: {e}")
