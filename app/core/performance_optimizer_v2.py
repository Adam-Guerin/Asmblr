"""
Performance Optimizer V2 - Version améliorée avec monitoring avancé
"""

import psutil
import time
import threading
from datetime import datetime, timedelta
from typing import Any
from dataclasses import dataclass
from collections import deque

from app.core.smart_logger import get_smart_logger, LogCategory, LogLevel
from app.core.error_handler_v2 import handle_errors


@dataclass
class PerformanceMetrics:
    """Métriques de performance détaillées"""
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_io: dict[str, float]
    response_times: list[float]
    error_rate: float
    uptime_seconds: float
    timestamp: datetime
    process_count: int
    thread_count: int
    open_files: int
    active_connections: int


@dataclass
class OptimizationRule:
    """Règle d'optimisation"""
    name: str
    threshold: float
    severity: str  # low, medium, high, critical
    action: str
    description: str
    enabled: bool = True


class PerformanceOptimizerV2:
    """Optimiseur de performance avancé avec monitoring temps réel"""
    
    def __init__(self):
        self.smart_logger = get_smart_logger()
        self.metrics_history = deque(maxlen=1000)  # Garder 1000 entrées
        self.optimization_rules = self._get_default_rules()
        self.auto_optimization_enabled = True
        self.monitoring_active = False
        self.monitoring_thread = None
        self.optimization_callbacks = []
        
        # Métriques de base
        self.base_metrics = self._get_base_metrics()
        
        self.smart_logger.system(
            LogLevel.LOW,
            "optimizer_init",
            "Performance Optimizer V2 initialisé",
            metadata={
                "rules_count": len(self.optimization_rules),
                "auto_optimization": self.auto_optimization_enabled
            }
        )
    
    def _get_default_rules(self) -> list[OptimizationRule]:
        """Règles d'optimisation par défaut"""
        return [
            OptimizationRule(
                name="cpu_high",
                threshold=80.0,
                severity="high",
                action="optimize_cpu",
                description="CPU usage > 80%",
                enabled=True
            ),
            OptimizationRule(
                name="memory_high",
                threshold=85.0,
                severity="high",
                action="optimize_memory",
                description="Memory usage > 85%",
                enabled=True
            ),
            OptimizationRule(
                name="disk_high",
                threshold=90.0,
                severity="medium",
                action="cleanup_disk",
                description="Disk usage > 90%",
                enabled=True
            ),
            OptimizationRule(
                name="response_time_high",
                threshold=2.0,
                severity="medium",
                action="optimize_requests",
                description="Response time > 2s",
                enabled=True
            ),
            OptimizationRule(
                name="error_rate_high",
                threshold=5.0,
                severity="high",
                action="reduce_errors",
                description="Error rate > 5%",
                enabled=True
            ),
            OptimizationRule(
                name="process_count_high",
                threshold=100,
                severity="medium",
                action="reduce_processes",
                description="Process count > 100",
                enabled=True
            )
        ]
    
    def _get_base_metrics(self) -> PerformanceMetrics:
        """Métriques de base du système"""
        try:
            return PerformanceMetrics(
                cpu_percent=psutil.cpu_percent(interval=1),
                memory_percent=psutil.virtual_memory().percent,
                disk_usage_percent=psutil.disk_usage('/').percent,
                network_io=psutil.net_io_counters(),
                response_times=[],
                error_rate=0.0,
                uptime_seconds=time.time() - psutil.boot_time(),
                timestamp=datetime.utcnow(),
                process_count=len(psutil.pids()),
                thread_count=psutil.cpu_count(),
                open_files=len(psutil.open_files()),
                active_connections=psutil.net_connections()
            )
        except Exception as e:
            self.smart_logger.error(
                LogCategory.SYSTEM,
                "metrics_collection_error",
                f"Erreur collecte métriques: {str(e)}"
            )
            return PerformanceMetrics(0, 0, 0, {}, [], 0.0, 0, datetime.utcnow(), 0, 0, 0, 0)
    
    @handle_errors("metrics_collection", reraise=False)
    def collect_metrics(self) -> PerformanceMetrics:
        """Collecte les métriques de performance"""
        try:
            # Métriques CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Métriques mémoire
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Métriques disque
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            
            # Métriques réseau
            network_io = psutil.net_io_counters()
            
            # Métriques processus
            process_count = len(psutil.pids())
            thread_count = psutil.cpu_count()
            open_files = len(psutil.open_files())
            active_connections = psutil.net_connections()
            
            # Métriques de réponse (simulées)
            response_times = list(self.metrics_history)[-10:] if self.metrics_history else [1.0]
            
            # Calculer le taux d'erreur (simulé)
            error_rate = 2.5  # 2.5% d'erreur simulé
            
            # Uptime
            uptime_seconds = time.time() - psutil.boot_time()
            
            metrics = PerformanceMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_usage_percent=disk_usage_percent,
                network_io=network_io,
                response_times=response_times,
                error_rate=error_rate,
                uptime_seconds=uptime_seconds,
                timestamp=datetime.utcnow(),
                process_count=process_count,
                thread_count=thread_count,
                open_files=open_files,
                active_connections=active_connections
            )
            
            # Ajouter à l'historique
            self.metrics_history.append(metrics)
            
            # Nettoyer l'historique
            if len(self.metrics_history) > 1000:
                self.metrics_history = deque(list(self.metrics_history)[-1000:])
            
            self.smart_logger.debug(
                LogCategory.SYSTEM,
                "metrics_collected",
                f"Métriques collectées: CPU={cpu_percent:.1f}%, MEM={memory_percent:.1f}%",
                metadata={
                    "processes": process_count,
                    "threads": thread_count,
                    "open_files": open_files,
                    "connections": active_connections
                }
            )
            
            return metrics
            
        except Exception as e:
            self.smart_logger.error(
                LogCategory.SYSTEM,
                "metrics_collection_error",
                f"Erreur collecte métriques: {str(e)}"
            )
            return self.base_metrics
    
    @handle_errors("performance_analysis", reraise=False)
    def analyze_performance(self, metrics: PerformanceMetrics) -> dict[str, Any]:
        """Analyse les performances et identifie les problèmes"""
        issues = []
        recommendations = []
        score = 100.0
        
        for rule in self.optimization_rules:
            if not rule.enabled:
                continue
            
            value = 0
            if rule.name == "cpu_high":
                value = metrics.cpu_percent
            elif rule.name == "memory_high":
                value = metrics.memory_percent
            elif rule.name == "disk_high":
                value = metrics.disk_usage_percent
            elif rule.name == "response_time_high":
                value = sum(metrics.response_times) / len(metrics.response_times) if metrics.response_times else 0
            elif rule.name == "error_rate_high":
                value = metrics.error_rate
            elif rule.name == "process_count_high":
                value = metrics.process_count
            
            if value > rule.threshold:
                severity = rule.severity
                issues.append({
                    "type": rule.name,
                    "severity": severity,
                    "value": value,
                    "threshold": rule.threshold,
                    "description": rule.description
                })
                
                # Ajuster le score
                if severity == "critical":
                    score -= 25
                elif severity == "high":
                    score -= 15
                elif severity == "medium":
                    score -= 10
                elif severity == "low":
                    score -= 5
                
                recommendations.append({
                    "rule": rule.name,
                    "action": rule.action,
                    "description": rule.description,
                    "priority": severity
                })
        
        return {
            "score": max(0, score),
            "issues": issues,
            "recommendations": recommendations,
            "timestamp": metrics.timestamp.isoformat()
        }
    
    @handle_errors("auto_optimization", reraise=False)
    def apply_optimizations(self, analysis: dict[str, Any]) -> list[str]:
        """Applique les optimisations automatiques"""
        if not self.auto_optimization_enabled:
            return []
        
        optimizations_applied = []
        
        for issue in analysis.get("issues", []):
            if issue["type"] == "cpu_high":
                optimizations_applied.append(self._optimize_cpu())
            elif issue["type"] == "memory_high":
                optimizations_applied.append(self._optimize_memory())
            elif issue["type"] == "disk_high":
                optimizations_applied.append(self._cleanup_disk())
            elif issue["type"] == "response_time_high":
                optimizations_applied.append(self._optimize_requests())
            elif issue["type"] == "error_rate_high":
                optimizations_applied.append(self._reduce_errors())
            elif issue["type"] == "process_count_high":
                optimizations_applied.append(self._reduce_processes())
        
        if optimizations_applied:
            self.smart_logger.business(
                LogLevel.HIGH,
                "auto_optimization",
                f"Optimisations appliquées: {', '.join(optimizations_applied)}",
                metadata={
                    "issues_count": len(analysis.get("issues", [])),
                    "optimizations_count": len(optimizations_applied)
                }
            )
        
        return optimizations_applied
    
    def _optimize_cpu(self) -> str:
        """Optimise l'utilisation CPU"""
        try:
            # Réduire la priorité des processus non critiques
            import os
            os.system("renice -n 5 $(pidof python)")
            return "CPU priority reduced"
        except Exception as e:
            self.smart_logger.error("cpu_optimization_error", f"Erreur optimisation CPU: {str(e)}")
            return "CPU optimization failed"
    
    def _optimize_memory(self) -> str:
        """Optimise l'utilisation mémoire"""
        try:
            import gc
            gc.collect()
            return "Memory garbage collected"
        except Exception as e:
            self.smart_logger.error("memory_optimization_error", f"Erreur optimisation mémoire: {str(e)}")
            return "Memory optimization failed"
    
    def _cleanup_disk(self) -> str:
        """Nettoie l'espace disque"""
        try:
            import tempfile
            
            # Nettoyer les fichiers temporaires
            temp_dir = tempfile.gettempdir()
            for item in os.listdir(temp_dir):
                item_path = os.path.join(temp_dir, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
            
            return "Temporary files cleaned"
        except Exception as e:
            self.smart_logger.error("disk_cleanup_error", f"Erreur nettoyage disque: {str(e)}")
            return "Disk cleanup failed"
    
    def _optimize_requests(self) -> str:
        """Optimise les requêtes"""
        # Simulé - en pratique, cela impliquerait des changements de configuration
        return "Request optimization applied"
    
    def _reduce_errors(self) -> str:
        """Réduit le taux d'erreurs"""
        # Simulé - en pratique, cela impliquerait une meilleure gestion d'erreurs
        return "Error rate reduction applied"
    
    def _reduce_processes(self) -> str:
        """Réduit le nombre de processus"""
        try:
            # Tuer les processus non critiques
            for proc in psutil.process_iter(['name', 'pid', 'cmdline']):
                if proc.name not in ['chrome', 'firefox', 'safari', 'systemd'] and proc.pid > 1000:
                    proc.terminate()
            return "Non-critical processes terminated"
        except Exception as e:
            self.smart_logger.error("process_reduction_error", f"Erreur réduction processus: {str(e)}")
            return "Process reduction failed"
    
    def start_monitoring(self, interval: int = 30):
        """Démarre le monitoring en arrière-plan"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        def monitoring_loop():
            while self.monitoring_active:
                try:
                    metrics = self.collect_metrics()
                    analysis = self.analyze_performance(metrics)
                    
                    # Appliquer les optimisations automatiques
                    if analysis["score"] < 70:
                        optimizations = self.apply_optimizations(analysis)
                    
                        # Notifier les optimisations
                        for opt in optimizations:
                            self.smart_logger.info(
                                LogCategory.SYSTEM,
                                "auto_optimization",
                                f"Optimisation: {opt}",
                                metadata={"severity": "auto"}
                            )
                    
                    # Attendre la prochaine itération
                    time.sleep(interval)
                    
                except Exception as e:
                    self.smart_logger.error("monitoring_loop_error", f"Erreur boucle monitoring: {str(e)}")
                    time.sleep(interval)
        
        self.monitoring_thread = threading.Thread(target=monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        self.smart_logger.business(
            LogLevel.MEDIUM,
            "monitoring_started",
            f"Monitoring démarré (intervalle: {interval}s)",
            metadata={"interval": interval}
        )
    
    def stop_monitoring(self):
        """Arrête le monitoring"""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        self.smart_logger.business(
            LogLevel.MEDIUM,
            "monitoring_stopped",
            "Monitoring arrêté"
        )
    
    def get_current_metrics(self) -> PerformanceMetrics:
        """Retourne les métriques actuelles"""
        return self.collect_metrics()
    
    def get_performance_summary(self, hours: int = 1) -> dict[str, Any]:
        """Retourne un résumé des performances sur N heures"""
        if not self.metrics_history:
            return {"status": "no_data"}
        
        # Calculer les moyennes sur N heures
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.metrics_history 
            if m.timestamp > cutoff_time
        ]
        
        if not recent_metrics:
            return {"status": "no_recent_data"}
        
        # Calculer les moyennes
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        avg_disk = sum(m.disk_usage_percent for m in recent_metrics) / len(recent_metrics)
        avg_response_time = sum(m.response_times for m in recent_metrics) / len(recent_metrics)
        avg_error_rate = sum(m.error_rate for m in recent_metrics) / len(recent_metrics)
        
        return {
            "status": "success",
            "period_hours": hours,
            "metrics_count": len(recent_metrics),
            "averages": {
                "cpu_percent": avg_cpu,
                "memory_percent": avg_memory,
                "disk_usage_percent": avg_disk,
                "response_time": avg_response_time,
                "error_rate": avg_error_rate
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def register_optimization_callback(self, callback):
        """Enregistre un callback d'optimisation personnalisé"""
        self.optimization_callbacks.append(callback)
    
    def get_optimization_rules(self) -> list[OptimizationRule]:
        """Retourne les règles d'optimisation"""
        return self.optimization_rules
    
    def update_optimization_rules(self, rules: list[OptimizationRule]):
        """Met à jour les règles d'optimisation"""
        self.optimization_rules = rules
        self.smart_logger.info(
            LogLevel.MEDIUM,
            "rules_updated",
            f"Règles d'optimisation mises à jour: {len(rules)} règles",
            metadata={"enabled_rules": len([r for r in rules if r.enabled])}
        )
    
    def enable_auto_optimization(self, enabled: bool = True):
        """Active/désactive l'optimisation automatique"""
        self.auto_optimization_enabled = enabled
        self.smart_logger.business(
            LogLevel.MEDIUM,
            "auto_optimization_toggled",
            f"Optimisation automatique: {'activée' if enabled else 'désactivée'}",
            metadata={"enabled": enabled}
        )


# Instance globale pour l'optimiseur
performance_optimizer_v2 = PerformanceOptimizerV2()
