from datetime import date

from src.knowledge_base.policy_versions import resolve_policy_metadata


def test_policy_metadata_selects_highest_current_active_version():
    documents = [
        {"document_id": "POL-REF-02", "version": "v1.0", "status": "Superseded"},
        {"document_id": "POL-REF-02", "version": "v2.0", "status": "Active", "effective_date": "2026-01-01"},
        {"document_id": "POL-REF-02", "version": "v3.0", "status": "Active", "effective_date": "2026-03-01"},
    ]

    assert resolve_policy_metadata("POL-REF-02", documents, date(2026, 10, 1)) == ("v3.0", "Active")


def test_policy_metadata_rejects_expired_and_future_active_versions():
    expired = [{"document_id": "POL-A", "version": "v2", "status": "Active", "expiry_date": "2026-09-30"}]
    future = [{"document_id": "POL-B", "version": "v3", "status": "Active", "effective_date": "2026-10-02"}]

    assert resolve_policy_metadata("POL-A", expired, date(2026, 10, 1)) == ("v2", "Expired")
    assert resolve_policy_metadata("POL-B", future, date(2026, 10, 1)) == ("v3", "Not Yet Effective")


def test_policy_metadata_reports_missing_or_malformed_sources():
    malformed = [{"document_id": "POL-C", "version": "v1", "status": "Active", "expiry_date": "not-a-date"}]

    assert resolve_policy_metadata("POL-MISSING", [], date(2026, 10, 1)) == ("Unknown", "Missing")
    assert resolve_policy_metadata("POL-C", malformed, date(2026, 10, 1)) == ("v1", "Invalid Metadata")
