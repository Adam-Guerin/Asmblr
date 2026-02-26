"""
Tests for LLM Cache functionality
Validates caching, similarity matching, and performance
"""

import pytest
import asyncio
import time
import json
from unittest.mock import AsyncMock, patch
from pathlib import Path

from app.core.llm_cache import LLMCacheManager, CacheEntry, cached_llm_call


class TestLLMCacheManager:
    """Test suite for LLM Cache Manager"""
    
    @pytest.fixture
    async def cache_manager(self):
        """Create cache manager for testing"""
        # Mock Redis for testing
        with patch('app.core.llm_cache.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            manager = LLMCacheManager()
            manager._redis_client = mock_client
            return manager
    
    @pytest.mark.asyncio
    async def test_generate_prompt_hash(self, cache_manager):
        """Test prompt hash generation"""
        prompt = "Generate a business idea for AI startups"
        model = "llama3.1:8b"
        
        hash1 = cache_manager._generate_prompt_hash(prompt, model)
        hash2 = cache_manager._generate_prompt_hash(prompt, model)
        
        # Same prompt should generate same hash
        assert hash1 == hash2
        assert len(hash1) == 16  # SHA256 truncated
        
        # Different model should generate different hash
        hash3 = cache_manager._generate_prompt_hash(prompt, "different-model")
        assert hash1 != hash3
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, cache_manager):
        """Test cache miss scenario"""
        prompt = "Test prompt for cache miss"
        model = "llama3.1:8b"
        
        # Mock Redis to return None (cache miss)
        cache_manager._redis_client.get.return_value = None
        
        result = await cache_manager.get(prompt, model)
        
        assert result is None
        cache_manager._redis_client.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_hit_local(self, cache_manager):
        """Test cache hit from local cache"""
        prompt = "Test prompt for local cache hit"
        model = "llama3.1:8b"
        response = "Cached response"
        
        # Add to local cache
        cache_hash = cache_manager._generate_prompt_hash(prompt, model)
        entry = CacheEntry(
            prompt_hash=cache_hash,
            response=response,
            model=model,
            timestamp=time.time(),
            ttl=3600
        )
        cache_manager._local_cache[cache_hash] = entry
        
        result = await cache_manager.get(prompt, model)
        
        assert result == response
        assert entry.hit_count == 1
    
    @pytest.mark.asyncio
    async def test_cache_hit_redis(self, cache_manager):
        """Test cache hit from Redis"""
        prompt = "Test prompt for Redis cache hit"
        model = "llama3.1:8b"
        response = "Redis cached response"
        
        # Mock Redis response
        cache_hash = cache_manager._generate_prompt_hash(prompt, model)
        entry = CacheEntry(
            prompt_hash=cache_hash,
            response=response,
            model=model,
            timestamp=time.time(),
            ttl=3600
        )
        
        cache_manager._redis_client.get.return_value = json.dumps(entry.to_dict())
        
        result = await cache_manager.get(prompt, model)
        
        assert result == response
        # Should be stored in local cache after Redis hit
        assert cache_hash in cache_manager._local_cache
    
    @pytest.mark.asyncio
    async def test_cache_set(self, cache_manager):
        """Test setting cache entries"""
        prompt = "Test prompt for cache set"
        model = "llama3.1:8b"
        response = "New cached response"
        
        await cache_manager.set(prompt, response, model, ttl=1800)
        
        # Verify Redis set was called
        cache_manager._redis_client.setex.assert_called_once()
        
        # Verify local cache has entry
        cache_hash = cache_manager._generate_prompt_hash(prompt, model)
        assert cache_hash in cache_manager._local_cache
        assert cache_manager._local_cache[cache_hash].response == response
    
    @pytest.mark.asyncio
    async def test_cache_ttl_expiration(self, cache_manager):
        """Test cache TTL expiration"""
        prompt = "Test prompt for TTL expiration"
        model = "llama3.1:8b"
        response = "Expired response"
        
        # Create expired entry
        cache_hash = cache_manager._generate_prompt_hash(prompt, model)
        entry = CacheEntry(
            prompt_hash=cache_hash,
            response=response,
            model=model,
            timestamp=time.time() - 7200,  # 2 hours ago
            ttl=3600  # 1 hour TTL
        )
        cache_manager._local_cache[cache_hash] = entry
        
        result = await cache_manager.get(prompt, model)
        
        assert result is None
        assert cache_hash not in cache_manager._local_cache
    
    @pytest.mark.asyncio
    async def test_similarity_search(self, cache_manager):
        """Test similarity-based cache matching"""
        prompt1 = "Generate business ideas for AI startups"
        prompt2 = "Create business ideas for AI companies"  # Similar
        model = "llama3.1:8b"
        response = "Similar cached response"
        
        # Add similar entry to Redis
        cache_hash = cache_manager._generate_prompt_hash(prompt1, model)
        entry = CacheEntry(
            prompt_hash=cache_hash,
            response=response,
            model=model,
            timestamp=time.time(),
            ttl=3600
        )
        
        # Mock Redis keys and get
        cache_manager._redis_client.keys.return_value = [f"llm_cache:{cache_hash}"]
        cache_manager._redis_client.get.return_value = json.dumps(entry.to_dict())
        
        result = await cache_manager.get(prompt2, model)
        
        # Should find similar response
        assert result == response
    
    def test_calculate_similarity(self, cache_manager):
        """Test similarity calculation"""
        prompt1 = "generate business ideas for AI"
        prompt2 = "create business ideas for AI"
        prompt3 = "completely different topic"
        
        # High similarity
        sim1 = cache_manager._calculate_similarity(prompt1, prompt2)
        assert sim1 > 0.7
        
        # Low similarity
        sim2 = cache_manager._calculate_similarity(prompt1, prompt3)
        assert sim2 < 0.3
        
        # Identical prompts
        sim3 = cache_manager._calculate_similarity(prompt1, prompt1)
        assert sim3 == 1.0
    
    @pytest.mark.asyncio
    async def test_cache_invalidate(self, cache_manager):
        """Test cache invalidation"""
        prompt = "Test prompt for invalidation"
        model = "llama3.1:8b"
        
        # Add to cache
        cache_hash = cache_manager._generate_prompt_hash(prompt, model)
        cache_manager._local_cache[cache_hash] = CacheEntry(
            prompt_hash=cache_hash,
            response="To be invalidated",
            model=model,
            timestamp=time.time(),
            ttl=3600
        )
        
        # Mock Redis delete
        cache_manager._redis_client.delete.return_value = 1
        
        result = await cache_manager.invalidate(prompt, model)
        
        assert result is True
        assert cache_hash not in cache_manager._local_cache
        cache_manager._redis_client.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_clear_model_cache(self, cache_manager):
        """Test clearing cache for specific model"""
        model = "llama3.1:8b"
        
        # Add entries for different models
        for i in range(5):
            prompt = f"Test prompt {i}"
            cache_hash = cache_manager._generate_prompt_hash(prompt, model)
            cache_manager._local_cache[cache_hash] = CacheEntry(
                prompt_hash=cache_hash,
                response=f"Response {i}",
                model=model,
                timestamp=time.time(),
                ttl=3600
            )
        
        # Mock Redis operations
        cache_manager._redis_client.keys.return_value = [f"llm_cache:hash{i}" for i in range(5)]
        cache_manager._redis_client.get.return_value = json.dumps({
            "model": model,
            "response": "test"
        })
        cache_manager._redis_client.delete.return_value = 1
        
        deleted_count = await cache_manager.clear_model(model)
        
        assert deleted_count == 5
        # Local cache should be empty for this model
        for entry in cache_manager._local_cache.values():
            assert entry.model != model
    
    @pytest.mark.asyncio
    async def test_get_stats(self, cache_manager):
        """Test cache statistics"""
        # Mock Redis data
        mock_stats = {
            "total_entries": 100,
            "local_entries": 20,
            "total_hits": 500,
            "hit_rate": 5.0,
            "model_stats": {
                "llama3.1:8b": {
                    "entries": 60,
                    "total_hits": 300,
                    "avg_ttl": 3600
                }
            }
        }
        
        cache_manager._redis_client.keys.return_value = [f"llm_cache:hash{i}" for i in range(100)]
        cache_manager._redis_client.get.return_value = json.dumps({
            "model": "llama3.1:8b",
            "hit_count": 5
        })
        
        stats = await cache_manager.get_stats()
        
        assert "total_entries" in stats
        assert "hit_rate" in stats
        assert "model_stats" in stats


class TestCachedLLMCall:
    """Test suite for cached LLM call decorator"""
    
    @pytest.mark.asyncio
    async def test_cached_llm_call_decorator(self):
        """Test cached LLM call decorator"""
        call_count = 0
        
        @cached_llm_call(ttl=3600)
        async def mock_llm_function(prompt: str, model: str = "test"):
            nonlocal call_count
            call_count += 1
            return f"Response for {prompt}"
        
        # Mock cache manager
        with patch('app.core.llm_cache.cache_manager') as mock_cache:
            mock_cache.get.return_value = None  # Cache miss first time
            mock_cache.set.return_value = None
            
            # First call - cache miss
            result1 = await mock_llm_function("test prompt", model="test-model")
            assert result1 == "Response for test prompt"
            assert call_count == 1
            
            # Verify cache set was called
            mock_cache.set.assert_called_once()
            
            # Reset mock
            mock_cache.get.return_value = "Cached response"
            mock_cache.set.reset_mock()
            
            # Second call - cache hit
            result2 = await mock_llm_function("test prompt", model="test-model")
            assert result2 == "Cached response"
            assert call_count == 1  # Should not increase
            
            # Verify cache set was not called again
            mock_cache.set.assert_not_called()


class TestCachePerformance:
    """Performance tests for LLM cache"""
    
    @pytest.mark.asyncio
    async def test_cache_performance(self):
        """Test cache performance under load"""
        with patch('app.core.llm_cache.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            manager = LLMCacheManager()
            manager._redis_client = mock_client
            
            # Mock cache hits
            mock_client.get.return_value = json.dumps({
                "prompt_hash": "test",
                "response": "cached response",
                "model": "test",
                "timestamp": time.time(),
                "ttl": 3600
            })
            
            # Measure performance
            start_time = time.time()
            
            tasks = []
            for i in range(100):
                task = manager.get(f"test prompt {i}", "test-model")
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # All should return cached response
            assert all(r == "cached response" for r in results)
            
            # Should be fast (under 1 second for 100 cache hits)
            assert duration < 1.0
            
            # Verify Redis was called 100 times
            assert mock_client.get.call_count == 100
    
    @pytest.mark.asyncio
    async def test_local_cache_performance(self):
        """Test local cache performance"""
        manager = LLMCacheManager()
        
        # Pre-populate local cache
        for i in range(1000):
            prompt = f"test prompt {i}"
            cache_hash = manager._generate_prompt_hash(prompt, "test-model")
            manager._local_cache[cache_hash] = CacheEntry(
                prompt_hash=cache_hash,
                response=f"response {i}",
                model="test-model",
                timestamp=time.time(),
                ttl=3600
            )
        
        # Measure local cache performance
        start_time = time.time()
        
        for i in range(1000):
            result = await manager.get(f"test prompt {i}", "test-model")
            assert result == f"response {i}"
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Local cache should be very fast (under 0.1 seconds for 1000 lookups)
        assert duration < 0.1


@pytest.mark.asyncio
async def test_cache_cleanup_expired():
    """Test cleanup of expired cache entries"""
    with patch('app.core.llm_cache.redis.from_url') as mock_redis:
        mock_client = AsyncMock()
        mock_redis.return_value = mock_client
        
        manager = LLMCacheManager()
        manager._redis_client = mock_client
        
        # Add expired entries to local cache
        current_time = time.time()
        for i in range(10):
            cache_hash = f"expired_hash_{i}"
            manager._local_cache[cache_hash] = CacheEntry(
                prompt_hash=cache_hash,
                response=f"expired_response_{i}",
                model="test-model",
                timestamp=current_time - 7200,  # 2 hours ago
                ttl=3600  # 1 hour TTL
            )
        
        # Add non-expired entries
        for i in range(5):
            cache_hash = f"valid_hash_{i}"
            manager._local_cache[cache_hash] = CacheEntry(
                prompt_hash=cache_hash,
                response=f"valid_response_{i}",
                model="test-model",
                timestamp=current_time,
                ttl=3600
            )
        
        # Mock Redis operations
        mock_client.keys.return_value = []
        mock_client.delete.return_value = 1
        
        deleted_count = await manager.cleanup_expired()
        
        # Should delete expired entries only
        assert deleted_count == 10
        assert len(manager._local_cache) == 5
        
        # Verify remaining entries are valid
        for entry in manager._local_cache.values():
            assert current_time - entry.timestamp < entry.ttl
