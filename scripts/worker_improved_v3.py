"""
Worker Amélioré pour Asmblr
Avec monitoring intelligent, retry automatique et métriques de performance
"""

import os
import asyncio
from datetime import datetime
from typing import Any
from dataclasses import dataclass, asdict

import redis
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger

# Import des systèmes améliorés
try:
    from app.core.smart_logger import get_smart_logger, LogLevel, LogCategory
    from app.core.error_handler_v2 import get_error_handler, handle_errors
    from app.core.retry_manager import get_retry_manager
    from app.core.performance_optimizer import get_performance_optimizer
    IMPROVED_SYSTEMS_AVAILABLE = True
except ImportError:
    IMPROVED_SYSTEMS_AVAILABLE = False
    logger.warning("Systèmes améliorés non disponibles, utilisation des fallbacks")

from app.core.config import Settings
from app.core.llm import check_ollama


@dataclass
class WorkerMetrics:
    """Métriques de performance du worker"""
    start_time: datetime
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    redis_connection_status: str = "unknown"
    ollama_status: str = "unknown"
    last_health_check: datetime | None = None


class ImprovedWorker:
    """Worker amélioré avec monitoring et retry intelligent"""
    
    def __init__(self):
        self.settings = Settings()
        self.metrics = WorkerMetrics(start_time=datetime.utcnow())
        self.app = FastAPI(title="Asmblr Worker v2", version="2.0.0")
        
        # Initialisation des systèmes améliorés
        if IMPROVED_SYSTEMS_AVAILABLE:
            self.smart_logger = get_smart_logger()
            self.error_handler = get_error_handler()
            self.retry_manager = get_retry_manager()
            self.performance_optimizer = get_performance_optimizer()
        else:
            self.smart_logger = None
            self.error_handler = None
            self.retry_manager = None
            self.performance_optimizer = None
        
        # Configuration Redis avec retry
        self.redis_client = None
        self._init_redis()
        
        # Routes FastAPI
        self._setup_routes()
        
        # Tâches de fond
        self.background_tasks = []
        
        logger.info("Improved Worker initialized")
    
    def _init_redis(self):
        """Initialise Redis avec retry automatique"""
        try:
            if self.retry_manager:
                self.redis_client = self.retry_manager.retry_redis_connection()
            else:
                self.redis_client = redis.from_url(
                    self.settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
            
            # Test de connexion
            self.redis_client.ping()
            self.metrics.redis_connection_status = "connected"
            
            if self.smart_logger:
                self.smart_logger.system(
                    LogLevel.MEDIUM,
                    "Redis connection established",
                    {"redis_url": self.settings.REDIS_URL}
                )
            
        except Exception as e:
            self.metrics.redis_connection_status = f"failed: {str(e)}"
            if self.error_handler:
                self.error_handler.handle_exception(e, "redis_init")
            else:
                logger.error(f"Redis connection failed: {e}")
    
    def _setup_routes(self):
        """Configure les routes FastAPI"""
        
        @self.app.get("/healthz")
        @handle_errors("worker_health", reraise=False) if IMPROVED_SYSTEMS_AVAILABLE else lambda f: f
        async def healthz():
            """Health check amélioré avec monitoring"""
            try:
                # Vérifier Redis avec retry
                if self.retry_manager:
                    redis_conn = self.retry_manager.retry_redis_connection()
                    redis_conn.ping()
                    redis_status = "ok"
                else:
                    redis_status = self._check_redis_simple()
                
                # Vérifier Ollama avec retry
                if self.retry_manager:
                    ollama_status = await self.retry_manager.retry_ollama_check_async()
                else:
                    ollama_status = await self._check_ollama_simple()
                
                # Métriques de performance
                if self.performance_optimizer:
                    perf_metrics = self.performance_optimizer.get_current_metrics()
                else:
                    perf_metrics = self._get_simple_metrics()
                
                # Mettre à jour les métriques du worker
                self.metrics.last_health_check = datetime.utcnow()
                self.metrics.redis_connection_status = redis_status
                self.metrics.ollama_status = ollama_status
                
                response_data = {
                    "status": "ok",
                    "timestamp": datetime.utcnow().isoformat(),
                    "metrics": {
                        "uptime_seconds": (datetime.utcnow() - self.metrics.start_time).total_seconds(),
                        "total_requests": self.metrics.total_requests,
                        "success_rate": (
                            self.metrics.successful_requests / max(1, self.metrics.total_requests) * 100
                        ),
                        "avg_response_time": self.metrics.avg_response_time,
                        **perf_metrics
                    },
                    "services": {
                        "redis": redis_status,
                        "ollama": ollama_status
                    }
                }
                
                if self.smart_logger:
                    self.smart_logger.system(
                        LogLevel.LOW,
                        "Worker health check passed",
                        response_data
                    )
                
                return JSONResponse(content=response_data)
                
            except Exception as e:
                if self.error_handler:
                    context = self.error_handler.handle_exception(e, "worker_health")
                    raise HTTPException(status_code=503, detail=context.to_dict())
                else:
                    raise HTTPException(status_code=503, detail=str(e))
        
        @self.app.get("/readyz")
        async def readyz():
            """Readiness check amélioré"""
            checks = {}
            
            # Redis check
            try:
                if self.redis_client:
                    self.redis_client.ping()
                    checks["redis"] = "ok"
                else:
                    checks["redis"] = "not_initialized"
            except Exception as e:
                checks["redis"] = f"failed: {e}"
            
            # Ollama check
            try:
                ollama_ok = await check_ollama(self.settings.OLLAMA_BASE_URL)
                checks["ollama"] = "ok" if ollama_ok else "failed"
            except Exception as e:
                checks["ollama"] = f"failed: {e}"
            
            # Performance check
            try:
                if self.performance_optimizer:
                    metrics = self.performance_optimizer.get_current_metrics()
                    checks["performance"] = "ok"
                else:
                    checks["performance"] = "basic_monitoring"
            except Exception as e:
                checks["performance"] = f"failed: {e}"
            
            # Memory check
            try:
                import psutil
                memory_percent = psutil.virtual_memory().percent
                checks["memory"] = "ok" if memory_percent < 80 else f"high: {memory_percent}%"
            except Exception:
                checks["memory"] = "unknown"
            
            all_ok = all("ok" in status for status in checks.values())
            
            return {
                "status": "ready" if all_ok else "not_ready",
                "checks": checks,
                "timestamp": datetime.utcnow().isoformat(),
                "worker_metrics": asdict(self.metrics)
            }
        
        @self.app.get("/metrics")
        async def metrics():
            """Métriques détaillées du worker"""
            return {
                "worker_metrics": asdict(self.metrics),
                "performance_metrics": (
                    self.performance_optimizer.get_current_metrics() 
                    if self.performance_optimizer 
                    else self._get_simple_metrics()
                ),
                "system_info": {
                    "improved_systems_available": IMPROVED_SYSTEMS_AVAILABLE,
                    "redis_connected": self.redis_client is not None,
                    "smart_logging_enabled": self.smart_logger is not None
                }
            }
    
    def _check_redis_simple(self) -> str:
        """Vérification Redis simple (fallback)"""
        try:
            if self.redis_client:
                self.redis_client.ping()
                return "ok"
            return "not_connected"
        except Exception as e:
            return f"failed: {e}"
    
    async def _check_ollama_simple(self) -> str:
        """Vérification Ollama simple (fallback)"""
        try:
            ollama_ok = await check_ollama(self.settings.OLLAMA_BASE_URL)
            return "ok" if ollama_ok else "failed"
        except Exception as e:
            return f"failed: {e}"
    
    def _get_simple_metrics(self) -> dict[str, Any]:
        """Métriques simples (fallback)"""
        try:
            import psutil
            return {
                "memory_usage_mb": psutil.virtual_memory().used / 1024 / 1024,
                "cpu_usage_percent": psutil.cpu_percent(),
                "disk_usage_percent": psutil.disk_usage('/').percent
            }
        except Exception:
            return {
                "memory_usage_mb": 0,
                "cpu_usage_percent": 0,
                "disk_usage_percent": 0
            }
    
    def update_request_metrics(self, success: bool, response_time: float):
        """Met à jour les métriques de requêtes"""
        self.metrics.total_requests += 1
        
        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1
        
        # Moyenne mobile du temps de réponse
        total_time = self.metrics.avg_response_time * (self.metrics.total_requests - 1) + response_time
        self.metrics.avg_response_time = total_time / self.metrics.total_requests
    
    async def start_background_monitoring(self):
        """Démarre le monitoring en arrière-plan"""
        while True:
            try:
                # Mettre à jour les métriques système
                if self.performance_optimizer:
                    self.performance_optimizer.collect_metrics()
                
                # Logger l'état du worker
                if self.smart_logger:
                    self.smart_logger.performance(
                        "Worker monitoring update",
                        {
                            "uptime_seconds": (datetime.utcnow() - self.metrics.start_time).total_seconds(),
                            "success_rate": (
                                self.metrics.successful_requests / max(1, self.metrics.total_requests) * 100
                            ),
                            "redis_status": self.metrics.redis_connection_status,
                            "ollama_status": self.metrics.ollama_status
                        }
                    )
                
                await asyncio.sleep(60)  # Monitoring toutes les minutes
                
            except Exception as e:
                if self.error_handler:
                    self.error_handler.handle_exception(e, "background_monitoring")
                else:
                    logger.error(f"Background monitoring error: {e}")
                await asyncio.sleep(60)


# Instance globale du worker
worker_instance: ImprovedWorker | None = None


def get_worker() -> ImprovedWorker:
    """Retourne l'instance du worker"""
    global worker_instance
    if worker_instance is None:
        worker_instance = ImprovedWorker()
    return worker_instance


def create_app() -> FastAPI:
    """Crée l'application FastAPI avec le worker amélioré"""
    worker = get_worker()
    
    # Démarrer le monitoring en arrière-plan
    @worker.app.on_event("startup")
    async def startup_event():
        asyncio.create_task(worker.start_background_monitoring())
        
        if worker.smart_logger:
            worker.smart_logger.business(
                LogLevel.MEDIUM,
                "Improved Worker started successfully",
                {
                    "version": "2.0.0",
                    "improved_systems": IMPROVED_SYSTEMS_AVAILABLE,
                    "redis_url": worker.settings.REDIS_URL,
                    "ollama_url": worker.settings.OLLAMA_BASE_URL
                }
            )
    
    return worker.app


# Point d'entrée pour le worker
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Improved Worker...")
    uvicorn.run(
        "worker_improved_v2:app",
        host="0.0.0.0",
        port=int(os.getenv("WORKER_PORT", 8001)),
        reload=False,
        log_level="info"
    )
