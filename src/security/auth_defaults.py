from typing import Any, Dict

from config.settings import settings


DEFAULT_USERS = [
    {
        "user_id": "USR-ADMIN-001",
        "username": "admin",
        "email": "admin@supportnova.io",
        "password": "admin123",
        "role": "admin",
        "display_name": "Executive Director",
        "designation": "Grievance Operations Director & CEO",
        "avatar": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=160&auto=format&fit=crop&q=80",
        "auth_provider": "local",
        "phone": "+1 800 555 0100",
        "created_at": "2026-01-01 00:00:00",
    },
    {
        "user_id": "USR-AGENT-002",
        "username": "agent",
        "email": "agent@supportnova.io",
        "password": "agent123",
        "role": "agent",
        "display_name": "Marcus Chen",
        "designation": "Lead Triage & Hardware Forensic Specialist",
        "avatar": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=160&auto=format&fit=crop&q=80",
        "auth_provider": "local",
        "phone": "+1 800 555 0142",
        "created_at": "2026-01-02 00:00:00",
    },
    {
        "user_id": "USR-WARRANTY-003",
        "username": "warranty_manager",
        "email": "warranty@supportnova.io",
        "password": "warranty123",
        "role": "warranty_manager",
        "display_name": "Sarah Jenkins",
        "designation": "Senior Warranty, Escrow & Refund Manager",
        "avatar": "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=160&auto=format&fit=crop&q=80",
        "auth_provider": "local",
        "phone": "+1 800 555 0199",
        "created_at": "2026-01-03 00:00:00",
    },
]

JUDGE_DEMO_USER = {
    "user_id": "USR-JUDGE-DEMO-001",
    "username": "judge",
    "email": "judge@supportnova.demo",
    "password": "judge2026",
    "role": "judge",
    "display_name": "Competition Judge",
    "designation": "Read-only project review",
    "auth_provider": "local",
    "phone": "",
    "created_at": "2026-10-01 00:00:00",
}

PUBLIC_DEMO_USERS = [
    {
        "user_id": "USR-PUBLIC-DEMO-ADMIN",
        "username": "admin",
        "email": "demo_admin@supportnova.demo",
        "password": "admin123",
        "role": "admin",
        "demo_portal": "admin",
        "display_name": "Competition Admin",
        "designation": "Competition demonstration account",
        "auth_provider": "local",
        "phone": "",
        "created_at": "2026-10-02 00:00:00",
    },
    {
        "user_id": "USR-PUBLIC-DEMO-AGENT",
        "username": "agent",
        "email": "demo_agent@supportnova.demo",
        "password": "agent123",
        "role": "agent",
        "demo_portal": "agent",
        "display_name": "Competition Agent",
        "designation": "Competition demonstration account",
        "auth_provider": "local",
        "phone": "",
        "created_at": "2026-10-02 00:00:00",
    },
]

PUBLIC_DEMO_PORTALS = {
    user["user_id"]: {"portal": user["demo_portal"], "role": user["role"]}
    for user in PUBLIC_DEMO_USERS
}


def _is_valid_public_demo_user(user: Dict[str, Any]) -> bool:
    expected = PUBLIC_DEMO_PORTALS.get(user.get("user_id"))
    return bool(
        settings.PUBLIC_DEMO_MODE
        and expected
        and user.get("role") == expected["role"]
        and user.get("demo_portal") == expected["portal"]
    )
