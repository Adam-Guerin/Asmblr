"""
Worker amélioré d'Asmblr - Version avec ErrorHandlerV2, SmartLogger et RetryManager
"""

import os
import sys
import time
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import HTTPException
from redis import Redis
from rq import Worker, Connection

# Importer les systèmes améliorés
from app.core.error_handler_v2 import get_error_handler, handle_errors, NetworkException, LLMException
from app.core.smart_logger import get_smart_logger, LogCategory, LogLevel
from app.core.retry_manager import get_retry_manager, retry_web_request, retry_llm_call
from app.core.config import get_settings
from app.llm import check_ollama


class ImprovedWorker:
    """Worker amélioré avec gestion d'erreurs unifiée et retry intelligent"""
    
    def __init__(self):
        self.error_handler = get_error_handler()
        self.smart_logger = get_smart_logger()
        self.retry_manager = get_retry_manager()
        self.settings = get_settings()
        
        # Démarrer le logging
        self.smart_logger.system(
            LogLevel.LOW,
            "worker_init",
            "Worker amélioré initialisé",
            metadata={
                "error_handler": "v2",
                "logger": "smart",
                "retry_manager": "enabled"
            }
        )
    
    @handle_errors("worker_health", reraise=False)
    def healthz(self):
        """
        Health check amélioré avec retry intelligent et monitoring
        """
        self.smart_logger.start_operation("worker_health_check")
        
        try:
            # Vérifier Redis avec retry automatique
            redis_conn = self.retry_manager.retry_redis_connection()
            redis_conn.ping()
            
            # Vérifier Ollama avec retry automatique
            self.retry_manager.retry_ollama_check()
            
            # Récupérer les métriques de performance
            metrics = self._get_performance_metrics()
            
            self.smart_logger.end_operation("worker_health_check", success=True)
            
            return {
                "status": "ok",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "2.0.0",
                "metrics": metrics,
                "systems": {
                    "error_handler": "v2",
                    "logger": "smart",
                    "retry_manager": "enabled"
                }
            }
            
        except Exception as e:
            context = self.error_handler.handle_exception(e, "worker_health")
            self.smart_logger.end_operation("worker_health_check", success=False)
            
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "error",
                    "message": "Health check failed",
                    "context": context.to_dict(),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
    
    @handle_errors("worker_ready", reraise=False)
    def readyz(self):
        """
        Readiness check amélioré avec vérifications détaillées
        """
        self.smart_logger.start_operation("worker_ready_check")
        
        checks = {}
        all_ok = True
        
        # Vérifier Redis
        try:
            redis_conn = self.retry_manager.retry_redis_connection()
            redis_conn.ping()
            checks["redis"] = {
                "status": "ok",
                "response_time": self._measure_redis_latency(redis_conn)
            }
        except Exception as e:
            checks["redis"] = {
                "status": "failed",
                "error": str(e)
            }
            all_ok = False
        
        # Vérifier Ollama
        try:
            self.retry_manager.retry_ollama_check()
            models = self._get_available_models()
            checks["ollama"] = {
                "status": "ok",
                "models": models,
                "model_count": len(models)
            }
        except Exception as e:
            checks["ollama"] = {
                "status": "failed",
                "error": str(e)
            }
            all_ok = False
        
        # Vérifier la configuration
        try:
            config_status = self._validate_configuration()
            checks["configuration"] = config_status
            if not config_status["valid"]:
                all_ok = False
        except Exception as e:
            checks["configuration"] = {
                "status": "failed",
                "error": str(e)
            }
            all_ok = False
        
        # Vérifier la performance
        try:
            perf_status = self._check_performance()
            checks["performance"] = perf_status
            if perf_status["status"] != "ok":
                all_ok = False
        except Exception as e:
            checks["performance"] = {
                "status": "failed",
                "error": str(e)
            }
            all_ok = False
        
        status = "ready" if all_ok else "not_ready"
        
        self.smart_logger.end_operation(
            "worker_ready_check", 
            success=all_ok,
            metadata={
                "status": status,
                "checks": checks
            }
        )
        
        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks,
            "summary": {
                "total_checks": len(checks),
                "passed_checks": sum(1 for check in checks.values() if check.get("status") == "ok"),
                "failed_checks": sum(1 for check in checks.values() if check.get("status") != "ok")
            }
        }
    
    def _measure_redis_latency(self, redis_conn) -> float:
        """Mesure la latence Redis"""
        start_time = time.time()
        redis_conn.ping()
        return time.time() - start_time
    
    def _get_available_models(self) -> list:
        """Récupère les modèles Ollama disponibles"""
        try:
            import requests
            response = requests.get(f"{self.settings.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
        except:
            pass
        return []
    
    def _validate_configuration(self) -> Dict[str, Any]:
        """Valide la configuration du worker"""
        required_vars = [
            "redis_url",
            "ollama_base_url", 
            "general_model",
            "code_model",
            "rq_queue_name"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not hasattr(self.settings, var) or not getattr(self.settings, var):
                missing_vars.append(var)
        
        return {
            "valid": len(missing_vars) == 0,
            "missing_variables": missing_vars,
            "total_required": len(required_vars)
        }
    
    def _check_performance(self) -> Dict[str, Any]:
        """Vérifie les métriques de performance"""
        try:
            import psutil
            
            # Utilisation CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Utilisation mémoire
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Espace disque
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Statut basé sur les seuils
            status = "ok"
            if cpu_percent > 80 or memory_percent > 80 or disk_percent > 90:
                status = "warning"
            if cpu_percent > 95 or memory_percent > 95 or disk_percent > 95:
                status = "critical"
            
            return {
                "status": status,
                "metrics": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "disk_percent": disk_percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_free_gb": disk.free / (1024**3)
                }
            }
        except ImportError:
            # psutil non disponible
            return {
                "status": "unknown",
                "message": "psutil not available for performance monitoring"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Récupère les métriques de performance"""
        try:
            import psutil
            
            return {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "uptime": time.time() - psutil.boot_time()
            }
        except ImportError:
            return {}
        except Exception:
            return {}
    
    def _run_worker(self) -> None:
        """
        Exécute le worker avec retry et monitoring
        """
        self.smart_logger.start_operation("worker_run")
        
        try:
            # Connexion Redis avec retry
            redis_conn = self.retry_manager.retry_redis_connection()
            
            # Configuration du worker
            worker_config = {
                "name": "asmblr-worker-v2",
                "connection_class": Connection,
                "queue": self.settings.rq_queue_name,
                "default_result_ttl": 3600,  # 1 heure
                "exception_handlers": {
                    "default": self._handle_worker_exception
                }
            }
            
            self.smart_logger.business(
                LogLevel.MEDIUM,
                "worker_start",
                "Worker démarré avec configuration améliorée",
                metadata=worker_config
            )
            
            # Créer et démarrer le worker
            with Connection(redis_conn):
                worker = Worker([self.settings.rq_queue_name], **worker_config)
                
                self.smart_logger.info(
                    LogCategory.SYSTEM,
                    "worker_running",
                    f"Worker en écoute sur la queue: {self.settings.rq_queue_name}",
                    metadata={
                        "worker_name": worker_config["name"],
                        "queue": self.settings.rq_queue_name
                    }
                )
                
                worker.work(with_scheduler=False)
                
        except Exception as e:
            self.smart_logger.end_operation("worker_run", success=False)
            self.error_handler.handle_exception(e, "worker_run")
            raise
    
    def _handle_worker_exception(self, job, exc_type, exc_value, traceback):
        """
        Gestionnaire d'exceptions pour le worker
        """
        self.smart_logger.error(
            LogCategory.SYSTEM,
            "worker_exception",
            f"Exception dans le worker: {exc_type.__name__}",
            metadata={
                "job_id": getattr(job, 'id', 'unknown'),
                "exception_type": exc_type.__name__,
                "exception_message": str(exc_value),
                "queue": self.settings.rq_queue_name
            }
        )
        
        # Retourner True pour que RQ continue de traiter d'autres jobs
        return True


def setup_logging():
    """
    Configure le logging pour le worker amélioré
    """
    # Le SmartLogger gère déjà le logging configuré
    smart_logger = get_smart_logger()
    
    smart_logger.system(
        LogLevel.LOW,
        "worker_setup",
        "Configuration du logging worker amélioré",
        metadata={
            "logger_type": "smart",
            "filtering_enabled": True,
            "structured_logging": True
        }
    )


def main() -> None:
    """
    Point d'entrée principal du worker amélioré
    """
    setup_logging()
    
    smart_logger = get_smart_logger()
    smart_logger.system(
        LogLevel.LOW,
        "worker_main",
        "Démarrage du worker amélioré v2.0",
        metadata={
            "python_version": sys.version,
            "start_time": datetime.utcnow().isoformat()
        }
    )
    
    # Créer et démarrer le worker
    worker = ImprovedWorker()
    
    try:
        worker._run_worker()
    except KeyboardInterrupt:
        smart_logger.business(
            LogLevel.MEDIUM,
            "worker_shutdown",
            "Worker arrêté par l'utilisateur",
            metadata={"graceful": True}
        )
    except Exception as e:
        smart_logger.error(
            LogCategory.SYSTEM,
            "worker_fatal_error",
            f"Erreur fatale du worker: {str(e)}",
            metadata={"fatal": True}
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
