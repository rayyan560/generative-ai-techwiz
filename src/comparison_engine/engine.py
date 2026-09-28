from typing import Dict, Any, List
from src.schemas.models import GenAIIntelligenceOutput, PythonGroundTruthResult, ComparisonResult
from src.hallucination_checks.detector import HallucinationDetector

class ComparisonEngine:
    @staticmethod
    def compare_and_verify(
        genai_out: GenAIIntelligenceOutput,
        ground_truth: PythonGroundTruthResult,
        complaint_dict: Dict[str, Any]
    ) -> ComparisonResult:
        """
        Compares GenAI Intelligence output with Python Ground-Truth rules.
        Calculates coverage, traceability, consistency, and sets the verification status.
        """
        complaint_id = genai_out.complaint_id
        
        # 1. Field-by-field matches
        category_match = (genai_out.category.lower() == ground_truth.expected_category.lower())
        subcategory_match = (genai_out.subcategory.lower() == ground_truth.expected_subcategory.lower())
        department_match = (genai_out.recommended_department.lower() == ground_truth.expected_department.lower())
        urgency_match = (genai_out.urgency.lower() == ground_truth.expected_urgency.lower())
        priority_match = (genai_out.priority.upper() == ground_truth.expected_priority.upper())
        escalation_match = (genai_out.escalation_required == ground_truth.mandatory_escalation)
        policy_match = (genai_out.referenced_policy_id == ground_truth.applicable_policy_id)

        # 2. Mandatory Resolution Steps Coverage Calculation
        mandatory_steps = ground_truth.mandatory_resolution_steps
        genai_steps = " ".join(genai_out.resolution_steps).lower()
        
        covered_count = 0
        if mandatory_steps:
            for step in mandatory_steps:
                # Check if key words in mandatory step appear in genai steps
                keywords = [w.lower() for w in step.split() if len(w) > 4]
                if any(kw in genai_steps for kw in keywords) or len(keywords) == 0:
                    covered_count += 1
            coverage_score = round((covered_count / len(mandatory_steps)) * 100.0, 1)
        else:
            coverage_score = 100.0

        # 3. Source Traceability & Hallucination Checks
        traceability_score, policy_flags = HallucinationDetector.verify_policy_traceability(genai_out, ground_truth)
        has_unsupported_promises, promise_flags = HallucinationDetector.detect_unsupported_promises(genai_out, ground_truth)

        # 4. Prompt Injection & Adversarial Flag
        prompt_injection = bool(genai_out.adversarial_warning)
        
        # 5. Consistency Score
        match_weights = [
            (category_match, 25.0),
            (department_match, 20.0),
            (urgency_match, 15.0),
            (priority_match, 15.0),
            (escalation_match, 25.0)
        ]
        consistency_score = sum(w for matched, w in match_weights if matched)

        # 6. Contradiction & Unsupported Claim Detection
        contradiction = False
        contradiction_details = None
        if not escalation_match and ground_truth.mandatory_escalation:
            contradiction = True
            contradiction_details = "CRITICAL: Python Ground-Truth mandates escalation but GenAI missed it."
        elif "OLD" in (genai_out.referenced_policy_id or ""):
            contradiction = True
            contradiction_details = "Policy Contradiction: Outdated/Superseded policy cited."

        # 7. Final Verification Status Decision
        requires_manual_review = False
        if contradiction or has_unsupported_promises or prompt_injection or (ground_truth.mandatory_escalation and not genai_out.escalation_required):
            verification_status = "Manual Review Required" if not contradiction else "Contradiction Detected"
            requires_manual_review = True
            explanation = contradiction_details or "; ".join(promise_flags or policy_flags) or "Significant mismatch requiring manager sign-off."
        elif not department_match or not category_match or coverage_score < 70.0:
            verification_status = "Verified with Warning"
            explanation = f"Department or Category variation (GenAI: {genai_out.recommended_department} / Expected: {ground_truth.expected_department})"
        elif has_unsupported_promises:
            verification_status = "Unsupported Requirement"
            requires_manual_review = True
            explanation = "; ".join(promise_flags)
        else:
            verification_status = "Verified"
            explanation = "100% compliant with ground-truth complaint matrix and active policies."

        return ComparisonResult(
            complaint_id=complaint_id,
            category_match=category_match,
            subcategory_match=subcategory_match,
            department_match=department_match,
            urgency_match=urgency_match,
            priority_match=priority_match,
            escalation_match=escalation_match,
            policy_match=policy_match,
            mandatory_coverage_score=coverage_score,
            source_traceability_score=traceability_score,
            consistency_score=consistency_score,
            unsupported_claims_flagged=promise_flags,
            prohibited_actions_detected=ground_truth.prohibited_actions if has_unsupported_promises else [],
            unauthorized_promise_detected=has_unsupported_promises,
            contradiction_detected=contradiction,
            contradiction_details=contradiction_details,
            prompt_injection_detected=prompt_injection,
            is_duplicate=complaint_dict.get("is_duplicate", False),
            duplicate_of_id=complaint_dict.get("duplicate_of_id"),
            verification_status=verification_status,
            explanation_of_disagreement=explanation,
            requires_manual_review=requires_manual_review
        )
