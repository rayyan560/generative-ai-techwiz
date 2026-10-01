from datetime import date
from typing import Any, Dict, List

from src.complaint_rules.matrix import ALL_RULES


class PolicyConflictAuditor:
    @classmethod
    def audit_all_policies(cls) -> Dict[str, Any]:
        from config.database import get_chunks_col, get_knowledge_col

        documents = list(get_knowledge_col().find({}))
        chunks = list(get_chunks_col().find({}))
        today = date.today().isoformat()
        active_documents = {
            str(doc.get("document_id", "")).strip().upper(): doc
            for doc in documents
            if doc.get("status", "Active") == "Active"
            and (not doc.get("effective_date") or str(doc["effective_date"]) <= today)
            and (not doc.get("expiry_date") or str(doc["expiry_date"]) >= today)
        }
        referenced_policy_ids = {
            str(rule.get("policy_id", "")).strip().upper()
            for rule in ALL_RULES
            if rule.get("policy_id")
        }
        missing_ids = sorted(referenced_policy_ids - active_documents.keys())
        findings: List[Dict[str, Any]] = []
        for index, policy_id in enumerate(missing_ids, start=1):
            findings.append({
                "conflict_id": f"REF-{index:03d}",
                "severity": "HIGH",
                "category": "Policy traceability",
                "topic": policy_id,
                "clause_a_ref": "Rule matrix",
                "clause_a_text": f"Rules reference {policy_id}.",
                "clause_b_ref": "Active knowledge base",
                "clause_b_text": "No currently valid Active document with this ID is indexed.",
                "resolution_guideline": "Index the approved source policy or correct the rule reference.",
                "precedence_winner": "Not determined",
            })

        expired_ids = sorted({
            str(doc.get("document_id", ""))
            for doc in documents
            if doc.get("status", "Active") == "Active"
            and doc.get("expiry_date")
            and str(doc["expiry_date"]) < today
        })
        for policy_id in expired_ids:
            findings.append({
                "conflict_id": f"EXP-{len(findings) + 1:03d}",
                "severity": "HIGH",
                "category": "Document validity",
                "topic": policy_id,
                "clause_a_ref": "Indexed metadata",
                "clause_a_text": f"{policy_id} is marked Active.",
                "clause_b_ref": "Expiry date",
                "clause_b_text": "Its recorded expiry date has passed.",
                "resolution_guideline": "Review the document and update its status or expiry date.",
                "precedence_winner": "Not determined",
            })

        return {
            "total_policies_scanned": len(documents),
            "total_chunks_evaluated": len(chunks),
            "total_rules_cross_referenced": len(ALL_RULES),
            "conflicts_detected": len(findings),
            "governance_health_score": None,
            "score_note": "A governance score is not calculated; semantic policy contradictions are not evaluated.",
            "conflicts": findings,
        }
