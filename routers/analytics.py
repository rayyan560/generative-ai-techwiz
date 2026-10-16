from fastapi import APIRouter

from routers.analytics_reports import router as reports_router
from routers.analytics_tools import router as tools_router
from routers.refund_actions import router as refund_actions_router
from routers.refund_summary import router as refund_summary_router


router = APIRouter()
for route_group in (refund_summary_router, refund_actions_router, reports_router, tools_router):
    router.include_router(route_group)
