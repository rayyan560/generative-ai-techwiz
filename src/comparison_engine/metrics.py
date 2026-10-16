import re
from typing import Dict, Optional

from src.schemas.models import GenAIIntelligenceOutput, PythonGroundTruthResult


def field_matches(
    genai: GenAIIntelligenceOutput, ground_truth: PythonGroundTruthResult
) -> Dict[str, bool]:
    return {
        "category": genai.category.casefold() == ground_truth.expected_category.casefold(),
        "subcategory": genai.subcategory.casefold() == ground_truth.expected_subcategory.casefold(),
        "department": genai.recommended_department.casefold() == ground_truth.expected_department.casefold(),
        "urgency": genai.urgency.casefold() == ground_truth.expected_urgency.casefold(),
        "priority": genai.priority.upper() == ground_truth.expected_priority.upper(),
        "escalation": genai.escalation_required == ground_truth.mandatory_escalation,
        "policy": (
            genai.referenced_policy_id == ground_truth.applicable_policy_id
            and genai.referenced_policy_version.strip().casefold()
            == ground_truth.policy_version.strip().casefold()
        ),
    }


def mandatory_coverage_score(
    genai: GenAIIntelligenceOutput, ground_truth: PythonGroundTruthResult
) -> Optional[float]:
    mandatory_steps = ground_truth.mandatory_resolution_steps
    if not mandatory_steps:
        return None
    ignored = {
        "check", "verify", "review", "confirm", "ensure", "provide", "perform",
        "conduct", "the", "and", "for", "with", "from", "should", "must",
    }
    response_words = {
        word.casefold() for word in re.findall(r"[a-zA-Z0-9]+", " ".join(genai.resolution_steps))
    }
    covered = 0
    for step in mandatory_steps:
        action_words = {
            word.casefold()
            for word in re.findall(r"[a-zA-Z0-9]+", step)
            if len(word) >= 4 and word.casefold() not in ignored
        }
        if not action_words or len(action_words & response_words) / len(action_words) >= 0.75:
            covered += 1
    return round((covered / len(mandatory_steps)) * 100.0, 1)


def consistency_score(matches: Dict[str, bool]) -> float:
    weights = {
        "category": 20.0,
        "subcategory": 10.0,
        "department": 15.0,
        "urgency": 10.0,
        "priority": 10.0,
        "escalation": 20.0,
        "policy": 15.0,
    }
    return sum(weight for field, weight in weights.items() if matches[field])
