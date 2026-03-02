"""
Cache système d'Asmblr - Version corrigée
Corrections des TODO et gestion d'erreurs unifiée
"""

import json
import time
from typing import Any
from dataclasses import dataclass

from app.core.error_handler_v2 import get_error_handler, handle_errors
from app.core.smart_logger import get_smart_logger, LogCategory


@dataclass
class CacheEntry:
    """Entrée de cache avec métadonnées"""
    data: Any
    timestamp: float
    access_count: int
    size_bytes: int


class CacheManagerFixed:
    """
    Gestionnaire de cache corrigé
    Résout les TODO et utilise la gestion d'erreurs unifiée
    """
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: dict[str, CacheEntry] = {}
        self.error_handler = get_error_handler()
        self.smart_logger = get_smart_logger()
        
        # Statistiques
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "errors": 0
        }
    
    @handle_errors("cache_get", reraise=False)
    def get(self, key: str) -> Any | None:
        """
        Récupère une valeur du cache avec gestion d'erreurs
        
        Args:
            key: Clé à récupérer
            
        Returns:
            Valeur en cache ou None
        """
        try:
            if key not in self.cache:
                self.stats["misses"] += 1
                self.smart_logger.debug(
                    LogCategory.SYSTEM,
                    "cache_miss",
                    f"Cache miss for key: {key[:50]}..."
                )
                return None
            
            entry = self.cache[key]
            
            # Vérifier l'expiration
            if self._is_expired(entry):
                self._remove_entry(key)
                self.stats["misses"] += 1
                self.smart_logger.debug(
                    LogCategory.SYSTEM,
                    "cache_expired",
                    f"Cache entry expired for key: {key[:50]}..."
                )
                return None
            
            # Mettre à jour l'accès
            entry.access_count += 1
            self.stats["hits"] += 1
            
            self.smart_logger.debug(
                LogCategory.SYSTEM,
                "cache_hit",
                f"Cache hit for key: {key[:50]}... (accesses: {entry.access_count})"
            )
            
            return entry.data
            
        except Exception as e:
            self.stats["errors"] += 1
            self.error_handler.handle_exception(e, "cache_get")
            return None
    
    @handle_errors("cache_set", reraise=False)
    def set(self, key: str, value: Any) -> bool:
        """
        Stocke une valeur dans le cache avec gestion d'erreurs
        
        Args:
            key: Clé de stockage
            value: Valeur à stocker
            
        Returns:
            True si succès, False sinon
        """
        try:
            # Calculer la taille (approximation)
            size_bytes = len(str(value).encode('utf-8'))
            
            # Vérifier si on doit faire de la place
            if len(self.cache) >= self.max_size:
                self._evict_if_needed()
            
            # Créer l'entrée
            entry = CacheEntry(
                data=value,
                timestamp=time.time(),
                access_count=1,
                size_bytes=size_bytes
            )
            
            self.cache[key] = entry
            
            self.smart_logger.debug(
                LogCategory.SYSTEM,
                "cache_set",
                f"Cached key: {key[:50]}... (size: {size_bytes} bytes)"
            )
            
            return True
            
        except Exception as e:
            self.stats["errors"] += 1
            self.error_handler.handle_exception(e, "cache_set")
            return False
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Vérifie si une entrée est expirée"""
        return time.time() - entry.timestamp > self.ttl_seconds
    
    def _remove_entry(self, key: str) -> None:
        """Supprime une entrée du cache"""
        if key in self.cache:
            del self.cache[key]
            self.smart_logger.debug(
                LogCategory.SYSTEM,
                "cache_remove",
                f"Removed cache entry: {key[:50]}..."
            )
    
    def _evict_if_needed(self) -> None:
        """
        Évince les entrées si nécessaire
        Version corrigée du TODO avec logging intelligent
        """
        if len(self.cache) < self.max_size:
            return
        
        # Trier par LRU (least recently used)
        sorted_entries = sorted(
            self.cache.items(),
            key=lambda item: (item[1].timestamp, item[1].access_count)
        )
        
        # Évinter les entrées les plus anciennes
        evicted_count = 0
        while len(self.cache) >= self.max_size * 0.8 and sorted_entries:  # Garder 20% de place
            key, entry = sorted_entries.pop(0)
            if key in self.cache:
                del self.cache[key]
                evicted_count += 1
                self.stats["evictions"] += 1
        
        if evicted_count > 0:
            self.smart_logger.info(
                LogCategory.SYSTEM,
                "cache_eviction",
                f"Evicted {evicted_count} cache entries (LRU strategy)",
                metadata={
                    "evicted_count": evicted_count,
                    "remaining_entries": len(self.cache),
                    "max_size": self.max_size
                }
            )
    
    def clear(self) -> bool:
        """
        Vide le cache avec gestion d'erreurs
        
        Returns:
            True si succès, False sinon
        """
        try:
            cache_size = len(self.cache)
            self.cache.clear()
            
            # Réinitialiser les statistiques
            self.stats = {
                "hits": 0,
                "misses": 0,
                "evictions": 0,
                "errors": 0
            }
            
            self.smart_logger.info(
                LogCategory.SYSTEM,
                "cache_clear",
                f"Cache cleared ({cache_size} entries removed)"
            )
            
            return True
            
        except Exception as e:
            self.error_handler.handle_exception(e, "cache_clear")
            return False
    
    def get_stats(self) -> dict[str, Any]:
        """
        Retourne les statistiques du cache
        
        Returns:
            Dictionnaire de statistiques
        """
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0
        
        return {
            "entries_count": len(self.cache),
            "max_size": self.max_size,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "evictions": self.stats["evictions"],
            "errors": self.stats["errors"],
            "hit_rate": hit_rate,
            "ttl_seconds": self.ttl_seconds,
            "memory_usage_mb": self._estimate_memory_usage()
        }
    
    def _estimate_memory_usage(self) -> float:
        """Estime l'utilisation mémoire en MB"""
        try:
            import sys
            
            total_size = 0
            for key, entry in self.cache.items():
                total_size += (
                    sys.getsizeof(key) +
                    sys.getsizeof(entry.data) +
                    sys.getsizeof(entry.timestamp) +
                    sys.getsizeof(entry.access_count) +
                    sys.getsizeof(entry.size_bytes)
                )
            
            return total_size / (1024 * 1024)  # Convertir en MB
            
        except Exception:
            return 0.0
    
    def cleanup_expired(self) -> int:
        """
        Nettoie les entrées expirées
        
        Returns:
            Nombre d'entrées supprimées
        """
        try:
            expired_keys = [
                key for key, entry in self.cache.items()
                if self._is_expired(entry)
            ]
            
            for key in expired_keys:
                self._remove_entry(key)
            
            if expired_keys:
                self.smart_logger.info(
                    LogCategory.SYSTEM,
                    "cache_cleanup",
                    f"Cleaned up {len(expired_keys)} expired entries",
                    metadata={"expired_keys": len(expired_keys)}
                )
            
            return len(expired_keys)
            
        except Exception as e:
            self.error_handler.handle_exception(e, "cache_cleanup")
            return 0
    
    def export_cache(self, format_type: str = "json") -> str:
        """
        Exporte le contenu du cache
        
        Args:
            format_type: Format d'export (json, csv)
            
        Returns:
            Contenu exporté
        """
        try:
            if format_type == "json":
                export_data = {
                    "metadata": self.get_stats(),
                    "entries": {
                        key: {
                            "data": entry.data,
                            "timestamp": entry.timestamp,
                            "access_count": entry.access_count,
                            "size_bytes": entry.size_bytes
                        }
                        for key, entry in self.cache.items()
                    }
                }
                return json.dumps(export_data, indent=2, default=str)
            
            else:
                raise ValueError(f"Format non supporté: {format_type}")
                
        except Exception as e:
            self.error_handler.handle_exception(e, "cache_export")
            return ""


# Instance globale du cache corrigé
_cache_manager_fixed: CacheManagerFixed | None = None


def get_cache_manager_fixed(max_size: int = 1000, ttl_seconds: int = 3600) -> CacheManagerFixed:
    """
    Récupère l'instance globale du cache corrigé
    
    Args:
        max_size: Taille maximale du cache
        ttl_seconds: Durée de vie en secondes
        
    Returns:
        Instance du gestionnaire de cache
    """
    global _cache_manager_fixed
    if _cache_manager_fixed is None:
        _cache_manager_fixed = CacheManagerFixed(max_size, ttl_seconds)
    return _cache_manager_fixed


# Fonctions pratiques pour le cache corrigé
def cache_get(key: str, default: Any = None) -> Any:
    """
    Récupère une valeur du cache avec valeur par défaut
    
    Args:
        key: Clé à récupérer
        default: Valeur par défaut
        
    Returns:
        Valeur en cache ou valeur par défaut
    """
    cache = get_cache_manager_fixed()
    result = cache.get(key)
    return result if result is not None else default


def cache_set(key: str, value: Any) -> bool:
    """
    Stocke une valeur dans le cache
    
    Args:
        key: Clé de stockage
        value: Valeur à stocker
        
    Returns:
        True si succès, False sinon
    """
    cache = get_cache_manager_fixed()
    return cache.set(key, value)


def cache_clear() -> bool:
    """
    Vide le cache
    
    Returns:
        True si succès, False sinon
    """
    cache = get_cache_manager_fixed()
    return cache.clear()


def cache_stats() -> dict[str, Any]:
    """
    Retourne les statistiques du cache
    
    Returns:
        Dictionnaire de statistiques
    """
    cache = get_cache_manager_fixed()
    return cache.get_stats()
