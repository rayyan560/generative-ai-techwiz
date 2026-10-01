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
        referenced_policy_version="v2.0",
        resolution_steps=["Verify payment gateway transaction logs for duplicate authorization", "Issue reversal for duplicate transaction"],
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

    sources = {"retrieved_policy_sources": [{"document_id": "POL-BIL-06", "section_id": "1.0", "version": "v2.0", "status": "Active"}]}
    comp = ComparisonEngine.compare_and_verify(genai_out, ground_truth, sources)
    assert comp.category_match is True
    assert comp.department_match is True
    assert comp.verification_status == "Verified"
    assert comp.consistency_score == 100.0
    assert comp.mandatory_coverage_score == 100.0
    assert comp.source_traceability_score == 100.0


def test_comparison_requires_review_for_partial_actions_or_unretrieved_policy():
    genai_out = GenAIIntelligenceOutput(
        complaint_id="CMP-TEST-02",
        primary_issue="Double charge",
        category="Billing & Charges",
        subcategory="Double Charge",
        sentiment="Negative",
        urgency="High",
        priority="P1",
        recommended_department="Billing & Payments",
        referenced_policy_id="POL-BIL-06",
        referenced_policy_section="1.0",
        referenced_policy_version="v2.0",
        resolution_steps=["Check payment gateway logs"],
        escalation_required=False,
        customer_response="We will review the transaction.",
    )
    ground_truth = PythonGroundTruthResult(
        complaint_id="CMP-TEST-02",
        expected_category="Billing & Charges",
        expected_subcategory="Double Charge",
        expected_department="Billing & Payments",
        expected_urgency="High",
        expected_priority="P1",
        mandatory_escalation=False,
        applicable_policy_id="POL-BIL-06",
        applicable_policy_name="Billing policy",
        policy_version="v2.0",
        policy_status="Active",
        refund_eligible=True,
        replacement_eligible=False,
        compensation_allowed=False,
        required_follow_up=True,
        mandatory_resolution_steps=["Verify payment gateway transaction logs for duplicate authorization"],
        rule_id_matched="RUL-BIL-009",
    )

    result = ComparisonEngine.compare_and_verify(genai_out, ground_truth, {"retrieved_policy_sources": []})

    assert result.mandatory_coverage_score == 0.0
    assert result.source_traceability_score == 0.0
    assert result.requires_manual_review is True
    assert result.verification_status == "Manual Review Required"


def test_comparison_does_not_report_unmeasured_coverage_as_perfect():
    ground_truth = PythonGroundTruthResult(
        complaint_id="CMP-TEST-03",
        expected_category="Billing & Charges",
        expected_subcategory="Double Charge",
        expected_department="Billing & Payments",
        expected_urgency="High",
        expected_priority="P1",
        mandatory_escalation=False,
        applicable_policy_id="POL-BIL-06",
        applicable_policy_name="Billing policy",
        policy_version="v2.0",
        policy_status="Active",
        refund_eligible=True,
        replacement_eligible=False,
        compensation_allowed=False,
        required_follow_up=False,
        mandatory_resolution_steps=[],
        rule_id_matched="RUL-BIL-009",
    )
    genai_out = GenAIIntelligenceOutput(
        complaint_id="CMP-TEST-03",
        primary_issue="Billing issue",
        category="Billing & Charges",
        subcategory="Double Charge",
        sentiment="Neutral",
        urgency="High",
        priority="P1",
        recommended_department="Billing & Payments",
        referenced_policy_id="POL-BIL-06",
        referenced_policy_section="1.0",
        referenced_policy_version="v2.0",
        customer_response="We will review it.",
        escalation_required=False,
    )

    result = ComparisonEngine.compare_and_verify(genai_out, ground_truth, {
        "retrieved_policy_sources": [{"document_id": "POL-BIL-06", "section_id": "1.0", "status": "Active"}]
    })

    assert result.mandatory_coverage_score is None


def test_comparison_rejects_old_version_even_when_policy_id_matches():
    ground_truth = PythonGroundTruthResult(
        complaint_id="CMP-TEST-04",
        expected_category="Billing & Charges",
        expected_subcategory="Double Charge",
        expected_department="Billing & Payments",
        expected_urgency="High",
        expected_priority="P1",
        mandatory_escalation=False,
        applicable_policy_id="POL-BIL-06",
        applicable_policy_name="Billing policy",
        policy_version="v3.0",
        policy_status="Active",
        refund_eligible=True,
        replacement_eligible=False,
        compensation_allowed=False,
        required_follow_up=False,
        mandatory_resolution_steps=[],
        rule_id_matched="RUL-BIL-009",
    )
    genai_out = GenAIIntelligenceOutput(
        complaint_id="CMP-TEST-04",
        primary_issue="Double charge",
        category="Billing & Charges",
        subcategory="Double Charge",
        sentiment="Negative",
        urgency="High",
        priority="P1",
        recommended_department="Billing & Payments",
        referenced_policy_id="POL-BIL-06",
        referenced_policy_section="1.0",
        referenced_policy_version="v2.0",
        customer_response="We will review it.",
        escalation_required=False,
    )

    result = ComparisonEngine.compare_and_verify(genai_out, ground_truth, {
        "retrieved_policy_sources": [{
            "document_id": "POL-BIL-06",
            "section_id": "1.0",
            "version": "v3.0",
            "status": "Active",
        }]
    })

    assert result.policy_match is False
    assert result.contradiction_detected is True
    assert result.requires_manual_review is True


def test_comparison_requires_clarification_for_missing_mandatory_fields():
    ground_truth = PythonGroundTruthResult(
        complaint_id="CMP-TEST-05",
        expected_category="Billing & Charges",
        expected_subcategory="Double Charge",
        expected_department="Billing & Payments",
        expected_urgency="High",
        expected_priority="P1",
        mandatory_escalation=False,
        applicable_policy_id="POL-BIL-06",
        applicable_policy_name="Billing policy",
        policy_version="v2.0",
        policy_status="Active",
        refund_eligible=True,
        replacement_eligible=False,
        compensation_allowed=False,
        required_follow_up=False,
        missing_mandatory_fields=["Order Reference Number"],
        mandatory_resolution_steps=[],
        rule_id_matched="RUL-BIL-009",
    )
    genai_out = GenAIIntelligenceOutput(
        complaint_id="CMP-TEST-05",
        primary_issue="Double charge",
        category="Billing & Charges",
        subcategory="Double Charge",
        sentiment="Negative",
        urgency="High",
        priority="P1",
        recommended_department="Billing & Payments",
        referenced_policy_id="POL-BIL-06",
        referenced_policy_section="1.0",
        referenced_policy_version="v2.0",
        customer_response="We will review the transaction.",
        escalation_required=False,
        clarification_questions=[],
    )

    result = ComparisonEngine.compare_and_verify(genai_out, ground_truth, {
        "retrieved_policy_sources": [{
            "document_id": "POL-BIL-06",
            "section_id": "1.0",
            "version": "v2.0",
            "status": "Active",
        }]
    })

    assert result.requires_manual_review is True
    assert "missing" in result.explanation_of_disagreement.lower()
