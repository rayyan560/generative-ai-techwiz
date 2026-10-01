from reports.generate_comparison_report import build_comparison_row


def test_comparison_report_records_complete_match_without_invented_defaults():
    complaint = {
        "complaint_id": "CMP-TEST-1",
        "category": "Delivery & Shipping",
        "genai_analysis": {
            "category": "Delivery & Shipping",
            "recommended_department": "Logistics & Delivery",
            "urgency": "High",
            "escalation_required": True,
        },
        "ground_truth": {
            "expected_category": "Delivery & Shipping",
            "expected_department": "Logistics & Delivery",
            "expected_urgency": "High",
            "mandatory_escalation": True,
            "applicable_policy_id": "POL-DEL-04",
        },
        "comparison": {
            "category_match": True,
            "department_match": True,
            "urgency_match": True,
            "escalation_match": True,
            "verification_status": "Verified",
        },
    }

    row = build_comparison_row(complaint)

    assert row[11] == "MATCH"
    assert row[12] == "Verified"
    assert row[10] == "POL-DEL-04"


def test_comparison_report_routes_missing_evidence_to_review():
    row = build_comparison_row({"complaint_id": "CMP-TEST-INCOMPLETE"})

    assert row[11] == "INCOMPLETE"
    assert row[12] == "Manual Review Required"
    assert row[10] == "Not recorded"
    assert "incomplete" in row[13].lower()
    assert row[8] == "N/A"
    assert row[9] == "N/A"
