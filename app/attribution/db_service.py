"""
Attribution Database Service Layer
Handles all database operations for attribution engine
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
import uuid
import logging

from app.attribution.db_models import (
    AttributionTouchpoint,
    AttributionConversion,
    AttributionJourney,
    AttributionResult,
    AttributionModelState,
    AttributionBatchJob
)
from app.attribution.event_schema import (
    TouchpointEvent,
    ConversionEvent,
    CustomerJourney,
    Platform
)
from app.attribution.models import (
    AttributionResult as AttributionResultModel,
    AttributionModelType
)

logger = logging.getLogger(__name__)


class AttributionDatabaseService:
    """Service for attribution database operations"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== TOUCHPOINT OPERATIONS ====================

    def save_touchpoint(self, touchpoint: TouchpointEvent, journey_id: str) -> AttributionTouchpoint:
        """Save a touchpoint event to database"""
        db_touchpoint = AttributionTouchpoint(
            id=touchpoint.event_id,
            journey_id=journey_id,
            user_id=touchpoint.user_id,
            event_type=touchpoint.event_type.value if hasattr(touchpoint.event_type, 'value') else touchpoint.event_type,
            platform=touchpoint.platform.value,
            timestamp=touchpoint.timestamp,
            campaign_id=touchpoint.campaign_id,
            campaign_name=touchpoint.campaign_name,
            ad_set_id=touchpoint.ad_set_id,
            ad_id=touchpoint.ad_id,
            utm_source=touchpoint.utm_source,
            utm_medium=touchpoint.utm_medium,
            utm_campaign=touchpoint.utm_campaign,
            utm_content=touchpoint.utm_content,
            utm_term=touchpoint.utm_term,
            page_url=touchpoint.page_url,
            referrer_url=touchpoint.referrer_url,
            device_type=touchpoint.device_type,
            browser=touchpoint.browser,
            country=touchpoint.country,
            region=touchpoint.region,
            city=touchpoint.city,
            engagement_score=touchpoint.engagement_score,
            time_spent=touchpoint.time_spent,
            custom_data=touchpoint.custom_data
        )

        self.db.add(db_touchpoint)
        self.db.commit()
        self.db.refresh(db_touchpoint)

        logger.info(f"Saved touchpoint {touchpoint.event_id} for journey {journey_id}")
        return db_touchpoint

    def get_touchpoints_for_journey(self, journey_id: str) -> List[AttributionTouchpoint]:
        """Get all touchpoints for a journey"""
        return self.db.query(AttributionTouchpoint)\
            .filter(AttributionTouchpoint.journey_id == journey_id)\
            .order_by(AttributionTouchpoint.timestamp)\
            .all()

    def get_touchpoints_for_user(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AttributionTouchpoint]:
        """Get all touchpoints for a user within date range"""
        query = self.db.query(AttributionTouchpoint)\
            .filter(AttributionTouchpoint.user_id == user_id)

        if start_date:
            query = query.filter(AttributionTouchpoint.timestamp >= start_date)
        if end_date:
            query = query.filter(AttributionTouchpoint.timestamp <= end_date)

        return query.order_by(AttributionTouchpoint.timestamp).all()

    # ==================== CONVERSION OPERATIONS ====================

    def save_conversion(self, conversion: ConversionEvent, journey_id: str) -> AttributionConversion:
        """Save a conversion event to database"""
        db_conversion = AttributionConversion(
            id=conversion.conversion_id,
            journey_id=journey_id,
            user_id=conversion.user_id,
            conversion_type=conversion.conversion_type,
            timestamp=conversion.timestamp,
            revenue=conversion.revenue,
            currency=conversion.currency,
            quantity=conversion.quantity,
            attribution_window_days=conversion.attribution_window_days,
            order_id=conversion.order_id,
            product_ids=conversion.product_ids,
            product_names=conversion.product_names,
            conversion_page_url=conversion.conversion_page_url,
            device_type=conversion.device_type,
            custom_data=conversion.custom_data
        )

        self.db.add(db_conversion)
        self.db.commit()
        self.db.refresh(db_conversion)

        logger.info(f"Saved conversion {conversion.conversion_id} for journey {journey_id}")
        return db_conversion

    def get_conversion_for_journey(self, journey_id: str) -> Optional[AttributionConversion]:
        """Get conversion for a journey"""
        return self.db.query(AttributionConversion)\
            .filter(AttributionConversion.journey_id == journey_id)\
            .first()

    # ==================== JOURNEY OPERATIONS ====================

    def create_or_update_journey(
        self,
        journey: CustomerJourney,
        tenant_id: Optional[str] = None
    ) -> AttributionJourney:
        """Create or update a customer journey"""
        # Check if journey already exists
        db_journey = self.db.query(AttributionJourney)\
            .filter(AttributionJourney.id == journey.journey_id)\
            .first()

        if db_journey:
            # Update existing journey
            db_journey.total_touchpoints = journey.total_touchpoints
            db_journey.unique_platforms = journey.unique_platforms
            db_journey.platform_list = [p.value for p in journey.get_platforms()]
            db_journey.last_touch_at = journey.last_touch_at
            db_journey.converted = journey.converted

            if journey.conversion:
                db_journey.conversion_at = journey.conversion.timestamp
                db_journey.conversion_value = journey.conversion.revenue
                db_journey.conversion_type = journey.conversion.conversion_type
                db_journey.days_to_convert = journey.days_to_convert
        else:
            # Create new journey
            db_journey = AttributionJourney(
                id=journey.journey_id,
                user_id=journey.user_id,
                tenant_id=tenant_id,
                converted=journey.converted,
                total_touchpoints=journey.total_touchpoints,
                unique_platforms=journey.unique_platforms,
                platform_list=[p.value for p in journey.get_platforms()],
                first_touch_at=journey.first_touch_at,
                last_touch_at=journey.last_touch_at,
                journey_type=journey.journey_type
            )

            if journey.conversion:
                db_journey.conversion_at = journey.conversion.timestamp
                db_journey.conversion_value = journey.conversion.revenue
                db_journey.conversion_type = journey.conversion.conversion_type
                db_journey.days_to_convert = journey.days_to_convert

            self.db.add(db_journey)

        self.db.commit()
        self.db.refresh(db_journey)

        logger.info(f"Saved journey {journey.journey_id} for user {journey.user_id}")
        return db_journey

    def get_journey(self, journey_id: str) -> Optional[AttributionJourney]:
        """Get a journey by ID"""
        return self.db.query(AttributionJourney)\
            .filter(AttributionJourney.id == journey_id)\
            .first()

    def get_journey_for_user(
        self,
        user_id: str,
        active_only: bool = True
    ) -> Optional[AttributionJourney]:
        """Get the most recent journey for a user"""
        query = self.db.query(AttributionJourney)\
            .filter(AttributionJourney.user_id == user_id)

        if active_only:
            query = query.filter(AttributionJourney.converted == False)

        return query.order_by(desc(AttributionJourney.created_at)).first()

    def build_journey_from_db(self, journey_id: str) -> Optional[CustomerJourney]:
        """Build a CustomerJourney object from database"""
        db_journey = self.get_journey(journey_id)
        if not db_journey:
            return None

        # Get touchpoints
        db_touchpoints = self.get_touchpoints_for_journey(journey_id)
        touchpoints = [self._touchpoint_db_to_model(tp) for tp in db_touchpoints]

        # Get conversion
        db_conversion = self.get_conversion_for_journey(journey_id)
        conversion = self._conversion_db_to_model(db_conversion) if db_conversion else None

        # Build journey
        return CustomerJourney.from_touchpoints(
            user_id=db_journey.user_id,
            touchpoints=touchpoints,
            conversion=conversion
        )

    def get_recent_journeys(
        self,
        limit: int = 100,
        converted_only: bool = False,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        tenant_id: Optional[str] = None
    ) -> List[AttributionJourney]:
        """Get recent journeys"""
        query = self.db.query(AttributionJourney)

        if converted_only:
            query = query.filter(AttributionJourney.converted == True)

        if start_date:
            query = query.filter(AttributionJourney.created_at >= start_date)

        if end_date:
            query = query.filter(AttributionJourney.created_at <= end_date)

        if tenant_id:
            query = query.filter(AttributionJourney.tenant_id == tenant_id)

        return query.order_by(desc(AttributionJourney.created_at)).limit(limit).all()

    # ==================== ATTRIBUTION RESULT OPERATIONS ====================

    def save_attribution_result(
        self,
        result: AttributionResultModel,
        journey_id: str
    ) -> AttributionResult:
        """Save attribution analysis result"""
        # Serialize platform and campaign attribution
        platform_attr = [
            {
                "platform": pa.platform.value,
                "credit": pa.credit,
                "touchpoint_count": pa.touchpoint_count,
                "revenue_attributed": pa.revenue_attributed,
                "cost": pa.cost,
                "roi": pa.roi
            }
            for pa in result.platform_attribution
        ]

        campaign_attr = [
            {
                "campaign_id": ca.campaign_id,
                "campaign_name": ca.campaign_name,
                "platform": ca.platform.value,
                "credit": ca.credit,
                "touchpoint_count": ca.touchpoint_count,
                "revenue_attributed": ca.revenue_attributed,
                "cost": ca.cost,
                "roas": ca.roas,
                "first_touch_count": ca.first_touch_count,
                "last_touch_count": ca.last_touch_count,
                "middle_touch_count": ca.middle_touch_count
            }
            for ca in result.campaign_attribution
        ]

        db_result = AttributionResult(
            id=str(uuid.uuid4()),
            journey_id=journey_id,
            model_type=result.model_type.value,
            model_version=result.model_version,
            converted=result.converted,
            conversion_value=result.conversion_value,
            conversion_date=result.conversion_date,
            total_touchpoints=result.total_touchpoints,
            unique_platforms=result.unique_platforms,
            days_to_convert=result.days_to_convert,
            confidence_score=result.confidence_score,
            platform_attribution=platform_attr,
            campaign_attribution=campaign_attr,
            insights=result.insights,
            analyzed_at=result.analyzed_at
        )

        self.db.add(db_result)
        self.db.commit()
        self.db.refresh(db_result)

        logger.info(f"Saved attribution result for journey {journey_id} using {result.model_type.value}")
        return db_result

    def get_attribution_results_for_journey(
        self,
        journey_id: str,
        model_type: Optional[AttributionModelType] = None
    ) -> List[AttributionResult]:
        """Get attribution results for a journey"""
        query = self.db.query(AttributionResult)\
            .filter(AttributionResult.journey_id == journey_id)

        if model_type:
            query = query.filter(AttributionResult.model_type == model_type.value)

        return query.order_by(desc(AttributionResult.analyzed_at)).all()

    # ==================== MODEL STATE OPERATIONS ====================

    def save_model_state(
        self,
        model_type: str,
        model_state: Dict[str, Any],
        training_journeys_count: int,
        tenant_id: Optional[str] = None
    ) -> AttributionModelState:
        """Save trained model state"""
        # Deactivate previous model states
        self.db.query(AttributionModelState)\
            .filter(
                AttributionModelState.model_type == model_type,
                AttributionModelState.tenant_id == tenant_id,
                AttributionModelState.is_active == True
            )\
            .update({"is_active": False})

        db_state = AttributionModelState(
            id=str(uuid.uuid4()),
            model_type=model_type,
            tenant_id=tenant_id,
            trained_at=datetime.now(),
            training_journeys_count=training_journeys_count,
            model_state=model_state,
            is_active=True,
            is_trained=True
        )

        self.db.add(db_state)
        self.db.commit()
        self.db.refresh(db_state)

        logger.info(f"Saved model state for {model_type}")
        return db_state

    def get_active_model_state(
        self,
        model_type: str,
        tenant_id: Optional[str] = None
    ) -> Optional[AttributionModelState]:
        """Get active model state"""
        return self.db.query(AttributionModelState)\
            .filter(
                AttributionModelState.model_type == model_type,
                AttributionModelState.tenant_id == tenant_id,
                AttributionModelState.is_active == True,
                AttributionModelState.is_trained == True
            )\
            .first()

    # ==================== HELPER METHODS ====================

    def _touchpoint_db_to_model(self, db_touchpoint: AttributionTouchpoint) -> TouchpointEvent:
        """Convert database touchpoint to model"""
        return TouchpointEvent(
            event_id=db_touchpoint.id,
            user_id=db_touchpoint.user_id,
            event_type=db_touchpoint.event_type,
            platform=Platform(db_touchpoint.platform),
            timestamp=db_touchpoint.timestamp,
            campaign_id=db_touchpoint.campaign_id,
            campaign_name=db_touchpoint.campaign_name,
            ad_set_id=db_touchpoint.ad_set_id,
            ad_id=db_touchpoint.ad_id,
            utm_source=db_touchpoint.utm_source,
            utm_medium=db_touchpoint.utm_medium,
            utm_campaign=db_touchpoint.utm_campaign,
            utm_content=db_touchpoint.utm_content,
            utm_term=db_touchpoint.utm_term,
            page_url=db_touchpoint.page_url,
            referrer_url=db_touchpoint.referrer_url,
            device_type=db_touchpoint.device_type,
            browser=db_touchpoint.browser,
            country=db_touchpoint.country,
            region=db_touchpoint.region,
            city=db_touchpoint.city,
            engagement_score=db_touchpoint.engagement_score,
            time_spent=db_touchpoint.time_spent,
            custom_data=db_touchpoint.custom_data
        )

    def _conversion_db_to_model(self, db_conversion: AttributionConversion) -> ConversionEvent:
        """Convert database conversion to model"""
        return ConversionEvent(
            conversion_id=db_conversion.id,
            user_id=db_conversion.user_id,
            conversion_type=db_conversion.conversion_type,
            timestamp=db_conversion.timestamp,
            revenue=db_conversion.revenue,
            currency=db_conversion.currency,
            quantity=db_conversion.quantity,
            attribution_window_days=db_conversion.attribution_window_days,
            order_id=db_conversion.order_id,
            product_ids=db_conversion.product_ids,
            product_names=db_conversion.product_names,
            conversion_page_url=db_conversion.conversion_page_url,
            device_type=db_conversion.device_type,
            custom_data=db_conversion.custom_data
        )

    # ==================== ANALYTICS QUERIES ====================

    def get_platform_performance(
        self,
        start_date: datetime,
        end_date: datetime,
        tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get aggregated platform performance"""
        # This would use SQL aggregation for efficient reporting
        # Placeholder for now
        pass

    def get_campaign_performance(
        self,
        start_date: datetime,
        end_date: datetime,
        platform: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get aggregated campaign performance"""
        # This would use SQL aggregation for efficient reporting
        pass
