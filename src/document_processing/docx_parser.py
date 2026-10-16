import io
import re
from typing import Any, Dict, List


def parse_docx_content(file_bytes: bytes, filename: str, doc_id: str, version: str = "v1.0") -> List[Dict[str, Any]]:
    chunks = []
    try:
        import docx

        document = docx.Document(io.BytesIO(file_bytes))
        current_heading = "General"
        current_section_id = "1.0"
        chunk_index = 1
        current_paragraphs = []

        def append_chunk():
            nonlocal chunk_index
            body = "\n".join(current_paragraphs)
            chunks.append({
                "chunk_id": f"{doc_id}-CHK-{chunk_index:03d}",
                "document_id": doc_id,
                "document_name": filename,
                "version": version,
                "section_id": current_section_id,
                "heading": current_heading,
                "page_number": 1,
                "content": body,
                "character_count": len(body),
            })
            chunk_index += 1

        for paragraph in document.paragraphs:
            text = paragraph.text.strip()
            if not text:
                continue
            is_heading = paragraph.style.name.startswith("Heading") or re.match(r"^[0-9]+(?:\.[0-9]+)*\s+[A-Z]", text)
            if is_heading:
                if current_paragraphs:
                    append_chunk()
                    current_paragraphs = []
                current_heading = text
                match = re.match(r"^([0-9]+(?:\.[0-9]+)*)", text)
                current_section_id = match.group(1) if match else f"{chunk_index}.0"
            else:
                current_paragraphs.append(text)

        if current_paragraphs:
            append_chunk()
    except Exception as error:
        raise RuntimeError(f"Failed to parse DOCX document: {error}")
    return chunks
