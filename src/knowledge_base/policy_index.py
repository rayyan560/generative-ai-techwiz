import logging
from datetime import date
from typing import Any, Dict, List, Optional

import numpy as np

from src.knowledge_base.policy_search import filter_current_policy_chunks


logger = logging.getLogger("SupportNova.RAG")
_RAG_MODEL = None
_RAG_INDEX = None
_RAG_CHUNKS: List[Dict[str, Any]] = []
_RAG_INDEX_DATE: Optional[str] = None


def _get_rag_model():
    global _RAG_MODEL
    if _RAG_MODEL is None:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading sentence-transformers all-MiniLM-L6-v2 model for RAG vector index...")
        _RAG_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _RAG_MODEL


def get_cached_chunks() -> List[Dict[str, Any]]:
    return _RAG_CHUNKS


def index_needs_rebuild() -> bool:
    return not _RAG_CHUNKS or _RAG_INDEX_DATE != date.today().isoformat()


def rebuild_vector_index() -> None:
    global _RAG_INDEX, _RAG_CHUNKS, _RAG_INDEX_DATE
    _RAG_INDEX = None
    _RAG_CHUNKS = []
    _RAG_INDEX_DATE = date.today().isoformat()
    try:
        from config.database import get_chunks_col

        all_chunks = list(get_chunks_col().find({"status": "Active"}))
        _RAG_CHUNKS = filter_current_policy_chunks(all_chunks, _RAG_INDEX_DATE)
        if not _RAG_CHUNKS:
            return
        try:
            import faiss
        except ImportError as error:
            logger.warning("Vector retrieval unavailable (%s); using policy keyword retrieval.", type(error).__name__)
            return
        texts = [chunk.get("content", "") for chunk in _RAG_CHUNKS]
        embeddings = _get_rag_model().encode(texts, convert_to_numpy=True)
        embeddings = np.ascontiguousarray(embeddings, dtype=np.float32)
        faiss.normalize_L2(embeddings)
        _RAG_INDEX = faiss.IndexFlatIP(embeddings.shape[1])
        _RAG_INDEX.add(embeddings)
        logger.info("RAG vector index built with %s policy chunks.", len(_RAG_CHUNKS))
    except Exception as error:
        logger.warning("Policy retrieval index build failed (%s).", type(error).__name__)


def search_vector_index(search_text: str, top_k: int) -> Optional[List[Dict[str, Any]]]:
    if _RAG_INDEX is None:
        return None
    try:
        import faiss

        query = _get_rag_model().encode([search_text], convert_to_numpy=True)
        query = np.ascontiguousarray(query, dtype=np.float32)
        faiss.normalize_L2(query)
        distances, indices = _RAG_INDEX.search(query, min(top_k, len(_RAG_CHUNKS)))
        return [_RAG_CHUNKS[index] for index in indices[0] if 0 <= index < len(_RAG_CHUNKS)]
    except Exception as error:
        logger.error("Vector search failed (%s); using policy keyword retrieval.", type(error).__name__)
        return None
