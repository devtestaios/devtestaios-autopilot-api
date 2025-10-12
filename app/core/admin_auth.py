"""
Admin Authentication Module
Secures admin-only endpoints with API key authentication
"""

from fastapi import HTTPException, Header
from typing import Optional
import os

# Get admin API key from environment
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "CHANGE_THIS_IN_PRODUCTION")

async def verify_admin_token(x_admin_key: Optional[str] = Header(None)):
    """
    Verify admin API key from request header

    Usage in routes:
        @router.post("/admin/endpoint")
        async def admin_endpoint(admin: bool = Depends(verify_admin_token)):
            # Your admin code here
            pass

    Args:
        x_admin_key: Admin API key from X-Admin-Key header

    Returns:
        True if authentication successful

    Raises:
        HTTPException 401: If no API key provided
        HTTPException 403: If API key is invalid
    """
    if not x_admin_key:
        raise HTTPException(
            status_code=401,
            detail="Admin authentication required. Please provide X-Admin-Key header."
        )

    if x_admin_key != ADMIN_API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid admin credentials"
        )

    return True


def get_admin_api_key() -> str:
    """
    Get the current admin API key
    Used for testing or programmatic admin access
    """
    return ADMIN_API_KEY


def is_admin_configured() -> bool:
    """
    Check if admin API key has been changed from default
    """
    return ADMIN_API_KEY != "CHANGE_THIS_IN_PRODUCTION"
