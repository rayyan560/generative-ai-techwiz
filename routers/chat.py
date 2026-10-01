from fastapi import APIRouter, Request, HTTPException, Form, UploadFile, File, Depends, Response
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import datetime
import asyncio
import os
import logging
import secrets

from config.database import get_live_chats_col, get_complaints_col, get_audit_logs_col
from src.security.auth import AuthManager
from routers.common import clean_doc, clean_docs, ws_manager
from src.security.permissions import require_roles

logger = logging.getLogger("SupportNova.ChatRouter")

router = APIRouter(prefix="/api", tags=["Live Chat & Staff Calls"])

STAFF_PRESENCE = {
    "admin": {"name": "Administrator", "role": "Administrator", "online": False, "avatar": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=160&auto=format&fit=crop&q=80"},
    "agent": {"name": "Support Agent", "role": "Triage Specialist", "online": False, "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=160&auto=format&fit=crop&q=80"},
    "warranty_manager": {"name": "Warranty Manager", "role": "Warranty Officer", "online": False, "avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=160&auto=format&fit=crop&q=80"}
}

ACTIVE_CALLS: Dict[str, Dict[str, Any]] = {}

def get_call_client_context(request: Request):
    user = AuthManager.get_current_user(request)
    if user:
        return user.get("user_id", "guest"), user.get("display_name") or user.get("username") or "Customer", None
    guest_id = request.cookies.get("supportnova_guest_id")
    new_guest_id = None
    if not guest_id or len(guest_id) > 80:
        guest_id = secrets.token_urlsafe(24)
        new_guest_id = guest_id
    return f"guest:{guest_id}", "Guest customer", new_guest_id

def set_guest_call_cookie(response: Response, guest_id: Optional[str], request: Request):
    if guest_id:
        response.set_cookie(
            "supportnova_guest_id",
            guest_id,
            max_age=60 * 60 * 24 * 365,
            httponly=True,
            secure=request.url.scheme == "https",
            samesite="lax",
            path="/",
        )

def reject_read_only_judge(user):
    if user and user.get("role") == "judge":
        raise HTTPException(status_code=403, detail="Judge access is read-only.")

@router.get("/chat/live/messages")
async def get_live_chat_messages(request: Request, client_id: Optional[str] = None):
    user = AuthManager.get_current_user(request)
    chats_col = get_live_chats_col()
    is_staff = bool(user and user.get("role") in ["admin", "agent", "warranty_manager"])
    cid = (client_id if is_staff else (user.get("user_id") if user else "guest_client_001")) or "guest_client_001"
    
    messages = list(chats_col.find({"client_id": cid}))
    if not messages:
        return {"messages": [], "client_id": cid}
        initial_msgs = [
            {
                "msg_id": "MSG-001",
                "client_id": cid,
                "sender": "agent",
                "sender_name": "Marcus Chen",
                "sender_role": "Lead Triage Specialist",
                "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=160&auto=format&fit=crop&q=80",
                "message": "Welcome to SupportNova Direct WhatsApp Care! I am Marcus Chen, your assigned technical triage specialist.",
                "timestamp": "10:14 AM",
                "status": "read"
            },
            {
                "msg_id": "MSG-002",
                "client_id": cid,
                "sender": "agent",
                "sender_name": "Marcus Chen",
                "sender_role": "Lead Triage Specialist",
                "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=160&auto=format&fit=crop&q=80",
                "message": "Feel free to share your ticket reference ID or describe any urgent hardware grievance. Rayyan Ahmed (Operations Director) and our warranty desk are also monitoring this chat channel.",
                "timestamp": "10:15 AM",
                "status": "read"
            }
        ]
        chats_col.insert_many(initial_msgs)
        messages = initial_msgs
    
    return {"messages": clean_docs(messages), "client_id": cid}

@router.post("/chat/live/send")
async def send_live_chat_message(request: Request):
    user = AuthManager.get_current_user(request)
    reject_read_only_judge(user)
    body = await request.json()
    message_text = (body.get("message") or "").strip()
    is_staff = bool(user and user.get("role") in ["admin", "agent", "warranty_manager"])
    client_id = (body.get("client_id") if is_staff else (user.get("user_id") if user else "guest_client_001")) or "guest_client_001"
    sender_type = "agent" if is_staff else "customer"
    
    if not message_text:
        raise HTTPException(status_code=400, detail="Message text is required.")
    
    chats_col = get_live_chats_col()
    now_str = datetime.datetime.now().strftime("%I:%M %p")
    
    sender_name = (user.get("display_name") or user.get("username")) if user else "You (Valued Customer)"
    avatar = user.get("avatar") if user else "https://ui-avatars.com/api/?name=Customer&background=4f46e5&color=fff"
    
    msg_doc = {
        "msg_id": f"MSG-{int(datetime.datetime.now().timestamp()*1000)}",
        "client_id": client_id,
        "sender": sender_type,
        "sender_name": sender_name,
        "avatar": avatar,
        "message": message_text,
        "timestamp": now_str,
        "status": "delivered"
    }
    
    chats_col.insert_one(msg_doc)
    
    try:
        await ws_manager.broadcast({
            "type": "LIVE_CHAT_MESSAGE",
            "message": clean_doc(msg_doc)
        })
    except Exception as e:
        logger.warning(f"Error broadcasting WS live chat: {e}")
    
    if sender_type == "customer":
        return {"success": True, "message": clean_doc(msg_doc)}
        async def delayed_agent_ack():
            await asyncio.sleep(1.8)
            ack_msg = {
                "msg_id": f"MSG-{int(datetime.datetime.now().timestamp()*1000)+1}",
                "client_id": client_id,
                "sender": "agent",
                "sender_name": "Marcus Chen",
                "sender_role": "Lead Triage Specialist",
                "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=160&auto=format&fit=crop&q=80",
                "message": "Received your update. Marcus Chen and Rayyan Ahmed have logged this in the priority queue and are reviewing your ticket right now.",
                "timestamp": datetime.datetime.now().strftime("%I:%M %p"),
                "status": "read"
            }
            chats_col.insert_one(ack_msg)
            try:
                await ws_manager.broadcast({
                    "type": "LIVE_CHAT_MESSAGE",
                    "message": clean_doc(ack_msg)
                })
            except Exception as e:
                logger.warning(f"Error broadcasting delayed agent ack: {e}")
        asyncio.create_task(delayed_agent_ack())

    return {"success": True, "message": clean_doc(msg_doc)}

@router.post("/chat/upload-file")
async def upload_chat_file(request: Request, file: UploadFile = File(...)):
    reject_read_only_judge(AuthManager.get_current_user(request))
    uploads_dir = os.path.join("static", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    filename = f"{int(datetime.datetime.now().timestamp()*1000)}_{file.filename}"
    filepath = os.path.join(uploads_dir, filename)
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)
    file_url = f"/static/uploads/{filename}"
    is_img = bool(file.content_type and file.content_type.startswith("image/"))
    return {
        "success": True,
        "file_url": file_url,
        "filename": file.filename,
        "is_image": is_img
    }

@router.get("/chat/live/conversations")
async def get_all_live_conversations(request: Request):
    user = AuthManager.get_current_user(request)
    if not user or user.get("role") not in ["admin", "agent", "warranty_manager"]:
        raise HTTPException(status_code=403, detail="Staff permissions required.")
    
    chats_col = get_live_chats_col()
    all_msgs = list(chats_col.find())
    
    conversations = {}
    for m in all_msgs:
        cid = m.get("client_id", "default")
        if cid not in conversations:
            conversations[cid] = []
        conversations[cid].append(clean_doc(m))
    
    return {"conversations": conversations, "total_clients": len(conversations)}

@router.get("/staff/presence")
async def get_staff_presence():
    return {"presence": STAFF_PRESENCE}

@router.post("/staff/presence/toggle", dependencies=[Depends(require_roles("admin", "agent", "warranty_manager"))])
async def toggle_staff_presence(request: Request):
    user = AuthManager.get_current_user(request)
    role = user.get("role")
    
    current_status = STAFF_PRESENCE[role]["online"]
    STAFF_PRESENCE[role]["online"] = not current_status
    
    try:
        await ws_manager.broadcast({
            "type": "STAFF_PRESENCE_UPDATE",
            "presence": STAFF_PRESENCE
        })
    except Exception as e:
        logger.warning(f"Error broadcasting staff presence toggle: {e}")
        
    return {"success": True, "role": role, "online": STAFF_PRESENCE[role]["online"], "presence": STAFF_PRESENCE}

@router.post("/call/initiate")
async def initiate_voice_call(request: Request):
    reject_read_only_judge(AuthManager.get_current_user(request))
    client_id, client_name, new_guest_id = get_call_client_context(request)
    
    target_role = None
    target_staff = None
    
    if STAFF_PRESENCE["admin"]["online"]:
        target_role = "admin"
        target_staff = STAFF_PRESENCE["admin"]
    elif STAFF_PRESENCE["agent"]["online"]:
        target_role = "agent"
        target_staff = STAFF_PRESENCE["agent"]
    elif STAFF_PRESENCE["warranty_manager"]["online"]:
        target_role = "warranty_manager"
        target_staff = STAFF_PRESENCE["warranty_manager"]
    
    if not target_role:
        response = JSONResponse({
            "status": "unavailable",
            "message": "No support staff are available to receive a call request right now."
        })
        set_guest_call_cookie(response, new_guest_id, request)
        return response
    
    call_id = f"CALL-{int(datetime.datetime.now().timestamp()*1000)}"
    call_obj = {
        "call_id": call_id,
        "client_id": client_id,
        "client_name": client_name,
        "target_role": target_role,
        "target_staff": target_staff,
        "status": "ringing",
        "timestamp": datetime.datetime.now().strftime("%I:%M:%S %p"),
        "start_time": None
    }
    
    ACTIVE_CALLS[call_id] = call_obj
    ACTIVE_CALLS["current"] = call_obj
    
    try:
        await ws_manager.broadcast({
            "type": "INCOMING_CALL",
            "call": call_obj
        })
    except Exception as e:
        logger.warning(f"Error broadcasting incoming call: {e}")
        
    response = JSONResponse({
        "status": "ringing",
        "call_id": call_id,
        "target_staff": target_staff,
        "message": "Call request sent; live audio is not connected."
    })
    set_guest_call_cookie(response, new_guest_id, request)
    return response

@router.post("/call/accept", dependencies=[Depends(require_roles("admin", "agent", "warranty_manager"))])
async def accept_voice_call(request: Request):
    body = await request.json()
    call_id = body.get("call_id") or (ACTIVE_CALLS.get("current", {}).get("call_id"))
    
    if not call_id or call_id not in ACTIVE_CALLS:
        raise HTTPException(status_code=404, detail="Active call not found")
    
    ACTIVE_CALLS[call_id]["status"] = "connected"
    ACTIVE_CALLS[call_id]["start_time"] = datetime.datetime.now().strftime("%I:%M:%S %p")
    
    try:
        await ws_manager.broadcast({
            "type": "CALL_ACCEPTED",
            "call": ACTIVE_CALLS[call_id]
        })
    except Exception as e:
        logger.warning(f"Error broadcasting call accepted: {e}")
        
    return {"success": True, "call": ACTIVE_CALLS[call_id]}

@router.post("/call/decline", dependencies=[Depends(require_roles("admin", "agent", "warranty_manager"))])
async def decline_voice_call(request: Request):
    body = await request.json()
    call_id = body.get("call_id") or (ACTIVE_CALLS.get("current", {}).get("call_id"))
    
    if call_id and call_id in ACTIVE_CALLS:
        ACTIVE_CALLS[call_id]["status"] = "declined"
        try:
            await ws_manager.broadcast({
                "type": "CALL_DECLINED",
                "call": ACTIVE_CALLS[call_id]
            })
        except Exception as e:
            logger.warning(f"Error broadcasting call declined: {e}")
        del ACTIVE_CALLS[call_id]
    
    if ACTIVE_CALLS.get("current", {}).get("call_id") == call_id:
        ACTIVE_CALLS.pop("current", None)
        
    return {"success": True, "message": "Call declined"}

@router.post("/call/end", dependencies=[Depends(require_roles("admin", "agent", "warranty_manager"))])
async def end_voice_call(request: Request):
    body = await request.json()
    call_id = body.get("call_id") or (ACTIVE_CALLS.get("current", {}).get("call_id"))
    
    if call_id and call_id in ACTIVE_CALLS:
        ACTIVE_CALLS[call_id]["status"] = "ended"
        try:
            await ws_manager.broadcast({
                "type": "CALL_ENDED",
                "call": ACTIVE_CALLS[call_id]
            })
        except Exception as e:
            logger.warning(f"Error broadcasting call ended: {e}")
        del ACTIVE_CALLS[call_id]
        
    if ACTIVE_CALLS.get("current", {}).get("call_id") == call_id:
        ACTIVE_CALLS.pop("current", None)
        
    return {"success": True, "message": "Call ended"}

@router.get("/call/status")
async def get_call_status(request: Request):
    client_id, _, new_guest_id = get_call_client_context(request)
    user = AuthManager.get_current_user(request)
    is_staff = bool(user and user.get("role") in ["admin", "agent", "warranty_manager"])
    current = ACTIVE_CALLS.get("current") if is_staff else next(
        (call for call in reversed(list(ACTIVE_CALLS.values())) if isinstance(call, dict) and call.get("client_id") == client_id),
        None,
    )
    if not current:
        response = JSONResponse({"active": False, "status": "none"})
    else:
        response = JSONResponse({"active": True, "call": current})
    set_guest_call_cookie(response, new_guest_id, request)
    return response

@router.get("/communication/threads", dependencies=[Depends(require_roles("admin", "agent", "warranty_manager"))])
async def get_communication_threads(limit: int = 50):
    col = get_complaints_col()
    raw = list(col.find({}, limit=limit, sort=[("created_at", -1)]))
    threads = []
    for c in raw:
        msgs = c.get("messages", [])
        last_msg = msgs[-1]["text"] if msgs else (c.get("complaint_description", "")[:90] + "...")
        threads.append({
            "complaint_id": c.get("complaint_id"),
            "customer_name": c.get("customer_name"),
            "customer_email": c.get("customer_email"),
            "customer_phone": c.get("customer_phone") or "Not provided",
            "customer_type": c.get("customer_type", "Standard"),
            "channel": c.get("preferred_channel", "Web Form"),
            "complaint_title": c.get("complaint_title"),
            "category": c.get("category", "General"),
            "urgency": c.get("urgency", "Medium"),
            "priority": c.get("priority", "P2"),
            "status": c.get("status", "New"),
            "last_message": last_msg,
            "created_at": c.get("created_at")
        })
    return {"threads": threads, "total": len(threads)}

@router.get("/communication/thread/{complaint_id}", dependencies=[Depends(require_roles("admin", "agent", "warranty_manager"))])
async def get_communication_thread_details(complaint_id: str):
    col = get_complaints_col()
    doc = col.find_one({"complaint_id": complaint_id.strip()})
    if not doc:
        raise HTTPException(status_code=404, detail="Complaint thread not found.")
    
    messages = doc.get("messages", [])
    if not messages:
        messages = [
            {
                "id": "msg-1",
                "sender": "customer",
                "sender_name": doc.get("customer_name", "Customer"),
                "text": doc.get("complaint_description", ""),
                "timestamp": doc.get("created_at", "Just now"),
                "channel": doc.get("preferred_channel", "Web Portal")
            }
        ]
        ai_resp = doc.get("genai_analysis", {}).get("customer_response")
        if ai_resp and doc.get("status") in ["Resolved", "Analyzed"]:
            messages.append({
                "id": "msg-2",
                "sender": "agent",
                "sender_name": "NovaTech Support Specialist",
                "text": ai_resp,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "channel": "Email / Web Ticket"
            })
    
    call_transcript = []
    return {
        "complaint_id": doc.get("complaint_id"),
        "customer_name": doc.get("customer_name"),
        "customer_email": doc.get("customer_email"),
        "customer_phone": doc.get("customer_phone") or "Not provided",
        "customer_type": doc.get("customer_type", "Standard"),
        "product_or_service": doc.get("product_or_service", "General Item"),
        "category": doc.get("category", "General"),
        "department": doc.get("department", "Customer Care"),
        "urgency": doc.get("urgency", "Medium"),
        "priority": doc.get("priority", "P2"),
        "status": doc.get("status", "New"),
        "messages": messages,
        "ai_suggested_draft": doc.get("genai_analysis", {}).get("customer_response") or "",
        "call_transcript": call_transcript,
        "sentiment": doc.get("genai_analysis", {}).get("sentiment", "Neutral")
    }

@router.post("/communication/send", dependencies=[Depends(require_roles("admin", "agent", "warranty_manager"))])
async def send_communication_message(
    complaint_id: str = Form(...),
    message_text: str = Form(...),
    channel: str = Form("Web Portal")
):
    col = get_complaints_col()
    doc = col.find_one({"complaint_id": complaint_id.strip()})
    if not doc:
        raise HTTPException(status_code=404, detail="Complaint not found.")

    new_msg = {
        "id": f"msg-{int(datetime.datetime.now().timestamp())}",
        "sender": "agent",
        "sender_name": "NovaTech Support Agent",
        "text": message_text.strip(),
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "channel": channel
    }

    col.update_one({"complaint_id": complaint_id}, {"$push": {"messages": new_msg}})

    audit_col = get_audit_logs_col()
    audit_col.insert_one({
        "log_id": f"AUD-COMM-{int(datetime.datetime.now().timestamp())}",
        "complaint_id": complaint_id,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "actor": "Support Agent",
        "action": f"Sent Message ({channel})",
        "details": {"message_snippet": message_text[:80]}
    })

    return {"success": True, "message": new_msg}
