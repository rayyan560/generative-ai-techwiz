import re
from typing import List, Dict, Any, Tuple
from src.schemas.models import GenAIIntelligenceOutput, PythonGroundTruthResult

PROMISE_KEYWORDS = [
    (r"\bwe (guarantee|promise|assure you) a full refund\b", "Unauthorized full refund promise without prior inspection"),
    (r"\bwe will instantly credit \$\d+\b", "Unauthorized instant credit commitment"),
    (r"\byou will receive a brand new replacement tomorrow\b", "Unauthorized delivery deadline commitment"),
    (r"\bwaive all fees and return conditions\b", "Unauthorized waiver of policy terms")
]

class HallucinationDetector:
    @staticmethod
    def detect_unsupported_promises(genai_out: GenAIIntelligenceOutput, ground_truth: PythonGroundTruthResult) -> Tuple[bool, List[str]]:
        """Checks if GenAI response made commitments forbidden by ground-truth rules."""
        violations = []
        resp_text = genai_out.customer_response.lower()
        
        # 1. Regex checks for explicit unauthorized promises
        for pattern, desc in PROMISE_KEYWORDS:
            if re.search(pattern, resp_text):
                violations.append(desc)
                
        # 2. If refund is NOT eligible under Python Ground Truth, but GenAI recommended immediate refund
        if not ground_truth.refund_eligible and "refund" in [s.lower() for s in genai_out.resolution_steps]:
            if "process immediate refund" in resp_text or "full refund will be credited" in resp_text:
                violations.append("GenAI promised refund on an item classified as non-refundable under Policy")

        # 3. If compensation exceeds policy limit
        # Check if amount mentioned in response is higher than max_compensation_limit
        amount_match = re.search(r"\$(\d+)", resp_text)
        if amount_match:
            amt = float(amount_match.group(1))
            if amt > ground_truth.max_compensation_limit and ground_truth.max_compensation_limit > 0:
                violations.append(f"Customer response promised ${amt} exceeding ground-truth limit of ${ground_truth.max_compensation_limit}")

        return len(violations) > 0, violations

    @staticmethod
    def verify_policy_traceability(genai_out: GenAIIntelligenceOutput, ground_truth: PythonGroundTruthResult, retrieved_sources: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """Checks policy citations against active chunks actually retrieved for the complaint."""
        flags = []
        if ground_truth.policy_status.casefold() != "active":
            return 0.0, [f"Ground-truth policy {ground_truth.applicable_policy_id} is not currently usable ({ground_truth.policy_status})"]
        gen_pol = (genai_out.referenced_policy_id or "").strip().upper()
        gen_section = (genai_out.referenced_policy_section or "").strip().casefold()
        gen_version = genai_out.referenced_policy_version.strip().casefold()
        active_sources = [
            source for source in retrieved_sources
            if str(source.get("status", "")).strip().casefold() == "active"
        ]
        cited_sources = [
            source for source in active_sources
            if str(source.get("document_id", "")).strip().upper() == gen_pol
        ]
        if not gen_pol:
            return 0.0, ["No policy ID cited by GenAI"]
        if "OLD" in gen_pol or "V1" in gen_pol:
            return 0.0, [f"GenAI referenced superseded/obsolete policy ({gen_pol})"]
        if gen_pol != ground_truth.applicable_policy_id.strip().upper():
            flags.append(f"Policy mismatch: GenAI cited {gen_pol}, expected {ground_truth.applicable_policy_id}")
            return 0.0, flags
        if gen_version != ground_truth.policy_version.strip().casefold():
            flags.append(f"Policy version mismatch: GenAI cited {gen_version or 'no version'}, expected {ground_truth.policy_version}")
            return 0.0, flags
        if not cited_sources:
            return 0.0, [f"No retrieved active source chunk verifies policy {gen_pol}"]
        source_versions = {
            str(source.get("version", "")).strip().casefold()
            for source in cited_sources
        }
        if gen_version not in source_versions:
            return 0.0, [f"No retrieved active source verifies policy version {gen_version}"]
        source_sections = {
            str(source.get("section_id", "")).strip().casefold()
            for source in cited_sources
            if source.get("section_id")
        }
        if not gen_section or gen_section not in source_sections:
            return 50.0, ["The cited policy section is not among the retrieved source sections"]
        return 100.0, flags
