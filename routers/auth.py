from fastapi import APIRouter

from routers.auth_google import router as google_router
from routers.auth_profile import router as profile_router
from routers.auth_sessions import router as sessions_router


router = APIRouter()
for route_group in (sessions_router, google_router, profile_router):
    router.include_router(route_group)
