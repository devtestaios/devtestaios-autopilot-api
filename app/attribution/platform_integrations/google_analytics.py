"""
Google Analytics 4 Measurement Protocol Integration
Server-side event tracking for Google Analytics 4

Documentation: https://developers.google.com/analytics/devguides/collection/protocol/ga4
"""
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import httpx
from pydantic import BaseModel, Field
import uuid

logger = logging.getLogger(__name__)


class GA4Event(BaseModel):
    """Google Analytics 4 event"""
    name: str = Field(..., description="Event name (purchase, lead, page_view, etc.)")
    params: Dict[str, Any] = Field(default_factory=dict, description="Event parameters")


class GA4UserProperties(BaseModel):
    """User properties for GA4"""
    user_id: Optional[str] = None  # Logged in user ID
    session_id: Optional[str] = None  # Session identifier
    engagement_time_msec: Optional[int] = None  # Engagement time in milliseconds


class GA4MeasurementProtocolClient:
    """
    Client for Google Analytics 4 Measurement Protocol
    Sends server-side events to GA4 for analytics and attribution
    """

    def __init__(
        self,
        measurement_id: Optional[str] = None,
        api_secret: Optional[str] = None
    ):
        """
        Initialize GA4 Measurement Protocol client

        Args:
            measurement_id: GA4 Measurement ID (G-XXXXXXXXXX)
            api_secret: GA4 Measurement Protocol API Secret
        """
        self.measurement_id = measurement_id or os.getenv('GA4_MEASUREMENT_ID')
        self.api_secret = api_secret or os.getenv('GA4_API_SECRET')

        self.base_url = "https://www.google-analytics.com"

        if not self.measurement_id:
            logger.warning("GA4_MEASUREMENT_ID not configured")
        if not self.api_secret:
            logger.warning("GA4_API_SECRET not configured")

    @property
    def is_configured(self) -> bool:
        """Check if API is properly configured"""
        return bool(self.measurement_id and self.api_secret)

    async def send_event(
        self,
        client_id: str,
        events: List[GA4Event],
        user_id: Optional[str] = None,
        user_properties: Optional[Dict[str, Any]] = None,
        timestamp_micros: Optional[int] = None
    ) -> bool:
        """
        Send events to GA4

        Args:
            client_id: Unique client identifier (anonymous ID)
            events: List of events to send
            user_id: Logged-in user ID (optional)
            user_properties: User properties (optional)
            timestamp_micros: Event timestamp in microseconds (optional)

        Returns:
            True if successful, False otherwise
        """
        if not self.is_configured:
            logger.error("GA4 Measurement Protocol not configured")
            return False

        url = f"{self.base_url}/mp/collect"
        params = {
            "measurement_id": self.measurement_id,
            "api_secret": self.api_secret
        }

        # Build payload
        payload = {
            "client_id": client_id,
            "events": [event.dict() for event in events]
        }

        if user_id:
            payload["user_id"] = user_id

        if user_properties:
            payload["user_properties"] = user_properties

        if timestamp_micros:
            payload["timestamp_micros"] = timestamp_micros

        # Send request
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    params=params,
                    json=payload,
                    timeout=10.0
                )

                # GA4 Measurement Protocol returns 2xx even with validation errors
                # Use debug endpoint to check for errors
                if response.status_code >= 400:
                    logger.error(f"GA4 error: {response.status_code} - {response.text}")
                    return False

                logger.info(f"GA4 events sent: {[e.name for e in events]} (client: {client_id})")
                return True

            except httpx.HTTPError as e:
                logger.error(f"GA4 request error: {e}")
                return False

    async def validate_event(
        self,
        client_id: str,
        events: List[GA4Event],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate events using GA4 debug endpoint

        Args:
            client_id: Client ID
            events: Events to validate
            user_id: User ID (optional)

        Returns:
            Validation result from GA4
        """
        if not self.is_configured:
            return {"error": "GA4 not configured"}

        url = f"{self.base_url}/debug/mp/collect"
        params = {
            "measurement_id": self.measurement_id,
            "api_secret": self.api_secret
        }

        payload = {
            "client_id": client_id,
            "events": [event.dict() for event in events]
        }

        if user_id:
            payload["user_id"] = user_id

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    params=params,
                    json=payload,
                    timeout=10.0
                )
                return response.json()

            except Exception as e:
                logger.error(f"GA4 validation error: {e}")
                return {"error": str(e)}

    async def send_purchase(
        self,
        client_id: str,
        user_id: Optional[str],
        transaction_id: str,
        value: float,
        currency: str = "USD",
        items: Optional[List[Dict[str, Any]]] = None,
        coupon: Optional[str] = None,
        shipping: Optional[float] = None,
        tax: Optional[float] = None
    ) -> bool:
        """
        Send purchase event to GA4

        Args:
            client_id: Client ID
            user_id: User ID (optional)
            transaction_id: Unique transaction ID
            value: Purchase value
            currency: Currency code
            items: List of purchased items
            coupon: Coupon code used
            shipping: Shipping cost
            tax: Tax amount

        Returns:
            True if successful
        """
        params = {
            "transaction_id": transaction_id,
            "value": value,
            "currency": currency
        }

        if items:
            params["items"] = items
        if coupon:
            params["coupon"] = coupon
        if shipping:
            params["shipping"] = shipping
        if tax:
            params["tax"] = tax

        event = GA4Event(name="purchase", params=params)

        return await self.send_event(
            client_id=client_id,
            events=[event],
            user_id=user_id
        )

    async def send_lead(
        self,
        client_id: str,
        user_id: Optional[str],
        value: Optional[float] = None,
        currency: str = "USD"
    ) -> bool:
        """Send lead generation event to GA4"""
        params = {}
        if value:
            params["value"] = value
            params["currency"] = currency

        event = GA4Event(name="generate_lead", params=params)

        return await self.send_event(
            client_id=client_id,
            events=[event],
            user_id=user_id
        )

    async def send_page_view(
        self,
        client_id: str,
        user_id: Optional[str],
        page_location: str,
        page_title: Optional[str] = None,
        page_referrer: Optional[str] = None
    ) -> bool:
        """Send page view event to GA4"""
        params = {
            "page_location": page_location
        }

        if page_title:
            params["page_title"] = page_title
        if page_referrer:
            params["page_referrer"] = page_referrer

        event = GA4Event(name="page_view", params=params)

        return await self.send_event(
            client_id=client_id,
            events=[event],
            user_id=user_id
        )

    async def send_add_to_cart(
        self,
        client_id: str,
        user_id: Optional[str],
        items: List[Dict[str, Any]],
        value: Optional[float] = None,
        currency: str = "USD"
    ) -> bool:
        """Send add_to_cart event to GA4"""
        params = {
            "items": items
        }

        if value:
            params["value"] = value
            params["currency"] = currency

        event = GA4Event(name="add_to_cart", params=params)

        return await self.send_event(
            client_id=client_id,
            events=[event],
            user_id=user_id
        )

    async def test_connection(self) -> bool:
        """Test if GA4 Measurement Protocol is working"""
        if not self.is_configured:
            return False

        try:
            # Send a test page_view event
            test_client_id = str(uuid.uuid4())

            event = GA4Event(
                name="page_view",
                params={
                    "page_location": "https://example.com/test",
                    "page_title": "Test Page"
                }
            )

            result = await self.send_event(
                client_id=test_client_id,
                events=[event]
            )

            return result

        except Exception as e:
            logger.error(f"GA4 connection test failed: {e}")
            return False


# Global client instance
_ga4_client: Optional[GA4MeasurementProtocolClient] = None


def get_ga4_client() -> GA4MeasurementProtocolClient:
    """Get or create global GA4 client"""
    global _ga4_client
    if _ga4_client is None:
        _ga4_client = GA4MeasurementProtocolClient()
    return _ga4_client
