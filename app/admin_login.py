"""
Admin Login Endpoint
Provides JWT token generation for admin authentication
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Dict, Any
import logging
import os

from app.auth import create_admin_token, AUTHORIZED_ADMIN_EMAILS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str

class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: str
    role: str
    expires_in: int = 86400  # 24 hours in seconds

@router.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(credentials: AdminLoginRequest):
    """
    Admin login endpoint - returns JWT token for admin authentication

    **For development:**
    - Email must be in AUTHORIZED_ADMIN_EMAILS list
    - Password is checked against ADMIN_PASSWORD environment variable

    **For production:**
    - Implement proper password hashing (bcrypt)
    - Store admin credentials in database
    - Add rate limiting
    - Add MFA support
    """
    try:
        # Verify email is authorized
        if credentials.email not in AUTHORIZED_ADMIN_EMAILS:
            logger.warning(f"Unauthorized admin login attempt: {credentials.email}")
            raise HTTPException(
                status_code=403,
                detail="Email not authorized for admin access"
            )

        # Simple password check (DEVELOPMENT ONLY!)
        # TODO: Replace with proper password hashing in production
        admin_password = os.getenv('ADMIN_PASSWORD', 'change-me-in-production')

        if not admin_password or admin_password == 'change-me-in-production':
            logger.error("ADMIN_PASSWORD not set or using default value")
            raise HTTPException(
                status_code=500,
                detail="Admin authentication not properly configured"
            )

        if credentials.password != admin_password:
            logger.warning(f"Failed admin login attempt for {credentials.email}")
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials"
            )

        # Generate JWT token
        access_token = create_admin_token(credentials.email)

        logger.info(f"Admin login successful: {credentials.email}")

        return AdminLoginResponse(
            access_token=access_token,
            email=credentials.email,
            role="super_admin"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.get("/admin/verify")
async def verify_admin_token_endpoint(
    authorization: str = None
):
    """
    Verify admin JWT token (for testing)
    """
    from app.auth import verify_admin_token
    from fastapi import Header

    try:
        admin = verify_admin_token(authorization)
        return {
            "valid": True,
            "admin": admin
        }
    except HTTPException as e:
        return {
            "valid": False,
            "error": e.detail
        }

@router.get("/admin/test-token")
async def get_test_admin_token():
    """
    Get a test admin token (DEVELOPMENT ONLY!)
    Remove this endpoint in production
    """
    if os.getenv('ENVIRONMENT') == 'production':
        raise HTTPException(status_code=404, detail="Not found")

    try:
        token = create_admin_token("admin@pulsebridge.ai")
        return {
            "access_token": token,
            "token_type": "bearer",
            "usage": "Add to requests as: Authorization: Bearer <token>",
            "warning": "This endpoint only works in development"
        }
    except Exception as e:
        logger.error(f"Test token generation failed: {e}")
        raise HTTPException(status_code=500, detail="Token generation failed")
