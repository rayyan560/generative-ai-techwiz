import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from config.database import get_chunks_col, get_knowledge_col
from routers.common import clean_docs
from src.complaint_rules.matrix import RuleMatrixManager
from src.document_processing.parser import DocumentParser
from src.document_processing.validation import (
    MAX_DOCUMENT_BYTES,
    document_fingerprint,
    validate_document_file,
    validate_document_metadata,
)
from src.knowledge_base.manager import rebuild_vector_index
from src.security.permissions import require_roles


router = APIRouter(
    prefix="/api",
    tags=["Knowledge Base & RAG Rules"],
    dependencies=[Depends(require_roles("admin", "agent", "warranty_manager"))],
)


@router.post("/knowledge/upload", dependencies=[Depends(require_roles("admin"))])
async def upload_policy_document(
    file: UploadFile = File(...),
    category: str = Form("General"),
    version: str = Form("v2.0"),
    status: str = Form("Active"),
    document_id: str = Form(""),
    effective_date: str = Form(""),
    expiry_date: str = Form(""),
):
    filename = file.filename or ""
    content_bytes = await file.read(MAX_DOCUMENT_BYTES + 1)
    try:
        suffix = validate_document_file(filename, content_bytes)
        metadata = validate_document_metadata(
            filename,
            document_id,
            version,
            status,
            effective_date,
            expiry_date,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    category = category.strip()
    if not category or len(category) > 80:
        raise HTTPException(status_code=400, detail="Enter a valid document category.")

    knowledge_col = get_knowledge_col()
    chunks_col = get_chunks_col()
    if knowledge_col.find_one({"document_id": metadata["document_id"], "version": metadata["version"]}):
        raise HTTPException(status_code=409, detail="That document ID and version are already indexed.")

    fingerprint = document_fingerprint(content_bytes)
    if knowledge_col.find_one({"content_sha256": fingerprint}):
        raise HTTPException(status_code=409, detail="An identical document is already indexed.")

    try:
        if suffix == ".pdf":
            chunks = DocumentParser.parse_pdf_content(content_bytes, filename, metadata["document_id"], metadata["version"])
        elif suffix == ".docx":
            chunks = DocumentParser.parse_docx_content(content_bytes, filename, metadata["document_id"], metadata["version"])
        else:
            text = content_bytes.decode("utf-8")
            chunks = DocumentParser.parse_plain_text(text, filename, metadata["document_id"], metadata["version"])
    except (RuntimeError, UnicodeDecodeError) as error:
        raise HTTPException(status_code=400, detail="The selected document could not be parsed.") from error

    if not chunks:
        raise HTTPException(status_code=400, detail="The document contains no extractable text.")

    document = {
        **metadata,
        "filename": filename,
        "title": filename.rsplit(".", 1)[0].replace("_", " ").title(),
        "category": category,
        "doc_type": "Policy / SOP",
        "content_sha256": fingerprint,
        "total_chunks": len(chunks),
        "chunk_ids": [chunk["chunk_id"] for chunk in chunks],
        "uploaded_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    for chunk in chunks:
        chunk["status"] = metadata["status"]
        chunk["version"] = metadata["version"]
        chunk["effective_date"] = metadata["effective_date"]
        chunk["expiry_date"] = metadata["expiry_date"]
        chunks_col.insert_one(chunk)

    knowledge_col.insert_one(document)
    if metadata["status"] == "Active":
        active_versions = list(knowledge_col.find({"document_id": metadata["document_id"], "status": "Active"}))
        for previous in active_versions:
            if previous.get("version") == metadata["version"]:
                continue
            previous_version = previous.get("version")
            knowledge_col.update_one(
                {"document_id": metadata["document_id"], "version": previous_version},
                {"$set": {"status": "Superseded"}},
            )
            previous_chunk_ids = set(previous.get("chunk_ids", []))
            for previous_chunk in chunks_col.find({"document_id": metadata["document_id"]}):
                if previous_chunk.get("version") == previous_version or previous_chunk.get("chunk_id") in previous_chunk_ids:
                    chunks_col.update_one(
                        {"chunk_id": previous_chunk.get("chunk_id")},
                        {"$set": {"status": "Superseded"}},
                    )

    rebuild_vector_index()
    return {"success": True, "document_id": metadata["document_id"], "chunks_created": len(chunks)}
