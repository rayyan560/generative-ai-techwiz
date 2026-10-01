from typing import Optional


SUPPORTED_IMAGE_TYPES = {
    "image/jpeg": lambda data: data.startswith(b"\xff\xd8\xff"),
    "image/png": lambda data: data.startswith(b"\x89PNG\r\n\x1a\n"),
    "image/webp": lambda data: len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP",
    "image/gif": lambda data: data.startswith((b"GIF87a", b"GIF89a")),
}


def detect_image_type(data: bytes) -> Optional[str]:
    for mime_type, validator in SUPPORTED_IMAGE_TYPES.items():
        if validator(data):
            return mime_type
    return None
