"""
Platform Interconnectivity API Endpoints
Cross-platform communication, data sync, and automation management
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from app.platform_interconnect import (
    interconnect_engine, 
    PlatformConnection, 
    PlatformType, 
    AutomationRule,
    CrossPlatformEvent
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/interconnect", tags=["Platform Interconnectivity"])

# Request/Response Models
class PlatformRegistrationRequest(BaseModel):
    """Request to register a new platform connection"""
    platform_id: str = Field(..., description="Unique identifier for the platform")
    platform_type: str = Field(..., description="Type of platform (crm, ads, email, etc.)")
    platform_name: str = Field(..., description="Human-readable platform name")
    api_credentials: Dict[str, str] = Field(..., description="API credentials for the platform")
    sync_frequency: int = Field(default=30, description="Sync frequency in minutes")
    data_mapping: Dict[str, str] = Field(default={}, description="Data field mapping configuration")
    capabilities: List[str] = Field(default=[], description="Platform capabilities")
    webhook_url: Optional[str] = Field(default=None, description="Webhook URL for real-time updates")

class PlatformRegistrationResponse(BaseModel):
    """Response from platform registration"""
    success: bool
    platform_id: str
    message: str
    connection_status: str

class AutomationRuleRequest(BaseModel):
    """Request to create custom automation rule"""
    name: str = Field(..., description="Name of the automation rule")
    trigger_conditions: Dict[str, Any] = Field(..., description="Conditions that trigger the automation")
    source_platforms: List[str] = Field(..., description="Platforms that can trigger this rule")
    target_platforms: List[str] = Field(..., description="Platforms where actions will be executed")
    actions: List[Dict[str, Any]] = Field(..., description="Actions to execute when triggered")
    ml_scoring: bool = Field(default=False, description="Whether to use ML scoring")
    confidence_threshold: float = Field(default=0.7, description="Minimum confidence score to execute")
    is_active: bool = Field(default=True, description="Whether the rule is active")

class AutomationRuleResponse(BaseModel):
    """Response from automation rule creation"""
    success: bool
    rule_id: str
    message: str

class PlatformStatusResponse(BaseModel):
    """Response with platform status information"""
    total_platforms: int
    healthy_platforms: int
    platform_types: List[str]
    active_rules: int
    total_executions: int
    avg_success_rate: float

class MLInsightsResponse(BaseModel):
    """Response with ML insights summary"""
    platforms_with_insights: int
    insights: Dict[str, Any]

class AutomationPerformanceResponse(BaseModel):
    """Response with automation performance metrics"""
    total_rules: int
    active_rules: int
    executions_last_7_days: int
    avg_success_rate: float
    most_triggered_rules: List[Dict[str, Any]]

class CrossPlatformSyncRequest(BaseModel):
    """Request to trigger cross-platform data sync"""
    platform_ids: Optional[List[str]] = Field(default=None, description="Specific platforms to sync (all if None)")
    sync_type: str = Field(default="incremental", description="Type of sync (incremental, full)")
    include_ml_analysis: bool = Field(default=True, description="Whether to include ML analysis")

class DataFlowVisualizationResponse(BaseModel):
    """Response with data flow visualization data"""
    platforms: List[Dict[str, Any]]
    connections: List[Dict[str, Any]]
    recent_events: List[Dict[str, Any]]
    automation_flows: List[Dict[str, Any]]

# Health and Status Endpoints

@router.get("/health", response_model=Dict[str, Any])
async def get_interconnect_health():
    """Get health status of the interconnectivity system"""
    try:
        status = await interconnect_engine.get_platform_status()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "interconnect_engine": "operational",
            "platform_summary": status
        }
    except Exception as e:
        logger.error(f"Error getting interconnect health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status", response_model=PlatformStatusResponse)
async def get_platform_status():
    """Get detailed status of all connected platforms"""
    try:
        status = await interconnect_engine.get_platform_status()
        return PlatformStatusResponse(**status)
    except Exception as e:
        logger.error(f"Error getting platform status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Platform Management Endpoints

@router.post("/platforms/register", response_model=PlatformRegistrationResponse)
async def register_platform(request: PlatformRegistrationRequest, background_tasks: BackgroundTasks):
    """Register a new platform for interconnectivity"""
    try:
        # Validate platform type
        try:
            platform_type = PlatformType(request.platform_type.lower())
        except ValueError:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid platform type: {request.platform_type}"
            )
        
        # Create platform connection
        connection = PlatformConnection(
            platform_id=request.platform_id,
            platform_type=platform_type,
            platform_name=request.platform_name,
            api_credentials=request.api_credentials,
            connection_status="pending",
            last_sync=datetime.now(),
            sync_frequency=request.sync_frequency,
            data_mapping=request.data_mapping,
            capabilities=request.capabilities,
            webhook_url=request.webhook_url
        )
        
        # Register platform (this will validate connection)
        success = await interconnect_engine.register_platform(connection)
        
        if success:
            # Update connection status
            connection.connection_status = "active"
            
            return PlatformRegistrationResponse(
                success=True,
                platform_id=request.platform_id,
                message=f"Platform {request.platform_name} registered successfully",
                connection_status="active"
            )
        else:
            return PlatformRegistrationResponse(
                success=False,
                platform_id=request.platform_id,
                message=f"Failed to register platform {request.platform_name}",
                connection_status="failed"
            )
            
    except Exception as e:
        logger.error(f"Error registering platform: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/platforms")
async def list_platforms():
    """List all registered platforms"""
    try:
        platforms = []
        for platform_id, connection in interconnect_engine.connections.items():
            platforms.append({
                "platform_id": platform_id,
                "platform_name": connection.platform_name,
                "platform_type": connection.platform_type.value,
                "connection_status": connection.connection_status,
                "last_sync": connection.last_sync.isoformat(),
                "sync_frequency": connection.sync_frequency,
                "is_healthy": connection.is_healthy(),
                "capabilities": connection.capabilities
            })
        
        return {
            "total_platforms": len(platforms),
            "platforms": platforms
        }
    except Exception as e:
        logger.error(f"Error listing platforms: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/platforms/{platform_id}")
async def unregister_platform(platform_id: str):
    """Unregister a platform"""
    try:
        if platform_id not in interconnect_engine.connections:
            raise HTTPException(status_code=404, detail=f"Platform {platform_id} not found")
        
        # Remove platform connection
        platform_name = interconnect_engine.connections[platform_id].platform_name
        del interconnect_engine.connections[platform_id]
        
        # Clean up related data
        if f"{platform_id}_data" in interconnect_engine.data_sync_cache:
            del interconnect_engine.data_sync_cache[f"{platform_id}_data"]
        if f"{platform_id}_config" in interconnect_engine.data_sync_cache:
            del interconnect_engine.data_sync_cache[f"{platform_id}_config"]
        if platform_id in interconnect_engine.ml_insights:
            del interconnect_engine.ml_insights[platform_id]
        
        return {
            "success": True,
            "message": f"Platform {platform_name} unregistered successfully"
        }
    except Exception as e:
        logger.error(f"Error unregistering platform: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ML Insights Endpoints

@router.get("/insights", response_model=MLInsightsResponse)
async def get_ml_insights():
    """Get ML insights summary across all platforms"""
    try:
        insights = await interconnect_engine.get_ml_insights_summary()
        return MLInsightsResponse(**insights)
    except Exception as e:
        logger.error(f"Error getting ML insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/insights/{platform_id}")
async def get_platform_insights(platform_id: str):
    """Get detailed ML insights for a specific platform"""
    try:
        if platform_id not in interconnect_engine.connections:
            raise HTTPException(status_code=404, detail=f"Platform {platform_id} not found")
        
        insights = interconnect_engine.ml_insights.get(platform_id, {})
        
        return {
            "platform_id": platform_id,
            "platform_name": interconnect_engine.connections[platform_id].platform_name,
            "insights": insights
        }
    except Exception as e:
        logger.error(f"Error getting platform insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Automation Management Endpoints

@router.get("/automation/performance", response_model=AutomationPerformanceResponse)
async def get_automation_performance():
    """Get automation performance metrics"""
    try:
        performance = await interconnect_engine.get_automation_performance()
        return AutomationPerformanceResponse(**performance)
    except Exception as e:
        logger.error(f"Error getting automation performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/automation/rules")
async def list_automation_rules():
    """List all automation rules"""
    try:
        rules = []
        for rule_id, rule in interconnect_engine.automation_rules.items():
            rules.append({
                "rule_id": rule_id,
                "name": rule.name,
                "source_platforms": rule.source_platforms,
                "target_platforms": rule.target_platforms,
                "is_active": rule.is_active,
                "execution_count": rule.execution_count,
                "success_rate": rule.success_rate,
                "confidence_threshold": rule.confidence_threshold,
                "ml_scoring": rule.ml_scoring
            })
        
        return {
            "total_rules": len(rules),
            "rules": rules
        }
    except Exception as e:
        logger.error(f"Error listing automation rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/automation/rules", response_model=AutomationRuleResponse)
async def create_automation_rule(request: AutomationRuleRequest):
    """Create a custom automation rule"""
    try:
        rule_data = request.dict()
        rule_id = await interconnect_engine.create_custom_automation_rule(rule_data)
        
        return AutomationRuleResponse(
            success=True,
            rule_id=rule_id,
            message=f"Automation rule '{request.name}' created successfully"
        )
    except Exception as e:
        logger.error(f"Error creating automation rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/automation/rules/{rule_id}/toggle")
async def toggle_automation_rule(rule_id: str):
    """Toggle automation rule active status"""
    try:
        if rule_id not in interconnect_engine.automation_rules:
            raise HTTPException(status_code=404, detail=f"Automation rule {rule_id} not found")
        
        rule = interconnect_engine.automation_rules[rule_id]
        rule.is_active = not rule.is_active
        
        status = "activated" if rule.is_active else "deactivated"
        
        return {
            "success": True,
            "rule_id": rule_id,
            "is_active": rule.is_active,
            "message": f"Automation rule '{rule.name}' {status}"
        }
    except Exception as e:
        logger.error(f"Error toggling automation rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/automation/rules/{rule_id}")
async def delete_automation_rule(rule_id: str):
    """Delete an automation rule"""
    try:
        if rule_id not in interconnect_engine.automation_rules:
            raise HTTPException(status_code=404, detail=f"Automation rule {rule_id} not found")
        
        rule_name = interconnect_engine.automation_rules[rule_id].name
        del interconnect_engine.automation_rules[rule_id]
        
        return {
            "success": True,
            "message": f"Automation rule '{rule_name}' deleted successfully"
        }
    except Exception as e:
        logger.error(f"Error deleting automation rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Data Synchronization Endpoints

@router.post("/sync/trigger")
async def trigger_cross_platform_sync(request: CrossPlatformSyncRequest, background_tasks: BackgroundTasks):
    """Trigger cross-platform data synchronization"""
    try:
        platforms_to_sync = request.platform_ids or list(interconnect_engine.connections.keys())
        
        # Validate platforms exist
        invalid_platforms = [p for p in platforms_to_sync if p not in interconnect_engine.connections]
        if invalid_platforms:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid platforms: {invalid_platforms}"
            )
        
        # Trigger sync for each platform
        sync_results = []
        for platform_id in platforms_to_sync:
            try:
                # Add sync task to background
                background_tasks.add_task(
                    interconnect_engine._sync_platform_data, 
                    platform_id
                )
                
                sync_results.append({
                    "platform_id": platform_id,
                    "status": "sync_scheduled",
                    "sync_type": request.sync_type
                })
            except Exception as e:
                sync_results.append({
                    "platform_id": platform_id,
                    "status": "sync_failed",
                    "error": str(e)
                })
        
        return {
            "success": True,
            "message": f"Sync triggered for {len(platforms_to_sync)} platforms",
            "sync_type": request.sync_type,
            "results": sync_results
        }
    except Exception as e:
        logger.error(f"Error triggering cross-platform sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sync/status")
async def get_sync_status():
    """Get synchronization status for all platforms"""
    try:
        sync_status = []
        for platform_id, connection in interconnect_engine.connections.items():
            last_sync_data = interconnect_engine.data_sync_cache.get(f"{platform_id}_data", {})
            
            sync_status.append({
                "platform_id": platform_id,
                "platform_name": connection.platform_name,
                "last_sync": connection.last_sync.isoformat(),
                "sync_frequency": connection.sync_frequency,
                "is_healthy": connection.is_healthy(),
                "record_count": last_sync_data.get("record_count", 0),
                "last_data_sync": last_sync_data.get("sync_time").isoformat() if last_sync_data.get("sync_time") else None
            })
        
        return {
            "total_platforms": len(sync_status),
            "sync_status": sync_status
        }
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Visualization and Analytics Endpoints

@router.get("/visualization/data-flow", response_model=DataFlowVisualizationResponse)
async def get_data_flow_visualization():
    """Get data flow visualization data"""
    try:
        # Prepare platforms data
        platforms = []
        for platform_id, connection in interconnect_engine.connections.items():
            platforms.append({
                "id": platform_id,
                "name": connection.platform_name,
                "type": connection.platform_type.value,
                "status": connection.connection_status,
                "health": connection.is_healthy(),
                "capabilities": connection.capabilities
            })
        
        # Prepare connections data (relationships between platforms)
        connections = []
        for rule_id, rule in interconnect_engine.automation_rules.items():
            if rule.is_active:
                for source in rule.source_platforms:
                    for target in rule.target_platforms:
                        connections.append({
                            "source": source,
                            "target": target,
                            "rule_id": rule_id,
                            "rule_name": rule.name,
                            "strength": rule.success_rate
                        })
        
        # Prepare recent events
        recent_events = []
        for event in interconnect_engine.event_queue[-10:]:  # Last 10 events
            recent_events.append({
                "event_id": event.event_id,
                "source_platform": event.source_platform,
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "confidence_score": event.confidence_score
            })
        
        # Prepare automation flows
        automation_flows = []
        for rule_id, rule in interconnect_engine.automation_rules.items():
            automation_flows.append({
                "rule_id": rule_id,
                "name": rule.name,
                "source_platforms": rule.source_platforms,
                "target_platforms": rule.target_platforms,
                "execution_count": rule.execution_count,
                "success_rate": rule.success_rate,
                "is_active": rule.is_active
            })
        
        return DataFlowVisualizationResponse(
            platforms=platforms,
            connections=connections,
            recent_events=recent_events,
            automation_flows=automation_flows
        )
    except Exception as e:
        logger.error(f"Error getting data flow visualization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/cross-platform-impact")
async def get_cross_platform_impact():
    """Get analytics on cross-platform impact and performance"""
    try:
        # Calculate cross-platform impact metrics
        total_automations = sum(rule.execution_count for rule in interconnect_engine.automation_rules.values())
        
        platform_impact = {}
        for platform_id, connection in interconnect_engine.connections.items():
            # Count how many rules this platform participates in
            source_rules = len([r for r in interconnect_engine.automation_rules.values() 
                              if platform_id in r.source_platforms or connection.platform_type.value in r.source_platforms])
            target_rules = len([r for r in interconnect_engine.automation_rules.values() 
                              if platform_id in r.target_platforms or connection.platform_type.value in r.target_platforms])
            
            platform_impact[platform_id] = {
                "platform_name": connection.platform_name,
                "platform_type": connection.platform_type.value,
                "source_rules": source_rules,
                "target_rules": target_rules,
                "total_participation": source_rules + target_rules,
                "health_score": 1.0 if connection.is_healthy() else 0.5
            }
        
        # Calculate automation effectiveness
        active_rules = len([r for r in interconnect_engine.automation_rules.values() if r.is_active])
        avg_success_rate = sum(r.success_rate for r in interconnect_engine.automation_rules.values()) / len(interconnect_engine.automation_rules) if interconnect_engine.automation_rules else 0
        
        return {
            "total_platforms": len(interconnect_engine.connections),
            "total_automation_rules": len(interconnect_engine.automation_rules),
            "active_automation_rules": active_rules,
            "total_automations_executed": total_automations,
            "average_success_rate": avg_success_rate,
            "platform_impact": platform_impact,
            "interconnectivity_score": (len(interconnect_engine.connections) * avg_success_rate * active_rules) / 100 if active_rules > 0 else 0
        }
    except Exception as e:
        logger.error(f"Error getting cross-platform impact: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Demo and Testing Endpoints

@router.post("/demo/simulate-event")
async def simulate_cross_platform_event(
    platform_id: str,
    event_type: str,
    event_data: Dict[str, Any] = None
):
    """Simulate a cross-platform event for testing"""
    try:
        if platform_id not in interconnect_engine.connections:
            raise HTTPException(status_code=404, detail=f"Platform {platform_id} not found")
        
        # Create simulated event
        event = CrossPlatformEvent(
            event_id=f"demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            source_platform=platform_id,
            event_type=event_type,
            event_data=event_data or {"demo": True, "timestamp": datetime.now().isoformat()},
            timestamp=datetime.now(),
            confidence_score=0.9,
            suggested_actions=[]
        )
        
        # Add to event queue
        interconnect_engine.event_queue.append(event)
        
        # Check for automation triggers
        await interconnect_engine._check_automation_triggers(platform_id, event_data)
        
        return {
            "success": True,
            "event_id": event.event_id,
            "message": f"Simulated {event_type} event for {platform_id}",
            "event": event.to_dict()
        }
    except Exception as e:
        logger.error(f"Error simulating cross-platform event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/demo/quick-setup")
async def demo_quick_setup():
    """Quick setup demo platforms for testing"""
    try:
        demo_platforms = [
            {
                "platform_id": "demo_hubspot",
                "platform_type": "crm",
                "platform_name": "Demo HubSpot",
                "api_credentials": {"api_key": "demo_key_hubspot"},
                "capabilities": ["lead_management", "contact_sync", "deal_tracking"]
            },
            {
                "platform_id": "demo_google_ads",
                "platform_type": "ads",
                "platform_name": "Demo Google Ads",
                "api_credentials": {"access_token": "demo_token_gads", "account_id": "demo_account"},
                "capabilities": ["campaign_management", "budget_optimization", "performance_tracking"]
            },
            {
                "platform_id": "demo_mailchimp",
                "platform_type": "email",
                "platform_name": "Demo Mailchimp",
                "api_credentials": {"api_key": "demo_key_mailchimp"},
                "capabilities": ["email_campaigns", "audience_segmentation", "automation_sequences"]
            },
            {
                "platform_id": "demo_slack",
                "platform_type": "communication",
                "platform_name": "Demo Slack",
                "api_credentials": {"webhook_url": "https://hooks.slack.com/demo"},
                "capabilities": ["notifications", "team_alerts", "integration_updates"]
            }
        ]
        
        setup_results = []
        for platform_data in demo_platforms:
            try:
                platform_type = PlatformType(platform_data["platform_type"])
                connection = PlatformConnection(
                    platform_id=platform_data["platform_id"],
                    platform_type=platform_type,
                    platform_name=platform_data["platform_name"],
                    api_credentials=platform_data["api_credentials"],
                    connection_status="active",
                    last_sync=datetime.now(),
                    sync_frequency=30,
                    data_mapping={},
                    capabilities=platform_data["capabilities"]
                )
                
                success = await interconnect_engine.register_platform(connection)
                setup_results.append({
                    "platform_id": platform_data["platform_id"],
                    "success": success,
                    "status": "registered" if success else "failed"
                })
            except Exception as e:
                setup_results.append({
                    "platform_id": platform_data["platform_id"],
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "message": "Demo platforms setup completed",
            "platforms_registered": len([r for r in setup_results if r["success"]]),
            "results": setup_results
        }
    except Exception as e:
        logger.error(f"Error in demo quick setup: {e}")
        raise HTTPException(status_code=500, detail=str(e))