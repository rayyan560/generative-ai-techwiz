from fastapi import APIRouter

from routers.call_client import router as call_client_router
from routers.call_staff import router as call_staff_router
from routers.chat_communication import router as communication_router
from routers.chat_messages import router as messages_router
from routers.chat_staff import router as staff_router
from routers.chat_state import ACTIVE_CALLS, STAFF_PRESENCE


router = APIRouter()
for route_group in (messages_router, staff_router, call_client_router, call_staff_router, communication_router):
    router.include_router(route_group)
