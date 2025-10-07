"""
Load balancer configuration and health checks
"""

import time
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

class HealthStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    WARNING = "warning"

@dataclass
class ServerInstance:
    id: str
    host: str
    port: int
    weight: int = 100
    status: HealthStatus = HealthStatus.HEALTHY
    last_health_check: Optional[datetime] = None
    response_time: float = 0.0
    error_count: int = 0
    success_count: int = 0

class LoadBalancerManager:
    def __init__(self):
        self.instances = self._initialize_instances()
        self.health_check_interval = 30  # seconds
        self.max_retries = 3
        self.timeout = 5  # seconds
        self.algorithms = {
            "round_robin": self._round_robin,
            "weighted_round_robin": self._weighted_round_robin,
            "least_connections": self._least_connections,
            "health_aware": self._health_aware
        }
        self.current_algorithm = "health_aware"
        self.current_index = 0
        
    def _initialize_instances(self) -> List[ServerInstance]:
        """Initialize server instances - in production this would be dynamic"""
        return [
            ServerInstance(
                id="primary-01",
                host="api-01.autopilot.internal",
                port=8000,
                weight=100
            )
            # Additional instances would be added during scaling
        ]
    
    def add_instance(self, instance: ServerInstance):
        """Add new server instance"""
        self.instances.append(instance)
        print(f"➕ Added server instance: {instance.id} ({instance.host}:{instance.port})")
    
    def remove_instance(self, instance_id: str):
        """Remove server instance"""
        self.instances = [inst for inst in self.instances if inst.id != instance_id]
        print(f"➖ Removed server instance: {instance_id}")
    
    def get_next_server(self) -> Optional[ServerInstance]:
        """Get next server based on current algorithm"""
        healthy_instances = [
            inst for inst in self.instances 
            if inst.status == HealthStatus.HEALTHY
        ]
        
        if not healthy_instances:
            # If no healthy instances, return least unhealthy
            return min(self.instances, key=lambda x: x.error_count) if self.instances else None
        
        algorithm = self.algorithms.get(self.current_algorithm, self._round_robin)
        return algorithm(healthy_instances)
    
    def _round_robin(self, instances: List[ServerInstance]) -> ServerInstance:
        """Simple round-robin selection"""
        if not instances:
            return None
        
        server = instances[self.current_index % len(instances)]
        self.current_index += 1
        return server
    
    def _weighted_round_robin(self, instances: List[ServerInstance]) -> ServerInstance:
        """Weighted round-robin based on server weights"""
        if not instances:
            return None
        
        # Calculate total weight
        total_weight = sum(inst.weight for inst in instances)
        
        # Select based on weights
        target = (self.current_index % total_weight)
        current_weight = 0
        
        for instance in instances:
            current_weight += instance.weight
            if target < current_weight:
                self.current_index += 1
                return instance
        
        # Fallback to first instance
        self.current_index += 1
        return instances[0]
    
    def _least_connections(self, instances: List[ServerInstance]) -> ServerInstance:
        """Select server with least active connections"""
        # In production, this would track actual connection counts
        # For now, use error count as proxy
        return min(instances, key=lambda x: x.error_count)
    
    def _health_aware(self, instances: List[ServerInstance]) -> ServerInstance:
        """Select server considering health and performance"""
        # Score based on response time and error rate
        def calculate_score(instance):
            error_rate = instance.error_count / max(instance.success_count + instance.error_count, 1)
            response_score = 1 / max(instance.response_time, 0.001)  # Avoid division by zero
            health_score = 1.0 if instance.status == HealthStatus.HEALTHY else 0.5
            return response_score * health_score * (1 - error_rate)
        
        return max(instances, key=calculate_score)
    
    async def health_check(self, instance: ServerInstance) -> HealthStatus:
        """Perform health check on server instance"""
        try:
            start_time = time.time()
            
            # Simulate health check - in production this would be actual HTTP request
            await asyncio.sleep(0.1)  # Simulate network delay
            
            response_time = time.time() - start_time
            instance.response_time = response_time
            instance.last_health_check = datetime.utcnow()
            
            # Determine health based on response time
            if response_time < 1.0:
                instance.success_count += 1
                return HealthStatus.HEALTHY
            elif response_time < 2.0:
                return HealthStatus.WARNING
            else:
                instance.error_count += 1
                return HealthStatus.UNHEALTHY
                
        except Exception as e:
            instance.error_count += 1
            instance.last_health_check = datetime.utcnow()
            print(f"❌ Health check failed for {instance.id}: {e}")
            return HealthStatus.UNHEALTHY
    
    async def run_health_checks(self):
        """Run health checks on all instances"""
        print("🔍 Running health checks on all instances...")
        
        tasks = [self.health_check(instance) for instance in self.instances]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if not isinstance(result, Exception):
                self.instances[i].status = result
                status_emoji = "✅" if result == HealthStatus.HEALTHY else "⚠️" if result == HealthStatus.WARNING else "❌"
                print(f"{status_emoji} {self.instances[i].id}: {result.value} (response: {self.instances[i].response_time:.3f}s)")
    
    def get_load_balancer_stats(self) -> Dict[str, any]:
        """Get load balancer statistics"""
        healthy_count = sum(1 for inst in self.instances if inst.status == HealthStatus.HEALTHY)
        warning_count = sum(1 for inst in self.instances if inst.status == HealthStatus.WARNING)
        unhealthy_count = sum(1 for inst in self.instances if inst.status == HealthStatus.UNHEALTHY)
        
        avg_response_time = sum(inst.response_time for inst in self.instances) / max(len(self.instances), 1)
        total_requests = sum(inst.success_count + inst.error_count for inst in self.instances)
        total_errors = sum(inst.error_count for inst in self.instances)
        
        return {
            "total_instances": len(self.instances),
            "healthy_instances": healthy_count,
            "warning_instances": warning_count,
            "unhealthy_instances": unhealthy_count,
            "availability_percentage": (healthy_count / max(len(self.instances), 1)) * 100,
            "current_algorithm": self.current_algorithm,
            "avg_response_time": round(avg_response_time, 3),
            "total_requests": total_requests,
            "error_rate": (total_errors / max(total_requests, 1)) * 100,
            "instances": [
                {
                    "id": inst.id,
                    "host": inst.host,
                    "port": inst.port,
                    "status": inst.status.value,
                    "response_time": inst.response_time,
                    "success_count": inst.success_count,
                    "error_count": inst.error_count,
                    "last_check": inst.last_health_check.isoformat() if inst.last_health_check else None
                }
                for inst in self.instances
            ]
        }
    
    def update_algorithm(self, algorithm: str) -> bool:
        """Update load balancing algorithm"""
        if algorithm in self.algorithms:
            self.current_algorithm = algorithm
            print(f"🔄 Updated load balancing algorithm to: {algorithm}")
            return True
        return False
    
    def simulate_scaling_event(self, action: str, instance_count: int = 1):
        """Simulate auto-scaling events"""
        if action == "scale_out":
            for i in range(instance_count):
                new_instance = ServerInstance(
                    id=f"auto-{len(self.instances) + i + 1:02d}",
                    host=f"api-{len(self.instances) + i + 1:02d}.autopilot.internal",
                    port=8000,
                    weight=100
                )
                self.add_instance(new_instance)
        
        elif action == "scale_in" and len(self.instances) > 1:
            # Remove instances with highest error rates
            instances_to_remove = sorted(
                self.instances, 
                key=lambda x: x.error_count, 
                reverse=True
            )[:instance_count]
            
            for instance in instances_to_remove:
                if len(self.instances) > 1:  # Keep at least one instance
                    self.remove_instance(instance.id)

# Global load balancer manager
load_balancer = LoadBalancerManager()
