from fastapi import HTTPException, Request

from src.security.auth import AuthManager


def require_roles(*allowed_roles: str):
    async def dependency(request: Request):
        user = AuthManager.get_current_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required.")
        if user.get("role") == "judge":
            if request.method not in {"GET", "HEAD"}:
                raise HTTPException(status_code=403, detail="Judge access is read-only.")
            if not set(allowed_roles).intersection({"admin", "agent", "warranty_manager"}):
                raise HTTPException(status_code=403, detail="Your role cannot access this resource.")
            return user
        if allowed_roles and user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Your role cannot access this resource.")
        return user

    return dependency
