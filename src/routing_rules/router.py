import re
from typing import Tuple, Optional, List, Dict, Any

ROUTING_MAP = {
    "Product Defect": ("Returns & Replacements", "Technical Support"),
    "Billing & Charges": ("Billing & Payments", "Customer Relations"),
    "Delivery & Shipping": ("Logistics & Delivery", "Returns & Replacements"),
    "Refund Request": ("Billing & Payments", "Returns & Replacements"),
    "Account Security": ("Account Security & Privacy", "Management Escalations"),
    "Technical Support": ("Technical Support", "Warranty & Repairs"),
    "Service Quality": ("Customer Relations", "Management Escalations"),
    "Warranty Claim": ("Warranty & Repairs", "Customer Relations"),
    "Data Privacy": ("Account Security & Privacy", "Legal & Compliance"),
    "Safety Hazard": ("Product Quality & Safety", "Legal & Compliance"),
    "Staff Conduct": ("Customer Relations", "Management Escalations"),
    "Order Cancellation": ("Returns & Replacements", "Billing & Payments")
}

class DepartmentRouter:
    @staticmethod
    def route_complaint(category: str, description: str = "") -> Tuple[str, Optional[str]]:
        """
        Determines Primary and Supporting Departments deterministically.
        Detects multi-department needs.
        """
        primary, supporting = ROUTING_MAP.get(category, ("Customer Relations", "Management Escalations"))
        desc_lower = description.lower()
        
        # Multi-department detection heuristics
        # 1. Product damaged + refund delay
        if ("damage" in desc_lower or "defect" in desc_lower) and ("refund" in desc_lower or "charge" in desc_lower):
            primary = "Returns & Replacements"
            supporting = "Billing & Payments"
            
        # 2. Delivery delay + rude driver
        elif ("delivery" in desc_lower or "courier" in desc_lower) and ("rude" in desc_lower or "abusive" in desc_lower):
            primary = "Logistics & Delivery"
            supporting = "Customer Relations"
            
        # 3. Safety spark + medical/legal
        elif ("spark" in desc_lower or "fire" in desc_lower or "shock" in desc_lower) and ("lawyer" in desc_lower or "hospital" in desc_lower):
            primary = "Product Quality & Safety"
            supporting = "Legal & Compliance"
            
        return primary, supporting
