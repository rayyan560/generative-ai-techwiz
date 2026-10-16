import re
from typing import Any, Dict, Tuple

from src.escalation_rules.conditions_core import CORE_ESCALATION_CONDITIONS
from src.escalation_rules.conditions_customer import CUSTOMER_ESCALATION_CONDITIONS
from src.escalation_rules.conditions_extended import EXTENDED_ESCALATION_CONDITIONS


ESCALATION_CONDITIONS = [
    *CORE_ESCALATION_CONDITIONS,
    *CUSTOMER_ESCALATION_CONDITIONS,
    *EXTENDED_ESCALATION_CONDITIONS,
]


class EscalationManager:
    @staticmethod
    def evaluate_escalation(complaint_dict: Dict[str, Any]) -> Tuple[bool, str, str, str]:
        text = f"{complaint_dict.get('complaint_title', '')} {complaint_dict.get('complaint_description', '')}".lower()
        matches = []
        for index, condition in enumerate(ESCALATION_CONDITIONS):
            matched = bool("pattern" in condition and re.search(condition["pattern"], text))
            if not matched and "condition_fn" in condition:
                try:
                    matched = bool(condition["condition_fn"](complaint_dict))
                except Exception:
                    matched = False
            if matched:
                tier = re.search(r"Tier\s+(\d+)", condition.get("required_tier", ""))
                matches.append((int(tier.group(1)) if tier else 0, -index, condition))
        if matches:
            _, _, selected = max(matches, key=lambda match: (match[0], match[1]))
            return True, selected["required_tier"], selected["reason"], selected["esc_id"]
        return False, "Tier 1 - Standard Agent", "Standard frontline agent resolution", "ESC-NONE"
