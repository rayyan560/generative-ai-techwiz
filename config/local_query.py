from typing import Any, Dict


def matches_document(item: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
    for key, expected in filter_dict.items():
        if key == "$or":
            if not isinstance(expected, list) or not any(matches_document(item, clause) for clause in expected):
                return False
            continue
        actual = item.get(key)
        if isinstance(expected, dict) and expected and all(str(operator).startswith("$") for operator in expected):
            for operator, value in expected.items():
                if operator == "$in" and actual not in value:
                    return False
                if operator == "$nin" and actual in value:
                    return False
                if operator == "$ne" and actual == value:
                    return False
                if operator == "$exists" and ((key in item) != bool(value)):
                    return False
                if operator not in {"$in", "$nin", "$ne", "$exists"}:
                    raise ValueError(f"Unsupported local query operator: {operator}")
        elif actual != expected:
            return False
    return True
