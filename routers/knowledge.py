from fastapi import APIRouter, Request, HTTPException, Form, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import datetime
import logging

from config.database import get_knowledge_col, get_chunks_col
from src.document_processing.parser import DocumentParser
from src.knowledge_base.manager import KnowledgeBaseManager, rebuild_vector_index
from src.knowledge_base.policy_auditor import PolicyConflictAuditor
from src.complaint_rules.matrix import RuleMatrixManager
from routers.common import clean_doc, clean_docs
from src.security.permissions import require_roles

logger = logging.getLogger("SupportNova.KnowledgeRouter")

router = APIRouter(
    prefix="/api",
    tags=["Knowledge Base & RAG Rules"],
    dependencies=[Depends(require_roles("admin", "agent", "warranty_manager"))]
)

@router.post("/knowledge/upload")
async def upload_policy_document(
    file: UploadFile = File(...),
    category: str = Form("General"),
    version: str = Form("v2.0"),
    status: str = Form("Active")
):
    content_bytes = await file.read()
    fname = file.filename
    doc_id = f"POL-{fname.split('.')[0].upper()[:10]}"
    
    if fname.endswith(".pdf"):
        chunks = DocumentParser.parse_pdf_content(content_bytes, fname, doc_id, version)
    elif fname.endswith(".docx"):
        chunks = DocumentParser.parse_docx_content(content_bytes, fname, doc_id, version)
    else:
        text = content_bytes.decode("utf-8", errors="ignore")
        chunks = DocumentParser.parse_plain_text(text, fname, doc_id, version)

    knowledge_col = get_knowledge_col()
    chunks_col = get_chunks_col()

    doc_record = {
        "document_id": doc_id,
        "filename": fname,
        "title": fname.split(".")[0].replace("_", " ").title(),
        "category": category,
        "version": version,
        "status": status,
        "total_chunks": len(chunks),
        "chunk_ids": [c["chunk_id"] for c in chunks],
        "uploaded_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    knowledge_col.insert_one(doc_record)
    
    for c in chunks:
        c["status"] = status
        chunks_col.insert_one(c)

    # Rebuild FAISS index upon upload
    rebuild_vector_index()

    return {"success": True, "document_id": doc_id, "chunks_created": len(chunks)}

@router.get("/rules/list")
async def list_rules():
    return {"rules": RuleMatrixManager.get_all_rules(), "total": len(RuleMatrixManager.get_all_rules())}

@router.get("/knowledge/list")
async def list_knowledge_docs():
    knowledge_col = get_knowledge_col()
    chunks_col = get_chunks_col()
    return {
        "documents": clean_docs(list(knowledge_col.find())),
        "total_chunks": chunks_col.count_documents({})
    }

@router.get("/knowledge/document/{doc_id}")
async def get_knowledge_doc_details(doc_id: str):
    knowledge_col = get_knowledge_col()
    chunks_col = get_chunks_col()
    
    clean_id = doc_id.strip()
    doc = knowledge_col.find_one({"document_id": clean_id})
    if not doc:
        all_docs = list(knowledge_col.find())
        for d in all_docs:
            if d.get("document_id", "").lower() == clean_id.lower():
                doc = d
                break
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    chunks = list(chunks_col.find({"document_id": doc.get("document_id")}))
    cleaned = clean_doc(doc)
    cleaned["chunks"] = clean_docs(chunks)
    return cleaned

@router.get("/knowledge/query")
async def query_knowledge_rag(category: str = "", query: str = "", top_k: int = 3):
    chunks = KnowledgeBaseManager.retrieve_relevant_policy_chunks(category=category, query=query, top_k=top_k)
    return {"query": query, "category": category, "chunks": clean_docs(chunks), "total_retrieved": len(chunks)}

@router.get("/knowledge/conflicts")
async def get_policy_conflicts():
    return PolicyConflictAuditor.audit_all_policies()
