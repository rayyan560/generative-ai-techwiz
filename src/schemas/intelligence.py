from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GenAIIntelligenceOutput(BaseModel):
    complaint_id: str
    primary_issue: str
    secondary_issues: List[str] = Field(default_factory=list)
    category: str
    subcategory: str
    sentiment: str
    urgency: str
    priority: str
    detected_emotions: List[str] = Field(default_factory=list)
    extracted_entities: Dict[str, Any] = Field(default_factory=dict)
    recommended_department: str
    supporting_departments: List[str] = Field(default_factory=list)
    referenced_policy_id: Optional[str] = None
    referenced_policy_section: Optional[str] = None
    referenced_policy_version: str
    analysis_metadata: Dict[str, Any] = Field(default_factory=dict)
    resolution_steps: List[str] = Field(default_factory=list)
    escalation_required: bool = False
    escalation_tier: Optional[str] = None
    escalation_reason: Optional[str] = None
    customer_response: str
    response_type: str = "Apology & Investigation"
    response_tone: str = "Professional & Empathetic"
    internal_agent_guidance: List[str] = Field(default_factory=list)
    follow_up_required: bool = True
    follow_up_action: Optional[str] = None
    clarification_questions: List[str] = Field(default_factory=list)
    adversarial_warning: Optional[str] = None
