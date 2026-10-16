import re
from datetime import date
from typing import Any, Dict, List, Optional


def filter_current_policy_chunks(
    chunks: List[Dict[str, Any]], today: Optional[str] = None
) -> List[Dict[str, Any]]:
    current_date = today or date.today().isoformat()
    current_chunks = [
        chunk
        for chunk in chunks
        if str(chunk.get("status", "")).casefold() == "active"
        and str(chunk.get("content", "")).strip()
        and (not chunk.get("effective_date") or str(chunk["effective_date"]) <= current_date)
        and (not chunk.get("expiry_date") or str(chunk["expiry_date"]) >= current_date)
    ]
    preferred_sources = {}
    for chunk in current_chunks:
        document_name = str(chunk.get("document_name", "")).casefold()
        if not document_name:
            continue
        key = (str(chunk.get("document_id", "")).casefold(), str(chunk.get("version", "")).casefold())
        rank = 0 if document_name.endswith(".pdf") else 1 if document_name.endswith(".docx") else 2
        previous = preferred_sources.get(key)
        if previous is None or rank < previous[0]:
            preferred_sources[key] = (rank, document_name)
    return [
        chunk
        for chunk in current_chunks
        if not chunk.get("document_name")
        or str(chunk.get("document_name", "")).casefold()
        == preferred_sources.get(
            (str(chunk.get("document_id", "")).casefold(), str(chunk.get("version", "")).casefold()),
            (None, None),
        )[1]
    ]


def keyword_policy_search(
    search_text: str, chunks: List[Dict[str, Any]], top_k: int
) -> List[Dict[str, Any]]:
    terms = set(re.findall(r"[a-z0-9]{3,}", search_text.casefold()))
    if not terms:
        return chunks[:top_k]
    ranked = []
    for index, chunk in enumerate(chunks):
        searchable = " ".join(
            str(chunk.get(field, "")) for field in ("document_id", "heading", "content")
        ).casefold()
        matches = sum(term in searchable for term in terms)
        if matches:
            ranked.append((matches, -index, chunk))
    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [chunk for _, _, chunk in ranked[:top_k]]


def retrieve_relevant_policy_chunks(
    category: str, query: str = "", top_k: int = 3
) -> List[Dict[str, Any]]:
    from src.knowledge_base.policy_index import (
        get_cached_chunks,
        index_needs_rebuild,
        rebuild_vector_index,
        search_vector_index,
    )

    if index_needs_rebuild():
        rebuild_vector_index()
    chunks = get_cached_chunks()
    if not chunks:
        return []
    search_text = f"{category}: {query}".strip() if category else query.strip()
    if not search_text:
        return chunks[:top_k]
    vector_results = search_vector_index(search_text, top_k)
    return vector_results if vector_results is not None else keyword_policy_search(search_text, chunks, top_k)
