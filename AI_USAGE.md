# AI Tool Usage Declaration (AI_USAGE.md)

**Project Name:** SupportNova - ResponseX Intelligence  
**Competition:** Techwiz 7 - Aptech World Tech Championship  
**Category:** Generative AI PowerPlay  
**Date:** September 2026  

---

## 1. Declarations & Compliance Summary

In compliance with Section 1.8 (Competition Integrity & Anti-Shortcut Requirements) and Section 1.10 (Project Deliverables) of the Techwiz 7 Specification, this document records all Generative AI API integrations, prompt engineering structures, model parameters, and development assistance used in SupportNova.

| Field | Description |
| :--- | :--- |
| **Primary GenAI Provider** | Google Gemini API (`gemini-1.5-flash` / `gemini-1.5-pro`) |
| **API Architecture** | Multi-Key Load Balancer & Automatic Fallback Rotation (3 Keys) |
| **Independent Validation Pipeline** | 100% Deterministic Python Ground-Truth Rule Engine (No AI in Pipeline 2) |
| **Ground-Truth Rules Enforced** | 105+ Rules in Complaint Resolution Matrix & 32+ Escalation Conditions |

---

## 2. Granular Module AI Assistance & Validation Audit

### Module 1: GenAI Complaint Intelligence Pipeline (`src/genai_pipeline/pipeline.py`)
- **Tool / Model**: Google Gemini 1.5 Flash (`AQ.Ab8RN...` Key Pool)
- **Purpose**: Autonomous analysis of unstructured customer complaints, primary & secondary issue extraction, sentiment analysis, entity parsing, draft response generation, and agent resolution guidance.
- **Type of Assistance**: Natural Language Understanding and structured JSON schema generation.
- **Files Affected**:
  - `src/genai_pipeline/pipeline.py`
  - `src/prompt_templates/templates.py`
  - `src/schemas/models.py`
- **Modifications & Safety Controls Implemented**:
  - Untrusted data fencing (`<<<UNTRUSTED_TEXT_START>>>`) to mitigate prompt injection attacks.
  - Strict Pydantic JSON schema parser with automatic retry and JSON fence extraction.
  - Fallback synthesizer ensuring 100% uptime if external API quotas are exhausted.
- **Tests Performed**: `tests/test_genai_pipeline.py` (Structured JSON output validation, multi-field verification).
- **Verified By**: SupportNova Engineering Team.

---

### Module 2: Deterministic Python Ground-Truth Pipeline (`src/python_validation/pipeline.py`)
- **Tool / Methodology**: Pure Python Deterministic Rule Engine (No AI model).
- **Purpose**: Independent verification of GenAI classifications against corporate business rules, department routing matrices, refund/replacement eligibility, and mandatory escalation triggers.
- **Files Affected**:
  - `src/python_validation/pipeline.py`
  - `src/complaint_rules/matrix.py`
  - `src/escalation_rules/manager.py`
  - `src/routing_rules/router.py`
- **Tests Performed**: `tests/test_python_validation.py`, `tests/test_sla_and_routing.py`.
- **Verified By**: SupportNova QA Directorate.

---

### Module 3: Comparison & Hallucination Defense Engine (`src/comparison_engine/engine.py`)
- **Tool / Methodology**: Rule-based similarity, policy precedence hierarchy, and promise regex scanner.
- **Purpose**: Compares GenAI recommendations with Ground Truth; calculates Mandatory Policy Coverage Score %, Source Traceability Score %, and flags unauthorized promises (e.g. unverified refund promises).
- **Files Affected**:
  - `src/comparison_engine/engine.py`
  - `src/hallucination_checks/detector.py`
  - `src/security/prompt_defense.py`
- **Tests Performed**: `tests/test_comparison_engine.py`, `tests/test_security_injection.py`.
- **Verified By**: SupportNova Security Team.

---

### Module 4: Knowledge Base & Document Processing (`src/document_processing/parser.py`)
- **Tool / Libraries**: PyMuPDF (`fitz`), `python-docx`, `reportlab`.
- **Purpose**: Parsing PDF and DOCX company policies into traceable chunks with document ID, section numbers, and version controls (Active vs Superseded).
- **Files Affected**:
  - `src/document_processing/parser.py`
  - `src/knowledge_base/manager.py`
  - `sample_documents/generate_docs.py`
- **Tests Performed**: Ingestion and parsing of 21 generated DOCX and PDF policy files.
- **Verified By**: SupportNova Architecture Review Board.

---

## 3. Team Verification Sign-Off

All AI-generated recommendations and system outputs are strictly guarded by deterministic validation layers, preventing unauthorized commitments, policy bypasses, or hallucinated claims from reaching end users.
