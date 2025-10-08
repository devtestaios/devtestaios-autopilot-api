"""
Authentication Module - Stub Implementation
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.models import User
import os

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Get current authenticated user from Bearer token.
    This is a stub implementation that returns a mock user.
    """
    # In production, this would:
    # 1. Validate the JWT token
    # 2. Extract user_id from token
    # 3. Fetch user from database
    # 4. Verify user is active

    # For stub, return a mock superuser
    mock_user = User()
    mock_user.id = "stub-user-id"
    mock_user.email = "admin@pulsebridge.ai"
    mock_user.full_name = "Admin User"
    mock_user.is_active = True
    mock_user.is_superuser = True
    mock_user.mfa_enabled = True
    mock_user.tenant_id = "default-tenant"
    mock_user.permissions = ["*"]  # All permissions

    return mock_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    # Stub implementation
    return True


def get_password_hash(password: str) -> str:
    """Hash a password"""
    # Stub implementation
    return f"hashed_{password}"


def create_access_token(data: dict) -> str:
    """Create a JWT access token"""
    # Stub implementation
    return "stub_jwt_token"
