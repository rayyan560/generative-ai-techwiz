import pytest
from src.python_validation.pipeline import python_validation_pipeline
from src.schemas.models import PythonGroundTruthResult

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
