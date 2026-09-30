import os
import json
from typing import List, Dict, Any, Optional

# 105 Comprehensive Complaint Resolution Rules Matrix for NovaTech Global
RULES_MATRIX: List[Dict[str, Any]] = [
    # -------------------------------------------------------------
    # 1. Product Defect (Rules 1 - 12)
    # -------------------------------------------------------------
    {
        "rule_id": "RUL-DEF-001",
        "category": "Product Defect",
        "subcategory": "Dead on Arrival",
        "keywords": ["dead on arrival", "doa", "does not turn on", "not powering on", "won't boot"],
        "department": "Returns & Replacements",
        "supporting_department": "Technical Support",
        "urgency": "High",
        "priority": "P1",
        "policy_id": "POL-DOA-16",
        "policy_section": "1.0",
        "mandatory_escalation": False,
        "escalation_tier": "Tier 1 - Standard Agent",
        "refund_eligible": True,
        "replacement_eligible": True,
        "compensation_allowed": True,
        "max_compensation": 15.0,
        "mandatory_actions": ["Request device serial number", "Verify purchase date within 7 days", "Issue priority prepaid return label", "Dispatch instant replacement upon label scan"],
        "prohibited_actions": ["Do not force customer through elongated repair cycle", "Do not charge return shipping fee"],
        "required_follow_up": True,
        "follow_up_days": 2
    },
    {
        "rule_id": "RUL-DEF-002",
        "category": "Product Defect",
        "subcategory": "Physical Damage",
        "keywords": ["cracked screen", "shattered glass", "dented casing", "broken hinge", "cosmetic damage out of box"],
        "department": "Returns & Replacements",
        "supporting_department": "Logistics & Delivery",
        "urgency": "High",
        "priority": "P1",
        "policy_id": "POL-REP-03",
        "policy_section": "1.0",
        "mandatory_escalation": False,
        "escalation_tier": "Tier 1 - Standard Agent",
        "refund_eligible": True,
        "replacement_eligible": True,
        "compensation_allowed": False,
        "max_compensation": 0.0,
        "mandatory_actions": ["Request photographic evidence of damaged device and outer box", "Validate damage reported within 48h of delivery", "Arrange carrier damage inspection if needed"],
        "prohibited_actions": ["Do not accuse customer of improper handling before photo review"],
        "required_follow_up": True,
        "follow_up_days": 3
    },
    {
        "rule_id": "RUL-DEF-003",
        "category": "Product Defect",
        "subcategory": "Missing Parts",
        "keywords": ["missing accessories", "no power adapter", "cable missing", "parts omitted", "missing screws"],
        "department": "Returns & Replacements",
        "supporting_department": "Logistics & Delivery",
        "urgency": "Medium",
        "priority": "P2",
        "policy_id": "POL-REP-03",
        "policy_section": "2.0",
        "mandatory_escalation": False,
        "escalation_tier": "Tier 1 - Standard Agent",
        "refund_eligible": False,
        "replacement_eligible": True,
        "compensation_allowed": True,
        "max_compensation": 10.0,
        "mandatory_actions": ["Identify missing component SKU", "Initiate expedited parts fulfillment", "Provide tracking for missing parts"],
        "prohibited_actions": ["Do not require return of whole product for a missing cable"],
        "required_follow_up": True,
        "follow_up_days": 2
    },
    {
        "rule_id": "RUL-DEF-004",
        "category": "Product Defect",
        "subcategory": "Malfunctioning Hardware",
        "keywords": ["screen flickering", "speaker distorted", "button stuck", "usb port loose", "camera blurry"],
        "department": "Technical Support",
        "supporting_department": "Warranty & Repairs",
        "urgency": "Medium",
        "priority": "P2",
        "policy_id": "POL-WAR-07",
        "policy_section": "1.0",
        "mandatory_escalation": False,
        "escalation_tier": "Tier 1 - Standard Agent",
        "refund_eligible": False,
        "replacement_eligible": True,
        "compensation_allowed": False,
        "max_compensation": 0.0,
        "mandatory_actions": ["Provide standard Level 1 diagnostic steps", "Verify hardware warranty status", "Create repair service authorization if diagnostics fail"],
        "prohibited_actions": ["Do not issue RMA without diagnostic verification"],
        "required_follow_up": True,
        "follow_up_days": 4
    },
    {
        "rule_id": "RUL-DEF-005",
        "category": "Product Defect",
        "subcategory": "Intermittent Failure",
        "keywords": ["random reboot", "freezes intermittently", "disconnects randomly", "unstable performance"],
        "department": "Technical Support",
        "supporting_department": "Warranty & Repairs",
        "urgency": "Medium",
        "priority": "P2",
        "policy_id": "POL-TEC-12",
        "policy_section": "1.0",
        "mandatory_escalation": False,
        "escalation_tier": "Tier 2 - Senior Specialist",
        "refund_eligible": False,
        "replacement_eligible": True,
        "compensation_allowed": False,
        "max_compensation": 0.0,
        "mandatory_actions": ["Collect error logs or crash dumps", "Verify latest firmware installed", "Offer remote diagnostic session"],
        "prohibited_actions": ["Do not prematurely blame customer software without logs"],
        "required_follow_up": True,
        "follow_up_days": 3
    },
    # -------------------------------------------------------------
    # 2. Safety Hazard (Rules 6 - 15) - High Criticality
    # -------------------------------------------------------------
    {
        "rule_id": "RUL-SAF-006",
        "category": "Safety Hazard",
        "subcategory": "Battery Overheating / Swelling",
        "keywords": ["battery swollen", "battery bulge", "device expanding", "excessive heat burning", "battery puffing"],
        "department": "Product Quality & Safety",
        "supporting_department": "Management Escalations",
        "urgency": "Critical",
        "priority": "P0",
        "policy_id": "POL-SAF-05",
        "policy_section": "1.0",
        "mandatory_escalation": True,
        "escalation_tier": "Tier 5 - Executive Management Escalation",
        "refund_eligible": True,
        "replacement_eligible": True,
        "compensation_allowed": True,
        "max_compensation": 100.0,
        "mandatory_actions": ["Instruct customer immediately to discontinue usage and place device in fireproof container", "Notify Safety Compliance Officer within 30 mins", "Dispatch hazmat return kit"],
        "prohibited_actions": ["DO NOT ask customer to ship swollen battery via standard postal mail", "Do not downplay the danger"],
        "required_follow_up": True,
        "follow_up_days": 1
    },
    {
        "rule_id": "RUL-SAF-007",
        "category": "Safety Hazard",
        "subcategory": "Electrical Spark / Shock Hazard",
        "keywords": ["electric shock", "sparking charger", "smoke from outlet", "fire hazard", "burnt wall plug"],
        "department": "Product Quality & Safety",
        "supporting_department": "Legal & Compliance",
        "urgency": "Critical",
        "priority": "P0",
        "policy_id": "POL-SAF-05",
        "policy_section": "2.0",
        "mandatory_escalation": True,
        "escalation_tier": "Tier 5 - Executive Management Escalation",
        "refund_eligible": True,
        "replacement_eligible": True,
        "compensation_allowed": True,
        "max_compensation": 100.0,
        "mandatory_actions": ["Instruct customer to unplug circuit breaker safely", "Escalate to Senior Safety Directorate", "Quarantine inventory of matching batch number"],
        "prohibited_actions": ["DO NOT offer casual advice to re-plug the device", "Never discuss company liability in writing"],
        "required_follow_up": True,
        "follow_up_days": 1
    },
    {
        "rule_id": "RUL-SAF-008",
        "category": "Safety Hazard",
        "subcategory": "Toxic Smell / Fumes",
        "keywords": ["burning plastic smell", "chemical fume", "toxic odor", "dizziness from smell", "melting plastic"],
        "department": "Product Quality & Safety",
        "supporting_department": "Warranty & Repairs",
        "urgency": "Critical",
        "priority": "P0",
        "policy_id": "POL-SAF-05",
        "policy_section": "1.0",
        "mandatory_escalation": True,
        "escalation_tier": "Tier 4 - Compliance & Legal Team",
        "refund_eligible": True,
        "replacement_eligible": True,
        "compensation_allowed": True,
        "max_compensation": 50.0,
        "mandatory_actions": ["Advise ventilating room immediately", "Collect photos of melted components", "Log incident in Corporate Safety Registry"],
        "prohibited_actions": ["Do not advise customer to keep inhaling or testing"],
        "required_follow_up": True,
        "follow_up_days": 1
    },
    # -------------------------------------------------------------
    # 3. Billing & Charges (Rules 9 - 22)
    # -------------------------------------------------------------
    {
        "rule_id": "RUL-BIL-009",
        "category": "Billing & Charges",
        "subcategory": "Double Charge",
        "keywords": ["charged twice", "double charge", "duplicate deduction", "two charges on credit card", "debited two times"],
        "department": "Billing & Payments",
        "supporting_department": "Customer Relations",
        "urgency": "High",
        "priority": "P1",
        "policy_id": "POL-BIL-06",
        "policy_section": "1.0",
        "mandatory_escalation": False,
        "escalation_tier": "Tier 1 - Standard Agent",
        "refund_eligible": True,
        "replacement_eligible": False,
        "compensation_allowed": True,
        "max_compensation": 15.0,
        "mandatory_actions": ["Check payment gateway transaction logs for duplicate authorization", "Void secondary duplicate hold immediately", "Provide ARN (Acquirer Reference Number)"],
        "prohibited_actions": ["Do not ask customer to wait more than 48 hours for billing audit"],
        "required_follow_up": True,
        "follow_up_days": 2
    },
    {
        "rule_id": "RUL-BIL-010",
        "category": "Billing & Charges",
        "subcategory": "Unauthorized Charge",
        "keywords": ["unauthorized charge", "fraudulent card swipe", "i did not purchase this", "stolen card used"],
        "department": "Account Security & Privacy",
        "supporting_department": "Billing & Payments",
        "urgency": "Critical",
        "priority": "P1",
        "policy_id": "POL-BIL-06",
        "policy_section": "2.0",
        "mandatory_escalation": True,
        "escalation_tier": "Tier 3 - Department Manager",
        "refund_eligible": True,
        "replacement_eligible": False,
        "compensation_allowed": False,
        "max_compensation": 0.0,
        "mandatory_actions": ["Halt any pending fulfillment tied to card", "Temporarily suspend account purchasing ability", "Initiate fraud verification workflow"],
        "prohibited_actions": ["Do not disclose full credit card numbers in ticket replies"],
        "required_follow_up": True,
        "follow_up_days": 1
    },
    {
        "rule_id": "RUL-BIL-011",
        "category": "Billing & Charges",
        "subcategory": "Subscription Overcharge",
        "keywords": ["subscription fee incorrect", "charged after cancelling subscription", "annual renewal wrong amount"],
        "department": "Billing & Payments",
        "supporting_department": "Customer Relations",
        "urgency": "Medium",
        "priority": "P2",
        "policy_id": "POL-SUB-17",
        "policy_section": "1.0",
        "mandatory_escalation": False,
        "escalation_tier": "Tier 1 - Standard Agent",
        "refund_eligible": True,
        "replacement_eligible": False,
        "compensation_allowed": True,
        "max_compensation": 10.0,
        "mandatory_actions": ["Audit subscription renewal timestamps", "Cancel recurring schedule if requested", "Credit back unauthorized overage"],
        "prohibited_actions": ["Do not auto-renew without customer consent"],
        "required_follow_up": True,
        "follow_up_days": 3
    },
    {
        "rule_id": "RUL-BIL-012",
        "category": "Billing & Charges",
        "subcategory": "Missing Invoice",
        "keywords": ["need tax invoice", "receipt missing", "gst invoice required", "vat bill not provided"],
        "department": "Billing & Payments",
        "supporting_department": "Customer Relations",
        "urgency": "Low",
        "priority": "P3",
        "policy_id": "POL-BIL-06",
        "policy_section": "1.0",
        "mandatory_escalation": False,
        "escalation_tier": "Tier 1 - Standard Agent",
        "refund_eligible": False,
        "replacement_eligible": False,
        "compensation_allowed": False,
        "max_compensation": 0.0,
        "mandatory_actions": ["Regenerate official PDF tax invoice", "Email invoice to verified account address"],
        "prohibited_actions": ["Do not modify billing legal name without verification"],
        "required_follow_up": False,
        "follow_up_days": 0
    },
    # -------------------------------------------------------------
    # 4. Delivery & Shipping (Rules 13 - 26)
    # -------------------------------------------------------------
    {
        "rule_id": "RUL-DEL-013",
        "category": "Delivery & Shipping",
        "subcategory": "Delayed Delivery",
        "keywords": ["late delivery", "package delayed", "tracking stuck in transit", "past delivery date", "estimated date passed"],
        "department": "Logistics & Delivery",
        "supporting_department": "Customer Relations",
        "urgency": "Medium",
        "priority": "P2",
        "policy_id": "POL-DEL-04",
        "policy_section": "1.0",
        "mandatory_escalation": False,
        "escalation_tier": "Tier 1 - Standard Agent",
        "refund_eligible": False,
        "replacement_eligible": False,
        "compensation_allowed": True,
        "max_compensation": 10.0,
        "mandatory_actions": ["Query carrier API for latest scan checkpoint", "Contact courier depot", "Provide updated expected delivery window"],
        "prohibited_actions": ["Do not promise delivery within 1 hour unless verified by courier"],
        "required_follow_up": True,
        "follow_up_days": 2
    },
    {
        "rule_id": "RUL-DEL-014",
        "category": "Delivery & Shipping",
        "subcategory": "Package Lost in Transit",
        "keywords": ["lost package", "tracking has not moved in week", "carrier lost my box", "missing shipment"],
        "department": "Logistics & Delivery",
        "supporting_department": "Returns & Replacements",
        "urgency": "High",
        "priority": "P1",
        "policy_id": "POL-DEL-04",
        "policy_section": "2.0",
        "mandatory_escalation": False,
        "escalation_tier": "Tier 2 - Senior Specialist",
        "refund_eligible": True,
        "replacement_eligible": True,
        "compensation_allowed": True,
        "max_compensation": 25.0,
        "mandatory_actions": ["Confirm no carrier movement for >5 business days", "File official carrier loss claim", "Offer immediate reshipment or full refund"],
        "prohibited_actions": ["Do not make customer wait for carrier insurance payout"],
        "required_follow_up": True,
        "follow_up_days": 2
    },
    {
        "rule_id": "RUL-DEL-015",
        "category": "Delivery & Shipping",
        "subcategory": "Wrong Item Delivered",
        "keywords": ["wrong item received", "different product in box", "received someone else's order", "incorrect model"],
        "department": "Returns & Replacements",
        "supporting_department": "Logistics & Delivery",
        "urgency": "High",
        "priority": "P1",
        "policy_id": "POL-REP-03",
        "policy_section": "1.0",
        "mandatory_escalation": False,
        "escalation_tier": "Tier 1 - Standard Agent",
        "refund_eligible": True,
        "replacement_eligible": True,
        "compensation_allowed": True,
        "max_compensation": 15.0,
        "mandatory_actions": ["Request photo of wrong item packing slip and SKU", "Issue prepaid pickup for erroneous item", "Dispatch correct item with priority shipping"],
        "prohibited_actions": ["Do not make customer pay to return warehouse error"],
        "required_follow_up": True,
        "follow_up_days": 2
    },
    # -------------------------------------------------------------
    # 5. Refund Request (Rules 16 - 28)
    # -------------------------------------------------------------
    {
        "rule_id": "RUL-REF-016",
        "category": "Refund Request",
        "subcategory": "Refund Not Processed",
        "keywords": ["where is my refund", "refund not received", "returned item but no money", "refund delay"],
        "department": "Billing & Payments",
        "supporting_department": "Returns & Replacements",
        "urgency": "High",
        "priority": "P1",
        "policy_id": "POL-REF-02",
        "policy_section": "3.0",
        "mandatory_escalation": False,
        "escalation_tier": "Tier 1 - Standard Agent",
        "refund_eligible": True,
        "replacement_eligible": False,
        "compensation_allowed": True,
        "max_compensation": 15.0,
        "mandatory_actions": ["Check warehouse return reception log", "Verify payment gateway refund status", "If stuck in pending, trigger manual re-credit"],
        "prohibited_actions": ["Do not promise instant 1-hour bank deposit (standard bank clearance is 3-5 days)"],
        "required_follow_up": True,
        "follow_up_days": 2
    },
    {
        "rule_id": "RUL-REF-017",
        "category": "Refund Request",
        "subcategory": "Partial Refund Dispute",
        "keywords": ["only partial refund given", "restocking fee deducted unfairly", "missing full refund amount"],
        "department": "Billing & Payments",
        "supporting_department": "Customer Relations",
        "urgency": "Medium",
        "priority": "P2",
        "policy_id": "POL-REF-02",
        "policy_section": "2.0",
        "mandatory_escalation": False,
        "escalation_tier": "Tier 2 - Senior Specialist",
        "refund_eligible": True,
        "replacement_eligible": False,
        "compensation_allowed": True,
        "max_compensation": 25.0,
        "mandatory_actions": ["Review deduction breakdown", "If deduction was error on defective item, refund difference"],
        "prohibited_actions": ["Do not waive fees on damaged non-defective buyer remorse without supervisor sign-off"],
        "required_follow_up": True,
        "follow_up_days": 3
    },
    # -------------------------------------------------------------
    # 6. Account Security & Data Privacy (Rules 18 - 32)
    # -------------------------------------------------------------
    {
        "rule_id": "RUL-SEC-018",
        "category": "Account Security",
        "subcategory": "Suspicious Login",
        "keywords": ["unrecognized login", "account hacked", "login from unknown country", "password changed without my knowledge"],
        "department": "Account Security & Privacy",
        "supporting_department": "Management Escalations",
        "urgency": "Critical",
        "priority": "P0",
        "policy_id": "POL-SEC-08",
        "policy_section": "1.0",
        "mandatory_escalation": True,
        "escalation_tier": "Tier 4 - Compliance & Legal Team",
        "refund_eligible": False,
        "replacement_eligible": False,
        "compensation_allowed": False,
        "max_compensation": 0.0,
        "mandatory_actions": ["Terminate all active JWT/browser sessions immediately", "Freeze linked payment methods", "Initiate secure identity challenge"],
        "prohibited_actions": ["DO NOT send password resets to unverified third-party emails"],
        "required_follow_up": True,
        "follow_up_days": 1
    },
    {
        "rule_id": "RUL-PRV-019",
        "category": "Data Privacy",
        "subcategory": "Data Deletion Request",
        "keywords": ["gdpr right to be forgotten", "delete my personal data", "erase my account permanently", "ccpa delete request"],
        "department": "Account Security & Privacy",
        "supporting_department": "Legal & Compliance",
        "urgency": "Medium",
        "priority": "P2",
        "policy_id": "POL-PRV-09",
        "policy_section": "1.0",
        "mandatory_escalation": False,
        "escalation_tier": "Tier 3 - Department Manager",
        "refund_eligible": False,
        "replacement_eligible": False,
        "compensation_allowed": False,
        "max_compensation": 0.0,
        "mandatory_actions": ["Verify identity of data subject", "Submit ticket to Data Privacy Officer", "Set 30-day purge SLA"],
        "prohibited_actions": ["Do not delete ongoing tax/fraud audit records"],
        "required_follow_up": True,
        "follow_up_days": 14
    },
    # -------------------------------------------------------------
    # 7. Staff Conduct & Customer Relations (Rules 20 - 35)
    # -------------------------------------------------------------
    {
        "rule_id": "RUL-CON-020",
        "category": "Staff Conduct",
        "subcategory": "Agent Misbehavior",
        "keywords": ["rude agent", "support agent hung up on me", "insulted by representative", "swore at me", "disrespectful agent"],
        "department": "Customer Relations",
        "supporting_department": "Management Escalations",
        "urgency": "High",
        "priority": "P1",
        "policy_id": "POL-CON-10",
        "policy_section": "2.0",
        "mandatory_escalation": True,
        "escalation_tier": "Tier 3 - Department Manager",
        "refund_eligible": False,
        "replacement_eligible": False,
        "compensation_allowed": True,
        "max_compensation": 25.0,
        "mandatory_actions": ["Pull call recordings and chat transcript", "Escalate to QA Supervisor", "Issue executive apology letter to customer"],
        "prohibited_actions": ["Do not justify abusive agent behavior to customer"],
        "required_follow_up": True,
        "follow_up_days": 1
    },
    # -------------------------------------------------------------
    # 8. Legal Threats & Escalations (Rules 21 - 45)
    # -------------------------------------------------------------
    {
        "rule_id": "RUL-LEG-021",
        "category": "Service Quality",
        "subcategory": "Unresolved Long-standing Issue",
        "keywords": ["attorney", "lawsuit", "legal action", "calling my lawyer", "consumer protection court", "suing you"],
        "department": "Legal & Compliance",
        "supporting_department": "Management Escalations",
        "urgency": "Critical",
        "priority": "P0",
        "policy_id": "POL-ESC-14",
        "policy_section": "2.0",
        "mandatory_escalation": True,
        "escalation_tier": "Tier 4 - Compliance & Legal Team",
        "refund_eligible": False,
        "replacement_eligible": False,
        "compensation_allowed": False,
        "max_compensation": 0.0,
        "mandatory_actions": ["Mark ticket strictly Confidential / Legal Hold", "Route immediately to Legal Counsel", "Provide formal legal contact notice"],
        "prohibited_actions": ["Frontline agents MUST NOT debate legal merits or offer unauthorized settlements"],
        "required_follow_up": True,
        "follow_up_days": 1
    },
    # -------------------------------------------------------------
    # 9. Warranty Claim (Rules 22 - 35)
    # -------------------------------------------------------------
    {
        "rule_id": "RUL-WAR-022",
        "category": "Warranty Claim",
        "subcategory": "Repair Delay",
        "keywords": ["service center has my phone for 3 weeks", "repair delayed", "no update on warranty repair"],
        "department": "Warranty & Repairs",
        "supporting_department": "Customer Relations",
        "urgency": "High",
        "priority": "P1",
        "policy_id": "POL-WAR-07",
        "policy_section": "2.0",
        "mandatory_escalation": False,
        "escalation_tier": "Tier 2 - Senior Specialist",
        "refund_eligible": False,
        "replacement_eligible": True,
        "compensation_allowed": True,
        "max_compensation": 25.0,
        "mandatory_actions": ["Contact repair depot supervisor", "If parts backordered > 14 days, offer instant refurbished replacement unit"],
        "prohibited_actions": ["Do not leave repair status in limbo without timeline"],
        "required_follow_up": True,
        "follow_up_days": 2
    }
]

# Generate helper to extend rule matrix to 105+ detailed rules across all permutations
def build_full_rule_matrix() -> List[Dict[str, Any]]:
    rules = list(RULES_MATRIX)
    existing_ids = {r["rule_id"] for r in rules}
    
    categories_sub = {
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
    
    dept_map = {
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
        "Order Cancellation": "Returns & Replacements"
    }

    rule_counter = len(rules) + 1
    for cat, subcats in categories_sub.items():
        for sub in subcats:
            for variant in ["Standard", "VIP Customer", "Repeat Complaint"]:
                rule_id = f"RUL-{cat[:3].upper()}-{rule_counter:03d}"
                if rule_id in existing_ids:
                    continue
                
                is_safety = (cat == "Safety Hazard")
                is_sec = (cat == "Account Security" or "Unauthorized" in sub)
                is_vip = (variant == "VIP Customer")
                is_repeat = (variant == "Repeat Complaint")
                
                urgency = "Critical" if is_safety else ("High" if (is_sec or is_vip or is_repeat) else "Medium")
                priority = "P0" if is_safety else ("P1" if (is_sec or is_vip or is_repeat) else "P2")
                escalation = is_safety or is_sec or (is_repeat and priority == "P1")
                tier = "Tier 5 - Executive Management Escalation" if is_safety else ("Tier 4 - Compliance & Legal Team" if is_sec else ("Tier 3 - Department Manager" if is_repeat else "Tier 1 - Standard Agent"))
                
                policy_id = f"POL-{cat[:3].upper()}-01"
                if cat == "Refund Request": policy_id = "POL-REF-02"
                elif cat == "Delivery & Shipping": policy_id = "POL-DEL-04"
                elif cat == "Safety Hazard": policy_id = "POL-SAF-05"
                elif cat == "Billing & Charges": policy_id = "POL-BIL-06"
                elif cat == "Warranty Claim": policy_id = "POL-WAR-07"
                elif cat == "Account Security": policy_id = "POL-SEC-08"
                elif cat == "Data Privacy": policy_id = "POL-PRV-09"
                elif cat == "Staff Conduct": policy_id = "POL-CON-10"
                elif cat == "Order Cancellation": policy_id = "POL-CAN-11"

                rules.append({
                    "rule_id": rule_id,
                    "category": cat,
                    "subcategory": sub,
                    "customer_tier_condition": variant,
                    "keywords": [sub.lower(), cat.lower(), variant.lower()],
                    "department": dept_map.get(cat, "Customer Relations"),
                    "supporting_department": "Customer Relations" if dept_map.get(cat) != "Customer Relations" else "Management Escalations",
                    "urgency": urgency,
                    "priority": priority,
                    "policy_id": policy_id,
                    "policy_section": "1.0",
                    "mandatory_escalation": escalation,
                    "escalation_tier": tier,
                    "refund_eligible": cat in ["Refund Request", "Billing & Charges", "Safety Hazard", "Product Defect"],
                    "replacement_eligible": cat in ["Product Defect", "Warranty Claim", "Delivery & Shipping", "Safety Hazard"],
                    "compensation_allowed": cat in ["Delivery & Shipping", "Service Quality", "Staff Conduct", "Safety Hazard"],
                    "max_compensation": 50.0 if is_vip else (100.0 if is_safety else 20.0),
                    "mandatory_actions": [f"Log ticket under {cat} workflow", f"Verify customer records and order reference", f"Execute {dept_map.get(cat)} standard protocol"],
                    "prohibited_actions": ["Do not promise unverified refunds or timeline commitments", "Do not ignore safety disclosures"],
                    "required_follow_up": True,
                    "follow_up_days": 1 if urgency in ["Critical", "High"] else 3
                })
                existing_ids.add(rule_id)
                rule_counter += 1
    return rules

ALL_RULES = build_full_rule_matrix()

class RuleMatrixManager:
    @staticmethod
    def get_all_rules() -> List[Dict[str, Any]]:
        return ALL_RULES

    @staticmethod
    def match_rule(category: str, subcategory: str, customer_type: str = "Standard", description: str = "") -> Optional[Dict[str, Any]]:
        """Finds the most specific matching rule in the Complaint Resolution Rule Matrix."""
        desc_lower = description.lower()
        
        # 1. First check explicit keyword / safety / legal triggers
        for rule in ALL_RULES:
            if any(kw in desc_lower for kw in rule.get("keywords", [])):
                if rule.get("category") == category:
                    return rule
                    
        # 2. Check category + subcategory match
        for rule in ALL_RULES:
            if rule["category"] == category and rule.get("subcategory") == subcategory:
                if customer_type == "VIP" and rule.get("customer_tier_condition") == "VIP Customer":
                    return rule
                return rule

        # 3. Fallback to category match
        for rule in ALL_RULES:
            if rule["category"] == category:
                return rule

        return ALL_RULES[0]
