from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from src.multimodal.image_validation import detect_image_type
from src.multimodal.vision_forensics import VisionForensicsEngine


router = APIRouter(prefix="/api", tags=["Visual Complaint Evidence"])


@router.post("/vision/inspect")
async def inspect_hardware_image(
    file: Optional[UploadFile] = File(None),
    complaint_text: str = Form(""),
    sample_defect: Optional[str] = Form(None),
    evidence_processing_consent: bool = Form(False),
):
    if not file:
        raise HTTPException(status_code=400, detail="Attach an image for manual review.")
    if not evidence_processing_consent:
        raise HTTPException(status_code=400, detail="Consent is required before processing an uploaded image.")
    content = await file.read(10 * 1024 * 1024 + 1)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image size must be 10 MB or less.")
    mime_type = detect_image_type(content)
    if not mime_type or mime_type != file.content_type:
        raise HTTPException(status_code=415, detail="Use a valid JPEG, PNG, WebP, or GIF image.")
    return await run_in_threadpool(VisionForensicsEngine.analyze_image, content, mime_type, complaint_text)
