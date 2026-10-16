from fastapi import APIRouter

from routers.complaint_pipeline import process_complaint_background as _process_complaint_bg
from routers.complaint_precheck import pre_check_complaint, router as precheck_router
from routers.complaint_submission import router as submission_router
from routers.complaint_tracking import router as tracking_router
from routers.complaint_vision import router as vision_router
from routers.product_catalog import router as product_router


router = APIRouter()
for route_group in (product_router, submission_router, tracking_router, vision_router, precheck_router):
    router.include_router(route_group)
