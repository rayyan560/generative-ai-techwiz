import datetime

from fastapi import APIRouter, Depends, Form, HTTPException

from config.database import get_audit_logs_col, get_complaints_col
from src.security.permissions import require_roles


router = APIRouter(prefix="/api", tags=["Customer Communications"])
staff_only = [Depends(require_roles("admin", "agent", "warranty_manager"))]


@router.get("/communication/threads", dependencies=staff_only)
async def get_communication_threads(limit: int = 50):
    complaints = get_complaints_col().find({}, limit=limit, sort=[("created_at", -1)])
    threads = []
    for complaint in complaints:
        messages = complaint.get("messages", [])
        last_message = messages[-1]["text"] if messages else complaint.get("complaint_description", "")[:90] + "..."
        threads.append({
            "complaint_id": complaint.get("complaint_id"),
            "customer_name": complaint.get("customer_name"),
            "customer_email": complaint.get("customer_email"),
            "customer_phone": complaint.get("customer_phone") or "Not provided",
            "customer_type": complaint.get("customer_type", "Standard"),
            "channel": complaint.get("preferred_channel", "Web Form"),
            "complaint_title": complaint.get("complaint_title"),
            "category": complaint.get("category", "General"),
            "urgency": complaint.get("urgency", "Medium"),
            "priority": complaint.get("priority", "P2"),
            "status": complaint.get("status", "New"),
            "last_message": last_message,
            "created_at": complaint.get("created_at"),
        })
    return {"threads": threads, "total": len(threads)}


@router.get("/communication/thread/{complaint_id}", dependencies=staff_only)
async def get_communication_thread_details(complaint_id: str):
    complaint = get_complaints_col().find_one({"complaint_id": complaint_id.strip()})
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint thread not found.")
    messages = complaint.get("messages", [])
    if not messages:
        messages = [{
            "id": "msg-1",
            "sender": "customer",
            "sender_name": complaint.get("customer_name", "Customer"),
            "text": complaint.get("complaint_description", ""),
            "timestamp": complaint.get("created_at", "Just now"),
            "channel": complaint.get("preferred_channel", "Web Portal"),
        }]
        ai_response = complaint.get("genai_analysis", {}).get("customer_response")
        if ai_response and complaint.get("status") in {"Resolved", "Analyzed"}:
            messages.append({
                "id": "msg-2",
                "sender": "agent",
                "sender_name": "NovaTech Support Specialist",
                "text": ai_response,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "channel": "Email / Web Ticket",
            })
    return {
        "complaint_id": complaint.get("complaint_id"),
        "customer_name": complaint.get("customer_name"),
        "customer_email": complaint.get("customer_email"),
        "customer_phone": complaint.get("customer_phone") or "Not provided",
        "customer_type": complaint.get("customer_type", "Standard"),
        "product_or_service": complaint.get("product_or_service", "General Item"),
        "category": complaint.get("category", "General"),
        "department": complaint.get("department", "Customer Care"),
        "urgency": complaint.get("urgency", "Medium"),
        "priority": complaint.get("priority", "P2"),
        "status": complaint.get("status", "New"),
        "messages": messages,
        "ai_recommended_draft": complaint.get("genai_analysis", {}).get("customer_response") or "",
        "call_transcript": [],
        "sentiment": complaint.get("genai_analysis", {}).get("sentiment", "Neutral"),
    }


@router.post("/communication/send", dependencies=staff_only)
async def send_communication_message(
    complaint_id: str = Form(...),
    message_text: str = Form(...),
    channel: str = Form("Web Portal"),
):
    col = get_complaints_col()
    complaint = col.find_one({"complaint_id": complaint_id.strip()})
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found.")
    new_message = {
        "id": f"msg-{int(datetime.datetime.now().timestamp())}",
        "sender": "agent",
        "sender_name": "NovaTech Support Agent",
        "text": message_text.strip(),
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "channel": channel,
    }
    col.update_one({"complaint_id": complaint_id}, {"$push": {"messages": new_message}})
    get_audit_logs_col().insert_one({
        "log_id": f"AUD-COMM-{int(datetime.datetime.now().timestamp())}",
        "complaint_id": complaint_id,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "actor": "Support Agent",
        "action": f"Sent Message ({channel})",
        "details": {"message_snippet": message_text[:80]},
    })
    return {"success": True, "message": new_message}
