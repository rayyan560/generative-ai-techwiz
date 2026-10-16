from typing import Optional

from fastapi import APIRouter, Form, HTTPException

from src.analytics.sentiment import SentimentTelemetryEngine
from src.complaint_processing.preprocessor import ComplaintPreprocessor
from src.python_validation.pipeline import python_validation_pipeline


router = APIRouter(prefix="/api", tags=["Complaint Pre-Check"])


@router.post("/complaints/pre-check")
async def pre_check_complaint(
    complaint_title: Optional[str] = Form(None),
    complaint_description: str = Form(...),
    customer_type: str = Form("Standard"),
):
    if not complaint_title or len(complaint_title.strip()) < 3:
        complaint_title = ComplaintPreprocessor.derive_complaint_title(complaint_description)
    is_valid, error = ComplaintPreprocessor.validate_complaint_input(complaint_title, complaint_description)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)
    complaint = {
        "complaint_title": complaint_title,
        "complaint_description": complaint_description,
        "customer_type": customer_type,
    }
    ground_truth = python_validation_pipeline.validate_complaint(complaint)
    sentiment = SentimentTelemetryEngine.analyze(complaint_title, complaint_description, customer_type)
    category = ground_truth.expected_category
    if category == "Safety Hazard":
        advisory = "A potential safety-related trigger was detected. Stop using the product if safe and wait for staff guidance; this is not a diagnosis."
    elif category in {"Account Security", "Data Privacy"}:
        advisory = "A security or privacy-related trigger was detected and may require priority staff review."
    elif ground_truth.mandatory_escalation:
        advisory = "A configured escalation trigger was detected; staff review is required."
    else:
        advisory = "This preliminary check did not detect a mandatory escalation trigger. Staff review may still change the assessment."
    return {
        "estimated_category": category,
        "estimated_priority": ground_truth.expected_priority,
        "estimated_urgency": ground_truth.expected_urgency,
        "estimated_sla": "Priority review target — not a guarantee" if ground_truth.expected_urgency in {"Critical", "High"} else "Standard review target — not a guarantee",
        "refund_eligibility_preview": ground_truth.refund_eligible,
        "sentiment": sentiment,
        "safety_advisory": advisory,
        "preview_basis": "Preliminary Python rules and text heuristics only; no GenAI analysis, live policy lookup, or approval was performed.",
    }
