import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Request, UploadFile

from config.database import get_complaints_col
from routers.complaint_pipeline import process_complaint_background
from src.analytics.sentiment import SentimentTelemetryEngine
from src.complaint_processing.duplicates import identify_related_complaints
from src.complaint_processing.preprocessor import ComplaintPreprocessor
from src.multimodal.image_validation import detect_image_type
from src.products.catalog import ProductCatalog
from src.security.auth import AuthManager


router = APIRouter(prefix="/api", tags=["Complaint Intake"])


@router.post("/complaints/submit")
async def submit_complaint(
    request: Request,
    background_tasks: BackgroundTasks,
    customer_name: str = Form(...),
    customer_email: str = Form(...),
    customer_phone: Optional[str] = Form(None),
    customer_type: str = Form("Standard"),
    complaint_title: Optional[str] = Form(None),
    complaint_description: str = Form(...),
    product_or_service: Optional[str] = Form(None),
    order_reference: Optional[str] = Form(None),
    preferred_channel: str = Form("Web Form"),
    evidence_image: Optional[UploadFile] = File(None),
    evidence_processing_consent: bool = Form(False),
):
    current_user = AuthManager.get_current_user(request)
    title_generated = not complaint_title or len(complaint_title.strip()) < 3
    if title_generated:
        complaint_title = ComplaintPreprocessor.derive_complaint_title(complaint_description)
    is_valid, error = ComplaintPreprocessor.validate_complaint_input(complaint_title, complaint_description)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error)

    image_bytes, image_mime_type = await _read_evidence(evidence_image, evidence_processing_consent)
    complaints = get_complaints_col()
    content_hash = ComplaintPreprocessor.compute_content_hash(complaint_description)
    user_id = current_user.get("user_id") if current_user else None
    customer_email_clean = customer_email.strip().lower()
    identity_filter = {"$or": [{"user_id": user_id}, {"customer_email": customer_email_clean}]} if user_id else {"customer_email": customer_email_clean}
    complaint_identity = {
        "user_id": user_id,
        "customer_email": customer_email_clean,
        "complaint_title": complaint_title.strip(),
        "complaint_description": complaint_description.strip(),
        "content_hash": content_hash,
        "order_reference": order_reference.strip() if order_reference else None,
    }
    history = list(complaints.find(identity_filter, sort=[("created_at", -1)], limit=500))
    relationship = identify_related_complaints(complaint_identity, history)
    total_count = complaints.count_documents({})
    complaint_id = f"CMP-{total_count + 1:05d}"
    product_metadata = ProductCatalog.find_product(product_or_service) if product_or_service else None
    sentiment = SentimentTelemetryEngine.analyze(complaint_title, complaint_description, customer_type)
    record = {
        "complaint_id": complaint_id,
        "customer_id": f"CUST-{1000 + total_count + 1}",
        "user_id": user_id,
        "user_avatar": current_user.get("avatar") if current_user else None,
        "customer_name": customer_name.strip(),
        "customer_email": customer_email_clean,
        "customer_phone": customer_phone.strip() if customer_phone else None,
        "customer_type": customer_type,
        "complaint_title": complaint_title.strip(),
        "complaint_description": complaint_description.strip(),
        "product_or_service": product_or_service.strip() if product_or_service else "General Item",
        "product_metadata": product_metadata,
        "order_reference": order_reference.strip() if order_reference else None,
        "preferred_channel": preferred_channel,
        "content_hash": content_hash,
        **relationship,
        "sentiment_telemetry": sentiment,
        "status": "AI Pipeline Processing",
        "photo_evidence_attached": image_bytes is not None,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    complaints.insert_one(record.copy())
    background_tasks.add_task(
        process_complaint_background,
        record,
        complaint_id,
        total_count,
        sentiment,
        image_bytes,
        image_mime_type,
    )
    return {
        "success": True,
        "complaint_id": complaint_id,
        "title_generated": title_generated,
        "message": "Your complaint has been registered. Triage is processing; if automated analysis is unavailable, it will be queued for human review.",
        "status": "AI Pipeline Processing",
        "submitted_at": record["created_at"],
    }


async def _read_evidence(evidence_image, consent):
    if not evidence_image:
        return None, None
    if not consent:
        raise HTTPException(status_code=400, detail="Consent is required before processing an uploaded image.")
    image_bytes = await evidence_image.read(10 * 1024 * 1024 + 1)
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Photo evidence must be 10 MB or less.")
    mime_type = detect_image_type(image_bytes)
    if not mime_type or mime_type != evidence_image.content_type:
        raise HTTPException(status_code=415, detail="Use a valid JPEG, PNG, WebP, or GIF image.")
    return image_bytes, mime_type
