import os
import secrets
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File

from config.database import get_live_chats_col
from routers.chat_state import STAFF_PRESENCE
from routers.common import clean_doc, ws_manager
from src.security.auth import AuthManager
from src.security.permissions import require_roles


router = APIRouter(prefix="/api", tags=["Live Chat & Staff Presence"])
logger = logging.getLogger("SupportNova.ChatStaff")


@router.post("/chat/upload-file")
async def upload_chat_file(request: Request, file: UploadFile = File(...)):
    user = AuthManager.get_current_user(request)
    if user and user.get("role") == "judge":
        raise HTTPException(status_code=403, detail="Judge access is read-only.")
    content = await file.read(10 * 1024 * 1024 + 1)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Chat attachments must be 10 MB or smaller.")
    original_name = (file.filename or "attachment").replace("\\", "/")
    safe_name = os.path.basename(original_name) or "attachment"
    extension = os.path.splitext(safe_name)[1].lower()
    allowed_extensions = {".csv", ".doc", ".docx", ".gif", ".jpeg", ".jpg", ".pdf", ".png", ".txt", ".webp"}
    if extension not in allowed_extensions:
        raise HTTPException(status_code=415, detail="Use a supported image or document attachment.")
    uploads_dir = os.path.join("static", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    filename = f"{secrets.token_urlsafe(18)}{extension}"
    with open(os.path.join(uploads_dir, filename), "wb") as uploaded_file:
        uploaded_file.write(content)
    return {
        "success": True,
        "file_url": f"/static/uploads/{filename}",
        "filename": safe_name,
        "is_image": bool(file.content_type and file.content_type.startswith("image/")),
    }


@router.get("/chat/live/conversations")
async def get_all_live_conversations(request: Request):
    user = AuthManager.get_current_user(request)
    if not user or user.get("role") not in {"admin", "agent", "warranty_manager"}:
        raise HTTPException(status_code=403, detail="Staff permissions required.")
    conversations = {}
    for message in get_live_chats_col().find():
        client_id = message.get("client_id", "default")
        conversations.setdefault(client_id, []).append(clean_doc(message))
    return {"conversations": conversations, "total_clients": len(conversations)}


@router.get("/staff/presence")
async def get_staff_presence():
    return {"presence": STAFF_PRESENCE}


@router.post("/staff/presence/toggle", dependencies=[Depends(require_roles("admin", "agent", "warranty_manager"))])
async def toggle_staff_presence(request: Request):
    role = AuthManager.get_current_user(request).get("role")
    STAFF_PRESENCE[role]["online"] = not STAFF_PRESENCE[role]["online"]
    try:
        await ws_manager.broadcast({"type": "STAFF_PRESENCE_UPDATE", "presence": STAFF_PRESENCE})
    except Exception as error:
        logger.warning("Staff presence broadcast failed: %s", type(error).__name__)
    return {"success": True, "role": role, "online": STAFF_PRESENCE[role]["online"], "presence": STAFF_PRESENCE}
