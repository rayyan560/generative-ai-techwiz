import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from config.database import get_complaints_col
from src.security.permissions import require_roles


router = APIRouter(
    prefix="/api",
    tags=["Analytics & Financial Refunds"],
    dependencies=[Depends(require_roles("admin", "warranty_manager"))],
)


@router.get("/analytics/metrics")
async def get_analytics():
    complaints = list(get_complaints_col().find({}, limit=550))
    categories, departments, urgencies, statuses = {}, {}, {}, {}
    mismatch = risk = verified = checked = manual_review = 0
    for complaint in complaints:
        category = complaint.get("category", "Unclassified")
        department = complaint.get("department", "Unassigned")
        urgency = complaint.get("urgency", "Medium")
        status = complaint.get("status", "New")
        categories[category] = categories.get(category, 0) + 1
        departments[department] = departments.get(department, 0) + 1
        urgencies[urgency] = urgencies.get(urgency, 0) + 1
        statuses[status] = statuses.get(status, 0) + 1
        comparison = complaint.get("comparison") or {}
        if comparison:
            checked += 1
            verified += comparison.get("verification_status") == "Verified"
            manual_review += bool(comparison.get("requires_manual_review"))
            mismatch += not comparison.get("department_match") or not comparison.get("category_match")
        risk += urgency in {"Critical", "High"} and status not in {"Resolved", "Closed"}
    return {
        "total_complaints": len(complaints),
        "verified_count": verified,
        "checked_count": checked,
        "manual_review_count": manual_review,
        "mismatch_count": mismatch,
        "sla_risk_count": risk,
        "categories": categories,
        "departments": departments,
        "urgencies": urgencies,
        "statuses": statuses,
        "compliance_rate": round(verified / checked * 100 if checked else 0, 1),
    }


@router.get("/reports/export/csv")
async def export_csv():
    records = list(get_complaints_col().find({}, limit=600))
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Complaint ID", "Customer Name", "Customer Type", "Title", "Category", "Subcategory",
        "Department", "Urgency", "Priority", "Status", "Verification Status", "Coverage Score",
        "Traceability Score", "Refund Eligible", "Mandatory Escalation", "Created At",
    ])
    for record in records:
        comparison = record.get("comparison") or {}
        ground_truth = record.get("ground_truth") or {}
        writer.writerow([
            record.get("complaint_id"), record.get("customer_name"), record.get("customer_type"),
            record.get("complaint_title"), record.get("category"), record.get("subcategory"),
            record.get("department"), record.get("urgency"), record.get("priority"), record.get("status"),
            comparison.get("verification_status", "Pending"), comparison.get("mandatory_coverage_score", "Not evaluated"),
            comparison.get("source_traceability_score", "Not evaluated"), ground_truth.get("refund_eligible", False),
            ground_truth.get("mandatory_escalation", False), record.get("created_at"),
        ])
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=supportnova_complaints_report.csv"},
    )
