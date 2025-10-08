"""
Workflow Automation API Endpoints
Cross-platform automation triggers and monitoring
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from app.workflow_engine import workflow_engine, EventType, WorkflowStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/workflows", tags=["Workflow Automation"])

# Request/Response Models
class TriggerWorkflowRequest(BaseModel):
    """Request to trigger workflow automation"""
    event_type: str = Field(..., description="Type of event that occurred")
    event_data: Dict[str, Any] = Field(..., description="Data associated with the event")
    async_execution: bool = Field(default=True, description="Execute workflows asynchronously")

class WorkflowExecutionResponse(BaseModel):
    """Response from workflow execution"""
    execution_id: str
    event_type: str
    workflows_triggered: int
    execution_status: str
    results: List[Dict[str, Any]]
    timestamp: str

class WorkflowStatsResponse(BaseModel):
    """Workflow system statistics"""
    total_workflows_registered: int
    total_executions: int
    successful_executions: int
    success_rate: float
    event_types_covered: int

# Demo Request Models
class DemoLeadData(BaseModel):
    """Demo lead data for testing workflows"""
    name: str = Field(default="Demo Lead")
    email: str = Field(default="demo@example.com")
    company: str = Field(default="Demo Company")
    source: str = Field(default="website")
    score_override: Optional[int] = Field(default=None, description="Override calculated score for demo")

# API Endpoints

@router.post("/trigger", response_model=WorkflowExecutionResponse)
async def trigger_workflows(
    request: TriggerWorkflowRequest,
    background_tasks: BackgroundTasks
) -> WorkflowExecutionResponse:
    """
    Trigger automation workflows for a specific event
    
    This is the main entry point for cross-platform automation.
    When events occur (new lead, campaign performance change, etc.),
    this endpoint triggers the appropriate automated workflows.
    """
    try:
        # Validate event type
        try:
            event_type_enum = EventType(request.event_type)
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid event type: {request.event_type}. Valid types: {[e.value for e in EventType]}"
            )
        
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        logger.info(f"Triggering workflows for event: {request.event_type}")
        
        if request.async_execution:
            # Execute workflows in background
            background_tasks.add_task(
                workflow_engine.trigger_workflows,
                event_type_enum,
                request.event_data
            )
            
            return WorkflowExecutionResponse(
                execution_id=execution_id,
                event_type=request.event_type,
                workflows_triggered=len(workflow_engine.workflows.get(event_type_enum, [])),
                execution_status="started_async",
                results=[],
                timestamp=datetime.now().isoformat()
            )
        else:
            # Execute workflows synchronously
            results = await workflow_engine.trigger_workflows(event_type_enum, request.event_data)
            
            return WorkflowExecutionResponse(
                execution_id=execution_id,
                event_type=request.event_type,
                workflows_triggered=len(results),
                execution_status="completed",
                results=results,
                timestamp=datetime.now().isoformat()
            )
        
    except Exception as e:
        logger.error(f"Failed to trigger workflows: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow trigger failed: {str(e)}")

@router.get("/stats", response_model=WorkflowStatsResponse)
async def get_workflow_stats() -> WorkflowStatsResponse:
    """
    Get workflow system statistics and performance metrics
    
    Returns information about registered workflows, execution history,
    and success rates across all automation types.
    """
    try:
        stats = workflow_engine.get_workflow_stats()
        return WorkflowStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get workflow stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@router.get("/history")
async def get_execution_history(limit: int = 20) -> Dict[str, Any]:
    """
    Get recent workflow execution history
    
    Returns detailed execution logs for monitoring and debugging
    automation performance.
    """
    try:
        history = workflow_engine.get_execution_history(limit)
        
        return {
            "status": "success",
            "execution_history": history,
            "total_returned": len(history),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get execution history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")

@router.get("/event-types")
async def get_supported_event_types() -> Dict[str, Any]:
    """
    Get list of supported event types for workflow triggers
    
    Returns all available event types that can trigger automations,
    along with descriptions and example usage.
    """
    try:
        event_types = []
        
        for event_type in EventType:
            # Count registered workflows for each event type
            workflow_count = len(workflow_engine.workflows.get(event_type, []))
            
            event_types.append({
                "event_type": event_type.value,
                "description": _get_event_description(event_type),
                "registered_workflows": workflow_count,
                "example_usage": _get_event_example(event_type)
            })
        
        return {
            "status": "success",
            "supported_event_types": event_types,
            "total_event_types": len(event_types),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get event types: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get event types: {str(e)}")

@router.get("/health")
async def workflow_health() -> Dict[str, Any]:
    """Health check for workflow automation system"""
    try:
        stats = workflow_engine.get_workflow_stats()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "workflows_registered": stats["total_workflows_registered"],
            "recent_success_rate": stats["success_rate"],
            "capabilities": [
                "cross_platform_automation",
                "lead_processing_workflows", 
                "campaign_optimization_workflows",
                "customer_lifecycle_automation",
                "real_time_event_processing"
            ]
        }
        
    except Exception as e:
        logger.error(f"Workflow health check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Demo Endpoints

@router.post("/demo/new-lead")
async def demo_new_lead_workflow(lead_data: DemoLeadData) -> Dict[str, Any]:
    """
    Demo: Trigger new lead processing workflow
    
    Demonstrates the complete lead processing automation:
    Lead Capture → AI Scoring → Sales Assignment → Follow-up Scheduling
    """
    try:
        # Prepare demo event data
        event_data = {
            "lead_data": {
                "contact_info": {
                    "name": lead_data.name,
                    "email": lead_data.email,
                    "company": lead_data.company
                },
                "source_info": {"source": lead_data.source},
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Add score override if provided
        if lead_data.score_override:
            event_data["lead_data"]["score_override"] = lead_data.score_override
        
        # Trigger new lead workflow
        results = await workflow_engine.trigger_workflows(
            EventType.NEW_LEAD_CAPTURED,
            event_data
        )
        
        return {
            "status": "success",
            "demo_type": "new_lead_processing",
            "lead_processed": lead_data.name,
            "workflow_results": results,
            "automation_summary": _summarize_lead_workflow_results(results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Demo new lead workflow failed: {e}")
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}")

@router.post("/demo/high-value-lead")
async def demo_high_value_lead_workflow() -> Dict[str, Any]:
    """
    Demo: Trigger high-value lead processing workflow
    
    Demonstrates VIP lead handling with priority assignment and
    custom follow-up sequences.
    """
    try:
        # High-value lead demo data
        event_data = {
            "lead_data": {
                "contact_info": {
                    "name": "Enterprise CEO",
                    "email": "ceo@fortune500.com",
                    "company": "Fortune 500 Corp"
                },
                "company_info": {
                    "employee_count": 50000,
                    "industry": "technology",
                    "revenue": 5000000000
                },
                "lead_score": 95,
                "quality_tier": "HOT"
            }
        }
        
        # Trigger high-value lead workflow
        results = await workflow_engine.trigger_workflows(
            EventType.HIGH_VALUE_LEAD_DETECTED,
            event_data
        )
        
        return {
            "status": "success",
            "demo_type": "high_value_lead_processing",
            "lead_processed": "Enterprise CEO",
            "workflow_results": results,
            "vip_benefits_activated": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Demo high-value lead workflow failed: {e}")
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}")

@router.post("/demo/campaign-optimization")
async def demo_campaign_optimization_workflow() -> Dict[str, Any]:
    """
    Demo: Trigger campaign optimization workflow
    
    Demonstrates automated response to underperforming campaigns
    with ML-powered budget adjustments.
    """
    try:
        # Campaign performance demo data
        event_data = {
            "campaign_data": {
                "campaign_id": "demo_campaign_123",
                "campaign_name": "Q4 Lead Generation",
                "performance_metrics": {
                    "cpa": 85.50,
                    "target_cpa": 50.00,
                    "performance_decline": 40,
                    "budget_remaining": 5000
                },
                "issues_detected": ["high_cpa", "low_conversion_rate", "audience_fatigue"]
            }
        }
        
        # Trigger campaign optimization workflow
        results = await workflow_engine.trigger_workflows(
            EventType.CAMPAIGN_UNDERPERFORMING,
            event_data
        )
        
        return {
            "status": "success",
            "demo_type": "campaign_optimization",
            "campaign_optimized": "Q4 Lead Generation",
            "workflow_results": results,
            "optimization_actions": _summarize_campaign_optimization(results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Demo campaign optimization workflow failed: {e}")
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}")

# Helper Functions

def _get_event_description(event_type: EventType) -> str:
    """Get human-readable description for event type"""
    descriptions = {
        EventType.NEW_LEAD_CAPTURED: "New lead captured from any platform (forms, ads, social, etc.)",
        EventType.LEAD_SCORED: "Lead has been scored by AI system",
        EventType.HIGH_VALUE_LEAD_DETECTED: "High-quality lead identified (score > 80)",
        EventType.CAMPAIGN_LAUNCHED: "New marketing campaign started",
        EventType.CAMPAIGN_UNDERPERFORMING: "Campaign performance below targets",
        EventType.BUDGET_OPTIMIZED: "Campaign budgets optimized by ML",
        EventType.CUSTOMER_CONVERTED: "Lead converted to paying customer",
        EventType.HIGH_VALUE_CUSTOMER_DETECTED: "High-value customer identified",
        EventType.CHURN_RISK_DETECTED: "Customer showing churn risk signals",
        EventType.CONTENT_PUBLISHED: "New content published across platforms",
        EventType.HIGH_ENGAGEMENT_CONTENT: "Content receiving high engagement",
        EventType.PERFORMANCE_ALERT: "System performance alert triggered",
        EventType.MODEL_RETRAINED: "ML model retrained with new data"
    }
    return descriptions.get(event_type, "Event description not available")

def _get_event_example(event_type: EventType) -> Dict[str, Any]:
    """Get example event data for event type"""
    examples = {
        EventType.NEW_LEAD_CAPTURED: {
            "lead_data": {
                "contact_info": {"name": "John Doe", "email": "john@company.com"},
                "source_info": {"source": "google_ads", "campaign_id": "camp_123"}
            }
        },
        EventType.CAMPAIGN_UNDERPERFORMING: {
            "campaign_data": {
                "campaign_id": "camp_123",
                "performance_decline": 30,
                "issues": ["high_cpa", "low_ctr"]
            }
        }
    }
    return examples.get(event_type, {"example": "data_structure"})

def _summarize_lead_workflow_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize lead workflow execution results"""
    if not results:
        return {"summary": "No workflows executed"}
    
    # Extract key information from workflow results
    summary = {
        "workflows_executed": len(results),
        "actions_taken": [],
        "lead_score": "N/A",
        "assigned_rep": "N/A",
        "follow_up_scheduled": False
    }
    
    for result in results:
        if result.get("status") == "completed":
            steps = result.get("step_results", [])
            for step in steps:
                step_result = step.get("result", {})
                summary["actions_taken"].append(step_result.get("action_taken", "unknown"))
                
                # Extract specific values
                if "lead_score" in step_result:
                    summary["lead_score"] = step_result["lead_score"]
                if "assigned_sales_rep" in step_result:
                    summary["assigned_rep"] = step_result["assigned_sales_rep"]
                if "follow_up_scheduled" in step_result:
                    summary["follow_up_scheduled"] = True
    
    return summary

def _summarize_campaign_optimization(results: List[Dict[str, Any]]) -> List[str]:
    """Summarize campaign optimization actions taken"""
    actions = []
    
    for result in results:
        if result.get("status") == "completed":
            steps = result.get("step_results", [])
            for step in steps:
                action = step.get("result", {}).get("action_taken")
                if action:
                    actions.append(action)
    
    return actions or ["No optimization actions taken"]

# Export router
__all__ = ["router"]