# AI Tool Usage Declaration (AI_USAGE.md)

**Project Name:** SupportNova - ResponseX Intelligence  
**Competition:** Techwiz 7 - Aptech World Tech Championship  
**Category:** Generative AI PowerPlay  
**Date:** October 1, 2026

---

## 1. Declarations & Compliance Summary

In compliance with Section 1.8 (Competition Integrity & Anti-Shortcut Requirements) and Section 1.10 (Project Deliverables) of the Techwiz 7 Specification, this document records all Generative AI API integrations, prompt engineering structures, model parameters, and development assistance used in SupportNova.

| Field | Description |
| :--- | :--- |
| **Primary GenAI Provider** | Google GenAI SDK; model configured with `GEMINI_MODEL` (`gemini-3.8-flash` by default) |
| **API Architecture** | Environment-configured key rotation; no API keys are stored in source control |
| **Independent Validation Pipeline** | 100% Deterministic Python Ground-Truth Rule Engine (No AI in Pipeline 2) |
| **Ground-Truth Rules Enforced** | 175 Complaint Resolution Rules & 34 Named Escalation Conditions |

OpenAI Codex was used for code review, implementation assistance, documentation corrections, and test authoring. Human project owners remain responsible for reviewing changes and the competition submission.

---

## 2. Granular Module AI Assistance & Validation Audit

### Module 1: GenAI Complaint Intelligence Pipeline (`src/genai_pipeline/pipeline.py`)
- **Tool / Model**: Google Gemini API (model selected through application configuration)
- **Purpose**: Autonomous analysis of unstructured customer complaints, primary & secondary issue extraction, sentiment analysis, entity parsing, draft response generation, and agent resolution guidance.
- **Type of Assistance**: Natural Language Understanding and structured JSON schema generation.
- **Files Affected**:
  - `src/genai_pipeline/pipeline.py`
  - `src/prompt_templates/templates.py`
  - `src/schemas/models.py`
  - `src/knowledge_base/policy_versions.py`
- **Modifications & Safety Controls Implemented**:
  - Untrusted data fencing (`<<<UNTRUSTED_TEXT_START>>>`) to mitigate prompt injection attacks.
  - Strict Pydantic JSON schema parser, bounded key rotation, and JSON fence extraction.
  - Current policy version, source metadata, model/provider, prompt version, and UTC analysis time are stored with generated output; suspicious instructions inside retrieved policy text fail closed to manual review.
  - Provider failures now result in manual review; no synthetic response is represented as GenAI output.
- **Tests Performed**: `tests/test_genai_pipeline.py` (provider-unavailable/manual-review and no-retrieved-policy behavior). The pipeline now requires retrieved policy chunks before sending a complaint to GenAI. This is not a live provider integration test.
- **Verification Status**: Automated provider-unavailable behavior is covered locally; live Gemini quality, credentials, rate limits, and production behavior were not tested.

---

### Module 2: Deterministic Python Ground-Truth Pipeline (`src/python_validation/pipeline.py`)
- **Tool / Methodology**: Pure Python Deterministic Rule Engine (No AI model).
- **Purpose**: Independent verification of GenAI classifications against corporate business rules, department routing matrices, refund/replacement eligibility, and mandatory escalation triggers.
- **Files Affected**:
  - `src/python_validation/pipeline.py`
  - `src/complaint_rules/matrix.py`
  - `src/escalation_rules/manager.py`
  - `src/routing_rules/router.py`
  - `src/complaint_processing/duplicates.py`
- **Tests Present**: `tests/test_python_validation.py` and `tests/test_srs_dataset_coverage.py`. They cover configured routing, current policy status, repeat attempts, and selected sample mappings; exhaustive SLA behavior is not covered.
- **Verification Status**: Local automated checks only; no independent QA sign-off is claimed.

---

### Module 3: Comparison & Hallucination Defense Engine (`src/comparison_engine/engine.py`)
- **Tool / Methodology**: Rule-based similarity, policy precedence hierarchy, and promise regex scanner.
- **Purpose**: Compares GenAI recommendations with Ground Truth; calculates Mandatory Policy Coverage Score %, Source Traceability Score %, and flags unauthorized promises (e.g. unverified refund promises).
- **Files Affected**:
  - `src/comparison_engine/engine.py`
  - `src/hallucination_checks/detector.py`
  - `src/security/prompt_defense.py`
- **Tests Performed**: `tests/test_comparison_engine.py`, `tests/test_security_injection.py`, and `tests/test_policy_versions.py`. Coverage and traceability are not defaulted to perfect when required actions or retrieved source/version evidence is missing; missing mandatory information without a clarification question requires review.
- **Verification Status**: Local automated tests cover selected comparison and prompt-injection cases; no independent security audit is claimed.

---

### Module 4: Knowledge Base & Document Processing (`src/document_processing/parser.py`)
- **Tool / Libraries**: `pypdf`, `python-docx`, `reportlab` (confirm installed versions from the environment before claiming a runtime test).
- **Purpose**: Parsing PDF and DOCX company policies into traceable chunks with document ID, section numbers, and version controls (Active vs Superseded).
- **Files Affected**:
  - `src/document_processing/parser.py`
  - `src/knowledge_base/manager.py`
  - `sample_documents/generate_docs.py`
- **Dataset**: 21 policy documents are present as PDF/DOCX artifacts. Tests cover upload validation and persistence with a mocked parser; extracted PDF/DOCX content still needs parser-fixture integration tests.
- **Verification Status**: Local unit and route-function checks only; no architecture-board sign-off is claimed.

---

## 3. Team Verification Sign-Off

No independent team-member verification sign-off is recorded in this repository; local automated checks are listed above and should not be presented as a human reviewer signature.

GenAI output must not be treated as available when the provider is unreachable. In that situation, the Python ground-truth result and human-review queue remain the supported path. The report CSV files in `reports/` are historical generated artifacts and are not verified evidence of a live Gemini evaluation; rerun them with configured credentials before submission.
