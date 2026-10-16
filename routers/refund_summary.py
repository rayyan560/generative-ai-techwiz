from fastapi import APIRouter, Depends

from config.database import get_complaints_col
from src.security.permissions import require_roles


router = APIRouter(
    prefix="/api",
    tags=["Analytics & Financial Refunds"],
    dependencies=[Depends(require_roles("admin", "warranty_manager"))],
)


@router.get("/refunds/summary")
async def get_refunds_summary():
    complaints = list(get_complaints_col().find({}, limit=600))
    refunds = []
    totals = {"total_claims_val": 0.0, "escrow_held_val": 0.0, "approved_payout_val": 0.0, "disputed_val": 0.0}
    for complaint in complaints:
        ground_truth = complaint.get("ground_truth") or {}
        title = (complaint.get("complaint_title") or "").lower()
        related = (
            complaint.get("category") in {"Refund Request", "Billing & Charges", "Order Cancellation"}
            or ground_truth.get("refund_eligible", False)
            or "refund" in title
            or "charge" in title
        )
        amount_value = complaint.get("verified_transaction_amount")
        if amount_value is None:
            amount_value = (complaint.get("payout_details") or {}).get("amount")
        try:
            amount = float(amount_value) if amount_value is not None else None
            if amount is not None and amount < 0:
                amount = None
        except (ValueError, TypeError):
            amount = None
        escrow_status = complaint.get("escrow_status") or "Not recorded"
        if related and amount is not None:
            totals["total_claims_val"] += amount
            if escrow_status == "Held in Escrow":
                totals["escrow_held_val"] += amount
            elif escrow_status == "Released / Paid":
                totals["approved_payout_val"] += amount
            elif "Disputed" in escrow_status:
                totals["disputed_val"] += amount
        if related:
            refunds.append({
                "complaint_id": complaint.get("complaint_id"),
                "customer_name": complaint.get("customer_name"),
                "customer_type": complaint.get("customer_type", "Standard"),
                "complaint_title": complaint.get("complaint_title"),
                "product_or_service": complaint.get("product_or_service") or "Not recorded",
                "order_reference": complaint.get("order_reference") or "Not linked",
                "amount": round(amount, 2) if amount is not None else None,
                "escrow_status": escrow_status,
                "refund_eligible": ground_truth.get("refund_eligible", False),
                "policy_matched": ground_truth.get("applicable_policy_id") or "Not evaluated",
                "status": complaint.get("status", "New"),
                "created_at": complaint.get("created_at"),
            })
    return {"metrics": {**{key: round(value, 2) for key, value in totals.items()}, "claims_count": len(refunds)}, "records": refunds}
