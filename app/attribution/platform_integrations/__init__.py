"""
Platform Integrations for Attribution Engine
Integrates with Meta, Google, LinkedIn, etc. for server-side tracking
"""

from app.attribution.platform_integrations.meta_conversions import (
    MetaConversionsAPIClient,
    MetaUserData,
    MetaCustomData,
    MetaConversionEvent,
    get_meta_client
)
from app.attribution.platform_integrations.google_analytics import (
    GA4MeasurementProtocolClient,
    GA4Event,
    GA4UserProperties,
    get_ga4_client
)

__all__ = [
    # Meta
    "MetaConversionsAPIClient",
    "MetaUserData",
    "MetaCustomData",
    "MetaConversionEvent",
    "get_meta_client",
    # Google Analytics 4
    "GA4MeasurementProtocolClient",
    "GA4Event",
    "GA4UserProperties",
    "get_ga4_client",
]
