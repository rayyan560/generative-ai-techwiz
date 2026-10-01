# SupportNova - ResponseX Intelligence Platform
**Aptech Techwiz 7 | Category: Generative AI PowerPlay**  
*Enterprise Customer Complaint Intelligence & Dual-Pipeline Ground-Truth Validation System*

---

## 🌟 Executive Summary

SupportNova is an AI-powered enterprise complaint triage and ground-truth validation solution built for **NovaTech Global Commerce & Electronics**. Traditional complaint resolution often suffers from delayed routing, inconsistent policy interpretation, and manual bottlenecks. SupportNova resolves this with a dual-pipeline architecture:

1. **Pipeline 1 (GenAI Complaint Intelligence)**: Uses the configured Google Gemini model (default `gemini-3.8-flash`) with bounded key rotation to analyze complaints and produce structured agent-assist recommendations. Provider failure sends the case to manual review.
2. **Pipeline 2 (Deterministic Python Ground-Truth Validation)**: An independent Python rule engine that checks recommendations against **175 complaint rules**, **34 named escalation conditions**, and the policy library.
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
            • Configurable Gemini API Key Rotation                                                     • 175 Complaint Resolution Rules Matrix
            • Sentiment & Emotion Analysis                                                             • 34 Named Escalation Conditions
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
                                                       • Agent Review & Decision Logging
                                                       • Call Request Signaling (audio not connected)
                                                       • Dashboard Analytics & CSV Export
```

---

## 🚀 Key Features

- **528 Unique Pre-seeded Complaints**: Covers simple, multi-issue, high-risk safety, calm-critical, prompt injections, and duplicate resubmissions.
- **20+ Parsed Policies & SOPs (PDF & DOCX)**: Ingested using PyMuPDF and python-docx with section chunking, heading extraction, and version status (Active vs Superseded).
- **175 Ground-Truth Rules**: Deterministic mappings across 12 complaint categories and configured departments.
- **34 Escalation Conditions**: Named safety, legal, privacy, financial, and operational triggers; staff must verify outcomes.
- **Adversarial & Prompt Injection Defense**: Neutralizes attempts to bypass refund policies or extract system prompts.
- **Repeat Complaint Review**: Exact/near-duplicate checks are scoped to the same customer; unresolved repeat history drives Python escalation at three total attempts.
- **MongoDB Atlas + Local Development Store**: Hosted deployments require a configured MongoDB URI; local JSON storage is for development only.
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

The customer complaint tracker is a React component. To rebuild its static browser bundle after editing the frontend:
```bash
cd frontend
npm ci
npm run build
```

For local-only demo accounts, copy `.env.example` to `.env` and set `DEMO_MODE=true`. Never enable demo mode on a public deployment. For hosted use, configure `MONGODB_URI`, `SESSION_SECRET_KEY`, `ADMIN_EMAIL`, and a strong `ADMIN_PASSWORD` in the host's private variables. Configure `GEMINI_API_KEYS` and Google OAuth credentials only when those integrations are enabled. Hosted startup refuses to use the local JSON store when MongoDB is missing or unreachable.

### 3. Generate Knowledge Base Documents & 500+ Dataset
```bash
# Generate 20+ policy documents in PDF and DOCX
python sample_documents/generate_docs.py

# Generate 528 unique complaints dataset
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
- **175 Rules Matrix**: `http://127.0.0.1:8000/rules`
- **Analytics & SLA Reports**: `http://127.0.0.1:8000/analytics`

---

## 📊 Evaluation & Verification Summary

| Requirement | Target | Achieved | Status |
| :--- | :--- | :--- | :--- |
| Unique Customer Complaints | >= 500 | **528** | ✅ Pass |
| Complaint Categories | >= 10 | **12** | ✅ Pass |
| Complaint Subcategories | >= 20 | **26** | ✅ Pass |
| Responsible Departments | >= 8 | **10** | ✅ Pass |
| Policy & SOP Documents | >= 20 | **21 (PDF & DOCX)** | ✅ Pass |
| Structured Resolution Rules | >= 100 | **175 Rules** | ✅ Pass |
| Mandatory Escalation Conditions | >= 30 | **34 Conditions** | ✅ Pass |
| Prompt Injection Test Cases | >= 20 | **25 Cases** | ✅ Pass |
| Automated Test Suite | All Passing | **60 passed** | ✅ Verified locally on October 1, 2026; browser interactions and live-provider behavior need separate verification |
