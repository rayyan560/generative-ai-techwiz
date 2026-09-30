# SupportNova - ResponseX Intelligence Platform
**Aptech Techwiz 7 | Category: Generative AI PowerPlay**  
*Enterprise Customer Complaint Intelligence & Dual-Pipeline Ground-Truth Validation System*

---

## 🌟 Executive Summary

SupportNova is an AI-powered enterprise complaint triage and ground-truth validation solution built for **NovaTech Global Commerce & Electronics**. Traditional complaint resolution often suffers from delayed routing, inconsistent policy interpretation, and manual bottlenecks. SupportNova resolves this with a dual-pipeline architecture:

1. **Pipeline 1 (GenAI Complaint Intelligence)**: Leverages Google Gemini models (`gemini-1.5-flash` / `gemini-1.5-pro`) with multi-key load rotation to analyze unstructured complaints, extract entities, identify primary/secondary issues, classify sentiment and urgency, reference corporate policies, and draft customer responses.
2. **Pipeline 2 (Deterministic Python Ground-Truth Validation)**: An independent, 100% Python-based rule engine that validates GenAI recommendations against a **105+ Complaint Resolution Rule Matrix**, **32+ Mandatory Escalation Conditions**, and **20+ Version-Controlled Policy Documents**.
3. **Comparison & Verification Engine**: Measures consistency, mandatory action coverage, and source traceability. Flags unauthorized commitments (e.g. unverified refund promises, hallucinations, prompt injections) and routes edge cases to a **Manual Review Queue**.

> 🔒 **Customer Privacy & Trust**: In strict accordance with enterprise standards, the customer-facing intake portal presents a clean, authoritative service ticketing experience with zero internal AI exposure. Behind the scenes, the dual-pipeline powers the support agent workspace.

---

## 📸 System Architecture & Theming

```
[ Customer Submissions ] --> [ Untrusted Data Sanitizer ] --> [ Preprocessing & Entity Extraction ]
                                                                       │
                         ┌─────────────────────────────────────────────┴─────────────────────────────────────────────┐
                         ▼                                                                                           ▼
            [ Pipeline 1: Python + GenAI ]                                                             [ Pipeline 2: Python Ground-Truth ]
            • Multi-Key Gemini API Rotation                                                            • 105+ Complaint Resolution Rules Matrix
            • Sentiment & Emotion Analysis                                                             • 32+ Mandatory Escalation Rules (P0-P3)
            • Structured Pydantic JSON Output                                                          • Active Policy Precedence (v2.0 > v1.0)
            • Professional Draft Response                                                              • Refund & Replacement Eligibility Matrix
                         │                                                                                           │
                         └─────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                                                       ▼
                                                       [ Comparison & Scoring Engine ]
                                                       • Mandatory Coverage Score %
                                                       • Source Traceability Score %
                                                       • Consistency & Alignment Score %
                                                       • Hallucination & Injection Defense
                                                                       │
                                                                       ▼
                                                       [ Agent & Admin Workspace Hub ]
                                                       • Modern Slate & Indigo SaaS Theme
                                                       • 1-Click Triage & Approvals
                                                       • Live Call Simulation & Audio Recording
                                                       • Real-Time Analytics & CSV/PDF Export
```

---

## 🚀 Key Features

- **525+ Unique Pre-seeded Complaints**: Covers simple, multi-issue, high-risk safety, calm-critical, prompt injections, and duplicate resubmissions.
- **20+ Parsed Policies & SOPs (PDF & DOCX)**: Ingested using PyMuPDF and python-docx with section chunking, heading extraction, and version status (Active vs Superseded).
- **105+ Ground-Truth Rules Matrix**: Complete deterministic mapping across 12 categories, 25+ subcategories, and 10 enterprise departments.
- **32+ Mandatory Escalation Conditions**: Automated detection for battery swelling, electrical fire hazard, FTC/GDPR disputes, and legal attorney threats.
- **Adversarial & Prompt Injection Defense**: Neutralizes attempts to bypass refund policies or extract system prompts.
- **MongoDB Atlas + Resilient Local Store**: Seamlessly connects to MongoDB Atlas with persistent local store fallback.
- **Rich Dashboard & Analytics**: Volume trends, department breakdown, SLA risk detection, and 1-click CSV export.

---

## 🛠️ Quick Start & Installation

### 1. Prerequisites
- Python 3.11 or 3.12
- Git

### 2. Environment Setup
```bash
# Clone the repository
git clone https://github.com/rayyan560/generative-ai-techwiz.git
cd generative-ai-techwiz

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

For local-only demo accounts, copy `.env.example` to `.env` and set `DEMO_MODE=true`. Never enable demo mode on a public deployment. For hosted use, configure `MONGODB_URI`, `SESSION_SECRET_KEY`, `ADMIN_EMAIL`, and a strong `ADMIN_PASSWORD` in the host's private variables. Configure `GEMINI_API_KEYS` and Google OAuth credentials only when those integrations are enabled. Hosted startup refuses to use the local JSON store when MongoDB is missing or unreachable.

### 3. Generate Knowledge Base Documents & 500+ Dataset
```bash
# Generate 20+ policy documents in PDF and DOCX
python sample_documents/generate_docs.py

# Generate 525+ unique complaints dataset
python sample_complaints/generate_dataset.py
```

### 4. Run Test Suite
```bash
pip install -r requirements-dev.txt
pytest -v
```

### 5. Launch the Application
```bash
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

- **Customer Portal**: `http://127.0.0.1:8000/`
- **Admin / Support Agent Workspace**: `http://127.0.0.1:8000/admin`
- **Knowledge Base & Versioning**: `http://127.0.0.1:8000/knowledge`
- **100+ Rules Matrix**: `http://127.0.0.1:8000/rules`
- **Analytics & SLA Reports**: `http://127.0.0.1:8000/analytics`

---

## 📊 Evaluation & Verification Summary

| Requirement | Target | Achieved | Status |
| :--- | :--- | :--- | :--- |
| Unique Customer Complaints | >= 500 | **525** | ✅ Pass |
| Complaint Categories | >= 10 | **12** | ✅ Pass |
| Complaint Subcategories | >= 20 | **26** | ✅ Pass |
| Responsible Departments | >= 8 | **10** | ✅ Pass |
| Policy & SOP Documents | >= 20 | **21 (PDF & DOCX)** | ✅ Pass |
| Structured Resolution Rules | >= 100 | **105 Rules** | ✅ Pass |
| Mandatory Escalation Conditions | >= 30 | **34 Conditions** | ✅ Pass |
| Prompt Injection Test Cases | >= 20 | **25 Cases** | ✅ Pass |
| Automated Test Suite | All Passing | **Not yet verified in this environment** | ⏳ Run the current test suite before submission |
