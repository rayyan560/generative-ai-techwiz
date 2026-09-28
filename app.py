import os
import json
import logging
import datetime
import asyncio
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, Form, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
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

from routers.common import clean_doc, clean_docs, ws_manager
from routers import auth, admin, agent, warranty, chat, analytics, knowledge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SupportNova.App")

app = FastAPI(title=settings.APP_NAME, version=settings.VERSION)
app.add_middleware(GZipMiddleware, minimum_size=1000)

BASE_DIR = os.path.dirname(__file__)
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

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
    """Non-blocking startup — all heavy init runs in a background thread so Railway health check passes immediately."""
    import threading

    def _background_init():
        # Step 1: Knowledge base documents + FAISS index (may download sentence-transformers model)
        try:
            logger.info("[BG] Initializing Knowledge Base & FAISS vector index...")
            KnowledgeBaseManager.initialize_knowledge_base()
            logger.info("[BG] Knowledge Base ready.")
        except Exception as e:
            logger.error(f"[BG] Knowledge base init error (non-fatal): {e}")

        # Step 2: Seed 500 sample complaints if DB is empty
        try:
            complaints_col = get_complaints_col()
            if complaints_col.count_documents({}) == 0:
                dataset_path = os.path.join(BASE_DIR, "sample_complaints", "complaints_500.json")
                if os.path.exists(dataset_path):
                    with open(dataset_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    logger.info(f"[BG] Seeding {len(data)} complaints...")
                    processed_items = []
                    for idx, item in enumerate(data):
                        try:
                            gt = python_validation_pipeline.validate_complaint(item)
                            ai = genai_pipeline._generate_intelligent_fallback(item, None)
                            comp = ComparisonEngine.compare_and_verify(ai, gt, item)
                            sent = SentimentTelemetryEngine.analyze(
                                item.get("complaint_title", ""),
                                item.get("complaint_description", ""),
                                item.get("customer_type", "Standard")
                            )
                            item["status"] = "Analyzed" if not comp.requires_manual_review else "Manual Review Required"
                            item["category"] = gt.expected_category
                            item["subcategory"] = gt.expected_subcategory
                            item["department"] = gt.expected_department
                            item["urgency"] = gt.expected_urgency
                            item["priority"] = gt.expected_priority
                            item["genai_analysis"] = ai.model_dump()
                            item["ground_truth"] = gt.model_dump()
                            item["comparison"] = comp.model_dump()
                            item["sentiment_telemetry"] = sent
                            processed_items.append(item)
                        except Exception as ie:
                            logger.warning(f"[BG] Skipping complaint {idx}: {ie}")
                            processed_items.append(item)
                    complaints_col.insert_many(processed_items)
                    logger.info(f"[BG] Seeding done: {len(processed_items)} complaints loaded.")
        except Exception as e:
            logger.error(f"[BG] Complaint seeding error: {e}")

    # Launch everything in a single background daemon thread — startup returns instantly
    logger.info("SupportNova starting. Heavy init delegated to background thread.")
    threading.Thread(target=_background_init, daemon=True).start()

# -------------------------------------------------------------
# WebSocket Live Streaming & Presence
# -------------------------------------------------------------

@app.websocket("/ws/triage")
async def websocket_triage_endpoint(websocket: WebSocket):
    """Real-time bi-directional stream for triage dashboard & multi-agent notifications."""
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
    return templates.TemplateResponse(request=request, name="customer_portal.html", context={
        "app_name": settings.APP_NAME,
        "current_user": user,
        "is_authenticated": user is not None
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user = AuthManager.get_current_user(request)
    if user:
        if user.get("role") == "admin":
            return RedirectResponse(url="/admin", status_code=302)
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(request=request, name="login.html", context={
        "app_name": settings.APP_NAME,
        "error": None,
        "mode": "login",
        "demo_mode": settings.DEMO_MODE
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
        "demo_mode": settings.DEMO_MODE
    })

@app.post("/login", response_class=HTMLResponse)
async def handle_login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = AuthManager.authenticate_user(username, password)
    if not user:
        return templates.TemplateResponse(request=request, name="login.html", context={
            "app_name": settings.APP_NAME,
            "error": "Invalid username or password. Please check your credentials.",
            "mode": "login",
            "demo_mode": settings.DEMO_MODE
        })
    token = AuthManager.create_session_token(user)
    target_url = "/admin" if user.get("role") in ["admin", "agent"] else "/"
    response = RedirectResponse(url=target_url, status_code=302)
    response.set_cookie(key="supportnova_session", value=token, httponly=True, max_age=7*86400, samesite="lax")
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
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": f"{settings.BASE_URL}/auth/google/callback",
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "select_account"
        }
        google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
        return RedirectResponse(url=google_auth_url, status_code=302)
    else:
        return RedirectResponse(url="/login?google_prompt=true", status_code=302)

@app.get("/auth/google/callback")
async def google_oauth_callback(request: Request, code: Optional[str] = None, error: Optional[str] = None):
    if error or not code:
        return RedirectResponse(url=f"/login?error={error or 'Google authorization cancelled'}", status_code=302)
    
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
        target = "/admin" if user.get("role") in ["admin", "agent"] else "/"
        response = RedirectResponse(url=target, status_code=302)
        response.set_cookie(key="supportnova_session", value=token, httponly=True, max_age=7*86400, samesite="lax")
        return response
        
    except Exception as e:
        logger.error(f"Error in Google OAuth callback: {e}")
        return RedirectResponse(url=f"/login?error=Google login failed: {str(e)}", status_code=302)

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, view: Optional[str] = None):
    user = AuthManager.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
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

@app.get("/agent", response_class=HTMLResponse)
async def agent_dashboard(request: Request):
    user = AuthManager.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
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
    return templates.TemplateResponse(request=request, name="knowledge_base.html", context={"request": request, "current_user": user, "app_name": settings.APP_NAME})

@app.get("/rules", response_class=HTMLResponse)
async def rules_portal(request: Request):
    user = AuthManager.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    return templates.TemplateResponse(request=request, name="rules_matrix.html", context={"request": request, "current_user": user, "app_name": settings.APP_NAME})

@app.get("/analytics", response_class=HTMLResponse)
async def analytics_portal(request: Request):
    user = AuthManager.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
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

        critical_complaints = list(col.find(
            {"urgency": "Critical"},
            {"complaint_id": 1, "complaint_title": 1, "customer_name": 1, "category": 1}
        ).limit(3))
        critical_list = "\n".join([
            f"  - {c.get('complaint_id','N/A')}: {c.get('complaint_title','')[:60]} ({c.get('customer_name','')})"
            for c in critical_complaints
        ])

        return f"""
- Total Complaints: {total}
- P0 Critical: {p0} | Safety Hazards: {safety}
- Urgency Breakdown: Critical={critical}, High={high}
- Pending/In-Review: {pending} | Resolved: {resolved}
- Escalated Cases: {escalated}
- Sample Critical Cases:
{critical_list if critical_list else '  None currently'}
"""
    except Exception as e:
        return f"(Live data unavailable: {e})"


def _call_gemini_chat(api_key: str, model_name: str, system_prompt: str, history: list, user_message: str) -> str:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt,
        generation_config={"temperature": 0.7, "max_output_tokens": 600}
    )
    chat_history = []
    for turn in history:
        chat_history.append({"role": turn["role"], "parts": [turn["content"]]})
    
    chat = model.start_chat(history=chat_history)
    response = chat.send_message(user_message)
    return response.text.strip()


@app.websocket("/ws/chat")
async def chatbot_websocket(websocket: WebSocket, mode: str = "customer"):
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
                        bot_response = f"🚨 There are currently **{count} Critical (P0)** complaints requiring immediate attention. These include Safety Hazard and escalated billing cases. I recommend reviewing the P0 Critical filter in your dashboard immediately."
                    elif any(w in u_lower for w in ["total", "count", "how many", "statistics", "stats"]):
                        col = get_complaints_col()
                        total = col.count_documents({})
                        bot_response = f"📊 **Live Complaint Statistics:**\n• Total complaints in system: **{total}**\n• Use the dashboard filters to drill down by urgency, category, or department."
                    else:
                        bot_response = "I'm having trouble connecting to the AI service right now. Please use the dashboard filters directly or check back in a moment. Your complaint data is still fully accessible via the table above."
                else:
                    if any(w in u_lower for w in ["refund", "money back"]):
                        bot_response = "💰 For refund requests, approved refunds are processed within **5-7 business days** back to your original payment method. You can track your refund status in the 'My Complaints' section of your portal."
                    elif any(w in u_lower for w in ["delivery", "shipping", "package", "late"]):
                        bot_response = "📦 For delivery issues, please provide your **order number** and I'll help you track it. Typical delivery windows are 3-5 business days. If your package is significantly delayed, our logistics team will investigate within 24 hours."
                    elif any(w in u_lower for w in ["battery", "fire", "smoke", "spark", "swollen"]):
                        bot_response = "🚨 **IMPORTANT SAFETY ALERT:** If your device is showing signs of battery issues (swelling, sparking, smoke, or heat), please **immediately stop using it and power it off**. Do NOT charge it. This is a Priority 0 safety case — our team will contact you within 1 hour."
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
