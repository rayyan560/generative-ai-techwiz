import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, Request

from routers.chat_state import ACTIVE_CALLS
from routers.common import ws_manager
from src.security.permissions import require_roles


router = APIRouter(prefix="/api", tags=["Staff Calls"])
staff_only = [Depends(require_roles("admin", "agent", "warranty_manager"))]
logger = logging.getLogger("SupportNova.CallStaff")


@router.post("/call/accept", dependencies=staff_only)
async def accept_voice_call(request: Request):
    body = await request.json()
    call_id = body.get("call_id") or ACTIVE_CALLS.get("current", {}).get("call_id")
    if not call_id or call_id not in ACTIVE_CALLS:
        raise HTTPException(status_code=404, detail="Active call not found")
    ACTIVE_CALLS[call_id]["status"] = "connected"
    ACTIVE_CALLS[call_id]["start_time"] = datetime.datetime.now().strftime("%I:%M:%S %p")
    try:
        await ws_manager.broadcast({"type": "CALL_ACCEPTED", "call": ACTIVE_CALLS[call_id]})
    except Exception as error:
        logger.warning("Call acceptance broadcast failed: %s", type(error).__name__)
    return {"success": True, "call": ACTIVE_CALLS[call_id]}


async def _finish_call(request: Request, status: str, event: str, message: str):
    body = await request.json()
    call_id = body.get("call_id") or ACTIVE_CALLS.get("current", {}).get("call_id")
    call = ACTIVE_CALLS.get(call_id) if call_id else None
    if call:
        call["status"] = status
        try:
            await ws_manager.broadcast({"type": event, "call": call})
        except Exception as error:
            logger.warning("Call status broadcast failed: %s", type(error).__name__)
        ACTIVE_CALLS.pop(call_id, None)
    if ACTIVE_CALLS.get("current", {}).get("call_id") == call_id:
        ACTIVE_CALLS.pop("current", None)
    return {"success": True, "message": message}


@router.post("/call/decline", dependencies=staff_only)
async def decline_voice_call(request: Request):
    return await _finish_call(request, "declined", "CALL_DECLINED", "Call declined")


@router.post("/call/end", dependencies=staff_only)
async def end_voice_call(request: Request):
    return await _finish_call(request, "ended", "CALL_ENDED", "Call ended")
