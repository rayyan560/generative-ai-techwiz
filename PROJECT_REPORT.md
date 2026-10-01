# SupportNova - Comprehensive Project Report
**Techwiz 7: The World Tech Championship**  
**Theme:** ResponseX Intelligence | **Category:** Generative AI PowerPlay  
**Organization:** NovaTech Global Commerce & Electronics  
**Version:** 1.0 (Development Snapshot; not a production-readiness certification)

---

## 1. Problem Definition & Industry Background

Customer service teams in omnichannel enterprises receive tens of thousands of complaints each month across web forms, emails, chat systems, and customer service portals. These complaints range from simple tracking queries to critical life-safety hazards (e.g., lithium battery swelling or electrical short-circuits) and sensitive legal threats.

Traditional complaint handling suffers from severe bottlenecks:
1. **Manual Triage Delays**: Customer service agents spend 10–25 minutes reading, categorizing, looking up policy documents, and identifying the correct department.
2. **Inconsistent Policy Enforcement**: Human agents frequently misinterpret refund windows (e.g. applying obsolete 14-day rules instead of active 30-day rules) or offer unauthorized goodwill compensations.
3. **Overlooked Critical Safety & Escalation Triggers**: Frontline agents often fail to recognize high-risk safety warnings (such as battery expansion) or legal risks hidden in unstructured text.
4. **The "Raw LLM" Trap**: Deploying ungrounded Generative AI directly to customers creates massive risks of hallucinated policies, unauthorized financial promises, and prompt injection exploits.

---

## 2. Proposed Solution: Dual-Pipeline Architecture

SupportNova solves this with an enterprise-grade **Dual-Pipeline Architecture**:
- **Pipeline 1 (GenAI Complaint Intelligence Pipeline)**: Integrates with configured Google Gemini API keys using bounded rotation. Provider outages do not generate synthetic GenAI findings; affected cases are routed to human review while deterministic Python ground truth remains available.
- **Pipeline 2 (Python Ground-Truth Validation Pipeline)**: An independent deterministic Python validation engine with **175 complaint rules**, **34 named escalation conditions**, and the project policy library.
- **Comparison & Verification Engine**: Measures alignment between GenAI output and Ground Truth. It calculates a **Mandatory Policy Coverage Score %**, **Source Traceability Score %**, and flags unauthorized promises, policy contradictions, and prompt injections.
- **Customer Privacy & Trust Preservation**: The customer portal presents an official, authoritative ticket submission and tracking experience with zero internal AI bot disclosure. The dual-pipeline acts exclusively as an internal intelligence and decision-support layer for support agents and supervisors.

---

## 3. System Architecture & Component Design

```
                                  ┌───────────────────────────────┐
                                  │ Customer Intake / Web Form    │
                                  └───────────────┬───────────────┘
                                                  │
                                                  ▼
                                  ┌───────────────────────────────┐
                                  │ Preprocessing & Sanitization  │
                                  │ • Entity Regex Extractor      │
                                  │ • Duplicate Hash Detector     │
                                  │ • Prompt Injection Defense    │
                                  └───────────────┬───────────────┘
                                                  │
                         ┌────────────────────────┴────────────────────────┐
                         ▼                                                 ▼
        ┌──────────────────────────────────┐             ┌──────────────────────────────────┐
        │ Pipeline 1: GenAI Intelligence   │             │ Pipeline 2: Ground-Truth Engine  │
        │ • Configurable Gemini API Keys   │             │ • 175 Rules Matrix               │
        │ • Structured Pydantic Output     │             │ • 34 Named Escalation Conditions │
        │ • Sentiment & Entity Detection   │             │ • Policy Precedence Hierarchy    │
        │ • Policy Retrieval Grounding     │             │ • Prohibited Action Constraints  │
        └────────────────┬─────────────────┘             └────────────────┬─────────────────┘
                         │                                                 │
                         └────────────────────────┬────────────────────────┘
                                                  ▼
                                  ┌───────────────────────────────┐
                                  │ Comparison & Scoring Engine   │
                                  │ • Mandatory Coverage Score %  │
                                  │ • Source Traceability Score % │
                                  │ • Consistency Index %         │
                                  │ • Hallucination Defense       │
                                  └───────────────┬───────────────┘
                                                  │
                         ┌────────────────────────┴────────────────────────┐
                         ▼                                                 ▼
        ┌──────────────────────────────────┐             ┌──────────────────────────────────┐
        │ Verified Case -> Auto Queue      │             │ Conflict / P0 -> Manual Review   │
        └──────────────────────────────────┘             └──────────────────────────────────┘
```

---

## 4. Database Schema & Data Models

SupportNova connects to MongoDB Atlas through `MONGODB_URI` in hosted deployments. The local JSON store is for local development; hosted startup refuses to fall back to ephemeral storage. Neither behavior guarantees 100% uptime; deployment persistence depends on the host's storage configuration.

### Key Collections:
1. `complaints`: Stores full complaint submissions, entity metadata, customer tier, GenAI intelligence output, Python Ground-Truth result, and comparison verdict.
2. `knowledge_documents`: Stores 21 active & superseded company policies and SOPs with version control metadata and precedence scores.
3. `document_chunks`: Traceable chunk collection indexed by `document_id`, `section_id`, `heading`, and page numbers.
4. `rule_matrix`: 175 deterministic complaint resolution rules.
5. `escalation_rules`: 34 named escalation conditions and thresholds.
6. `audit_logs`: Application audit records for selected automated triage and manual agent actions; immutability is not guaranteed.

---

## 5. Security & Prompt Injection Defense

SupportNova treats all customer-submitted text and file attachments as **untrusted data**.
1. **Fencing Wrappers**: Complaint inputs are framed within strict markdown boundary fencing (`<<<UNTRUSTED_TEXT_START>>>`).
2. **Regex Pattern Inspection**: `PromptDefense` scans input for 15+ prompt injection vectors (`"ignore previous instructions"`, `"system override"`, `"jailbreak"`, `"dan mode"`, `"grant admin access"`).
3. **Adversarial Compensation Trap Mitigation**: Prohibits GenAI models from executing customer demands for unauthorized refunds or financial compensation.

---

## 6. Verification Metrics & Compliance Audit

| Requirement | Specification Target | SupportNova Achieved | Verification Status |
| :--- | :--- | :--- | :--- |
| Unique Customer Complaints | >= 500 | **528 Unique Cases** | ✅ Meets target |
| Complaint Categories | >= 10 | **12 Categories** | ✅ Meets target |
| Complaint Subcategories | >= 20 | **26 Subcategories** | ✅ Meets target |
| Responsible Departments | >= 8 | **10 Departments** | ✅ Meets target |
| Policy Documents (PDF/DOCX) | >= 20 | **21 Documents (42 files)** | ✅ Meets target |
| Resolution Rules Matrix | >= 100 | **175 Ground-Truth Rules** | ✅ Meets target |
| Mandatory Escalations | >= 30 | **34 Conditions** | ✅ Meets target |
| Prompt Injection Test Cases | >= 20 | **25 Cases** | ✅ Meets target |
| Automated Test Suite | All Passing | **75 passed** | ✅ Verified locally on October 2, 2026; provider-backed and browser interaction tests remain separate |

---

## 7. Conclusion

SupportNova demonstrates a design for combining generative analysis with deterministic review controls. This development snapshot does not certify zero hallucinations, zero vulnerabilities, production reliability, or live provider performance. The complaint tracker is an initial React component; the remaining dashboards still use server-rendered HTML and JavaScript, so the full React-component requirement in `docs/rules.md` remains unmet.
