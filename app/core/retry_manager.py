"""
Gestionnaire centralisé des retries et timeouts
Remplace les 260 occurrences dispersées par un système unifié
"""

import time
import random
import asyncio
from typing import Any, Callable, Optional, Union, Type, TypeVar, Dict
from functools import wraps
from dataclasses import dataclass
from enum import Enum
from loguru import logger

T = TypeVar('T')


class RetryStrategy(Enum):
    """Stratégies de retry disponibles"""
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    FIXED_DELAY = "fixed_delay"
    JITTER_BACKOFF = "jitter_backoff"


@dataclass
class RetryConfig:
    """Configuration pour les retries"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    jitter: bool = True
    timeout: Optional[float] = None
    retryable_exceptions: tuple = (Exception,)


class RetryManager:
    """
    Gestionnaire centralisé pour tous les retries et timeouts
    Remplace la logique dispersée dans toute l'application
    """
    
    def __init__(self):
        self.stats: Dict[str, Dict[str, Any]] = {}
    
    def retry(self, 
              config: Optional[RetryConfig] = None,
              operation_name: str = "unknown",
              on_retry: Optional[Callable[[Exception, int], None]] = None):
        """
        Décorateur pour retry automatique
        
        Args:
            config: Configuration de retry
            operation_name: Nom de l'opération pour les logs
            on_retry: Callback appelé à chaque retry
        """
        if config is None:
            config = RetryConfig()
        
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            def sync_wrapper(*args, **kwargs) -> T:
                return self._execute_with_retry(
                    func, args, kwargs, config, operation_name, on_retry
                )
            
            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> T:
                return await self._execute_with_retry_async(
                    func, args, kwargs, config, operation_name, on_retry
                )
            
            # Détecter si la fonction est async
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def _execute_with_retry(self, 
                          func: Callable[..., T], 
                          args: tuple, 
                          kwargs: dict,
                          config: RetryConfig,
                          operation_name: str,
                          on_retry: Optional[Callable[[Exception, int], None]]) -> T:
        """Exécution synchrone avec retry"""
        last_exception = None
        
        for attempt in range(config.max_attempts):
            try:
                # Appliquer timeout si configuré
                if config.timeout:
                    result = self._execute_with_timeout(func, args, kwargs, config.timeout)
                else:
                    result = func(*args, **kwargs)
                
                # Succès - enregistrer les stats
                self._record_success(operation_name, attempt + 1)
                return result
                
            except Exception as e:
                last_exception = e
                
                # Vérifier si l'exception est retryable
                if not isinstance(e, config.retryable_exceptions):
                    logger.error(f"Exception non-retryable dans {operation_name}: {e}")
                    raise
                
                # Dernier essai
                if attempt == config.max_attempts - 1:
                    self._record_failure(operation_name, config.max_attempts)
                    logger.error(f"Échec final de {operation_name} après {config.max_attempts} tentatives: {e}")
                    raise
                
                # Calculer le délai
                delay = self._calculate_delay(attempt, config)
                
                logger.warning(
                    f"Retry {attempt + 1}/{config.max_attempts} pour {operation_name} "
                    f"après {delay:.2f}s: {e}"
                )
                
                # Callback de retry
                if on_retry:
                    on_retry(e, attempt + 1)
                
                # Attendre avant le prochain essai
                time.sleep(delay)
        
        # Ne devrait pas arriver
        raise last_exception
    
    async def _execute_with_retry_async(self,
                                      func: Callable[..., T],
                                      args: tuple,
                                      kwargs: dict,
                                      config: RetryConfig,
                                      operation_name: str,
                                      on_retry: Optional[Callable[[Exception, int], None]]) -> T:
        """Exécution asynchrone avec retry"""
        last_exception = None
        
        for attempt in range(config.max_attempts):
            try:
                # Appliquer timeout si configuré
                if config.timeout:
                    result = await self._execute_with_timeout_async(func, args, kwargs, config.timeout)
                else:
                    result = await func(*args, **kwargs)
                
                # Succès
                self._record_success(operation_name, attempt + 1)
                return result
                
            except Exception as e:
                last_exception = e
                
                # Vérifier si l'exception est retryable
                if not isinstance(e, config.retryable_exceptions):
                    logger.error(f"Exception non-retryable dans {operation_name}: {e}")
                    raise
                
                # Dernier essai
                if attempt == config.max_attempts - 1:
                    self._record_failure(operation_name, config.max_attempts)
                    logger.error(f"Échec final de {operation_name} après {config.max_attempts} tentatives: {e}")
                    raise
                
                # Calculer le délai
                delay = self._calculate_delay(attempt, config)
                
                logger.warning(
                    f"Retry {attempt + 1}/{config.max_attempts} pour {operation_name} "
                    f"après {delay:.2f}s: {e}"
                )
                
                # Callback de retry
                if on_retry:
                    on_retry(e, attempt + 1)
                
                # Attendre en async
                await asyncio.sleep(delay)
        
        raise last_exception
    
    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calcule le délai selon la stratégie"""
        if config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.base_delay * (2 ** attempt)
        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.base_delay * (attempt + 1)
        elif config.strategy == RetryStrategy.FIXED_DELAY:
            delay = config.base_delay
        elif config.strategy == RetryStrategy.JITTER_BACKOFF:
            delay = config.base_delay * (2 ** attempt)
            # Ajouter jitter aléatoire
            jitter_range = delay * 0.1
            delay += random.uniform(-jitter_range, jitter_range)
        else:
            delay = config.base_delay
        
        # Appliquer jitter si demandé
        if config.jitter and config.strategy != RetryStrategy.JITTER_BACKOFF:
            jitter = random.uniform(0, delay * 0.1)
            delay += jitter
        
        # Limiter au délai maximum
        return min(delay, config.max_delay)
    
    def _execute_with_timeout(self, func: Callable[..., T], args: tuple, kwargs: dict, timeout: float) -> T:
        """Exécute une fonction avec timeout"""
        import signal
        import threading
        
        result = None
        exception = None
        
        def target():
            nonlocal result, exception
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                exception = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            # Timeout - on ne peut pas tuer le thread en Python
            raise TimeoutError(f"Opération timeout après {timeout}s")
        
        if exception:
            raise exception
        
        return result
    
    async def _execute_with_timeout_async(self, func: Callable[..., T], args: tuple, kwargs: dict, timeout: float) -> T:
        """Exécute une fonction async avec timeout"""
        try:
            return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Opération timeout après {timeout}s")
    
    def _record_success(self, operation_name: str, attempts: int) -> None:
        """Enregistre une opération réussie"""
        if operation_name not in self.stats:
            self.stats[operation_name] = {
                "successes": 0,
                "failures": 0,
                "total_attempts": 0,
                "avg_attempts": 0
            }
        
        self.stats[operation_name]["successes"] += 1
        self.stats[operation_name]["total_attempts"] += attempts
        self.stats[operation_name]["avg_attempts"] = (
            self.stats[operation_name]["total_attempts"] / 
            (self.stats[operation_name]["successes"] + self.stats[operation_name]["failures"])
        )
    
    def _record_failure(self, operation_name: str, attempts: int) -> None:
        """Enregistre un échec d'opération"""
        if operation_name not in self.stats:
            self.stats[operation_name] = {
                "successes": 0,
                "failures": 0,
                "total_attempts": 0,
                "avg_attempts": 0
            }
        
        self.stats[operation_name]["failures"] += 1
        self.stats[operation_name]["total_attempts"] += attempts
        self.stats[operation_name]["avg_attempts"] = (
            self.stats[operation_name]["total_attempts"] / 
            (self.stats[operation_name]["successes"] + self.stats[operation_name]["failures"])
        )
    
    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Retourne les statistiques de retry"""
        return self.stats.copy()
    
    def reset_stats(self) -> None:
        """Réinitialise les statistiques"""
        self.stats.clear()


# Instance globale du gestionnaire de retry
_retry_manager = RetryManager()


def get_retry_manager() -> RetryManager:
    """Récupère l'instance globale du gestionnaire de retry"""
    return _retry_manager


# Configurations prédéfinies pour les cas d'usage courants
class RetryConfigs:
    """Configurations de retry prédéfinies"""
    
    # Pour les requêtes web
    WEB_REQUEST = RetryConfig(
        max_attempts=3,
        base_delay=1.0,
        max_delay=10.0,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        jitter=True,
        timeout=30.0,
        retryable_exceptions=(TimeoutError, ConnectionError, OSError)
    )
    
    # Pour les appels LLM
    LLM_CALL = RetryConfig(
        max_attempts=5,
        base_delay=0.5,
        max_delay=30.0,
        strategy=RetryStrategy.JITTER_BACKOFF,
        jitter=True,
        timeout=120.0,
        retryable_exceptions=(TimeoutError, ConnectionError, OSError)
    )
    
    # Pour les opérations de fichier
    FILE_OPERATION = RetryConfig(
        max_attempts=3,
        base_delay=0.1,
        max_delay=2.0,
        strategy=RetryStrategy.LINEAR_BACKOFF,
        jitter=False,
        retryable_exceptions=(IOError, OSError, PermissionError)
    )
    
    # Pour les opérations de base de données
    DATABASE_OPERATION = RetryConfig(
        max_attempts=5,
        base_delay=0.5,
        max_delay=5.0,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        jitter=True,
        timeout=30.0,
        retryable_exceptions=(TimeoutError, ConnectionError)
    )
    
    # Pour les services externes (API tierces)
    EXTERNAL_API = RetryConfig(
        max_attempts=3,
        base_delay=2.0,
        max_delay=60.0,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        jitter=True,
        timeout=60.0,
        retryable_exceptions=(TimeoutError, ConnectionError, OSError)
    )


# Décorateurs pratiques pour les cas courants
def retry_web_request(operation_name: str = "web_request"):
    """Décorateur pour retry de requêtes web"""
    return get_retry_manager().retry(RetryConfigs.WEB_REQUEST, operation_name)


def retry_llm_call(operation_name: str = "llm_call"):
    """Décorateur pour retry d'appels LLM"""
    return get_retry_manager().retry(RetryConfigs.LLM_CALL, operation_name)


def retry_file_operation(operation_name: str = "file_operation"):
    """Décorateur pour retry d'opérations fichier"""
    return get_retry_manager().retry(RetryConfigs.FILE_OPERATION, operation_name)


def retry_database_operation(operation_name: str = "database_operation"):
    """Décorateur pour retry d'opérations base de données"""
    return get_retry_manager().retry(RetryConfigs.DATABASE_OPERATION, operation_name)


def retry_external_api(operation_name: str = "external_api"):
    """Décorateur pour retry d'API externes"""
    return get_retry_manager().retry(RetryConfigs.EXTERNAL_API, operation_name)


# Fonctions utilitaires pour les timeouts
def with_timeout(timeout: float):
    """
    Décorateur pour ajouter un timeout à une fonction
    
    Args:
        timeout: Timeout en secondes
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            config = RetryConfig(timeout=timeout)
            manager = get_retry_manager()
            return manager._execute_with_timeout(func, args, kwargs, timeout)
        
        return wrapper
    return decorator


def with_async_timeout(timeout: float):
    """
    Décorateur pour ajouter un timeout à une fonction async
    
    Args:
        timeout: Timeout en secondes
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            except asyncio.TimeoutError:
                raise TimeoutError(f"Opération timeout après {timeout}s")
        
        return wrapper
    return decorator
