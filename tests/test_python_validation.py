import pytest
from src.python_validation.pipeline import python_validation_pipeline
from src.schemas.models import PythonGroundTruthResult
from src.complaint_rules.matrix import RuleMatrixManager
from config.settings import settings
from src.escalation_rules.manager import ESCALATION_CONDITIONS, EscalationManager

def test_ground_truth_safety_critical():
    safety_complaint = {
        "complaint_id": "CMP-TEST-SAF",
        "customer_name": "David Miller",
        "customer_type": "Standard",
        "complaint_title": "Battery is swollen and emitting smoke",
        "complaint_description": "My laptop battery pack is bulging and getting extremely hot with smoke."
    }
    gt = python_validation_pipeline.validate_complaint(safety_complaint)
    assert isinstance(gt, PythonGroundTruthResult)
    assert gt.expected_category == "Safety Hazard"
    assert gt.expected_department == "Product Quality & Safety"
    assert gt.mandatory_escalation is True
    assert "Tier 5" in gt.escalation_tier
    assert gt.expected_priority == "P0"

def test_ground_truth_double_charge():
    billing_complaint = {
        "complaint_id": "CMP-TEST-BIL",
        "customer_name": "Emma Watson",
        "customer_type": "Standard",
        "complaint_title": "Charged twice on credit card",
        "complaint_description": "I got a double charge for order ORD-1122 for $149."
    }
    gt = python_validation_pipeline.validate_complaint(billing_complaint)
    assert gt.expected_category == "Billing & Charges"
    assert gt.expected_department == "Billing & Payments"
    assert gt.refund_eligible is True

def test_rule_matrix_covers_all_configured_categories():
    rules = RuleMatrixManager.get_all_rules()
    assert len(rules) >= 100
    assert set(settings.CATEGORIES).issubset({rule["category"] for rule in rules})


def test_rule_matrix_prefers_exact_subcategory_over_category_keyword():
    rule = RuleMatrixManager.match_rule(
        "Product Defect",
        "Physical Damage",
        "Standard",
        "Please review my product defect. The screen was cracked.",
    )
    assert rule["category"] == "Product Defect"
    assert rule["subcategory"] == "Physical Damage"


def test_escalation_conditions_are_named_and_not_placeholder_rules():
    assert len(ESCALATION_CONDITIONS) == 34
    assert all(not condition["name"].startswith("Specific Regulatory / Operational") for condition in ESCALATION_CONDITIONS)
    escalated, tier, _, rule_id = EscalationManager.evaluate_escalation({
        "complaint_title": "Hospitalized after chemical exposure",
        "complaint_description": "The device released toxic fumes.",
    })
    assert escalated is True
    assert "Tier 5" in tier
    assert rule_id == "ESC-016"
