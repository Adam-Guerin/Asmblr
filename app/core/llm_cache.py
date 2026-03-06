"""
Intelligent LLM Response Caching for Asmblr
Reduces API calls and improves response times for similar prompts
"""

import hashlib
import json
import time
import asyncio
from typing import Any
from dataclasses import dataclass, asdict
import redis.asyncio as redis
from loguru import logger

from app.core.config import get_settings


@dataclass
class CacheEntry:
    """Cache entry for LLM responses"""
    prompt_hash: str
    response: str
    model: str
    timestamp: float
    ttl: int
    hit_count: int = 0
    similarity_score: float = 1.0
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'CacheEntry':
        return cls(**data)


class LLMCacheManager:
    """Intelligent caching system for LLM responses"""
    
    def __init__(self):
        settings = get_settings()
        self.redis_url = settings.redis_url
        self.default_ttl = 3600  # 1 hour
        self.max_cache_size = 10000
        self.similarity_threshold = 0.85
        self._redis_client: redis.Redis | None = None
        self._local_cache: dict[str, CacheEntry] = {}
        self._local_cache_size = 1000
        self._lock = asyncio.Lock()
        
    async def _get_redis_client(self) -> redis.Redis:
        """Get or create Redis client"""
        if self._redis_client is None:
            self._redis_client = redis.from_url(self.redis_url)
        return self._redis_client
    
    def _generate_prompt_hash(self, prompt: str, model: str, **kwargs) -> str:
        """Generate hash for prompt and parameters"""
        # Create a deterministic string from prompt and parameters
        cache_data = {
            "prompt": prompt.strip().lower(),
            "model": model,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2000),
            "top_p": kwargs.get("top_p", 0.9)
        }
        
        # Sort keys for deterministic hashing
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()  # Use full hash to prevent collisions
    
    def _calculate_similarity(self, prompt1: str, prompt2: str) -> float:
        """Calculate semantic similarity between prompts (simplified)"""
        # Simple word overlap similarity (can be enhanced with embeddings)
        words1 = set(prompt1.lower().split())
        words2 = set(prompt2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    async def get(self, prompt: str, model: str, **kwargs) -> str | None:
        """Get cached response for prompt"""
        try:
            # Try exact match first
            exact_hash = self._generate_prompt_hash(prompt, model, **kwargs)
            
            async with self._lock:
                # Check local cache first (thread-safe)
                if exact_hash in self._local_cache:
                    entry = self._local_cache[exact_hash]
                    if time.time() - entry.timestamp < entry.ttl:
                        entry.hit_count += 1  # Atomic update
                        logger.debug(f"Cache hit (local): {exact_hash[:8]}")
                        return entry.response
                    else:
                        # Remove expired entry
                        del self._local_cache[exact_hash]
            
            # Check Redis cache
            redis_client = await self._get_redis_client()
            cached_data = await redis_client.get(f"llm_cache:{exact_hash}")
            
            if cached_data:
                entry = CacheEntry.from_dict(json.loads(cached_data))
                if time.time() - entry.timestamp < entry.ttl:
                    entry.hit_count += 1
                    # Store in local cache for faster access
                    self._local_cache[exact_hash] = entry
                    await redis_client.setex(
                        f"llm_cache:{exact_hash}", 
                        entry.ttl, 
                        json.dumps(entry.to_dict())
                    )
                    logger.debug(f"Cache hit (redis): {exact_hash[:8]}")
                    return entry.response
                else:
                    # Remove expired entry
                    await redis_client.delete(f"llm_cache:{exact_hash}")
            
            # Try similarity search for near matches
            similar_response = await self._get_similar_response(prompt, model, **kwargs)
            if similar_response:
                return similar_response
            
            logger.debug(f"Cache miss: {exact_hash[:8]}")
            return None
            
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    async def _get_similar_response(self, prompt: str, model: str, **kwargs) -> str | None:
        """Find similar cached responses"""
        try:
            redis_client = await self._get_redis_client()
            
            # Get all cache keys for this model
            pattern = f"llm_cache:*"
            keys = await redis_client.keys(pattern)
            
            best_match = None
            best_similarity = 0.0
            
            for key in keys:
                try:
                    cached_data = await redis_client.get(key)
                    if not cached_data:
                        continue
                    
                    entry = CacheEntry.from_dict(json.loads(cached_data))
                    if entry.model != model:
                        continue
                    
                    # Calculate similarity
                    similarity = self._calculate_similarity(prompt, entry.prompt_hash)
                    
                    if similarity > best_similarity and similarity >= self.similarity_threshold:
                        best_similarity = similarity
                        best_match = entry.response
                        
                except Exception:
                    continue
            
            if best_match:
                logger.debug(f"Similar cache hit: similarity={best_similarity:.2f}")
                return best_match
            
            return None
            
        except Exception as e:
            logger.warning(f"Similarity search error: {e}")
            return None
    
    async def set(self, prompt: str, response: str, model: str, ttl: int | None = None, **kwargs) -> None:
        """Cache response for prompt"""
        try:
            if ttl is None:
                ttl = self.default_ttl
            
            prompt_hash = self._generate_prompt_hash(prompt, model, **kwargs)
            
            entry = CacheEntry(
                prompt_hash=prompt_hash,
                response=response,
                model=model,
                timestamp=time.time(),
                ttl=ttl,
                metadata=kwargs.get("metadata")
            )
            
            # Store in local cache
            self._local_cache[prompt_hash] = entry
            
            # Store in Redis
            redis_client = await self._get_redis_client()
            await redis_client.setex(
                f"llm_cache:{prompt_hash}", 
                ttl, 
                json.dumps(entry.to_dict())
            )
            
            logger.debug(f"Cached response: {prompt_hash[:8]}")
            
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
    
    def get_sync(self, prompt: str, model: str, **kwargs) -> str | None:
        """Synchronous version of get for non-async contexts"""
        try:
            # Try exact match first
            exact_hash = self._generate_prompt_hash(prompt, model, **kwargs)
            
            # Check local cache first
            if exact_hash in self._local_cache:
                entry = self._local_cache[exact_hash]
                if time.time() - entry.timestamp < entry.ttl:
                    entry.hit_count += 1
                    logger.debug(f"Cache hit (local sync): {exact_hash[:8]}")
                    return entry.response
                else:
                    # Remove expired entry
                    del self._local_cache[exact_hash]
            
            logger.debug(f"Cache miss (sync): {exact_hash[:8]}")
            return None
            
        except Exception as e:
            logger.warning(f"Cache get sync error: {e}")
            return None
    
    def set_sync(self, prompt: str, response: str, model: str, ttl: int | None = None, **kwargs) -> None:
        """Synchronous version of set for non-async contexts"""
        try:
            if ttl is None:
                ttl = self.default_ttl
            
            prompt_hash = self._generate_prompt_hash(prompt, model, **kwargs)
            
            entry = CacheEntry(
                prompt_hash=prompt_hash,
                response=response,
                model=model,
                timestamp=time.time(),
                ttl=ttl,
                metadata=kwargs.get("metadata")
            )
            
            # Store in local cache only (Redis requires async)
            self._local_cache[prompt_hash] = entry
            
            logger.debug(f"Cached response (sync): {prompt_hash[:8]}")
            
        except Exception as e:
            logger.warning(f"Cache set sync error: {e}")
            
    async def invalidate(self, prompt: str, model: str, **kwargs) -> bool:
        """Invalidate cached response for prompt"""
        try:
            prompt_hash = self._generate_prompt_hash(prompt, model, **kwargs)
            
            # Remove from local cache
            if prompt_hash in self._local_cache:
                del self._local_cache[prompt_hash]
            
            # Remove from Redis
            redis_client = await self._get_redis_client()
            result = await redis_client.delete(f"llm_cache:{prompt_hash}")
            
            logger.debug(f"Invalidated cache: {prompt_hash[:8]}")
            return result > 0
            
        except Exception as e:
            logger.warning(f"Cache invalidate error: {e}")
            return False
    
    async def clear_model(self, model: str) -> int:
        """Clear all cache entries for a specific model"""
        try:
            redis_client = await self._get_redis_client()
            pattern = f"llm_cache:*"
            keys = await redis_client.keys(pattern)
            
            deleted_count = 0
            for key in keys:
                try:
                    cached_data = await redis_client.get(key)
                    if cached_data:
                        entry = CacheEntry.from_dict(json.loads(cached_data))
                        if entry.model == model:
                            await redis_client.delete(key)
                            deleted_count += 1
                except Exception:
                    continue
            
            # Clear local cache for this model
            keys_to_remove = [
                k for k, v in self._local_cache.items() 
                if v.model == model
            ]
            for key in keys_to_remove:
                del self._local_cache[key]
            
            logger.info(f"Cleared {deleted_count} cache entries for model: {model}")
            return deleted_count
            
        except Exception as e:
            logger.warning(f"Cache clear model error: {e}")
            return 0
    
    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        try:
            redis_client = await self._get_redis_client()
            pattern = f"llm_cache:*"
            keys = await redis_client.keys(pattern)
            
            total_entries = len(keys)
            model_stats = {}
            total_hits = 0
            
            for key in keys:
                try:
                    cached_data = await redis_client.get(key)
                    if cached_data:
                        entry = CacheEntry.from_dict(json.loads(cached_data))
                        
                        if entry.model not in model_stats:
                            model_stats[entry.model] = {
                                "entries": 0,
                                "total_hits": 0,
                                "avg_ttl": 0
                            }
                        
                        model_stats[entry.model]["entries"] += 1
                        model_stats[entry.model]["total_hits"] += entry.hit_count
                        total_hits += entry.hit_count
                        
                except Exception:
                    continue
            
            return {
                "total_entries": total_entries,
                "local_entries": len(self._local_cache),
                "total_hits": total_hits,
                "hit_rate": total_hits / max(total_entries, 1),
                "model_stats": model_stats,
                "similarity_threshold": self.similarity_threshold
            }
            
        except Exception as e:
            logger.warning(f"Cache stats error: {e}")
            return {"error": str(e)}
    
    async def cleanup_expired(self) -> int:
        """Clean up expired cache entries"""
        try:
            redis_client = await self._get_redis_client()
            pattern = f"llm_cache:*"
            keys = await redis_client.keys(pattern)
            
            current_time = time.time()
            deleted_count = 0
            
            for key in keys:
                try:
                    cached_data = await redis_client.get(key)
                    if cached_data:
                        entry = CacheEntry.from_dict(json.loads(cached_data))
                        
                        if current_time - entry.timestamp > entry.ttl:
                            await redis_client.delete(key)
                            deleted_count += 1
                            
                except Exception:
                    continue
            
            # Clean local cache
            expired_keys = [
                k for k, v in self._local_cache.items()
                if current_time - v.timestamp > v.ttl
            ]
            for key in expired_keys:
                del self._local_cache[key]
            
            logger.info(f"Cleaned up {deleted_count} expired cache entries")
            return deleted_count
            
        except Exception as e:
            logger.warning(f"Cache cleanup error: {e}")
            return 0


# Global cache manager instance
cache_manager = LLMCacheManager()


# Decorator for automatic caching
def cached_llm_call(ttl: int = 3600, similarity: bool = True):
    """Decorator to automatically cache LLM function calls"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract prompt and model from args/kwargs
            prompt = kwargs.get("prompt") or (args[0] if args else "")
            model = kwargs.get("model") or (args[1] if len(args) > 1 else "default")
            
            if not prompt:
                return await func(*args, **kwargs)
            
            # Try to get from cache
            cached_response = await cache_manager.get(prompt, model, **kwargs)
            if cached_response:
                return cached_response
            
            # Call the function
            response = await func(*args, **kwargs)
            
            # Cache the response
            await cache_manager.set(prompt, response, model, ttl, **kwargs)
            
            return response
        
        return wrapper
    return decorator
