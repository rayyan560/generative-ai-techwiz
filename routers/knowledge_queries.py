from fastapi import APIRouter, Depends, HTTPException

from config.database import get_chunks_col, get_knowledge_col
from routers.common import clean_doc, clean_docs
from src.complaint_rules.matrix import RuleMatrixManager
from src.knowledge_base.manager import KnowledgeBaseManager
from src.knowledge_base.policy_auditor import PolicyConflictAuditor
from src.security.permissions import require_roles


router = APIRouter(
    prefix="/api",
    tags=["Knowledge Base & RAG Rules"],
    dependencies=[Depends(require_roles("admin", "agent", "warranty_manager"))],
)


@router.get("/rules/list")
async def list_rules():
    rules = RuleMatrixManager.get_all_rules()
    return {"rules": rules, "total": len(rules)}


@router.get("/knowledge/list")
async def list_knowledge_docs():
    documents = clean_docs(list(get_knowledge_col().find()))
    total_chunks = get_chunks_col().count_documents({})
    return {"documents": documents, "total_chunks": total_chunks}


@router.get("/knowledge/document/{doc_id}")
async def get_knowledge_doc_details(doc_id: str):
    clean_id = doc_id.strip()
    knowledge_col = get_knowledge_col()
    document = knowledge_col.find_one({"document_id": clean_id})
    if not document:
        document = next(
            (item for item in knowledge_col.find() if item.get("document_id", "").lower() == clean_id.lower()),
            None,
        )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    chunks = list(get_chunks_col().find({"document_id": document.get("document_id")}))
    cleaned = clean_doc(document)
    cleaned["chunks"] = clean_docs(chunks)
    return cleaned


@router.get("/knowledge/query")
async def query_knowledge_rag(category: str = "", query: str = "", top_k: int = 3):
    chunks = KnowledgeBaseManager.retrieve_relevant_policy_chunks(category=category, query=query, top_k=top_k)
    return {"query": query, "category": category, "chunks": clean_docs(chunks), "total_retrieved": len(chunks)}


@router.get("/knowledge/conflicts")
async def get_policy_conflicts():
    return PolicyConflictAuditor.audit_all_policies()
