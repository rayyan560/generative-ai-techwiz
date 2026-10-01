import re
from typing import Dict, Any, List, Optional
from src.schemas.models import PythonGroundTruthResult
from src.complaint_rules.matrix import RuleMatrixManager
from src.escalation_rules.manager import EscalationManager
from src.routing_rules.router import DepartmentRouter

class PythonGroundTruthPipeline:
    @staticmethod
    def validate_complaint(complaint_dict: Dict[str, Any]) -> PythonGroundTruthResult:
        """
        Executes Pipeline 2: 100% Deterministic Python Ground-Truth Validation.
        DOES NOT USE ANY GENAI API.
        """
        complaint_id = complaint_dict.get("complaint_id", "CMP-00001")
        title = complaint_dict.get("complaint_title", "")
        desc = complaint_dict.get("complaint_description", "")
        full_text = f"{title} {desc}".lower()
        customer_type = complaint_dict.get("customer_type", "Standard")
        
        # 1. Deterministic Category & Subcategory Detection from keywords
        category = "Customer Relations"
        subcategory = "General Inquiry"
        
        if any(w in full_text for w in ["fire", "spark", "shock", "smoke", "swollen", "fume", "burn", "explosion"]):
            category = "Safety Hazard"
            subcategory = "Battery Overheating / Swelling" if "battery" in full_text or "swollen" in full_text else "Electrical Spark / Shock Hazard"
        elif any(w in full_text for w in ["hacked", "stolen", "unauthorized login", "data breach", "privacy", "gdpr", "compromised"]):
            category = "Account Security" if ("login" in full_text or "password" in full_text or "hacked" in full_text) else "Data Privacy"
            subcategory = "Suspicious Login" if category == "Account Security" else "Data Deletion Request"
        elif any(w in full_text for w in ["double charge", "charged twice", "overcharge", "unauthorized charge", "billing error", "subscription", "missing invoice", "invoice is missing"]):
            category = "Billing & Charges"
            if "twice" in full_text or "double" in full_text:
                subcategory = "Double Charge"
            elif "subscription" in full_text or "renewal" in full_text:
                subcategory = "Subscription Overcharge"
            elif "invoice" in full_text:
                subcategory = "Missing Invoice"
            else:
                subcategory = "Incorrect Amount"
        elif any(w in full_text for w in ["refund", "money back", "return my money", "where is my refund"]):
            category = "Refund Request"
            subcategory = "Refund Not Processed"
        elif any(w in full_text for w in ["late delivery", "delayed delivery", "lost package", "package not arrived", "tracking stuck", "wrong item", "wrong product", "incorrect item"]):
            category = "Delivery & Shipping"
            if any(w in full_text for w in ["wrong item", "wrong product", "incorrect item"]):
                subcategory = "Wrong Item Delivered"
            elif "delay" in full_text or "late" in full_text:
                subcategory = "Delayed Delivery"
            else:
                subcategory = "Package Lost in Transit"
        elif any(w in full_text for w in ["dead on arrival", "doa", "broken", "cracked screen", "defect", "damage", "malfunction", "intermittent", "shuts down"]):
            category = "Product Defect"
            if "doa" in full_text or "dead" in full_text:
                subcategory = "Dead on Arrival"
            elif "intermittent" in full_text or "randomly shuts down" in full_text:
                subcategory = "Intermittent Failure"
            else:
                subcategory = "Physical Damage"
        elif any(w in full_text for w in ["rude agent", "unprofessional staff", "hung up on me", "harassed", "insulted"]):
            category = "Staff Conduct"
            subcategory = "Agent Misbehavior"
        elif any(w in full_text for w in ["poor installation", "misleading information", "service quality", "installation service"]):
            category = "Service Quality"
            subcategory = "Poor Installation Service" if "installation" in full_text else "Misleading Information"
        elif any(w in full_text for w in ["software crash", "firmware update", "wifi", "wi-fi", "connectivity issue", "bluetooth"]):
            category = "Technical Support"
            subcategory = "Connectivity Issue" if any(w in full_text for w in ["wifi", "wi-fi", "connectivity", "bluetooth"]) else "Software Crash"
        elif any(w in full_text for w in ["warranty", "repair", "service center"]):
            category = "Warranty Claim"
            subcategory = "Repair Delay"
        elif any(w in full_text for w in ["cancel order", "cancellation denied", "stop shipment"]):
            category = "Order Cancellation"
            subcategory = "Cancellation Denied"

        # 2. Match with Complaint Resolution Rule Matrix
        matched_rule = RuleMatrixManager.match_rule(category, subcategory, customer_type, full_text)
        
        # 3. Department Routing Validation
        primary_dept, supp_dept = DepartmentRouter.route_complaint(category, full_text)
        
        # 4. Mandatory Escalation Evaluation (32+ conditions)
        is_escalated, esc_tier, esc_reason, esc_id = EscalationManager.evaluate_escalation(complaint_dict)
        
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
            expected_urgency="Critical" if is_escalated and "Tier 5" in esc_tier else matched_rule.get("urgency", "Medium"),
            expected_priority="P0" if is_escalated and ("Tier 5" in esc_tier or "Tier 4" in esc_tier) else matched_rule.get("priority", "P2"),
            mandatory_escalation=is_escalated or matched_rule.get("mandatory_escalation", False),
            escalation_tier=esc_tier,
            escalation_reason=esc_reason if is_escalated else None,
            applicable_policy_id=matched_rule.get("policy_id", "POL-CMP-01"),
            applicable_policy_name=matched_rule.get("policy_id", "").replace("POL-", "Policy "),
            policy_version="v2.0",
            policy_status="Active",
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
