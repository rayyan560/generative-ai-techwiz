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
    def verify_policy_traceability(genai_out: GenAIIntelligenceOutput, ground_truth: PythonGroundTruthResult) -> Tuple[float, List[str]]:
        """Verifies whether GenAI cited valid and active policy IDs rather than hallucinated or obsolete IDs."""
        flags = []
        score = 100.0
        
        gen_pol = genai_out.referenced_policy_id or ""
        if not gen_pol:
            score -= 30.0
            flags.append("No policy ID cited by GenAI")
        elif "OLD" in gen_pol.upper() or "V1" in gen_pol.upper():
            score -= 50.0
            flags.append(f"GenAI referenced superseded/obsolete policy ({gen_pol})")
        elif gen_pol != ground_truth.applicable_policy_id:
            # Minor mismatch
            score -= 15.0
            flags.append(f"Policy mismatch: GenAI cited {gen_pol}, expected {ground_truth.applicable_policy_id}")

        return max(0.0, score), flags
