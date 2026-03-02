#!/usr/bin/env python
"""
Worker d'Asmblr - Version amelioree avec ErrorHandlerV2 et SmartLogger
"""

import sys
from datetime import datetime

try:
    from app.core.error_handler_v2 import get_error_handler, handle_errors
    from app.core.smart_logger import get_smart_logger, LogCategory, LogLevel
    from app.core.retry_manager import get_retry_manager
    from app.core.config import get_settings
    from app.llm import check_ollama
    from fastapi import HTTPException
    from redis import Redis
    from rq import Worker, Connection
    
    # Initialiser les systemes ameliores
    ERROR_HANDLER = get_error_handler()
    SMART_LOGGER = get_smart_logger()
    RETRY_MANAGER = get_retry_manager()
    SETTINGS = get_settings()
    
except ImportError as e:
    print(f"Erreur import systemes ameliores: {e}")
    sys.exit(1)


class ImprovedWorker:
    def __init__(self):
        self.smart_logger = get_smart_logger()
        self.error_handler = get_error_handler()
        self.retry_manager = get_retry_manager()
        
        self.smart_logger.system(
            LogLevel.LOW,
            "worker_init",
            "Worker ameliore initialise"
        )
    
    @handle_errors("health_check", reraise=False)
    def healthz(self):
        """Health check ameliore"""
        try:
            # Redis avec retry
            redis_conn = self.retry_manager.retry_redis_connection()
            redis_conn.ping()
            
            # Ollama avec retry
            self.retry_manager.retry_ollama_check()
            
            self.smart_logger.info(LogCategory.SYSTEM, "health", "Health check OK")
            return {"status": "ok"}
            
        except Exception as e:
            context = self.error_handler.handle_exception(e, "health_check")
            raise HTTPException(status_code=503, detail=context.to_dict())
    
    @handle_errors("ready_check", reraise=False)
    def readyz(self):
        """Readiness check ameliore"""
        try:
            # Verifications detaillees
            redis_ok = self.retry_manager.retry_redis_connection().ping()
            ollama_ok = self.retry_manager.retry_ollama_check()
            
            status = "ready" if redis_ok and ollama_ok else "not_ready"
            
            self.smart_logger.info(
                LogCategory.SYSTEM, 
                "readiness", 
                f"Readiness check: {status}"
            )
            
            return {"status": status}
            
        except Exception as e:
            context = self.error_handler.handle_exception(e, "ready_check")
            raise HTTPException(status_code=503, detail=context.to_dict())
    
    def run(self):
        """Execution du worker ameliore"""
        self.smart_logger.business(
            LogLevel.MEDIUM,
            "worker_start",
            "Demarrage du worker ameliore"
        )
        
        try:
            redis_conn = self.retry_manager.retry_redis_connection()
            with Connection(redis_conn):
                worker = Worker([SETTINGS.rq_queue_name])
                worker.work(with_scheduler=False)
        except Exception as e:
            self.error_handler.handle_exception(e, "worker_run")
            raise


def setup_logging():
    """Configure le logging pour le worker ameliore"""
    # Le SmartLogger gere deja le logging configure
    smart_logger = get_smart_logger()
    
    smart_logger.system(
        LogLevel.LOW,
        "worker_setup",
        "Configuration du logging worker ameliore",
        metadata={
            "logger_type": "smart",
            "filtering_enabled": True,
            "structured_logging": True
        }
    )


def main():
    """Point d'entree principal"""
    setup_logging()
    
    smart_logger = get_smart_logger()
    smart_logger.system(
        LogLevel.LOW,
        "worker_main",
        "Demarrage du worker ameliore v2.0",
        metadata={
            "python_version": sys.version,
            "start_time": datetime.utcnow().isoformat()
        }
    )
    
    # Creer et demarrer le worker
    worker = ImprovedWorker()
    
    try:
        worker.run()
    except KeyboardInterrupt:
        SMART_LOGGER.business(
            LogLevel.MEDIUM,
            "worker_shutdown",
            "Worker arrete proprement"
        )
    except Exception as e:
        ERROR_HANDLER.handle_exception(e, "main")
        sys.exit(1)


if __name__ == "__main__":
    main()
