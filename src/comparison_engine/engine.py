import re
from typing import Dict, Any, List, Optional
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
        policy_match = (
            genai_out.referenced_policy_id == ground_truth.applicable_policy_id
            and genai_out.referenced_policy_version.strip().casefold() == ground_truth.policy_version.strip().casefold()
        )

        # 2. Mandatory Resolution Steps Coverage Calculation
        mandatory_steps = ground_truth.mandatory_resolution_steps
        genai_step_words = {
            word.casefold()
            for word in re.findall(r"[a-zA-Z0-9]+", " ".join(genai_out.resolution_steps))
        }
        ignored_terms = {"check", "verify", "review", "confirm", "ensure", "provide", "perform", "conduct", "the", "and", "for", "with", "from", "should", "must"}
        covered_count = 0
        for step in mandatory_steps:
            action_words = {
                word.casefold()
                for word in re.findall(r"[a-zA-Z0-9]+", step)
                if len(word) >= 4 and word.casefold() not in ignored_terms
            }
            if not action_words or len(action_words & genai_step_words) / len(action_words) >= 0.75:
                covered_count += 1
        coverage_score: Optional[float] = round((covered_count / len(mandatory_steps)) * 100.0, 1) if mandatory_steps else None

        # 3. Source Traceability & Hallucination Checks
        traceability_score, policy_flags = HallucinationDetector.verify_policy_traceability(
            genai_out,
            ground_truth,
            complaint_dict.get("retrieved_policy_sources", []),
        )
        has_unsupported_promises, promise_flags = HallucinationDetector.detect_unsupported_promises(genai_out, ground_truth)

        # 4. Prompt Injection & Adversarial Flag
        prompt_injection = bool(genai_out.adversarial_warning)
        
        # 5. Consistency Score
        match_weights = [
            (category_match, 20.0),
            (subcategory_match, 10.0),
            (department_match, 15.0),
            (urgency_match, 10.0),
            (priority_match, 10.0),
            (escalation_match, 20.0),
            (policy_match, 15.0),
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
        elif (
            genai_out.referenced_policy_id == ground_truth.applicable_policy_id
            and genai_out.referenced_policy_version.strip().casefold() != ground_truth.policy_version.strip().casefold()
        ):
            contradiction = True
            contradiction_details = "Policy Contradiction: The cited policy version is not the current ground-truth version."

        # 7. Final Verification Status Decision
        field_mismatches = [
            name for name, matched in (
                ("category", category_match),
                ("subcategory", subcategory_match),
                ("department", department_match),
                ("urgency", urgency_match),
                ("priority", priority_match),
                ("escalation", escalation_match),
            ) if not matched
        ]
        requires_manual_review = False
        missing_information_unaddressed = bool(ground_truth.missing_mandatory_fields) and not genai_out.clarification_questions
        unresolved_warnings = (
            prompt_injection
            or has_unsupported_promises
            or not policy_match
            or traceability_score < 100.0
            or missing_information_unaddressed
            or ground_truth.policy_status.casefold() != "active"
        )
        missing_actions = coverage_score is not None and coverage_score < 100.0
        if contradiction:
            verification_status = "Contradiction Detected"
            requires_manual_review = True
            explanation = contradiction_details or "A mandatory policy or escalation check conflicts with the generated result."
        elif unresolved_warnings or missing_actions:
            verification_status = "Manual Review Required"
            requires_manual_review = True
            details = promise_flags + policy_flags
            if prompt_injection:
                details.append("Adversarial instructions were detected in complaint text")
            if missing_actions:
                details.append(f"Mandatory resolution-step coverage is {coverage_score}%, below the full-required-actions threshold")
            if missing_information_unaddressed:
                details.append("Required complaint information is missing and no clarification question was generated")
            if ground_truth.policy_status.casefold() != "active":
                details.append(f"Ground-truth policy status requires review: {ground_truth.policy_status}")
            explanation = "; ".join(details) or "One or more source or mandatory-action checks require staff review."
        elif field_mismatches:
            verification_status = "Verified with Warning"
            requires_manual_review = True
            explanation = "Rule comparison mismatch: " + ", ".join(field_mismatches)
        else:
            verification_status = "Verified"
            explanation = "Configured classification, escalation, source-reference, and required-action checks matched."

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
