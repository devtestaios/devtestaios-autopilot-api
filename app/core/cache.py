"""
Redis caching implementation for performance optimization
"""

import redis
import json
import pickle
from typing import Any, Optional, Union
from datetime import timedelta
import os
from functools import wraps

# Redis connection
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=int(os.getenv('REDIS_DB', 0)),
    password=os.getenv('REDIS_PASSWORD'),
    decode_responses=True
)

class CacheManager:
    def __init__(self):
        self.client = redis_client
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            value = self.client.get(key)
            if value is None:
                return None
            
            # Try to parse as JSON first, then pickle
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return pickle.loads(value.encode('latin1'))
        except Exception as e:
            print(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL in seconds"""
        try:
            # Try to serialize as JSON first, then pickle
            try:
                serialized = json.dumps(value)
            except (TypeError, ValueError):
                serialized = pickle.dumps(value).decode('latin1')
            
            return self.client.setex(key, ttl, serialized)
        except Exception as e:
            print(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            print(f"Cache delete error for key {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache clear pattern error for {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            print(f"Cache exists error for key {key}: {e}")
            return False

# Global cache instance
cache = CacheManager()

def cached(ttl: int = 3600, key_prefix: str = ""):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:"
            
            # Add args to key (skip self for methods)
            if args:
                start_idx = 1 if hasattr(args[0], func.__name__) else 0
                cache_key += ":".join(str(arg) for arg in args[start_idx:])
            
            # Add kwargs to key
            if kwargs:
                cache_key += ":" + ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        
        # Add cache control methods
        wrapper.cache_clear = lambda: cache.clear_pattern(f"{key_prefix}:{func.__name__}:*")
        wrapper.cache_key = lambda *args, **kwargs: f"{key_prefix}:{func.__name__}:" + ":".join(str(arg) for arg in args) + (":" + ":".join(f"{k}={v}" for k, v in sorted(kwargs.items())) if kwargs else "")
        
        return wrapper
    return decorator

# Pre-defined cache keys for common operations
class CacheKeys:
    USER_PROFILE = "user:profile:{user_id}"
    CAMPAIGN_ANALYTICS = "campaign:analytics:{campaign_id}:{timeframe}"
    PLATFORM_METRICS = "platform:metrics:{metric_type}:{period}"
    SUBSCRIPTION_STATUS = "subscription:status:{user_id}"
    COMPLIANCE_SCORE = "compliance:score:{tenant_id}"
    PERFORMANCE_METRICS = "performance:metrics:{timestamp}"
    
    @staticmethod
    def format_key(key_template: str, **kwargs) -> str:
        """Format cache key with parameters"""
        return key_template.format(**kwargs)

# Cache warming functions
async def warm_cache():
    """Warm up frequently accessed cache entries"""
    print("🔥 Warming up cache...")
    
    # This would be called during application startup
    # or periodically to ensure hot data is cached
    
    # Example: Pre-cache platform metrics
    cache.set("platform:active_users:24h", 1250, ttl=1800)  # 30 min TTL
    cache.set("platform:api_calls:1h", 5640, ttl=300)       # 5 min TTL
    cache.set("platform:revenue:today", 2340.50, ttl=3600)  # 1 hour TTL
    
    print("✅ Cache warmed up successfully")

# Cache monitoring
def get_cache_stats():
    """Get cache statistics"""
    try:
        info = redis_client.info()
        return {
            "used_memory": info.get('used_memory_human', 'N/A'),
            "connected_clients": info.get('connected_clients', 0),
            "total_commands_processed": info.get('total_commands_processed', 0),
            "keyspace_hits": info.get('keyspace_hits', 0),
            "keyspace_misses": info.get('keyspace_misses', 0),
            "hit_rate": round(
                info.get('keyspace_hits', 0) / 
                max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1) * 100, 
                2
            )
        }
    except Exception as e:
        return {"error": str(e)}
