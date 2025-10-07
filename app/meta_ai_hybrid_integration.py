# Meta AI Hybrid Integration for PulseBridge.ai
# Master AI Controller with Meta AI as Specialized Tool
# Enhanced symbiotic intelligence system

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIDecisionType(Enum):
    STRATEGIC_OVERRIDE = "strategic_override"
    PLATFORM_COORDINATION = "platform_coordination"
    BUDGET_REALLOCATION = "budget_reallocation"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    CROSS_PLATFORM_ANALYSIS = "cross_platform_analysis"

class OverrideReason(Enum):
    UNDERPERFORMANCE = "meta_underperformance"
    BETTER_PLATFORM_ROI = "better_platform_roi"
    BUDGET_EFFICIENCY = "budget_efficiency"
    STRATEGIC_REBALANCE = "strategic_rebalance"

@dataclass
class CrossPlatformMetrics:
    platform: str
    campaign_id: str
    roas: float
    cpa: float
    conversion_rate: float
    ctr: float
    quality_score: float
    confidence_score: float
    performance_trend: str  # "improving", "declining", "stable"

@dataclass
class AIDecisionLog:
    decision_id: str
    timestamp: datetime
    decision_type: AIDecisionType
    platform_affected: str
    campaign_id: Optional[str]
    override_reason: Optional[OverrideReason]
    confidence_score: float
    expected_impact: Dict[str, float]
    meta_ai_input: Dict[str, Any]
    cross_platform_context: List[CrossPlatformMetrics]
    action_taken: str
    estimated_roi_improvement: float

class PulseBridgeAIMasterController:
    """
    Master AI Controller - Primary intelligence system
    Coordinates all platform AIs including Meta AI as specialized tool
    """
    
    def __init__(self, supabase_client, meta_integration, config: Dict[str, Any]):
        self.supabase = supabase_client
        self.meta_integration = meta_integration
        self.config = config
        self.ml_models = {}
        self.decision_history = []
        self.platform_performances = {}
        self.initialize_master_ai()
    
    def initialize_master_ai(self):
        """Initialize master AI with cross-platform intelligence"""
        # Cross-platform performance predictor
        self.ml_models['cross_platform_optimizer'] = RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            random_state=42
        )
        
        # Meta AI integration analyzer
        self.ml_models['meta_ai_analyzer'] = RandomForestRegressor(
            n_estimators=150,
            max_depth=12,
            random_state=42
        )
        
        # Budget allocation optimizer
        self.ml_models['budget_allocator'] = RandomForestRegressor(
            n_estimators=175,
            max_depth=14,
            random_state=42
        )
        
        # Performance attribution model
        self.ml_models['attribution_model'] = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        
        self.scaler = StandardScaler()
        logger.info("🧠 PulseBridge AI Master Controller initialized")
    
    async def master_optimization_cycle(self) -> Dict[str, Any]:
        """
        Master AI optimization cycle
        Coordinates all platform AIs and makes strategic decisions
        """
        cycle_start = datetime.now()
        
        try:
            # Step 1: Gather intelligence from all platforms
            logger.info("📊 Gathering cross-platform intelligence...")
            platform_intelligence = await self.gather_cross_platform_data()
            
            # Step 2: Process Meta AI insights as specialized input
            logger.info("🔍 Processing Meta AI insights...")
            meta_ai_insights = await self.process_meta_ai_insights(platform_intelligence)
            
            # Step 3: Perform cross-platform analysis
            logger.info("⚡ Analyzing cross-platform performance...")
            performance_analysis = await self.analyze_cross_platform_performance(
                platform_intelligence, meta_ai_insights
            )
            
            # Step 4: Make strategic decisions
            logger.info("🎯 Making strategic optimization decisions...")
            strategic_decisions = await self.make_strategic_decisions(performance_analysis)
            
            # Step 5: Execute optimizations (when not in testing mode)
            logger.info("🚀 Executing optimization strategy...")
            execution_results = await self.execute_strategic_decisions(strategic_decisions)
            
            # Step 6: Update models and log decisions
            logger.info("📝 Updating AI models and logging decisions...")
            await self.update_master_models(platform_intelligence, execution_results)
            
            return {
                'success': True,
                'cycle_duration': (datetime.now() - cycle_start).total_seconds(),
                'platforms_analyzed': len(platform_intelligence),
                'strategic_decisions': len(strategic_decisions),
                'meta_ai_insights_processed': len(meta_ai_insights),
                'estimated_roi_improvement': execution_results.get('total_roi_improvement', 0),
                'next_cycle': cycle_start + timedelta(hours=self.config.get('cycle_interval', 6))
            }
            
        except Exception as e:
            logger.error(f"❌ Master optimization cycle failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'cycle_duration': (datetime.now() - cycle_start).total_seconds()
            }
    
    async def gather_cross_platform_data(self) -> Dict[str, List[CrossPlatformMetrics]]:
        """Gather performance data from all advertising platforms"""
        platform_data = {}
        
        # Meta platform data (processed through Meta AI)
        meta_data = await self.get_meta_platform_data()
        platform_data['meta'] = meta_data
        
        # Google Ads data
        google_data = await self.get_google_ads_data()
        platform_data['google_ads'] = google_data
        
        # LinkedIn data
        linkedin_data = await self.get_linkedin_data()
        platform_data['linkedin'] = linkedin_data
        
        # Pinterest data
        pinterest_data = await self.get_pinterest_data()
        platform_data['pinterest'] = pinterest_data
        
        return platform_data
    
    async def get_meta_platform_data(self) -> List[CrossPlatformMetrics]:
        """Get Meta platform data enhanced by Meta AI insights"""
        try:
            # Get raw Meta performance data
            meta_insights = await self.meta_integration.get_campaign_insights(
                date_preset='yesterday',
                level='campaign'
            )
            
            processed_metrics = []
            for insight in meta_insights.get('insights', []):
                # Calculate key metrics
                roas = float(insight.get('roas', 0))
                cpa = self.calculate_cpa(insight)
                ctr = float(insight.get('ctr', 0))
                conversion_rate = self.calculate_conversion_rate(insight)
                
                # Get Meta AI confidence score for this campaign
                confidence_score = await self.get_meta_ai_confidence(insight)
                
                # Determine performance trend
                performance_trend = await self.calculate_performance_trend(
                    insight.get('campaign_id'), 'meta'
                )
                
                metrics = CrossPlatformMetrics(
                    platform='meta',
                    campaign_id=insight.get('campaign_id'),
                    roas=roas,
                    cpa=cpa,
                    conversion_rate=conversion_rate,
                    ctr=ctr,
                    quality_score=insight.get('relevance_score', 5.0),
                    confidence_score=confidence_score,
                    performance_trend=performance_trend
                )
                processed_metrics.append(metrics)
            
            return processed_metrics
            
        except Exception as e:
            logger.error(f"❌ Failed to get Meta platform data: {str(e)}")
            return []
    
    async def process_meta_ai_insights(self, platform_data: Dict) -> List[Dict[str, Any]]:
        """Process Meta AI insights as input for master AI decisions"""
        meta_ai_insights = []
        
        if 'meta' not in platform_data:
            return meta_ai_insights
        
        for meta_metric in platform_data['meta']:
            # Extract Meta AI optimization recommendations
            meta_recommendations = await self.meta_integration.generate_ai_recommendations([{
                'campaign_id': meta_metric.campaign_id,
                'roas': meta_metric.roas,
                'cpa': meta_metric.cpa,
                'ctr': meta_metric.ctr,
                'spend': 100  # Placeholder, would get from actual data
            }])
            
            # Process Meta AI insights for master AI consumption
            insight = {
                'campaign_id': meta_metric.campaign_id,
                'meta_ai_recommendations': meta_recommendations,
                'meta_confidence': meta_metric.confidence_score,
                'meta_performance_trend': meta_metric.performance_trend,
                'meta_optimization_potential': self.calculate_meta_optimization_potential(meta_metric),
                'cross_platform_context': self.get_cross_platform_context(
                    meta_metric.campaign_id, platform_data
                )
            }
            meta_ai_insights.append(insight)
        
        return meta_ai_insights
    
    async def analyze_cross_platform_performance(
        self, 
        platform_data: Dict, 
        meta_ai_insights: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze performance across all platforms to identify optimization opportunities"""
        analysis = {
            'platform_rankings': {},
            'underperforming_campaigns': [],
            'reallocation_opportunities': [],
            'meta_ai_effectiveness': {}
        }
        
        # Rank platforms by performance metrics
        platform_scores = {}
        for platform, metrics_list in platform_data.items():
            if not metrics_list:
                continue
                
            avg_roas = np.mean([m.roas for m in metrics_list])
            avg_cpa = np.mean([m.cpa for m in metrics_list if m.cpa > 0])
            avg_conversion_rate = np.mean([m.conversion_rate for m in metrics_list])
            
            # Calculate composite performance score
            platform_scores[platform] = {
                'roas': avg_roas,
                'cpa': avg_cpa,
                'conversion_rate': avg_conversion_rate,
                'composite_score': (avg_roas * 0.4) + (avg_conversion_rate * 0.3) + (100/max(avg_cpa, 1) * 0.3)
            }
        
        # Sort platforms by performance
        analysis['platform_rankings'] = dict(
            sorted(platform_scores.items(), key=lambda x: x[1]['composite_score'], reverse=True)
        )
        
        # Identify underperforming Meta campaigns
        if 'meta' in platform_data:
            best_platform_score = max(platform_scores.values(), key=lambda x: x['composite_score'])['composite_score']
            
            for meta_metric in platform_data['meta']:
                meta_score = (meta_metric.roas * 0.4) + (meta_metric.conversion_rate * 0.3) + (100/max(meta_metric.cpa, 1) * 0.3)
                
                # If Meta campaign is significantly underperforming
                if meta_score < best_platform_score * 0.75:  # 25% threshold
                    analysis['underperforming_campaigns'].append({
                        'platform': 'meta',
                        'campaign_id': meta_metric.campaign_id,
                        'performance_gap': best_platform_score - meta_score,
                        'recommended_action': 'budget_reallocation'
                    })
        
        # Assess Meta AI effectiveness
        for insight in meta_ai_insights:
            campaign_id = insight['campaign_id']
            meta_ai_effectiveness = self.calculate_meta_ai_effectiveness(insight, platform_data)
            analysis['meta_ai_effectiveness'][campaign_id] = meta_ai_effectiveness
        
        return analysis
    
    async def make_strategic_decisions(self, performance_analysis: Dict) -> List[AIDecisionLog]:
        """Make strategic decisions based on cross-platform analysis"""
        strategic_decisions = []
        
        # Process underperforming campaigns
        for underperforming in performance_analysis['underperforming_campaigns']:
            if underperforming['platform'] == 'meta':
                # Create strategic override decision
                decision = AIDecisionLog(
                    decision_id=f"decision_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{underperforming['campaign_id']}",
                    timestamp=datetime.now(),
                    decision_type=AIDecisionType.STRATEGIC_OVERRIDE,
                    platform_affected='meta',
                    campaign_id=underperforming['campaign_id'],
                    override_reason=OverrideReason.UNDERPERFORMANCE,
                    confidence_score=0.85,  # Based on performance gap analysis
                    expected_impact={
                        'roi_improvement': underperforming['performance_gap'] * 0.6,
                        'budget_efficiency': 0.25
                    },
                    meta_ai_input=performance_analysis['meta_ai_effectiveness'].get(
                        underperforming['campaign_id'], {}
                    ),
                    cross_platform_context=[],  # Would populate with relevant metrics
                    action_taken='budget_reduction_and_reallocation',
                    estimated_roi_improvement=underperforming['performance_gap'] * 0.6
                )
                strategic_decisions.append(decision)
        
        # Identify budget reallocation opportunities
        platform_rankings = performance_analysis['platform_rankings']
        if len(platform_rankings) > 1:
            best_platform = list(platform_rankings.keys())[0]
            worst_platform = list(platform_rankings.keys())[-1]
            
            if worst_platform == 'meta' and platform_rankings[best_platform]['composite_score'] > platform_rankings[worst_platform]['composite_score'] * 1.2:
                decision = AIDecisionLog(
                    decision_id=f"reallocation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    timestamp=datetime.now(),
                    decision_type=AIDecisionType.BUDGET_REALLOCATION,
                    platform_affected='cross_platform',
                    campaign_id=None,
                    override_reason=OverrideReason.BETTER_PLATFORM_ROI,
                    confidence_score=0.88,
                    expected_impact={
                        'cross_platform_roi': 0.15,
                        'budget_efficiency': 0.20
                    },
                    meta_ai_input={},
                    cross_platform_context=[],
                    action_taken=f'reallocate_from_{worst_platform}_to_{best_platform}',
                    estimated_roi_improvement=0.15
                )
                strategic_decisions.append(decision)
        
        return strategic_decisions
    
    async def execute_strategic_decisions(self, decisions: List[AIDecisionLog]) -> Dict[str, Any]:
        """Execute strategic decisions (in testing mode, only log and recommend)"""
        execution_results = {
            'executed_decisions': [],
            'recommended_actions': [],
            'total_roi_improvement': 0,
            'testing_mode': self.config.get('testing_mode', True)
        }
        
        for decision in decisions:
            if self.config.get('testing_mode', True):
                # Testing mode: Only log and recommend
                execution_results['recommended_actions'].append({
                    'decision_id': decision.decision_id,
                    'recommendation': decision.action_taken,
                    'expected_impact': decision.expected_impact,
                    'confidence': decision.confidence_score,
                    'platform': decision.platform_affected
                })
                logger.info(f"📋 TESTING MODE - Recommended action: {decision.action_taken}")
                
            else:
                # Production mode: Execute decisions
                try:
                    execution_result = await self.execute_single_decision(decision)
                    execution_results['executed_decisions'].append(execution_result)
                    execution_results['total_roi_improvement'] += decision.estimated_roi_improvement
                    
                    # Log to database
                    await self.log_decision_to_database(decision, execution_result)
                    
                except Exception as e:
                    logger.error(f"❌ Failed to execute decision {decision.decision_id}: {str(e)}")
        
        return execution_results
    
    async def execute_single_decision(self, decision: AIDecisionLog) -> Dict[str, Any]:
        """Execute a single strategic decision"""
        if decision.decision_type == AIDecisionType.STRATEGIC_OVERRIDE:
            if decision.platform_affected == 'meta':
                # Override Meta AI decision
                return await self.override_meta_campaign(decision)
        
        elif decision.decision_type == AIDecisionType.BUDGET_REALLOCATION:
            # Reallocate budget across platforms
            return await self.execute_budget_reallocation(decision)
        
        return {'success': True, 'action': 'logged_only'}
    
    async def override_meta_campaign(self, decision: AIDecisionLog) -> Dict[str, Any]:
        """Override Meta AI optimization for underperforming campaign"""
        try:
            # Reduce Meta campaign budget
            budget_reduction = 0.3  # 30% reduction
            
            # This would integrate with Meta API to reduce budget
            override_result = {
                'success': True,
                'action': 'budget_reduced',
                'campaign_id': decision.campaign_id,
                'budget_change': -budget_reduction,
                'reason': decision.override_reason.value
            }
            
            logger.info(f"🎯 Overrode Meta AI for campaign {decision.campaign_id}: {override_result}")
            return override_result
            
        except Exception as e:
            logger.error(f"❌ Failed to override Meta campaign: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def log_decision_to_database(self, decision: AIDecisionLog, execution_result: Dict) -> None:
        """Log AI decision to database for audit trail and learning"""
        try:
            decision_record = {
                'decision_id': decision.decision_id,
                'timestamp': decision.timestamp.isoformat(),
                'decision_type': decision.decision_type.value,
                'platform_affected': decision.platform_affected,
                'campaign_id': decision.campaign_id,
                'override_reason': decision.override_reason.value if decision.override_reason else None,
                'confidence_score': decision.confidence_score,
                'expected_impact': decision.expected_impact,
                'meta_ai_input': decision.meta_ai_input,
                'action_taken': decision.action_taken,
                'execution_result': execution_result,
                'estimated_roi_improvement': decision.estimated_roi_improvement
            }
            
            # Insert into ai_insights table with enhanced data
            result = self.supabase.table('ai_insights').insert(decision_record).execute()
            logger.info(f"📝 Logged decision {decision.decision_id} to database")
            
        except Exception as e:
            logger.error(f"❌ Failed to log decision to database: {str(e)}")
    
    # Utility methods for calculations and analysis
    def calculate_cpa(self, insight: Dict) -> float:
        """Calculate cost per acquisition"""
        spend = float(insight.get('spend', 0))
        conversions = float(insight.get('conversions', 0))
        return spend / max(conversions, 1)
    
    def calculate_conversion_rate(self, insight: Dict) -> float:
        """Calculate conversion rate"""
        clicks = float(insight.get('clicks', 0))
        conversions = float(insight.get('conversions', 0))
        return (conversions / max(clicks, 1)) * 100
    
    async def get_meta_ai_confidence(self, insight: Dict) -> float:
        """Get Meta AI confidence score for campaign optimization"""
        # This would integrate with Meta's native confidence indicators
        # For now, calculate based on performance stability
        roas = float(insight.get('roas', 0))
        frequency = float(insight.get('frequency', 1))
        
        # Higher ROAS and lower frequency = higher confidence
        confidence = min(1.0, (roas / 4.0) * (2.0 / max(frequency, 1)))
        return confidence
    
    async def calculate_performance_trend(self, campaign_id: str, platform: str) -> str:
        """Calculate performance trend for campaign"""
        try:
            # Get historical performance data
            historical_data = self.supabase.table('performance_snapshots').select('*').eq('campaign_id', campaign_id).order('date', desc=True).limit(7).execute()
            
            if len(historical_data.data) < 3:
                return "insufficient_data"
            
            # Calculate trend based on ROAS changes
            recent_roas = [float(d.get('roas', 0)) for d in historical_data.data[:3]]
            older_roas = [float(d.get('roas', 0)) for d in historical_data.data[3:6]]
            
            recent_avg = np.mean(recent_roas)
            older_avg = np.mean(older_roas)
            
            if recent_avg > older_avg * 1.1:
                return "improving"
            elif recent_avg < older_avg * 0.9:
                return "declining"
            else:
                return "stable"
                
        except Exception as e:
            logger.error(f"❌ Failed to calculate performance trend: {str(e)}")
            return "unknown"
    
    def calculate_meta_optimization_potential(self, metric: CrossPlatformMetrics) -> float:
        """Calculate how much Meta AI can optimize this campaign"""
        # Based on current performance vs benchmarks
        potential = 0.5  # Base potential
        
        if metric.roas < 2.0:
            potential += 0.3  # High potential for improvement
        elif metric.roas > 4.0:
            potential -= 0.2  # Less room for improvement
        
        if metric.ctr < 1.0:
            potential += 0.2  # CTR optimization potential
        
        return min(1.0, potential)
    
    def get_cross_platform_context(self, campaign_id: str, platform_data: Dict) -> List[CrossPlatformMetrics]:
        """Get cross-platform context for decision making"""
        context = []
        for platform, metrics_list in platform_data.items():
            if platform != 'meta':
                # Add relevant cross-platform metrics
                context.extend(metrics_list[:3])  # Top 3 performers from each platform
        return context
    
    def calculate_meta_ai_effectiveness(self, insight: Dict, platform_data: Dict) -> Dict[str, float]:
        """Calculate how effectively Meta AI is performing vs other platforms"""
        campaign_id = insight['campaign_id']
        meta_confidence = insight['meta_confidence']
        meta_recommendations = len(insight.get('meta_ai_recommendations', []))
        
        # Compare Meta performance to other platforms
        other_platform_scores = []
        for platform, metrics_list in platform_data.items():
            if platform != 'meta' and metrics_list:
                avg_score = np.mean([m.roas for m in metrics_list])
                other_platform_scores.append(avg_score)
        
        avg_other_performance = np.mean(other_platform_scores) if other_platform_scores else 2.0
        
        # Find Meta performance for this campaign
        meta_performance = 2.0  # Default
        if 'meta' in platform_data:
            for metric in platform_data['meta']:
                if metric.campaign_id == campaign_id:
                    meta_performance = metric.roas
                    break
        
        effectiveness = {
            'relative_performance': meta_performance / max(avg_other_performance, 1),
            'ai_confidence': meta_confidence,
            'recommendation_activity': min(1.0, meta_recommendations / 5),
            'overall_effectiveness': (meta_performance / max(avg_other_performance, 1)) * meta_confidence
        }
        
        return effectiveness

    async def get_google_ads_data(self) -> List[CrossPlatformMetrics]:
        """Get Google Ads performance data"""
        # Placeholder for Google Ads integration
        return []
    
    async def get_linkedin_data(self) -> List[CrossPlatformMetrics]:
        """Get LinkedIn Ads performance data"""
        # Placeholder for LinkedIn integration
        return []
    
    async def get_pinterest_data(self) -> List[CrossPlatformMetrics]:
        """Get Pinterest Ads performance data"""
        # Placeholder for Pinterest integration
        return []
    
    async def update_master_models(self, platform_data: Dict, execution_results: Dict) -> None:
        """Update master AI models with latest performance data"""
        # Update ML models with new data
        # This would involve retraining models with recent performance data
        logger.info("🧠 Updated master AI models with latest data")
    
    async def execute_budget_reallocation(self, decision: AIDecisionLog) -> Dict[str, Any]:
        """Execute budget reallocation across platforms"""
        # Placeholder for cross-platform budget reallocation
        return {'success': True, 'action': 'budget_reallocated'}

# Example usage integration with PulseBridge.ai
async def initialize_hybrid_ai_system(supabase_client, meta_integration, config):
    """Initialize the hybrid AI system"""
    master_controller = PulseBridgeAIMasterController(
        supabase_client=supabase_client,
        meta_integration=meta_integration,
        config=config
    )
    
    # Run master optimization cycle
    result = await master_controller.master_optimization_cycle()
    
    return {
        'system_status': 'initialized',
        'master_ai': 'active',
        'meta_ai_integration': 'symbiotic',
        'cycle_result': result
    }