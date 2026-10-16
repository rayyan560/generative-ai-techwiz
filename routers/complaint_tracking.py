from fastapi import APIRouter, HTTPException, Query, Request

from config.database import get_complaints_col
from routers.common import clean_docs
from src.security.auth import AuthManager


router = APIRouter(prefix="/api", tags=["Complaint Tracking"])


@router.get("/complaints/my-complaints")
async def get_my_complaints(request: Request):
    user = AuthManager.get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required to view your complaints.")
    email = (user.get("email") or "").lower().strip()
    user_id = user.get("user_id") or ""
    query = {"$or": [{"customer_email": email}, {"user_id": user_id}]}
    raw = list(get_complaints_col().find(query, sort=[("created_at", -1)], limit=50))
    return {"complaints": clean_docs(raw), "total": len(raw), "user_email": email}


@router.get("/complaints/track/{complaint_id}")
async def track_complaint(complaint_id: str, email: str = Query("", max_length=254)):
    complaint = get_complaints_col().find_one({"complaint_id": complaint_id.strip()})
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint reference ID not found.")
    clean_email = (email or "").strip().lower()
    if not clean_email or clean_email != (complaint.get("customer_email") or "").strip().lower():
        raise HTTPException(status_code=404, detail="Complaint reference ID or customer email was not recognized.")
    status = complaint.get("status", "Under Review")
    updates = {
        "New": "Your complaint was received and is waiting for review.",
        "AI Pipeline Processing": "Your complaint is being checked and will be reviewed by support staff.",
        "Analyzed": "Initial checks are complete; support staff may still need to review your case.",
        "Resolved": "Your complaint has been marked resolved. Contact support if you still need help.",
        "Closed": "This complaint has been closed. Contact support if you need further assistance.",
    }
    return {
        "complaint_id": complaint.get("complaint_id"),
        "complaint_title": complaint.get("complaint_title"),
        "product_or_service": complaint.get("product_or_service"),
        "status": status,
        "submitted_at": complaint.get("created_at") or "Not available",
        "assigned_department": complaint.get("department") or "Support team",
        "official_update": updates.get(status, "Your case is being reviewed by the support team."),
    }
