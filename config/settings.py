import os
from pathlib import Path
from typing import List
from pydantic import BaseModel
from config.domain_settings import (
    CATEGORIES as COMPLAINT_CATEGORIES,
    DEPARTMENTS as SUPPORT_DEPARTMENTS,
    ESCALATION_LEVELS as ESCALATION_TIERS,
    PRIORITY_SLA_HOURS as PRIORITY_TARGETS,
    SUBCATEGORIES as CATEGORY_SUBCATEGORIES,
    URGENCY_LEVELS as COMPLAINT_URGENCY_LEVELS,
)

env_file = Path(__file__).resolve().parent.parent / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

class AppSettings(BaseModel):
    APP_NAME: str = "SupportNova - ResponseX Intelligence"
    ORG_NAME: str = "NovaTech Global Commerce & Electronics"
    ORG_DOMAIN: str = "E-commerce, Consumer Electronics & Digital Services"
    VERSION: str = "1.0.0"
    
    # Google OAuth 2.0 Credentials
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    BASE_URL: str = os.getenv("BASE_URL", "http://127.0.0.1:8000")
    DEMO_MODE: bool = os.getenv(
        "DEMO_MODE",
        "false" if os.getenv("RAILWAY_ENVIRONMENT_ID") or os.getenv("RENDER") else "true"
    ).lower() in ("true", "1", "yes")
    PUBLIC_DEMO_MODE: bool = os.getenv("PUBLIC_DEMO_MODE", "false").lower() in ("true", "1", "yes")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "").strip().lower()
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "")
    AGENT_EMAIL: str = os.getenv("AGENT_EMAIL", "").strip().lower()
    AGENT_PASSWORD: str = os.getenv("AGENT_PASSWORD", "")
    COOKIE_SECURE: bool = os.getenv(
        "COOKIE_SECURE",
        "true" if os.getenv("RAILWAY_ENVIRONMENT_ID") or os.getenv("RENDER") else "false"
    ).lower() in ("true", "1", "yes")
    
    # MongoDB Atlas Connection
    MONGODB_URI: str = os.getenv("MONGODB_URI", "").strip()
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "supportnova_db").strip()
    
    GEMINI_API_KEYS: List[str] = [k.strip() for k in os.getenv("GEMINI_API_KEYS", os.getenv("GOOGLE_GENAI_API_KEY", "")).split(",") if k.strip()]
    DEFAULT_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    
    DEPARTMENTS: List[str] = SUPPORT_DEPARTMENTS
    CATEGORIES: List[str] = COMPLAINT_CATEGORIES
    SUBCATEGORIES: dict = CATEGORY_SUBCATEGORIES
    URGENCY_LEVELS: List[str] = COMPLAINT_URGENCY_LEVELS
    PRIORITY_SLA_HOURS: dict = PRIORITY_TARGETS
    ESCALATION_LEVELS: List[str] = ESCALATION_TIERS

def validate_public_demo_settings(config: AppSettings) -> None:
    """Require public preview deployments to be isolated and provider-free."""
    if not config.PUBLIC_DEMO_MODE:
        return

    problems = []
    if config.DEMO_MODE:
        problems.append("DEMO_MODE must be false (local privileged seed accounts are not allowed).")
    if not config.DATABASE_NAME.startswith("supportnova_demo_"):
        problems.append("DATABASE_NAME must start with 'supportnova_demo_'.")
    if not config.MONGODB_URI:
        problems.append("MONGODB_URI must point to the isolated demo database account.")
    if config.GEMINI_API_KEYS:
        problems.append("Gemini API keys must not be configured for the public demo.")
    if config.GOOGLE_CLIENT_ID or config.GOOGLE_CLIENT_SECRET:
        problems.append("Google OAuth credentials must not be configured for the public demo.")
    if config.ADMIN_EMAIL or config.ADMIN_PASSWORD or config.AGENT_EMAIL or config.AGENT_PASSWORD:
        problems.append("Production admin/agent credentials must not be configured for the public demo.")
    if len(os.getenv("SESSION_SECRET_KEY", "")) < 32:
        problems.append("A unique SESSION_SECRET_KEY of at least 32 characters is required.")

    if problems:
        raise RuntimeError("Unsafe PUBLIC_DEMO_MODE configuration: " + " ".join(problems))


settings = AppSettings()
validate_public_demo_settings(settings)
