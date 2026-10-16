import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.complaint_rules.rule_expansion import build_full_rule_matrix


RULES_MATRIX: List[Dict[str, Any]] = json.loads(
    Path(__file__).with_name("rules_base.json").read_text(encoding="utf-8")
)
ALL_RULES = build_full_rule_matrix(RULES_MATRIX)


class RuleMatrixManager:
    @staticmethod
    def get_all_rules() -> List[Dict[str, Any]]:
        return ALL_RULES

    @staticmethod
    def match_rule(
        category: str,
        subcategory: str,
        customer_type: str = "Standard",
        description: str = "",
    ) -> Optional[Dict[str, Any]]:
        description_lower = description.lower()
        exact_rules = [
            rule for rule in ALL_RULES
            if rule["category"] == category and rule.get("subcategory") == subcategory
        ]
        if exact_rules:
            preferred_tier = "VIP Customer" if customer_type == "VIP" else "Standard"
            return next(
                (rule for rule in exact_rules if rule.get("customer_tier_condition") == preferred_tier),
                next((rule for rule in exact_rules if not rule.get("customer_tier_condition")), exact_rules[0]),
            )
        category_rules = [rule for rule in ALL_RULES if rule["category"] == category]
        specific_matches = []
        ignored_terms = {category.lower(), customer_type.lower(), "standard", "vip customer", "repeat complaint"}
        for rule in category_rules:
            terms = [term for term in rule.get("keywords", []) if term.lower() not in ignored_terms]
            matching = [term for term in terms if term and term in description_lower]
            if matching:
                specific_matches.append((max(map(len, matching)), rule))
        if specific_matches:
            return max(specific_matches, key=lambda match: match[0])[1]
        if category_rules:
            return next((rule for rule in category_rules if not rule.get("customer_tier_condition")), category_rules[0])
        return ALL_RULES[0]
