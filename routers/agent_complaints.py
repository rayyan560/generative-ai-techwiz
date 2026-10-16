from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from config.database import get_complaints_col
from routers.common import clean_doc, clean_docs
from src.analytics.sentiment import SentimentTelemetryEngine
from src.comparison_engine.engine import ComparisonEngine
from src.genai_pipeline.pipeline import GenAIUnavailableError, genai_pipeline
from src.python_validation.pipeline import python_validation_pipeline
from src.security.auth import AuthManager
from src.security.permissions import require_roles


router = APIRouter(
    prefix="/api",
    tags=["Agent"],
    dependencies=[Depends(require_roles("admin", "agent", "warranty_manager"))],
)


@router.get("/complaints")
async def list_complaints(
    search: Optional[str] = None,
    category: Optional[str] = None,
    department: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=200),
):
    filters = {
        name: value
        for name, value in (("category", category), ("department", department), ("priority", priority), ("status", status))
        if value and value != "All"
    }
    docs = clean_docs(list(get_complaints_col().find(filters, sort=[("created_at", -1)], limit=limit)))
    for doc in docs:
        if not doc.get("sentiment_telemetry"):
            doc["sentiment_telemetry"] = SentimentTelemetryEngine.analyze(
                doc.get("complaint_title", ""),
                doc.get("complaint_description", ""),
                doc.get("customer_type", "Standard"),
            )
    if search:
        needle = search.casefold()
        docs = [
            doc for doc in docs
            if any(needle in str(doc.get(field, "")).casefold() for field in ("complaint_id", "complaint_title", "customer_name"))
        ]
    return {"complaints": docs, "total": len(docs)}


@router.get("/complaints/{complaint_id}")
async def get_complaint_details(request: Request, complaint_id: str):
    complaints = get_complaints_col()
    doc = complaints.find_one({"complaint_id": complaint_id.strip()})
    if not doc:
        raise HTTPException(status_code=404, detail="Complaint not found.")
    user = AuthManager.get_current_user(request)
    needs_update = False
    if not doc.get("sentiment_telemetry"):
        doc["sentiment_telemetry"] = SentimentTelemetryEngine.analyze(
            doc.get("complaint_title", ""), doc.get("complaint_description", ""), doc.get("customer_type", "Standard")
        )
        needs_update = True
    if "genai_analysis" not in doc or "ground_truth" not in doc:
        needs_update = True
        ground_truth = python_validation_pipeline.validate_complaint(doc)
        doc.update({
            "ground_truth": ground_truth.model_dump(),
            "category": ground_truth.expected_category,
            "subcategory": ground_truth.expected_subcategory,
            "department": ground_truth.expected_department,
            "urgency": ground_truth.expected_urgency,
            "priority": ground_truth.expected_priority,
        })
        try:
            genai_result = genai_pipeline.generate_intelligence(doc)
        except GenAIUnavailableError as error:
            doc["status"] = "Manual Review Required"
            doc["analysis_error"] = str(error)
        else:
            comparison = ComparisonEngine.compare_and_verify(genai_result, ground_truth, doc)
            doc["genai_analysis"] = genai_result.model_dump()
            doc["comparison"] = comparison.model_dump()
            doc["status"] = "Manual Review Required" if comparison.requires_manual_review else "Analyzed"
    if needs_update and user.get("role") != "judge":
        complaints.update_one({"complaint_id": complaint_id}, {"$set": doc})
    return clean_doc(doc)
