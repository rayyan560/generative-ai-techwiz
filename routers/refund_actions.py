import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException

from config.database import get_audit_logs_col, get_complaints_col
from src.security.permissions import require_roles


router = APIRouter(
    prefix="/api",
    tags=["Analytics & Financial Refunds"],
    dependencies=[Depends(require_roles("admin", "warranty_manager"))],
)


@router.post("/refunds/process")
async def process_refund_action(
    complaint_id: str = Form(...),
    action: str = Form(...),
    amount: float = Form(0.0),
    payment_method: str = Form("Original Payment Method (Stripe/Card)"),
    reviewer_notes: Optional[str] = Form(""),
):
    complaints = get_complaints_col()
    complaint = complaints.find_one({"complaint_id": complaint_id.strip()})
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found.")
    if action not in {"release_escrow", "reject_claim"}:
        raise HTTPException(status_code=400, detail="That settlement action is not supported by an integrated payment service.")
    if action == "release_escrow":
        verified_amount = complaint.get("verified_transaction_amount")
        if not complaint.get("payment_verified") or not (complaint.get("ground_truth") or {}).get("refund_eligible") or verified_amount is None:
            raise HTTPException(status_code=409, detail="Verified payment amount and policy eligibility are required before approval.")
        try:
            verified_amount = float(verified_amount)
        except (TypeError, ValueError):
            raise HTTPException(status_code=409, detail="The verified transaction amount is invalid.")
        if amount <= 0 or amount != verified_amount:
            raise HTTPException(status_code=400, detail="Decision amount must match the verified transaction amount.")
        if complaint.get("payout_details"):
            raise HTTPException(status_code=409, detail="A payout record already exists for this case.")

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    update = {"last_modified": now}
    if action == "release_escrow":
        update.update(
            escrow_status="Approval Recorded — payment pending integration",
            status="Refund Approval Pending",
            refund_decision={"decision": "approved_pending_payment", "amount": amount, "method": payment_method, "recorded_at": now},
        )
    else:
        update.update(escrow_status="Claim Rejected", status="Refund Denied", refund_decision={"decision": "rejected", "recorded_at": now})
    if reviewer_notes:
        update["reviewer_notes"] = reviewer_notes
    complaints.update_one({"complaint_id": complaint_id}, {"$set": update})
    get_audit_logs_col().insert_one({
        "log_id": f"AUD-REF-{int(datetime.datetime.now().timestamp())}",
        "complaint_id": complaint_id,
        "timestamp": now,
        "actor": "Authenticated Finance & Support Staff",
        "action": f"Refund/Escrow: {action}",
        "details": {"amount": amount if action == "release_escrow" else None, "method": payment_method if action == "release_escrow" else None, "notes": reviewer_notes},
    })
    return {"success": True, "complaint_id": complaint_id, "action": action, "escrow_status": update.get("escrow_status"), "payment_executed": False}
