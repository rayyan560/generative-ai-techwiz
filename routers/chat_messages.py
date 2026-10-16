import datetime
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from config.database import get_live_chats_col
from routers.chat_state import get_call_client_context, reject_read_only_judge, set_guest_call_cookie
from routers.common import clean_doc, clean_docs, ws_manager
from src.security.auth import AuthManager


logger = logging.getLogger("SupportNova.ChatMessages")
router = APIRouter(prefix="/api", tags=["Live Chat"])


@router.get("/chat/live/messages")
async def get_live_chat_messages(request: Request, client_id: Optional[str] = None):
    user = AuthManager.get_current_user(request)
    is_staff = bool(user and user.get("role") in {"admin", "agent", "warranty_manager"})
    guest_client_id, _, new_guest_id = get_call_client_context(request)
    client_id = (client_id if is_staff else (user.get("user_id") if user else guest_client_id)) or guest_client_id
    messages = list(get_live_chats_col().find({"client_id": client_id}))
    response = JSONResponse({"messages": clean_docs(messages), "client_id": client_id})
    set_guest_call_cookie(response, new_guest_id, request)
    return response


@router.post("/chat/live/send")
async def send_live_chat_message(request: Request):
    user = AuthManager.get_current_user(request)
    reject_read_only_judge(user)
    body = await request.json()
    if not isinstance(body, dict) or not isinstance(body.get("message"), str):
        raise HTTPException(status_code=400, detail="Message text is required.")
    message_text = body["message"].strip()
    if not message_text:
        raise HTTPException(status_code=400, detail="Message text is required.")
    if len(message_text) > 4000:
        raise HTTPException(status_code=413, detail="Messages must be 4,000 characters or shorter.")

    is_staff = bool(user and user.get("role") in {"admin", "agent", "warranty_manager"})
    guest_client_id, _, new_guest_id = get_call_client_context(request)
    client_id = (body.get("client_id") if is_staff else (user.get("user_id") if user else guest_client_id)) or guest_client_id
    sender_type = "agent" if is_staff else "customer"
    sender_name = (user.get("display_name") or user.get("username")) if user else "You (Valued Customer)"
    avatar = user.get("avatar") if user else "https://ui-avatars.com/api/?name=Customer&background=4f46e5&color=fff"
    now = datetime.datetime.now()
    msg_doc = {
        "msg_id": f"MSG-{int(now.timestamp() * 1000)}",
        "client_id": client_id,
        "sender": sender_type,
        "sender_name": sender_name,
        "avatar": avatar,
        "message": message_text,
        "timestamp": now.strftime("%I:%M %p"),
        "status": "delivered",
    }
    get_live_chats_col().insert_one(msg_doc)
    try:
        await ws_manager.broadcast({"type": "LIVE_CHAT_MESSAGE", "message": clean_doc(msg_doc)})
    except Exception as error:
        logger.warning("Live chat broadcast failed: %s", type(error).__name__)

    response = JSONResponse({"success": True, "message": clean_doc(msg_doc)})
    set_guest_call_cookie(response, new_guest_id, request)
    return response
