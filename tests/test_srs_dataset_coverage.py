import json
from pathlib import Path

from src.complaint_rules.matrix import ALL_RULES
from src.escalation_rules.manager import ESCALATION_CONDITIONS
from src.python_validation.pipeline import PythonGroundTruthPipeline
from src.routing_rules.router import ROUTING_MAP


ROOT = Path(__file__).resolve().parents[1]
COMPLAINTS = json.loads((ROOT / "sample_complaints" / "complaints_500.json").read_text(encoding="utf-8"))


def test_supportnova_sample_pack_meets_srs_minimums():
    assert len(COMPLAINTS) >= 500
    assert len({item["complaint_id"] for item in COMPLAINTS}) == len(COMPLAINTS)
    assert len({item["category"] for item in COMPLAINTS}) >= 10
    assert len({item["subcategory"] for item in COMPLAINTS}) >= 20
    assert len(ROUTING_MAP) >= 8
    assert len(ALL_RULES) >= 100
    assert len(ESCALATION_CONDITIONS) >= 30
    assert sum(bool(item.get("is_adversarial")) for item in COMPLAINTS) >= 20
    assert sum(item.get("issue_type") == "Multi-issue" for item in COMPLAINTS) >= 25
    assert sum(bool(item.get("is_duplicate")) for item in COMPLAINTS) >= 25


def test_new_subcategories_match_ground_truth_and_approved_policy_ids():
    examples = {
        "Intermittent Failure": ("I have an intermittent hardware failure and my laptop randomly shuts down.", "POL-WAR-07"),
        "Missing Invoice": ("The invoice is missing for my paid order.", "POL-BIL-06"),
        "Wrong Item Delivered": ("I received the wrong item instead of the monitor I ordered.", "POL-DEL-04"),
    }

    for expected_subcategory, (description, expected_policy) in examples.items():
        result = PythonGroundTruthPipeline.validate_complaint({
            "complaint_id": "CMP-SRS-COVERAGE",
            "complaint_title": description,
            "complaint_description": description,
            "customer_type": "Standard",
            "order_reference": "ORD-SRS-COVERAGE",
            "customer_email": "sample@example.com",
        })
        assert result.expected_subcategory == expected_subcategory
        assert result.applicable_policy_id == expected_policy
