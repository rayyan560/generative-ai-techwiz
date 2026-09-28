import os
import glob
import re
import logging
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger("SupportNova.RAG")

DOCS_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "sample_documents", "docs")

# Policy Precedence Ranking (Higher number = Higher precedence)
PRECEDENCE_HIERARCHY = {
    "Active Policy": 100,
    "Standard Operating Procedure (SOP)": 80,
    "Departmental Guideline": 60,
    "Frequently Asked Questions (FAQ)": 40,
    "Informal Guidance": 20,
    "Superseded Policy": 0,
    "Draft Policy": 10
}

POLICY_TITLES = {
    "POL-REF-02": "Customer Refund & Escrow Payout Policy",
    "POL-WAR-07": "Limited Hardware Warranty Coverage Policy",
    "POL-DEL-04": "Delivery & Logistics Replacement Policy",
    "POL-SAF-05": "Product Safety & Fire Hazard Escalation Policy",
    "POL-BIL-06": "Billing Discrepancy & Chargeback Policy",
    "POL-SEC-08": "Account Security & Fraud Prevention Policy",
    "POL-PRV-09": "Data Privacy & GDPR Governance Policy",
    "POL-CON-10": "Staff Professional Conduct & Service Quality SOP",
    "POL-TEC-12": "Technical Support Diagnostics & Hardware Repair SOP",
    "POL-ESC-14": "Escalation Matrix & Manager Sign-off Governance",
    "POL-DOA-16": "Dead-on-Arrival (DOA) Return Policy",
    "POL-SUB-17": "Subscription & Recurring Billing Terms",
    "POL-B2B-19": "B2B Enterprise SLA & Bulk Refund Policy",
    "POL-GWD-15": "Global Warranty & Defect Exchange Policy",
    "POL-REP-03": "Product Replacement & Repair Operations Policy"
}

_RAG_MODEL = None
_RAG_INDEX = None
_RAG_CHUNKS = []

def _get_rag_model():
    global _RAG_MODEL
    if _RAG_MODEL is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading sentence-transformers all-MiniLM-L6-v2 model for RAG vector index...")
        _RAG_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _RAG_MODEL

def rebuild_vector_index():
    """Builds or rebuilds the FAISS vector index from active knowledge base chunks."""
    global _RAG_INDEX, _RAG_CHUNKS
    try:
        # Guard: if sentence-transformers or faiss not available, skip gracefully
        try:
            import faiss
            from sentence_transformers import SentenceTransformer  # noqa: F401
        except ImportError as ie:
            logger.warning(f"RAG vector index skipped (ML library unavailable): {ie}")
            return

        from config.database import get_chunks_col
        chunks_col = get_chunks_col()
        all_chunks = list(chunks_col.find({"status": "Active"}))
        if not all_chunks:
            _RAG_INDEX = None
            _RAG_CHUNKS = []
            return

        texts = [c.get("content", "") for c in all_chunks]
        model = _get_rag_model()
        embeddings = model.encode(texts, convert_to_numpy=True)
        embeddings = np.ascontiguousarray(embeddings, dtype=np.float32)
        faiss.normalize_L2(embeddings)

        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings)

        _RAG_INDEX = index
        _RAG_CHUNKS = all_chunks
        logger.info(f"RAG vector index built with {len(all_chunks)} policy chunks.")
    except Exception as e:
        logger.warning(f"RAG vector index build failed (non-fatal, keyword fallback active): {e}")

class KnowledgeBaseManager:
    @staticmethod
    def initialize_knowledge_base():
        """Scans sample_documents/docs and populates database with parsed policy chunks."""
        from config.database import get_knowledge_col, get_chunks_col
        from src.document_processing.parser import DocumentParser
        
        knowledge_col = get_knowledge_col()
        chunks_col = get_chunks_col()
        
        if knowledge_col.count_documents({}) == 0:
            pdf_files = glob.glob(os.path.join(DOCS_FOLDER, "*.pdf"))
            docx_files = glob.glob(os.path.join(DOCS_FOLDER, "*.docx"))
            
            all_files = list(set(pdf_files + docx_files))
            for fpath in all_files:
                fname = os.path.basename(fpath)
                doc_id = fname.replace(".pdf", "").replace(".docx", "")
                is_superseded = "OLD" in doc_id
                version = "v1.0 (Superseded)" if is_superseded else "v2.0"
                status = "Superseded" if is_superseded else "Active"
                doc_type = "Standard Operating Procedure (SOP)" if "SOP" in fname or "DOA" in fname else "Active Policy"
                
                with open(fpath, "rb") as f:
                    content_bytes = f.read()
                    
                if fpath.endswith(".pdf"):
                    chunks = DocumentParser.parse_pdf_content(content_bytes, fname, doc_id, version)
                else:
                    chunks = DocumentParser.parse_docx_content(content_bytes, fname, doc_id, version)

                # Store document metadata
                doc_title = POLICY_TITLES.get(doc_id, doc_id.replace("POL-", "Policy ").replace("-", " "))
                doc_record = {
                    "document_id": doc_id,
                    "filename": fname,
                    "title": doc_title,
                    "version": version,
                    "status": status,
                    "doc_type": doc_type,
                    "precedence_score": PRECEDENCE_HIERARCHY.get(status, 100),
                    "total_chunks": len(chunks),
                    "chunk_ids": [c["chunk_id"] for c in chunks]
                }
                knowledge_col.insert_one(doc_record)
                
                # Store chunks
                for c in chunks:
                    c["status"] = status
                    chunks_col.insert_one(c)
        
        # Always ensure FAISS index is populated
        rebuild_vector_index()

    @staticmethod
    def get_all_documents() -> List[Dict[str, Any]]:
        from config.database import get_knowledge_col
        col = get_knowledge_col()
        return col.find()

    @staticmethod
    def get_document_chunks(doc_id: str) -> List[Dict[str, Any]]:
        from config.database import get_chunks_col
        col = get_chunks_col()
        return col.find({"document_id": doc_id})

    @staticmethod
    def retrieve_relevant_policy_chunks(category: str, query: str = "", top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieves active policy chunks using dense vector embeddings (RAG with SentenceTransformers & FAISS)."""
        global _RAG_INDEX, _RAG_CHUNKS
        
        if _RAG_INDEX is None or len(_RAG_CHUNKS) == 0:
            rebuild_vector_index()
            
        if _RAG_INDEX is None or len(_RAG_CHUNKS) == 0:
            return []

        search_text = f"{category}: {query}".strip() if category else query.strip()
        if not search_text:
            return _RAG_CHUNKS[:top_k]

        try:
            import faiss
            model = _get_rag_model()
            q_emb = model.encode([search_text], convert_to_numpy=True)
            q_emb = np.ascontiguousarray(q_emb, dtype=np.float32)
            faiss.normalize_L2(q_emb)
            
            k = min(top_k, len(_RAG_CHUNKS))
            distances, indices = _RAG_INDEX.search(q_emb, k)
            
            results = []
            for idx in indices[0]:
                if 0 <= idx < len(_RAG_CHUNKS):
                    results.append(_RAG_CHUNKS[idx])
            return results
        except Exception as e:
            logger.error(f"Vector search failed, returning fallback top chunks: {e}")
            return _RAG_CHUNKS[:top_k]

