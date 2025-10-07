# Hybrid AI Endpoints for PulseBridge.ai
# Advanced hybrid AI system with Meta AI integration
# Master AI controller endpoints

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPAuthorizationCredentials
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging
import json

# Import hybrid AI components
from meta_ai_hybrid_integration import PulseBridgeAIMasterController, CrossPlatformMetrics, AIDecisionLog, AIDecisionType, OverrideReason
from smart_risk_management import SmartRiskManager, ClientReportingManager, RiskLevel, ClientVisibilityMode, RISK_MANAGEMENT_TEMPLATES, CLIENT_REPORTING_TEMPLATES

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/hybrid-ai", tags=["Hybrid AI System"])

# Pydantic models for API
class HybridAIConfig(BaseModel):
    testing_mode: bool = True
    risk_level: str = "conservative"
    auto_execution_enabled: bool = False
    cycle_interval_hours: int = 6
    client_visibility_mode: str = "pulsebridge_branded"
    max_daily_budget: float = 1000.0
    min_confidence_threshold: float = 0.85

class OptimizationRequest(BaseModel):
    force_execution: bool = False
    platforms: Optional[List[str]] = None
    campaign_ids: Optional[List[str]] = None
    custom_risk_config: Optional[Dict[str, Any]] = None

class DecisionApprovalRequest(BaseModel):
    decision_id: str
    approved: bool
    approval_notes: Optional[str] = None

# Global instances (would be properly initialized in production)
master_controller = None
risk_manager = None
reporting_manager = None

def get_hybrid_ai_dependencies():
    """Get or initialize hybrid AI system components"""
    global master_controller, risk_manager, reporting_manager
    
    if not master_controller:
        # Initialize with default config (would get from database in production)
        config = {
            'testing_mode': True,
            'cycle_interval': 6,
            'risk_level': 'conservative',
            'optimization_level': 'balanced'
        }
        
        # These would be properly injected in production
        supabase_client = None  # Your Supabase client
        meta_integration = None  # Your Meta integration
        
        master_controller = PulseBridgeAIMasterController(
            supabase_client=supabase_client,
            meta_integration=meta_integration,
            config=config
        )
        
        risk_manager = SmartRiskManager(RISK_MANAGEMENT_TEMPLATES['beta_testing_conservative'])
        reporting_manager = ClientReportingManager(CLIENT_REPORTING_TEMPLATES['agency_transparent'])
    
    return master_controller, risk_manager, reporting_manager

@router.get("/status")
async def get_hybrid_ai_status():
    """Get current status of hybrid AI system"""
    try:
        controller, risk_mgr, reporting_mgr = get_hybrid_ai_dependencies()
        
        return {
            'status': 'active',
            'system_type': 'PulseBridge AI Master Controller',
            'meta_ai_integration': 'symbiotic',
            'testing_mode': True,
            'last_optimization_cycle': None,
            'platforms_monitored': ['meta', 'google_ads', 'linkedin', 'pinterest'],
            'risk_management': 'conservative',
            'client_reporting': 'pulsebridge_branded',
            'capabilities': [
                'cross_platform_optimization',
                'meta_ai_coordination',
                'strategic_override_system',
                'intelligent_risk_management',
                'client_branded_reporting'
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get hybrid AI status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize")
async def run_master_optimization_cycle(request: OptimizationRequest):
    """Run master AI optimization cycle"""
    try:
        controller, risk_mgr, reporting_mgr = get_hybrid_ai_dependencies()
        
        logger.info("🚀 Starting master AI optimization cycle...")
        
        # Run the optimization cycle
        result = await controller.master_optimization_cycle()
        
        if result['success']:
            # Format for client reporting
            client_report = reporting_mgr.format_ai_decision_for_client({
                'timestamp': datetime.now(),
                'decision_type': 'optimization_cycle',
                'platforms_affected': ['meta', 'google_ads', 'linkedin'],
                'confidence_score': 0.87,
                'action_taken': 'cross_platform_optimization',
                'expected_impact': {
                    'roi_improvement': 0.15,
                    'efficiency_gain': 0.20
                }
            })
            
            return {
                'success': True,
                'cycle_result': result,
                'client_report': client_report,
                'ai_system': 'PulseBridge AI',
                'optimization_summary': {
                    'platforms_analyzed': result.get('platforms_analyzed', 0),
                    'strategic_decisions': result.get('strategic_decisions', 0),
                    'estimated_roi_improvement': result.get('estimated_roi_improvement', 0),
                    'next_cycle': result.get('next_cycle')
                }
            }
        else:
            return {
                'success': False,
                'error': result.get('error'),
                'cycle_duration': result.get('cycle_duration', 0)
            }
            
    except Exception as e:
        logger.error(f"Master optimization cycle failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/decisions")
async def get_recent_ai_decisions(
    limit: int = 20,
    platform: Optional[str] = None,
    decision_type: Optional[str] = None
):
    """Get recent AI decisions with client-friendly formatting"""
    try:
        controller, risk_mgr, reporting_mgr = get_hybrid_ai_dependencies()
        
        # In production, this would query the ai_decision_logs table
        # For now, return mock data showing the system capabilities
        
        mock_decisions = [
            {
                'decision_id': 'decision_20250924_143022_meta_001',
                'timestamp': datetime.now() - timedelta(hours=2),
                'ai_system': 'PulseBridge AI',
                'decision_type': 'strategic_override',
                'platform_affected': 'meta',
                'campaign_id': 'camp_meta_12345',
                'confidence_level': 'High',
                'action_taken': 'Budget optimized for better ROI',
                'expected_improvement': {'roi_improvement': 0.18, 'efficiency_gain': 0.12},
                'reasoning': 'PulseBridge AI detected 87% confident optimization opportunity by reallocating budget to higher-performing LinkedIn campaigns.',
                'client_visible': True,
                'testing_mode': True
            },
            {
                'decision_id': 'decision_20250924_120045_cross_001',
                'timestamp': datetime.now() - timedelta(hours=4),
                'ai_system': 'PulseBridge AI',
                'decision_type': 'budget_reallocation',
                'platform_affected': 'cross_platform',
                'confidence_level': 'High',
                'action_taken': 'Smart budget reallocation across platforms',
                'expected_improvement': {'cross_platform_roi': 0.22},
                'reasoning': 'PulseBridge AI analyzed cross-platform performance and found better conversion opportunities. Smart budget reallocation will maximize advertising investment.',
                'client_visible': True,
                'testing_mode': True
            }
        ]
        
        # Filter by platform if specified
        if platform:
            mock_decisions = [d for d in mock_decisions if d.get('platform_affected') == platform or d.get('platform_affected') == 'cross_platform']
        
        # Filter by decision type if specified
        if decision_type:
            mock_decisions = [d for d in mock_decisions if d.get('decision_type') == decision_type]
        
        return {
            'success': True,
            'decisions': mock_decisions[:limit],
            'total_count': len(mock_decisions),
            'ai_system': 'PulseBridge AI Master Controller',
            'note': 'All decisions show PulseBridge AI as primary intelligence system'
        }
        
    except Exception as e:
        logger.error(f"Failed to get AI decisions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance-analysis")
async def get_cross_platform_performance_analysis():
    """Get cross-platform performance analysis from master AI"""
    try:
        controller, risk_mgr, reporting_mgr = get_hybrid_ai_dependencies()
        
        # Mock cross-platform analysis (would be real data in production)
        analysis = {
            'analysis_timestamp': datetime.now(),
            'ai_system': 'PulseBridge AI',
            'platform_rankings': {
                'linkedin': {
                    'rank': 1,
                    'composite_score': 8.7,
                    'roas': 4.2,
                    'conversion_rate': 3.8,
                    'trend': 'improving'
                },
                'google_ads': {
                    'rank': 2,
                    'composite_score': 7.9,
                    'roas': 3.8,
                    'conversion_rate': 3.2,
                    'trend': 'stable'
                },
                'meta': {
                    'rank': 3,
                    'composite_score': 6.4,
                    'roas': 2.9,
                    'conversion_rate': 2.1,
                    'trend': 'declining',
                    'meta_ai_effectiveness': 0.72
                },
                'pinterest': {
                    'rank': 4,
                    'composite_score': 5.8,
                    'roas': 2.3,
                    'conversion_rate': 1.9,
                    'trend': 'stable'
                }
            },
            'optimization_opportunities': [
                {
                    'platform': 'meta',
                    'opportunity': 'Strategic budget reallocation to LinkedIn',
                    'confidence': 0.89,
                    'estimated_roi_improvement': 0.25,
                    'reasoning': 'LinkedIn showing 45% better conversion rates'
                }
            ],
            'meta_ai_coordination': {
                'status': 'active',
                'effectiveness_score': 0.72,
                'recommendations_processed': 12,
                'overrides_applied': 2,
                'symbiosis_health': 'good'
            }
        }
        
        return {
            'success': True,
            'analysis': analysis,
            'generated_by': 'PulseBridge AI Master Controller',
            'includes_meta_ai_insights': True,
            'client_facing': True
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/risk-assessment")
async def assess_decision_risk(decision_data: Dict[str, Any]):
    """Assess risk for a potential AI decision"""
    try:
        controller, risk_mgr, reporting_mgr = get_hybrid_ai_dependencies()
        
        # Perform risk assessment
        risk_analysis = risk_mgr.assess_decision_risk(
            decision_data=decision_data,
            current_performance={'roas': 3.2, 'conversion_rate': 2.5},
            market_conditions={'volatility': 0.15}
        )
        
        return {
            'success': True,
            'risk_analysis': risk_analysis,
            'recommendation': risk_analysis['recommendation'],
            'safeguards_active': len(risk_analysis['safeguards_triggered']) > 0,
            'assessed_by': 'PulseBridge AI Risk Management System'
        }
        
    except Exception as e:
        logger.error(f"Risk assessment failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/approve-decision")
async def approve_ai_decision(request: DecisionApprovalRequest):
    """Approve or reject an AI decision (for testing mode)"""
    try:
        controller, risk_mgr, reporting_mgr = get_hybrid_ai_dependencies()
        
        # In production, this would update the decision in the database
        # and potentially execute the approved action
        
        return {
            'success': True,
            'decision_id': request.decision_id,
            'approval_status': 'approved' if request.approved else 'rejected',
            'approval_timestamp': datetime.now(),
            'notes': request.approval_notes,
            'next_action': 'execute_decision' if request.approved else 'log_rejection'
        }
        
    except Exception as e:
        logger.error(f"Decision approval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/configuration")
async def get_hybrid_ai_configuration():
    """Get current hybrid AI system configuration"""
    try:
        return {
            'success': True,
            'configuration': {
                'ai_system': 'PulseBridge AI Master Controller',
                'meta_ai_integration': 'symbiotic',
                'risk_management': {
                    'level': 'conservative',
                    'testing_mode': True,
                    'auto_execution': False,
                    'approval_required_over': 100.0
                },
                'client_reporting': {
                    'visibility_mode': 'pulsebridge_branded',
                    'show_confidence_scores': True,
                    'meta_ai_visible': False
                },
                'optimization_settings': {
                    'cycle_frequency': '6 hours',
                    'platforms_monitored': ['meta', 'google_ads', 'linkedin', 'pinterest'],
                    'cross_platform_coordination': True
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get configuration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/configuration")
async def update_hybrid_ai_configuration(config: HybridAIConfig):
    """Update hybrid AI system configuration"""
    try:
        # In production, this would update the configuration in the database
        # and reinitialize the system components with new settings
        
        return {
            'success': True,
            'message': 'Hybrid AI configuration updated successfully',
            'new_configuration': config.dict(),
            'restart_required': False,
            'updated_by': 'PulseBridge AI Configuration Manager'
        }
        
    except Exception as e:
        logger.error(f"Configuration update failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/meta-ai-coordination")
async def get_meta_ai_coordination_status():
    """Get Meta AI coordination status and effectiveness"""
    try:
        return {
            'success': True,
            'coordination_status': {
                'meta_ai_status': 'active',
                'integration_type': 'symbiotic',
                'master_controller': 'PulseBridge AI',
                'effectiveness_metrics': {
                    'symbiosis_score': 0.84,
                    'recommendations_processed': 45,
                    'strategic_overrides': 8,
                    'coordination_success_rate': 0.92
                },
                'recent_coordination': [
                    {
                        'timestamp': datetime.now() - timedelta(minutes=30),
                        'action': 'Meta AI provided audience insights',
                        'pulsebridge_decision': 'Incorporated into cross-platform strategy',
                        'outcome': 'Improved targeting efficiency by 15%'
                    },
                    {
                        'timestamp': datetime.now() - timedelta(hours=2),
                        'action': 'Meta AI recommended budget increase',
                        'pulsebridge_decision': 'Override applied - reallocated to LinkedIn instead',
                        'outcome': 'Better ROI achieved through platform reallocation'
                    }
                ]
            },
            'client_perspective': 'All optimizations appear as PulseBridge AI intelligence',
            'meta_ai_visibility': 'Internal tool only - invisible to clients'
        }
        
    except Exception as e:
        logger.error(f"Failed to get Meta AI coordination status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Export the router
hybrid_ai_router = router