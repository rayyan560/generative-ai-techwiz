from typing import Any, Dict, Optional

from pydantic import BaseModel


class AuditLogEntry(BaseModel):
    log_id: str
    complaint_id: str
    timestamp: str
    actor: str
    action: str
    details: Dict[str, Any]
    previous_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None
