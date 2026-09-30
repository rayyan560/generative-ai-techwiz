from fastapi import APIRouter, Request, HTTPException, Form, Depends
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import datetime
import logging
from statistics import mean

from config.database import get_complaints_col, get_audit_logs_col
from config.settings import settings
from src.genai_pipeline.pipeline import GenAIUnavailableError, genai_pipeline
from src.python_validation.pipeline import python_validation_pipeline
from src.comparison_engine.engine import ComparisonEngine
from src.analytics.sentiment import SentimentTelemetryEngine
from routers.common import clean_doc, clean_docs, ws_manager
from src.security.permissions import require_roles

logger = logging.getLogger("SupportNova.AgentRouter")

router = APIRouter(
    prefix="/api",
    tags=["Agent"],
    dependencies=[Depends(require_roles("admin", "agent", "warranty_manager"))]
)

def _parse_timestamp(value):
    if not value:
        return None
    try:
        return datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


async def calculate_avg_inspection_time() -> Optional[str]:
    col = get_complaints_col()
    durations = []
    start_fields = ("review_started_at", "triage_started_at", "created_at")
    end_fields = ("review_completed_at", "triage_completed_at", "resolved_at")
    for record in col.find({}, limit=2000):
        start = next((_parse_timestamp(record.get(field)) for field in start_fields if record.get(field)), None)
        end = next((_parse_timestamp(record.get(field)) for field in end_fields if record.get(field)), None)
        if start and end:
            duration = (end - start).total_seconds() / 60
            if 0 <= duration <= 24 * 60:
                durations.append(duration)
    return f"{mean(durations):.1f} mins" if durations else None

async def calculate_accuracy_pct() -> Optional[float]:
    col = get_complaints_col()
    scores = []
    for record in col.find({}, limit=2000):
        comparison = record.get("comparison") or {}
        score = comparison.get("consistency_score")
        if isinstance(score, (int, float)) and 0 <= score <= 100:
            scores.append(float(score))
    return round(mean(scores), 1) if scores else None

@router.get("/agent/stats")
async def get_agent_stats():
    """Real backing API for agent dashboard stats (Issue 9 fix)."""
    col = get_complaints_col()
    resolved_count = col.count_documents({"status": {"$in": ["Resolved", "Refund Approved"]}})
    pending_count = col.count_documents({"status": {"$in": ["Analyzed", "Manual Review Required", "Escalated"]}})
    avg_time = await calculate_avg_inspection_time()
    accuracy = await calculate_accuracy_pct()
    critical_count = col.count_documents({"priority": "P0", "status": {"$nin": ["Resolved", "Refund Approved"]}})
    
    return {
        "resolved_cases": resolved_count,
        "pending_reviews": pending_count,
        "critical_alerts": critical_count,
        "avg_inspection_time": avg_time,
        "accuracy_pct": accuracy
    }

@router.get("/complaints")
async def list_complaints(
    search: Optional[str] = None,
    category: Optional[str] = None,
    department: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
):
    col = get_complaints_col()
    filter_dict = {}
    if category and category != "All":
        filter_dict["category"] = category
    if department and department != "All":
        filter_dict["department"] = department
    if priority and priority != "All":
        filter_dict["priority"] = priority
    if status and status != "All":
        filter_dict["status"] = status

    raw_docs = list(col.find(filter_dict, sort=[("created_at", -1)], limit=limit))
    docs = clean_docs(raw_docs)
    
    for d in docs:
        if "sentiment_telemetry" not in d or not d["sentiment_telemetry"]:
            d["sentiment_telemetry"] = SentimentTelemetryEngine.analyze(
                d.get("complaint_title", ""),
                d.get("complaint_description", ""),
                d.get("customer_type", "Standard")
            )

    if search:
        s_lower = search.lower()
        docs = [d for d in docs if s_lower in d.get("complaint_id", "").lower() or s_lower in d.get("complaint_title", "").lower() or s_lower in d.get("customer_name", "").lower()]
        
    return {"complaints": docs, "total": len(docs)}

@router.get("/complaints/{complaint_id}")
async def get_complaint_details(complaint_id: str):
    col = get_complaints_col()
    doc = col.find_one({"complaint_id": complaint_id.strip()})
    if not doc:
        raise HTTPException(status_code=404, detail="Complaint not found.")
    
    if "sentiment_telemetry" not in doc or not doc["sentiment_telemetry"]:
        doc["sentiment_telemetry"] = SentimentTelemetryEngine.analyze(
            doc.get("complaint_title", ""),
            doc.get("complaint_description", ""),
            doc.get("customer_type", "Standard")
        )
        col.update_one({"complaint_id": complaint_id}, {"$set": {"sentiment_telemetry": doc["sentiment_telemetry"]}})
    
    if "genai_analysis" not in doc or "ground_truth" not in doc:
        ground_truth = python_validation_pipeline.validate_complaint(doc)
        doc["ground_truth"] = ground_truth.model_dump()
        doc["category"] = ground_truth.expected_category
        doc["subcategory"] = ground_truth.expected_subcategory
        doc["department"] = ground_truth.expected_department
        doc["urgency"] = ground_truth.expected_urgency
        doc["priority"] = ground_truth.expected_priority
        try:
            genai_out = genai_pipeline.generate_intelligence(doc)
        except GenAIUnavailableError as error:
            doc["status"] = "Manual Review Required"
            doc["analysis_error"] = str(error)
        else:
            comp_result = ComparisonEngine.compare_and_verify(genai_out, ground_truth, doc)
            doc["genai_analysis"] = genai_out.model_dump()
            doc["comparison"] = comp_result.model_dump()
            doc["status"] = "Analyzed" if not comp_result.requires_manual_review else "Manual Review Required"
        col.update_one({"complaint_id": complaint_id}, {"$set": doc})

    return clean_doc(doc)

@router.post("/complaints/{complaint_id}/triage", dependencies=[Depends(require_roles("admin", "agent"))])
async def triage_complaint(
    request: Request,
    complaint_id: str,
    action: str = Form(...),
    reviewer_notes: Optional[str] = Form(""),
    response_draft: Optional[str] = Form(None),
    new_department: Optional[str] = Form(None),
    new_category: Optional[str] = Form(None)
):
    col = get_complaints_col()
    doc = col.find_one({"complaint_id": complaint_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Complaint not found.")
    if action not in {"approve", "override_refund", "escalate", "reassign", "close", "regenerate"}:
        raise HTTPException(status_code=400, detail="Unsupported review action.")

    update_payload = {"last_modified": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    
    if action == "approve":
        update_payload["status"] = "Agent Reviewed"
        update_payload["reviewer_decision"] = "Review recorded; customer response has not been sent"
    elif action == "override_refund":
        gt = doc.get("ground_truth") or {}
        if not gt.get("refund_eligible") or not doc.get("payment_verified") or doc.get("verified_transaction_amount") is None:
            raise HTTPException(status_code=409, detail="Verified payment and policy eligibility are required before refund approval.")
        update_payload["status"] = "Refund Approval Pending"
        update_payload["escrow_status"] = "Approval Recorded — payment pending integration"
        update_payload["reviewer_decision"] = "Refund approval recorded; external payment not executed"
    elif action == "escalate":
        update_payload["status"] = "Escalated"
        update_payload["reviewer_decision"] = "Escalated to Tier 3 Management"
    elif action == "reassign":
        if new_department not in settings.DEPARTMENTS:
            raise HTTPException(status_code=400, detail="Choose a configured department.")
        update_payload["department"] = new_department
        update_payload["status"] = "Reassigned"
    elif action == "close":
        update_payload["status"] = "Closed"
    elif action == "regenerate":
        ground_truth = python_validation_pipeline.validate_complaint(doc)
        update_payload["ground_truth"] = ground_truth.model_dump()
        try:
            genai_out = genai_pipeline.generate_intelligence(doc)
        except GenAIUnavailableError:
            update_payload["status"] = "Manual Review Required"
            update_payload["analysis_error"] = "GenAI is unavailable; Python ground truth was refreshed."
        else:
            comp_result = ComparisonEngine.compare_and_verify(genai_out, ground_truth, doc)
            update_payload["genai_analysis"] = genai_out.model_dump()
            update_payload["comparison"] = comp_result.model_dump()
            update_payload["status"] = "Analyzed" if not comp_result.requires_manual_review else "Manual Review Required"

    if response_draft is not None:
        update_payload["customer_response_draft"] = response_draft[:5000]

    if reviewer_notes:
        update_payload["reviewer_notes"] = reviewer_notes

    col.update_one({"complaint_id": complaint_id}, {"$set": update_payload})

    audit_col = get_audit_logs_col()
    audit_col.insert_one({
        "log_id": f"AUD-{datetime.datetime.now().timestamp()}",
        "complaint_id": complaint_id,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "actor": AuthManager.get_current_user(request).get("username", "Support staff"),
        "action": action,
        "details": update_payload
    })

    try:
        await ws_manager.broadcast({
            "type": "TRIAGE_ACTION_EXECUTED",
            "complaint_id": complaint_id,
            "action": action,
            "new_status": update_payload.get("status"),
            "timestamp": update_payload["last_modified"]
        })
    except Exception as e:
        logger.warning(f"Error broadcasting triage action: {e}")

    return {"success": True, "message": f"Action '{action}' executed successfully.", "complaint_id": complaint_id}
