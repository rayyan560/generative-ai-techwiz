from src.knowledge_base.manager import filter_current_policy_chunks, keyword_policy_search


def test_policy_retrieval_excludes_draft_expired_and_future_chunks():
    chunks = [
        {"document_id": "POL-A", "content": "Active current policy", "status": "Active", "effective_date": "2026-01-01"},
        {"document_id": "POL-B", "content": "Expired policy", "status": "Active", "expiry_date": "2026-09-30"},
        {"document_id": "POL-C", "content": "Future policy", "status": "Active", "effective_date": "2026-10-02"},
        {"document_id": "POL-D", "content": "Draft policy", "status": "Draft"},
    ]

    result = filter_current_policy_chunks(chunks, "2026-10-01")

    assert [chunk["document_id"] for chunk in result] == ["POL-A"]


def test_policy_retrieval_prefers_one_pdf_copy_when_pdf_and_docx_are_both_indexed():
    chunks = [
        {"document_id": "POL-DUP", "version": "v2", "document_name": "policy.docx", "content": "DOCX copy", "status": "Active"},
        {"document_id": "POL-DUP", "version": "v2", "document_name": "policy.pdf", "content": "PDF copy", "status": "Active"},
    ]

    result = filter_current_policy_chunks(chunks, "2026-10-01")

    assert len(result) == 1
    assert result[0]["document_name"] == "policy.pdf"


def test_keyword_retrieval_ranks_chunks_by_query_term_overlap():
    chunks = [
        {"document_id": "POL-REF-01", "section_id": "1.0", "content": "Refund policy requires receipt verification."},
        {"document_id": "POL-DEL-02", "section_id": "2.0", "content": "Delivery delays and shipment tracking."},
        {"document_id": "POL-REF-03", "section_id": "3.0", "content": "Refund disputes require proof of transaction and review."},
    ]

    result = keyword_policy_search("refund transaction review", chunks, 2)

    assert [chunk["document_id"] for chunk in result] == ["POL-REF-03", "POL-REF-01"]
