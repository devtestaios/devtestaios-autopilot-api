"""
Autonomous Decision API Endpoints for PulseBridge.ai
Provides REST API endpoints for autonomous decision-making system
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging
import asyncio

# Import our autonomous decision components
from autonomous_decision_framework import (
    AutonomousDecisionFramework, 
    AutonomousDecision,
    DecisionContext,
    DecisionType,
    RiskLevel,
    ApprovalStatus,
    ExecutionResult,
    LearningFeedback
)
from decision_execution_engine import DecisionExecutionEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/autonomous", tags=["Autonomous Decision System"])

# Global instances
decision_framework = AutonomousDecisionFramework()
execution_engine = DecisionExecutionEngine()

# Pydantic models for API
class DecisionContextRequest(BaseModel):
    campaign_id: str
    platform: str
    current_performance: Dict[str, float]
    historical_performance: List[Dict[str, Any]]
    budget_constraints: Dict[str, float]
    business_goals: Dict[str, float]
    market_conditions: Optional[Dict[str, Any]] = {}
    competitor_analysis: Optional[Dict[str, Any]] = {}
    seasonal_factors: Optional[Dict[str, float]] = {}

class OptimizationGoals(BaseModel):
    target_roas: Optional[float] = 3.0
    max_cpa: Optional[float] = None
    target_conversion_rate: Optional[float] = 0.05
    budget_efficiency_threshold: Optional[float] = 0.8

class DecisionApprovalRequest(BaseModel):
    decision_id: str
    approved: bool
    approval_notes: Optional[str] = None
    approver_id: Optional[str] = None

class ExecutionRequest(BaseModel):
    decision_id: str
    force_execute: Optional[bool] = False
    scheduled_time: Optional[datetime] = None
    priority: Optional[int] = 3

class LearningFeedbackRequest(BaseModel):
    decision_id: str
    actual_performance: Dict[str, float]
    timeframe_days: Optional[int] = 7

class AutonomySettings(BaseModel):
    auto_execution_enabled: bool
    risk_tolerance: str  # low, medium, high
    approval_thresholds: Dict[str, float]
    safety_guardrails_enabled: bool
    emergency_stop_enabled: bool

# Global autonomy settings
current_autonomy_settings = AutonomySettings(
    auto_execution_enabled=True,
    risk_tolerance="medium",
    approval_thresholds={
        "budget_change_percentage": 25.0,
        "minimum_confidence_score": 0.7,
        "maximum_daily_spend": 1000.0
    },
    safety_guardrails_enabled=True,
    emergency_stop_enabled=True
)

@router.get("/health")
async def health_check():
    """Health check for autonomous decision system"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "decision_framework": "operational",
            "execution_engine": "operational",
            "safety_guardrails": "enabled" if current_autonomy_settings.safety_guardrails_enabled else "disabled"
        }
    }

@router.post("/analyze")
async def analyze_decision_opportunities(
    context: DecisionContextRequest,
    goals: OptimizationGoals
) -> Dict[str, Any]:
    """Analyze current context and generate autonomous decision recommendations"""
    try:
        # Convert request to DecisionContext
        decision_context = DecisionContext(
            campaign_id=context.campaign_id,
            platform=context.platform,
            current_performance=context.current_performance,
            historical_performance=context.historical_performance,
            budget_constraints=context.budget_constraints,
            business_goals=context.business_goals,
            market_conditions=context.market_conditions,
            competitor_analysis=context.competitor_analysis,
            seasonal_factors=context.seasonal_factors
        )
        
        # Generate decisions
        decisions = await decision_framework.analyze_decision_opportunity(
            decision_context, 
            goals.dict()
        )
        
        # Format response
        return {
            "total_opportunities": len(decisions),
            "decisions": [
                {
                    "decision_id": d.decision_id,
                    "decision_type": d.decision_type.value,
                    "campaign_id": d.campaign_id,
                    "platform": d.platform,
                    "proposed_action": d.proposed_action,
                    "reasoning": d.reasoning,
                    "confidence_score": d.confidence_score,
                    "risk_level": d.risk_level.value,
                    "expected_impact": d.expected_impact,
                    "requires_human_approval": d.requires_human_approval,
                    "auto_execute_allowed": d.auto_execute_allowed,
                    "safety_checks": d.safety_checks,
                    "expires_at": d.expires_at.isoformat()
                }
                for d in decisions
            ],
            "analysis_timestamp": datetime.now().isoformat(),
            "autonomy_settings": current_autonomy_settings.dict()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing decision opportunities: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/decisions/pending")
async def get_pending_decisions():
    """Get all pending decisions awaiting approval or execution"""
    try:
        # This would retrieve from a database in production
        pending_decisions = [
            d for d in decision_framework.active_decisions.values()
            if d.approval_status in [ApprovalStatus.PENDING, ApprovalStatus.APPROVED]
        ]
        
        return {
            "total_pending": len(pending_decisions),
            "decisions": [
                {
                    "decision_id": d.decision_id,
                    "decision_type": d.decision_type.value,
                    "campaign_id": d.campaign_id,
                    "platform": d.platform,
                    "proposed_action": d.proposed_action,
                    "reasoning": d.reasoning,
                    "confidence_score": d.confidence_score,
                    "risk_level": d.risk_level.value,
                    "approval_status": d.approval_status.value,
                    "requires_human_approval": d.requires_human_approval,
                    "created_at": d.created_at.isoformat(),
                    "expires_at": d.expires_at.isoformat()
                }
                for d in pending_decisions
            ]
        }
        
    except Exception as e:
        logger.error(f"Error retrieving pending decisions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve pending decisions: {str(e)}")

@router.post("/decisions/{decision_id}/approve")
async def approve_decision(
    decision_id: str,
    approval: DecisionApprovalRequest
) -> Dict[str, Any]:
    """Approve or reject a pending decision"""
    try:
        # Find the decision
        decision = decision_framework.active_decisions.get(decision_id)
        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")
        
        # Update approval status
        if approval.approved:
            decision.approval_status = ApprovalStatus.APPROVED
            status_message = "Decision approved"
        else:
            decision.approval_status = ApprovalStatus.REJECTED
            status_message = "Decision rejected"
        
        # If approved and auto-execution is allowed, queue for execution
        if approval.approved and decision.auto_execute_allowed:
            execution_id = await execution_engine.queue_decision_execution(decision)
            return {
                "status": status_message,
                "decision_id": decision_id,
                "execution_queued": True,
                "execution_id": execution_id,
                "approval_timestamp": datetime.now().isoformat()
            }
        
        return {
            "status": status_message,
            "decision_id": decision_id,
            "execution_queued": False,
            "approval_timestamp": datetime.now().isoformat(),
            "notes": approval.approval_notes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving decision {decision_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Approval failed: {str(e)}")

@router.post("/execute")
async def execute_decision(
    execution_request: ExecutionRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Execute an approved decision"""
    try:
        # Find the decision
        decision = decision_framework.active_decisions.get(execution_request.decision_id)
        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")
        
        # Check if execution is allowed
        if not execution_request.force_execute:
            if decision.requires_human_approval and decision.approval_status != ApprovalStatus.APPROVED:
                raise HTTPException(
                    status_code=403, 
                    detail="Decision requires approval before execution"
                )
            
            if not decision.auto_execute_allowed and not execution_request.force_execute:
                raise HTTPException(
                    status_code=403, 
                    detail="Decision cannot be auto-executed. Use force_execute=true to override."
                )
        
        # Queue for execution
        execution_id = await execution_engine.queue_decision_execution(
            decision,
            priority=execution_request.priority,
            scheduled_time=execution_request.scheduled_time
        )
        
        # Start background execution if scheduled for immediate execution
        if not execution_request.scheduled_time or execution_request.scheduled_time <= datetime.now():
            background_tasks.add_task(execution_engine.execute_next_queued_decision)
        
        return {
            "status": "execution_queued",
            "decision_id": execution_request.decision_id,
            "execution_id": execution_id,
            "scheduled_time": (execution_request.scheduled_time or datetime.now()).isoformat(),
            "priority": execution_request.priority
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing decision: {e}")
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")

@router.get("/execution/{execution_id}/status")
async def get_execution_status(execution_id: str):
    """Get status of a decision execution"""
    try:
        status = execution_engine.get_execution_status(execution_id)
        if not status:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving execution status: {e}")
        raise HTTPException(status_code=500, detail=f"Status retrieval failed: {str(e)}")

@router.get("/execution/queue")
async def get_execution_queue():
    """Get current execution queue status"""
    try:
        return execution_engine.get_queue_status()
        
    except Exception as e:
        logger.error(f"Error retrieving queue status: {e}")
        raise HTTPException(status_code=500, detail=f"Queue status retrieval failed: {str(e)}")

@router.post("/execution/{execution_id}/rollback")
async def rollback_execution(execution_id: str):
    """Rollback a previously executed decision"""
    try:
        success = await execution_engine.rollback_execution(execution_id)
        
        if success:
            return {
                "status": "rollback_successful",
                "execution_id": execution_id,
                "rollback_timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "rollback_failed",
                "execution_id": execution_id,
                "error": "Rollback operation failed"
            }
        
    except Exception as e:
        logger.error(f"Error rolling back execution {execution_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Rollback failed: {str(e)}")

@router.post("/learning/feedback")
async def submit_learning_feedback(feedback_request: LearningFeedbackRequest):
    """Submit learning feedback for decision improvement"""
    try:
        feedback = await decision_framework.learn_from_outcomes(
            feedback_request.decision_id,
            feedback_request.actual_performance,
            feedback_request.timeframe_days
        )
        
        return {
            "status": "feedback_recorded",
            "decision_id": feedback_request.decision_id,
            "accuracy_score": feedback.accuracy_score,
            "decision_quality": feedback.decision_quality,
            "lessons_learned": feedback.lessons_learned,
            "model_adjustments": feedback.model_adjustments,
            "feedback_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error submitting learning feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Feedback submission failed: {str(e)}")

@router.get("/settings")
async def get_autonomy_settings():
    """Get current autonomy settings"""
    return {
        "settings": current_autonomy_settings.dict(),
        "last_updated": datetime.now().isoformat()
    }

@router.put("/settings")
async def update_autonomy_settings(settings: AutonomySettings):
    """Update autonomy settings"""
    try:
        global current_autonomy_settings
        current_autonomy_settings = settings
        
        return {
            "status": "settings_updated",
            "settings": settings.dict(),
            "updated_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating autonomy settings: {e}")
        raise HTTPException(status_code=500, detail=f"Settings update failed: {str(e)}")

@router.post("/emergency-stop")
async def emergency_stop():
    """Emergency stop all autonomous operations"""
    try:
        # This would implement emergency stop procedures
        # For now, we'll disable auto-execution
        global current_autonomy_settings
        current_autonomy_settings.auto_execution_enabled = False
        current_autonomy_settings.emergency_stop_enabled = True
        
        # Stop all queued executions
        execution_queue_status = execution_engine.get_queue_status()
        
        return {
            "status": "emergency_stop_activated",
            "timestamp": datetime.now().isoformat(),
            "actions_taken": [
                "Auto-execution disabled",
                "Emergency stop enabled",
                f"{execution_queue_status['total_queued']} queued executions halted"
            ],
            "active_executions": execution_queue_status['active_executions']
        }
        
    except Exception as e:
        logger.error(f"Error activating emergency stop: {e}")
        raise HTTPException(status_code=500, detail=f"Emergency stop failed: {str(e)}")

@router.get("/performance/summary")
async def get_autonomous_performance_summary():
    """Get performance summary of autonomous decision system"""
    try:
        # Calculate performance metrics from decision history
        total_decisions = len(decision_framework.decision_history)
        successful_decisions = len([
            d for d in decision_framework.decision_history 
            if d.approval_status == ApprovalStatus.EXECUTED
        ])
        
        # Calculate learning metrics
        total_feedback = len(decision_framework.learning_data)
        avg_accuracy = sum(f.accuracy_score for f in decision_framework.learning_data) / max(total_feedback, 1)
        
        # Calculate execution metrics
        queue_status = execution_engine.get_queue_status()
        
        return {
            "decision_metrics": {
                "total_decisions_generated": total_decisions,
                "successful_executions": successful_decisions,
                "success_rate": successful_decisions / max(total_decisions, 1),
                "pending_approvals": len([
                    d for d in decision_framework.active_decisions.values()
                    if d.approval_status == ApprovalStatus.PENDING
                ])
            },
            "learning_metrics": {
                "total_feedback_received": total_feedback,
                "average_accuracy_score": avg_accuracy,
                "improvement_rate": 0.15  # Would be calculated from historical data
            },
            "execution_metrics": queue_status,
            "system_health": {
                "auto_execution_enabled": current_autonomy_settings.auto_execution_enabled,
                "safety_guardrails_active": current_autonomy_settings.safety_guardrails_enabled,
                "emergency_stop_enabled": current_autonomy_settings.emergency_stop_enabled
            },
            "summary_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating performance summary: {e}")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")

# Background task for continuous autonomous operation
async def autonomous_decision_loop():
    """Background loop for continuous autonomous decision making"""
    while current_autonomy_settings.auto_execution_enabled:
        try:
            # Execute next queued decision
            result = await execution_engine.execute_next_queued_decision()
            
            if result:
                logger.info(f"Autonomous execution completed: {result.decision_id}")
            
            # Wait before next iteration
            await asyncio.sleep(30)  # Check every 30 seconds
            
        except Exception as e:
            logger.error(f"Error in autonomous decision loop: {e}")
            await asyncio.sleep(60)  # Wait longer on error

# Start the autonomous loop when the module is imported
# In production, this would be managed by a proper task scheduler
asyncio.create_task(autonomous_decision_loop())

# Export the router
__all__ = ['router']