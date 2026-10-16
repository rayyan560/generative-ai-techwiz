import datetime
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request

from config.database import get_audit_logs_col, get_complaints_col
from config.settings import settings
from routers.common import ws_manager
from src.comparison_engine.engine import ComparisonEngine
from src.genai_pipeline.pipeline import GenAIUnavailableError, genai_pipeline
from src.python_validation.pipeline import python_validation_pipeline
from src.security.auth import AuthManager
from src.security.permissions import require_roles


logger = logging.getLogger("SupportNova.AgentTriage")
router = APIRouter(
    prefix="/api",
    tags=["Agent"],
    dependencies=[Depends(require_roles("admin", "agent", "warranty_manager"))],
)


@router.post("/complaints/{complaint_id}/triage", dependencies=[Depends(require_roles("admin", "agent"))])
async def triage_complaint(
    request: Request,
    complaint_id: str,
    action: str = Form(...),
    reviewer_notes: Optional[str] = Form(""),
    response_draft: Optional[str] = Form(None),
    new_department: Optional[str] = Form(None),
    new_category: Optional[str] = Form(None),
):
    complaints = get_complaints_col()
    doc = complaints.find_one({"complaint_id": complaint_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Complaint not found.")
    if action not in {"approve", "override_refund", "escalate", "reassign", "close", "regenerate"}:
        raise HTTPException(status_code=400, detail="Unsupported review action.")
    update = {"last_modified": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    if action == "approve":
        update.update(status="Agent Reviewed", reviewer_decision="Review recorded; customer response has not been sent")
    elif action == "override_refund":
        ground_truth = doc.get("ground_truth") or {}
        if not ground_truth.get("refund_eligible") or not doc.get("payment_verified") or doc.get("verified_transaction_amount") is None:
            raise HTTPException(status_code=409, detail="Verified payment and policy eligibility are required before refund approval.")
        update.update(status="Refund Approval Pending", escrow_status="Approval Recorded — payment pending integration", reviewer_decision="Refund approval recorded; external payment not executed")
    elif action == "escalate":
        update.update(status="Escalated", reviewer_decision="Escalated to Tier 3 Management")
    elif action == "reassign":
        if new_department not in settings.DEPARTMENTS:
            raise HTTPException(status_code=400, detail="Choose a configured department.")
        update.update(department=new_department, status="Reassigned")
    elif action == "close":
        update["status"] = "Closed"
    else:
        _regenerate_analysis(doc, update)
    if response_draft is not None:
        update["customer_response_draft"] = response_draft[:5000]
    if reviewer_notes:
        update["reviewer_notes"] = reviewer_notes
    complaints.update_one({"complaint_id": complaint_id}, {"$set": update})
    get_audit_logs_col().insert_one({
        "log_id": f"AUD-{datetime.datetime.now().timestamp()}",
        "complaint_id": complaint_id,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "actor": AuthManager.get_current_user(request).get("username", "Support staff"),
        "action": action,
        "details": update,
    })
    try:
        await ws_manager.broadcast({
            "type": "TRIAGE_ACTION_EXECUTED",
            "complaint_id": complaint_id,
            "action": action,
            "new_status": update.get("status"),
            "timestamp": update["last_modified"],
        })
    except Exception as error:
        logger.warning("Triage event broadcast failed (%s).", type(error).__name__)
    return {"success": True, "message": f"Action '{action}' executed successfully.", "complaint_id": complaint_id}


def _regenerate_analysis(doc, update):
    ground_truth = python_validation_pipeline.validate_complaint(doc)
    update["ground_truth"] = ground_truth.model_dump()
    try:
        genai_result = genai_pipeline.generate_intelligence(doc)
    except GenAIUnavailableError:
        update.update(status="Manual Review Required", analysis_error="GenAI is unavailable; Python ground truth was refreshed.")
        return
    comparison = ComparisonEngine.compare_and_verify(genai_result, ground_truth, doc)
    update["genai_analysis"] = genai_result.model_dump()
    update["comparison"] = comparison.model_dump()
    update["status"] = "Manual Review Required" if comparison.requires_manual_review else "Analyzed"
