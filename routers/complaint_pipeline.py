import datetime
import logging

from fastapi.concurrency import run_in_threadpool

from config.database import get_audit_logs_col, get_complaints_col
from routers.common import ws_manager
from src.comparison_engine.engine import ComparisonEngine
from src.genai_pipeline.pipeline import GenAIUnavailableError, genai_pipeline
from src.multimodal.vision_forensics import VisionForensicsEngine
from src.python_validation.pipeline import python_validation_pipeline


logger = logging.getLogger("SupportNova.ComplaintPipeline")


async def process_complaint_background(complaint, complaint_id, total_count, sentiment, image_bytes=None, image_mime_type=None):
    def run_pipeline():
        if image_bytes and image_mime_type:
            complaint["vision_analysis"] = VisionForensicsEngine.analyze_image(
                image_bytes, image_mime_type, complaint.get("complaint_description", "")
            )
        try:
            genai_result = genai_pipeline.generate_intelligence(complaint)
            ground_truth = python_validation_pipeline.validate_complaint(complaint)
            comparison = ComparisonEngine.compare_and_verify(genai_result, ground_truth, complaint)
            complaint["genai_analysis"] = genai_result.model_dump()
            complaint["ground_truth"] = ground_truth.model_dump()
            complaint["comparison"] = comparison.model_dump()
            complaint["status"] = "Manual Review Required" if comparison.requires_manual_review else "Analyzed"
            if complaint.get("vision_analysis", {}).get("manual_review_required"):
                complaint["status"] = "Manual Review Required"
            _apply_ground_truth(complaint, ground_truth)
        except GenAIUnavailableError as error:
            ground_truth = python_validation_pipeline.validate_complaint(complaint)
            complaint["ground_truth"] = ground_truth.model_dump()
            _apply_ground_truth(complaint, ground_truth)
            complaint["analysis_error"] = str(error)
            complaint["status"] = "Manual Review Required"
        except Exception as error:
            logger.error("Complaint processing failed (%s).", type(error).__name__)
            complaint["analysis_error"] = "The complaint could not be analyzed automatically and requires review."
            complaint["status"] = "Manual Review Required"

        get_complaints_col().update_one({"complaint_id": complaint_id}, {"$set": complaint})
        get_audit_logs_col().insert_one({
            "log_id": f"AUD-{total_count + 1:05d}",
            "complaint_id": complaint_id,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "actor": "AI_Dual_Pipeline",
            "action": "Analyzed & Verified",
            "details": {
                "status": complaint.get("status"),
                "verification": complaint.get("comparison", {}).get("verification_status"),
            },
        })
        return complaint

    updated = await run_in_threadpool(run_pipeline)
    try:
        await ws_manager.broadcast({
            "type": "NEW_COMPLAINT",
            "complaint_id": complaint_id,
            "customer_name": updated["customer_name"],
            "complaint_title": updated["complaint_title"],
            "category": updated.get("category", "General"),
            "urgency": updated.get("urgency", "Medium"),
            "priority": updated.get("priority", "P2"),
            "status": updated.get("status", "New"),
            "sentiment": sentiment,
            "timestamp": updated["created_at"],
        })
    except Exception as error:
        logger.warning("Complaint event broadcast failed (%s).", type(error).__name__)


def _apply_ground_truth(complaint, result):
    complaint.update({
        "category": result.expected_category,
        "subcategory": result.expected_subcategory,
        "department": result.expected_department,
        "urgency": result.expected_urgency,
        "priority": result.expected_priority,
    })
