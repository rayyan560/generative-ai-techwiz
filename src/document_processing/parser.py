import os
import io
import re
from typing import List, Dict, Any, Optional

class DocumentParser:
    @staticmethod
    def parse_pdf_content(file_bytes: bytes, filename: str, doc_id: str, version: str = "v1.0") -> List[Dict[str, Any]]:
        """Parses PDF bytes into structured chunks with page numbers and section headers."""
        chunks = []
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            chunk_idx = 1
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")
                if not text.strip():
                    continue
                
                # Split by sections or paragraphs
                sections = re.split(r"\n(?=[0-9]+\.[0-9]*\s+[A-Z])", text)
                for sec in sections:
                    clean_sec = sec.strip()
                    if not clean_sec:
                        continue
                    
                    lines = clean_sec.split("\n")
                    heading = lines[0][:80].strip() if lines else f"Page {page_num + 1} Section"
                    
                    # Extract section id if formatted like '5.2 Refund Policy'
                    sec_match = re.match(r"^([0-9]+(?:\.[0-9]+)*)", heading)
                    section_id = sec_match.group(1) if sec_match else f"{page_num+1}.{chunk_idx}"

                    chunks.append({
                        "chunk_id": f"{doc_id}-CHK-{chunk_idx:03d}",
                        "document_id": doc_id,
                        "document_name": filename,
                        "version": version,
                        "section_id": section_id,
                        "heading": heading,
                        "page_number": page_num + 1,
                        "content": clean_sec,
                        "character_count": len(clean_sec)
                    })
                    chunk_idx += 1
            doc.close()
        except Exception as e:
            # Fallback to PyPDF
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                chunk_idx = 1
                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    if text.strip():
                        chunks.append({
                            "chunk_id": f"{doc_id}-CHK-{chunk_idx:03d}",
                            "document_id": doc_id,
                            "document_name": filename,
                            "version": version,
                            "section_id": f"{page_num+1}.1",
                            "heading": f"Page {page_num+1} Content",
                            "page_number": page_num + 1,
                            "content": text.strip(),
                            "character_count": len(text.strip())
                        })
                        chunk_idx += 1
            except Exception as e2:
                raise RuntimeError(f"Failed to parse PDF: {e} | {e2}")
        return chunks

    @staticmethod
    def parse_docx_content(file_bytes: bytes, filename: str, doc_id: str, version: str = "v1.0") -> List[Dict[str, Any]]:
        """Parses DOCX bytes into structured chunks with heading hierarchy."""
        chunks = []
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            current_heading = "General"
            current_section_id = "1.0"
            chunk_idx = 1
            current_paragraphs = []

            for p in doc.paragraphs:
                text = p.text.strip()
                if not text:
                    continue
                
                # Detect heading style
                if p.style.name.startswith("Heading") or re.match(r"^[0-9]+(?:\.[0-9]+)*\s+[A-Z]", text):
                    # Flush previous chunk
                    if current_paragraphs:
                        body = "\n".join(current_paragraphs)
                        chunks.append({
                            "chunk_id": f"{doc_id}-CHK-{chunk_idx:03d}",
                            "document_id": doc_id,
                            "document_name": filename,
                            "version": version,
                            "section_id": current_section_id,
                            "heading": current_heading,
                            "page_number": 1,
                            "content": body,
                            "character_count": len(body)
                        })
                        chunk_idx += 1
                        current_paragraphs = []

                    current_heading = text
                    sec_match = re.match(r"^([0-9]+(?:\.[0-9]+)*)", text)
                    current_section_id = sec_match.group(1) if sec_match else f"{chunk_idx}.0"
                else:
                    current_paragraphs.append(text)

            # Flush tail chunk
            if current_paragraphs:
                body = "\n".join(current_paragraphs)
                chunks.append({
                    "chunk_id": f"{doc_id}-CHK-{chunk_idx:03d}",
                    "document_id": doc_id,
                    "document_name": filename,
                    "version": version,
                    "section_id": current_section_id,
                    "heading": current_heading,
                    "page_number": 1,
                    "content": body,
                    "character_count": len(body)
                })
        except Exception as e:
            raise RuntimeError(f"Failed to parse DOCX document: {e}")
        return chunks

    @staticmethod
    def parse_plain_text(text: str, filename: str, doc_id: str, version: str = "v1.0") -> List[Dict[str, Any]]:
        """Parses markdown or plain text files into structured chunks."""
        chunks = []
        raw_sections = re.split(r"\n(?=#{1,3}\s+|[0-9]+\.[0-9]*\s+)", text)
        chunk_idx = 1
        for sec in raw_sections:
            clean = sec.strip()
            if not clean:
                continue
            lines = clean.split("\n")
            heading = lines[0].replace("#", "").strip()
            sec_match = re.match(r"^([0-9]+(?:\.[0-9]+)*)", heading)
            section_id = sec_match.group(1) if sec_match else f"{chunk_idx}.0"

            chunks.append({
                "chunk_id": f"{doc_id}-CHK-{chunk_idx:03d}",
                "document_id": doc_id,
                "document_name": filename,
                "version": version,
                "section_id": section_id,
                "heading": heading,
                "page_number": 1,
                "content": clean,
                "character_count": len(clean)
            })
            chunk_idx += 1
        return chunks
