"""
Système de métriques complet pour Asmblr avec Prometheus
Exportateur de métriques, registry centralisé et métriques business
"""

import time
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum

from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client.core import REGISTRY
from fastapi import FastAPI, Response
from loguru import logger


class MetricType(Enum):
    """Types de métriques supportées"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    INFO = "info"


@dataclass
class MetricConfig:
    """Configuration pour une métrique"""
    name: str
    metric_type: MetricType
    description: str
    labels: List[str] = None
    buckets: List[float] = None  # Pour les histogrammes
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = []
        if self.buckets is None:
            self.buckets = [0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0]


class PrometheusMetricsRegistry:
    """Registry centralisé pour les métriques Prometheus"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        self.metrics: Dict[str, Any] = {}
        self.configs: Dict[str, MetricConfig] = {}
        self._lock = threading.Lock()
    
    def register_metric(self, config: MetricConfig) -> bool:
        """Enregistre une nouvelle métrique"""
        with self._lock:
            if config.name in self.metrics:
                logger.warning(f"Métrique {config.name} déjà enregistrée")
                return False
            
            try:
                # Créer la métrique selon son type
                if config.metric_type == MetricType.COUNTER:
                    metric = Counter(
                        config.name,
                        config.description,
                        labelnames=config.labels,
                        registry=self.registry
                    )
                elif config.metric_type == MetricType.GAUGE:
                    metric = Gauge(
                        config.name,
                        config.description,
                        labelnames=config.labels,
                        registry=self.registry
                    )
                elif config.metric_type == MetricType.HISTOGRAM:
                    metric = Histogram(
                        config.name,
                        config.description,
                        labelnames=config.labels,
                        buckets=config.buckets,
                        registry=self.registry
                    )
                elif config.metric_type == MetricType.INFO:
                    metric = Info(
                        config.name,
                        config.description,
                        labelnames=config.labels,
                        registry=self.registry
                    )
                else:
                    logger.error(f"Type de métrique non supporté: {config.metric_type}")
                    return False
                
                self.metrics[config.name] = metric
                self.configs[config.name] = config
                
                logger.info(f"Métrique {config.name} enregistrée avec succès")
                return True
                
            except Exception as e:
                logger.error(f"Erreur lors de l'enregistrement de la métrique {config.name}: {e}")
                return False
    
    def get_metric(self, name: str) -> Optional[Any]:
        """Récupère une métrique par son nom"""
        return self.metrics.get(name)
    
    def increment_counter(self, name: str, value: float = 1, labels: Dict[str, str] = None):
        """Incrémente un counter"""
        metric = self.get_metric(name)
        if metric and isinstance(metric, Counter):
            if labels:
                metric.labels(**labels).inc(value)
            else:
                metric.inc(value)
        else:
            logger.warning(f"Counter {name} non trouvé")
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Définit la valeur d'un gauge"""
        metric = self.get_metric(name)
        if metric and isinstance(metric, Gauge):
            if labels:
                metric.labels(**labels).set(value)
            else:
                metric.set(value)
        else:
            logger.warning(f"Gauge {name} non trouvé")
    
    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Observe une valeur dans un histogramme"""
        metric = self.get_metric(name)
        if metric and isinstance(metric, Histogram):
            if labels:
                metric.labels(**labels).observe(value)
            else:
                metric.observe(value)
        else:
            logger.warning(f"Histogram {name} non trouvé")
    
    def set_info(self, name: str, info: Dict[str, str]):
        """Définit une métrique de type info"""
        from prometheus_client import Info
        
        if name not in self.metrics:
            # Créer la métrique info si elle n'existe pas
            self.metrics[name] = Info(name, self.configs.get(name, {}).get('description', name))
        
        # Définir les informations
        if isinstance(self.metrics[name], Info):
            self.metrics[name].info(info)
        else:
            logger.warning(f"Info {name} non trouvé")
    
    def generate_metrics(self) -> str:
        """Génère les métriques au format Prometheus"""
        return generate_latest(self.registry).decode('utf-8')
    
    def list_metrics(self) -> List[str]:
        """Liste toutes les métriques enregistrées"""
        return list(self.metrics.keys())


class BusinessMetrics:
    """Métriques business pour Asmblr"""
    
    def __init__(self, registry: PrometheusMetricsRegistry):
        self.registry = registry
        self._setup_business_metrics()
    
    def _setup_business_metrics(self):
        """Configure les métriques business"""
        business_configs = [
            # Métriques de pipeline
            MetricConfig(
                name="asmblr_pipeline_runs_total",
                metric_type=MetricType.COUNTER,
                description="Nombre total d'exécutions de pipeline",
                labels=["status", "type"]
            ),
            MetricConfig(
                name="asmblr_pipeline_duration_seconds",
                metric_type=MetricType.HISTOGRAM,
                description="Durée d'exécution des pipelines",
                labels=["type", "stage"],
                buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0, 600.0, 1800.0, 3600.0]
            ),
            MetricConfig(
                name="asmblr_ideas_generated_total",
                metric_type=MetricType.COUNTER,
                description="Nombre total d'idées générées",
                labels=["source", "quality"]
            ),
            MetricConfig(
                name="asmblr_mvp_builds_total",
                metric_type=MetricType.COUNTER,
                description="Nombre total de builds MVP",
                labels=["status", "framework"]
            ),
            
            # Métriques LLM
            MetricConfig(
                name="asmblr_llm_requests_total",
                metric_type=MetricType.COUNTER,
                description="Nombre total de requêtes LLM",
                labels=["model", "status", "type"]
            ),
            MetricConfig(
                name="asmblr_llm_response_time_seconds",
                metric_type=MetricType.HISTOGRAM,
                description="Temps de réponse des requêtes LLM",
                labels=["model", "type"],
                buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
            ),
            MetricConfig(
                name="asmblr_llm_tokens_total",
                metric_type=MetricType.COUNTER,
                description="Nombre total de tokens utilisés",
                labels=["model", "type"]
            ),
            
            # Métriques de cache
            MetricConfig(
                name="asmblr_cache_operations_total",
                metric_type=MetricType.COUNTER,
                description="Nombre total d'opérations de cache",
                labels=["cache_type", "operation", "result"]
            ),
            MetricConfig(
                name="asmblr_cache_size_bytes",
                metric_type=MetricType.GAUGE,
                description="Taille du cache en bytes",
                labels=["cache_type"]
            ),
            MetricConfig(
                name="asmblr_cache_hit_ratio",
                metric_type=MetricType.GAUGE,
                description="Ratio de hits du cache",
                labels=["cache_type"]
            ),
            
            # Métriques d'alertes
            MetricConfig(
                name="asmblr_alerts_total",
                metric_type=MetricType.COUNTER,
                description="Nombre total d'alertes",
                labels=["name", "severity", "status"]
            ),
            
            # Métriques utilisateur
            MetricConfig(
                name="asmblr_active_users",
                metric_type=MetricType.GAUGE,
                description="Nombre d'utilisateurs actifs",
                labels=["period"]
            ),
            MetricConfig(
                name="asmblr_user_sessions_total",
                metric_type=MetricType.COUNTER,
                description="Nombre total de sessions utilisateur",
                labels=["status"]
            ),
            
            # Métriques système
            MetricConfig(
                name="asmblr_system_info",
                metric_type=MetricType.INFO,
                description="Informations système sur Asmblr",
                labels=["version", "environment"]
            )
        ]
        
        for config in business_configs:
            self.registry.register_metric(config)
    
    def record_pipeline_start(self, pipeline_type: str):
        """Enregistre le début d'une pipeline"""
        self.registry.increment_counter(
            "asmblr_pipeline_runs_total",
            labels={"status": "started", "type": pipeline_type}
        )
    
    def record_pipeline_completion(self, pipeline_type: str, duration: float, status: str):
        """Enregistre la completion d'une pipeline"""
        self.registry.increment_counter(
            "asmblr_pipeline_runs_total",
            labels={"status": status, "type": pipeline_type}
        )
        self.registry.observe_histogram(
            "asmblr_pipeline_duration_seconds",
            duration,
            labels={"type": pipeline_type, "stage": "total"}
        )
    
    def record_idea_generation(self, source: str, quality: str, count: int = 1):
        """Enregistre la génération d'idées"""
        self.registry.increment_counter(
            "asmblr_ideas_generated_total",
            value=count,
            labels={"source": source, "quality": quality}
        )
    
    def record_mvp_build(self, status: str, framework: str):
        """Enregistre un build MVP"""
        self.registry.increment_counter(
            "asmblr_mvp_builds_total",
            labels={"status": status, "framework": framework}
        )
    
    def record_llm_request(self, model: str, request_type: str, response_time: float, status: str, tokens: int = 0):
        """Enregistre une requête LLM"""
        self.registry.increment_counter(
            "asmblr_llm_requests_total",
            labels={"model": model, "status": status, "type": request_type}
        )
        self.registry.observe_histogram(
            "asmblr_llm_response_time_seconds",
            response_time,
            labels={"model": model, "type": request_type}
        )
        if tokens > 0:
            self.registry.increment_counter(
                "asmblr_llm_tokens_total",
                value=tokens,
                labels={"model": model, "type": request_type}
            )
    
    def record_cache_operation(self, cache_type: str, operation: str, result: str):
        """Enregistre une opération de cache"""
        self.registry.increment_counter(
            "asmblr_cache_operations_total",
            labels={"cache_type": cache_type, "operation": operation, "result": result}
        )
    
    def update_cache_metrics(self, cache_type: str, size_bytes: int, hit_ratio: float):
        """Met à jour les métriques de cache"""
        self.registry.set_gauge(
            "asmblr_cache_size_bytes",
            size_bytes,
            labels={"cache_type": cache_type}
        )
        self.registry.set_gauge(
            "asmblr_cache_hit_ratio",
            hit_ratio,
            labels={"cache_type": cache_type}
        )
    
    def update_active_users(self, count: int, period: str):
        """Met à jour le nombre d'utilisateurs actifs"""
        self.registry.set_gauge(
            "asmblr_active_users",
            count,
            labels={"period": period}
        )
    
    def record_alert(self, name: str, severity: str, status: str):
        """Enregistre une alerte"""
        self.registry.increment_counter(
            "asmblr_alerts_total",
            labels={"name": name, "severity": severity, "status": status}
        )
    
    def record_user_session(self, status: str):
        """Enregistre une session utilisateur"""
        self.registry.increment_counter(
            "asmblr_user_sessions_total",
            labels={"status": status}
        )
    
    def set_system_info(self, version: str, environment: str):
        """Définit les informations système"""
        self.registry.set_info(
            "asmblr_system_info",
            {"version": version, "environment": environment}
        )


class SystemMetrics:
    """Métriques système pour Asmblr"""
    
    def __init__(self, registry: PrometheusMetricsRegistry):
        self.registry = registry
        self._setup_system_metrics()
        self._start_collection()
    
    def _setup_system_metrics(self):
        """Configure les métriques système"""
        system_configs = [
            MetricConfig(
                name="asmblr_cpu_usage_percent",
                metric_type=MetricType.GAUGE,
                description="Pourcentage d'utilisation CPU",
                labels=["core"]
            ),
            MetricConfig(
                name="asmblr_memory_usage_bytes",
                metric_type=MetricType.GAUGE,
                description="Utilisation mémoire en bytes",
                labels=["type"]
            ),
            MetricConfig(
                name="asmblr_disk_usage_bytes",
                metric_type=MetricType.GAUGE,
                description="Utilisation disque en bytes",
                labels=["mount_point"]
            ),
            MetricConfig(
                name="asmblr_network_bytes_total",
                metric_type=MetricType.COUNTER,
                description="Total de bytes réseau",
                labels=["direction", "interface"]
            ),
            MetricConfig(
                name="asmblr_process_count",
                metric_type=MetricType.GAUGE,
                description="Nombre de processus",
                labels=["type"]
            ),
            MetricConfig(
                name="asmblr_uptime_seconds",
                metric_type=MetricType.GAUGE,
                description="Uptime du service en secondes"
            )
        ]
        
        for config in system_configs:
            self.registry.register_metric(config)
    
    def _start_collection(self):
        """Démarre la collecte en arrière-plan"""
        def collect_metrics():
            while True:
                try:
                    self._collect_system_metrics()
                except Exception as e:
                    logger.error(f"Erreur lors de la collecte des métriques système: {e}")
                time.sleep(30)  # Collecte toutes les 30 secondes
        
        thread = threading.Thread(target=collect_metrics, daemon=True)
        thread.start()
        logger.info("Collecte des métriques système démarrée")
    
    def _collect_system_metrics(self):
        """Collecte les métriques système"""
        try:
            import psutil
            
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            self.registry.set_gauge("asmblr_cpu_usage_percent", cpu_percent, labels={"core": "total"})
            
            # Mémoire
            memory = psutil.virtual_memory()
            self.registry.set_gauge("asmblr_memory_usage_bytes", memory.used, labels={"type": "used"})
            self.registry.set_gauge("asmblr_memory_usage_bytes", memory.available, labels={"type": "available"})
            
            # Disque
            disk = psutil.disk_usage('/')
            self.registry.set_gauge("asmblr_disk_usage_bytes", disk.used, labels={"mount_point": "/"})
            self.registry.set_gauge("asmblr_disk_usage_bytes", disk.free, labels={"mount_point": "free"})
            
            # Processus
            process_count = len(psutil.pids())
            self.registry.set_gauge("asmblr_process_count", process_count, labels={"type": "total"})
            
        except ImportError:
            logger.warning("psutil non disponible, métriques système désactivées")
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des métriques système: {e}")


class AsmblrMetrics:
    """Point d'entrée principal pour les métriques Asmblr"""
    
    def __init__(self):
        self.registry = PrometheusMetricsRegistry()
        self.business_metrics = BusinessMetrics(self.registry)
        self.system_metrics = SystemMetrics(self.registry)
        self.start_time = time.time()
        
        # Enregistrer les métriques de base
        self._setup_basic_metrics()
    
    def _setup_basic_metrics(self):
        """Configure les métriques de base"""
        basic_configs = [
            MetricConfig(
                name="asmblr_requests_total",
                metric_type=MetricType.COUNTER,
                description="Nombre total de requêtes HTTP",
                labels=["method", "endpoint", "status"]
            ),
            MetricConfig(
                name="asmblr_request_duration_seconds",
                metric_type=MetricType.HISTOGRAM,
                description="Durée des requêtes HTTP",
                labels=["method", "endpoint"],
                buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
            ),
            MetricConfig(
                name="asmblr_errors_total",
                metric_type=MetricType.COUNTER,
                description="Nombre total d'erreurs",
                labels=["type", "component"]
            )
        ]
        
        for config in basic_configs:
            self.registry.register_metric(config)
    
    def record_request(self, method: str, endpoint: str, status: int, duration: float):
        """Enregistre une requête HTTP"""
        self.registry.increment_counter(
            "asmblr_requests_total",
            labels={"method": method, "endpoint": endpoint, "status": str(status)}
        )
        self.registry.observe_histogram(
            "asmblr_request_duration_seconds",
            duration,
            labels={"method": method, "endpoint": endpoint}
        )
        
        if status >= 400:
            self.registry.increment_counter(
                "asmblr_errors_total",
                labels={"type": "http_error", "component": "api"}
            )
    
    def record_error(self, error_type: str, component: str):
        """Enregistre une erreur"""
        self.registry.increment_counter(
            "asmblr_errors_total",
            labels={"type": error_type, "component": component}
        )

    def update_uptime(self):
        """Met à jour l'uptime"""
        uptime = time.time() - self.start_time
        self.registry.set_gauge("asmblr_uptime_seconds", uptime)

    def record_alert(self, name: str, severity: str, status: str):
        """Enregistre une alerte"""
        self.registry.increment_counter(
            "asmblr_alerts_total",
            labels={"name": name, "severity": severity, "status": status}
        )

    def create_metrics_endpoint(self, app: FastAPI):
        """Crée l'endpoint /metrics pour Prometheus"""

        @app.get("/metrics")
        async def metrics():
            """Endpoint Prometheus pour les métriques"""
            self.update_uptime()
            metrics_data = self.registry.generate_metrics()
            return Response(metrics_data, media_type=CONTENT_TYPE_LATEST)
        
        logger.info("Endpoint /metrics configuré pour Prometheus")
    
    def get_metric(self, name: str) -> Optional[Any]:
        """Retourne une métrique par son nom"""
        return self.registry.get_metric(name)
    
    def generate_metrics(self) -> str:
        """Génère les métriques au format Prometheus"""
        return self.registry.generate_metrics()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des métriques"""
        return {
            "registered_metrics": len(self.registry.list_metrics()),
            "metric_names": self.registry.list_metrics(),
            "uptime_seconds": time.time() - self.start_time,
            "business_metrics_count": len(self.registry.metrics),
            "system_metrics_active": True
        }


# Instance globale
ASMblr_METRICS = AsmblrMetrics()


def get_metrics() -> AsmblrMetrics:
    """Retourne l'instance globale des métriques"""
    return ASMblr_METRICS


# Decorateurs pour faciliter l'enregistrement
def track_requests(metric_name: str = None):
    """Décorateur pour tracker les requêtes"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            method = kwargs.get('method', 'unknown')
            endpoint = metric_name or func.__name__
            
            try:
                result = func(*args, **kwargs)
                status = 200
                return result
            except Exception as e:
                status = 500
                ASMblr_METRICS.record_error("function_error", func.__name__)
                raise
            finally:
                duration = time.time() - start_time
                ASMblr_METRICS.record_request(method, endpoint, status, duration)
        
        return wrapper
    return decorator


# Exemples d'utilisation
if __name__ == "__main__":
    # Créer une application FastAPI de test
    app = FastAPI()
    
    # Configurer les métriques
    metrics = get_metrics()
    metrics.create_metrics_endpoint(app)
    
    # Exemple d'enregistrement de métriques
    metrics.record_pipeline_start("venture_creation")
    metrics.record_idea_generation("ai", "high", 5)
    metrics.record_llm_request("llama3.1:8b", "generation", 2.5, "success", 150)
    
    print("Métriques configurées. Accédez à http://localhost:8000/metrics")
