from fastapi import APIRouter, Depends, Form, HTTPException

from config.database import get_complaints_col
from src.analytics.defect_radar import DefectRadarEngine
from src.security.permissions import require_roles


router = APIRouter(
    prefix="/api",
    tags=["Analytics & Financial Refunds"],
    dependencies=[Depends(require_roles("admin", "warranty_manager"))],
)


@router.get("/escrow/clv-optimizer/{complaint_id}")
async def get_clv_settlement_options(complaint_id: str):
    if not get_complaints_col().find_one({"complaint_id": complaint_id.strip()}):
        raise HTTPException(status_code=404, detail="Complaint not found.")
    return {
        "available": False,
        "reason": "A verified transaction amount and validated customer history are required; no live payment or retention model is connected.",
    }


@router.get("/analytics/defect-radar")
async def get_defect_radar():
    complaints = list(get_complaints_col().find({}, limit=550))
    return DefectRadarEngine.generate_defect_radar(complaints)


@router.post("/translate")
async def translate_text(text: str = Form(...), target_lang: str = Form("en")):
    raise HTTPException(status_code=503, detail="Translation service is not configured.")
