import re
from typing import Dict, Any, List, Tuple

# 32+ Mandatory Escalation Rules & Conditions as required by SRS
ESCALATION_CONDITIONS = [
    {
        "esc_id": "ESC-001",
        "name": "Critical Battery Swelling / Fire Hazard",
        "pattern": r"\b(swollen|battery puff|fire|spark|exploded|smoke|flame)\b",
        "required_tier": "Tier 5 - Executive Management Escalation",
        "reason": "Life safety hazard and fire prevention protocol",
        "mandatory": True
    },
    {
        "esc_id": "ESC-002",
        "name": "Electrical Shock / Injury",
        "pattern": r"\b(electric shock|electrocuted|burnt hand|hospital|injury|doctor)\b",
        "required_tier": "Tier 5 - Executive Management Escalation",
        "reason": "Personal bodily harm and urgent product safety containment",
        "mandatory": True
    },
    {
        "esc_id": "ESC-003",
        "name": "Formal Legal Threat / Attorney Notice",
        "pattern": r"\b(lawyer|attorney|lawsuit|suing|court|legal action|bar association)\b",
        "required_tier": "Tier 4 - Compliance & Legal Team",
        "reason": "Pending litigation risk and statutory legal preservation",
        "mandatory": True
    },
    {
        "esc_id": "ESC-004",
        "name": "Regulatory Agency / FTC / GDPR Threat",
        "pattern": r"\b(ftc|gdpr|consumer protection bureau|bbb|attorney general|regulatory complaint)\b",
        "required_tier": "Tier 4 - Compliance & Legal Team",
        "reason": "Regulatory compliance inspection risk",
        "mandatory": True
    },
    {
        "esc_id": "ESC-005",
        "name": "Account Takeover / Stolen Identity",
        "pattern": r"\b(hacked|stolen credentials|unauthorized access|someone logged into my account|identity theft)\b",
        "required_tier": "Tier 4 - Compliance & Legal Team",
        "reason": "Account security compromise and data privacy risk",
        "mandatory": True
    },
    {
        "esc_id": "ESC-006",
        "name": "Mass Data Leak / Privacy Breach",
        "pattern": r"\b(data breach|leaked records|saw someone else's data|credit card exposed)\b",
        "required_tier": "Tier 4 - Compliance & Legal Team",
        "reason": "Statutory data breach disclosure requirement",
        "mandatory": True
    },
    {
        "esc_id": "ESC-007",
        "name": "Severe Staff Harassment / Abusive Agent",
        "pattern": r"\b(verbally abused|agent insulted|cursed at me|racial slur|harassed by representative)\b",
        "required_tier": "Tier 3 - Department Manager",
        "reason": "Severe staff misconduct and HR quality audit",
        "mandatory": True
    },
    {
        "esc_id": "ESC-008",
        "name": "High-Value Transaction Dispute (> $1,000)",
        "condition_fn": lambda c: (c.get("extracted_entities", {}).get("amount", 0) or 0) >= 1000.0,
        "required_tier": "Tier 3 - Department Manager",
        "reason": "High financial exposure exceeding frontline authority",
        "mandatory": True
    },
    {
        "esc_id": "ESC-009",
        "name": "Repeated Unresolved Complaint (3+ attempts)",
        "condition_fn": lambda c: c.get("is_repeat_complaint", False) or c.get("repeat_count", 0) >= 2,
        "required_tier": "Tier 3 - Department Manager",
        "reason": "Chronic customer dissatisfaction and resolution failure",
        "mandatory": True
    },
    {
        "esc_id": "ESC-010",
        "name": "VIP / Corporate Executive Customer",
        "condition_fn": lambda c: c.get("customer_type") in ["VIP", "Corporate", "Enterprise"],
        "required_tier": "Tier 2 - Senior Specialist",
        "reason": "Contractual VIP enterprise account SLA",
        "mandatory": True
    },
    {
        "esc_id": "ESC-011",
        "name": "Social Media / PR Viral Threat",
        "pattern": r"\b(twitter|x\.com|viral|press release|news channel|influencer|million followers)\b",
        "required_tier": "Tier 3 - Department Manager",
        "reason": "Public relations and brand reputation risk",
        "mandatory": True
    },
    {
        "esc_id": "ESC-012",
        "name": "Courier Theft / Tampered Package",
        "pattern": r"\b(package was cut open|driver stole contents|empty box delivered|tampered seal)\b",
        "required_tier": "Tier 2 - Senior Specialist",
        "reason": "Carrier supply chain theft investigation",
        "mandatory": True
    },
    {
        "esc_id": "ESC-013",
        "name": "Critical Infrastructure / Cloud Server Outage",
        "pattern": r"\b(cloud service down|server offline|enterprise system down|database outage)\b",
        "required_tier": "Tier 4 - Compliance & Legal Team",
        "reason": "High-severity B2B service availability SLA breach",
        "mandatory": True
    },
    {
        "esc_id": "ESC-014",
        "name": "Child / Minor Safety Concern",
        "pattern": r"\b(child swallowed|toxic to kids|sharp blade cut child|baby choked)\b",
        "required_tier": "Tier 5 - Executive Management Escalation",
        "reason": "Child safety hazard and mandatory CPSC recall alert",
        "mandatory": True
    },
    {
        "esc_id": "ESC-015",
        "name": "Bribery / Fraud Attempt",
        "pattern": r"\b(bribe|under the table|fake receipt offer|collusion)\b",
        "required_tier": "Tier 4 - Compliance & Legal Team",
        "reason": "Anti-fraud and corporate compliance policy violation",
        "mandatory": True
    }
]

ESCALATION_CONDITIONS.extend([
    {"esc_id": "ESC-016", "name": "Emergency Medical Treatment", "pattern": r"\b(emergency room|hospitalized|hospitalised|medical treatment|permanent injury)\b", "required_tier": "Tier 5 - Executive Management Escalation", "reason": "Reported injury requires urgent safety and compliance review", "mandatory": True},
    {"esc_id": "ESC-017", "name": "Product Recall or Safety Notice", "pattern": r"\b(product recall|safety recall|recall notice|cpsc investigation)\b", "required_tier": "Tier 5 - Executive Management Escalation", "reason": "Potential recall or regulator-directed product action", "mandatory": True},
    {"esc_id": "ESC-018", "name": "Property Fire or Evacuation", "pattern": r"\b(house fire|apartment fire|evacuated|property caught fire|fire department responded)\b", "required_tier": "Tier 5 - Executive Management Escalation", "reason": "Potential property damage or immediate life-safety event", "mandatory": True},
    {"esc_id": "ESC-019", "name": "Toxic Fumes or Chemical Exposure", "pattern": r"\b(toxic fumes|chemical exposure|poisonous vapou?r|inhaled fumes|chemical burn)\b", "required_tier": "Tier 5 - Executive Management Escalation", "reason": "Potential exposure requiring safety escalation", "mandatory": True},
    {"esc_id": "ESC-020", "name": "Suspected Child Product Injury", "pattern": r"\b(child was injured|injured my child|child safety injury|infant was hurt)\b", "required_tier": "Tier 5 - Executive Management Escalation", "reason": "Reported child injury needs immediate safety review", "mandatory": True},
    {"esc_id": "ESC-021", "name": "Ransomware or Extortion", "pattern": r"\b(ransomware|ransom demand|encrypted our files|extortion demand)\b", "required_tier": "Tier 4 - Compliance & Legal Team", "reason": "Possible cyber extortion or business data compromise", "mandatory": True},
    {"esc_id": "ESC-022", "name": "Unauthorized Financial Transfer", "pattern": r"\b(unauthorized transfer|money transferred without permission|bank transfer fraud|funds stolen from)\b", "required_tier": "Tier 4 - Compliance & Legal Team", "reason": "Possible financial fraud requiring payment and security review", "mandatory": True},
    {"esc_id": "ESC-023", "name": "Regulator Data-Access or Deletion Deadline", "pattern": r"\b(data subject request|gdpr deadline|ccpa deadline|regulator ordered deletion|privacy regulator)\b", "required_tier": "Tier 4 - Compliance & Legal Team", "reason": "Potential statutory response deadline", "mandatory": True},
    {"esc_id": "ESC-024", "name": "Court Order or Evidence Preservation", "pattern": r"\b(court order|preserve evidence|litigation hold|subpoena|discovery request)\b", "required_tier": "Tier 4 - Compliance & Legal Team", "reason": "Potential legal preservation or court-directed obligation", "mandatory": True},
    {"esc_id": "ESC-025", "name": "Accessibility Discrimination Allegation", "pattern": r"\b(denied reasonable accommodation|accessibility discrimination|ada violation|discriminated due to disability)\b", "required_tier": "Tier 4 - Compliance & Legal Team", "reason": "Potential accessibility or civil-rights compliance matter", "mandatory": True},
    {"esc_id": "ESC-026", "name": "Protected-Class Discrimination Allegation", "pattern": r"\b(racial discrimination|discrimination based on|sexual harassment|religious discrimination|discriminated against me)\b", "required_tier": "Tier 4 - Compliance & Legal Team", "reason": "Sensitive discrimination or harassment allegation", "mandatory": True},
    {"esc_id": "ESC-027", "name": "Credential or Payment-Card Exposure", "pattern": r"\b(passwords exposed|credit card data leaked|payment card exposed|credentials leaked|card number disclosed)\b", "required_tier": "Tier 4 - Compliance & Legal Team", "reason": "Possible credential or payment data exposure", "mandatory": True},
    {"esc_id": "ESC-028", "name": "Multi-Customer Safety Pattern", "pattern": r"\b(other customers.{0,30}(same issue|same defect)|multiple units.{0,30}(overheat|catch fire)|same defect reported by)\b", "required_tier": "Tier 5 - Executive Management Escalation", "reason": "Possible systemic product hazard affecting multiple customers", "mandatory": True},
    {"esc_id": "ESC-029", "name": "Tampered Safety Evidence", "pattern": r"\b(altered safety report|destroyed test results|evidence was tampered|falsified inspection)\b", "required_tier": "Tier 4 - Compliance & Legal Team", "reason": "Potential evidence integrity concern", "mandatory": True},
    {"esc_id": "ESC-030", "name": "Threat to Public or Staff Safety", "pattern": r"\b(threatened to hurt|threat to kill|weapon at (the )?(store|office)|going to attack)\b", "required_tier": "Tier 5 - Executive Management Escalation", "reason": "Credible threat requires immediate safety escalation", "mandatory": True},
    {"esc_id": "ESC-031", "name": "Coordinated Account Takeover", "pattern": r"\b(accounts were taken over|mass account takeover|multiple accounts compromised|credential stuffing)\b", "required_tier": "Tier 4 - Compliance & Legal Team", "reason": "Possible coordinated security incident", "mandatory": True},
    {"esc_id": "ESC-032", "name": "High-Value Shipment Theft", "condition_fn": lambda c: c.get("category") == "Delivery & Shipping" and float((c.get("genai_analysis") or {}).get("extracted_entities", {}).get("amount") or 0) >= 5000, "required_tier": "Tier 3 - Department Manager", "reason": "High-value shipment loss needs management and carrier review", "mandatory": True},
    {"esc_id": "ESC-033", "name": "Time-Sensitive Payment Dispute", "pattern": r"\b(chargeback deadline|bank dispute deadline|fraud claim deadline|payment dispute deadline)\b", "required_tier": "Tier 3 - Department Manager", "reason": "Potential time-limited payment dispute response", "mandatory": True},
    {"esc_id": "ESC-034", "name": "Journalist or National Media Inquiry", "pattern": r"\b(journalist contacted|national news contacted|reporter requested comment|media inquiry)\b", "required_tier": "Tier 3 - Department Manager", "reason": "External media inquiry requires communications review", "mandatory": True},
])

class EscalationManager:
    @staticmethod
    def evaluate_escalation(complaint_dict: Dict[str, Any]) -> Tuple[bool, str, str, str]:
        """
        Deterministically evaluates whether a complaint must be escalated.
        Returns: (is_escalated, escalation_tier, escalation_reason, rule_id)
        """
        text = f"{complaint_dict.get('complaint_title', '')} {complaint_dict.get('complaint_description', '')}".lower()
        
        # Check all escalation conditions
        for cond in ESCALATION_CONDITIONS:
            # 1. Regex pattern check
            if "pattern" in cond and re.search(cond["pattern"], text):
                return True, cond["required_tier"], cond["reason"], cond["esc_id"]
                
            # 2. Lambda condition check
            if "condition_fn" in cond:
                try:
                    if cond["condition_fn"](complaint_dict):
                        return True, cond["required_tier"], cond["reason"], cond["esc_id"]
                except Exception:
                    pass

        return False, "Tier 1 - Standard Agent", "Standard frontline agent resolution", "ESC-NONE"
