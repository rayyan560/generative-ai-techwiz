import os
import sys
import csv
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config.database import get_complaints_col

REPORTS_DIR = os.path.dirname(__file__)
os.makedirs(REPORTS_DIR, exist_ok=True)
REPORT_FILE = os.path.join(REPORTS_DIR, "genai_python_comparison_report.csv")

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
            "Match/Mismatch",
            "Verification Status",
            "Explanation of Disagreement"
        ])

        for c in complaints:
            comp = c.get("comparison", {})
            gt = c.get("ground_truth", {})
            ai = c.get("genai_analysis", {})

            is_match = (
                comp.get("category_match", True) and
                comp.get("department_match", True) and
                comp.get("urgency_match", True) and
                comp.get("escalation_match", True)
            )

            writer.writerow([
                c.get("complaint_id"),
                gt.get("expected_category", "N/A"),
                ai.get("category", "N/A"),
                gt.get("expected_category", "N/A"),
                ai.get("recommended_department", "N/A"),
                gt.get("expected_department", "N/A"),
                ai.get("urgency", "N/A"),
                gt.get("expected_urgency", "N/A"),
                ai.get("escalation_required", False),
                gt.get("mandatory_escalation", False),
                gt.get("applicable_policy_id", "POL-CMP-01"),
                "MATCH" if is_match else "MISMATCH",
                comp.get("verification_status", "Verified"),
                comp.get("explanation_of_disagreement", "Compliant")
            ])

    print(f"Comparison report written successfully to {REPORT_FILE}")

if __name__ == "__main__":
    generate_comparison_report()
