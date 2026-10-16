from fastapi import APIRouter

from routers.knowledge_queries import router as query_router
from routers.knowledge_upload import router as upload_router


router = APIRouter()
router.include_router(upload_router)
router.include_router(query_router)
