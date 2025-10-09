"""
Multi-Platform Attribution Engine
AI-powered attribution across Meta, Google, LinkedIn, TikTok, and more
"""
from app.attribution.event_schema import (
    EventType,
    Platform,
    TouchpointEvent,
    ConversionEvent,
    CustomerJourney,
    AttributionWindow,
    EcommerceJourney,
    LeadGenJourney,
    SaaSJourney
)
from app.attribution.models import (
    AttributionModel,
    AttributionModelType,
    AttributionResult,
    PlatformAttribution,
    CampaignAttribution
)
from app.attribution.shapley import ShapleyAttributionModel
from app.attribution.markov import MarkovChainAttributionModel

__all__ = [
    # Event schema
    "EventType",
    "Platform",
    "TouchpointEvent",
    "ConversionEvent",
    "CustomerJourney",
    "AttributionWindow",
    "EcommerceJourney",
    "LeadGenJourney",
    "SaaSJourney",
    # Models
    "AttributionModel",
    "AttributionModelType",
    "AttributionResult",
    "PlatformAttribution",
    "CampaignAttribution",
    "ShapleyAttributionModel",
    "MarkovChainAttributionModel",
]
