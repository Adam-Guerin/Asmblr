"""
Logger structuré pour Asmblr avec intégration ELK Stack
Compatible avec le smart logger existant
"""

import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any, Optional, Union
from pathlib import Path
from enum import Enum
import uuid

from loguru import logger


class LogLevel(Enum):
    """Niveaux de log structurés"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(Enum):
    """Catégories de logs pour Asmblr"""
    SYSTEM = "SYSTEM"
    BUSINESS = "BUSINESS"
    PERFORMANCE = "PERFORMANCE"
    SECURITY = "SECURITY"
    API = "API"
    WORKER = "WORKER"
    LLM = "LLM"
    CACHE = "CACHE"
    PIPELINE = "PIPELINE"
    MVP = "MVP"
    USER = "USER"


class StructuredLogger:
    """Logger structuré avec format JSON pour ELK Stack"""
    
    def __init__(self, 
                 service_name: str = "asmblr",
                 environment: str = "development",
                 version: str = "1.0.0",
                 enable_file_output: bool = True,
                 log_file_path: Optional[str] = None):
        
        self.service_name = service_name
        self.environment = environment
        self.version = version
        self.enable_file_output = enable_file_output
        
        # Configuration du fichier de logs
        if log_file_path is None:
            log_file_path = f"/var/log/asmblr/{service_name}.json"
        
        self.log_file_path = Path(log_file_path)
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Contexte global
        self.global_context = {
            "service": service_name,
            "environment": environment,
            "version": version
        }
        
        # Configurer le logger structuré
        self._setup_structured_logging()
    
    def _setup_structured_logging(self):
        """Configure le logging structuré"""
        # Créer un handler custom pour le format JSON
        if self.enable_file_output:
            handler = logging.FileHandler(self.log_file_path)
            handler.setFormatter(JsonFormatter())
            
            # Configurer le logger root
            root_logger = logging.getLogger()
            root_logger.addHandler(handler)
            root_logger.setLevel(logging.DEBUG)
    
    def _create_log_entry(self,
                         level: LogLevel,
                         category: LogCategory,
                         message: str,
                         **kwargs) -> Dict[str, Any]:
        """Crée une entrée de log structurée"""
        
        # Timestamp
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Contexte de corrélation
        trace_id = kwargs.get("trace_id") or self._generate_trace_id()
        span_id = kwargs.get("span_id") or self._generate_span_id()
        
        # Construire l'entrée de log
        log_entry = {
            "@timestamp": timestamp,
            "level": level.value,
            "category": category.value,
            "message": message,
            "service": self.service_name,
            "environment": self.environment,
            "version": self.version,
            "trace_id": trace_id,
            "span_id": span_id,
            **self.global_context
        }
        
        # Ajouter les métadonnées
        metadata = kwargs.get("metadata", {})
        if metadata:
            log_entry["metadata"] = metadata
        
        # Ajouter les labels
        labels = kwargs.get("labels", {})
        if labels:
            log_entry["labels"] = labels
        
        # Ajouter les métriques
        metrics = kwargs.get("metrics", {})
        if metrics:
            log_entry["metrics"] = metrics
        
        # Ajouter les informations d'erreur si présentes
        if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
            error_info = kwargs.get("error_info", {})
            if error_info:
                log_entry["error"] = error_info
        
        # Ajouter le contexte utilisateur
        user_context = kwargs.get("user_context", {})
        if user_context:
            log_entry["user"] = user_context
        
        # Ajouter le contexte de requête
        request_context = kwargs.get("request_context", {})
        if request_context:
            log_entry["request"] = request_context
        
        return log_entry
    
    def _generate_trace_id(self) -> str:
        """Génère un trace ID unique"""
        return str(uuid.uuid4())
    
    def _generate_span_id(self) -> str:
        """Génère un span ID unique"""
        return str(uuid.uuid4())[:16]
    
    def _write_log(self, log_entry: Dict[str, Any]):
        """Écrire le log avec le logger approprié"""
        level = log_entry["level"]
        message = log_entry["message"]
        
        # Mapper les niveaux de log vers les fonctions du logger
        import logging
        logger = logging.getLogger("asmblr")
        level_map = {
            "DEBUG": logger.debug,
            "INFO": logger.info,
            "WARNING": logger.warning,
            "ERROR": logger.error,
            "CRITICAL": logger.critical
        }
        
        logger_func = level_map.get(level.upper(), logger.info)
        logger_func(f"[{log_entry['category']}] {log_entry['message']}")
        
        # Écrire dans le fichier JSON
        if self.enable_file_output:
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    def debug(self, category: LogCategory, message: str, **kwargs):
        """Log de niveau DEBUG"""
        log_entry = self._create_log_entry(LogLevel.DEBUG, category, message, **kwargs)
        self._write_log(log_entry)
    
    def info(self, category: LogCategory, message: str, **kwargs):
        """Log de niveau INFO"""
        log_entry = self._create_log_entry(LogLevel.INFO, category, message, **kwargs)
        self._write_log(log_entry)
    
    def warning(self, category: LogCategory, message: str, **kwargs):
        """Log de niveau WARNING"""
        log_entry = self._create_log_entry(LogLevel.WARNING, category, message, **kwargs)
        self._write_log(log_entry)
    
    def error(self, category: LogCategory, message: str, **kwargs):
        """Log de niveau ERROR"""
        log_entry = self._create_log_entry(LogLevel.ERROR, category, message, **kwargs)
        self._write_log(log_entry)
    
    def critical(self, category: LogCategory, message: str, **kwargs):
        """Log de niveau CRITICAL"""
        log_entry = self._create_log_entry(LogLevel.CRITICAL, category, message, **kwargs)
        self._write_log(log_entry)
    
    # Méthodes spécialisées pour différents types de logs
    def system(self, message: str, **kwargs):
        """Log système"""
        self.info(LogCategory.SYSTEM, message, **kwargs)
    
    def business(self, message: str, **kwargs):
        """Log business"""
        self.info(LogCategory.BUSINESS, message, **kwargs)
    
    def performance(self, message: str, **kwargs):
        """Log de performance"""
        self.info(LogCategory.PERFORMANCE, message, **kwargs)
    
    def security(self, message: str, **kwargs):
        """Log de sécurité"""
        self.warning(LogCategory.SECURITY, message, **kwargs)
    
    def api_request(self, method: str, endpoint: str, status: int, duration: float, **kwargs):
        """Log de requête API"""
        message = f"{method} {endpoint} - {status} in {duration:.3f}s"
        self.info(LogCategory.API, message, 
                 metadata={
                     "method": method,
                     "endpoint": endpoint,
                     "status": status,
                     "duration": duration
                 },
                 **kwargs)
    
    def llm_request(self, model: str, prompt_tokens: int, response_tokens: int, duration: float, **kwargs):
        """Log de requête LLM"""
        message = f"LLM request to {model} - {prompt_tokens + response_tokens} tokens in {duration:.3f}s"
        self.info(LogCategory.LLM, message,
                 metadata={
                     "model": model,
                     "prompt_tokens": prompt_tokens,
                     "response_tokens": response_tokens,
                     "total_tokens": prompt_tokens + response_tokens,
                     "duration": duration
                 },
                 **kwargs)
    
    def cache_operation(self, operation: str, key: str, hit: bool, **kwargs):
        """Log d'opération de cache"""
        message = f"Cache {operation} - {key} - {'HIT' if hit else 'MISS'}"
        self.debug(LogCategory.CACHE, message,
                  metadata={
                      "operation": operation,
                      "key": key,
                      "hit": hit
                  },
                  **kwargs)
    
    def pipeline_step(self, pipeline: str, step: str, status: str, duration: float, **kwargs):
        """Log d'étape de pipeline"""
        message = f"Pipeline {pipeline} - {step} - {status} in {duration:.3f}s"
        self.info(LogCategory.PIPELINE, message,
                 metadata={
                     "pipeline": pipeline,
                     "step": step,
                     "status": status,
                     "duration": duration
                 },
                 **kwargs)
    
    def mvp_build(self, framework: str, status: str, duration: float, **kwargs):
        """Log de build MVP"""
        message = f"MVP build - {framework} - {status} in {duration:.3f}s"
        self.info(LogCategory.MVP, message,
                 metadata={
                     "framework": framework,
                     "status": status,
                     "duration": duration
                 },
                 **kwargs)
    
    def user_action(self, user_id: str, action: str, resource: str, **kwargs):
        """Log d'action utilisateur"""
        message = f"User {user_id} - {action} - {resource}"
        self.info(LogCategory.USER, message,
                 user_context={"user_id": user_id},
                 metadata={
                     "action": action,
                     "resource": resource
                 },
                 **kwargs)
    
    def error_with_exception(self, category: LogCategory, message: str, exception: Exception, **kwargs):
        """Log d'erreur avec exception"""
        import traceback
        
        error_info = {
            "type": type(exception).__name__,
            "message": str(exception),
            "stack_trace": traceback.format_exc()
        }
        
        self.error(category, message, error_info=error_info, **kwargs)


class JsonFormatter(logging.Formatter):
    """Formatter JSON pour les logs structurés"""
    
    def format(self, record):
        log_entry = {
            "@timestamp": datetime.fromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Ajouter les attributs supplémentaires
        if hasattr(record, 'trace_id'):
            log_entry['trace_id'] = record.trace_id
        if hasattr(record, 'span_id'):
            log_entry['span_id'] = record.span_id
        
        return json.dumps(log_entry, ensure_ascii=False)


# Instance globale du logger structuré
STRUCTURED_LOGGER = StructuredLogger()


def get_structured_logger() -> StructuredLogger:
    """Retourne l'instance globale du logger structuré"""
    return STRUCTURED_LOGGER


# Context manager pour les traces
class TraceContext:
    """Context manager pour les traces distribuées"""
    
    def __init__(self, 
                 operation: str,
                 category: LogCategory = LogCategory.SYSTEM,
                 logger: StructuredLogger = None,
                 **metadata):
        self.operation = operation
        self.category = category
        self.logger = logger or get_structured_logger()
        self.metadata = metadata
        self.trace_id = self.logger._generate_trace_id()
        self.span_id = self.logger._generate_span_id()
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        
        self.logger.info(
            self.category,
            f"Starting {self.operation}",
            trace_id=self.trace_id,
            span_id=self.span_id,
            metadata={
                "operation": self.operation,
                "start_time": self.start_time.isoformat(),
                **self.metadata
            }
        )
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.utcnow() - self.start_time).total_seconds()
        
        if exc_type:
            self.logger.error(
                self.category,
                f"Failed {self.operation}",
                trace_id=self.trace_id,
                span_id=self.span_id,
                metadata={
                    "operation": self.operation,
                    "duration": duration,
                    "error": str(exc_val) if exc_val else None
                }
            )
        else:
            self.logger.info(
                self.category,
                f"Completed {self.operation}",
                trace_id=self.trace_id,
                span_id=self.span_id,
                metadata={
                    "operation": self.operation,
                    "duration": duration
                }
            )


# Decorateur pour tracer automatiquement les fonctions
def trace(operation: str = None, category: LogCategory = LogCategory.SYSTEM):
    """Décorateur pour tracer automatiquement les fonctions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            op_name = operation or f"{func.__module__}.{func.__name__}"
            
            with TraceContext(op_name, category):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    STRUCTURED_LOGGER.error_with_exception(
                        category,
                        f"Error in {op_name}",
                        e
                    )
                    raise
        
        return wrapper
    return decorator


# Exemples d'utilisation
if __name__ == "__main__":
    # Logger structuré
    logger = get_structured_logger()
    
    # Logs basiques
    logger.system("Démarrage du service Asmblr")
    logger.business("Pipeline démarrée", metadata={"pipeline_id": "123"})
    
    # Logs spécialisés
    logger.api_request("GET", "/api/health", 200, 0.05)
    logger.llm_request("llama3.1:8b", 50, 100, 2.5)
    logger.cache_operation("get", "user:123", True)
    
    # Avec contexte de trace
    with TraceContext("process_venture", LogCategory.BUSINESS, venture_id="456"):
        logger.info(LogCategory.BUSINESS, "Traitement du venture")
        logger.info(LogCategory.BUSINESS, "Génération des idées")
    
    # Avec décorateur
    @trace("calculate_metrics", LogCategory.PERFORMANCE)
    def calculate_metrics():
        logger.performance("Calcul des métriques", metrics={"cpu": 45.2, "memory": 67.8})
        return {"cpu": 45.2, "memory": 67.8}
    
    result = calculate_metrics()
    print(f"Métriques: {result}")
