"""
Auto-scaling configuration and monitoring
"""

from typing import Dict, List, Any
from datetime import datetime, timedelta
import psutil
import asyncio
from app.core.cache import cache, cached

class AutoScalingManager:
    def __init__(self):
        self.scaling_policies = {
            "cpu_scale_out": {
                "metric": "cpu_percent",
                "threshold": 70,
                "action": "scale_out",
                "cooldown": 300  # 5 minutes
            },
            "cpu_scale_in": {
                "metric": "cpu_percent", 
                "threshold": 30,
                "action": "scale_in",
                "cooldown": 600  # 10 minutes
            },
            "memory_scale_out": {
                "metric": "memory_percent",
                "threshold": 80,
                "action": "scale_out",
                "cooldown": 300
            },
            "response_time_scale_out": {
                "metric": "response_time",
                "threshold": 1.0,
                "action": "scale_out", 
                "cooldown": 180  # 3 minutes
            }
        }
        
        self.current_instances = 1
        self.min_instances = 1
        self.max_instances = 10
        self.last_scaling_action = None
    
    @cached(ttl=60, key_prefix="autoscaling")
    def get_current_metrics(self) -> Dict[str, float]:
        """Get current system metrics for scaling decisions"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "response_time": self._get_avg_response_time(),
            "active_connections": self._get_active_connections(),
            "requests_per_minute": self._get_requests_per_minute()
        }
    
    def _get_avg_response_time(self) -> float:
        """Get average response time from cache or default"""
        cached_response_time = cache.get("performance:avg_response_time")
        return cached_response_time if cached_response_time else 0.25
    
    def _get_active_connections(self) -> int:
        """Get active database connections"""
        # This would integrate with actual database monitoring
        return cache.get("database:active_connections") or 5
    
    def _get_requests_per_minute(self) -> int:
        """Get requests per minute"""
        return cache.get("api:requests_per_minute") or 120
    
    def evaluate_scaling_decision(self) -> Dict[str, Any]:
        """Evaluate whether scaling action is needed"""
        metrics = self.get_current_metrics()
        current_time = datetime.utcnow()
        
        scaling_recommendation = {
            "action": "none",
            "reason": "All metrics within normal range",
            "current_instances": self.current_instances,
            "target_instances": self.current_instances,
            "metrics": metrics,
            "evaluated_at": current_time.isoformat()
        }
        
        # Check if we're in cooldown period
        if self._in_cooldown(current_time):
            scaling_recommendation["reason"] = "In cooldown period from last scaling action"
            return scaling_recommendation
        
        # Evaluate each scaling policy
        for policy_name, policy in self.scaling_policies.items():
            metric_value = metrics.get(policy["metric"], 0)
            
            # Scale out conditions
            if (policy["action"] == "scale_out" and 
                metric_value > policy["threshold"] and 
                self.current_instances < self.max_instances):
                
                scaling_recommendation.update({
                    "action": "scale_out",
                    "reason": f"{policy['metric']} ({metric_value}) exceeded threshold ({policy['threshold']})",
                    "target_instances": min(self.current_instances + 1, self.max_instances),
                    "triggered_by": policy_name
                })
                break
            
            # Scale in conditions  
            elif (policy["action"] == "scale_in" and 
                  metric_value < policy["threshold"] and 
                  self.current_instances > self.min_instances):
                
                scaling_recommendation.update({
                    "action": "scale_in",
                    "reason": f"{policy['metric']} ({metric_value}) below threshold ({policy['threshold']})",
                    "target_instances": max(self.current_instances - 1, self.min_instances),
                    "triggered_by": policy_name
                })
                break
        
        return scaling_recommendation
    
    def _in_cooldown(self, current_time: datetime) -> bool:
        """Check if we're in cooldown period"""
        if not self.last_scaling_action:
            return False
        
        cooldown_period = timedelta(seconds=300)  # 5 minutes default
        return current_time - self.last_scaling_action < cooldown_period
    
    async def execute_scaling_action(self, action: str, target_instances: int) -> Dict[str, Any]:
        """Execute scaling action"""
        if action == "none":
            return {"status": "no_action", "message": "No scaling action required"}
        
        try:
            if action == "scale_out":
                result = await self._scale_out(target_instances)
            elif action == "scale_in":
                result = await self._scale_in(target_instances)
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}
            
            if result["status"] == "success":
                self.current_instances = target_instances
                self.last_scaling_action = datetime.utcnow()
            
            return result
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _scale_out(self, target_instances: int) -> Dict[str, Any]:
        """Scale out to more instances"""
        # In production, this would integrate with cloud auto-scaling APIs
        print(f"🚀 Scaling OUT from {self.current_instances} to {target_instances} instances")
        
        # Simulate scaling delay
        await asyncio.sleep(2)
        
        # Update cache with new capacity
        cache.set("autoscaling:capacity_increase", True, ttl=300)
        
        return {
            "status": "success",
            "action": "scale_out",
            "previous_instances": self.current_instances,
            "new_instances": target_instances,
            "message": f"Successfully scaled out to {target_instances} instances"
        }
    
    async def _scale_in(self, target_instances: int) -> Dict[str, Any]:
        """Scale in to fewer instances"""
        print(f"📉 Scaling IN from {self.current_instances} to {target_instances} instances")
        
        # Simulate graceful shutdown delay
        await asyncio.sleep(3)
        
        # Update cache
        cache.set("autoscaling:capacity_decrease", True, ttl=300)
        
        return {
            "status": "success", 
            "action": "scale_in",
            "previous_instances": self.current_instances,
            "new_instances": target_instances,
            "message": f"Successfully scaled in to {target_instances} instances"
        }
    
    def get_scaling_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get scaling history for the last N hours"""
        # In production, this would query actual scaling history
        return [
            {
                "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                "action": "scale_out",
                "from_instances": 1,
                "to_instances": 2,
                "reason": "High CPU usage (75%)",
                "metric_trigger": "cpu_percent"
            },
            {
                "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                "action": "scale_in",
                "from_instances": 2,
                "to_instances": 1,
                "reason": "Low CPU usage (25%)",
                "metric_trigger": "cpu_percent"
            }
        ]
    
    def update_scaling_policy(self, policy_name: str, threshold: float, cooldown: int = None):
        """Update scaling policy threshold"""
        if policy_name in self.scaling_policies:
            self.scaling_policies[policy_name]["threshold"] = threshold
            if cooldown:
                self.scaling_policies[policy_name]["cooldown"] = cooldown
            return {"status": "success", "message": f"Updated {policy_name} policy"}
        return {"status": "error", "message": f"Policy {policy_name} not found"}

# Global auto-scaling manager
auto_scaling = AutoScalingManager()
