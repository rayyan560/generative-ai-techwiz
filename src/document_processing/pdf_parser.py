import io
import re
from typing import Any, Dict, List


def parse_pdf_content(file_bytes: bytes, filename: str, doc_id: str, version: str = "v1.0") -> List[Dict[str, Any]]:
    chunks = []
    try:
        import fitz

        document = fitz.open(stream=file_bytes, filetype="pdf")
        chunk_index = 1
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text")
            if not text.strip():
                continue
            sections = re.split(r"\n(?=[0-9]+\.[0-9]*\s+[A-Z])", text)
            for section in sections:
                content = section.strip()
                if not content:
                    continue
                lines = content.split("\n")
                heading = lines[0][:80].strip() if lines else f"Page {page_number} Section"
                match = re.match(r"^([0-9]+(?:\.[0-9]+)*)", heading)
                section_id = match.group(1) if match else f"{page_number}.{chunk_index}"
                chunks.append({
                    "chunk_id": f"{doc_id}-CHK-{chunk_index:03d}",
                    "document_id": doc_id,
                    "document_name": filename,
                    "version": version,
                    "section_id": section_id,
                    "heading": heading,
                    "page_number": page_number,
                    "content": content,
                    "character_count": len(content),
                })
                chunk_index += 1
        document.close()
    except Exception as error:
        try:
            import pypdf

            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            for page_number, page in enumerate(reader.pages, start=1):
                text = (page.extract_text() or "").strip()
                if not text:
                    continue
                chunk_index = len(chunks) + 1
                chunks.append({
                    "chunk_id": f"{doc_id}-CHK-{chunk_index:03d}",
                    "document_id": doc_id,
                    "document_name": filename,
                    "version": version,
                    "section_id": f"{page_number}.1",
                    "heading": f"Page {page_number} Content",
                    "page_number": page_number,
                    "content": text,
                    "character_count": len(text),
                })
        except Exception as fallback_error:
            raise RuntimeError(f"Failed to parse PDF: {error} | {fallback_error}")
    return chunks
