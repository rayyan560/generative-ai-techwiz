from fastapi import APIRouter

from routers.agent_complaints import router as complaints_router
from routers.agent_stats import router as stats_router
from routers.agent_triage import router as triage_router


router = APIRouter()
for route_group in (stats_router, complaints_router, triage_router):
    router.include_router(route_group)
