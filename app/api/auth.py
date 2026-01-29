# app/api/auth.py
"""
Authentication endpoints for login and token management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from datetime import timedelta
from app.core.security import create_access_token, verify_password, get_password_hash
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request model"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


# Temporary in-memory users (replace with database)
# In production, this should be in database with proper user management
import os

def get_admin_user():
    """Load admin user from environment variables"""
    username = os.getenv("ADMIN_USERNAME", "admin")
    password_hash = os.getenv("ADMIN_PASSWORD_HASH")
    
    if not password_hash:
        # Fallback for development only - log warning
        logger.warning(
            "⚠️  ADMIN_PASSWORD_HASH not set in .env! Using insecure default. "
            "Run 'python scripts/create_admin.py' to create secure credentials."
        )
        password_hash = get_password_hash("admin123456")
    
    return {
        "username": username,
        "hashed_password": password_hash,
        "role": "admin"
    }

TEMP_USERS = {
    os.getenv("ADMIN_USERNAME", "admin"): get_admin_user()
}


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    """
    Login endpoint to get JWT access token
    
    **Note:** This is a temporary implementation. In production:
    - Use database for user management
    - Implement proper user registration
    - Add account lockout after failed attempts
    - Add 2FA support
    """
    user = TEMP_USERS.get(credentials.username)
    
    if not user or not verify_password(credentials.password, user["hashed_password"]):
        logger.warning(f"Failed login attempt for user: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    
    logger.info(f"Successful login for user: {credentials.username}")
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh")
async def refresh_token():
    """
    Refresh token endpoint (placeholder for future implementation)
    
    TODO: Implement refresh token mechanism
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh token not implemented yet"
    )
