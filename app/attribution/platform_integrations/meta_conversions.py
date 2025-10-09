"""
Meta Conversions API Integration
Server-side event tracking for Meta (Facebook/Instagram) ads

Documentation: https://developers.facebook.com/docs/marketing-api/conversions-api
"""
import os
import hashlib
import time
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MetaUserData(BaseModel):
    """User data for Meta Conversions API (hashed for privacy)"""
    email: Optional[str] = None  # Will be hashed
    phone: Optional[str] = None  # Will be hashed
    first_name: Optional[str] = None  # Will be hashed
    last_name: Optional[str] = None  # Will be hashed
    city: Optional[str] = None  # Will be hashed
    state: Optional[str] = None  # Will be hashed
    zip_code: Optional[str] = None  # Will be hashed
    country: Optional[str] = None  # Will be hashed
    external_id: Optional[str] = None  # Customer ID (hashed)
    client_ip_address: Optional[str] = None  # Not hashed
    client_user_agent: Optional[str] = None  # Not hashed
    fbp: Optional[str] = None  # Facebook browser pixel cookie
    fbc: Optional[str] = None  # Facebook click ID

    def to_meta_format(self) -> Dict[str, str]:
        """Convert to Meta Conversions API format with hashing"""
        data = {}

        # Hash PII fields
        if self.email:
            data['em'] = self._hash(self.email.lower().strip())
        if self.phone:
            # Remove all non-digits
            clean_phone = ''.join(filter(str.isdigit, self.phone))
            data['ph'] = self._hash(clean_phone)
        if self.first_name:
            data['fn'] = self._hash(self.first_name.lower().strip())
        if self.last_name:
            data['ln'] = self._hash(self.last_name.lower().strip())
        if self.city:
            data['ct'] = self._hash(self.city.lower().strip())
        if self.state:
            data['st'] = self._hash(self.state.lower().strip())
        if self.zip_code:
            data['zp'] = self._hash(self.zip_code.strip())
        if self.country:
            data['country'] = self._hash(self.country.lower().strip())
        if self.external_id:
            data['external_id'] = self._hash(str(self.external_id))

        # Non-hashed fields
        if self.client_ip_address:
            data['client_ip_address'] = self.client_ip_address
        if self.client_user_agent:
            data['client_user_agent'] = self.client_user_agent
        if self.fbp:
            data['fbp'] = self.fbp
        if self.fbc:
            data['fbc'] = self.fbc

        return data

    @staticmethod
    def _hash(value: str) -> str:
        """SHA256 hash for PII"""
        return hashlib.sha256(value.encode('utf-8')).hexdigest()


class MetaCustomData(BaseModel):
    """Custom data for the conversion event"""
    value: Optional[float] = None  # Revenue
    currency: Optional[str] = "USD"
    content_name: Optional[str] = None  # Product name
    content_category: Optional[str] = None  # Product category
    content_ids: Optional[List[str]] = None  # Product IDs
    content_type: Optional[str] = None  # 'product' or 'product_group'
    order_id: Optional[str] = None  # Transaction ID
    predicted_ltv: Optional[float] = None  # Predicted lifetime value
    num_items: Optional[int] = None  # Number of items
    search_string: Optional[str] = None  # Search query if applicable
    status: Optional[str] = None  # Order status


class MetaConversionEvent(BaseModel):
    """Complete conversion event for Meta"""
    event_name: str = Field(..., description="Event name (Purchase, Lead, etc.)")
    event_time: int = Field(..., description="Unix timestamp")
    event_source_url: Optional[str] = None  # Where event occurred
    action_source: str = Field(default="website", description="website, app, etc.")
    user_data: MetaUserData
    custom_data: Optional[MetaCustomData] = None
    event_id: Optional[str] = None  # Deduplication ID
    opt_out: bool = False  # User opted out of tracking


class MetaConversionsAPIClient:
    """
    Client for Meta Conversions API
    Sends server-side events to Meta for attribution
    """

    def __init__(
        self,
        pixel_id: Optional[str] = None,
        access_token: Optional[str] = None,
        test_event_code: Optional[str] = None
    ):
        """
        Initialize Meta Conversions API client

        Args:
            pixel_id: Meta Pixel ID
            access_token: Meta Marketing API access token
            test_event_code: Test event code for debugging (optional)
        """
        self.pixel_id = pixel_id or os.getenv('META_PIXEL_ID')
        self.access_token = access_token or os.getenv('META_ACCESS_TOKEN')
        self.test_event_code = test_event_code or os.getenv('META_TEST_EVENT_CODE')

        self.base_url = "https://graph.facebook.com/v18.0"

        if not self.pixel_id:
            logger.warning("META_PIXEL_ID not configured")
        if not self.access_token:
            logger.warning("META_ACCESS_TOKEN not configured")

    @property
    def is_configured(self) -> bool:
        """Check if API is properly configured"""
        return bool(self.pixel_id and self.access_token)

    async def send_event(
        self,
        event: MetaConversionEvent
    ) -> Dict[str, Any]:
        """
        Send a conversion event to Meta

        Args:
            event: MetaConversionEvent to send

        Returns:
            Response from Meta API

        Raises:
            HTTPError if request fails
        """
        if not self.is_configured:
            logger.error("Meta Conversions API not configured")
            raise ValueError("Meta Pixel ID and Access Token required")

        url = f"{self.base_url}/{self.pixel_id}/events"

        # Build request payload
        payload = {
            "data": [{
                "event_name": event.event_name,
                "event_time": event.event_time,
                "action_source": event.action_source,
                "user_data": event.user_data.to_meta_format(),
                "opt_out": event.opt_out
            }],
            "access_token": self.access_token
        }

        # Add optional fields
        if event.event_source_url:
            payload["data"][0]["event_source_url"] = event.event_source_url
        if event.custom_data:
            payload["data"][0]["custom_data"] = event.custom_data.dict(exclude_none=True)
        if event.event_id:
            payload["data"][0]["event_id"] = event.event_id

        # Add test event code if in test mode
        if self.test_event_code:
            payload["test_event_code"] = self.test_event_code

        # Send request
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, timeout=10.0)
                response.raise_for_status()

                result = response.json()

                logger.info(f"Meta event sent: {event.event_name} (id: {event.event_id})")

                # Check for errors in response
                if "events_received" in result and result["events_received"] == 0:
                    logger.error(f"Meta rejected event: {result}")

                return result

            except httpx.HTTPError as e:
                logger.error(f"Meta Conversions API error: {e}")
                raise

    async def send_purchase(
        self,
        user_data: MetaUserData,
        revenue: float,
        currency: str = "USD",
        order_id: Optional[str] = None,
        product_ids: Optional[List[str]] = None,
        event_id: Optional[str] = None,
        event_source_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a purchase event to Meta

        Args:
            user_data: User information
            revenue: Purchase amount
            currency: Currency code
            order_id: Transaction ID
            product_ids: List of product IDs purchased
            event_id: Unique event ID for deduplication
            event_source_url: URL where purchase occurred

        Returns:
            Meta API response
        """
        custom_data = MetaCustomData(
            value=revenue,
            currency=currency,
            order_id=order_id,
            content_ids=product_ids,
            content_type="product" if product_ids else None,
            num_items=len(product_ids) if product_ids else None
        )

        event = MetaConversionEvent(
            event_name="Purchase",
            event_time=int(time.time()),
            user_data=user_data,
            custom_data=custom_data,
            event_id=event_id,
            event_source_url=event_source_url
        )

        return await self.send_event(event)

    async def send_lead(
        self,
        user_data: MetaUserData,
        value: Optional[float] = None,
        event_id: Optional[str] = None,
        event_source_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a lead event to Meta

        Args:
            user_data: User information
            value: Estimated lead value
            event_id: Unique event ID
            event_source_url: URL where lead was captured

        Returns:
            Meta API response
        """
        custom_data = MetaCustomData(
            value=value,
            currency="USD"
        ) if value else None

        event = MetaConversionEvent(
            event_name="Lead",
            event_time=int(time.time()),
            user_data=user_data,
            custom_data=custom_data,
            event_id=event_id,
            event_source_url=event_source_url
        )

        return await self.send_event(event)

    async def send_add_to_cart(
        self,
        user_data: MetaUserData,
        content_ids: List[str],
        value: Optional[float] = None,
        currency: str = "USD",
        event_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send AddToCart event to Meta"""
        custom_data = MetaCustomData(
            value=value,
            currency=currency,
            content_ids=content_ids,
            content_type="product"
        )

        event = MetaConversionEvent(
            event_name="AddToCart",
            event_time=int(time.time()),
            user_data=user_data,
            custom_data=custom_data,
            event_id=event_id
        )

        return await self.send_event(event)

    async def send_page_view(
        self,
        user_data: MetaUserData,
        event_source_url: str,
        event_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send PageView event to Meta"""
        event = MetaConversionEvent(
            event_name="PageView",
            event_time=int(time.time()),
            user_data=user_data,
            event_source_url=event_source_url,
            event_id=event_id
        )

        return await self.send_event(event)

    async def test_connection(self) -> bool:
        """Test if Meta Conversions API is working"""
        if not self.is_configured:
            return False

        try:
            # Send a test event
            test_user = MetaUserData(
                external_id="test_user_123",
                client_ip_address="127.0.0.1"
            )

            test_event = MetaConversionEvent(
                event_name="PageView",
                event_time=int(time.time()),
                user_data=test_user,
                event_id=f"test_{int(time.time())}"
            )

            result = await self.send_event(test_event)

            return result.get("events_received", 0) > 0

        except Exception as e:
            logger.error(f"Meta connection test failed: {e}")
            return False


# Global client instance
_meta_client: Optional[MetaConversionsAPIClient] = None


def get_meta_client() -> MetaConversionsAPIClient:
    """Get or create global Meta Conversions API client"""
    global _meta_client
    if _meta_client is None:
        _meta_client = MetaConversionsAPIClient()
    return _meta_client
