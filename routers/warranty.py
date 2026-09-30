from fastapi import APIRouter, Request, HTTPException, Form, UploadFile, File, Depends, BackgroundTasks
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import datetime
import logging

from config.database import get_complaints_col, get_audit_logs_col
from src.products.catalog import ProductCatalog
from src.complaint_processing.preprocessor import ComplaintPreprocessor
from src.genai_pipeline.pipeline import GenAIUnavailableError, genai_pipeline
from src.python_validation.pipeline import python_validation_pipeline
from src.comparison_engine.engine import ComparisonEngine
from src.analytics.sentiment import SentimentTelemetryEngine
from src.multimodal.vision_forensics import VisionForensicsEngine
from src.security.auth import AuthManager
from routers.common import clean_doc, clean_docs, ws_manager

logger = logging.getLogger("SupportNova.WarrantyRouter")

router = APIRouter(prefix="/api", tags=["Warranty & Customer Portal"])

@router.get("/products")
async def get_products():
    return {"products": ProductCatalog.get_all_products(), "total": len(ProductCatalog.get_all_products())}



async def _process_complaint_bg(complaint_dict, new_id, total_count, sentiment_data):
    def blocking_pipeline():
        try:
            genai_out = genai_pipeline.generate_intelligence(complaint_dict)
            ground_truth = python_validation_pipeline.validate_complaint(complaint_dict)
            comp_result = ComparisonEngine.compare_and_verify(genai_out, ground_truth, complaint_dict)

            complaint_dict["genai_analysis"] = genai_out.model_dump()
            complaint_dict["ground_truth"] = ground_truth.model_dump()
            complaint_dict["comparison"] = comp_result.model_dump()
            complaint_dict["status"] = "Analyzed" if not comp_result.requires_manual_review else "Manual Review Required"
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
    preferred_channel: str = Form("Web Form")
):
    current_user = AuthManager.get_current_user(request)
    
    is_valid, err_msg = ComplaintPreprocessor.validate_complaint_input(complaint_title, complaint_description)
    if not is_valid:
        raise HTTPException(status_code=400, detail=err_msg)

    complaints_col = get_complaints_col()
    content_hash = ComplaintPreprocessor.compute_content_hash(complaint_description)
    
    is_dup = False
    dup_id = None
    existing = complaints_col.find_one({"content_hash": content_hash})
    if existing:
        is_dup = True
        dup_id = existing.get("complaint_id")

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

    user_id = current_user.get("user_id") if current_user else None
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
        "is_duplicate": is_dup,
        "duplicate_of_id": dup_id,
        "sentiment_telemetry": sentiment_data,
        "status": "AI Pipeline Processing",
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    # IMPORTANT: Insert synchronously first so it is immediately trackable by the user!
    complaints_col.insert_one(complaint_dict.copy())

    background_tasks.add_task(_process_complaint_bg, complaint_dict, new_id, total_count, sentiment_data)

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
async def track_complaint(complaint_id: str):
    col = get_complaints_col()
    doc = col.find_one({"complaint_id": complaint_id.strip()})
    if not doc:
        raise HTTPException(status_code=404, detail="Complaint reference ID not found.")
    
    customer_view = {
        "complaint_id": doc.get("complaint_id"),
        "customer_name": doc.get("customer_name"),
        "complaint_title": doc.get("complaint_title"),
        "complaint_description": doc.get("complaint_description"),
        "product_or_service": doc.get("product_or_service"),
        "status": doc.get("status"),
        "created_at": doc.get("created_at"),
        "last_modified": doc.get("last_modified") or doc.get("created_at"),
        "estimated_resolution": "Within 24 Hours",
        "category": doc.get("category", "General Support"),
        "urgency": doc.get("urgency", "Medium")
    }
    return customer_view

@router.post("/vision/inspect")
async def inspect_hardware_image(
    file: Optional[UploadFile] = File(None),
    complaint_text: str = Form(""),
    sample_defect: Optional[str] = Form(None)
):
    if not file:
        raise HTTPException(status_code=400, detail="Attach an image for manual review.")
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Only image files are accepted.")
    content_bytes = await file.read(10 * 1024 * 1024 + 1)
    if len(content_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image size must be 10 MB or less.")
    fname = file.filename or "uploaded-image"
    
    analysis = VisionForensicsEngine.analyze_image(fname, content_bytes, complaint_text)
    raise HTTPException(status_code=503, detail=analysis["reason"])

@router.post("/complaints/pre-check")
async def pre_check_complaint(
    complaint_title: str = Form(...),
    complaint_description: str = Form(...),
    customer_type: str = Form("Standard")
):
    sim_complaint = {
        "complaint_title": complaint_title,
        "complaint_description": complaint_description,
        "customer_type": customer_type
    }
    ground_truth = python_validation_pipeline.validate_complaint(sim_complaint)
    sentiment = SentimentTelemetryEngine.analyze(complaint_title, complaint_description, customer_type)

    return {
        "estimated_category": ground_truth.expected_category,
        "estimated_priority": ground_truth.expected_priority,
        "estimated_urgency": ground_truth.expected_urgency,
        "estimated_sla": "Priority review target — not a guarantee" if ground_truth.expected_urgency in ["Critical", "High"] else "Standard review target — not a guarantee",
        "refund_eligibility_preview": ground_truth.refund_eligible,
        "sentiment": sentiment,
        "safety_advisory": "Hazardous battery issue detected — Keep device powered off" if ground_truth.mandatory_escalation else "Normal warranty coverage applicable"
    }
