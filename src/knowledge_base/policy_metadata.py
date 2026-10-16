import os


DOCS_FOLDER = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "sample_documents",
    "docs",
)

PRECEDENCE_HIERARCHY = {
    "Active Policy": 100,
    "Standard Operating Procedure (SOP)": 80,
    "Departmental Guideline": 60,
    "Frequently Asked Questions (FAQ)": 40,
    "Informal Guidance": 20,
    "Superseded Policy": 0,
    "Draft Policy": 10,
}

POLICY_TITLES = {
    "POL-REF-02": "Customer Refund & Escrow Payout Policy",
    "POL-WAR-07": "Limited Hardware Warranty Coverage Policy",
    "POL-DEL-04": "Delivery & Logistics Replacement Policy",
    "POL-SAF-05": "Product Safety & Fire Hazard Escalation Policy",
    "POL-BIL-06": "Billing Discrepancy & Chargeback Policy",
    "POL-SEC-08": "Account Security & Fraud Prevention Policy",
    "POL-PRV-09": "Data Privacy & GDPR Governance Policy",
    "POL-CON-10": "Staff Professional Conduct & Service Quality SOP",
    "POL-TEC-12": "Technical Support Diagnostics & Hardware Repair SOP",
    "POL-ESC-14": "Escalation Matrix & Manager Sign-off Governance",
    "POL-DOA-16": "Dead-on-Arrival (DOA) Return Policy",
    "POL-SUB-17": "Subscription & Recurring Billing Terms",
    "POL-B2B-19": "B2B Enterprise SLA & Bulk Refund Policy",
    "POL-GWD-15": "Global Warranty & Defect Exchange Policy",
    "POL-REP-03": "Product Replacement & Repair Operations Policy",
    "POL-CAN-11": "Order Cancellation & Change Request Policy",
}


def precedence_score_for(doc_type: str, status: str) -> int:
    if status.casefold() == "superseded":
        return PRECEDENCE_HIERARCHY["Superseded Policy"]
    return PRECEDENCE_HIERARCHY.get(doc_type, PRECEDENCE_HIERARCHY["Active Policy"])
