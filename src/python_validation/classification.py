from src.security.prompt_defense import PromptDefense


def classify_complaint(full_text: str) -> tuple[str, str]:
    category = "Customer Relations"
    subcategory = "General Inquiry"
    injection_detected, _ = PromptDefense.inspect_text_for_injections(full_text)
    if any(word in full_text for word in ["fire", "spark", "shock", "smoke", "swollen", "fume", "burn", "explosion"]):
        category = "Safety Hazard"
        subcategory = "Battery Overheating / Swelling" if "battery" in full_text or "swollen" in full_text else "Electrical Spark / Shock Hazard"
    elif injection_detected:
        category = "Account Security"
        subcategory = "Prompt Injection Attempt"
    elif any(word in full_text for word in ["hacked", "stolen", "unauthorized login", "unauthorized access", "accessed my account", "unknown login", "account takeover", "stolen credentials", "data breach", "privacy", "gdpr", "compromised"]):
        category = "Account Security" if any(term in full_text for term in ("account", "login", "password", "hacked", "stolen credentials", "accessed my account")) else "Data Privacy"
        subcategory = "Suspicious Login" if category == "Account Security" else "Data Deletion Request"
    elif any(word in full_text for word in ["double charge", "charged twice", "overcharge", "unauthorized charge", "billing error", "subscription", "missing invoice", "invoice is missing"]):
        category = "Billing & Charges"
        if "twice" in full_text or "double" in full_text:
            subcategory = "Double Charge"
        elif "subscription" in full_text or "renewal" in full_text:
            subcategory = "Subscription Overcharge"
        elif "invoice" in full_text:
            subcategory = "Missing Invoice"
        else:
            subcategory = "Incorrect Amount"
    elif any(word in full_text for word in ["refund", "money back", "return my money", "where is my refund"]):
        category, subcategory = "Refund Request", "Refund Not Processed"
    elif any(word in full_text for word in ["late delivery", "delayed delivery", "days late", "lost package", "lost in transit", "package not arrived", "tracking stuck", "wrong item", "wrong product", "incorrect item"]):
        category = "Delivery & Shipping"
        if any(word in full_text for word in ["wrong item", "wrong product", "incorrect item"]):
            subcategory = "Wrong Item Delivered"
        elif "delay" in full_text or "late" in full_text:
            subcategory = "Delayed Delivery"
        else:
            subcategory = "Package Lost in Transit"
    elif any(word in full_text for word in ["dead on arrival", "doa", "failed to turn on", "out of the box", "missing power adapter", "missing accessories", "accessories compartment", "broken", "cracked screen", "defect", "damage", "malfunction", "intermittent", "shuts down"]):
        category = "Product Defect"
        if "doa" in full_text or "dead" in full_text or any(word in full_text for word in ["failed to turn on", "out of the box"]):
            subcategory = "Dead on Arrival"
        elif any(word in full_text for word in ["missing power adapter", "missing accessories", "accessories compartment"]):
            subcategory = "Missing Parts"
        elif "intermittent" in full_text or "randomly shuts down" in full_text:
            subcategory = "Intermittent Failure"
        else:
            subcategory = "Physical Damage"
    elif any(word in full_text for word in ["rude agent", "unprofessional staff", "hung up on me", "hung up", "abusive", "harassed", "insulted"]):
        category, subcategory = "Staff Conduct", "Agent Misbehavior"
    elif any(word in full_text for word in ["poor installation", "misleading information", "service quality", "installation service"]):
        category = "Service Quality"
        subcategory = "Poor Installation Service" if "installation" in full_text else "Misleading Information"
    elif any(word in full_text for word in ["software crash", "firmware update", "wifi", "wi-fi", "connectivity issue", "bluetooth"]):
        category = "Technical Support"
        subcategory = "Connectivity Issue" if any(word in full_text for word in ["wifi", "wi-fi", "connectivity", "bluetooth"]) else "Software Crash"
    elif any(word in full_text for word in ["warranty", "repair", "service center"]):
        category, subcategory = "Warranty Claim", "Repair Delay"
    elif any(word in full_text for word in ["cancel order", "cancellation denied", "cancellation request", "requested cancellation", "cancelled my", "cancelled before shipment", "stop shipment"]):
        category, subcategory = "Order Cancellation", "Cancellation Denied"
    return category, subcategory
