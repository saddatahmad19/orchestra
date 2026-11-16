import secrets
from fastapi import Header, HTTPException

def require_token(authorization: str | None, expected: str):
    token = authorization.removeprefix("Bearer ").strip() if authorization else ""
    if not token or not secrets.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="Valid bearer token required")
