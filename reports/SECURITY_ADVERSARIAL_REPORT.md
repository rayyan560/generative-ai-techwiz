# Security and Adversarial Testing Report

**Project:** SupportNova - ResponseX Intelligence
**Verification date:** October 2, 2026
**Scope:** Repository-local prompt-injection and access-control checks. This report is not an external penetration-test certificate.

## Prompt-injection corpus

The bundled complaint corpus contains 25 cases marked adversarial. The detector is also run against ordinary, non-repeat examples to check for obvious false positives. The corpus has 30 repeated submissions; 17 contain adversarial text, so all repeated cases are kept separate from the ordinary-sample check.

| Check | Result | Evidence |
| :--- | :--- | :--- |
| Marked adversarial examples detected | 25 / 25 | `tests/test_srs_dataset_coverage.py` |
| Ordinary non-repeat examples not flagged | 473 / 473 | `tests/test_srs_dataset_coverage.py` |
| Repeated complaint examples | 30 total; 17 contain adversarial text | Dataset `issue_type` and detector scan |
| Prompt-defense focused tests | 5 | `tests/test_security_injection.py` |

The detector covers instruction override and policy-disregard language, requests to expose prompts or API keys, hidden system/developer blocks, SQL-like destructive commands and compensation traps. Prompt text and retrieved policy content are fenced as untrusted data; delimiter breakout markers are sanitized. Suspicious complaint text is stopped before policy retrieval or any Gemini call; suspicious retrieved policy content also fails closed to manual review. The provider-call boundary is tested in `tests/test_genai_pipeline.py` without making a live request.

## Other relevant controls

- `tests/test_complaint_tracking_privacy.py` verifies that complaint tracking is scoped to the owner identity.
- `tests/test_chatbot_websocket_access.py` verifies access restrictions for the staff websocket.
- `tests/test_public_demo_access.py` checks public demo authorization and judge read-only behavior.
- The full local automated suite is recorded in `PROJECT_REPORT.md`; it does not represent a third-party security review.

## Limitations

- Regex and dataset coverage cannot detect every novel, obfuscated or multilingual attack.
- No live Gemini red-team run, independent penetration test, production security scan or external reviewer sign-off is claimed.
- Production readiness still depends on secure secret handling, database access controls, deployment configuration and human review of consequential decisions.
- Re-run the focused tests and conduct an independent security review after changes to prompt templates, policies, role checks or model providers.
