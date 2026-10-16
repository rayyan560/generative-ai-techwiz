from typing import Any, Dict, List

from src.knowledge_base.policy_index import rebuild_vector_index
from src.knowledge_base.policy_metadata import DOCS_FOLDER, POLICY_TITLES, PRECEDENCE_HIERARCHY
from src.knowledge_base.policy_search import (
    filter_current_policy_chunks,
    keyword_policy_search,
    retrieve_relevant_policy_chunks,
)


class KnowledgeBaseManager:
    @staticmethod
    def initialize_knowledge_base() -> None:
        from src.knowledge_base.policy_seed import initialize_knowledge_base

        initialize_knowledge_base()

    @staticmethod
    def get_all_documents() -> List[Dict[str, Any]]:
        from config.database import get_knowledge_col

        return get_knowledge_col().find()

    @staticmethod
    def get_document_chunks(doc_id: str) -> List[Dict[str, Any]]:
        from config.database import get_chunks_col

        return get_chunks_col().find({"document_id": doc_id})

    @staticmethod
    def retrieve_relevant_policy_chunks(category: str, query: str = "", top_k: int = 3) -> List[Dict[str, Any]]:
        return retrieve_relevant_policy_chunks(category, query, top_k)
