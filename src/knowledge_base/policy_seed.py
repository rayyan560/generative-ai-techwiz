import glob
import os

from src.knowledge_base.policy_metadata import (
    DOCS_FOLDER,
    POLICY_TITLES,
    precedence_score_for,
)


def initialize_knowledge_base() -> None:
    from config.database import get_chunks_col, get_knowledge_col
    from src.document_processing.parser import DocumentParser
    from src.knowledge_base.policy_index import rebuild_vector_index

    knowledge_col = get_knowledge_col()
    chunks_col = get_chunks_col()
    if knowledge_col.count_documents({}) == 0:
        paths = sorted(glob.glob(os.path.join(DOCS_FOLDER, "*.pdf")) + glob.glob(os.path.join(DOCS_FOLDER, "*.docx")))
        for file_path in paths:
            file_name = os.path.basename(file_path)
            document_id = file_name.replace(".pdf", "").replace(".docx", "")
            is_superseded = "OLD" in document_id
            version = "v1.0 (Superseded)" if is_superseded else "v2.0"
            status = "Superseded" if is_superseded else "Active"
            document_type = "Standard Operating Procedure (SOP)" if "SOP" in file_name or "DOA" in file_name else "Active Policy"
            with open(file_path, "rb") as stream:
                content = stream.read()
            if file_path.endswith(".pdf"):
                chunks = DocumentParser.parse_pdf_content(content, file_name, document_id, version)
            else:
                chunks = DocumentParser.parse_docx_content(content, file_name, document_id, version)
            record = {
                "document_id": document_id,
                "filename": file_name,
                "title": POLICY_TITLES.get(document_id, document_id.replace("POL-", "Policy ").replace("-", " ")),
                "version": version,
                "status": status,
                "doc_type": document_type,
                "precedence_score": precedence_score_for(document_type, status),
                "total_chunks": len(chunks),
                "chunk_ids": [chunk["chunk_id"] for chunk in chunks],
            }
            knowledge_col.insert_one(record)
            for chunk in chunks:
                chunk["status"] = status
                chunks_col.insert_one(chunk)
    rebuild_vector_index()
