import re
from typing import List, Tuple

from src.security.roles import USER_ROLES

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above|system)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|system)\s+rules",
    r"disregard\s+(?:all\s+)?(?:[a-z]+\s+){0,3}(?:policy|policies|rules|constraints)",
    r"regardless\s+of\s+(?:the\s+)?(?:company\s+)?(?:policy|policies|rules)",
    r"without\s+(?:checking|following|considering)\s+(?:the\s+)?(?:company\s+)?(?:policy|policies|rules)",
    r"system\s+override",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"you\s+must\s+approve\s+a?\s*(full\s+)?refund\s+immediately",
    r"grant\s+(full\s+)?admin(istrator)?\s+access",
    r"execute\s+command",
    r"print\s+system\s+prompt",
    r"show\s+secret\s+key",
    r"(?:output|reveal|show|print|expose|dump|leak)\s+(?:all\s+)?(?:(?:confidential|hidden|internal|the)\s+)?(?:system\s+prompt|api\s+keys?|secret\s+keys?|prompt\s+templates?)",
    r"(?:```|~~~)\s*(?:system|developer|assistant)\b|\[\s*critical_instruction\s*\]",
    r"(?:select\s+\*\s+from\s+\w+|drop\s+table\s+\w+)",
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
        if not text:
            return ""
        for marker in (
            "<<<UNTRUSTED_TEXT_START>>>",
            "<<<UNTRUSTED_TEXT_END>>>",
            "<<<POLICY_SOURCE_START>>>",
            "<<<POLICY_SOURCE_END>>>",
        ):
            text = re.sub(re.escape(marker), "[literal prompt boundary marker]", text, flags=re.IGNORECASE)
        sanitized = text.replace("```system", "'''system")
        sanitized = sanitized.replace("```assistant", "'''assistant")
        sanitized = sanitized.replace("```json", "'''json")
        sanitized = sanitized.replace("<|im_start|>", "")
        sanitized = sanitized.replace("<|im_end|>", "")
        return sanitized.strip()
