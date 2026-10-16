import re
from typing import Any, Dict, List


def parse_plain_text(text: str, filename: str, doc_id: str, version: str = "v1.0") -> List[Dict[str, Any]]:
    chunks = []
    sections = re.split(r"\n(?=#{1,3}\s+|[0-9]+\.[0-9]*\s+)", text)
    chunk_index = 1
    for section in sections:
        content = section.strip()
        if not content:
            continue
        heading = content.split("\n")[0].replace("#", "").strip()
        match = re.match(r"^([0-9]+(?:\.[0-9]+)*)", heading)
        chunks.append({
            "chunk_id": f"{doc_id}-CHK-{chunk_index:03d}",
            "document_id": doc_id,
            "document_name": filename,
            "version": version,
            "section_id": match.group(1) if match else f"{chunk_index}.0",
            "heading": heading,
            "page_number": 1,
            "content": content,
            "character_count": len(content),
        })
        chunk_index += 1
    return chunks
