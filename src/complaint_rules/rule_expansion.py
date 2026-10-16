from typing import Any, Dict, List


def build_full_rule_matrix(base_rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rules = list(base_rules)
    existing_ids = {rule["rule_id"] for rule in rules}
    categories_subcategories = {
        "Product Defect": ["Dead on Arrival", "Physical Damage", "Missing Parts", "Malfunctioning Hardware", "Intermittent Failure"],
        "Billing & Charges": ["Double Charge", "Incorrect Amount", "Subscription Overcharge", "Unauthorized Charge", "Missing Invoice"],
        "Delivery & Shipping": ["Delayed Delivery", "Package Lost in Transit", "Wrong Item Delivered", "Damaged Packaging", "Failed Courier Attempt"],
        "Refund Request": ["Refund Not Processed", "Partial Refund Dispute", "Refund Mode Disagreement", "Cancelled Order Refund"],
        "Account Security": ["Suspicious Login", "Password Reset Failure", "Unauthorized Profile Change", "2FA Lockout", "Prompt Injection Attempt"],
        "Technical Support": ["Software Crash", "Firmware Update Error", "Connectivity Issue", "Compatibility Problem"],
        "Service Quality": ["Rude Staff Interaction", "Unresolved Long-standing Issue", "Poor Installation Service", "Misleading Information"],
        "Warranty Claim": ["Claim Denied Dispute", "Extended Warranty Inquiry", "Repair Delay", "Service Center Refusal"],
        "Data Privacy": ["Unauthorized Marketing", "Data Deletion Request", "Data Breach Concern", "Third-party Sharing Dispute"],
        "Safety Hazard": ["Electrical Spark / Shock Hazard", "Battery Overheating / Swelling", "Sharp Edges / Physical Hazard", "Toxic Smell / Fumes"],
        "Staff Conduct": ["Agent Misbehavior", "Supervisor Refusal", "False Commitments", "Discrimination Complaint"],
        "Order Cancellation": ["Cancellation Denied", "Auto-Renewal Dispute", "Pre-order Cancellation", "Partial Order Cancellation"],
    }
    departments = {
        "Product Defect": "Returns & Replacements",
        "Billing & Charges": "Billing & Payments",
        "Delivery & Shipping": "Logistics & Delivery",
        "Refund Request": "Billing & Payments",
        "Account Security": "Account Security & Privacy",
        "Technical Support": "Technical Support",
        "Service Quality": "Customer Relations",
        "Warranty Claim": "Warranty & Repairs",
        "Data Privacy": "Account Security & Privacy",
        "Safety Hazard": "Product Quality & Safety",
        "Staff Conduct": "Customer Relations",
        "Order Cancellation": "Returns & Replacements",
    }
    counter = len(rules) + 1
    for category, subcategories in categories_subcategories.items():
        for subcategory in subcategories:
            for variant in ("Standard", "VIP Customer", "Repeat Complaint"):
                rule_id = f"RUL-{category[:3].upper()}-{counter:03d}"
                if rule_id in existing_ids:
                    continue
                safety = category == "Safety Hazard"
                security = category == "Account Security" or "Unauthorized" in subcategory
                vip = variant == "VIP Customer"
                repeat = variant == "Repeat Complaint"
                urgency = "Critical" if safety else "High" if security or vip or repeat else "Medium"
                priority = "P0" if safety else "P1" if security or vip or repeat else "P2"
                escalation = safety or security or (repeat and priority == "P1")
                tier = "Tier 5 - Executive Management Escalation" if safety else "Tier 4 - Compliance & Legal Team" if security else "Tier 3 - Department Manager" if repeat else "Tier 1 - Standard Agent"
                policy_id = _policy_for(category, subcategory)
                department = departments.get(category, "Customer Relations")
                rules.append({
                    "rule_id": rule_id,
                    "category": category,
                    "subcategory": subcategory,
                    "customer_tier_condition": variant,
                    "keywords": [subcategory.lower(), category.lower(), variant.lower()],
                    "department": department,
                    "supporting_department": "Customer Relations" if department != "Customer Relations" else "Management Escalations",
                    "urgency": urgency,
                    "priority": priority,
                    "policy_id": policy_id,
                    "policy_section": "1.0",
                    "mandatory_escalation": escalation,
                    "escalation_tier": tier,
                    "refund_eligible": category in ["Refund Request", "Billing & Charges", "Safety Hazard", "Product Defect"],
                    "replacement_eligible": category in ["Product Defect", "Warranty Claim", "Delivery & Shipping", "Safety Hazard"],
                    "compensation_allowed": category in ["Delivery & Shipping", "Service Quality", "Staff Conduct", "Safety Hazard"],
                    "max_compensation": 50.0 if vip else 100.0 if safety else 20.0,
                    "mandatory_actions": [f"Log ticket under {category} workflow", "Verify customer records and order reference", f"Execute {department} standard protocol"],
                    "prohibited_actions": ["Do not promise unverified refunds or timeline commitments", "Do not ignore safety disclosures"],
                    "required_follow_up": True,
                    "follow_up_days": 1 if urgency in ["Critical", "High"] else 3,
                })
                existing_ids.add(rule_id)
                counter += 1
    return rules


def _policy_for(category: str, subcategory: str) -> str:
    if category == "Product Defect":
        return "POL-DOA-16" if subcategory == "Dead on Arrival" else "POL-WAR-07" if subcategory in ["Malfunctioning Hardware", "Intermittent Failure"] else "POL-REP-03"
    return {
        "Technical Support": "POL-TEC-12",
        "Service Quality": "POL-CON-10",
        "Refund Request": "POL-REF-02",
        "Delivery & Shipping": "POL-DEL-04",
        "Safety Hazard": "POL-SAF-05",
        "Billing & Charges": "POL-BIL-06",
        "Warranty Claim": "POL-WAR-07",
        "Account Security": "POL-SEC-08",
        "Data Privacy": "POL-PRV-09",
        "Staff Conduct": "POL-CON-10",
        "Order Cancellation": "POL-CAN-11",
    }.get(category, f"POL-{category[:3].upper()}-01")
