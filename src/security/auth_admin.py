from config.database import get_users_col
from src.security.auth_defaults import JUDGE_DEMO_USER


def update_user_role(user_id: str, new_role: str) -> bool:
    if user_id == JUDGE_DEMO_USER["user_id"]:
        return False
    result = get_users_col().update_one({"user_id": user_id}, {"$set": {"role": new_role}})
    return result.modified_count > 0
