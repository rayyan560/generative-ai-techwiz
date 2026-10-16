import hashlib
import hmac
import logging

import bcrypt


logger = logging.getLogger("SupportNova.Auth")


def get_password_hash(password: str) -> str:
    if not password:
        return ""
    try:
        password_bytes = password.strip().encode("utf-8")[:72]
        return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")
    except Exception as error:
        logger.error("Error hashing password: %s", error)
        return hashlib.sha256(password.strip().encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    clean_password = plain_password.strip()
    clean_hash = hashed_password.strip()
    try:
        if clean_hash.startswith(("$2b$", "$2a$", "$2y$")):
            password_bytes = clean_password.encode("utf-8")[:72]
            return bcrypt.checkpw(password_bytes, clean_hash.encode("utf-8"))
        if clean_hash == hashlib.sha256(clean_password.encode()).hexdigest():
            return True
        return clean_password == clean_hash or hmac.compare_digest(clean_password, clean_hash)
    except Exception as error:
        logger.error("Password verification fallback error: %s", error)
        return clean_password == clean_hash
