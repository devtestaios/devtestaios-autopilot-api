"""
Workflow Automation Engine
Cross-platform automation triggers and intelligent decision making
"""
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import logging
import asyncio
from enum import Enum

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class EventType(Enum):
    # Lead-related events
    NEW_LEAD_CAPTURED = "new_lead_captured"
    LEAD_SCORED = "lead_scored"
    HIGH_VALUE_LEAD_DETECTED = "high_value_lead_detected"
    
    # Campaign-related events  
    CAMPAIGN_LAUNCHED = "campaign_launched"
    CAMPAIGN_UNDERPERFORMING = "campaign_underperforming"
    BUDGET_OPTIMIZED = "budget_optimized"
    
    # Customer-related events
    CUSTOMER_CONVERTED = "customer_converted"
    HIGH_VALUE_CUSTOMER_DETECTED = "high_value_customer_detected"
    CHURN_RISK_DETECTED = "churn_risk_detected"
    
    # Content-related events
    CONTENT_PUBLISHED = "content_published"
    HIGH_ENGAGEMENT_CONTENT = "high_engagement_content"
    
    # System events
    PERFORMANCE_ALERT = "performance_alert"
    MODEL_RETRAINED = "model_retrained"

class WorkflowStep:
    """Individual step in a workflow"""
    
    def __init__(self, name: str, action: Callable, params: Dict[str, Any] = None):
        self.name = name
        self.action = action
        self.params = params or {}
        self.status = WorkflowStatus.PENDING
        self.started_at = None
        self.completed_at = None
        self.error = None
        
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute this workflow step"""
        try:
            self.status = WorkflowStatus.RUNNING
            self.started_at = datetime.now()
            
            logger.info(f"Executing workflow step: {self.name}")
            
            # Merge context with step params
            execution_params = {**context, **self.params}
            
            # Execute the action
            result = await self.action(**execution_params)
            
            self.status = WorkflowStatus.COMPLETED
            self.completed_at = datetime.now()
            
            logger.info(f"Workflow step {self.name} completed successfully")
            return result
            
        except Exception as e:
            self.status = WorkflowStatus.FAILED
            self.error = str(e)
            self.completed_at = datetime.now()
            
            logger.error(f"Workflow step {self.name} failed: {e}")
            raise

class Workflow:
    """Complete workflow definition"""
    
    def __init__(self, name: str, event_type: EventType, steps: List[WorkflowStep]):
        self.name = name
        self.event_type = event_type
        self.steps = steps
        self.status = WorkflowStatus.PENDING
        self.started_at = None
        self.completed_at = None
        self.current_step = 0
        
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete workflow"""
        try:
            self.status = WorkflowStatus.RUNNING
            self.started_at = datetime.now()
            
            logger.info(f"Starting workflow: {self.name}")
            
            results = []
            
            for i, step in enumerate(self.steps):
                self.current_step = i
                
                # Execute step and collect result
                step_result = await step.execute(context)
                results.append({
                    "step": step.name,
                    "result": step_result,
                    "duration": (step.completed_at - step.started_at).total_seconds()
                })
                
                # Update context with step results for next steps
                context.update(step_result)
            
            self.status = WorkflowStatus.COMPLETED
            self.completed_at = datetime.now()
            
            logger.info(f"Workflow {self.name} completed successfully")
            
            return {
                "workflow": self.name,
                "status": "completed",
                "total_duration": (self.completed_at - self.started_at).total_seconds(),
                "steps_executed": len(results),
                "step_results": results
            }
            
        except Exception as e:
            self.status = WorkflowStatus.FAILED
            logger.error(f"Workflow {self.name} failed at step {self.current_step}: {e}")
            
            return {
                "workflow": self.name,
                "status": "failed",
                "error": str(e),
                "failed_at_step": self.current_step,
                "step_results": results
            }

class WorkflowEngine:
    """Central workflow automation engine"""
    
    def __init__(self):
        self.workflows: Dict[EventType, List[Workflow]] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
        # Register default workflows
        self._register_default_workflows()
    
    def register_workflow(self, workflow: Workflow):
        """Register a new workflow for an event type"""
        if workflow.event_type not in self.workflows:
            self.workflows[workflow.event_type] = []
        
        self.workflows[workflow.event_type].append(workflow)
        logger.info(f"Registered workflow '{workflow.name}' for event {workflow.event_type.value}")
    
    async def trigger_workflows(self, event_type: EventType, event_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Trigger all workflows for a specific event type"""
        if event_type not in self.workflows:
            logger.info(f"No workflows registered for event type: {event_type.value}")
            return []
        
        logger.info(f"Triggering {len(self.workflows[event_type])} workflows for event: {event_type.value}")
        
        results = []
        
        # Execute all workflows for this event type
        for workflow in self.workflows[event_type]:
            try:
                # Create context with event data
                context = {
                    "event_type": event_type.value,
                    "event_data": event_data,
                    "timestamp": datetime.now().isoformat()
                }
                
                # Execute workflow
                result = await workflow.execute(context)
                results.append(result)
                
                # Store in execution history
                self.execution_history.append({
                    "event_type": event_type.value,
                    "workflow_name": workflow.name,
                    "execution_time": datetime.now().isoformat(),
                    "result": result
                })
                
            except Exception as e:
                logger.error(f"Failed to execute workflow {workflow.name}: {e}")
                results.append({
                    "workflow": workflow.name,
                    "status": "failed",
                    "error": str(e)
                })
        
        return results
    
    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get workflow system statistics"""
        total_workflows = sum(len(workflows) for workflows in self.workflows.values())
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for execution in self.execution_history 
                                  if execution.get("result", {}).get("status") == "completed")
        
        success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
        
        return {
            "total_workflows_registered": total_workflows,
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": round(success_rate, 2),
            "event_types_covered": len(self.workflows)
        }
    
    def get_execution_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent execution history"""
        # Return most recent executions first
        return self.execution_history[-limit:] if self.execution_history else []
    
    def _register_default_workflows(self):
        """Register default automation workflows"""
        
        # Workflow 1: New Lead → Scoring → Assignment → Follow-up
        new_lead_workflow = Workflow(
            name="New Lead Processing",
            event_type=EventType.NEW_LEAD_CAPTURED,
            steps=[
                WorkflowStep("score_lead", self._score_lead_action),
                WorkflowStep("assign_sales_rep", self._assign_sales_rep_action),
                WorkflowStep("send_notifications", self._send_notifications_action),
                WorkflowStep("schedule_follow_up", self._schedule_follow_up_action),
                WorkflowStep("update_crm", self._update_crm_action)
            ]
        )
        self.register_workflow(new_lead_workflow)
        
        # Workflow 2: High Value Lead → Priority Processing
        high_value_lead_workflow = Workflow(
            name="High Value Lead Priority Processing",
            event_type=EventType.HIGH_VALUE_LEAD_DETECTED,
            steps=[
                WorkflowStep("notify_management", self._notify_management_action),
                WorkflowStep("assign_senior_rep", self._assign_senior_rep_action),
                WorkflowStep("create_custom_sequence", self._create_custom_sequence_action),
                WorkflowStep("add_to_vip_list", self._add_to_vip_list_action)
            ]
        )
        self.register_workflow(high_value_lead_workflow)
        
        # Workflow 3: Campaign Underperforming → ML Optimization
        campaign_optimization_workflow = Workflow(
            name="Campaign Performance Optimization",
            event_type=EventType.CAMPAIGN_UNDERPERFORMING,
            steps=[
                WorkflowStep("analyze_performance", self._analyze_performance_action),
                WorkflowStep("run_ml_optimization", self._run_ml_optimization_action),
                WorkflowStep("adjust_budgets", self._adjust_budgets_action),
                WorkflowStep("generate_alerts", self._generate_alerts_action)
            ]
        )
        self.register_workflow(campaign_optimization_workflow)
        
        # Workflow 4: Customer Converted → Upsell Preparation
        conversion_workflow = Workflow(
            name="Post-Conversion Optimization",
            event_type=EventType.CUSTOMER_CONVERTED,
            steps=[
                WorkflowStep("update_customer_profile", self._update_customer_profile_action),
                WorkflowStep("create_lookalike_audience", self._create_lookalike_audience_action),
                WorkflowStep("schedule_onboarding", self._schedule_onboarding_action),
                WorkflowStep("identify_upsell_opportunities", self._identify_upsell_opportunities_action)
            ]
        )
        self.register_workflow(conversion_workflow)
    
    # Workflow Action Implementations
    
    async def _score_lead_action(self, **kwargs) -> Dict[str, Any]:
        """Score lead using ML model"""
        event_data = kwargs.get("event_data", {})
        lead_data = event_data.get("lead_data", {})
        
        # Here you would call the actual lead scoring ML model
        # For demo purposes, we'll simulate the scoring
        
        # Simulate ML scoring based on available data
        score = 75  # Would be actual ML prediction
        quality_tier = "WARM"
        
        return {
            "lead_score": score,
            "quality_tier": quality_tier,
            "scoring_model": "lead_scorer_v1.0",
            "action_taken": "lead_scored"
        }
    
    async def _assign_sales_rep_action(self, **kwargs) -> Dict[str, Any]:
        """Assign lead to appropriate sales rep"""
        lead_score = kwargs.get("lead_score", 50)
        quality_tier = kwargs.get("quality_tier", "COOL")
        
        # Assign based on lead quality
        if quality_tier == "HOT":
            assigned_rep = "senior_rep_1"
        elif quality_tier == "WARM":
            assigned_rep = "mid_level_rep_2"
        else:
            assigned_rep = "junior_rep_3"
        
        return {
            "assigned_sales_rep": assigned_rep,
            "assignment_reason": f"Lead quality: {quality_tier}",
            "action_taken": "sales_rep_assigned"
        }
    
    async def _send_notifications_action(self, **kwargs) -> Dict[str, Any]:
        """Send notifications to relevant team members"""
        assigned_rep = kwargs.get("assigned_sales_rep")
        quality_tier = kwargs.get("quality_tier")
        
        notifications_sent = []
        
        # Send SMS to assigned rep for hot leads
        if quality_tier == "HOT":
            notifications_sent.append(f"SMS sent to {assigned_rep}")
        
        # Send email notification
        notifications_sent.append(f"Email sent to {assigned_rep}")
        
        # Slack notification for management on hot leads
        if quality_tier == "HOT":
            notifications_sent.append("Slack notification sent to #sales-alerts")
        
        return {
            "notifications_sent": notifications_sent,
            "notification_count": len(notifications_sent),
            "action_taken": "notifications_sent"
        }
    
    async def _schedule_follow_up_action(self, **kwargs) -> Dict[str, Any]:
        """Schedule appropriate follow-up sequence"""
        quality_tier = kwargs.get("quality_tier")
        
        # Different follow-up schedules based on lead quality
        if quality_tier == "HOT":
            follow_up_schedule = ["5 minutes", "1 hour", "4 hours", "24 hours"]
        elif quality_tier == "WARM":  
            follow_up_schedule = ["1 hour", "24 hours", "3 days", "1 week"]
        else:
            follow_up_schedule = ["24 hours", "1 week", "2 weeks", "1 month"]
        
        return {
            "follow_up_schedule": follow_up_schedule,
            "sequence_type": f"{quality_tier.lower()}_lead_sequence",
            "action_taken": "follow_up_scheduled"
        }
    
    async def _update_crm_action(self, **kwargs) -> Dict[str, Any]:
        """Update CRM with lead information and workflow results"""
        event_data = kwargs.get("event_data", {})
        lead_score = kwargs.get("lead_score")
        assigned_rep = kwargs.get("assigned_sales_rep")
        
        crm_updates = {
            "lead_score": lead_score,
            "assigned_sales_rep": assigned_rep,
            "workflow_processed": True,
            "last_updated": datetime.now().isoformat()
        }
        
        return {
            "crm_updated": True,
            "fields_updated": list(crm_updates.keys()),
            "action_taken": "crm_updated"
        }
    
    async def _notify_management_action(self, **kwargs) -> Dict[str, Any]:
        """Notify management of high-value lead"""
        return {
            "management_notified": True,
            "notification_method": "slack_and_email",
            "action_taken": "management_notified"
        }
    
    async def _assign_senior_rep_action(self, **kwargs) -> Dict[str, Any]:
        """Assign high-value lead to senior sales rep"""
        return {
            "assigned_sales_rep": "senior_rep_vip",
            "priority": "high",
            "action_taken": "senior_rep_assigned"
        }
    
    async def _create_custom_sequence_action(self, **kwargs) -> Dict[str, Any]:
        """Create custom follow-up sequence for high-value leads"""
        return {
            "custom_sequence_created": True,
            "sequence_type": "vip_personalized",
            "action_taken": "custom_sequence_created"
        }
    
    async def _add_to_vip_list_action(self, **kwargs) -> Dict[str, Any]:
        """Add lead to VIP prospect list"""
        return {
            "added_to_vip_list": True,
            "vip_benefits": ["priority_support", "executive_demo", "custom_pricing"],
            "action_taken": "added_to_vip_list"
        }
    
    async def _analyze_performance_action(self, **kwargs) -> Dict[str, Any]:
        """Analyze campaign performance issues"""
        return {
            "performance_analysis": "completed",
            "issues_identified": ["high_cpa", "low_ctr", "audience_fatigue"],
            "action_taken": "performance_analyzed"
        }
    
    async def _run_ml_optimization_action(self, **kwargs) -> Dict[str, Any]:
        """Run ML budget optimization"""
        return {
            "ml_optimization": "completed",
            "budget_recommendations": {"reduce_budget": 20, "shift_to_top_performers": True},
            "action_taken": "ml_optimization_run"
        }
    
    async def _adjust_budgets_action(self, **kwargs) -> Dict[str, Any]:
        """Adjust campaign budgets based on ML recommendations"""
        return {
            "budgets_adjusted": True,
            "adjustment_type": "automated_optimization",
            "action_taken": "budgets_adjusted"
        }
    
    async def _generate_alerts_action(self, **kwargs) -> Dict[str, Any]:
        """Generate performance alerts"""
        return {
            "alerts_generated": True,
            "alert_recipients": ["campaign_manager", "marketing_director"],
            "action_taken": "alerts_generated"
        }
    
    async def _update_customer_profile_action(self, **kwargs) -> Dict[str, Any]:
        """Update customer profile after conversion"""
        return {
            "customer_profile_updated": True,
            "profile_enhancements": ["conversion_source", "ltv_prediction", "segment_assignment"],
            "action_taken": "customer_profile_updated"
        }
    
    async def _create_lookalike_audience_action(self, **kwargs) -> Dict[str, Any]:
        """Create lookalike audience based on converted customer"""
        return {
            "lookalike_audience_created": True,
            "audience_size": "1-2% similarity",
            "action_taken": "lookalike_audience_created"
        }
    
    async def _schedule_onboarding_action(self, **kwargs) -> Dict[str, Any]:
        """Schedule customer onboarding process"""
        return {
            "onboarding_scheduled": True,
            "onboarding_type": "premium_white_glove",
            "action_taken": "onboarding_scheduled"
        }
    
    async def _identify_upsell_opportunities_action(self, **kwargs) -> Dict[str, Any]:
        """Identify potential upsell opportunities"""
        return {
            "upsell_opportunities": ["enterprise_features", "additional_seats", "premium_support"],
            "upsell_probability": 0.75,
            "action_taken": "upsell_opportunities_identified"
        }
    
    def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent workflow execution history"""
        return self.execution_history[-limit:]
    
    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get workflow execution statistics"""
        total_executions = len(self.execution_history)
        successful_executions = sum(1 for h in self.execution_history if h["result"]["status"] == "completed")
        
        return {
            "total_workflows_registered": sum(len(workflows) for workflows in self.workflows.values()),
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
            "event_types_covered": len(self.workflows)
        }

# Global workflow engine instance
workflow_engine = WorkflowEngine()