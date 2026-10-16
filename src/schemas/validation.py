from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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
    policy_status: str
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
    mandatory_coverage_score: Optional[float] = None
    source_traceability_score: Optional[float] = None
    consistency_score: Optional[float] = None
    unsupported_claims_flagged: List[str] = Field(default_factory=list)
    prohibited_actions_detected: List[str] = Field(default_factory=list)
    unauthorized_promise_detected: bool = False
    contradiction_detected: bool = False
    contradiction_details: Optional[str] = None
    prompt_injection_detected: bool = False
    is_duplicate: bool = False
    duplicate_of_id: Optional[str] = None
    verification_status: str
    explanation_of_disagreement: Optional[str] = None
    requires_manual_review: bool = False
