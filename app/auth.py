"""
Authentication and Authorization Module
Provides admin authentication and role-based access control
"""

from fastapi import HTTPException, Depends, Header
from typing import Optional, Dict, Any
import os
import logging
from datetime import datetime, timedelta, timezone
import jwt
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Admin authentication configuration
ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY', 'your-secret-key-change-in-production')
ADMIN_ALGORITHM = 'HS256'
ADMIN_TOKEN_EXPIRE_HOURS = 24

# Temporary: Authorized admin emails (move to database in production)
AUTHORIZED_ADMIN_EMAILS = {
    "admin@pulsebridge.ai",
    "admin@20n1.ai",
    "admin@20n1digital.com",
    # Add your admin emails here
}

class AdminUser(BaseModel):
    """Admin user model"""
    email: str
    role: str = "super_admin"
    permissions: list[str] = []

def create_admin_token(email: str) -> str:
    """Create admin JWT token"""
    try:
        payload = {
            'email': email,
            'role': 'admin',
            'exp': datetime.now(timezone.utc) + timedelta(hours=ADMIN_TOKEN_EXPIRE_HOURS),
            'iat': datetime.now(timezone.utc)
        }
        token = jwt.encode(payload, ADMIN_SECRET_KEY, algorithm=ADMIN_ALGORITHM)
        return token
    except Exception as e:
        logger.error(f"Error creating admin token: {e}")
        raise HTTPException(status_code=500, detail="Token creation failed")

def verify_admin_token(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Verify admin JWT token from Authorization header
    Returns admin user info if valid, raises HTTPException if not

    Usage in endpoints:
    ```
    @router.post("/admin/endpoint")
    async def admin_endpoint(admin: dict = Depends(verify_admin_token)):
        # Only authenticated admins can access
        pass
    ```
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Extract token from "Bearer <token>" format
    try:
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"}
            )
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Verify token
    try:
        payload = jwt.decode(token, ADMIN_SECRET_KEY, algorithms=[ADMIN_ALGORITHM])
        email = payload.get('email')

        if not email:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        # Verify admin is authorized
        if email not in AUTHORIZED_ADMIN_EMAILS:
            logger.warning(f"Unauthorized admin access attempt from {email}")
            raise HTTPException(status_code=403, detail="Admin not authorized")

        logger.info(f"Admin authenticated: {email}")

        return {
            'email': email,
            'role': payload.get('role', 'admin'),
            'authenticated': True
        }

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")

async def verify_admin_api_key(x_api_key: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Alternative: Verify admin API key from X-API-Key header
    Simpler than JWT for server-to-server communication

    Usage:
    ```
    @router.post("/admin/endpoint")
    async def admin_endpoint(admin: dict = Depends(verify_admin_api_key)):
        pass
    ```
    """
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing X-API-Key header"
        )

    # Get admin API key from environment
    valid_api_key = os.getenv('ADMIN_API_KEY')

    if not valid_api_key:
        logger.error("ADMIN_API_KEY not set in environment")
        raise HTTPException(status_code=500, detail="Server configuration error")

    if x_api_key != valid_api_key:
        logger.warning(f"Invalid API key attempt")
        raise HTTPException(status_code=403, detail="Invalid API key")

    logger.info("Admin authenticated via API key")

    return {
        'authenticated': True,
        'method': 'api_key'
    }

# Optional: Convenience function for development/testing
def create_dev_admin_token() -> str:
    """
    Create a development admin token for testing
    Only use in development environments!
    """
    if os.getenv('ENVIRONMENT') == 'production':
        raise Exception("Cannot create dev tokens in production")

    return create_admin_token("admin@pulsebridge.ai")
