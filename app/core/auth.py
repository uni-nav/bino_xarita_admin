# app/core/auth.py
"""
Simple token-based authentication for admin endpoints
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings

security = HTTPBearer()

async def verify_admin_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Verify admin token from Authorization header.
    
    Usage:
        @router.delete("/{id}")
        async def delete_item(id: int, token: str = Depends(verify_admin_token)):
            ...
    """
    if credentials.credentials != settings.ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


# Optional: make some endpoints public, others protected
def optional_admin_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> bool:
    """Returns True if valid admin token, False otherwise"""
    return credentials.credentials == settings.ADMIN_TOKEN
