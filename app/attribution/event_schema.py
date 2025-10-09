"""
Unified Event Schema for Multi-Platform Attribution
Tracks customer touchpoints across Meta, Google, LinkedIn, TikTok, etc.
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
import hashlib


class EventType(str, Enum):
    """Types of marketing touchpoints"""
    # Awareness
    IMPRESSION = "impression"
    VIDEO_VIEW = "video_view"

    # Consideration
    CLICK = "click"
    LANDING_PAGE_VIEW = "landing_page_view"
    CONTENT_VIEW = "content_view"

    # Conversion
    LEAD_FORM_SUBMIT = "lead_form_submit"
    ADD_TO_CART = "add_to_cart"
    CHECKOUT_STARTED = "checkout_started"
    PURCHASE = "purchase"

    # Engagement
    SOCIAL_ENGAGEMENT = "social_engagement"
    EMAIL_OPEN = "email_open"
    EMAIL_CLICK = "email_click"


class Platform(str, Enum):
    """Marketing platforms"""
    META = "meta"
    GOOGLE_ADS = "google_ads"
    GOOGLE_SEARCH = "google_search"
    LINKEDIN = "linkedin"
    TIKTOK = "tiktok"
    PINTEREST = "pinterest"
    TWITTER = "twitter"
    ORGANIC_SOCIAL = "organic_social"
    EMAIL = "email"
    DIRECT = "direct"
    REFERRAL = "referral"


class TouchpointEvent(BaseModel):
    """
    A single touchpoint in a customer journey

    This is the atomic unit of attribution - every customer interaction
    across all platforms gets logged as a TouchpointEvent
    """
    # Identity
    event_id: str = Field(..., description="Unique event identifier")
    user_id: Optional[str] = Field(None, description="Anonymized user identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    device_id: Optional[str] = Field(None, description="Device fingerprint")

    # Event details
    event_type: EventType = Field(..., description="Type of touchpoint")
    platform: Platform = Field(..., description="Marketing platform")
    timestamp: datetime = Field(..., description="When event occurred")

    # Campaign attribution
    campaign_id: Optional[str] = Field(None, description="Platform campaign ID")
    campaign_name: Optional[str] = Field(None, description="Human-readable campaign name")
    ad_set_id: Optional[str] = Field(None, description="Ad set/ad group ID")
    ad_id: Optional[str] = Field(None, description="Individual ad ID")

    # UTM parameters (for web tracking)
    utm_source: Optional[str] = Field(None, description="UTM source parameter")
    utm_medium: Optional[str] = Field(None, description="UTM medium parameter")
    utm_campaign: Optional[str] = Field(None, description="UTM campaign parameter")
    utm_content: Optional[str] = Field(None, description="UTM content parameter")
    utm_term: Optional[str] = Field(None, description="UTM term parameter")

    # Context
    page_url: Optional[str] = Field(None, description="Page where event occurred")
    referrer_url: Optional[str] = Field(None, description="Referring URL")
    device_type: Optional[str] = Field(None, description="mobile, desktop, tablet")
    browser: Optional[str] = Field(None, description="Browser name")
    os: Optional[str] = Field(None, description="Operating system")

    # Geo
    country: Optional[str] = Field(None, description="Country code (ISO)")
    region: Optional[str] = Field(None, description="State/region")
    city: Optional[str] = Field(None, description="City")

    # Value (for conversion events)
    revenue: Optional[float] = Field(None, description="Revenue attributed to event")
    currency: Optional[str] = Field("USD", description="Currency code")
    quantity: Optional[int] = Field(None, description="Number of items")

    # Engagement metrics
    time_on_page: Optional[float] = Field(None, description="Seconds on page")
    scroll_depth: Optional[float] = Field(None, description="Percentage scrolled (0-100)")

    # Metadata
    custom_data: Dict[str, Any] = Field(default_factory=dict, description="Platform-specific data")

    @property
    def attribution_key(self) -> str:
        """Generate unique key for deduplication"""
        key_parts = [
            str(self.user_id or ""),
            str(self.timestamp.timestamp()),
            self.event_type.value,
            self.platform.value
        ]
        return hashlib.md5("_".join(key_parts).encode()).hexdigest()


class ConversionEvent(BaseModel):
    """
    A conversion that we want to attribute to touchpoints

    This represents the "goal" - what we're trying to optimize for
    """
    conversion_id: str = Field(..., description="Unique conversion identifier")
    user_id: str = Field(..., description="User who converted")

    # Conversion details
    conversion_type: str = Field(..., description="purchase, lead, signup, etc.")
    timestamp: datetime = Field(..., description="When conversion occurred")

    # Value
    revenue: float = Field(0.0, description="Revenue from conversion")
    currency: str = Field("USD", description="Currency code")
    lifetime_value: Optional[float] = Field(None, description="Predicted LTV")

    # Attribution window
    attribution_window_days: int = Field(30, description="Days to look back for touchpoints")

    # Metadata
    order_id: Optional[str] = Field(None, description="Order/transaction ID")
    product_ids: List[str] = Field(default_factory=list, description="Products purchased")
    custom_data: Dict[str, Any] = Field(default_factory=dict)


class CustomerJourney(BaseModel):
    """
    Complete journey from first touchpoint to conversion

    This is what attribution models analyze to assign credit
    """
    journey_id: str = Field(..., description="Unique journey identifier")
    user_id: str = Field(..., description="User identifier")

    # Journey timeline
    first_touch: datetime = Field(..., description="First known touchpoint")
    last_touch: datetime = Field(..., description="Most recent touchpoint")
    conversion_time: Optional[datetime] = Field(None, description="Conversion timestamp")

    # Touchpoints (ordered chronologically)
    touchpoints: List[TouchpointEvent] = Field(default_factory=list)

    # Conversion
    conversion: Optional[ConversionEvent] = Field(None, description="Conversion if any")
    converted: bool = Field(False, description="Whether journey converted")

    # Journey metrics
    total_touchpoints: int = Field(0, description="Number of touchpoints")
    unique_platforms: int = Field(0, description="Number of different platforms")
    days_to_convert: Optional[float] = Field(None, description="Time to conversion in days")

    @classmethod
    def from_touchpoints(
        cls,
        user_id: str,
        touchpoints: List[TouchpointEvent],
        conversion: Optional[ConversionEvent] = None
    ) -> "CustomerJourney":
        """Construct journey from list of touchpoints"""
        if not touchpoints:
            raise ValueError("Journey must have at least one touchpoint")

        # Sort chronologically
        sorted_touchpoints = sorted(touchpoints, key=lambda t: t.timestamp)

        first_touch = sorted_touchpoints[0].timestamp
        last_touch = sorted_touchpoints[-1].timestamp

        journey_id = hashlib.md5(
            f"{user_id}_{first_touch.timestamp()}_{last_touch.timestamp()}".encode()
        ).hexdigest()

        unique_platforms = len(set(t.platform for t in touchpoints))

        days_to_convert = None
        conversion_time = None
        if conversion:
            conversion_time = conversion.timestamp
            days_to_convert = (conversion_time - first_touch).total_seconds() / 86400

        return cls(
            journey_id=journey_id,
            user_id=user_id,
            first_touch=first_touch,
            last_touch=last_touch,
            conversion_time=conversion_time,
            touchpoints=sorted_touchpoints,
            conversion=conversion,
            converted=conversion is not None,
            total_touchpoints=len(touchpoints),
            unique_platforms=unique_platforms,
            days_to_convert=days_to_convert
        )

    def get_touchpoints_by_platform(self, platform: Platform) -> List[TouchpointEvent]:
        """Get all touchpoints from specific platform"""
        return [t for t in self.touchpoints if t.platform == platform]

    def get_conversion_path(self) -> List[str]:
        """Get simplified conversion path (platforms only)"""
        return [t.platform.value for t in self.touchpoints]

    def get_unique_campaigns(self) -> List[str]:
        """Get list of unique campaign IDs in journey"""
        campaigns = set()
        for t in self.touchpoints:
            if t.campaign_id:
                campaigns.add(t.campaign_id)
        return list(campaigns)


class AttributionWindow(BaseModel):
    """Configuration for attribution window"""
    click_window_days: int = Field(30, description="Days after click to attribute")
    view_window_days: int = Field(7, description="Days after view to attribute")
    include_organic: bool = Field(True, description="Include organic touchpoints")
    min_touchpoints: int = Field(1, description="Minimum touchpoints required")


# Example journey schemas for different use cases

class EcommerceJourney(CustomerJourney):
    """E-commerce specific journey with product data"""
    products_viewed: List[str] = Field(default_factory=list)
    cart_value: Optional[float] = Field(None)
    discount_codes_used: List[str] = Field(default_factory=list)


class LeadGenJourney(CustomerJourney):
    """Lead generation journey with qualification scores"""
    lead_score: Optional[int] = Field(None, description="Lead quality score (0-100)")
    lead_source: Optional[str] = Field(None)
    sales_qualified: bool = Field(False)
    deal_value: Optional[float] = Field(None)


class SaaSJourney(CustomerJourney):
    """SaaS journey with trial/subscription data"""
    trial_started: bool = Field(False)
    trial_start_date: Optional[datetime] = Field(None)
    subscription_tier: Optional[str] = Field(None)
    mrr: Optional[float] = Field(None, description="Monthly recurring revenue")
