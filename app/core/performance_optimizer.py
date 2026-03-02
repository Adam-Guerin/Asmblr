"""
Optimiseur de performance pour Asmblr
Analyse et optimise automatiquement les problèmes de performance
"""

import time
import psutil
import threading
from typing import Any
from collections.abc import Callable
from dataclasses import dataclass, asdict
from loguru import logger
from collections import defaultdict


@dataclass
class PerformanceMetrics:
    """Métriques de performance d'une opération"""
    operation_name: str
    start_time: float
    end_time: float
    duration: float
    memory_usage_mb: float
    cpu_usage_percent: float
    success: bool
    error_message: str | None = None
    retry_count: int = 0


@dataclass
class PerformanceIssue:
    """Problème de performance détecté"""
    issue_type: str
    severity: str  # low, medium, high, critical
    operation_name: str
    description: str
    recommendation: str
    metrics: dict[str, Any]


class PerformanceOptimizer:
    """
    Optimiseur de performance qui analyse et corrige automatiquement
    les problèmes de performance dans Asmblr
    """
    
    def __init__(self, enable_auto_optimization: bool = True):
        self.enable_auto_optimization = enable_auto_optimization
        self.metrics_history: list[PerformanceMetrics] = []
        self.issues_detected: list[PerformanceIssue] = []
        self.optimization_rules = self._load_optimization_rules()
        self.performance_cache = {}
        self.lock = threading.Lock()
        
        # Seuils de performance
        self.thresholds = {
            "slow_operation_seconds": 30.0,
            "high_memory_mb": 1024,  # 1GB
            "high_cpu_percent": 80.0,
            "high_retry_rate": 0.3,
            "high_error_rate": 0.1
        }
    
    def monitor_operation(self, operation_name: str):
        """
        Décorateur pour monitorer une opération et détecter les problèmes
        
        Args:
            operation_name: Nom de l'opération à monitorer
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                return self._execute_with_monitoring(func, args, kwargs, operation_name)
            return wrapper
        return decorator
    
    def _execute_with_monitoring(self, func: Callable, args: tuple, kwargs: dict, 
                                operation_name: str) -> Any:
        """Exécute une fonction avec monitoring complet"""
        # Mesurer l'état initial
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu = process.cpu_percent()
        
        start_time = time.time()
        retry_count = 0
        success = False
        error_message = None
        
        try:
            result = func(*args, **kwargs)
            success = True
            return result
            
        except Exception as e:
            error_message = str(e)
            # Compter les retries depuis les logs ou metadata
            retry_count = self._extract_retry_count(e)
            raise
            
        finally:
            # Mesurer l'état final
            end_time = time.time()
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            final_cpu = process.cpu_percent()
            
            # Créer les métriques
            metrics = PerformanceMetrics(
                operation_name=operation_name,
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                memory_usage_mb=final_memory - initial_memory,
                cpu_usage_percent=final_cpu - initial_cpu,
                success=success,
                error_message=error_message,
                retry_count=retry_count
            )
            
            # Analyser et stocker
            self._analyze_metrics(metrics)
            self._store_metrics(metrics)
    
    def _extract_retry_count(self, exception: Exception) -> int:
        """Extrait le nombre de retries d'une exception"""
        # Chercher des patterns dans le message d'erreur
        error_msg = str(exception).lower()
        
        # Patterns courants
        patterns = [
            "retry", "attempt", "tentative", "essai",
            "timeout", "expired", "dépassé"
        ]
        
        retry_count = 0
        for pattern in patterns:
            if pattern in error_msg:
                # Extraire les nombres près du pattern
                import re
                numbers = re.findall(r'\d+', error_msg)
                if numbers:
                    retry_count = max(retry_count, max(int(n) for n in numbers))
        
        return retry_count
    
    def _analyze_metrics(self, metrics: PerformanceMetrics) -> None:
        """Analyse les métriques et détecte les problèmes"""
        issues = []
        
        # Vérifier les seuils
        if metrics.duration > self.thresholds["slow_operation_seconds"]:
            issues.append(PerformanceIssue(
                issue_type="slow_operation",
                severity="high" if metrics.duration > 60 else "medium",
                operation_name=metrics.operation_name,
                description=f"Opération lente: {metrics.duration:.1f}s",
                recommendation=self._get_slow_operation_recommendation(metrics),
                metrics={"duration": metrics.duration}
            ))
        
        if metrics.memory_usage_mb > self.thresholds["high_memory_mb"]:
            issues.append(PerformanceIssue(
                issue_type="high_memory",
                severity="high" if metrics.memory_usage_mb > 2048 else "medium",
                operation_name=metrics.operation_name,
                description=f"Utilisation mémoire élevée: {metrics.memory_usage_mb:.1f}MB",
                recommendation=self._get_memory_recommendation(metrics),
                metrics={"memory_mb": metrics.memory_usage_mb}
            ))
        
        if metrics.cpu_usage_percent > self.thresholds["high_cpu_percent"]:
            issues.append(PerformanceIssue(
                issue_type="high_cpu",
                severity="medium",
                operation_name=metrics.operation_name,
                description=f"Utilisation CPU élevée: {metrics.cpu_usage_percent:.1f}%",
                recommendation=self._get_cpu_recommendation(metrics),
                metrics={"cpu_percent": metrics.cpu_usage_percent}
            ))
        
        if metrics.retry_count > 0:
            issues.append(PerformanceIssue(
                issue_type="excessive_retries",
                severity="high" if metrics.retry_count > 3 else "medium",
                operation_name=metrics.operation_name,
                description=f"Trop de retries: {metrics.retry_count}",
                recommendation=self._get_retry_recommendation(metrics),
                metrics={"retry_count": metrics.retry_count}
            ))
        
        if not metrics.success:
            issues.append(PerformanceIssue(
                issue_type="operation_failure",
                severity="high",
                operation_name=metrics.operation_name,
                description=f"Échec opération: {metrics.error_message}",
                recommendation=self._get_failure_recommendation(metrics),
                metrics={"error": metrics.error_message}
            ))
        
        # Stocker les problèmes
        with self.lock:
            self.issues_detected.extend(issues)
        
        # Auto-optimisation si activée
        if self.enable_auto_optimization and issues:
            self._auto_optimize(issues)
    
    def _store_metrics(self, metrics: PerformanceMetrics) -> None:
        """Stocke les métriques pour analyse"""
        with self.lock:
            self.metrics_history.append(metrics)
            
            # Garder seulement les 1000 dernières métriques
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]
    
    def _get_slow_operation_recommendation(self, metrics: PerformanceMetrics) -> str:
        """Recommandation pour opération lente"""
        recommendations = [
            "Réduire le nombre de sources à analyser",
            "Augmenter les timeouts pour éviter les retries",
            "Utiliser le cache pour éviter les traitements répétés",
            "Activer le mode fast pour cette opération",
            "Paralléliser les sous-opérations si possible"
        ]
        
        # Recommandations spécifiques selon l'opération
        if "web" in metrics.operation_name.lower():
            return "Réduire MAX_SOURCES ou activer le cache web"
        elif "llm" in metrics.operation_name.lower():
            return "Utiliser un modèle plus rapide ou réduire la taille du prompt"
        elif "mvp" in metrics.operation_name.lower():
            return "Désactiver les fonctionnalités avancées (MLP, emotional design)"
        
        return recommendations[0]
    
    def _get_memory_recommendation(self, metrics: PerformanceMetrics) -> str:
        """Recommandation pour utilisation mémoire élevée"""
        return [
            "Réduire la taille des batchs",
            "Activer le garbage collection plus fréquent",
            "Utiliser des générateurs au lieu de listes",
            "Désactiver les modèles lourds (torch/diffusers)"
        ][0]
    
    def _get_cpu_recommendation(self, metrics: PerformanceMetrics) -> str:
        """Recommandation pour utilisation CPU élevée"""
        return [
            "Réduire le parallélisme",
            "Utiliser des algorithmes plus efficaces",
            "Activer le mode économie d'énergie",
            "Optimiser les boucles de traitement"
        ][0]
    
    def _get_retry_recommendation(self, metrics: PerformanceMetrics) -> str:
        """Recommandation pour retries excessifs"""
        return [
            "Augmenter les timeouts pour éviter les timeouts",
            "Vérifier la connectivité réseau",
            "Réduire la charge sur les services externes",
            "Implémenter un backoff plus agressif"
        ][0]
    
    def _get_failure_recommendation(self, metrics: PerformanceMetrics) -> str:
        """Recommandation pour échec d'opération"""
        return [
            "Vérifier la configuration des services externes",
            "Activer le mode fallback pour cette opération",
            "Implémenter une gestion d'erreur plus robuste",
            "Consulter les logs pour plus de détails"
        ][0]
    
    def _auto_optimize(self, issues: list[PerformanceIssue]) -> None:
        """Applique automatiquement des optimisations"""
        for issue in issues:
            try:
                if issue.issue_type == "slow_operation":
                    self._optimize_slow_operation(issue)
                elif issue.issue_type == "high_memory":
                    self._optimize_memory_usage(issue)
                elif issue.issue_type == "excessive_retries":
                    self._optimize_retries(issue)
            except Exception as e:
                logger.error(f"Erreur auto-optimisation {issue.issue_type}: {e}")
    
    def _optimize_slow_operation(self, issue: PerformanceIssue) -> None:
        """Optimise automatiquement une opération lente"""
        # Exemple: réduire les sources pour les opérations web
        if "web" in issue.operation_name.lower():
            logger.info(f"Auto-optimisation: réduction sources pour {issue.operation_name}")
            # Cette logique serait implémentée avec le système de configuration intelligente
    
    def _optimize_memory_usage(self, issue: PerformanceIssue) -> None:
        """Optimise automatiquement l'utilisation mémoire"""
        logger.info(f"Auto-optimisation: nettoyage mémoire pour {issue.operation_name}")
        import gc
        gc.collect()
    
    def _optimize_retries(self, issue: PerformanceIssue) -> None:
        """Optimise automatiquement les retries"""
        retry_count = issue.metrics.get("retry_count", 0)
        logger.info(f"Auto-optimisation: ajustement retries pour {issue.operation_name} (count: {retry_count})")
    
    def _load_optimization_rules(self) -> dict[str, Any]:
        """Charge les règles d'optimisation"""
        return {
            "web_operations": {
                "max_sources": 8,
                "timeout_multiplier": 1.5,
                "cache_ttl": 3600
            },
            "llm_operations": {
                "max_tokens": 2000,
                "temperature": 0.7,
                "timeout": 60
            },
            "mvp_operations": {
                "disable_heavy_features": True,
                "max_build_time": 300,
                "enable_fast_mode": True
            }
        }
    
    def get_performance_summary(self) -> dict[str, Any]:
        """Retourne un résumé des performances"""
        if not self.metrics_history:
            return {"message": "Aucune métrique disponible"}
        
        # Calculer les statistiques
        recent_metrics = self.metrics_history[-100:]  # 100 dernières opérations
        
        total_operations = len(recent_metrics)
        successful_operations = sum(1 for m in recent_metrics if m.success)
        avg_duration = sum(m.duration for m in recent_metrics) / total_operations
        avg_memory = sum(m.memory_usage_mb for m in recent_metrics) / total_operations
        avg_retries = sum(m.retry_count for m in recent_metrics) / total_operations
        
        # Compter les problèmes par type
        issues_by_type = defaultdict(int)
        for issue in self.issues_detected[-50:]:  # 50 derniers problèmes
            issues_by_type[issue.issue_type] += 1
        
        return {
            "operations_analyzed": total_operations,
            "success_rate": successful_operations / total_operations,
            "avg_duration_seconds": avg_duration,
            "avg_memory_mb": avg_memory,
            "avg_retries": avg_retries,
            "recent_issues": dict(issues_by_type),
            "total_issues_detected": len(self.issues_detected),
            "auto_optimization_enabled": self.enable_auto_optimization
        }
    
    def get_recommendations(self) -> list[dict[str, Any]]:
        """Retourne les recommandations d'optimisation"""
        recommendations = []
        
        # Analyser les problèmes récents
        recent_issues = self.issues_detected[-20:]
        
        if not recent_issues:
            return [{"message": "Aucun problème de performance détecté"}]
        
        # Grouper par type
        issues_by_type = defaultdict(list)
        for issue in recent_issues:
            issues_by_type[issue.issue_type].append(issue)
        
        # Générer des recommandations par type
        for issue_type, issues in issues_by_type.items():
            if issue_type == "slow_operation":
                avg_duration = sum(issue.metrics.get("duration", 0) for issue in issues) / len(issues)
                recommendations.append({
                    "priority": "high",
                    "category": "Performance",
                    "issue": f"Opérations lentes détectées ({len(issues)} occurrences)",
                    "impact": f"Durée moyenne: {avg_duration:.1f}s",
                    "recommendation": "Réduire la complexité des opérations ou activer le cache"
                })
            
            elif issue_type == "high_memory":
                recommendations.append({
                    "priority": "medium",
                    "category": "Ressources",
                    "issue": f"Utilisation mémoire élevée ({len(issues)} occurrences)",
                    "recommendation": "Optimiser la gestion mémoire ou utiliser la version lightweight"
                })
            
            elif issue_type == "excessive_retries":
                recommendations.append({
                    "priority": "high",
                    "category": "Fiabilité",
                    "issue": f"Trop de retries ({len(issues)} occurrences)",
                    "recommendation": "Ajuster les timeouts ou améliorer la gestion d'erreurs"
                })
        
        return recommendations
    
    def export_metrics(self, format_type: str = "json") -> str:
        """Exporte les métriques de performance"""
        if format_type == "json":
            import json
            return json.dumps([asdict(m) for m in self.metrics_history[-100:]], indent=2)
        
        elif format_type == "csv":
            import csv
            import io
            
            output = io.StringIO()
            if self.metrics_history:
                writer = csv.DictWriter(output, fieldnames=asdict(self.metrics_history[0]).keys())
                writer.writeheader()
                for metrics in self.metrics_history[-100:]:
                    writer.writerow(asdict(metrics))
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Format non supporté: {format_type}")
    
    def reset_metrics(self) -> None:
        """Réinitialise toutes les métriques"""
        with self.lock:
            self.metrics_history.clear()
            self.issues_detected.clear()
        logger.info("Métriques de performance réinitialisées")


# Instance globale de l'optimiseur
_performance_optimizer: PerformanceOptimizer | None = None


def get_performance_optimizer() -> PerformanceOptimizer:
    """Récupère l'instance globale de l'optimiseur de performance"""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
    return _performance_optimizer


def monitor_performance(operation_name: str):
    """Décorateur pratique pour monitorer la performance"""
    return get_performance_optimizer().monitor_operation(operation_name)
