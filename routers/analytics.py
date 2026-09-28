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

logger = logging.getLogger("SupportNova.AnalyticsRouter")

router = APIRouter(prefix="/api", tags=["Analytics & Financial Refunds"])

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
        
        amount = 149.99
        entities = c.get("genai_analysis", {}).get("extracted_entities", {})
        if entities and "amount" in entities and entities["amount"]:
            try:
                amount = float(entities["amount"])
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse amount float: {e}")
                amount = 149.99
        elif "price" in str(c.get("product_metadata", {})):
            try:
                amount = float(c.get("product_metadata", {}).get("price", 149.99))
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse product metadata price: {e}")
                amount = 149.99

        escrow_status = c.get("escrow_status")
        if not escrow_status:
            if c.get("status") in ["Refund Approved", "Resolved"]:
                escrow_status = "Released / Paid"
            elif c.get("status") == "Escalated" or c.get("urgency") == "Critical":
                escrow_status = "Disputed / Held"
            else:
                escrow_status = "Held in Escrow"

        if is_refund_related:
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
                "product_or_service": c.get("product_or_service", "NovaTech Device"),
                "order_reference": c.get("order_reference") or f"ORD-{c.get('complaint_id')[-4:]}",
                "amount": round(amount, 2),
                "escrow_status": escrow_status,
                "refund_eligible": c.get("ground_truth", {}).get("refund_eligible", True),
                "policy_matched": c.get("ground_truth", {}).get("applicable_policy_id", "POL-REF-02"),
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

    update_fields = {"last_modified": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    if action in ["release_escrow", "approve_refund"]:
        update_fields["escrow_status"] = "Released / Paid"
        update_fields["status"] = "Refund Approved"
        update_fields["payout_details"] = {
            "amount": amount,
            "method": payment_method,
            "processed_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "transaction_id": f"TXN-ESC-{int(datetime.datetime.now().timestamp())}"
        }
    elif action == "reject_claim":
        update_fields["escrow_status"] = "Claim Rejected / Funds Restored"
        update_fields["status"] = "Refund Denied"
    elif action == "issue_credit":
        update_fields["escrow_status"] = "Goodwill Credit Issued"
        update_fields["status"] = "Resolved"
        update_fields["payout_details"] = {
            "amount": amount,
            "method": "NovaTech Store Wallet Credit",
            "processed_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "credit_voucher": f"VOUCHER-{int(datetime.datetime.now().timestamp())}"
        }

    if reviewer_notes:
        update_fields["reviewer_notes"] = reviewer_notes

    col.update_one({"complaint_id": complaint_id}, {"$set": update_fields})

    audit_col = get_audit_logs_col()
    audit_col.insert_one({
        "log_id": f"AUD-REF-{int(datetime.datetime.now().timestamp())}",
        "complaint_id": complaint_id,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "actor": "Finance & Support Admin",
        "action": f"Refund/Escrow: {action}",
        "details": {"amount": amount, "method": payment_method, "notes": reviewer_notes}
    })

    return {"success": True, "complaint_id": complaint_id, "action": action, "escrow_status": update_fields.get("escrow_status")}

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
        "manual_review_count": manual_review_count,
        "mismatch_count": mismatch_count,
        "sla_risk_count": sla_risk_count,
        "categories": category_counts,
        "departments": dept_counts,
        "urgencies": urgency_counts,
        "statuses": status_counts,
        "compliance_rate": round((verified_count / total * 100) if total > 0 else 100, 1)
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
            comp.get("mandatory_coverage_score", 100),
            comp.get("source_traceability_score", 100),
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
    
    optimization = EscrowClvOptimizer.optimize_settlement(doc)
    return optimization

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
    lang_names = {"ur": "Urdu", "ar": "Arabic", "es": "Spanish", "zh": "Chinese", "en": "English"}
    return {
        "source_text": text,
        "target_lang": target_lang,
        "target_lang_name": lang_names.get(target_lang, "English"),
        "translated_text": text,
        "status": "Synchronized"
    }
