import datetime
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from routers.chat_state import ACTIVE_CALLS, STAFF_PRESENCE, get_call_client_context, reject_read_only_judge, set_guest_call_cookie
from routers.common import ws_manager
from src.security.auth import AuthManager


router = APIRouter(prefix="/api", tags=["Staff Calls"])
logger = logging.getLogger("SupportNova.CallClient")


@router.post("/call/initiate")
async def initiate_voice_call(request: Request):
    reject_read_only_judge(AuthManager.get_current_user(request))
    client_id, client_name, new_guest_id = get_call_client_context(request)
    target_role = next((role for role in ("admin", "agent", "warranty_manager") if STAFF_PRESENCE[role]["online"]), None)
    if not target_role:
        response = JSONResponse({"status": "unavailable", "message": "No support staff are available to receive a call request right now."})
        set_guest_call_cookie(response, new_guest_id, request)
        return response

    target_staff = STAFF_PRESENCE[target_role]
    call_id = f"CALL-{int(datetime.datetime.now().timestamp() * 1000)}"
    call = {
        "call_id": call_id,
        "client_id": client_id,
        "client_name": client_name,
        "target_role": target_role,
        "target_staff": target_staff,
        "status": "ringing",
        "timestamp": datetime.datetime.now().strftime("%I:%M:%S %p"),
        "start_time": None,
    }
    ACTIVE_CALLS[call_id] = call
    ACTIVE_CALLS["current"] = call
    try:
        await ws_manager.broadcast({"type": "INCOMING_CALL", "call": call})
    except Exception as error:
        logger.warning("Incoming call broadcast failed: %s", type(error).__name__)
    response = JSONResponse({"status": "ringing", "call_id": call_id, "target_staff": target_staff, "message": "Call request sent; live audio is not connected."})
    set_guest_call_cookie(response, new_guest_id, request)
    return response


@router.get("/call/status")
async def get_call_status(request: Request):
    client_id, _, new_guest_id = get_call_client_context(request)
    user = AuthManager.get_current_user(request)
    is_staff = bool(user and user.get("role") in {"admin", "agent", "warranty_manager"})
    current = ACTIVE_CALLS.get("current") if is_staff else next(
        (call for call in reversed(list(ACTIVE_CALLS.values())) if isinstance(call, dict) and call.get("client_id") == client_id),
        None,
    )
    response = JSONResponse({"active": bool(current), **({"call": current} if current else {"status": "none"})})
    set_guest_call_cookie(response, new_guest_id, request)
    return response
