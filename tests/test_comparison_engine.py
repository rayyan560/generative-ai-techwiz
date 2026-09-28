import pytest
from src.schemas.models import GenAIIntelligenceOutput, PythonGroundTruthResult
from src.comparison_engine.engine import ComparisonEngine

def test_comparison_perfect_match():
    genai_out = GenAIIntelligenceOutput(
        complaint_id="CMP-TEST-01",
        primary_issue="Double charge",
        secondary_issues=[],
        category="Billing & Charges",
        subcategory="Double Charge",
        sentiment="Negative",
        urgency="High",
        priority="P1",
        detected_emotions=["Frustration"],
        extracted_entities={"order_id": "ORD-1234"},
        recommended_department="Billing & Payments",
        supporting_departments=["Customer Relations"],
        referenced_policy_id="POL-BIL-06",
        referenced_policy_section="1.0",
        resolution_steps=["Verify payment gateway logs", "Issue reversal for duplicate transaction"],
        escalation_required=False,
        escalation_tier="Tier 1 - Standard Agent",
        customer_response="We are reversing the duplicate transaction.",
        response_type="Apology & Investigation",
        response_tone="Professional",
        internal_agent_guidance=["Check ERP"],
        follow_up_required=True,
        follow_up_action="Check logs",
        clarification_questions=[],
        adversarial_warning=None
    )

    ground_truth = PythonGroundTruthResult(
        complaint_id="CMP-TEST-01",
        expected_category="Billing & Charges",
        expected_subcategory="Double Charge",
        expected_department="Billing & Payments",
        expected_urgency="High",
        expected_priority="P1",
        mandatory_escalation=False,
        escalation_tier="Tier 1 - Standard Agent",
        applicable_policy_id="POL-BIL-06",
        applicable_policy_name="Policy Billing Disputes",
        policy_version="v2.0",
        policy_status="Active",
        refund_eligible=True,
        replacement_eligible=False,
        compensation_allowed=True,
        max_compensation_limit=15.0,
        mandatory_resolution_steps=["Verify payment gateway logs for duplicate authorization"],
        prohibited_actions=[],
        required_follow_up=True,
        rule_id_matched="RUL-BIL-009"
    )

    comp = ComparisonEngine.compare_and_verify(genai_out, ground_truth, {})
    assert comp.category_match is True
    assert comp.department_match is True
    assert comp.verification_status == "Verified"
    assert comp.consistency_score == 100.0
