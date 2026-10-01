import re
from datetime import date
from typing import Any, Dict, Iterable, Optional, Tuple


def _version_order(record: Dict[str, Any]) -> Tuple[str, Tuple[int, ...]]:
    effective_date = str(record.get("effective_date") or "0001-01-01")[:10]
    version_numbers = tuple(int(value) for value in re.findall(r"\d+", str(record.get("version", ""))))
    return effective_date, version_numbers


def _within_effective_period(record: Dict[str, Any], today: date) -> Tuple[bool, Optional[str]]:
    try:
        effective = date.fromisoformat(str(record["effective_date"])[:10]) if record.get("effective_date") else None
        expiry = date.fromisoformat(str(record["expiry_date"])[:10]) if record.get("expiry_date") else None
    except (TypeError, ValueError):
        return False, "Invalid Metadata"
    if effective and effective > today:
        return False, "Not Yet Effective"
    if expiry and expiry < today:
        return False, "Expired"
    return True, None


def resolve_policy_metadata(
    document_id: str,
    documents: Optional[Iterable[Dict[str, Any]]] = None,
    today: Optional[date] = None,
) -> Tuple[str, str]:
    current_date = today or date.today()
    if documents is None:
        try:
            from config.database import get_knowledge_col
            documents = get_knowledge_col().find({"document_id": document_id})
        except Exception:
            return "Unknown", "Unavailable"

    matching = [
        dict(document)
        for document in documents
        if str(document.get("document_id", "")).strip().casefold() == document_id.strip().casefold()
    ]
    if not matching:
        return "Unknown", "Missing"

    active_current = []
    inactive = []
    for document in matching:
        status = str(document.get("status", "Unknown")).strip().title()
        valid_period, date_status = _within_effective_period(document, current_date)
        if status == "Active" and valid_period:
            active_current.append(document)
        else:
            document["_resolved_status"] = date_status or status
            inactive.append(document)

    if active_current:
        selected = max(active_current, key=_version_order)
        return str(selected.get("version") or "Unknown"), "Active"

    selected = max(inactive, key=_version_order)
    return str(selected.get("version") or "Unknown"), str(selected.get("_resolved_status") or "Unknown")
