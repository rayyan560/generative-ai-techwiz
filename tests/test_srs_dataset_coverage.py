import json
from pathlib import Path

from src.complaint_rules.matrix import ALL_RULES
from src.escalation_rules.manager import ESCALATION_CONDITIONS
from src.python_validation.pipeline import PythonGroundTruthPipeline
from src.routing_rules.router import ROUTING_MAP
from src.complaint_processing.duplicates import identify_related_complaints
from src.security.prompt_defense import PromptDefense


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


def test_every_adversarial_sample_triggers_prompt_defense():
    adversarial_cases = [item for item in COMPLAINTS if item.get("is_adversarial")]
    missed_cases = []

    for case in adversarial_cases:
        text = f"{case.get('complaint_title', '')}\n{case.get('complaint_description', '')}"
        suspicious, _ = PromptDefense.inspect_text_for_injections(text)
        if not suspicious:
            missed_cases.append(case.get("complaint_id", "unknown"))

    assert len(adversarial_cases) >= 25
    assert missed_cases == []


def test_prompt_defense_does_not_flag_non_adversarial_non_repeat_samples():
    ordinary_cases = [
        item
        for item in COMPLAINTS
        if not item.get("is_adversarial") and item.get("issue_type") != "Repeated complaint"
    ]
    false_positives = []

    for case in ordinary_cases:
        text = f"{case.get('complaint_title', '')}\n{case.get('complaint_description', '')}"
        suspicious, _ = PromptDefense.inspect_text_for_injections(text)
        if suspicious:
            false_positives.append(case.get("complaint_id", "unknown"))

    assert ordinary_cases
    assert false_positives == []


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


def test_near_duplicate_and_repeat_detection_is_limited_to_same_customer_history():
    current = {
        "user_id": "user-1",
        "customer_email": "customer@example.com",
        "complaint_id": "CMP-NEW",
        "complaint_title": "Laptop keeps shutting down",
        "complaint_description": "My laptop randomly shuts down during video calls.",
        "order_reference": "ORD-23456",
        "content_hash": "new-hash",
    }
    history = [
        {
            "user_id": "user-1",
            "customer_email": "customer@example.com",
            "complaint_id": "CMP-OLD",
            "complaint_title": "Laptop shuts off during calls",
            "complaint_description": "The laptop powers down in the middle of video meetings.",
            "order_reference": "ORD-23456",
            "content_hash": "old-hash",
            "status": "In Progress",
        },
        {
            "user_id": "user-2",
            "customer_email": "other@example.com",
            "complaint_id": "CMP-OTHER",
            "complaint_title": current["complaint_title"],
            "complaint_description": current["complaint_description"],
            "order_reference": "ORD-23456",
            "content_hash": current["content_hash"],
            "status": "New",
        },
    ]

    result = identify_related_complaints(current, history)

    assert result["is_duplicate"] is False
    assert result["is_repeat_complaint"] is True
    assert result["repeat_count"] == 1
    assert result["related_complaint_id"] == "CMP-OLD"
