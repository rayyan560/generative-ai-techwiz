from fastapi import APIRouter, Request, HTTPException, Form, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional, List, Dict, Any
import datetime
import io
import csv
import logging

from config.database import get_complaints_col, get_audit_logs_col
from src.analytics.escrow_clv_optimizer import EscrowClvOptimizer
from src.analytics.defect_radar import DefectRadarEngine
from routers.common import clean_doc, clean_docs, ws_manager
from src.security.permissions import require_roles

logger = logging.getLogger("SupportNova.AnalyticsRouter")

router = APIRouter(
    prefix="/api",
    tags=["Analytics & Financial Refunds"],
    dependencies=[Depends(require_roles("admin", "warranty_manager"))]
)

@router.get("/refunds/summary")
async def get_refunds_summary():
    col = get_complaints_col()
    all_complaints = list(col.find({}, limit=600))
    
    refund_items = []
    total_claims_val = 0.0
    escrow_held_val = 0.0
    approved_payout_val = 0.0
    disputed_val = 0.0

    for c in all_complaints:
        is_refund_related = (
            c.get("category") in ["Refund Request", "Billing & Charges", "Order Cancellation"] or
            c.get("ground_truth", {}).get("refund_eligible", False) or
            "refund" in c.get("complaint_title", "").lower() or
            "charge" in c.get("complaint_title", "").lower()
        )
        
        amount_value = c.get("verified_transaction_amount")
        if amount_value is None:
            amount_value = (c.get("payout_details") or {}).get("amount")
        try:
            amount = float(amount_value) if amount_value is not None else None
            if amount is not None and amount < 0:
                amount = None
        except (ValueError, TypeError):
            amount = None

        escrow_status = c.get("escrow_status") or "Not recorded"

        if is_refund_related:
            if amount is not None:
                total_claims_val += amount
                if escrow_status == "Held in Escrow":
                    escrow_held_val += amount
                elif escrow_status == "Released / Paid":
                    approved_payout_val += amount
                elif "Disputed" in escrow_status:
                    disputed_val += amount

            refund_items.append({
                "complaint_id": c.get("complaint_id"),
                "customer_name": c.get("customer_name"),
                "customer_type": c.get("customer_type", "Standard"),
                "complaint_title": c.get("complaint_title"),
                "product_or_service": c.get("product_or_service") or "Not recorded",
                "order_reference": c.get("order_reference") or "Not linked",
                "amount": round(amount, 2) if amount is not None else None,
                "escrow_status": escrow_status,
                "refund_eligible": c.get("ground_truth", {}).get("refund_eligible", False),
                "policy_matched": c.get("ground_truth", {}).get("applicable_policy_id") or "Not evaluated",
                "status": c.get("status", "New"),
                "created_at": c.get("created_at")
            })

    return {
        "metrics": {
            "total_claims_val": round(total_claims_val, 2),
            "escrow_held_val": round(escrow_held_val, 2),
            "approved_payout_val": round(approved_payout_val, 2),
            "disputed_val": round(disputed_val, 2),
            "claims_count": len(refund_items)
        },
        "records": refund_items
    }

@router.post("/refunds/process")
async def process_refund_action(
    complaint_id: str = Form(...),
    action: str = Form(...),
    amount: float = Form(0.0),
    payment_method: str = Form("Original Payment Method (Stripe/Card)"),
    reviewer_notes: Optional[str] = Form("")
):
    col = get_complaints_col()
    doc = col.find_one({"complaint_id": complaint_id.strip()})
    if not doc:
        raise HTTPException(status_code=404, detail="Complaint not found.")

    if action not in {"release_escrow", "reject_claim"}:
        raise HTTPException(status_code=400, detail="That settlement action is not supported by an integrated payment service.")
    if action == "release_escrow":
        gt = doc.get("ground_truth") or {}
        verified_amount = doc.get("verified_transaction_amount")
        if not doc.get("payment_verified") or not gt.get("refund_eligible") or verified_amount is None:
            raise HTTPException(status_code=409, detail="Verified payment amount and policy eligibility are required before approval.")
        try:
            verified_amount = float(verified_amount)
        except (TypeError, ValueError):
            raise HTTPException(status_code=409, detail="The verified transaction amount is invalid.")
        if amount <= 0 or amount != verified_amount:
            raise HTTPException(status_code=400, detail="Decision amount must match the verified transaction amount.")
        if doc.get("payout_details"):
            raise HTTPException(status_code=409, detail="A payout record already exists for this case.")

    update_fields = {"last_modified": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    if action == "release_escrow":
        update_fields["escrow_status"] = "Approval Recorded — payment pending integration"
        update_fields["status"] = "Refund Approval Pending"
        update_fields["refund_decision"] = {
            "decision": "approved_pending_payment",
            "amount": amount,
            "method": payment_method,
            "recorded_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    elif action == "reject_claim":
        update_fields["escrow_status"] = "Claim Rejected"
        update_fields["status"] = "Refund Denied"
        update_fields["refund_decision"] = {"decision": "rejected", "recorded_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    if reviewer_notes:
        update_fields["reviewer_notes"] = reviewer_notes

    col.update_one({"complaint_id": complaint_id}, {"$set": update_fields})

    audit_col = get_audit_logs_col()
    audit_col.insert_one({
        "log_id": f"AUD-REF-{int(datetime.datetime.now().timestamp())}",
        "complaint_id": complaint_id,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "actor": "Authenticated Finance & Support Staff",
        "action": f"Refund/Escrow: {action}",
        "details": {"amount": amount if action == "release_escrow" else None, "method": payment_method if action == "release_escrow" else None, "notes": reviewer_notes}
    })

    return {"success": True, "complaint_id": complaint_id, "action": action, "escrow_status": update_fields.get("escrow_status"), "payment_executed": False}

@router.get("/analytics/metrics")
async def get_analytics():
    complaints_col = get_complaints_col()
    all_complaints = list(complaints_col.find({}, limit=550))
    
    total = len(all_complaints)
    category_counts = {}
    dept_counts = {}
    urgency_counts = {}
    status_counts = {}
    mismatch_count = 0
    sla_risk_count = 0
    verified_count = 0
    checked_count = 0
    manual_review_count = 0

    for c in all_complaints:
        cat = c.get("category", "Unclassified")
        dept = c.get("department", "Unassigned")
        urg = c.get("urgency", "Medium")
        st = c.get("status", "New")
        
        category_counts[cat] = category_counts.get(cat, 0) + 1
        dept_counts[dept] = dept_counts.get(dept, 0) + 1
        urgency_counts[urg] = urgency_counts.get(urg, 0) + 1
        status_counts[st] = status_counts.get(st, 0) + 1
        
        comp = c.get("comparison", {})
        if comp:
            checked_count += 1
            if comp.get("verification_status") == "Verified":
                verified_count += 1
            if comp.get("requires_manual_review"):
                manual_review_count += 1
            if not comp.get("department_match") or not comp.get("category_match"):
                mismatch_count += 1

        if urg in ["Critical", "High"] and st not in ["Resolved", "Closed"]:
            sla_risk_count += 1

    return {
        "total_complaints": total,
        "verified_count": verified_count,
        "checked_count": checked_count,
        "manual_review_count": manual_review_count,
        "mismatch_count": mismatch_count,
        "sla_risk_count": sla_risk_count,
        "categories": category_counts,
        "departments": dept_counts,
        "urgencies": urgency_counts,
        "statuses": status_counts,
        "compliance_rate": round((verified_count / checked_count * 100) if checked_count > 0 else 0, 1)
    }

@router.get("/reports/export/csv")
async def export_csv():
    complaints_col = get_complaints_col()
    records = list(complaints_col.find({}, limit=600))
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Complaint ID", "Customer Name", "Customer Type", "Title",
        "Category", "Subcategory", "Department", "Urgency", "Priority",
        "Status", "Verification Status", "Coverage Score", "Traceability Score",
        "Refund Eligible", "Mandatory Escalation", "Created At"
    ])
    
    for r in records:
        comp = r.get("comparison", {})
        gt = r.get("ground_truth", {})
        writer.writerow([
            r.get("complaint_id"),
            r.get("customer_name"),
            r.get("customer_type"),
            r.get("complaint_title"),
            r.get("category"),
            r.get("subcategory"),
            r.get("department"),
            r.get("urgency"),
            r.get("priority"),
            r.get("status"),
            comp.get("verification_status", "Pending"),
            comp.get("mandatory_coverage_score", "Not evaluated"),
            comp.get("source_traceability_score", "Not evaluated"),
            gt.get("refund_eligible", False),
            gt.get("mandatory_escalation", False),
            r.get("created_at")
        ])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=supportnova_complaints_report.csv"}
    )

@router.get("/escrow/clv-optimizer/{complaint_id}")
async def get_clv_settlement_options(complaint_id: str):
    col = get_complaints_col()
    doc = col.find_one({"complaint_id": complaint_id.strip()})
    if not doc:
        raise HTTPException(status_code=404, detail="Complaint not found.")
    
    return {
        "available": False,
        "reason": "A verified transaction amount and validated customer history are required; no live payment or retention model is connected.",
    }

@router.get("/analytics/defect-radar")
async def get_defect_radar():
    col = get_complaints_col()
    complaints = list(col.find({}, limit=550))
    return DefectRadarEngine.generate_defect_radar(complaints)

@router.post("/translate")
async def translate_text(
    text: str = Form(...),
    target_lang: str = Form("en")
):
    raise HTTPException(status_code=503, detail="Translation service is not configured.")
