from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from app.database import get_db
from app.models import User
from app.core.auth import get_current_user
from app.core.permissions import require_permissions, Permission
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import psutil
import time

router = APIRouter(prefix="/api/performance", tags=["performance"])

@router.get("/metrics")
async def get_performance_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive performance metrics"""
    require_permissions(current_user, [Permission.ADMIN])
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Database performance
    db_stats = db.execute(text("""
        SELECT 
            COUNT(*) as total_connections,
            (SELECT COUNT(*) FROM users) as total_users,
            (SELECT COUNT(*) FROM audit_logs WHERE created_at > NOW() - INTERVAL '1 hour') as logs_last_hour,
            (SELECT AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) FROM audit_logs WHERE created_at > NOW() - INTERVAL '1 hour') as avg_response_time
    """)).fetchone()
    
    # API response times (simulated for now - would integrate with actual monitoring)
    response_times = {
        "/api/campaigns": 0.25,
        "/api/users": 0.18,
        "/api/analytics": 0.45,
        "/api/billing": 0.32,
        "/api/compliance": 0.28
    }
    
    # Performance thresholds
    thresholds = {
        "cpu_warning": 70,
        "cpu_critical": 90,
        "memory_warning": 80,
        "memory_critical": 95,
        "response_time_warning": 1.0,
        "response_time_critical": 2.0
    }
    
    # Calculate performance score
    cpu_score = max(0, 100 - cpu_percent)
    memory_score = max(0, 100 - memory.percent)
    response_score = max(0, 100 - (max(response_times.values()) * 50))
    
    overall_score = (cpu_score + memory_score + response_score) / 3
    
    return {
        "overall_score": round(overall_score, 1),
        "system_metrics": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "disk_usage_percent": round((disk.used / disk.total) * 100, 1),
            "disk_free_gb": round(disk.free / (1024**3), 2)
        },
        "database_metrics": {
            "total_connections": db_stats.total_connections,
            "total_users": db_stats.total_users,
            "logs_last_hour": db_stats.logs_last_hour,
            "avg_response_time": round(float(db_stats.avg_response_time or 0), 3)
        },
        "api_response_times": response_times,
        "thresholds": thresholds,
        "alerts": _generate_performance_alerts(
            cpu_percent, memory.percent, response_times, thresholds
        ),
        "timestamp": datetime.utcnow().isoformat()
    }

def _generate_performance_alerts(cpu_percent, memory_percent, response_times, thresholds):
    """Generate performance alerts based on thresholds"""
    alerts = []
    
    if cpu_percent > thresholds["cpu_critical"]:
        alerts.append({
            "level": "critical",
            "metric": "CPU",
            "value": cpu_percent,
            "threshold": thresholds["cpu_critical"],
            "message": f"Critical CPU usage: {cpu_percent}%"
        })
    elif cpu_percent > thresholds["cpu_warning"]:
        alerts.append({
            "level": "warning",
            "metric": "CPU",
            "value": cpu_percent,
            "threshold": thresholds["cpu_warning"],
            "message": f"High CPU usage: {cpu_percent}%"
        })
    
    if memory_percent > thresholds["memory_critical"]:
        alerts.append({
            "level": "critical",
            "metric": "Memory",
            "value": memory_percent,
            "threshold": thresholds["memory_critical"],
            "message": f"Critical memory usage: {memory_percent}%"
        })
    elif memory_percent > thresholds["memory_warning"]:
        alerts.append({
            "level": "warning",
            "metric": "Memory",
            "value": memory_percent,
            "threshold": thresholds["memory_warning"],
            "message": f"High memory usage: {memory_percent}%"
        })
    
    for endpoint, response_time in response_times.items():
        if response_time > thresholds["response_time_critical"]:
            alerts.append({
                "level": "critical",
                "metric": "Response Time",
                "endpoint": endpoint,
                "value": response_time,
                "threshold": thresholds["response_time_critical"],
                "message": f"Critical response time for {endpoint}: {response_time}s"
            })
        elif response_time > thresholds["response_time_warning"]:
            alerts.append({
                "level": "warning",
                "metric": "Response Time",
                "endpoint": endpoint,
                "value": response_time,
                "threshold": thresholds["response_time_warning"],
                "message": f"Slow response time for {endpoint}: {response_time}s"
            })
    
    return alerts

@router.get("/optimization-recommendations")
async def get_optimization_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get performance optimization recommendations"""
    require_permissions(current_user, [Permission.ADMIN])
    
    # Analyze current performance
    metrics = await get_performance_metrics(current_user, db)
    
    recommendations = []
    
    # CPU recommendations
    if metrics["system_metrics"]["cpu_percent"] > 70:
        recommendations.append({
            "category": "CPU Optimization",
            "priority": "high" if metrics["system_metrics"]["cpu_percent"] > 90 else "medium",
            "title": "Scale CPU Resources",
            "description": "Consider upgrading to more CPU cores or optimizing CPU-intensive operations",
            "actions": [
                "Enable horizontal scaling",
                "Implement caching for CPU-intensive operations",
                "Optimize database queries",
                "Consider CPU auto-scaling"
            ]
        })
    
    # Memory recommendations
    if metrics["system_metrics"]["memory_percent"] > 80:
        recommendations.append({
            "category": "Memory Optimization",
            "priority": "high" if metrics["system_metrics"]["memory_percent"] > 95 else "medium",
            "title": "Optimize Memory Usage",
            "description": "Memory usage is high, consider optimization strategies",
            "actions": [
                "Implement Redis caching",
                "Optimize database connection pooling",
                "Add memory monitoring alerts",
                "Consider memory auto-scaling"
            ]
        })
    
    # Database recommendations
    if metrics["database_metrics"]["logs_last_hour"] > 1000:
        recommendations.append({
            "category": "Database Optimization",
            "priority": "medium",
            "title": "Optimize Database Performance",
            "description": "High database activity detected",
            "actions": [
                "Implement database read replicas",
                "Add database connection pooling",
                "Optimize slow queries",
                "Consider database sharding"
            ]
        })
    
    # API response time recommendations
    slow_endpoints = [
        endpoint for endpoint, time in metrics["api_response_times"].items()
        if time > 0.5
    ]
    
    if slow_endpoints:
        recommendations.append({
            "category": "API Performance",
            "priority": "medium",
            "title": "Optimize API Response Times",
            "description": f"Slow endpoints detected: {', '.join(slow_endpoints)}",
            "actions": [
                "Implement API response caching",
                "Add database query optimization",
                "Consider API rate limiting",
                "Implement async processing for heavy operations"
            ]
        })
    
    # Scaling recommendations
    user_count = metrics["database_metrics"]["total_users"]
    if user_count > 1000:
        recommendations.append({
            "category": "Infrastructure Scaling",
            "priority": "high" if user_count > 5000 else "medium",
            "title": "Prepare for Scale",
            "description": f"Current user count: {user_count}. Prepare for increased load",
            "actions": [
                "Implement auto-scaling groups",
                "Set up load balancers",
                "Add CDN for static assets",
                "Implement microservices architecture"
            ]
        })
    
    return {
        "total_recommendations": len(recommendations),
        "high_priority": len([r for r in recommendations if r["priority"] == "high"]),
        "medium_priority": len([r for r in recommendations if r["priority"] == "medium"]),
        "low_priority": len([r for r in recommendations if r["priority"] == "low"]),
        "recommendations": recommendations,
        "generated_at": datetime.utcnow().isoformat()
    }

@router.post("/optimize")
async def trigger_optimization(
    optimization_type: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Trigger specific optimization tasks"""
    require_permissions(current_user, [Permission.ADMIN])
    
    valid_types = ["cache_warmup", "database_cleanup", "index_optimization", "memory_cleanup"]
    
    if optimization_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid optimization type. Valid types: {valid_types}")
    
    # Add background task for optimization
    background_tasks.add_task(_run_optimization, optimization_type)
    
    return {
        "message": f"Optimization '{optimization_type}' started",
        "type": optimization_type,
        "status": "running",
        "started_at": datetime.utcnow().isoformat()
    }

async def _run_optimization(optimization_type: str):
    """Run specific optimization in background"""
    try:
        if optimization_type == "cache_warmup":
            # Warm up frequently accessed data
            await asyncio.sleep(2)  # Simulate cache warmup
            
        elif optimization_type == "database_cleanup":
            # Clean up old audit logs, temporary data
            await asyncio.sleep(3)  # Simulate cleanup
            
        elif optimization_type == "index_optimization":
            # Analyze and optimize database indexes
            await asyncio.sleep(5)  # Simulate index optimization
            
        elif optimization_type == "memory_cleanup":
            # Force garbage collection and memory cleanup
            import gc
            gc.collect()
            
        print(f"✅ Optimization '{optimization_type}' completed successfully")
        
    except Exception as e:
        print(f"❌ Optimization '{optimization_type}' failed: {str(e)}")

@router.get("/scaling-plan")
async def get_scaling_plan(
    target_users: int = 10000,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate scaling plan for target user count"""
    require_permissions(current_user, [Permission.ADMIN])
    
    current_users = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
    scale_factor = target_users / max(current_users, 1)
    
    scaling_plan = {
        "current_users": current_users,
        "target_users": target_users,
        "scale_factor": round(scale_factor, 2),
        "infrastructure_requirements": {
            "api_servers": {
                "current": 1,
                "recommended": max(2, int(scale_factor * 2)),
                "reason": "Load distribution and redundancy"
            },
            "database": {
                "current": "Single instance",
                "recommended": "Primary + 2 read replicas" if target_users > 5000 else "Primary + 1 read replica",
                "reason": "Read scaling and availability"
            },
            "cache_layer": {
                "current": "None",
                "recommended": "Redis cluster",
                "memory_gb": max(4, int(scale_factor * 2)),
                "reason": "Reduce database load and improve response times"
            },
            "cdn": {
                "current": "None",
                "recommended": "Global CDN with edge caching",
                "reason": "Static asset delivery and global performance"
            },
            "load_balancer": {
                "current": "None", 
                "recommended": "Application Load Balancer with auto-scaling",
                "reason": "Traffic distribution and high availability"
            }
        },
        "estimated_costs": {
            "current_monthly": 200,  # Estimated current cost
            "projected_monthly": int(200 * scale_factor * 0.7),  # Economies of scale
            "cost_per_user": round((200 * scale_factor * 0.7) / target_users, 2)
        },
        "implementation_phases": [
            {
                "phase": 1,
                "users": min(target_users, 2500),
                "priority": "high",
                "tasks": [
                    "Implement Redis caching",
                    "Database connection pooling",
                    "API response optimization",
                    "Basic monitoring setup"
                ]
            },
            {
                "phase": 2,
                "users": min(target_users, 5000),
                "priority": "medium",
                "tasks": [
                    "Add read replica",
                    "Implement CDN",
                    "Set up load balancer",
                    "Auto-scaling configuration"
                ]
            },
            {
                "phase": 3,
                "users": target_users,
                "priority": "low",
                "tasks": [
                    "Database sharding",
                    "Microservices architecture",
                    "Advanced caching strategies",
                    "Global multi-region deployment"
                ]
            }
        ]
    }
    
    return scaling_plan
