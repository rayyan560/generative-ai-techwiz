DEPARTMENTS = [
    "Billing & Payments",
    "Logistics & Delivery",
    "Technical Support",
    "Returns & Replacements",
    "Warranty & Repairs",
    "Customer Relations",
    "Account Security & Privacy",
    "Product Quality & Safety",
    "Legal & Compliance",
    "Management Escalations",
]

CATEGORIES = [
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
    "Order Cancellation",
]

SUBCATEGORIES = {
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
    "Order Cancellation": ["Cancellation Denied", "Auto-Renewal Dispute", "Pre-order Cancellation", "Partial Order Cancellation"],
}

URGENCY_LEVELS = ["Low", "Medium", "High", "Critical"]
PRIORITY_SLA_HOURS = {
    "P0": {"name": "Critical", "response_hours": 1, "resolution_hours": 4, "badge_color": "danger"},
    "P1": {"name": "High", "response_hours": 4, "resolution_hours": 12, "badge_color": "warning"},
    "P2": {"name": "Medium", "response_hours": 12, "resolution_hours": 24, "badge_color": "primary"},
    "P3": {"name": "Low", "response_hours": 24, "resolution_hours": 72, "badge_color": "secondary"},
}
ESCALATION_LEVELS = [
    "Tier 1 - Standard Agent",
    "Tier 2 - Senior Specialist",
    "Tier 3 - Department Manager",
    "Tier 4 - Compliance & Legal Team",
    "Tier 5 - Executive Management Escalation",
]
