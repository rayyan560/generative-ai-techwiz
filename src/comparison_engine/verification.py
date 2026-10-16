from typing import Any, Dict, List, Tuple

from src.hallucination_checks.detector import HallucinationDetector
from src.schemas.models import GenAIIntelligenceOutput, PythonGroundTruthResult


def verify_policy_sources(
    genai: GenAIIntelligenceOutput,
    ground_truth: PythonGroundTruthResult,
    complaint: Dict[str, Any],
) -> Tuple[float, List[str], bool, List[str]]:
    traceability, policy_flags = HallucinationDetector.verify_policy_traceability(
        genai,
        ground_truth,
        complaint.get("retrieved_policy_sources", []),
    )
    unsupported, promise_flags = HallucinationDetector.detect_unsupported_promises(genai, ground_truth)
    return traceability, policy_flags, unsupported, promise_flags


def verification_decision(
    genai: GenAIIntelligenceOutput,
    ground_truth: PythonGroundTruthResult,
    matches: Dict[str, bool],
    traceability: float,
    unsupported_promises: bool,
    coverage: float | None,
    policy_flags: List[str],
    promise_flags: List[str],
) -> Tuple[str, bool, str, bool, str | None]:
    contradiction_details = None
    if not matches["escalation"] and ground_truth.mandatory_escalation:
        contradiction_details = "CRITICAL: Python Ground-Truth mandates escalation but GenAI missed it."
    elif "OLD" in (genai.referenced_policy_id or ""):
        contradiction_details = "Policy Contradiction: Outdated/Superseded policy cited."
    elif (
        genai.referenced_policy_id == ground_truth.applicable_policy_id
        and genai.referenced_policy_version.strip().casefold()
        != ground_truth.policy_version.strip().casefold()
    ):
        contradiction_details = "Policy Contradiction: The cited policy version is not the current ground-truth version."
    missing_information = bool(ground_truth.missing_mandatory_fields) and not genai.clarification_questions
    unresolved_warning = (
        bool(genai.adversarial_warning)
        or unsupported_promises
        or not matches["policy"]
        or traceability < 100.0
        or missing_information
        or ground_truth.policy_status.casefold() != "active"
    )
    missing_actions = coverage is not None and coverage < 100.0
    mismatches = [name for name, matched in matches.items() if name != "policy" and not matched]
    if contradiction_details:
        return "Contradiction Detected", True, contradiction_details, True, contradiction_details
    if unresolved_warning or missing_actions:
        details = list(promise_flags) + list(policy_flags)
        if genai.adversarial_warning:
            details.append("Adversarial instructions were detected in complaint text")
        if missing_actions:
            details.append(f"Mandatory resolution-step coverage is {coverage}%, below the full-required-actions threshold")
        if missing_information:
            details.append("Required complaint information is missing and no clarification question was generated")
        if ground_truth.policy_status.casefold() != "active":
            details.append(f"Ground-truth policy status requires review: {ground_truth.policy_status}")
        explanation = "; ".join(details) or "One or more source or mandatory-action checks require staff review."
        return "Manual Review Required", True, explanation, False, None
    if mismatches:
        explanation = "Rule comparison mismatch: " + ", ".join(mismatches)
        return "Verified with Warning", True, explanation, False, None
    return "Verified", False, "Configured classification, escalation, source-reference, and required-action checks matched.", False, None
