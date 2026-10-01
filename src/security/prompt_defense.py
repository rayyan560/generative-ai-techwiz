import re
from typing import Tuple, List, Dict, Any

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above|system)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|system)\s+rules",
    r"system\s+override",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"you\s+must\s+approve\s+a?\s*(full\s+)?refund\s+immediately",
    r"grant\s+(full\s+)?admin(istrator)?\s+access",
    r"execute\s+command",
    r"print\s+system\s+prompt",
    r"show\s+secret\s+key",
    r"give\s+me\s+free\s+gift\s*card",
    r"authorize\s+unlimited\s+compensation",
    r"jailbreak",
    r"dan\s+mode",
    r"pretend\s+to\s+be\s+an\s+admin",
    r"bypass\s+(all\s+)?policy"
]

ADVERSARIAL_COMPENSATION_TRAPS = [
    r"give\s+me\s+\$\d{4,}",
    r"promise\s+me\s+100%\s+cashback",
    r"threaten\s+lawsuit\s+unless\s+you\s+pay\s+\$\d+",
    r"waive\s+all\s+return\s+conditions"
]

class PromptDefense:
    @staticmethod
    def inspect_text_for_injections(text: str) -> Tuple[bool, List[str]]:
        """Inspects customer complaint text for adversarial prompt injection or override instructions."""
        if not text:
            return False, []
        
        flags = []
        lower_text = text.lower()
        
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, lower_text):
                flags.append(f"Prompt Injection Pattern Detected: {pattern}")
                
        for trap in ADVERSARIAL_COMPENSATION_TRAPS:
            if re.search(trap, lower_text):
                flags.append(f"Adversarial Compensation Extortion Detected: {trap}")
                
        is_suspicious = len(flags) > 0
        return is_suspicious, flags

    @staticmethod
    def sanitize_untrusted_input(text: str) -> str:
        """Sanitizes text to avoid delimiter breakouts while keeping semantic content intact."""
        if not text:
            return ""
        for marker in (
            "<<<UNTRUSTED_TEXT_START>>>",
            "<<<UNTRUSTED_TEXT_END>>>",
            "<<<POLICY_SOURCE_START>>>",
            "<<<POLICY_SOURCE_END>>>",
        ):
            text = re.sub(re.escape(marker), "[literal prompt boundary marker]", text, flags=re.IGNORECASE)
        # Neutralize markdown system prompt injection wrappers
        sanitized = text.replace("```system", "'''system")
        sanitized = sanitized.replace("```assistant", "'''assistant")
        sanitized = sanitized.replace("```json", "'''json")
        sanitized = sanitized.replace("<|im_start|>", "")
        sanitized = sanitized.replace("<|im_end|>", "")
        return sanitized.strip()

# User Roles & RBAC Matrix
USER_ROLES = {
    "customer": {
        "can_submit_complaint": True,
        "can_view_own_complaint": True,
        "can_view_internal_ai_analysis": False,  # Customer must NEVER see AI backend
        "can_view_validation_rules": False,
        "can_perform_triage": False,
        "can_override_decisions": False,
        "can_manage_knowledge_base": False
    },
    "agent": {
        "can_submit_complaint": True,
        "can_view_own_complaint": True,
        "can_view_internal_ai_analysis": True,
        "can_view_validation_rules": True,
        "can_perform_triage": True,
        "can_override_decisions": False,
        "can_manage_knowledge_base": False
    },
    "reviewer": {
        "can_submit_complaint": True,
        "can_view_own_complaint": True,
        "can_view_internal_ai_analysis": True,
        "can_view_validation_rules": True,
        "can_perform_triage": True,
        "can_override_decisions": True,
        "can_manage_knowledge_base": False
    },
    "manager": {
        "can_submit_complaint": True,
        "can_view_own_complaint": True,
        "can_view_internal_ai_analysis": True,
        "can_view_validation_rules": True,
        "can_perform_triage": True,
        "can_override_decisions": True,
        "can_manage_knowledge_base": True
    },
    "admin": {
        "can_submit_complaint": True,
        "can_view_own_complaint": True,
        "can_view_internal_ai_analysis": True,
        "can_view_validation_rules": True,
        "can_perform_triage": True,
        "can_override_decisions": True,
        "can_manage_knowledge_base": True
    }
}
