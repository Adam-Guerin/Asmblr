"""
Système de health checks complets pour Asmblr
Vérification de l'état de tous les composants du système
"""

import asyncio
import time
import psutil
import subprocess
import requests
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import logging

from app.core.config import Settings
from app.core.llm import LLMClient
from app.core.cache import ArtifactCache
from app.monitoring.prometheus_metrics import AsmblrMetrics
from app.monitoring.structured_logger import StructuredLogger


class HealthStatus(Enum):
    """Statuts de santé"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class CheckType(Enum):
    """Types de checks"""
    SYSTEM = "system"
    APPLICATION = "application"
    EXTERNAL = "external"
    DATABASE = "database"
    CACHE = "cache"
    NETWORK = "network"


@dataclass
class HealthCheck:
    """Résultat d'un health check"""
    name: str
    type: CheckType
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)
    critical: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir en dictionnaire"""
        return {
            "name": self.name,
            "type": self.type.value,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
            "critical": self.critical
        }


class HealthChecker:
    """Gestionnaire de health checks pour Asmblr"""
    
    def __init__(
        self,
        settings: Settings,
        metrics: AsmblrMetrics,
        logger: StructuredLogger
    ):
        self.settings = settings
        self.metrics = metrics
        self.logger = logger
        self.checks: Dict[str, Callable] = {}
        self.last_results: Dict[str, HealthCheck] = {}
        
        # Enregistrer les checks par défaut
        self._register_default_checks()
    
    def _register_default_checks(self):
        """Enregistrer les checks par défaut"""
        self.register_check("system_cpu", self.check_system_cpu, CheckType.SYSTEM)
        self.register_check("system_memory", self.check_system_memory, CheckType.SYSTEM)
        self.register_check("system_disk", self.check_system_disk, CheckType.SYSTEM)
        self.register_check("application_config", self.check_application_config, CheckType.APPLICATION)
        self.register_check("cache_status", self.check_cache_status, CheckType.CACHE)
        self.register_check("ollama_service", self.check_ollama_service, CheckType.EXTERNAL)
        self.register_check("prometheus_metrics", self.check_prometheus_metrics, CheckType.APPLICATION)
        self.register_check("logging_system", self.check_logging_system, CheckType.APPLICATION)
    
    def register_check(
        self,
        name: str,
        check_func: Callable,
        check_type: CheckType,
        critical: bool = True
    ):
        """Enregistrer un nouveau health check"""
        self.checks[name] = {
            "func": check_func,
            "type": check_type,
            "critical": critical
        }
        self.logger.system(f"Registered health check: {name}")
    
    async def run_all_checks(self) -> Dict[str, HealthCheck]:
        """Exécuter tous les health checks"""
        results = {}
        
        for check_name, check_info in self.checks.items():
            try:
                start_time = time.time()
                result = await self._run_single_check(check_name, check_info)
                duration_ms = (time.time() - start_time) * 1000
                result.duration_ms = duration_ms
                
                results[check_name] = result
                self.last_results[check_name] = result
                
                # Mettre à jour les métriques
                self.metrics.system_metrics.record_health_check(
                    check_name, result.status.value
                )
                
            except Exception as e:
                error_result = HealthCheck(
                    name=check_name,
                    type=check_info["type"],
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check execution failed: {str(e)}",
                    critical=check_info["critical"]
                )
                results[check_name] = error_result
                self.last_results[check_name] = error_result
                
                self.logger.error(f"Health check {check_name} failed: {e}")
        
        return results
    
    async def _run_single_check(self, name: str, check_info: Dict) -> HealthCheck:
        """Exécuter un seul health check"""
        check_func = check_info["func"]
        check_type = check_info["type"]
        critical = check_info["critical"]
        
        try:
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()
            
            if isinstance(result, HealthCheck):
                result.critical = critical
                return result
            else:
                # Si le check retourne juste un booléen
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                message = "Check passed" if result else "Check failed"
                
                return HealthCheck(
                    name=name,
                    type=check_type,
                    status=status,
                    message=message,
                    critical=critical
                )
                
        except Exception as e:
            return HealthCheck(
                name=name,
                type=check_type,
                status=HealthStatus.UNHEALTHY,
                message=f"Check error: {str(e)}",
                critical=critical
            )
    
    def get_overall_status(self, results: Dict[str, HealthCheck]) -> HealthStatus:
        """Calculer le statut global"""
        if not results:
            return HealthStatus.UNKNOWN
        
        critical_checks = [r for r in results.values() if r.critical]
        critical_failed = [r for r in critical_checks if r.status == HealthStatus.UNHEALTHY]
        
        if critical_failed:
            return HealthStatus.UNHEALTHY
        
        degraded_checks = [r for r in results.values() if r.status == HealthStatus.DEGRADED]
        if degraded_checks:
            return HealthStatus.DEGRADED
        
        return HealthStatus.HEALTHY
    
    # Checks système
    async def check_system_cpu(self) -> HealthCheck:
        """Vérifier l'utilisation CPU"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = psutil.getloadavg()
            
            details = {
                "cpu_percent": cpu_percent,
                "cpu_count": cpu_count,
                "load_1min": load_avg[0],
                "load_5min": load_avg[1],
                "load_15min": load_avg[2]
            }
            
            if cpu_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"CPU usage critically high: {cpu_percent}%"
            elif cpu_percent > 80:
                status = HealthStatus.DEGRADED
                message = f"CPU usage high: {cpu_percent}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"CPU usage normal: {cpu_percent}%"
            
            return HealthCheck(
                name="system_cpu",
                type=CheckType.SYSTEM,
                status=status,
                message=message,
                details=details
            )
            
        except Exception as e:
            return HealthCheck(
                name="system_cpu",
                type=CheckType.SYSTEM,
                status=HealthStatus.UNHEALTHY,
                message=f"CPU check failed: {str(e)}"
            )
    
    async def check_system_memory(self) -> HealthCheck:
        """Vérifier l'utilisation mémoire"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            details = {
                "memory_total": memory.total,
                "memory_available": memory.available,
                "memory_percent": memory.percent,
                "memory_used": memory.used,
                "memory_free": memory.free,
                "swap_total": swap.total,
                "swap_used": swap.used,
                "swap_percent": swap.percent
            }
            
            if memory.percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"Memory usage critically high: {memory.percent}%"
            elif memory.percent > 80:
                status = HealthStatus.DEGRADED
                message = f"Memory usage high: {memory.percent}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Memory usage normal: {memory.percent}%"
            
            return HealthCheck(
                name="system_memory",
                type=CheckType.SYSTEM,
                status=status,
                message=message,
                details=details
            )
            
        except Exception as e:
            return HealthCheck(
                name="system_memory",
                type=CheckType.SYSTEM,
                status=HealthStatus.UNHEALTHY,
                message=f"Memory check failed: {str(e)}"
            )
    
    async def check_system_disk(self) -> HealthCheck:
        """Vérifier l'espace disque"""
        try:
            # Vérifier le disque principal
            disk = psutil.disk_usage('/')
            
            details = {
                "disk_total": disk.total,
                "disk_used": disk.used,
                "disk_free": disk.free,
                "disk_percent": (disk.used / disk.total) * 100
            }
            
            disk_percent = (disk.used / disk.total) * 100
            
            if disk_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"Disk usage critically high: {disk_percent:.1f}%"
            elif disk_percent > 80:
                status = HealthStatus.DEGRADED
                message = f"Disk usage high: {disk_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Disk usage normal: {disk_percent:.1f}%"
            
            return HealthCheck(
                name="system_disk",
                type=CheckType.SYSTEM,
                status=status,
                message=message,
                details=details
            )
            
        except Exception as e:
            return HealthCheck(
                name="system_disk",
                type=CheckType.SYSTEM,
                status=HealthStatus.UNHEALTHY,
                message=f"Disk check failed: {str(e)}"
            )
    
    # Checks application
    async def check_application_config(self) -> HealthCheck:
        """Vérifier la configuration de l'application"""
        try:
            required_settings = [
                'ollama_base_url',
                'general_model',
                'default_n_ideas'
            ]
            
            missing_settings = []
            for setting in required_settings:
                if not hasattr(self.settings, setting) or not getattr(self.settings, setting):
                    missing_settings.append(setting)
            
            details = {
                "required_settings": required_settings,
                "missing_settings": missing_settings,
                "settings_count": len(vars(self.settings))
            }
            
            if missing_settings:
                status = HealthStatus.UNHEALTHY
                message = f"Missing required settings: {', '.join(missing_settings)}"
            else:
                status = HealthStatus.HEALTHY
                message = "Application configuration valid"
            
            return HealthCheck(
                name="application_config",
                type=CheckType.APPLICATION,
                status=status,
                message=message,
                details=details
            )
            
        except Exception as e:
            return HealthCheck(
                name="application_config",
                type=CheckType.APPLICATION,
                status=HealthStatus.UNHEALTHY,
                message=f"Config check failed: {str(e)}"
            )
    
    async def check_cache_status(self) -> HealthCheck:
        """Vérifier le statut du cache"""
        try:
            # Créer une instance de cache pour le test
            cache = ArtifactCache(max_size=10, ttl_seconds=60)
            
            # Test d'écriture
            test_key = "health_check_test"
            test_value = {"test": True, "timestamp": time.time()}
            cache.set(test_key, test_value)
            
            # Test de lecture
            retrieved_value = cache.get(test_key)
            
            # Nettoyer
            cache.delete(test_key)
            
            details = {
                "cache_type": "ArtifactCache",
                "write_test": retrieved_value is not None,
                "read_test": retrieved_value == test_value,
                "cache_size": cache.size()
            }
            
            if retrieved_value == test_value:
                status = HealthStatus.HEALTHY
                message = "Cache system working correctly"
            else:
                status = HealthStatus.UNHEALTHY
                message = "Cache system malfunctioning"
            
            return HealthCheck(
                name="cache_status",
                type=CheckType.CACHE,
                status=status,
                message=message,
                details=details
            )
            
        except Exception as e:
            return HealthCheck(
                name="cache_status",
                type=CheckType.CACHE,
                status=HealthStatus.UNHEALTHY,
                message=f"Cache check failed: {str(e)}"
            )
    
    async def check_ollama_service(self) -> HealthCheck:
        """Vérifier le service Ollama"""
        try:
            ollama_url = self.settings.ollama_base_url
            
            # Test de connexion
            response = requests.get(f"{ollama_url}/api/tags", timeout=5)
            
            details = {
                "ollama_url": ollama_url,
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                details["available_models"] = len(models)
                details["model_names"] = [model.get("name") for model in models[:5]]  # Top 5
                
                status = HealthStatus.HEALTHY
                message = f"Ollama service available with {len(models)} models"
            else:
                status = HealthStatus.UNHEALTHY
                message = f"Ollama service returned status {response.status_code}"
            
            return HealthCheck(
                name="ollama_service",
                type=CheckType.EXTERNAL,
                status=status,
                message=message,
                details=details
            )
            
        except requests.exceptions.Timeout:
            return HealthCheck(
                name="ollama_service",
                type=CheckType.EXTERNAL,
                status=HealthStatus.UNHEALTHY,
                message="Ollama service timeout"
            )
        except Exception as e:
            return HealthCheck(
                name="ollama_service",
                type=CheckType.EXTERNAL,
                status=HealthStatus.UNHEALTHY,
                message=f"Ollama check failed: {str(e)}"
            )
    
    async def check_prometheus_metrics(self) -> HealthCheck:
        """Vérifier les métriques Prometheus"""
        try:
            # Vérifier que les métriques sont générées
            metrics_output = self.metrics.generate_metrics()
            
            details = {
                "metrics_length": len(metrics_output),
                "registered_metrics": len(self.metrics.registry.list_metrics()),
                "sample_metrics": metrics_output[:500]  # Premier 500 caractères
            }
            
            if metrics_output and "asmblr_" in metrics_output:
                status = HealthStatus.HEALTHY
                message = "Prometheus metrics working correctly"
            else:
                status = HealthStatus.DEGRADED
                message = "Prometheus metrics may not be fully configured"
            
            return HealthCheck(
                name="prometheus_metrics",
                type=CheckType.APPLICATION,
                status=status,
                message=message,
                details=details
            )
            
        except Exception as e:
            return HealthCheck(
                name="prometheus_metrics",
                type=CheckType.APPLICATION,
                status=HealthStatus.UNHEALTHY,
                message=f"Prometheus metrics check failed: {str(e)}"
            )
    
    async def check_logging_system(self) -> HealthCheck:
        """Vérifier le système de logging"""
        try:
            # Test d'écriture de log
            test_message = "Health check test message"
            self.logger.system(test_message)
            
            # Vérifier que le logger est configuré
            details = {
                "logger_name": self.logger.logger.name,
                "logger_level": self.logger.logger.level,
                "test_message": test_message,
                "handlers_count": len(self.logger.logger.handlers)
            }
            
            status = HealthStatus.HEALTHY
            message = "Logging system working correctly"
            
            return HealthCheck(
                name="logging_system",
                type=CheckType.APPLICATION,
                status=status,
                message=message,
                details=details
            )
            
        except Exception as e:
            return HealthCheck(
                name="logging_system",
                type=CheckType.APPLICATION,
                status=HealthStatus.UNHEALTHY,
                message=f"Logging system check failed: {str(e)}"
            )
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Obtenir un résumé de la santé du système"""
        if not self.last_results:
            return {
                "status": HealthStatus.UNKNOWN.value,
                "timestamp": time.time(),
                "checks": {},
                "summary": "No health checks have been run"
            }
        
        overall_status = self.get_overall_status(self.last_results)
        
        # Compter par statut
        status_counts = {}
        for check in self.last_results.values():
            status = check.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Checks critiques
        critical_checks = [name for name, check in self.last_results.items() if check.critical]
        failed_critical = [name for name, check in self.last_results.items() 
                          if check.critical and check.status == HealthStatus.UNHEALTHY]
        
        return {
            "status": overall_status.value,
            "timestamp": time.time(),
            "checks": {name: check.to_dict() for name, check in self.last_results.items()},
            "summary": {
                "total_checks": len(self.last_results),
                "status_counts": status_counts,
                "critical_checks": len(critical_checks),
                "failed_critical": len(failed_critical),
                "critical_failed_names": failed_critical
            }
        }


# Endpoint FastAPI pour les health checks
async def health_endpoint(checker: HealthChecker) -> Dict[str, Any]:
    """Endpoint FastAPI pour les health checks"""
    results = await checker.run_all_checks()
    summary = checker.get_health_summary()
    
    return {
        "status": summary["status"],
        "timestamp": summary["timestamp"],
        "checks": {name: check.to_dict() for name, check in results.items()},
        "summary": summary["summary"]
    }


async def readiness_endpoint(checker: HealthChecker) -> Dict[str, Any]:
    """Endpoint de readiness (vérifie seulement les checks critiques)"""
    results = await checker.run_all_checks()
    
    critical_checks = {name: check for name, check in results.items() if check.critical}
    critical_failed = [name for name, check in critical_checks.items() 
                      if check.status == HealthStatus.UNHEALTHY]
    
    status = HealthStatus.HEALTHY if not critical_failed else HealthStatus.UNHEALTHY
    
    return {
        "status": status.value,
        "timestamp": time.time(),
        "critical_checks": {name: check.to_dict() for name, check in critical_checks.items()},
        "failed_critical": critical_failed,
        "ready": len(critical_failed) == 0
    }


async def liveness_endpoint() -> Dict[str, Any]:
    """Endpoint de liveness (vérifie que l'application est en vie)"""
    return {
        "status": HealthStatus.HEALTHY.value,
        "timestamp": time.time(),
        "message": "Application is alive"
    }


# Configuration pour le monitoring
def configure_health_checks(
    settings: Settings,
    metrics: AsmblrMetrics,
    logger: StructuredLogger
) -> HealthChecker:
    """Configurer les health checks"""
    checker = HealthChecker(settings, metrics, logger)
    
    # Ajouter des checks spécifiques à Asmblr
    async def check_mvp_directories() -> HealthCheck:
        """Vérifier les répertoires MVP"""
        try:
            runs_dir = Path(settings.runs_dir)
            data_dir = Path(settings.data_dir)
            
            details = {
                "runs_dir_exists": runs_dir.exists(),
                "runs_dir_writable": runs_dir.exists() and os.access(runs_dir, os.W_OK),
                "data_dir_exists": data_dir.exists(),
                "data_dir_writable": data_dir.exists() and os.access(data_dir, os.W_OK)
            }
            
            all_good = all(details.values())
            status = HealthStatus.HEALTHY if all_good else HealthStatus.DEGRADED
            message = "MVP directories accessible" if all_good else "Some MVP directories have issues"
            
            return HealthCheck(
                name="mvp_directories",
                type=CheckType.APPLICATION,
                status=status,
                message=message,
                details=details
            )
            
        except Exception as e:
            return HealthCheck(
                name="mvp_directories",
                type=CheckType.APPLICATION,
                status=HealthStatus.UNHEALTHY,
                message=f"MVP directories check failed: {str(e)}"
            )
    
    checker.register_check("mvp_directories", check_mvp_directories, CheckType.APPLICATION)
    
    return checker
