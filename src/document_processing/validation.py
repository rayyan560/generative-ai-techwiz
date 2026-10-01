import hashlib
import io
import re
import zipfile
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Dict, Optional


MAX_DOCUMENT_BYTES = 10 * 1024 * 1024
SUPPORTED_DOCUMENT_SUFFIXES = {".pdf", ".docx", ".txt", ".md", ".csv"}
SUPPORTED_DOCUMENT_STATUSES = {"Active", "Superseded", "Draft"}


def validate_document_file(filename: Optional[str], content: bytes) -> str:
    normalized_name = (filename or "").replace("\\", "/")
    if not normalized_name or PurePosixPath(normalized_name).name != normalized_name:
        raise ValueError("Choose a valid filename without directory paths.")
    if len(content) == 0:
        raise ValueError("The selected document is empty.")
    if len(content) > MAX_DOCUMENT_BYTES:
        raise ValueError("The document exceeds the 10 MB upload limit.")

    suffix = Path(normalized_name).suffix.lower()
    if suffix not in SUPPORTED_DOCUMENT_SUFFIXES:
        raise ValueError("Supported documents are PDF, DOCX, TXT, Markdown, and CSV.")

    if suffix == ".pdf" and not content.startswith(b"%PDF-"):
        raise ValueError("The file contents do not match a PDF document.")
    if suffix == ".docx":
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                if "word/document.xml" not in archive.namelist():
                    raise ValueError("The file is not a valid DOCX document.")
                if sum(info.file_size for info in archive.infolist()) > 30 * 1024 * 1024:
                    raise ValueError("The expanded DOCX content exceeds the allowed size.")
        except (zipfile.BadZipFile, OSError) as error:
            raise ValueError("The file is not a valid DOCX document.") from error
    if suffix in {".txt", ".md", ".csv"}:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError("Text documents must use UTF-8 encoding.") from error
        if not text.strip() or "\x00" in text:
            raise ValueError("The text document has no readable content.")

    return suffix


def validate_document_metadata(
    filename: str,
    document_id: Optional[str],
    version: Optional[str],
    status: Optional[str],
    effective_date: Optional[str],
    expiry_date: Optional[str],
) -> Dict[str, Optional[str]]:
    clean_id = (document_id or Path(filename).stem).strip().upper()
    clean_version = (version or "").strip()
    clean_status = (status or "Active").strip().title()
    clean_effective = (effective_date or date.today().isoformat()).strip()
    clean_expiry = (expiry_date or "").strip() or None

    if not re.fullmatch(r"[A-Z0-9][A-Z0-9._-]{0,63}", clean_id):
        raise ValueError("Document ID may contain letters, numbers, dots, underscores, and hyphens.")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,31}", clean_version):
        raise ValueError("Enter a valid document version, such as v2.1.")
    if clean_status not in SUPPORTED_DOCUMENT_STATUSES:
        raise ValueError("Document status must be Active, Superseded, or Draft.")

    try:
        effective = date.fromisoformat(clean_effective)
        expiry = date.fromisoformat(clean_expiry) if clean_expiry else None
    except ValueError as error:
        raise ValueError("Effective and expiry dates must use YYYY-MM-DD format.") from error
    if expiry and expiry < effective:
        raise ValueError("Expiry date cannot be earlier than the effective date.")

    return {
        "document_id": clean_id,
        "version": clean_version,
        "status": clean_status,
        "effective_date": effective.isoformat(),
        "expiry_date": expiry.isoformat() if expiry else None,
    }


def document_fingerprint(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
