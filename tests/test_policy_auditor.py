from src.knowledge_base import policy_auditor


class Collection:
    def __init__(self, records):
        self.records = records

    def find(self, query):
        return list(self.records)


def test_policy_audit_uses_indexed_records_and_does_not_claim_semantic_scan(monkeypatch):
    documents = Collection([{"document_id": "POL-REF-02", "status": "Active"}])
    chunks = Collection([{"chunk_id": "POL-REF-02-CHK-001"}])
    monkeypatch.setattr(policy_auditor, "ALL_RULES", [{"policy_id": "POL-REF-02"}, {"policy_id": "POL-DEL-04"}])
    monkeypatch.setattr("config.database.get_knowledge_col", lambda: documents)
    monkeypatch.setattr("config.database.get_chunks_col", lambda: chunks)

    result = policy_auditor.PolicyConflictAuditor.audit_all_policies()

    assert result["total_policies_scanned"] == 1
    assert result["total_chunks_evaluated"] == 1
    assert result["total_rules_cross_referenced"] == 2
    assert result["governance_health_score"] is None
    assert result["conflicts"][0]["topic"] == "POL-DEL-04"
    assert "semantic" in result["score_note"].lower()
