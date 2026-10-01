import re
from difflib import SequenceMatcher
from typing import Any, Dict, Iterable, Optional


RESOLVED_STATUSES = {"resolved", "closed", "refund approved", "case closed"}


def _normalized_text(record: Dict[str, Any]) -> str:
    text = f"{record.get('complaint_title', '')} {record.get('complaint_description', '')}"
    return " ".join(re.findall(r"[a-z0-9]+", text.casefold()))


def _similarity(first: str, second: str) -> float:
    if not first or not second:
        return 0.0
    first_words = set(first.split())
    second_words = set(second.split())
    overlap = len(first_words & second_words) / len(first_words | second_words)
    sequence = SequenceMatcher(None, first, second).ratio()
    return max(overlap, sequence)


def _same_customer(current: Dict[str, Any], previous: Dict[str, Any]) -> bool:
    current_user = str(current.get("user_id") or "").strip()
    previous_user = str(previous.get("user_id") or "").strip()
    if current_user and previous_user:
        return current_user == previous_user
    current_email = str(current.get("customer_email") or "").strip().casefold()
    previous_email = str(previous.get("customer_email") or "").strip().casefold()
    return bool(current_email and current_email == previous_email)


def identify_related_complaints(
    current: Dict[str, Any],
    history: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    current_text = _normalized_text(current)
    matches = []
    for previous in history:
        if not _same_customer(current, previous):
            continue
        score = _similarity(current_text, _normalized_text(previous))
        exact = bool(current.get("content_hash")) and current.get("content_hash") == previous.get("content_hash")
        same_reference = any(
            current.get(field)
            and previous.get(field)
            and str(current[field]).strip().casefold() == str(previous[field]).strip().casefold()
            for field in ("order_reference", "transaction_reference")
        )
        unresolved = str(previous.get("status", "New")).strip().casefold() not in RESOLVED_STATUSES
        duplicate = exact or score >= 0.82
        repeat = unresolved and (score >= 0.5 or same_reference)
        if duplicate or repeat:
            matches.append({
                "complaint_id": previous.get("complaint_id"),
                "score": round(score, 3),
                "duplicate": duplicate,
                "repeat": repeat,
            })

    duplicate_matches = [match for match in matches if match["duplicate"]]
    repeat_matches = [match for match in matches if match["repeat"]]
    best_match = max(matches, key=lambda match: match["score"], default=None)
    best_duplicate = max(duplicate_matches, key=lambda match: match["score"], default=None)
    return {
        "is_duplicate": best_duplicate is not None,
        "duplicate_of_id": best_duplicate["complaint_id"] if best_duplicate else None,
        "duplicate_similarity": best_duplicate["score"] if best_duplicate else None,
        "is_repeat_complaint": bool(repeat_matches),
        "repeat_count": len(repeat_matches),
        "related_complaint_id": best_match["complaint_id"] if best_match else None,
    }
