"""
Meta (Facebook/Instagram) OAuth Flow
Handles user authorization and token exchange for Meta Business API
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Request
from pydantic import BaseModel
from typing import Optional
import requests
import os
import logging
from datetime import datetime
import secrets
from slowapi import Limiter
from slowapi.util import get_remote_address

# Import Supabase for storing connections
from supabase import create_client, Client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/oauth", tags=["oauth"])

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Meta OAuth Configuration
META_APP_ID = os.getenv("META_APP_ID")
META_APP_SECRET = os.getenv("META_APP_SECRET")
META_REDIRECT_URI = os.getenv("META_REDIRECT_URI", "http://localhost:3002/auth/meta/callback")

# Supabase Configuration
SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    logger.warning("Supabase not configured - OAuth flow will not persist connections")
    supabase = None

class MetaAuthResponse(BaseModel):
    """Response from Meta auth URL generation"""
    authorization_url: str
    state: str

class MetaCallbackResponse(BaseModel):
    """Response from Meta OAuth callback"""
    success: bool
    access_token: str
    ad_account_id: Optional[str]
    user_id: str
    message: str

@router.get("/meta/authorize-url")
@limiter.limit("10/minute")  # Allow 10 authorization requests per minute
async def get_meta_authorization_url(
    request: Request,
    user_id: str = Query(..., description="User ID to associate with this connection")
) -> MetaAuthResponse:
    """
    Generate Meta OAuth authorization URL

    This URL redirects users to Meta to grant permissions for:
    - ads_management: Manage ad accounts
    - ads_read: Read ad data
    - business_management: Manage business assets

    Args:
        user_id: The user ID to associate with this Meta connection

    Returns:
        Authorization URL and state for CSRF protection
    """
    if not META_APP_ID:
        raise HTTPException(
            status_code=500,
            detail="Meta App ID not configured. Please set META_APP_ID environment variable."
        )

    # Generate random state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Store state temporarily (in production, use Redis with TTL)
    # For now, we'll verify in callback using the user_id in state
    state_with_user = f"{user_id}_{state}"

    # Meta OAuth URL
    # Docs: https://developers.facebook.com/docs/facebook-login/manually-build-a-login-flow
    authorization_url = (
        f"https://www.facebook.com/v18.0/dialog/oauth?"
        f"client_id={META_APP_ID}"
        f"&redirect_uri={META_REDIRECT_URI}"
        f"&state={state_with_user}"
        f"&scope=ads_management,ads_read,business_management,read_insights"
        f"&response_type=code"
    )

    logger.info(f"Generated Meta auth URL for user {user_id}")

    return MetaAuthResponse(
        authorization_url=authorization_url,
        state=state_with_user
    )

@router.get("/meta/callback")
@limiter.limit("20/minute")  # Allow 20 callback requests per minute
async def meta_oauth_callback(
    request: Request,
    code: str = Query(..., description="Authorization code from Meta"),
    state: str = Query(..., description="State parameter for CSRF protection"),
    error: Optional[str] = Query(None, description="Error from Meta if authorization failed"),
    error_description: Optional[str] = Query(None, description="Error description from Meta")
) -> MetaCallbackResponse:
    """
    Handle OAuth callback from Meta

    After user authorizes, Meta redirects here with:
    - code: Authorization code to exchange for access token
    - state: State parameter we sent (contains user_id)

    This endpoint:
    1. Exchanges code for access token
    2. Fetches user's ad accounts
    3. Stores connection in database

    Returns:
        Access token and ad account info
    """
    # Check for authorization errors
    if error:
        logger.error(f"Meta OAuth error: {error} - {error_description}")
        raise HTTPException(
            status_code=400,
            detail=f"Meta authorization failed: {error_description or error}"
        )

    # Extract user_id from state
    try:
        user_id = state.split("_")[0]
    except:
        raise HTTPException(
            status_code=400,
            detail="Invalid state parameter"
        )

    if not META_APP_ID or not META_APP_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Meta credentials not configured"
        )

    # Step 1: Exchange code for access token
    token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
    token_params = {
        "client_id": META_APP_ID,
        "client_secret": META_APP_SECRET,
        "redirect_uri": META_REDIRECT_URI,
        "code": code
    }

    try:
        token_response = requests.get(token_url, params=token_params)
        token_response.raise_for_status()
        token_data = token_response.json()

        access_token = token_data.get("access_token")

        if not access_token:
            raise HTTPException(
                status_code=400,
                detail="Failed to obtain access token from Meta"
            )

        logger.info(f"Successfully obtained Meta access token for user {user_id}")

    except requests.RequestException as e:
        logger.error(f"Failed to exchange code for token: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to exchange authorization code: {str(e)}"
        )

    # Step 2: Get user's ad accounts
    ad_accounts = []
    ad_account_id = None

    try:
        # Fetch ad accounts
        # Docs: https://developers.facebook.com/docs/marketing-api/reference/user/adaccounts
        accounts_url = "https://graph.facebook.com/v18.0/me/adaccounts"
        accounts_params = {
            "access_token": access_token,
            "fields": "id,name,account_status,currency,timezone_name"
        }

        accounts_response = requests.get(accounts_url, params=accounts_params)
        accounts_response.raise_for_status()
        accounts_data = accounts_response.json()

        ad_accounts = accounts_data.get("data", [])

        if ad_accounts:
            # Use first active ad account
            ad_account_id = ad_accounts[0]["id"]
            logger.info(f"Found {len(ad_accounts)} ad accounts for user {user_id}")
        else:
            logger.warning(f"No ad accounts found for user {user_id}")

    except requests.RequestException as e:
        logger.error(f"Failed to fetch ad accounts: {e}")
        # Don't fail the whole flow if we can't get accounts
        pass

    # Step 3: Store connection in database
    if supabase:
        try:
            # Check if connection already exists
            existing = supabase.table("platform_connections")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("platform", "meta")\
                .execute()

            connection_data = {
                "user_id": user_id,
                "platform": "meta",
                "account_id": ad_account_id,
                "access_token": access_token,
                "is_active": True,
                "last_sync_at": datetime.now().isoformat(),
                "sync_status": "connected",
                "updated_at": datetime.now().isoformat()
            }

            if existing.data and len(existing.data) > 0:
                # Update existing connection
                result = supabase.table("platform_connections")\
                    .update(connection_data)\
                    .eq("user_id", user_id)\
                    .eq("platform", "meta")\
                    .execute()
                logger.info(f"Updated Meta connection for user {user_id}")
            else:
                # Insert new connection
                connection_data["created_at"] = datetime.now().isoformat()
                result = supabase.table("platform_connections")\
                    .insert(connection_data)\
                    .execute()
                logger.info(f"Created new Meta connection for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to store connection in database: {e}")
            # Continue even if database save fails
            pass

    return MetaCallbackResponse(
        success=True,
        access_token=access_token,
        ad_account_id=ad_account_id,
        user_id=user_id,
        message=f"Successfully connected Meta account{f' with {len(ad_accounts)} ad accounts' if ad_accounts else ''}"
    )

@router.get("/meta/status/{user_id}")
async def get_meta_connection_status(user_id: str):
    """
    Check if user has Meta connected

    Returns:
        Connection status and ad account info
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        connection = supabase.table("platform_connections")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("platform", "meta")\
            .execute()

        if connection.data and len(connection.data) > 0:
            conn = connection.data[0]
            return {
                "connected": True,
                "ad_account_id": conn.get("account_id"),
                "last_sync": conn.get("last_sync_at"),
                "sync_status": conn.get("sync_status"),
                "is_active": conn.get("is_active")
            }
        else:
            return {
                "connected": False,
                "message": "Meta not connected. Please authorize."
            }

    except Exception as e:
        logger.error(f"Failed to check connection status: {e}")
        raise HTTPException(status_code=500, detail="Failed to check connection status")

@router.delete("/meta/disconnect/{user_id}")
async def disconnect_meta(user_id: str):
    """
    Disconnect Meta account

    This doesn't revoke the token on Meta's side, just removes from our database
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")

    try:
        result = supabase.table("platform_connections")\
            .delete()\
            .eq("user_id", user_id)\
            .eq("platform", "meta")\
            .execute()

        logger.info(f"Disconnected Meta for user {user_id}")

        return {
            "success": True,
            "message": "Meta account disconnected"
        }

    except Exception as e:
        logger.error(f"Failed to disconnect Meta: {e}")
        raise HTTPException(status_code=500, detail="Failed to disconnect Meta account")
