from fastapi import APIRouter, Request, HTTPException, Form, UploadFile, File, Depends, BackgroundTasks, Query
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import datetime
import logging

from config.database import get_complaints_col, get_audit_logs_col
from src.products.catalog import ProductCatalog
from src.complaint_processing.preprocessor import ComplaintPreprocessor
from src.complaint_processing.duplicates import identify_related_complaints
from src.genai_pipeline.pipeline import GenAIUnavailableError, genai_pipeline
from src.python_validation.pipeline import python_validation_pipeline
from src.comparison_engine.engine import ComparisonEngine
from src.analytics.sentiment import SentimentTelemetryEngine
from src.multimodal.vision_forensics import VisionForensicsEngine
from src.multimodal.image_validation import detect_image_type
from src.security.auth import AuthManager
from routers.common import clean_doc, clean_docs, ws_manager

logger = logging.getLogger("SupportNova.WarrantyRouter")

router = APIRouter(prefix="/api", tags=["Warranty & Customer Portal"])

@router.get("/products")
async def get_products():
    return {"products": ProductCatalog.get_all_products(), "total": len(ProductCatalog.get_all_products())}



async def _process_complaint_bg(complaint_dict, new_id, total_count, sentiment_data, image_bytes=None, image_mime_type=None):
    def blocking_pipeline():
        if image_bytes and image_mime_type:
            complaint_dict["vision_analysis"] = VisionForensicsEngine.analyze_image(
                image_bytes, image_mime_type, complaint_dict.get("complaint_description", "")
            )
        try:
            genai_out = genai_pipeline.generate_intelligence(complaint_dict)
            ground_truth = python_validation_pipeline.validate_complaint(complaint_dict)
            comp_result = ComparisonEngine.compare_and_verify(genai_out, ground_truth, complaint_dict)

            complaint_dict["genai_analysis"] = genai_out.model_dump()
            complaint_dict["ground_truth"] = ground_truth.model_dump()
            complaint_dict["comparison"] = comp_result.model_dump()
            complaint_dict["status"] = "Analyzed" if not comp_result.requires_manual_review else "Manual Review Required"
            if complaint_dict.get("vision_analysis", {}).get("manual_review_required"):
                complaint_dict["status"] = "Manual Review Required"
            complaint_dict["category"] = ground_truth.expected_category
            complaint_dict["subcategory"] = ground_truth.expected_subcategory
            complaint_dict["department"] = ground_truth.expected_department
            complaint_dict["urgency"] = ground_truth.expected_urgency
            complaint_dict["priority"] = ground_truth.expected_priority
        except GenAIUnavailableError as e:
            ground_truth = python_validation_pipeline.validate_complaint(complaint_dict)
            complaint_dict["ground_truth"] = ground_truth.model_dump()
            complaint_dict["category"] = ground_truth.expected_category
            complaint_dict["subcategory"] = ground_truth.expected_subcategory
            complaint_dict["department"] = ground_truth.expected_department
            complaint_dict["urgency"] = ground_truth.expected_urgency
            complaint_dict["priority"] = ground_truth.expected_priority
            complaint_dict["analysis_error"] = str(e)
            complaint_dict["status"] = "Manual Review Required"
        except Exception as e:
            logger.error(f"Error executing dual pipeline on complaint {new_id}: {e}")
            complaint_dict["analysis_error"] = "The complaint could not be analyzed automatically and requires review."
            complaint_dict["status"] = "Manual Review Required"

        complaints_col = get_complaints_col()
        # Update the existing record instead of inserting a new one
        complaints_col.update_one({"complaint_id": new_id}, {"$set": complaint_dict})
        
        audit_col = get_audit_logs_col()
        audit_col.insert_one({
            "log_id": f"AUD-{total_count+1:05d}",
            "complaint_id": new_id,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "actor": "AI_Dual_Pipeline",
            "action": "Analyzed & Verified",
            "details": {"status": complaint_dict.get("status"), "verification": complaint_dict.get("comparison", {}).get("verification_status")}
        })
        return complaint_dict

    updated_dict = await run_in_threadpool(blocking_pipeline)

    try:
        await ws_manager.broadcast({
            "type": "NEW_COMPLAINT",
            "complaint_id": new_id,
            "customer_name": updated_dict["customer_name"],
            "complaint_title": updated_dict["complaint_title"],
            "category": updated_dict.get("category", "General"),
            "urgency": updated_dict.get("urgency", "Medium"),
            "priority": updated_dict.get("priority", "P2"),
            "status": updated_dict.get("status", "New"),
            "sentiment": sentiment_data,
            "timestamp": updated_dict["created_at"]
        })
    except Exception as e:
        logger.error(f"Error broadcasting WebSocket event: {e}")

@router.post("/complaints/submit")
async def submit_complaint(
    request: Request,
    background_tasks: BackgroundTasks,
    customer_name: str = Form(...),
    customer_email: str = Form(...),
    customer_phone: Optional[str] = Form(None),
    customer_type: str = Form("Standard"),
    complaint_title: str = Form(...),
    complaint_description: str = Form(...),
    product_or_service: Optional[str] = Form(None),
    order_reference: Optional[str] = Form(None),
    preferred_channel: str = Form("Web Form"),
    evidence_image: Optional[UploadFile] = File(None),
    evidence_processing_consent: bool = Form(False)
):
    current_user = AuthManager.get_current_user(request)
    
    is_valid, err_msg = ComplaintPreprocessor.validate_complaint_input(complaint_title, complaint_description)
    if not is_valid:
        raise HTTPException(status_code=400, detail=err_msg)

    image_bytes = None
    image_mime_type = None
    if evidence_image:
        if not evidence_processing_consent:
            raise HTTPException(status_code=400, detail="Consent is required before processing an uploaded image.")
        image_bytes = await evidence_image.read(10 * 1024 * 1024 + 1)
        if len(image_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Photo evidence must be 10 MB or less.")
        image_mime_type = detect_image_type(image_bytes)
        if not image_mime_type or image_mime_type != evidence_image.content_type:
            raise HTTPException(status_code=415, detail="Use a valid JPEG, PNG, WebP, or GIF image.")

    complaints_col = get_complaints_col()
    content_hash = ComplaintPreprocessor.compute_content_hash(complaint_description)
    user_id = current_user.get("user_id") if current_user else None
    normalized_email = customer_email.strip().lower()
    identity_filter = {"$or": [{"user_id": user_id}, {"customer_email": normalized_email}]} if user_id else {"customer_email": normalized_email}
    complaint_identity = {
        "user_id": user_id,
        "customer_email": normalized_email,
        "complaint_title": complaint_title.strip(),
        "complaint_description": complaint_description.strip(),
        "content_hash": content_hash,
        "order_reference": order_reference.strip() if order_reference else None,
    }
    complaint_history = list(complaints_col.find(identity_filter, sort=[("created_at", -1)], limit=500))
    relationship = identify_related_complaints(complaint_identity, complaint_history)

    total_count = complaints_col.count_documents({})
    new_id = f"CMP-{total_count + 1:05d}"
    
    prod_meta = None
    if product_or_service:
        prod_meta = ProductCatalog.find_product(product_or_service)

    sentiment_data = SentimentTelemetryEngine.analyze(
        complaint_title,
        complaint_description,
        customer_type
    )

    user_avatar = current_user.get("avatar") if current_user else None

    complaint_dict = {
        "complaint_id": new_id,
        "customer_id": f"CUST-{1000 + total_count + 1}",
        "user_id": user_id,
        "user_avatar": user_avatar,
        "customer_name": customer_name.strip(),
        "customer_email": customer_email.strip().lower(),
        "customer_phone": customer_phone.strip() if customer_phone else None,
        "customer_type": customer_type,
        "complaint_title": complaint_title.strip(),
        "complaint_description": complaint_description.strip(),
        "product_or_service": product_or_service.strip() if product_or_service else "General Item",
        "product_metadata": prod_meta,
        "order_reference": order_reference.strip() if order_reference else None,
        "preferred_channel": preferred_channel,
        "content_hash": content_hash,
        **relationship,
        "sentiment_telemetry": sentiment_data,
        "status": "AI Pipeline Processing",
        "photo_evidence_attached": image_bytes is not None,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # IMPORTANT: Insert synchronously first so it is immediately trackable by the user!
    complaints_col.insert_one(complaint_dict.copy())

    background_tasks.add_task(
        _process_complaint_bg,
        complaint_dict,
        new_id,
        total_count,
        sentiment_data,
        image_bytes,
        image_mime_type,
    )

    return {
        "success": True,
        "complaint_id": new_id,
        "message": "Your complaint has been registered. Triage is processing; if an automated analysis is unavailable, the case will be queued for human review.",
        "status": "AI Pipeline Processing",
        "submitted_at": complaint_dict["created_at"]
    }



@router.get("/complaints/my-complaints")
async def get_my_complaints(request: Request):
    user = AuthManager.get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required to view your complaints.")
    
    complaints_col = get_complaints_col()
    clean_email = (user.get("email") or "").lower().strip()
    user_id = user.get("user_id") or ""
    
    query = {
        "$or": [
            {"customer_email": clean_email},
            {"user_id": user_id}
        ]
    }
    raw = list(complaints_col.find(query, sort=[("created_at", -1)], limit=50))
    docs = clean_docs(raw)
    return {"complaints": docs, "total": len(docs), "user_email": clean_email}

@router.get("/complaints/track/{complaint_id}")
async def track_complaint(complaint_id: str, email: str = Query("", max_length=254)):
    col = get_complaints_col()
    doc = col.find_one({"complaint_id": complaint_id.strip()})
    if not doc:
        raise HTTPException(status_code=404, detail="Complaint reference ID not found.")

    clean_email = (email or "").strip().lower()
    if not clean_email or clean_email != (doc.get("customer_email") or "").strip().lower():
        raise HTTPException(status_code=404, detail="Complaint reference ID or customer email was not recognized.")

    status = doc.get("status", "Under Review")
    status_updates = {
        "New": "Your complaint was received and is waiting for review.",
        "AI Pipeline Processing": "Your complaint is being checked and will be reviewed by support staff.",
        "Analyzed": "Initial checks are complete; support staff may still need to review your case.",
        "Resolved": "Your complaint has been marked resolved. Contact support if you still need help.",
        "Closed": "This complaint has been closed. Contact support if you need further assistance.",
    }
    customer_view = {
        "complaint_id": doc.get("complaint_id"),
        "complaint_title": doc.get("complaint_title"),
        "product_or_service": doc.get("product_or_service"),
        "status": status,
        "submitted_at": doc.get("created_at") or "Not available",
        "assigned_department": doc.get("department") or "Support team",
        "official_update": status_updates.get(status, "Your case is being reviewed by the support team."),
    }
    return customer_view

@router.post("/vision/inspect")
async def inspect_hardware_image(
    file: Optional[UploadFile] = File(None),
    complaint_text: str = Form(""),
    sample_defect: Optional[str] = Form(None),
    evidence_processing_consent: bool = Form(False)
):
    if not file:
        raise HTTPException(status_code=400, detail="Attach an image for manual review.")
    if not evidence_processing_consent:
        raise HTTPException(status_code=400, detail="Consent is required before processing an uploaded image.")
    content_bytes = await file.read(10 * 1024 * 1024 + 1)
    if len(content_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image size must be 10 MB or less.")
    image_mime_type = detect_image_type(content_bytes)
    if not image_mime_type or image_mime_type != file.content_type:
        raise HTTPException(status_code=415, detail="Use a valid JPEG, PNG, WebP, or GIF image.")
    analysis = await run_in_threadpool(
        VisionForensicsEngine.analyze_image,
        content_bytes,
        image_mime_type,
        complaint_text,
    )
    return analysis

@router.post("/complaints/pre-check")
async def pre_check_complaint(
    complaint_title: str = Form(...),
    complaint_description: str = Form(...),
    customer_type: str = Form("Standard")
):
    is_valid, error_message = ComplaintPreprocessor.validate_complaint_input(complaint_title, complaint_description)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_message)

    sim_complaint = {
        "complaint_title": complaint_title,
        "complaint_description": complaint_description,
        "customer_type": customer_type
    }
    ground_truth = python_validation_pipeline.validate_complaint(sim_complaint)
    sentiment = SentimentTelemetryEngine.analyze(complaint_title, complaint_description, customer_type)

    category = ground_truth.expected_category
    if category == "Safety Hazard":
        advisory = "A potential safety-related trigger was detected. Stop using the product if it is safe to do so and wait for staff guidance; this is not a diagnosis."
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
        "estimated_sla": "Priority review target — not a guarantee" if ground_truth.expected_urgency in ["Critical", "High"] else "Standard review target — not a guarantee",
        "refund_eligibility_preview": ground_truth.refund_eligible,
        "sentiment": sentiment,
        "safety_advisory": advisory,
        "preview_basis": "Preliminary Python rules and text heuristics only; no GenAI analysis, live policy lookup, or approval was performed."
    }
