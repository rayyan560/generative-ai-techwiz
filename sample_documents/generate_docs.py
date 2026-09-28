import os
import io
import docx
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
os.makedirs(DOCS_DIR, exist_ok=True)

POLICIES = [
    {
        "doc_id": "POL-CMP-01",
        "title": "Customer Complaint Handling Standard Operating Procedure",
        "category": "Customer Relations",
        "version": "v2.1",
        "effective_date": "2024-01-01",
        "status": "Active",
        "sections": [
            ("1.0 Purpose and Scope", "This procedure sets mandatory requirements for receiving, logging, triage, and resolving complaints across NovaTech Global retail, online e-commerce, and electronics divisions."),
            ("2.0 Initial Response SLA", "All submitted complaints must receive an immediate automated acknowledgment and be reviewed by an agent within 4 hours for P1/P2 issues and within 1 hour for P0 critical safety issues."),
            ("3.0 Prohibited Commitments", "Agents must NEVER guarantee refunds, monetary compensation, or product replacements in initial responses without prior ground-truth validation and manager sign-off.")
        ]
    },
    {
        "doc_id": "POL-REF-02",
        "title": "Global Refund and Return Policy",
        "category": "Refund Request",
        "version": "v2.0",
        "effective_date": "2024-02-15",
        "status": "Active",
        "sections": [
            ("1.0 Eligibility Window", "Customers may request a full refund within 30 days of confirmed delivery for unopened, unused, or defective items. Digital goods and gift cards are non-refundable once redeemed."),
            ("2.0 Return Shipping Charges", "NovaTech provides prepaid return labels for all defective, damaged, or erroneously shipped items. Discretionary buyer's remorse returns incur a $5.99 return shipping fee."),
            ("3.0 Refund Processing Timelines", "Approved refunds are credited back to the original payment method within 3 to 5 business days upon warehouse receipt.")
        ]
    },
    {
        "doc_id": "POL-REF-02-OLD",
        "title": "Global Refund and Return Policy (Old 2022 Version)",
        "category": "Refund Request",
        "version": "v1.0",
        "effective_date": "2022-01-01",
        "status": "Superseded",
        "sections": [
            ("1.0 Obsolete 14-Day Window", "Customers must return products strictly within 14 days of purchase. (NOTE: This policy is OBSOLETE and superseded by POL-REF-02 v2.0).")
        ]
    },
    {
        "doc_id": "POL-REP-03",
        "title": "Product Replacement and Exchange Standard Operating Procedure",
        "category": "Product Defect",
        "version": "v2.0",
        "effective_date": "2024-01-10",
        "status": "Active",
        "sections": [
            ("1.0 Dead on Arrival (DOA) Replacements", "Any consumer electronics device failing within 7 days of delivery qualifies for immediate Priority Express replacement without waiting for the defective unit to be inspected."),
            ("2.0 Out of Stock Exchange", "If identical SKU is unavailable for replacement, customer must be offered an upgraded model of equal or greater value or an instant full refund.")
        ]
    },
    {
        "doc_id": "POL-DEL-04",
        "title": "Logistics, Delivery Delays and Lost Package Policy",
        "category": "Delivery & Shipping",
        "version": "v1.5",
        "effective_date": "2024-03-01",
        "status": "Active",
        "sections": [
            ("1.0 Delivery Delay Thresholds", "If a package is delayed by more than 48 hours past the estimated delivery date, the logistics team must initiate a courier trace and provide daily updates."),
            ("2.0 Package Deemed Lost in Transit", "If tracking shows no movement for 7 consecutive business days, the shipment is classified as lost. Customer is immediately entitled to re-shipment or full refund plus a $15 courtesy credit.")
        ]
    },
    {
        "doc_id": "POL-SAF-05",
        "title": "Product Safety Hazard and Critical Incident Protocol",
        "category": "Safety Hazard",
        "version": "v3.0",
        "effective_date": "2024-01-01",
        "status": "Active",
        "sections": [
            ("1.0 Critical Safety Triggers", "Any report mentioning electrical shock, sparks, battery swelling, fire, explosion, or chemical leakage is automatically designated Priority P0 Critical."),
            ("2.0 Mandatory Tier 5 Escalation", "All safety hazard complaints must be immediately routed to the Product Safety & Legal Compliance Committee within 30 minutes. Frontline agents are strictly forbidden from dismissing safety reports.")
        ]
    },
    {
        "doc_id": "POL-BIL-06",
        "title": "Billing Disputes, Double Charges and Payment Resolution SOP",
        "category": "Billing & Charges",
        "version": "v2.0",
        "effective_date": "2024-01-15",
        "status": "Active",
        "sections": [
            ("1.0 Duplicate Charge Investigation", "If customer provides bank statements showing duplicate charges for a single order, the Billing department must reverse the secondary authorization within 24 hours."),
            ("2.0 Unauthorized Card Charges", "Transactions flagged by customer as fraudulent must trigger instant account freeze, cancellation of pending shipments, and referral to Account Security.")
        ]
    },
    {
        "doc_id": "POL-WAR-07",
        "title": "Hardware Warranty and Repair Services Policy",
        "category": "Warranty Claim",
        "version": "v2.2",
        "effective_date": "2024-02-01",
        "status": "Active",
        "sections": [
            ("1.0 Standard 1-Year Limited Warranty", "All NovaTech manufactured hardware includes a 1-year limited warranty covering manufacturing defects in materials and workmanship."),
            ("2.0 Exclusions", "Accidental drops, liquid submersion (unless IP68 certified), and unauthorized modifications void the warranty.")
        ]
    },
    {
        "doc_id": "POL-SEC-08",
        "title": "Account Security, Unauthorized Access and Data Privacy SOP",
        "category": "Account Security",
        "version": "v2.1",
        "effective_date": "2024-01-20",
        "status": "Active",
        "sections": [
            ("1.0 Account Compromise Protocol", "If customer reports unauthorized password change, 2FA bypass, or unrecognized orders, agent must instantly lock user profile and invalidate all active session tokens."),
            ("2.0 Identity Verification", "Account recovery requires two-factor verification via verified secondary email or government ID submission.")
        ]
    },
    {
        "doc_id": "POL-PRV-09",
        "title": "Data Privacy and GDPR Right-to-be-Forgotten Policy",
        "category": "Data Privacy",
        "version": "v1.8",
        "effective_date": "2024-01-01",
        "status": "Active",
        "sections": [
            ("1.0 Data Deletion Requests", "Customer requests for personal data deletion must be fulfilled within 30 calendar days in compliance with GDPR / CCPA."),
            ("2.0 Marketing Opt-Out", "Unsubscribe requests from promotional emails and SMS must take effect within 48 hours.")
        ]
    },
    {
        "doc_id": "POL-CON-10",
        "title": "Employee Workplace Conduct and Anti-Harassment Standard",
        "category": "Staff Conduct",
        "version": "v2.0",
        "effective_date": "2024-01-01",
        "status": "Active",
        "sections": [
            ("1.0 Customer Interaction Standards", "All support personnel must maintain a respectful, courteous, and non-discriminatory demeanor at all times."),
            ("2.0 Escalation for Staff Abuse", "Complaints detailing verbal abuse, derogatory slurs, or harassment by staff are escalated to HR & Quality Assurance Tier 3 within 2 hours.")
        ]
    },
    {
        "doc_id": "POL-CAN-11",
        "title": "Order Cancellation and Pre-Order Modification SOP",
        "category": "Order Cancellation",
        "version": "v1.4",
        "effective_date": "2024-02-01",
        "status": "Active",
        "sections": [
            ("1.0 Cancellation Before Shipment", "Customers may cancel orders at zero penalty while status is 'Processing' or 'Order Placed'."),
            ("2.0 Cancellation Post-Dispatch", "Once package is handed to courier, order cannot be cancelled; customer must refuse delivery or initiate a standard return.")
        ]
    },
    {
        "doc_id": "POL-TEC-12",
        "title": "Technical Support and Software Troubleshooting SOP",
        "category": "Technical Support",
        "version": "v2.0",
        "effective_date": "2024-01-15",
        "status": "Active",
        "sections": [
            ("1.0 Level 1 Troubleshooting Checklist", "Agents must guide customer through device power cycle, firmware version verification, and factory reset before ordering hardware replacement."),
            ("2.0 Level 2 Escalation", "Persistent software crashes with error logs must be assigned to Senior Software Engineering Support.")
        ]
    },
    {
        "doc_id": "POL-VIP-13",
        "title": "VIP & Corporate Enterprise SLA Guidelines",
        "category": "Customer Relations",
        "version": "v1.5",
        "effective_date": "2024-01-01",
        "status": "Active",
        "sections": [
            ("1.0 VIP Customer Identification", "Customers with annual spend exceeding $10,000 or holding 'Titanium Executive' status receive dedicated account manager routing."),
            ("2.0 Expedited SLA", "VIP ticket response target is within 30 minutes, and maximum resolution time is 8 business hours.")
        ]
    },
    {
        "doc_id": "POL-ESC-14",
        "title": "Enterprise Escalation Hierarchy & Tiers Matrix",
        "category": "Management Escalations",
        "version": "v3.0",
        "effective_date": "2024-01-01",
        "status": "Active",
        "sections": [
            ("1.0 Escalation Tier Definitions", "Tier 1: Frontline Agent | Tier 2: Senior Specialist | Tier 3: Department Manager | Tier 4: Compliance & Legal | Tier 5: Executive Board."),
            ("2.0 Legal Threat Trigger", "Any communication explicitly threatening legal action or attorney involvement must immediately be escalated to Tier 4 Legal & Compliance.")
        ]
    },
    {
        "doc_id": "POL-GWD-15",
        "title": "Customer Goodwill, Compensation and Courtesy Credits SOP",
        "category": "Customer Relations",
        "version": "v2.0",
        "effective_date": "2024-03-01",
        "status": "Active",
        "sections": [
            ("1.0 Frontline Authorization Limit", "Frontline agents may issue goodwill store credits up to $25 without supervisor approval."),
            ("2.0 Manager Approval Limits", "Store credits between $26 and $100 require Tier 3 Manager approval. Credits exceeding $100 require Director authorization.")
        ]
    },
    {
        "doc_id": "POL-DOA-16",
        "title": "Dead On Arrival (DOA) Hardware Diagnostic Protocol",
        "category": "Product Defect",
        "version": "v1.2",
        "effective_date": "2024-01-01",
        "status": "Active",
        "sections": [
            ("1.0 DOA Verification Criteria", "Products reported inoperable out of box with undamaged packaging qualify as DOA upon providing serial number and photo.")
        ]
    },
    {
        "doc_id": "POL-SUB-17",
        "title": "Recurring Subscription Billing and Auto-Renewal Policy",
        "category": "Billing & Charges",
        "version": "v1.6",
        "effective_date": "2024-02-01",
        "status": "Active",
        "sections": [
            ("1.0 Auto-Renewal Notification", "Customers are billed automatically unless cancelled 24 hours prior to billing cycle date.")
        ]
    },
    {
        "doc_id": "POL-LOST-18",
        "title": "Courier Lost In Transit and Stolen Package Claims SOP",
        "category": "Delivery & Shipping",
        "version": "v2.0",
        "effective_date": "2024-01-10",
        "status": "Active",
        "sections": [
            ("1.0 Porch Piracy / Missing Delivery Investigation", "When carrier claims delivered but customer has not received package, carrier GPS coordinates must be requested within 24 hours.")
        ]
    },
    {
        "doc_id": "POL-B2B-19",
        "title": "B2B Commercial Partner Service Level Agreement",
        "category": "Customer Relations",
        "version": "v1.1",
        "effective_date": "2024-01-01",
        "status": "Active",
        "sections": [
            ("1.0 Wholesale Customer Terms", "Commercial accounts receive guaranteed 99.9% uptime for cloud services and 4-hour replacement hardware delivery.")
        ]
    },
    {
        "doc_id": "POL-FAQ-20",
        "title": "Customer Service Frequently Asked Questions (FAQ) Guide",
        "category": "Customer Relations",
        "version": "v2.5",
        "effective_date": "2024-03-15",
        "status": "Active",
        "sections": [
            ("1.0 Common Delivery Queries", "Standard shipping takes 3-5 business days. Express shipping takes 1-2 business days."),
            ("2.0 Return Address & Packaging", "Items must be returned in original packaging with all included accessories and user manuals.")
        ]
    }
]

def generate_docx_file(doc_data, filepath):
    doc = docx.Document()
    doc.add_heading(f"{doc_data['doc_id']}: {doc_data['title']}", level=0)
    p_meta = doc.add_paragraph()
    p_meta.add_run(f"Category: {doc_data['category']} | Version: {doc_data['version']} | Status: {doc_data['status']} | Effective: {doc_data['effective_date']}").bold = True
    
    for heading, text in doc_data["sections"]:
        doc.add_heading(heading, level=1)
        doc.add_paragraph(text)
    
    doc.save(filepath)

def generate_pdf_file(doc_data, filepath):
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    y = height - 50
    
    # Title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, f"{doc_data['doc_id']}: {doc_data['title']}")
    y -= 25
    
    # Metadata
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#2B6CB0"))
    c.drawString(50, y, f"Category: {doc_data['category']} | Version: {doc_data['version']} | Status: {doc_data['status']} | Date: {doc_data['effective_date']}")
    y -= 30
    c.setFillColor(colors.black)
    
    for heading, text in doc_data["sections"]:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, heading)
        y -= 18
        c.setFont("Helvetica", 9)
        # Word wrap basic
        words = text.split(" ")
        line = ""
        for w in words:
            if len(line + " " + w) > 85:
                c.drawString(60, y, line)
                y -= 14
                line = w
            else:
                line = line + " " + w if line else w
        if line:
            c.drawString(60, y, line)
            y -= 25
            
    c.save()

def generate_all():
    print(f"Generating {len(POLICIES)} company policy & SOP documents in DOCX and PDF...")
    for item in POLICIES:
        docx_path = os.path.join(DOCS_DIR, f"{item['doc_id']}.docx")
        pdf_path = os.path.join(DOCS_DIR, f"{item['doc_id']}.pdf")
        generate_docx_file(item, docx_path)
        generate_pdf_file(item, pdf_path)
    print("All documents generated successfully in", DOCS_DIR)

if __name__ == "__main__":
    generate_all()
