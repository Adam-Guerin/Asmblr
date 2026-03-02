"""
Unified Caching System for Asmblr
Consolidates multiple cache implementations for efficiency
"""

import time
import json
import hashlib
import threading
from typing import Any, Optional, Dict
from pathlib import Path
import redis

class UnifiedCache:
    """Unified caching system with Redis backend and local fallback"""
    
    def __init__(self, redis_url: str = None, local_cache_size: int = 1000):
        self.redis_url = redis_url
        self.local_cache_size = local_cache_size
        self._local_cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
        self._lock = threading.RLock()
        self._redis_client = None
        
    def _get_redis(self):
        """Get Redis client with lazy initialization"""
        if self.redis_url and self._redis_client is None:
            try:
                import redis
                self._redis_client = redis.from_url(self.redis_url)
            except Exception:
                self._redis_client = None
        return self._redis_client
    
    def _is_expired(self, key: str, ttl: int = 3600) -> bool:
        """Check if cache entry is expired"""
        if key not in self._timestamps:
            return True
        return time.time() - self._timestamps[key] > ttl
    
    def get(self, key: str, ttl: int = 3600) -> Optional[Any]:
        """Get cached value"""
        # Try Redis first
        redis_client = self._get_redis()
        if redis_client:
            try:
                value = redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception:
                pass
        
        # Fallback to local cache
        with self._lock:
            if key in self._local_cache and not self._is_expired(key, ttl):
                return self._local_cache[key]
            elif key in self._local_cache:
                del self._local_cache[key]
                del self._timestamps[key]
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Set cached value"""
        serialized = json.dumps(value)
        
        # Try Redis first
        redis_client = self._get_redis()
        if redis_client:
            try:
                redis_client.setex(key, ttl, serialized)
                return
            except Exception:
                pass
        
        # Fallback to local cache
        with self._lock:
            # Evict if needed
            if len(self._local_cache) >= self.local_cache_size:
                oldest_key = min(self._timestamps.keys(), key=self._timestamps.get)
                del self._local_cache[oldest_key]
                del self._timestamps[oldest_key]
            
            self._local_cache[key] = value
            self._timestamps[key] = time.time()
    
    def clear(self) -> None:
        """Clear all cache"""
        with self._lock:
            self._local_cache.clear()
            self._timestamps.clear()
        
        redis_client = self._get_redis()
        if redis_client:
            try:
                redis_client.flushdb()
            except Exception:
                pass

# Global cache instance
_cache: Optional[UnifiedCache] = None

def get_cache() -> UnifiedCache:
    """Get global cache instance"""
    global _cache
    if _cache is None:
        from app.core.config import get_settings
        settings = get_settings()
        _cache = UnifiedCache(
            redis_url=getattr(settings, 'redis_url', None),
            local_cache_size=1000
        )
    return _cache
