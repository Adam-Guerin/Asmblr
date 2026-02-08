"""File caching system for frequently accessed artifacts.

This module provides a centralized cache for JSON artifacts that are
read multiple times during pipeline execution, reducing I/O overhead and improving performance.
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional, Union
import json
import threading
import time
import hashlib
import logging


logger = logging.getLogger(__name__)


class ArtifactCache:
    """Thread-safe cache for JSON artifacts with TTL support."""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        """Initialize the artifact cache.
        
        Args:
            max_size: Maximum number of cached items
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, float] = {}
        self._lock = threading.RLock()
    
    def _is_expired(self, key: str) -> bool:
        """Check if a cache entry has expired."""
        if key not in self._timestamps:
            return True
        age = time.time() - self._timestamps[key]
        return age > self.ttl_seconds
    
    def _evict_if_needed(self) -> None:
        """Evict expired entries if cache is full."""
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in self._timestamps.items()
            if current_time - timestamp > self.ttl_seconds
        ]
        
        for key in expired_keys:
            del self._cache[key]
            del self._timestamps[key]
            logger.debug(f"Evicted expired cache entry: {key}")
        
        # Evict oldest entries if cache is full
        if len(self._cache) >= self.max_size:
            # Sort by timestamp (oldest first)
            sorted_items = sorted(
                self._timestamps.items(),
                key=lambda item: item[1],
                reverse=True
            )
            
            # Remove oldest entries
            while len(self._cache) >= self.max_size and sorted_items:
                key, _ = sorted_items.pop()
                del self._cache[key]
                del self._timestamps[key]
                logger.debug(f"Evicted old cache entry: {key}")
    
    def get(self, key: str) -> Any:
        """Get cached artifact by key."""
        self._evict_if_needed()
        
        if key in self._cache:
            # Update access time for LRU
            self._timestamps[key] = time.time()
            logger.debug(f"Cache hit: {key}")
            return self._cache[key]
        
        logger.debug(f"Cache miss: {key}")
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Cache an artifact with automatic eviction."""
        self._evict_if_needed()
        
        # Add new entry
        self._cache[key] = value
        self._timestamps[key] = time.time()
        
        logger.debug(f"Cached artifact: {key} (size: {len(self._cache)})")
    
    def clear(self) -> None:
        """Clear all cached artifacts."""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            logger.debug("Cleared artifact cache")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            "keys": list(self._cache.keys()),
        }


class CachedArtifactLoader:
    """Utility class for loading artifacts with caching support."""
    
    def __init__(self, cache: ArtifactCache, file_path: Path):
        """Initialize with cache instance and file path."""
        self.cache = cache
        self.file_path = file_path
    
    def load_json(self, run_id: str, artifact_name: str) -> Any:
        """Load JSON artifact with caching."""
        cache_key = f"{run_id}:{artifact_name}"
        
        # Try cache first
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Load from disk with caching
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.cache.set(cache_key, data)
                logger.debug(f"Cached artifact: {artifact_name}")
                return data
        except Exception as e:
            logger.error(f"Failed to load artifact {artifact_name}: {e}")
            return None
    
    def load_text(self, run_id: str, artifact_name: str) -> str:
        """Load text artifact with caching."""
        cache_key = f"{run_id}:{artifact_name}"
        
        # Try cache first
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Load from disk with caching
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = f.read()
                self.cache.set(cache_key, data)
                logger.debug(f"Cached text artifact: {artifact_name}")
                return data
        except Exception as e:
            logger.error(f"Failed to load artifact {artifact_name}: {e}")
            return None
    
    def invalidate(self, run_id: str, artifact_name: str) -> None:
        """Invalidate cached artifact."""
        cache_key = f"{run_id}:{artifact_name}"
        if cache_key in self.cache._cache:
            del self.cache._cache[cache_key]
            del self.cache._timestamps[cache_key]
            logger.debug(f"Invalidated cached artifact: {artifact_name}")


# Global cache instance for frequently accessed artifacts
_artifact_cache = ArtifactCache(max_size=50, ttl_seconds=300)  # Cache 50 items for 5 minutes
_cached_loader = CachedArtifactLoader(_artifact_cache, Path("data") / "artifact_cache.json")


def get_cached_artifact_loader() -> CachedArtifactLoader:
    """Get the global cached artifact loader."""
    return _cached_loader


def load_cached_json(run_id: str, artifact_name: str) -> Any:
    """Load JSON artifact using global cache."""
    return _cached_loader.load_json(run_id, artifact_name)


def load_cached_text(run_id: str, artifact_name: str) -> str:
    """Load text artifact using global cache."""
    return _cached_loader.load_text(run_id, artifact_name)


def invalidate_cached_artifact(run_id: str, artifact_name: str) -> None:
    """Invalidate cached artifact."""
    _cached_loader.invalidate(run_id, artifact_name)


def clear_artifact_cache() -> None:
    """Clear the global artifact cache."""
    _artifact_cache.clear()
