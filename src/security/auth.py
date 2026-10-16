from src.security.auth_admin import update_user_role
from src.security.auth_bootstrap import initialize_default_users
from src.security.auth_defaults import (
    DEFAULT_USERS,
    JUDGE_DEMO_USER,
    PUBLIC_DEMO_PORTALS,
    PUBLIC_DEMO_USERS,
    _is_valid_public_demo_user,
)
from src.security.auth_google_accounts import authenticate_google_user
from src.security.auth_lookup import authenticate_user, get_user_by_id, get_user_by_identifier
from src.security.auth_passwords import get_password_hash, verify_password
from src.security.auth_profile import generate_google_avatar, get_all_users, update_user_credentials
from src.security.auth_registration import register_user
from src.security.auth_sessions import (
    SECRET_KEY,
    SESSION_SECRET_KEY,
    create_session_token,
    get_current_user,
    verify_session_token,
)


class AuthManager:
    _init_users_if_empty = staticmethod(initialize_default_users)
    get_user_by_identifier = staticmethod(get_user_by_identifier)
    get_user_by_id = staticmethod(get_user_by_id)
    authenticate_user = staticmethod(authenticate_user)
    authenticate_google_user = staticmethod(authenticate_google_user)
    register_user = staticmethod(register_user)
    update_user_credentials = staticmethod(update_user_credentials)
    get_all_users = staticmethod(get_all_users)
    update_user_role = staticmethod(update_user_role)
    create_session_token = staticmethod(create_session_token)
    verify_session_token = staticmethod(verify_session_token)
    get_current_user = staticmethod(get_current_user)
