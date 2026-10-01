import os
import sys
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config.database import get_complaints_col

REPORTS_DIR = os.path.dirname(__file__)
os.makedirs(REPORTS_DIR, exist_ok=True)
REPORT_FILE = os.path.join(REPORTS_DIR, "genai_python_comparison_report.csv")

def build_comparison_row(complaint):
    comparison = complaint.get("comparison") or {}
    ground_truth = complaint.get("ground_truth") or {}
    ai = complaint.get("genai_analysis") or {}
    comparison_fields = ("category_match", "department_match", "urgency_match", "escalation_match")
    ai_fields = ("category", "recommended_department", "urgency", "escalation_required")
    ground_truth_fields = ("expected_category", "expected_department", "expected_urgency", "mandatory_escalation")
    complete = (
        all(field in comparison for field in comparison_fields)
        and all(field in ai for field in ai_fields)
        and all(field in ground_truth for field in ground_truth_fields)
    )
    if complete:
        result = "MATCH" if all(comparison[field] is True for field in comparison_fields) else "MISMATCH"
    else:
        result = "INCOMPLETE"
    verification_status = comparison.get("verification_status") or "Manual Review Required"
    explanation = comparison.get("explanation_of_disagreement")
    if not explanation:
        explanation = "Comparison evidence is incomplete; manual review is required." if not complete else "No disagreement details recorded."
    return [
        complaint.get("complaint_id", "N/A"),
        complaint.get("category", ground_truth.get("expected_category", "N/A")),
        ai.get("category", "N/A"),
        ground_truth.get("expected_category", "N/A"),
        ai.get("recommended_department", "N/A"),
        ground_truth.get("expected_department", "N/A"),
        ai.get("urgency", "N/A"),
        ground_truth.get("expected_urgency", "N/A"),
        ai.get("escalation_required", "N/A"),
        ground_truth.get("mandatory_escalation", "N/A"),
        ground_truth.get("applicable_policy_id", "Not recorded"),
        result,
        verification_status,
        explanation,
    ]

def generate_comparison_report():
    col = get_complaints_col()
    complaints = list(col.find({}, limit=150))
    
    print(f"Generating GenAI vs Python Ground-Truth Comparison Report on {len(complaints)} cases...")
    
    with open(REPORT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Complaint ID",
            "Actual/Expected Category",
            "GenAI Category",
            "Python Expected Category",
            "GenAI Department",
            "Python Department",
            "GenAI Urgency",
            "Python Urgency",
            "GenAI Escalation",
            "Python Escalation",
            "Policy Reference",
            "Match/Mismatch/Incomplete",
            "Verification Status",
            "Explanation of Disagreement"
        ])

        for c in complaints:
            writer.writerow(build_comparison_row(c))

    print(f"Comparison report written successfully to {REPORT_FILE}")

if __name__ == "__main__":
    generate_comparison_report()
