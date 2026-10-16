import datetime
from statistics import mean
from typing import Optional

from fastapi import APIRouter, Depends

from config.database import get_complaints_col
from src.security.permissions import require_roles


router = APIRouter(
    prefix="/api",
    tags=["Agent"],
    dependencies=[Depends(require_roles("admin", "agent", "warranty_manager"))],
)


def _parse_timestamp(value):
    if not value:
        return None
    try:
        return datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


async def calculate_avg_inspection_time() -> Optional[str]:
    durations = []
    start_fields = ("review_started_at", "triage_started_at", "created_at")
    end_fields = ("review_completed_at", "triage_completed_at", "resolved_at")
    for record in get_complaints_col().find({}, limit=2000):
        start = next((_parse_timestamp(record.get(field)) for field in start_fields if record.get(field)), None)
        end = next((_parse_timestamp(record.get(field)) for field in end_fields if record.get(field)), None)
        if start and end:
            minutes = (end - start).total_seconds() / 60
            if 0 <= minutes <= 24 * 60:
                durations.append(minutes)
    return f"{mean(durations):.1f} mins" if durations else None


async def calculate_accuracy_pct() -> Optional[float]:
    scores = [
        float((record.get("comparison") or {}).get("consistency_score"))
        for record in get_complaints_col().find({}, limit=2000)
        if isinstance((record.get("comparison") or {}).get("consistency_score"), (int, float))
        and 0 <= (record.get("comparison") or {}).get("consistency_score") <= 100
    ]
    return round(mean(scores), 1) if scores else None


@router.get("/agent/stats")
async def get_agent_stats():
    complaints = get_complaints_col()
    return {
        "resolved_cases": complaints.count_documents({"status": {"$in": ["Resolved", "Refund Approved"]}}),
        "pending_reviews": complaints.count_documents({"status": {"$in": ["Analyzed", "Manual Review Required", "Escalated"]}}),
        "critical_alerts": complaints.count_documents({"priority": "P0", "status": {"$nin": ["Resolved", "Refund Approved"]}}),
        "avg_inspection_time": await calculate_avg_inspection_time(),
        "accuracy_pct": await calculate_accuracy_pct(),
    }
