"""
Attribution Engine Database Models
SQLAlchemy models for persisting attribution data
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


class AttributionTouchpoint(Base):
    """
    Individual touchpoint event in a customer journey
    Stores every marketing interaction across all platforms
    """
    __tablename__ = "attribution_touchpoints"

    # Primary key
    id = Column(String, primary_key=True)  # event_id from TouchpointEvent

    # Journey relationship
    journey_id = Column(String, ForeignKey("attribution_journeys.id"), nullable=False, index=True)

    # User identification
    user_id = Column(String, index=True)  # May be null for anonymous

    # Event details
    event_type = Column(String, nullable=False)  # click, impression, view, etc.
    platform = Column(String, nullable=False, index=True)  # meta, google_ads, linkedin, etc.
    timestamp = Column(DateTime, nullable=False, index=True)

    # Campaign details
    campaign_id = Column(String, index=True)
    campaign_name = Column(String)
    ad_set_id = Column(String)
    ad_id = Column(String)

    # UTM parameters
    utm_source = Column(String)
    utm_medium = Column(String)
    utm_campaign = Column(String)
    utm_content = Column(String)
    utm_term = Column(String)

    # Context
    page_url = Column(Text)
    referrer_url = Column(Text)
    device_type = Column(String)
    browser = Column(String)

    # Geo
    country = Column(String)
    region = Column(String)
    city = Column(String)

    # Engagement metrics (for impression events)
    engagement_score = Column(Float)
    time_spent = Column(Float)  # seconds

    # Custom data (platform-specific metadata)
    custom_data = Column(JSON, default=dict)

    # Metadata
    created_at = Column(DateTime, server_default=func.now())

    # Indexes for common queries
    __table_args__ = (
        Index('idx_touchpoint_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_touchpoint_platform_timestamp', 'platform', 'timestamp'),
        Index('idx_touchpoint_campaign', 'campaign_id', 'timestamp'),
    )

    def __repr__(self):
        return f"<Touchpoint(id='{self.id}', platform='{self.platform}', type='{self.event_type}')>"


class AttributionConversion(Base):
    """
    Conversion event (purchase, lead, signup, etc.)
    The outcome we're attributing credit to
    """
    __tablename__ = "attribution_conversions"

    # Primary key
    id = Column(String, primary_key=True)  # conversion_id

    # Journey relationship
    journey_id = Column(String, ForeignKey("attribution_journeys.id"), nullable=False, index=True)

    # User identification
    user_id = Column(String, nullable=False, index=True)

    # Conversion details
    conversion_type = Column(String, nullable=False)  # purchase, lead, signup, etc.
    timestamp = Column(DateTime, nullable=False, index=True)

    # Value
    revenue = Column(Float, default=0.0)
    currency = Column(String, default="USD")
    quantity = Column(Integer, default=1)

    # Attribution window
    attribution_window_days = Column(Integer, default=30)

    # Order/transaction details
    order_id = Column(String, index=True)
    product_ids = Column(JSON, default=list)  # List of product IDs
    product_names = Column(JSON, default=list)

    # Context
    conversion_page_url = Column(Text)
    device_type = Column(String)

    # Custom data
    custom_data = Column(JSON, default=dict)

    # Metadata
    created_at = Column(DateTime, server_default=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_conversion_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_conversion_timestamp', 'timestamp'),
    )

    def __repr__(self):
        return f"<Conversion(id='{self.id}', type='{self.conversion_type}', revenue={self.revenue})>"


class AttributionJourney(Base):
    """
    Complete customer journey from first touch to conversion (or not)
    Aggregates all touchpoints for a user
    """
    __tablename__ = "attribution_journeys"

    # Primary key
    id = Column(String, primary_key=True)  # journey_id

    # User identification
    user_id = Column(String, nullable=False, index=True)

    # Tenant (for multi-tenancy)
    tenant_id = Column(String, index=True)

    # Journey status
    converted = Column(Boolean, default=False, index=True)
    conversion_id = Column(String, ForeignKey("attribution_conversions.id"))

    # Journey metrics
    total_touchpoints = Column(Integer, default=0)
    unique_platforms = Column(Integer, default=0)
    platform_list = Column(JSON, default=list)  # List of platform names

    # Timeline
    first_touch_at = Column(DateTime, index=True)
    last_touch_at = Column(DateTime)
    conversion_at = Column(DateTime)
    days_to_convert = Column(Float)  # Duration from first touch to conversion

    # Value
    conversion_value = Column(Float, default=0.0)
    conversion_type = Column(String)  # purchase, lead, etc.

    # Journey classification
    journey_type = Column(String)  # ecommerce, lead_gen, saas, etc.

    # Relationships
    touchpoints = relationship("AttributionTouchpoint", backref="journey", lazy="dynamic")
    conversion = relationship("AttributionConversion", backref="journey", uselist=False)
    attribution_results = relationship("AttributionResult", backref="journey", lazy="dynamic")

    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_journey_user_converted', 'user_id', 'converted'),
        Index('idx_journey_converted_timestamp', 'converted', 'conversion_at'),
        Index('idx_journey_tenant', 'tenant_id', 'created_at'),
    )

    def __repr__(self):
        return f"<Journey(id='{self.id}', user='{self.user_id}', converted={self.converted}, touchpoints={self.total_touchpoints})>"


class AttributionResult(Base):
    """
    Attribution analysis result for a journey
    Stores the output of Shapley, Markov, or other attribution models
    """
    __tablename__ = "attribution_results"

    # Primary key
    id = Column(String, primary_key=True)

    # Journey relationship
    journey_id = Column(String, ForeignKey("attribution_journeys.id"), nullable=False, index=True)

    # Attribution model used
    model_type = Column(String, nullable=False, index=True)  # shapley, markov, linear, etc.
    model_version = Column(String, default="1.0.0")

    # Results
    converted = Column(Boolean, nullable=False)
    conversion_value = Column(Float, default=0.0)
    conversion_date = Column(DateTime)

    # Journey stats
    total_touchpoints = Column(Integer)
    unique_platforms = Column(Integer)
    days_to_convert = Column(Float)

    # Model confidence
    confidence_score = Column(Float, default=0.0)

    # Platform attribution (stored as JSON array)
    platform_attribution = Column(JSON, default=list)  # List of {platform, credit, revenue, etc}

    # Campaign attribution (stored as JSON array)
    campaign_attribution = Column(JSON, default=list)  # List of {campaign_id, credit, revenue, etc}

    # AI-generated insights
    insights = Column(JSON, default=list)  # List of insight strings

    # Metadata
    analyzed_at = Column(DateTime, server_default=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_result_journey_model', 'journey_id', 'model_type'),
        Index('idx_result_model_analyzed', 'model_type', 'analyzed_at'),
    )

    def __repr__(self):
        return f"<AttributionResult(journey='{self.journey_id}', model='{self.model_type}', converted={self.converted})>"


class AttributionModelState(Base):
    """
    Persisted state for attribution models (especially Markov)
    Stores trained model parameters, transitions, etc.
    """
    __tablename__ = "attribution_model_states"

    # Primary key
    id = Column(String, primary_key=True)

    # Model identification
    model_type = Column(String, nullable=False, index=True)
    model_version = Column(String, default="1.0.0")
    tenant_id = Column(String, index=True)  # For multi-tenant models

    # Training info
    trained_at = Column(DateTime, nullable=False)
    training_data_start = Column(DateTime)
    training_data_end = Column(DateTime)
    training_journeys_count = Column(Integer)

    # Model parameters (serialized as JSON)
    model_params = Column(JSON, default=dict)  # config parameters
    model_state = Column(JSON, default=dict)  # learned weights, transitions, etc.

    # For Markov models specifically
    transition_matrix = Column(JSON, default=dict)  # State transitions
    state_counts = Column(JSON, default=dict)  # State frequency
    conversion_probs = Column(JSON, default=dict)  # P(conversion | state)

    # Model performance
    accuracy_metrics = Column(JSON, default=dict)  # Accuracy, precision, recall, etc.
    validation_score = Column(Float)

    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_trained = Column(Boolean, default=False)

    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_model_state_active', 'model_type', 'is_active', 'tenant_id'),
    )

    def __repr__(self):
        return f"<ModelState(type='{self.model_type}', trained={self.is_trained}, active={self.is_active})>"


class AttributionBatchJob(Base):
    """
    Track batch attribution analysis jobs
    For processing large numbers of journeys
    """
    __tablename__ = "attribution_batch_jobs"

    # Primary key
    id = Column(String, primary_key=True)

    # Job details
    tenant_id = Column(String, index=True)
    user_id = Column(String)  # Who started the job

    # Job type
    job_type = Column(String, nullable=False)  # batch_analysis, model_training, cohort_analysis
    model_type = Column(String)  # Which attribution model

    # Parameters
    params = Column(JSON, default=dict)  # Start/end dates, filters, etc.

    # Status
    status = Column(String, default="pending", index=True)  # pending, running, completed, failed
    progress = Column(Float, default=0.0)  # 0.0 to 1.0

    # Results
    journeys_processed = Column(Integer, default=0)
    journeys_total = Column(Integer)
    results_summary = Column(JSON, default=dict)  # Aggregated results

    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)

    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)

    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_batch_job_status', 'tenant_id', 'status', 'created_at'),
    )

    def __repr__(self):
        return f"<BatchJob(id='{self.id}', type='{self.job_type}', status='{self.status}', progress={self.progress})>"
