from typing import Any, Dict

from src.comparison_engine.metrics import consistency_score, field_matches, mandatory_coverage_score
from src.comparison_engine.verification import verification_decision, verify_policy_sources
from src.schemas.models import ComparisonResult, GenAIIntelligenceOutput, PythonGroundTruthResult


class ComparisonEngine:
    @staticmethod
    def compare_and_verify(
        genai_out: GenAIIntelligenceOutput,
        ground_truth: PythonGroundTruthResult,
        complaint_dict: Dict[str, Any],
    ) -> ComparisonResult:
        matches = field_matches(genai_out, ground_truth)
        coverage = mandatory_coverage_score(genai_out, ground_truth)
        traceability, policy_flags, unsupported, promise_flags = verify_policy_sources(
            genai_out, ground_truth, complaint_dict
        )
        status, manual_review, explanation, contradiction, contradiction_details = verification_decision(
            genai_out,
            ground_truth,
            matches,
            traceability,
            unsupported,
            coverage,
            policy_flags,
            promise_flags,
        )
        return ComparisonResult(
            complaint_id=genai_out.complaint_id,
            category_match=matches["category"],
            subcategory_match=matches["subcategory"],
            department_match=matches["department"],
            urgency_match=matches["urgency"],
            priority_match=matches["priority"],
            escalation_match=matches["escalation"],
            policy_match=matches["policy"],
            mandatory_coverage_score=coverage,
            source_traceability_score=traceability,
            consistency_score=consistency_score(matches),
            unsupported_claims_flagged=promise_flags,
            prohibited_actions_detected=ground_truth.prohibited_actions if unsupported else [],
            unauthorized_promise_detected=unsupported,
            contradiction_detected=contradiction,
            contradiction_details=contradiction_details,
            prompt_injection_detected=bool(genai_out.adversarial_warning),
            is_duplicate=complaint_dict.get("is_duplicate", False),
            duplicate_of_id=complaint_dict.get("duplicate_of_id"),
            verification_status=status,
            explanation_of_disagreement=explanation,
            requires_manual_review=manual_review,
        )
