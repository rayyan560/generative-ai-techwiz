import re
from typing import Dict, Any, List, Optional
from src.schemas.models import PythonGroundTruthResult
from src.complaint_rules.matrix import RuleMatrixManager
from src.escalation_rules.manager import EscalationManager
from src.routing_rules.router import DepartmentRouter
from src.knowledge_base.policy_versions import resolve_policy_metadata
from src.python_validation.classification import classify_complaint

class PythonGroundTruthPipeline:
    @staticmethod
    def validate_complaint(
        complaint_dict: Dict[str, Any],
        policy_documents: Optional[List[Dict[str, Any]]] = None,
    ) -> PythonGroundTruthResult:
        """
        Executes Pipeline 2: 100% Deterministic Python Ground-Truth Validation.
        DOES NOT USE ANY GENAI API.
        """
        complaint_id = complaint_dict.get("complaint_id", "CMP-00001")
        title = complaint_dict.get("complaint_title", "")
        desc = complaint_dict.get("complaint_description", "")
        full_text = f"{title} {desc}".lower()
        customer_type = complaint_dict.get("customer_type", "Standard")
        
        category, subcategory = classify_complaint(full_text)

        # 2. Match with Complaint Resolution Rule Matrix
        matched_rule = RuleMatrixManager.match_rule(category, subcategory, customer_type, full_text)
        
        # 3. Department Routing Validation
        primary_dept, supp_dept = DepartmentRouter.route_complaint(category, full_text)
        
        # 4. Mandatory Escalation Evaluation (32+ conditions)
        is_escalated, esc_tier, esc_reason, esc_id = EscalationManager.evaluate_escalation(complaint_dict)
        policy_id = matched_rule.get("policy_id", "POL-CMP-01")
        policy_version, policy_status = resolve_policy_metadata(policy_id, documents=policy_documents)
        tier_match = re.search(r"Tier\s+(\d+)", str(esc_tier or ""))
        escalation_level = int(tier_match.group(1)) if tier_match else 0
        expected_urgency = "Critical" if escalation_level >= 5 else "High" if is_escalated and escalation_level >= 3 else matched_rule.get("urgency", "Medium")
        expected_priority = "P0" if escalation_level >= 5 else "P1" if is_escalated and escalation_level >= 3 else matched_rule.get("priority", "P2")
        
        # 5. Missing Mandatory Fields Check
        missing_fields = []
        if not complaint_dict.get("order_reference") and category in ["Billing & Charges", "Delivery & Shipping", "Product Defect", "Refund Request"]:
            missing_fields.append("Order Reference Number")
        if not complaint_dict.get("customer_email") and not complaint_dict.get("customer_phone"):
            missing_fields.append("Contact Details (Email/Phone)")

        # 6. Build Deterministic Ground-Truth Result
        return PythonGroundTruthResult(
            complaint_id=complaint_id,
            expected_category=category,
            expected_subcategory=subcategory,
            expected_department=primary_dept,
            expected_supporting_department=supp_dept,
            expected_urgency=expected_urgency,
            expected_priority=expected_priority,
            mandatory_escalation=is_escalated or matched_rule.get("mandatory_escalation", False),
            escalation_tier=esc_tier,
            escalation_reason=esc_reason if is_escalated else None,
            applicable_policy_id=policy_id,
            applicable_policy_name=policy_id.replace("POL-", "Policy "),
            policy_version=policy_version,
            policy_status=policy_status,
            refund_eligible=matched_rule.get("refund_eligible", False),
            replacement_eligible=matched_rule.get("replacement_eligible", False),
            compensation_allowed=matched_rule.get("compensation_allowed", False),
            max_compensation_limit=float(matched_rule.get("max_compensation", 0.0)),
            mandatory_resolution_steps=matched_rule.get("mandatory_actions", []),
            prohibited_actions=matched_rule.get("prohibited_actions", []),
            required_follow_up=matched_rule.get("required_follow_up", True),
            missing_mandatory_fields=missing_fields,
            rule_id_matched=matched_rule.get("rule_id", "RUL-GEN-001")
        )

python_validation_pipeline = PythonGroundTruthPipeline()
