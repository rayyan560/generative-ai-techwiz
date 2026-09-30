import os
import sys
import json
import csv
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.genai_pipeline.pipeline import genai_pipeline
from src.genai_pipeline.pipeline import GenAIUnavailableError
from src.python_validation.pipeline import python_validation_pipeline
from src.comparison_engine.engine import ComparisonEngine

def run_hidden_evaluation(input_file: str, output_csv: str, limit: int = 50, all_records: bool = False):
    """
    Evaluator Runner for Techwiz 7 Judges.
    Processes any unseen JSON complaints file through the Dual-Pipeline and outputs a full verification report.
    """
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        complaints = json.load(f)

    if not all_records:
        complaints = complaints[:limit]

    print(f"=== Techwiz 7 Hidden Dataset Evaluation Runner ===")
    print(f"Loaded {len(complaints)} test complaints from '{input_file}'.")
    print(f"Executing Dual-Pipeline Analysis & Python Ground-Truth Verification...\n")

    results = []
    for idx, c in enumerate(complaints, start=1):
        # Pipeline 1: GenAI
        gt_out = python_validation_pipeline.validate_complaint(c)
        try:
            ai_out = genai_pipeline.generate_intelligence(c)
        except GenAIUnavailableError as error:
            results.append({
                "Complaint_ID": c.get("complaint_id", f"HIDDEN-{idx:04d}"),
                "Customer": c.get("customer_name", "Evaluator Customer"),
                "Title": c.get("complaint_title", "Test Title"),
                "GenAI_Category": "Unavailable",
                "Python_Category": gt_out.expected_category,
                "Category_Match": "Not compared",
                "GenAI_Dept": "Unavailable",
                "Python_Dept": gt_out.expected_department,
                "Dept_Match": "Not compared",
                "GenAI_Urgency": "Unavailable",
                "Python_Urgency": gt_out.expected_urgency,
                "GenAI_Escalation": "Unavailable",
                "Python_Escalation": gt_out.mandatory_escalation,
                "Escalation_Tier": gt_out.escalation_tier,
                "Coverage_Score": "Not measured",
                "Traceability_Score": "Not measured",
                "Consistency_Score": "Not measured",
                "Verification_Status": "Manual Review Required",
                "Manual_Review_Needed": True,
                "Flags": str(error)
            })
            continue
        comp = ComparisonEngine.compare_and_verify(ai_out, gt_out, c)

        results.append({
            "Complaint_ID": c.get("complaint_id", f"HIDDEN-{idx:04d}"),
            "Customer": c.get("customer_name", "Evaluator Customer"),
            "Title": c.get("complaint_title", "Test Title"),
            "GenAI_Category": ai_out.category,
            "Python_Category": gt_out.expected_category,
            "Category_Match": comp.category_match,
            "GenAI_Dept": ai_out.recommended_department,
            "Python_Dept": gt_out.expected_department,
            "Dept_Match": comp.department_match,
            "GenAI_Urgency": ai_out.urgency,
            "Python_Urgency": gt_out.expected_urgency,
            "GenAI_Escalation": ai_out.escalation_required,
            "Python_Escalation": gt_out.mandatory_escalation,
            "Escalation_Tier": gt_out.escalation_tier,
            "Coverage_Score": f"{comp.mandatory_coverage_score}%",
            "Traceability_Score": f"{comp.source_traceability_score}%",
            "Consistency_Score": f"{comp.consistency_score}%",
            "Verification_Status": comp.verification_status,
            "Manual_Review_Needed": comp.requires_manual_review,
            "Flags": comp.explanation_of_disagreement
        })

    # Write results to CSV
    fieldnames = [
        "Complaint_ID", "Customer", "Title", "GenAI_Category", "Python_Category", "Category_Match",
        "GenAI_Dept", "Python_Dept", "Dept_Match", "GenAI_Urgency", "Python_Urgency",
        "GenAI_Escalation", "Python_Escalation", "Escalation_Tier", "Coverage_Score",
        "Traceability_Score", "Consistency_Score", "Verification_Status", "Manual_Review_Needed", "Flags"
    ]
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Evaluation complete! Results exported to: '{output_csv}'")
    
    # Summary
    verified_cnt = sum(1 for r in results if r["Verification_Status"] == "Verified")
    manual_cnt = sum(1 for r in results if r["Manual_Review_Needed"])
    print(f"Summary: Total: {len(results)} | Verified: {verified_cnt} | Manual Review Required: {manual_cnt}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SupportNova Hidden Dataset Evaluation Runner")
    parser.add_argument("--input", default="sample_complaints/complaints_500.json", help="Path to unseen complaints JSON")
    parser.add_argument("--output", default="reports/hidden_evaluation_results.csv", help="Path to output CSV report")
    parser.add_argument("--limit", type=int, default=50, help="Max sample cases to evaluate")
    parser.add_argument("--all", action="store_true", help="Evaluate entire dataset")
    args = parser.parse_args()
    
    inp = args.input
    if not os.path.exists(inp):
        inp = "sample_complaints/complaints_500.json"
        
    run_hidden_evaluation(inp, args.output, limit=args.limit, all_records=args.all)
