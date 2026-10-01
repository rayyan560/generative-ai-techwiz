import os
from pathlib import Path
from typing import List
from pydantic import BaseModel

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
    DATABASE_NAME: str = "supportnova_db"
    
    GEMINI_API_KEYS: List[str] = [k.strip() for k in os.getenv("GEMINI_API_KEYS", os.getenv("GOOGLE_GENAI_API_KEY", "")).split(",") if k.strip()]
    DEFAULT_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    
    # Departments (10 distinct enterprise departments as required by SRS)
    DEPARTMENTS: List[str] = [
        "Billing & Payments",
        "Logistics & Delivery",
        "Technical Support",
        "Returns & Replacements",
        "Warranty & Repairs",
        "Customer Relations",
        "Account Security & Privacy",
        "Product Quality & Safety",
        "Legal & Compliance",
        "Management Escalations"
    ]
    
    # 12 Primary Complaint Categories
    CATEGORIES: List[str] = [
        "Product Defect",
        "Billing & Charges",
        "Delivery & Shipping",
        "Refund Request",
        "Account Security",
        "Technical Support",
        "Service Quality",
        "Warranty Claim",
        "Data Privacy",
        "Safety Hazard",
        "Staff Conduct",
        "Order Cancellation"
    ]
    
    # 25+ Subcategories
    SUBCATEGORIES: dict = {
        "Product Defect": ["Dead on Arrival", "Physical Damage", "Missing Parts", "Malfunctioning Hardware", "Intermittent Failure"],
        "Billing & Charges": ["Double Charge", "Incorrect Amount", "Subscription Overcharge", "Unauthorized Charge", "Missing Invoice"],
        "Delivery & Shipping": ["Delayed Delivery", "Package Lost in Transit", "Wrong Item Delivered", "Damaged Packaging", "Failed Courier Attempt"],
        "Refund Request": ["Refund Not Processed", "Partial Refund Dispute", "Refund Mode Disagreement", "Cancelled Order Refund"],
        "Account Security": ["Suspicious Login", "Password Reset Failure", "Unauthorized Profile Change", "2FA Lockout"],
        "Technical Support": ["Software Crash", "Firmware Update Error", "Connectivity Issue", "Compatibility Problem"],
        "Service Quality": ["Rude Staff Interaction", "Unresolved Long-standing Issue", "Poor Installation Service", "Misleading Information"],
        "Warranty Claim": ["Claim Denied Dispute", "Extended Warranty Inquiry", "Repair Delay", "Service Center Refusal"],
        "Data Privacy": ["Unauthorized Marketing", "Data Deletion Request", "Data Breach Concern", "Third-party Sharing Dispute"],
        "Safety Hazard": ["Electrical Spark / Shock Hazard", "Battery Overheating / Swelling", "Sharp Edges / Physical Hazard", "Toxic Smell / Fumes"],
        "Staff Conduct": ["Agent Misbehavior", "Supervisor Refusal", "False Commitments", "Discrimination Complaint"],
        "Order Cancellation": ["Cancellation Denied", "Auto-Renewal Dispute", "Pre-order Cancellation", "Partial Order Cancellation"]
    }
    
    # Urgency Levels
    URGENCY_LEVELS: List[str] = ["Low", "Medium", "High", "Critical"]
    
    # Priority Levels & Target SLAs (in hours)
    PRIORITY_SLA_HOURS: dict = {
        "P0": {"name": "Critical", "response_hours": 1, "resolution_hours": 4, "badge_color": "danger"},
        "P1": {"name": "High", "response_hours": 4, "resolution_hours": 12, "badge_color": "warning"},
        "P2": {"name": "Medium", "response_hours": 12, "resolution_hours": 24, "badge_color": "primary"},
        "P3": {"name": "Low", "response_hours": 24, "resolution_hours": 72, "badge_color": "secondary"}
    }
    
    # Escalation Tiers
    ESCALATION_LEVELS: List[str] = [
        "Tier 1 - Standard Agent",
        "Tier 2 - Senior Specialist",
        "Tier 3 - Department Manager",
        "Tier 4 - Compliance & Legal Team",
        "Tier 5 - Executive Management Escalation"
    ]

settings = AppSettings()
