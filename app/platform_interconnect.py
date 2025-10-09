"""
Universal Platform Interconnectivity Engine
Cross-Platform Communication, Data Sync, and ML-Driven Automation

This system enables all platforms to communicate and share data intelligently,
creating a unified ecosystem where insights from one platform trigger actions
across the entire suite.
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)

class PlatformType(Enum):
    """Supported platform types"""
    CRM = "crm"  # HubSpot, Salesforce, Pipedrive
    ADS = "ads"  # Google Ads, Facebook Ads, LinkedIn Ads
    EMAIL = "email"  # Mailchimp, ConvertKit, ActiveCampaign
    ANALYTICS = "analytics"  # Google Analytics, Mixpanel
    SOCIAL = "social"  # Facebook, LinkedIn, Twitter
    ECOMMERCE = "ecommerce"  # Shopify, WooCommerce
    PROJECT = "project"  # Asana, Monday, Trello
    COMMUNICATION = "communication"  # Slack, Teams, Discord
    FINANCE = "finance"  # QuickBooks, Stripe, PayPal
    CONTENT = "content"  # WordPress, Ghost, Webflow
    VIDEO = "video"  # Zoom, Loom, Calendly
    AUTOMATION = "automation"  # Zapier, Make, PulseBridge

@dataclass
class PlatformConnection:
    """Represents a connection to a specific platform"""
    platform_id: str
    platform_type: PlatformType
    platform_name: str
    api_credentials: Dict[str, str]
    connection_status: str
    last_sync: datetime
    sync_frequency: int  # minutes
    data_mapping: Dict[str, str]
    capabilities: List[str]
    webhook_url: Optional[str] = None
    rate_limits: Optional[Dict[str, int]] = None
    
    def is_healthy(self) -> bool:
        """Check if platform connection is healthy"""
        if self.connection_status != "active":
            return False
        
        # Check if last sync was within expected frequency
        time_since_sync = datetime.now() - self.last_sync
        max_sync_gap = timedelta(minutes=self.sync_frequency * 2)
        
        return time_since_sync <= max_sync_gap

@dataclass
class CrossPlatformEvent:
    """Event that can trigger actions across platforms"""
    event_id: str
    source_platform: str
    event_type: str
    event_data: Dict[str, Any]
    timestamp: datetime
    confidence_score: float  # ML-driven confidence
    suggested_actions: List[Dict[str, Any]]
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            **asdict(self),
            'timestamp': self.timestamp.isoformat(),
        }

@dataclass
class AutomationRule:
    """Rule for cross-platform automation"""
    rule_id: str
    name: str
    trigger_conditions: Dict[str, Any]
    source_platforms: List[str]
    target_platforms: List[str]
    actions: List[Dict[str, Any]]
    ml_scoring: bool
    confidence_threshold: float
    is_active: bool
    execution_count: int = 0
    success_rate: float = 0.0

class PlatformInterconnectEngine:
    """
    Core engine for cross-platform interconnectivity
    Manages connections, data flow, and intelligent automation
    """
    
    def __init__(self):
        self.connections: Dict[str, PlatformConnection] = {}
        self.event_queue: List[CrossPlatformEvent] = []
        self.automation_rules: Dict[str, AutomationRule] = {}
        self.data_sync_cache: Dict[str, Any] = {}
        self.ml_insights: Dict[str, Any] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
        # Initialize with default automation rules
        self._initialize_default_rules()
        
        logger.info("🔗 Platform Interconnect Engine initialized")
    
    def _initialize_default_rules(self):
        """Initialize default cross-platform automation rules"""
        
        # Rule 1: Lead scoring triggers CRM and email campaigns
        lead_scoring_rule = AutomationRule(
            rule_id="lead_score_automation",
            name="High-Value Lead Cross-Platform Action",
            trigger_conditions={
                "event_type": "lead_scored",
                "min_score": 80,
                "platforms": ["lead_scoring", "crm"]
            },
            source_platforms=["lead_scoring"],
            target_platforms=["hubspot", "mailchimp", "slack"],
            actions=[
                {
                    "platform": "hubspot",
                    "action": "create_hot_lead",
                    "data_mapping": {
                        "email": "lead_email",
                        "score": "lead_score",
                        "source": "ai_scoring"
                    }
                },
                {
                    "platform": "mailchimp",
                    "action": "add_to_nurture_sequence",
                    "sequence_type": "high_value_leads"
                },
                {
                    "platform": "slack",
                    "action": "notify_sales_team",
                    "channel": "#hot-leads"
                }
            ],
            ml_scoring=True,
            confidence_threshold=0.8,
            is_active=True
        )
        
        # Rule 2: Ad campaign performance triggers budget optimization
        ad_optimization_rule = AutomationRule(
            rule_id="ad_budget_optimization",
            name="ML-Driven Ad Budget Reallocation",
            trigger_conditions={
                "event_type": "campaign_performance_analyzed",
                "metrics": ["cpa", "roas", "conversion_rate"],
                "variance_threshold": 0.2
            },
            source_platforms=["google_ads", "facebook_ads"],
            target_platforms=["google_ads", "facebook_ads", "slack", "analytics"],
            actions=[
                {
                    "platform": "google_ads",
                    "action": "adjust_budget",
                    "ml_driven": True
                },
                {
                    "platform": "facebook_ads", 
                    "action": "pause_underperforming",
                    "threshold": "bottom_20_percent"
                },
                {
                    "platform": "analytics",
                    "action": "log_optimization_event"
                }
            ],
            ml_scoring=True,
            confidence_threshold=0.75,
            is_active=True
        )
        
        # Rule 3: Customer behavior triggers personalized campaigns
        behavior_campaign_rule = AutomationRule(
            rule_id="behavior_triggered_campaigns",
            name="Behavioral Trigger Cross-Platform Campaigns",
            trigger_conditions={
                "event_type": "customer_behavior_pattern",
                "patterns": ["high_engagement", "purchase_intent", "churn_risk"]
            },
            source_platforms=["analytics", "crm"],
            target_platforms=["email", "ads", "social"],
            actions=[
                {
                    "platform": "mailchimp",
                    "action": "trigger_personalized_campaign",
                    "personalization_level": "high"
                },
                {
                    "platform": "facebook_ads",
                    "action": "create_lookalike_audience"
                },
                {
                    "platform": "linkedin",
                    "action": "retarget_engagement_campaign"
                }
            ],
            ml_scoring=True,
            confidence_threshold=0.7,
            is_active=True
        )
        
        # Store all default rules
        self.automation_rules = {
            rule.rule_id: rule for rule in [
                lead_scoring_rule,
                ad_optimization_rule, 
                behavior_campaign_rule
            ]
        }
        
        logger.info(f"✅ Initialized {len(self.automation_rules)} default automation rules")
    
    async def register_platform(self, connection: PlatformConnection) -> bool:
        """Register a new platform connection"""
        try:
            # Validate connection
            if not await self._validate_platform_connection(connection):
                logger.error(f"❌ Failed to validate connection for {connection.platform_name}")
                return False
            
            # Store connection
            self.connections[connection.platform_id] = connection
            
            # Set up data sync
            await self._setup_data_sync(connection)
            
            # Initialize platform-specific configurations
            await self._initialize_platform_config(connection)
            
            logger.info(f"✅ Registered platform: {connection.platform_name} ({connection.platform_type.value})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error registering platform {connection.platform_name}: {e}")
            return False
    
    async def _validate_platform_connection(self, connection: PlatformConnection) -> bool:
        """Validate that platform connection is working"""
        try:
            # Basic validation
            if not connection.api_credentials:
                return False
            
            # Platform-specific validation
            if connection.platform_type == PlatformType.CRM:
                return await self._validate_crm_connection(connection)
            elif connection.platform_type == PlatformType.ADS:
                return await self._validate_ads_connection(connection)
            elif connection.platform_type == PlatformType.EMAIL:
                return await self._validate_email_connection(connection)
            else:
                # Generic validation - check if credentials exist
                return bool(connection.api_credentials.get('api_key') or 
                           connection.api_credentials.get('access_token'))
                
        except Exception as e:
            logger.error(f"Validation error for {connection.platform_name}: {e}")
            return False
    
    async def _validate_crm_connection(self, connection: PlatformConnection) -> bool:
        """Validate CRM platform connection"""
        # Simulate CRM validation
        required_fields = ['api_key', 'domain']
        return all(field in connection.api_credentials for field in required_fields)
    
    async def _validate_ads_connection(self, connection: PlatformConnection) -> bool:
        """Validate ads platform connection"""
        # Simulate ads platform validation
        required_fields = ['access_token', 'account_id']
        return all(field in connection.api_credentials for field in required_fields)
    
    async def _validate_email_connection(self, connection: PlatformConnection) -> bool:
        """Validate email platform connection"""
        # Simulate email platform validation
        required_fields = ['api_key']
        return all(field in connection.api_credentials for field in required_fields)
    
    async def _setup_data_sync(self, connection: PlatformConnection):
        """Set up data synchronization for platform"""
        sync_config = {
            'platform_id': connection.platform_id,
            'sync_frequency': connection.sync_frequency,
            'last_sync': connection.last_sync,
            'data_mapping': connection.data_mapping
        }
        
        # Schedule periodic sync
        asyncio.create_task(self._periodic_sync(connection.platform_id))
        
        logger.info(f"📊 Data sync configured for {connection.platform_name}")
    
    async def _initialize_platform_config(self, connection: PlatformConnection):
        """Initialize platform-specific configurations"""
        config = {
            'webhooks_enabled': bool(connection.webhook_url),
            'rate_limits': connection.rate_limits or {},
            'capabilities': connection.capabilities,
            'ml_integration': connection.platform_type in [
                PlatformType.CRM, PlatformType.ADS, PlatformType.EMAIL, PlatformType.ANALYTICS
            ]
        }
        
        # Store platform config
        self.data_sync_cache[f"{connection.platform_id}_config"] = config
        
        logger.info(f"⚙️ Platform configuration initialized for {connection.platform_name}")
    
    async def _periodic_sync(self, platform_id: str):
        """Periodic data synchronization for platform"""
        while platform_id in self.connections:
            try:
                connection = self.connections[platform_id]
                
                if connection.is_healthy():
                    # Perform data sync
                    await self._sync_platform_data(platform_id)
                    
                    # Update last sync time
                    self.connections[platform_id].last_sync = datetime.now()
                
                # Wait for next sync cycle
                await asyncio.sleep(connection.sync_frequency * 60)
                
            except Exception as e:
                logger.error(f"Error in periodic sync for {platform_id}: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _sync_platform_data(self, platform_id: str):
        """Synchronize data from platform"""
        connection = self.connections[platform_id]
        
        try:
            # Platform-specific data sync logic
            if connection.platform_type == PlatformType.CRM:
                data = await self._sync_crm_data(connection)
            elif connection.platform_type == PlatformType.ADS:
                data = await self._sync_ads_data(connection)
            elif connection.platform_type == PlatformType.EMAIL:
                data = await self._sync_email_data(connection)
            elif connection.platform_type == PlatformType.ANALYTICS:
                data = await self._sync_analytics_data(connection)
            else:
                data = await self._sync_generic_data(connection)
            
            # Store synced data
            self.data_sync_cache[f"{platform_id}_data"] = {
                'data': data,
                'sync_time': datetime.now(),
                'record_count': len(data) if isinstance(data, list) else 1
            }
            
            # Process data for ML insights
            await self._process_ml_insights(platform_id, data)
            
            # Check for automation triggers
            await self._check_automation_triggers(platform_id, data)
            
            logger.info(f"📥 Data synced for {connection.platform_name}")
            
        except Exception as e:
            logger.error(f"Error syncing data for {platform_id}: {e}")
    
    async def _sync_crm_data(self, connection: PlatformConnection) -> List[Dict[str, Any]]:
        """Sync CRM data (leads, contacts, deals)"""
        # Simulate CRM data sync
        return [
            {
                "id": f"crm_lead_{i}",
                "email": f"lead{i}@example.com",
                "status": "new" if i % 3 == 0 else "qualified",
                "score": 75 + (i % 25),
                "source": "website",
                "created_date": datetime.now().isoformat()
            }
            for i in range(10)
        ]
    
    async def _sync_ads_data(self, connection: PlatformConnection) -> List[Dict[str, Any]]:
        """Sync ads platform data (campaigns, performance)"""
        # Simulate ads data sync
        return [
            {
                "campaign_id": f"camp_{i}",
                "campaign_name": f"Campaign {i}",
                "spend": 1000 + (i * 100),
                "clicks": 500 + (i * 50),
                "conversions": 25 + (i * 2),
                "cpa": 40 + (i % 20),
                "status": "active"
            }
            for i in range(5)
        ]
    
    async def _sync_email_data(self, connection: PlatformConnection) -> List[Dict[str, Any]]:
        """Sync email platform data (campaigns, subscribers)"""
        # Simulate email data sync
        return [
            {
                "campaign_id": f"email_{i}",
                "subject": f"Email Campaign {i}",
                "open_rate": 0.2 + (i % 10) * 0.01,
                "click_rate": 0.05 + (i % 5) * 0.01,
                "subscribers": 1000 + (i * 100),
                "sent_date": datetime.now().isoformat()
            }
            for i in range(8)
        ]
    
    async def _sync_analytics_data(self, connection: PlatformConnection) -> List[Dict[str, Any]]:
        """Sync analytics data (traffic, conversions)"""
        # Simulate analytics data sync
        return [
            {
                "date": (datetime.now() - timedelta(days=i)).isoformat(),
                "sessions": 1000 + (i * 50),
                "users": 800 + (i * 40),
                "page_views": 3000 + (i * 150),
                "bounce_rate": 0.4 + (i % 10) * 0.01,
                "conversion_rate": 0.02 + (i % 5) * 0.001
            }
            for i in range(7)
        ]
    
    async def _sync_generic_data(self, connection: PlatformConnection) -> Dict[str, Any]:
        """Sync generic platform data"""
        return {
            "platform": connection.platform_name,
            "sync_time": datetime.now().isoformat(),
            "status": "healthy",
            "data_points": 100
        }
    
    async def _process_ml_insights(self, platform_id: str, data: Any):
        """Process data through ML models for insights"""
        try:
            connection = self.connections[platform_id]
            
            # Generate ML insights based on platform type
            insights = {}
            
            if connection.platform_type == PlatformType.CRM:
                insights = await self._generate_crm_insights(data)
            elif connection.platform_type == PlatformType.ADS:
                insights = await self._generate_ads_insights(data)
            elif connection.platform_type == PlatformType.EMAIL:
                insights = await self._generate_email_insights(data)
            elif connection.platform_type == PlatformType.ANALYTICS:
                insights = await self._generate_analytics_insights(data)
            
            # Store insights
            self.ml_insights[platform_id] = {
                'insights': insights,
                'generated_at': datetime.now(),
                'confidence_score': insights.get('confidence', 0.5)
            }
            
            logger.info(f"🧠 ML insights generated for {connection.platform_name}")
            
        except Exception as e:
            logger.error(f"Error processing ML insights for {platform_id}: {e}")
    
    async def _generate_crm_insights(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate ML insights from CRM data"""
        if not data:
            return {}
        
        # Analyze lead quality and patterns
        total_leads = len(data)
        high_score_leads = len([lead for lead in data if lead.get('score', 0) > 80])
        
        return {
            'lead_quality_score': high_score_leads / total_leads if total_leads > 0 else 0,
            'recommended_actions': [
                'Focus on high-score leads for immediate follow-up',
                'Create nurture sequence for medium-score leads'
            ],
            'confidence': 0.85,
            'priority_leads': [lead for lead in data if lead.get('score', 0) > 85]
        }
    
    async def _generate_ads_insights(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate ML insights from ads data"""
        if not data:
            return {}
        
        # Analyze campaign performance
        total_spend = sum(camp.get('spend', 0) for camp in data)
        total_conversions = sum(camp.get('conversions', 0) for camp in data)
        avg_cpa = total_spend / total_conversions if total_conversions > 0 else 0
        
        # Identify top and bottom performers
        sorted_campaigns = sorted(data, key=lambda x: x.get('conversions', 0), reverse=True)
        
        return {
            'overall_cpa': avg_cpa,
            'top_performers': sorted_campaigns[:2],
            'underperformers': sorted_campaigns[-2:],
            'recommended_actions': [
                'Increase budget for top-performing campaigns',
                'Pause or optimize underperforming campaigns'
            ],
            'confidence': 0.9,
            'budget_reallocation': True
        }
    
    async def _generate_email_insights(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate ML insights from email data"""
        if not data:
            return {}
        
        # Analyze email performance
        avg_open_rate = sum(camp.get('open_rate', 0) for camp in data) / len(data)
        avg_click_rate = sum(camp.get('click_rate', 0) for camp in data) / len(data)
        
        return {
            'avg_open_rate': avg_open_rate,
            'avg_click_rate': avg_click_rate,
            'performance_trend': 'improving' if avg_open_rate > 0.25 else 'needs_attention',
            'recommended_actions': [
                'A/B test subject lines for better open rates',
                'Segment audience for targeted campaigns'
            ],
            'confidence': 0.8
        }
    
    async def _generate_analytics_insights(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate ML insights from analytics data"""
        if not data:
            return {}
        
        # Analyze traffic patterns
        total_sessions = sum(day.get('sessions', 0) for day in data)
        avg_conversion_rate = sum(day.get('conversion_rate', 0) for day in data) / len(data)
        
        return {
            'traffic_trend': 'growing' if total_sessions > 7000 else 'stable',
            'avg_conversion_rate': avg_conversion_rate,
            'optimization_opportunities': [
                'Improve page load speed',
                'Optimize conversion funnels'
            ],
            'confidence': 0.75
        }
    
    async def _check_automation_triggers(self, platform_id: str, data: Any):
        """Check if data triggers any automation rules"""
        try:
            for rule_id, rule in self.automation_rules.items():
                if not rule.is_active:
                    continue
                
                # Check if this platform is a source for this rule
                if platform_id not in rule.source_platforms and \
                   self.connections[platform_id].platform_type.value not in rule.source_platforms:
                    continue
                
                # Evaluate trigger conditions
                if await self._evaluate_trigger_conditions(rule, platform_id, data):
                    # Create and queue cross-platform event
                    event = CrossPlatformEvent(
                        event_id=self._generate_event_id(rule_id, platform_id),
                        source_platform=platform_id,
                        event_type=rule.trigger_conditions.get('event_type', 'automation_trigger'),
                        event_data=data,
                        timestamp=datetime.now(),
                        confidence_score=self.ml_insights.get(platform_id, {}).get('confidence_score', 0.5),
                        suggested_actions=rule.actions
                    )
                    
                    self.event_queue.append(event)
                    
                    # Execute automation if confidence is high enough
                    if event.confidence_score >= rule.confidence_threshold:
                        await self._execute_automation_rule(rule, event)
                    
                    logger.info(f"🎯 Automation triggered: {rule.name}")
        
        except Exception as e:
            logger.error(f"Error checking automation triggers: {e}")
    
    async def _evaluate_trigger_conditions(self, rule: AutomationRule, platform_id: str, data: Any) -> bool:
        """Evaluate if trigger conditions are met"""
        try:
            conditions = rule.trigger_conditions
            
            # Check event type matches
            if 'event_type' in conditions:
                # This would normally come from the event, for now we simulate
                return True
            
            # Check ML insights if available
            insights = self.ml_insights.get(platform_id, {}).get('insights', {})
            
            # Example condition evaluation
            if 'min_score' in conditions and insights:
                if insights.get('lead_quality_score', 0) * 100 >= conditions['min_score']:
                    return True
            
            if 'performance_threshold' in conditions and insights:
                if insights.get('avg_conversion_rate', 0) >= conditions['performance_threshold']:
                    return True
            
            return True  # For demo purposes, we'll trigger automation
            
        except Exception as e:
            logger.error(f"Error evaluating trigger conditions: {e}")
            return False
    
    def _generate_event_id(self, rule_id: str, platform_id: str) -> str:
        """Generate unique event ID"""
        timestamp = datetime.now().isoformat()
        content = f"{rule_id}_{platform_id}_{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    async def _execute_automation_rule(self, rule: AutomationRule, event: CrossPlatformEvent):
        """Execute cross-platform automation actions"""
        try:
            execution_results = []
            
            for action in rule.actions:
                target_platform = action.get('platform')
                action_type = action.get('action')
                
                # Execute action on target platform
                result = await self._execute_platform_action(
                    target_platform, 
                    action_type, 
                    event.event_data,
                    action
                )
                
                execution_results.append({
                    'platform': target_platform,
                    'action': action_type,
                    'success': result.get('success', False),
                    'result': result
                })
            
            # Update rule execution stats
            rule.execution_count += 1
            successful_actions = len([r for r in execution_results if r['success']])
            rule.success_rate = (rule.success_rate * (rule.execution_count - 1) + 
                               (successful_actions / len(execution_results))) / rule.execution_count
            
            # Log execution
            execution_record = {
                'rule_id': rule.rule_id,
                'event_id': event.event_id,
                'timestamp': datetime.now(),
                'results': execution_results,
                'success_rate': successful_actions / len(execution_results)
            }
            
            self.execution_history.append(execution_record)
            
            logger.info(f"✅ Executed automation rule: {rule.name} with {successful_actions}/{len(execution_results)} successful actions")
            
        except Exception as e:
            logger.error(f"Error executing automation rule {rule.rule_id}: {e}")
    
    async def _execute_platform_action(self, platform_id: str, action_type: str, 
                                     event_data: Any, action_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute specific action on target platform"""
        try:
            # Get platform connection
            connection = self.connections.get(platform_id)
            if not connection:
                return {'success': False, 'error': f'Platform {platform_id} not connected'}
            
            # Execute platform-specific action
            if connection.platform_type == PlatformType.CRM:
                return await self._execute_crm_action(action_type, event_data, action_config)
            elif connection.platform_type == PlatformType.EMAIL:
                return await self._execute_email_action(action_type, event_data, action_config)
            elif connection.platform_type == PlatformType.ADS:
                return await self._execute_ads_action(action_type, event_data, action_config)
            elif connection.platform_type == PlatformType.COMMUNICATION:
                return await self._execute_communication_action(action_type, event_data, action_config)
            else:
                return await self._execute_generic_action(action_type, event_data, action_config)
                
        except Exception as e:
            logger.error(f"Error executing action {action_type} on {platform_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _execute_crm_action(self, action_type: str, data: Any, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute CRM-specific actions"""
        if action_type == "create_hot_lead":
            # Simulate creating hot lead in CRM
            return {
                'success': True,
                'action': 'create_hot_lead',
                'lead_id': f"hot_lead_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'message': 'Hot lead created in CRM'
            }
        elif action_type == "update_lead_score":
            return {
                'success': True,
                'action': 'update_lead_score',
                'message': 'Lead score updated'
            }
        else:
            return {'success': False, 'error': f'Unknown CRM action: {action_type}'}
    
    async def _execute_email_action(self, action_type: str, data: Any, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute email platform actions"""
        if action_type == "add_to_nurture_sequence":
            return {
                'success': True,
                'action': 'add_to_nurture_sequence',
                'sequence_id': f"nurture_{config.get('sequence_type', 'default')}",
                'message': 'Contact added to nurture sequence'
            }
        elif action_type == "trigger_personalized_campaign":
            return {
                'success': True,
                'action': 'trigger_personalized_campaign',
                'campaign_id': f"personalized_{datetime.now().strftime('%Y%m%d')}",
                'message': 'Personalized campaign triggered'
            }
        else:
            return {'success': False, 'error': f'Unknown email action: {action_type}'}
    
    async def _execute_ads_action(self, action_type: str, data: Any, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ads platform actions"""
        if action_type == "adjust_budget":
            return {
                'success': True,
                'action': 'adjust_budget',
                'adjustment': '+20%',
                'message': 'Campaign budget adjusted based on ML recommendations'
            }
        elif action_type == "pause_underperforming":
            return {
                'success': True,
                'action': 'pause_underperforming',
                'campaigns_paused': 2,
                'message': 'Underperforming campaigns paused'
            }
        else:
            return {'success': False, 'error': f'Unknown ads action: {action_type}'}
    
    async def _execute_communication_action(self, action_type: str, data: Any, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute communication platform actions (Slack, Teams, etc.)"""
        if action_type == "notify_sales_team":
            return {
                'success': True,
                'action': 'notify_sales_team',
                'channel': config.get('channel', '#general'),
                'message': 'Sales team notified about hot lead'
            }
        else:
            return {'success': False, 'error': f'Unknown communication action: {action_type}'}
    
    async def _execute_generic_action(self, action_type: str, data: Any, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute generic platform actions"""
        return {
            'success': True,
            'action': action_type,
            'message': f'Generic action {action_type} executed'
        }
    
    # Public API Methods
    
    async def get_platform_status(self) -> Dict[str, Any]:
        """Get status of all connected platforms"""
        return {
            'total_platforms': len(self.connections),
            'healthy_platforms': len([conn for conn in self.connections.values() if conn.is_healthy()]),
            'platform_types': list(set(conn.platform_type.value for conn in self.connections.values())),
            'active_rules': len([rule for rule in self.automation_rules.values() if rule.is_active]),
            'total_executions': sum(rule.execution_count for rule in self.automation_rules.values()),
            'avg_success_rate': sum(rule.success_rate for rule in self.automation_rules.values()) / len(self.automation_rules) if self.automation_rules else 0
        }
    
    async def get_ml_insights_summary(self) -> Dict[str, Any]:
        """Get summary of ML insights across all platforms"""
        return {
            'platforms_with_insights': len(self.ml_insights),
            'insights': {
                platform_id: {
                    'confidence': insights.get('confidence_score', 0),
                    'generated_at': insights.get('generated_at').isoformat() if insights.get('generated_at') else None,
                    'key_insights': list(insights.get('insights', {}).keys())
                }
                for platform_id, insights in self.ml_insights.items()
            }
        }
    
    async def get_automation_performance(self) -> Dict[str, Any]:
        """Get automation performance metrics"""
        recent_executions = [
            exec for exec in self.execution_history 
            if (datetime.now() - exec['timestamp']).days <= 7
        ]
        
        return {
            'total_rules': len(self.automation_rules),
            'active_rules': len([rule for rule in self.automation_rules.values() if rule.is_active]),
            'executions_last_7_days': len(recent_executions),
            'avg_success_rate': sum(exec['success_rate'] for exec in recent_executions) / len(recent_executions) if recent_executions else 0,
            'most_triggered_rules': [
                {
                    'rule_id': rule.rule_id,
                    'name': rule.name,
                    'execution_count': rule.execution_count,
                    'success_rate': rule.success_rate
                }
                for rule in sorted(self.automation_rules.values(), key=lambda x: x.execution_count, reverse=True)[:5]
            ]
        }
    
    async def create_custom_automation_rule(self, rule_data: Dict[str, Any]) -> str:
        """Create a custom automation rule"""
        rule = AutomationRule(
            rule_id=rule_data.get('rule_id', f"custom_{len(self.automation_rules) + 1}"),
            name=rule_data['name'],
            trigger_conditions=rule_data['trigger_conditions'],
            source_platforms=rule_data['source_platforms'],
            target_platforms=rule_data['target_platforms'],
            actions=rule_data['actions'],
            ml_scoring=rule_data.get('ml_scoring', False),
            confidence_threshold=rule_data.get('confidence_threshold', 0.7),
            is_active=rule_data.get('is_active', True)
        )
        
        self.automation_rules[rule.rule_id] = rule
        logger.info(f"✅ Created custom automation rule: {rule.name}")
        
        return rule.rule_id

# Global instance
interconnect_engine = PlatformInterconnectEngine()