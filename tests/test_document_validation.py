import io
import zipfile
import asyncio
from datetime import date

import pytest
from fastapi import HTTPException, UploadFile

from src.document_processing.validation import (
    document_fingerprint,
    validate_document_file,
    validate_document_metadata,
)


def test_valid_pdf_signature_and_metadata():
    assert validate_document_file("policy.pdf", b"%PDF-1.7 sample") == ".pdf"
    metadata = validate_document_metadata("policy.pdf", "", "v2.1", "Active", "", "")
    assert metadata["document_id"] == "POLICY"
    assert metadata["effective_date"] == date.today().isoformat()


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("policy.exe", b"text"),
        ("policy.pdf", b"not a PDF"),
        ("policy.txt", b"\xff"),
        ("policy.txt", b"\x00"),
        ("../policy.txt", b"text"),
        ("policy.txt", b""),
    ],
)
def test_rejects_invalid_document_files(filename, content):
    with pytest.raises(ValueError):
        validate_document_file(filename, content)


def test_accepts_docx_and_rejects_corrupt_docx():
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("word/document.xml", "<document/>")
    assert validate_document_file("policy.docx", output.getvalue()) == ".docx"
    with pytest.raises(ValueError, match="valid DOCX"):
        validate_document_file("policy.docx", b"not a zip")


def test_rejects_invalid_metadata_and_expiry_order():
    with pytest.raises(ValueError, match="version"):
        validate_document_metadata("policy.txt", "POLICY", "bad version", "Active", "", "")
    with pytest.raises(ValueError, match="earlier"):
        validate_document_metadata("policy.txt", "POLICY", "v1", "Active", "2025-01-02", "2025-01-01")


def test_fingerprint_is_stable_and_content_sensitive():
    assert document_fingerprint(b"policy") == document_fingerprint(b"policy")
    assert document_fingerprint(b"policy") != document_fingerprint(b"other")


def test_upload_persists_document_once_with_traceable_metadata(monkeypatch):
    from routers import knowledge

    class Collection:
        def __init__(self):
            self.records = []

        def find_one(self, criteria):
            return next((record for record in self.records if all(record.get(key) == value for key, value in criteria.items())), None)

        def insert_one(self, record):
            self.records.append(dict(record))

    documents = Collection()
    chunks = Collection()
    monkeypatch.setattr(knowledge, "get_knowledge_col", lambda: documents)
    monkeypatch.setattr(knowledge, "get_chunks_col", lambda: chunks)
    monkeypatch.setattr(knowledge, "rebuild_vector_index", lambda: None)
    monkeypatch.setattr(
        knowledge.DocumentParser,
        "parse_plain_text",
        lambda text, filename, document_id, version: [{
            "chunk_id": f"{document_id}-CHK-001",
            "document_id": document_id,
            "content": text,
        }],
    )

    async def upload():
        result = await knowledge.upload_policy_document(
            file=UploadFile(filename="policy.txt", file=io.BytesIO(b"Refund policy text")),
            category="Refund Request",
            version="v1",
            status="Active",
            document_id="POL-REF-TEST",
            effective_date="2025-01-01",
            expiry_date="",
        )
        assert result["chunks_created"] == 1
        assert len(documents.records) == 1
        assert len(chunks.records) == 1
        assert chunks.records[0]["content"] == "Refund policy text"
        assert chunks.records[0]["effective_date"] == "2025-01-01"
        with pytest.raises(HTTPException) as duplicate:
            await knowledge.upload_policy_document(
                file=UploadFile(filename="policy.txt", file=io.BytesIO(b"Refund policy text")),
                category="Refund Request",
                version="v1",
                status="Active",
                document_id="POL-REF-TEST",
                effective_date="2025-01-01",
                expiry_date="",
            )
        assert duplicate.value.status_code == 409

    asyncio.run(upload())
