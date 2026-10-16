from typing import Any, Dict, List

from src.document_processing.docx_parser import parse_docx_content
from src.document_processing.pdf_parser import parse_pdf_content
from src.document_processing.text_parser import parse_plain_text


class DocumentParser:
    @staticmethod
    def parse_pdf_content(file_bytes: bytes, filename: str, doc_id: str, version: str = "v1.0") -> List[Dict[str, Any]]:
        return parse_pdf_content(file_bytes, filename, doc_id, version)

    @staticmethod
    def parse_docx_content(file_bytes: bytes, filename: str, doc_id: str, version: str = "v1.0") -> List[Dict[str, Any]]:
        return parse_docx_content(file_bytes, filename, doc_id, version)

    @staticmethod
    def parse_plain_text(text: str, filename: str, doc_id: str, version: str = "v1.0") -> List[Dict[str, Any]]:
        return parse_plain_text(text, filename, doc_id, version)
