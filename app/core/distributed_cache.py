"""
Advanced Distributed Cache Manager for Asmblr
Multi-layer caching with intelligent eviction and distribution
"""

import asyncio
import time
import json
import hashlib
import pickle
import zlib
import gzip
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import OrderedDict, defaultdict
import redis.asyncio as redis
import aioredis
from loguru import logger
import psutil

class CacheLevel(Enum):
    """Cache levels"""
    L1_MEMORY = "l1_memory"
    L2_REDIS = "l2_redis"
    L3_DISTRIBUTED = "l3_distributed"

class EvictionPolicy(Enum):
    """Cache eviction policies"""
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    RANDOM = "random"
    SIZE_BASED = "size_based"

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    size_bytes: int = 0
    ttl_seconds: Optional[float] = None
    expires_at: Optional[datetime] = None
    level: CacheLevel = CacheLevel.L1_MEMORY
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.ttl_seconds:
            self.expires_at = self.created_at + timedelta(seconds=self.ttl_seconds)
        
        # Calculate size if not provided
        if self.size_bytes == 0:
            self.size_bytes = len(pickle.dumps(self.value))
    
    @property
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False
    
    @property
    def age_seconds(self) -> float:
        """Get age in seconds"""
        return (datetime.now() - self.created_at).total_seconds()

@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    evictions: int = 0
    total_size_bytes: int = 0
    hit_rate: float = 0.0
    avg_response_time: float = 0.0
    memory_usage: float = 0.0
    redis_usage: float = 0.0
    compression_ratio: float = 0.0
    
    @property
    def miss_rate(self) -> float:
        """Calculate miss rate"""
        if self.total_requests == 0:
            return 0.0
        return self.cache_misses / self.total_requests

class AdvancedDistributedCache:
    """Advanced distributed cache with multi-layer architecture"""
    
    def __init__(self, max_memory_size: int = 100 * 1024 * 1024):  # 100MB
        self.max_memory_size = max_memory_size
        self.eviction_policy = EvictionPolicy.LRU
        
        # Multi-layer cache
        self.l1_cache = OrderedDict()  # Memory cache
        self.l2_cache = None  # Redis cache
        self.l3_cache = None  # Distributed cache
        
        # Cache configuration
        self.compression_enabled = True
        self.compression_threshold = 1024  # Compress items > 1KB
        self.default_ttl = 3600  # 1 hour
        self.max_ttl = 86400  # 24 hours
        self.cleanup_interval = 300  # 5 minutes
        
        # Performance tracking
        self.metrics = CacheMetrics()
        self.response_times = []
        self.access_patterns = defaultdict(int)
        
        # Redis connection
        self.redis_client = None
        self.redis_enabled = False
        
        # Background tasks
        self.cleanup_task = None
        self.metrics_task = None
        
        # Cache warming
        self.warmup_enabled = True
        self.warmup_keys = set()
        
        # Intelligent features
        self.predictive_prefetch = True
        self.access_pattern_analysis = True
        self.auto_tuning = True
        
    async def initialize(self):
        """Initialize the distributed cache"""
        try:
            # Initialize Redis connection
            try:
                self.redis_client = aioredis.from_url(
                    "redis://localhost:6379/3",
                    max_connections=20,
                    retry_on_timeout=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
                await self.redis_client.ping()
                self.redis_enabled = True
                logger.info("Redis connection established for L2 cache")
            except Exception as e:
                logger.warning(f"Redis not available, using L1 cache only: {e}")
            
            # Start background tasks
            await self.start_cleanup_task()
            await self.start_metrics_task()
            
            logger.info(f"Distributed cache initialized with {self.max_memory_size} bytes memory limit")
            
        except Exception as e:
            logger.error(f"Failed to initialize distributed cache: {e}")
            raise
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache (multi-layer lookup)"""
        start_time = time.time()
        
        try:
            self.metrics.total_requests += 1
            self.access_patterns[key] += 1
            
            # L1 Memory cache lookup
            if key in self.l1_cache:
                entry = self.l1_cache[key]
                
                if not entry.is_expired:
                    # Update access metadata
                    entry.last_accessed = datetime.now()
                    entry.access_count += 1
                    
                    # Move to end (LRU)
                    self.l1_cache.move_to_end(key)
                    
                    self.metrics.cache_hits += 1
                    self.metrics.hit_rate = self.metrics.cache_hits / self.metrics.total_requests
                    
                    # Update response time
                    response_time = time.time() - start_time
                    self.response_times.append(response_time)
                    if len(self.response_times) > 1000:
                        self.response_times = self.response_times[-1000:]
                    self.metrics.avg_response_time = sum(self.response_times) / len(self.response_times)
                    
                    return entry.value
                else:
                    # Expired, remove from cache
                    del self.l1_cache[key]
            
            # L2 Redis cache lookup
            if self.redis_enabled:
                try:
                    cached_data = await self.redis_client.get(f"cache:{key}")
                    if cached_data:
                        entry = pickle.loads(cached_data)
                        
                        if not entry.is_expired:
                            # Store in L1 cache
                            await self._store_l1(entry)
                            
                            self.metrics.cache_hits += 1
                            self.metrics.hit_rate = self.metrics.cache_hits / self.metrics.total_requests
                            
                            return entry.value
                except Exception as e:
                    logger.error(f"Redis cache lookup error: {e}")
            
            # Cache miss
            self.metrics.cache_misses += 1
            self.metrics.hit_rate = self.metrics.cache_hits / self.metrics.total_requests
            
            # Predictive prefetch if enabled
            if self.predictive_prefetch:
                await self._predictive_prefetch(key)
            
            return default
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return default
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        level: Optional[CacheLevel] = None
    ) -> bool:
        """Set value in cache"""
        try:
            # Validate TTL
            if ttl_seconds and (ttl_seconds < 0 or ttl_seconds > self.max_ttl):
                ttl_seconds = self.default_ttl
            
            if not ttl_seconds:
                ttl_seconds = self.default_ttl
            
            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                ttl_seconds=ttl_seconds,
                metadata=metadata,
                level=level or CacheLevel.L1_MEMORY
            )
            
            # Compress if needed
            if self.compression_enabled and entry.size_bytes > self.compression_threshold:
                original_value = entry.value
                entry.value = self._compress_data(original_value)
                entry.size_bytes = len(pickle.dumps(entry.value))
                entry.metadata = entry.metadata or {}
                entry.metadata['compressed'] = True
                entry.metadata['original_size'] = len(pickle.dumps(original_value))
            
            # Store in appropriate level
            if level == CacheLevel.L1_MEMORY or level is None:
                await self._store_l1(entry)
            elif level == CacheLevel.L2_REDIS and self.redis_enabled:
                await self._store_l2(entry)
            elif level == CacheLevel.L3_DISTRIBUTED:
                await self._store_l3(entry)
            
            # Update metrics
            self.metrics.total_size_bytes += entry.size_bytes
            
            # Update memory usage
            self.metrics.memory_usage = psutil.virtual_memory().percent
            
            # Update Redis usage if available
            if self.redis_enabled:
                try:
                    info = await self.redis_client.info()
                    self.metrics.redis_usage = float(info.get('used_memory_human', '0B').replace('B', '')) / float(info.get('maxmemory_human', '1B').replace('B', ''))
                except:
                    pass
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            deleted = False
            
            # Delete from L1
            if key in self.l1_cache:
                entry = self.l1_cache[key]
                self.metrics.total_size_bytes -= entry.size_bytes
                del self.l1_cache[key]
                deleted = True
            
            # Delete from L2
            if self.redis_enabled:
                try:
                    result = await self.redis_client.delete(f"cache:{key}")
                    if result:
                        deleted = True
                except Exception as e:
                    logger.error(f"Redis delete error: {e}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries"""
        try:
            cleared_count = 0
            
            if pattern:
                # Clear matching keys
                keys_to_delete = [k for k in self.l1_cache.keys() if pattern in k]
                for key in keys_to_delete:
                    if await self.delete(key):
                        cleared_count += 1
            else:
                # Clear all
                cleared_count = len(self.l1_cache)
                self.l1_cache.clear()
                self.metrics.total_size_bytes = 0
                
                if self.redis_enabled:
                    try:
                        # Clear all Redis cache keys
                        keys = await self.redis_client.keys("cache:*")
                        if keys:
                            cleared_count += await self.redis_client.delete(*keys)
                    except Exception as e:
                        logger.error(f"Redis clear error: {e}")
            
            logger.info(f"Cleared {cleared_count} cache entries")
            return cleared_count
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0
    
    async def _store_l1(self, entry: CacheEntry):
        """Store in L1 memory cache"""
        # Check memory limit
        while len(self.l1_cache) > 0 and self._should_evict():
            await self._evict_lru()
        
        self.l1_cache[entry.key] = entry
    
    async def _store_l2(self, entry: CacheEntry):
        """Store in L2 Redis cache"""
        try:
            serialized = pickle.dumps(entry)
            await self.redis_client.setex(
                f"cache:{entry.key}",
                int(entry.ttl_seconds or self.default_ttl),
                serialized
            )
        except Exception as e:
            logger.error(f"L2 cache store error: {e}")
    
    async def _store_l3(self, entry: CacheEntry):
        """Store in L3 distributed cache"""
        # Placeholder for distributed cache implementation
        # This could integrate with other distributed cache systems
        logger.debug(f"L3 cache store not implemented for key {entry.key}")
    
    def _should_evict(self) -> bool:
        """Check if eviction is needed"""
        return self.metrics.total_size_bytes > self.max_memory_size
    
    async def _evict_lru(self):
        """Evict least recently used entry"""
        if self.l1_cache:
            key, entry = self.l1_cache.popitem(last=False)
            self.metrics.total_size_bytes -= entry.size_bytes
            self.metrics.evictions += 1
            logger.debug(f"Evicted LRU cache entry: {key}")
    
    def _compress_data(self, data: Any) -> bytes:
        """Compress data"""
        try:
            return gzip.compress(pickle.dumps(data))
        except Exception as e:
            logger.error(f"Compression error: {e}")
            return pickle.dumps(data)
    
    def _decompress_data(self, compressed_data: bytes) -> Any:
        """Decompress data"""
        try:
            return pickle.loads(gzip.decompress(compressed_data))
        except Exception as e:
            logger.error(f"Decompression error: {e}")
            return pickle.loads(compressed_data)
    
    async def _predictive_prefetch(self, key: str):
        """Predictive prefetch based on access patterns"""
        try:
            # Analyze access patterns
            if len(self.access_patterns[key]) < 3:
                return
            
            # Find related keys (simple heuristic)
            key_parts = key.split(':')
            if len(key_parts) < 2:
                return
            
            prefix = ':'.join(key_parts[:-1])
            related_keys = [k for k in self.access_patterns.keys() if k.startswith(prefix) and k != key]
            
            # Sort by access frequency
            related_keys.sort(key=lambda k: self.access_patterns[k], reverse=True)
            
            # Prefetch top related keys
            for related_key in related_keys[:3]:
                if related_key not in self.l1_cache:
                    # This is a simplified prefetch - in practice, you'd want more sophisticated logic
                    logger.debug(f"Predictive prefetch triggered for {related_key}")
                    break
            
        except Exception as e:
            logger.error(f"Predictive prefetch error: {e}")
    
    async def start_cleanup_task(self):
        """Start background cleanup task"""
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("Cache cleanup task started")
    
    async def stop_cleanup_task(self):
        """Stop background cleanup task"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Cache cleanup task stopped")
    
    async def _cleanup_loop(self):
        """Background cleanup loop"""
        while True:
            try:
                await self._cleanup_expired_entries()
                await self._optimize_cache_size()
                await asyncio.sleep(self.cleanup_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache cleanup error: {e}")
                await asyncio.sleep(self.cleanup_interval)
    
    async def _cleanup_expired_entries(self):
        """Clean up expired entries"""
        expired_keys = []
        
        for key, entry in self.l1_cache.items():
            if entry.is_expired:
                expired_keys.append(key)
        
        for key in expired_keys:
            await self.delete(key)
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    async def _optimize_cache_size(self):
        """Optimize cache size based on usage patterns"""
        try:
            if self.auto_tuning:
                # Analyze access patterns and adjust cache size
                memory_usage = psutil.virtual_memory().percent
                
                if memory_usage > 80:
                    # High memory usage, reduce cache size
                    target_size = int(self.max_memory_size * 0.8)
                    await self._resize_cache(target_size)
                elif memory_usage < 50 and len(self.l1_cache) < self.max_memory_size * 0.5:
                    # Low memory usage, can increase cache size
                    target_size = int(self.max_memory_size * 1.2)
                    await self._resize_cache(target_size)
        
        except Exception as e:
            logger.error(f"Cache optimization error: {e}")
    
    async def _resize_cache(self, target_size: int):
        """Resize cache to target size"""
        current_size = len(self.l1_cache)
        
        if current_size > target_size:
            # Evict entries to reduce size
            while len(self.l1_cache) > target_size:
                await self._evict_lru()
    
    async def start_metrics_task(self):
        """Start metrics collection task"""
        self.metrics_task = asyncio.create_task(self._metrics_loop())
        logger.info("Cache metrics task started")
    
    async def stop_metrics_task(self):
        """Stop metrics collection task"""
        if self.metrics_task:
            self.metrics_task.cancel()
            try:
                await self.metrics_task
            except asyncio.CancelledError:
                pass
        logger.info("Cache metrics task stopped")
    
    async def _metrics_loop(self):
        """Background metrics collection loop"""
        while True:
            try:
                # Update system metrics
                self.metrics.memory_usage = psutil.virtual_memory().percent
                
                if self.redis_enabled:
                    try:
                        info = await self.redis_client.info()
                        self.metrics.redis_usage = float(info.get('used_memory_human', '0B').replace('B', '')) / float(info.get('maxmemory_human', '1B').replace('B', ''))
                    except:
                        pass
                
                # Calculate compression ratio
                if self.metrics.total_size_bytes > 0:
                    original_size = sum(
                        entry.metadata.get('original_size', entry.size_bytes)
                        for entry in self.l1_cache.values()
                        if entry.metadata and entry.metadata.get('compressed')
                    )
                    if original_size > 0:
                        self.metrics.compression_ratio = original_size / self.metrics.total_size_bytes
                
                await asyncio.sleep(60)  # Update every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(60)
    
    async def warmup_cache(self, keys: List[str], values: List[Any]):
        """Warm up cache with common keys"""
        try:
            logger.info(f"Warming up cache with {len(keys)} keys")
            
            for key, value in zip(keys, values):
                await self.set(key, value, ttl_seconds=3600)  # 1 hour TTL
                self.warmup_keys.add(key)
            
            logger.info(f"Cache warmup completed with {len(keys)} keys")
            
        except Exception as e:
            logger.error(f"Cache warmup error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'total_requests': self.metrics.total_requests,
            'cache_hits': self.metrics.cache_hits,
            'cache_misses': self.metrics.cache_misses,
            'hit_rate': self.metrics.hit_rate,
            'miss_rate': self.metrics.miss_rate,
            'total_size_bytes': self.metrics.total_size_bytes,
            'memory_usage': self.metrics.memory_usage,
            'redis_usage': self.metrics.redis_usage,
            'compression_ratio': self.metrics.compression_ratio,
            'avg_response_time': self.metrics.avg_response_time,
            'l1_cache_size': len(self.l1_cache),
            'redis_enabled': self.redis_enabled,
            'compression_enabled': self.compression_enabled,
            'warmup_keys': len(self.warmup_keys)
        }
    
    async def shutdown(self):
        """Shutdown the cache manager"""
        logger.info("Shutting down distributed cache...")
        
        # Stop background tasks
        await self.stop_cleanup_task()
        await self.stop_metrics_task()
        
        # Clear cache
        await self.clear()
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Distributed cache shutdown complete")

# Global distributed cache instance
distributed_cache = AdvancedDistributedCache()
