# PulseBridge AI - Smart Risk Management & Configuration System
# Advanced risk assessment with customizable testing modes
# Client-facing intelligence with Meta AI invisible integration

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum
import json

class RiskLevel(Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced" 
    AGGRESSIVE = "aggressive"
    CUSTOM = "custom"

class ClientVisibilityMode(Enum):
    FULL_TRANSPARENCY = "full_transparency"  # Show all AI decisions
    SUMMARY_ONLY = "summary_only"  # Show results, not process
    PULSEBRIDGE_BRANDED = "pulsebridge_branded"  # Only show PulseBridge AI
    INVISIBLE = "invisible"  # Background optimization only

@dataclass
class RiskManagementConfig:
    """Smart risk management configuration"""
    risk_level: RiskLevel
    max_budget_change_percent: float
    max_daily_budget: float
    min_confidence_threshold: float
    max_concurrent_changes: int
    cooling_off_period_hours: int
    require_human_approval_over: float
    emergency_stop_conditions: Dict[str, float]
    platform_specific_limits: Dict[str, Dict[str, float]]

@dataclass 
class ClientReportingConfig:
    """Client-facing reporting and branding configuration"""
    visibility_mode: ClientVisibilityMode
    brand_as_pulsebridge_only: bool
    show_confidence_scores: bool
    include_meta_ai_insights: bool
    notification_frequency: str  # "real_time", "daily", "weekly"
    custom_dashboard_elements: List[str]
    performance_attribution: str  # "pulsebridge", "platform_native", "hybrid"

class SmartRiskManager:
    """
    Advanced risk management system with intelligent safeguards
    Ensures safe testing while maximizing optimization potential
    """
    
    def __init__(self, base_config: RiskManagementConfig):
        self.base_config = base_config
        self.dynamic_adjustments = {}
        self.performance_history = []
        self.risk_score_history = []
    
    def assess_decision_risk(
        self, 
        decision_data: Dict[str, Any],
        current_performance: Dict[str, Any],
        market_conditions: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Intelligent risk assessment for AI decisions
        Returns comprehensive risk analysis with recommendations
        """
        risk_analysis = {
            'overall_risk_score': 0.0,
            'risk_factors': {},
            'safeguards_triggered': [],
            'recommendation': 'proceed',
            'confidence_adjustment': 0.0,
            'monitoring_requirements': []
        }
        
        # Budget Change Risk Assessment
        budget_risk = self._assess_budget_change_risk(decision_data)
        risk_analysis['risk_factors']['budget_change'] = budget_risk
        risk_analysis['overall_risk_score'] += budget_risk['score'] * 0.3
        
        # Performance Impact Risk
        performance_risk = self._assess_performance_impact_risk(decision_data, current_performance)
        risk_analysis['risk_factors']['performance_impact'] = performance_risk
        risk_analysis['overall_risk_score'] += performance_risk['score'] * 0.25
        
        # Platform Coordination Risk
        coordination_risk = self._assess_platform_coordination_risk(decision_data)
        risk_analysis['risk_factors']['coordination'] = coordination_risk
        risk_analysis['overall_risk_score'] += coordination_risk['score'] * 0.2
        
        # Market Timing Risk
        timing_risk = self._assess_timing_risk(decision_data, market_conditions)
        risk_analysis['risk_factors']['timing'] = timing_risk
        risk_analysis['overall_risk_score'] += timing_risk['score'] * 0.15
        
        # Client Impact Risk
        client_risk = self._assess_client_impact_risk(decision_data)
        risk_analysis['risk_factors']['client_impact'] = client_risk
        risk_analysis['overall_risk_score'] += client_risk['score'] * 0.1
        
        # Apply risk-based recommendations
        risk_analysis = self._generate_risk_recommendations(risk_analysis, decision_data)
        
        return risk_analysis
    
    def _assess_budget_change_risk(self, decision_data: Dict) -> Dict[str, Any]:
        """Assess risk related to budget changes"""
        budget_change_percent = abs(decision_data.get('budget_change_percent', 0))
        current_spend = decision_data.get('current_daily_spend', 0)
        
        risk_score = 0.0
        risk_factors = []
        
        # Percentage change risk
        if budget_change_percent > self.base_config.max_budget_change_percent:
            risk_score += 0.4
            risk_factors.append(f"Budget change {budget_change_percent:.1%} exceeds limit {self.base_config.max_budget_change_percent:.1%}")
        
        # Absolute amount risk
        new_daily_spend = current_spend * (1 + budget_change_percent/100)
        if new_daily_spend > self.base_config.max_daily_budget:
            risk_score += 0.3
            risk_factors.append(f"New daily spend ${new_daily_spend:.2f} exceeds limit ${self.base_config.max_daily_budget:.2f}")
        
        # Frequency risk (rapid successive changes)
        recent_changes = len([h for h in self.performance_history if h.get('budget_changed', False)])
        if recent_changes > 2:
            risk_score += 0.2
            risk_factors.append(f"Too many recent budget changes ({recent_changes})")
        
        return {
            'score': min(1.0, risk_score),
            'factors': risk_factors,
            'severity': 'high' if risk_score > 0.7 else 'medium' if risk_score > 0.3 else 'low'
        }
    
    def _assess_performance_impact_risk(self, decision_data: Dict, current_performance: Dict) -> Dict[str, Any]:
        """Assess risk of performance degradation"""
        risk_score = 0.0
        risk_factors = []
        
        current_roas = current_performance.get('roas', 2.0)
        current_conversion_rate = current_performance.get('conversion_rate', 2.0)
        
        # Low current performance increases risk of optimization attempts
        if current_roas < 1.5:
            risk_score += 0.3
            risk_factors.append(f"Current ROAS {current_roas:.2f} below safe threshold")
        
        if current_conversion_rate < 1.0:
            risk_score += 0.2
            risk_factors.append(f"Low conversion rate {current_conversion_rate:.2f}% increases optimization risk")
        
        # Confidence vs performance mismatch
        decision_confidence = decision_data.get('confidence_score', 0.5)
        if decision_confidence < 0.8 and current_roas > 3.0:
            risk_score += 0.4
            risk_factors.append("Low confidence decision on well-performing campaign")
        
        return {
            'score': min(1.0, risk_score),
            'factors': risk_factors,
            'severity': 'high' if risk_score > 0.7 else 'medium' if risk_score > 0.3 else 'low'
        }
    
    def _assess_platform_coordination_risk(self, decision_data: Dict) -> Dict[str, Any]:
        """Assess risk of platform AI conflicts"""
        risk_score = 0.0
        risk_factors = []
        
        # Meta AI override risk
        if decision_data.get('overrides_meta_ai', False):
            meta_confidence = decision_data.get('meta_ai_confidence', 0.5)
            our_confidence = decision_data.get('confidence_score', 0.5)
            
            if meta_confidence > our_confidence:
                risk_score += 0.3
                risk_factors.append(f"Overriding Meta AI with lower confidence (ours: {our_confidence:.2f}, Meta: {meta_confidence:.2f})")
        
        # Cross-platform coordination complexity
        platforms_affected = len(decision_data.get('platforms_affected', []))
        if platforms_affected > 2:
            risk_score += 0.2
            risk_factors.append(f"Complex multi-platform coordination ({platforms_affected} platforms)")
        
        return {
            'score': min(1.0, risk_score),
            'factors': risk_factors,
            'severity': 'high' if risk_score > 0.7 else 'medium' if risk_score > 0.3 else 'low'
        }
    
    def _assess_timing_risk(self, decision_data: Dict, market_conditions: Dict = None) -> Dict[str, Any]:
        """Assess market timing and external factor risks"""
        risk_score = 0.0
        risk_factors = []
        
        # Weekend/holiday risk
        import datetime
        now = datetime.datetime.now()
        if now.weekday() >= 5:  # Weekend
            risk_score += 0.1
            risk_factors.append("Weekend execution increases risk")
        
        # Recent major changes risk
        hours_since_last_change = decision_data.get('hours_since_last_change', 24)
        if hours_since_last_change < self.base_config.cooling_off_period_hours:
            risk_score += 0.2
            risk_factors.append(f"Recent change {hours_since_last_change}h ago, cooling period not met")
        
        # Market conditions risk (if provided)
        if market_conditions:
            volatility = market_conditions.get('volatility', 0.0)
            if volatility > 0.3:
                risk_score += 0.3
                risk_factors.append(f"High market volatility {volatility:.1%}")
        
        return {
            'score': min(1.0, risk_score),
            'factors': risk_factors,
            'severity': 'high' if risk_score > 0.7 else 'medium' if risk_score > 0.3 else 'low'
        }
    
    def _assess_client_impact_risk(self, decision_data: Dict) -> Dict[str, Any]:
        """Assess potential client relationship impact"""
        risk_score = 0.0
        risk_factors = []
        
        # High-value client risk
        client_tier = decision_data.get('client_tier', 'standard')
        if client_tier == 'premium':
            risk_score += 0.1
            risk_factors.append("Premium client requires extra caution")
        
        # Large campaign risk
        campaign_value = decision_data.get('monthly_budget', 0)
        if campaign_value > 10000:
            risk_score += 0.2
            risk_factors.append(f"High-value campaign ${campaign_value:,.2f}/month")
        
        return {
            'score': min(1.0, risk_score),
            'factors': risk_factors,
            'severity': 'high' if risk_score > 0.7 else 'medium' if risk_score > 0.3 else 'low'
        }
    
    def _generate_risk_recommendations(self, risk_analysis: Dict, decision_data: Dict) -> Dict[str, Any]:
        """Generate intelligent risk-based recommendations"""
        overall_risk = risk_analysis['overall_risk_score']
        
        # Risk-based decision logic
        if overall_risk > 0.8:
            risk_analysis['recommendation'] = 'block'
            risk_analysis['safeguards_triggered'].append('HIGH_RISK_BLOCK')
            risk_analysis['monitoring_requirements'].extend([
                'immediate_human_review',
                'extended_monitoring_period',
                'performance_alerts'
            ])
        
        elif overall_risk > 0.6:
            risk_analysis['recommendation'] = 'require_approval'
            risk_analysis['safeguards_triggered'].append('APPROVAL_REQUIRED')
            risk_analysis['confidence_adjustment'] = -0.1
            risk_analysis['monitoring_requirements'].extend([
                'human_approval_required',
                'enhanced_monitoring',
                'rollback_plan_ready'
            ])
        
        elif overall_risk > 0.4:
            risk_analysis['recommendation'] = 'proceed_with_caution'
            risk_analysis['safeguards_triggered'].append('ENHANCED_MONITORING')
            risk_analysis['confidence_adjustment'] = -0.05
            risk_analysis['monitoring_requirements'].extend([
                'increased_monitoring_frequency',
                'performance_thresholds_tightened'
            ])
        
        else:
            risk_analysis['recommendation'] = 'proceed'
            risk_analysis['monitoring_requirements'].append('standard_monitoring')
        
        return risk_analysis

class ClientReportingManager:
    """
    Manages client-facing reporting and branding
    Ensures PulseBridge AI appears as primary intelligence system
    """
    
    def __init__(self, reporting_config: ClientReportingConfig):
        self.config = reporting_config
    
    def format_ai_decision_for_client(
        self, 
        decision_data: Dict[str, Any],
        meta_ai_contributions: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Format AI decision data for client consumption
        Always shows PulseBridge AI as primary decision maker
        """
        client_report = {
            'ai_system': 'PulseBridge AI',
            'decision_timestamp': decision_data.get('timestamp'),
            'optimization_type': decision_data.get('decision_type'),
            'platforms_optimized': decision_data.get('platforms_affected', []),
            'confidence_level': 'High' if decision_data.get('confidence_score', 0) > 0.8 else 'Medium',
            'expected_improvement': decision_data.get('expected_impact', {}),
            'action_taken': self._translate_action_for_client(decision_data.get('action_taken', '')),
            'reasoning': self._generate_client_friendly_reasoning(decision_data, meta_ai_contributions)
        }
        
        # Conditional information based on visibility settings
        if self.config.show_confidence_scores:
            client_report['confidence_score'] = decision_data.get('confidence_score', 0)
        
        if self.config.include_meta_ai_insights and meta_ai_contributions:
            client_report['platform_insights'] = self._format_meta_insights_for_client(meta_ai_contributions)
        
        # Performance attribution
        if self.config.performance_attribution == 'pulsebridge':
            client_report['attribution'] = 'Optimized by PulseBridge AI advanced algorithms'
        elif self.config.performance_attribution == 'hybrid':
            client_report['attribution'] = 'PulseBridge AI with platform-native optimization integration'
        
        return client_report
    
    def _translate_action_for_client(self, technical_action: str) -> str:
        """Translate technical actions to client-friendly language"""
        translations = {
            'budget_reduction_and_reallocation': 'Budget optimized across platforms for better ROI',
            'strategic_override': 'AI detected optimization opportunity and adjusted strategy',
            'cross_platform_rebalance': 'Balanced investment across platforms for maximum impact',
            'meta_campaign_pause': 'Paused underperforming Facebook/Instagram ads',
            'audience_optimization': 'Refined target audience for better engagement',
            'creative_refresh': 'Recommended new ad creative based on performance data'
        }
        return translations.get(technical_action, 'AI optimization applied')
    
    def _generate_client_friendly_reasoning(
        self, 
        decision_data: Dict, 
        meta_ai_contributions: Dict = None
    ) -> str:
        """Generate client-friendly explanation of AI reasoning"""
        base_reasoning = "PulseBridge AI analyzed cross-platform performance data"
        
        # Add specific reasoning based on decision type
        decision_type = decision_data.get('decision_type', '')
        confidence = decision_data.get('confidence_score', 0)
        
        if 'override' in decision_type:
            reasoning = f"{base_reasoning} and identified a {confidence*100:.0f}% confident optimization opportunity. "
            reasoning += "By reallocating budget to higher-performing platforms, we expect improved ROI."
        
        elif 'reallocation' in decision_type:
            reasoning = f"{base_reasoning} and found better conversion opportunities on alternative platforms. "
            reasoning += "Smart budget reallocation will maximize your advertising investment."
        
        else:
            reasoning = f"{base_reasoning} and recommended strategic adjustments "
            reasoning += f"with {confidence*100:.0f}% confidence to improve campaign performance."
        
        return reasoning
    
    def _format_meta_insights_for_client(self, meta_ai_contributions: Dict) -> Dict[str, Any]:
        """Format Meta AI insights for client visibility (when enabled)"""
        if not self.config.include_meta_ai_insights:
            return {}
        
        return {
            'facebook_instagram_insights': 'Advanced audience analysis completed',
            'platform_optimization': 'Native Facebook optimization algorithms consulted',
            'integration_effectiveness': 'PulseBridge AI successfully coordinated with platform tools'
        }

# Configuration templates for different client types
RISK_MANAGEMENT_TEMPLATES = {
    'beta_testing_conservative': RiskManagementConfig(
        risk_level=RiskLevel.CONSERVATIVE,
        max_budget_change_percent=10.0,
        max_daily_budget=500.0,
        min_confidence_threshold=0.95,
        max_concurrent_changes=2,
        cooling_off_period_hours=24,
        require_human_approval_over=100.0,
        emergency_stop_conditions={
            'roas_drop_threshold': 0.3,
            'spend_spike_threshold': 2.0,
            'conversion_drop_threshold': 0.5
        },
        platform_specific_limits={
            'meta': {'max_budget_change': 0.1, 'min_confidence': 0.9},
            'google_ads': {'max_budget_change': 0.15, 'min_confidence': 0.85},
            'linkedin': {'max_budget_change': 0.2, 'min_confidence': 0.8}
        }
    ),
    
    'production_balanced': RiskManagementConfig(
        risk_level=RiskLevel.BALANCED,
        max_budget_change_percent=25.0,
        max_daily_budget=2000.0,
        min_confidence_threshold=0.85,
        max_concurrent_changes=5,
        cooling_off_period_hours=12,
        require_human_approval_over=500.0,
        emergency_stop_conditions={
            'roas_drop_threshold': 0.4,
            'spend_spike_threshold': 2.5,
            'conversion_drop_threshold': 0.4
        },
        platform_specific_limits={
            'meta': {'max_budget_change': 0.25, 'min_confidence': 0.8},
            'google_ads': {'max_budget_change': 0.3, 'min_confidence': 0.85},
            'linkedin': {'max_budget_change': 0.3, 'min_confidence': 0.75}
        }
    )
}

CLIENT_REPORTING_TEMPLATES = {
    'agency_transparent': ClientReportingConfig(
        visibility_mode=ClientVisibilityMode.PULSEBRIDGE_BRANDED,
        brand_as_pulsebridge_only=True,
        show_confidence_scores=True,
        include_meta_ai_insights=False,  # Hide Meta AI, show as PulseBridge capability
        notification_frequency='daily',
        custom_dashboard_elements=['roi_trends', 'optimization_history', 'ai_recommendations'],
        performance_attribution='pulsebridge'
    ),
    
    'client_summary': ClientReportingConfig(
        visibility_mode=ClientVisibilityMode.SUMMARY_ONLY,
        brand_as_pulsebridge_only=True,
        show_confidence_scores=False,
        include_meta_ai_insights=False,
        notification_frequency='weekly',
        custom_dashboard_elements=['performance_summary', 'roi_improvement'],
        performance_attribution='pulsebridge'
    )
}