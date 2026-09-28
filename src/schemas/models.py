from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import datetime

class EntityExtractionResult(BaseModel):
    order_id: Optional[str] = None
    transaction_id: Optional[str] = None
    product_name: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = "USD"
    incident_date: Optional[str] = None
    serial_number: Optional[str] = None
    location: Optional[str] = None
    tracking_number: Optional[str] = None

class ComplaintSubmission(BaseModel):
    complaint_id: Optional[str] = None
    customer_id: str = "CUST-1001"
    customer_name: str
    customer_email: str
    customer_phone: Optional[str] = None
    customer_type: str = "Standard"  # Standard, Premium, VIP, Corporate
    complaint_title: str
    complaint_description: str
    product_or_service: Optional[str] = None
    order_reference: Optional[str] = None
    transaction_reference: Optional[str] = None
    preferred_channel: str = "Web Form"  # Web Form, Email, Phone, Chat
    attachment_names: List[str] = Field(default_factory=list)
    previous_complaint_id: Optional[str] = None
    created_at: Optional[str] = None

class GenAIIntelligenceOutput(BaseModel):
    complaint_id: str
    primary_issue: str
    secondary_issues: List[str] = Field(default_factory=list)
    category: str
    subcategory: str
    sentiment: str  # Positive, Neutral, Negative, Strongly Negative
    urgency: str    # Low, Medium, High, Critical
    priority: str   # P0, P1, P2, P3
    detected_emotions: List[str] = Field(default_factory=list)
    extracted_entities: Dict[str, Any] = Field(default_factory=dict)
    recommended_department: str
    supporting_departments: List[str] = Field(default_factory=list)
    referenced_policy_id: Optional[str] = None
    referenced_policy_section: Optional[str] = None
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

class PythonGroundTruthResult(BaseModel):
    complaint_id: str
    expected_category: str
    expected_subcategory: str
    expected_department: str
    expected_supporting_department: Optional[str] = None
    expected_urgency: str
    expected_priority: str
    mandatory_escalation: bool
    escalation_tier: Optional[str] = None
    escalation_reason: Optional[str] = None
    applicable_policy_id: str
    applicable_policy_name: str
    policy_version: str
    policy_status: str  # Active, Superseded, Draft
    refund_eligible: bool
    replacement_eligible: bool
    compensation_allowed: bool
    max_compensation_limit: float = 0.0
    mandatory_resolution_steps: List[str] = Field(default_factory=list)
    prohibited_actions: List[str] = Field(default_factory=list)
    required_follow_up: bool
    missing_mandatory_fields: List[str] = Field(default_factory=list)
    rule_id_matched: str

class ComparisonResult(BaseModel):
    complaint_id: str
    category_match: bool
    subcategory_match: bool
    department_match: bool
    urgency_match: bool
    priority_match: bool
    escalation_match: bool
    policy_match: bool
    
    # Quantitative Scores
    mandatory_coverage_score: float = 100.0   # % of mandatory steps included
    source_traceability_score: float = 100.0  # % of claims backed by active docs
    consistency_score: float = 100.0          # Overall alignment index
    
    # Flags & Warnings
    unsupported_claims_flagged: List[str] = Field(default_factory=list)
    prohibited_actions_detected: List[str] = Field(default_factory=list)
    unauthorized_promise_detected: bool = False
    contradiction_detected: bool = False
    contradiction_details: Optional[str] = None
    prompt_injection_detected: bool = False
    is_duplicate: bool = False
    duplicate_of_id: Optional[str] = None
    
    # Verification Decision
    verification_status: str  # Verified, Verified with Warning, Contradiction Detected, Unsupported Requirement, Manual Review Required
    explanation_of_disagreement: Optional[str] = None
    requires_manual_review: bool = False

class AuditLogEntry(BaseModel):
    log_id: str
    complaint_id: str
    timestamp: str
    actor: str  # AI_Pipeline, Python_Engine, Agent, Reviewer, Admin
    action: str # Created, Analyzed, Validated, Approved, Modified, Reassigned, Escalated, Overridden, Closed
    details: Dict[str, Any]
    previous_state: Optional[Dict[str, Any]] = None
    new_state: Optional[Dict[str, Any]] = None
