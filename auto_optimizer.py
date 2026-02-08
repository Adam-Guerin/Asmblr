"""
Auto-Optimization Engine pour Asmblr
Optimisation automatique des performances et des ressources
"""

import os
import asyncio
import json
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from contextlib import asynccontextmanager

import redis.asyncio as redis
from loguru import logger
from prometheus_client import Gauge, Counter, Histogram

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
OPTIMIZATION_INTERVAL = int(os.getenv("OPTIMIZATION_INTERVAL", "60"))  # secondes
ENABLE_AUTO_OPTIMIZATION = os.getenv("ENABLE_AUTO_OPTIMIZATION", "true").lower() == "true"

# Métriques d'optimisation
OPTIMIZATION_CYCLES = Counter('asmblr_optimization_cycles_total', 'Optimization cycles')
RESOURCE_USAGE = Gauge('asmblr_resource_usage_percent', 'Resource usage', ['resource'])
PERFORMANCE_SCORE = Gauge('asmblr_performance_score', 'Overall performance score')
OPTIMIZATION_ACTIONS = Counter('asmblr_optimization_actions_total', 'Optimization actions', ['action_type'])


@dataclass
class SystemMetrics:
    """Métriques système"""
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    disk_usage_percent: float
    active_connections: int
    response_time_avg: float
    error_rate: float
    throughput: float
    timestamp: datetime


@dataclass
class OptimizationAction:
    """Action d'optimisation"""
    action_type: str
    description: str
    impact: str
    timestamp: datetime
    metrics_before: Dict[str, float]
    metrics_after: Optional[Dict[str, float]] = None


class ResourceOptimizer:
    """Optimiseur de ressources"""
    
    def __init__(self):
        self.redis_client = None
        self.optimization_history: List[OptimizationAction] = []
        self.baseline_metrics: Optional[SystemMetrics] = None
        
    async def initialize(self):
        """Initialise l'optimiseur"""
        try:
            self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
            await self.redis_client.ping()
            logger.info("Resource optimizer initialized")
        except Exception as e:
            logger.warning(f"Redis not available for optimizer: {e}")
            self.redis_client = None
    
    async def collect_metrics(self) -> SystemMetrics:
        """Collecte les métriques système"""
        # Métriques CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Métriques mémoire
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_gb = memory.available / (1024**3)
        
        # Métriques disque
        disk = psutil.disk_usage('/')
        disk_usage_percent = disk.percent
        
        # Métriques réseau (simplifié)
        active_connections = len(psutil.net_connections())
        
        # Métriques application (à récupérer depuis les services)
        response_time_avg = await self.get_avg_response_time()
        error_rate = await self.get_error_rate()
        throughput = await self.get_throughput()
        
        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_available_gb=memory_available_gb,
            disk_usage_percent=disk_usage_percent,
            active_connections=active_connections,
            response_time_avg=response_time_avg,
            error_rate=error_rate,
            throughput=throughput,
            timestamp=datetime.utcnow()
        )
    
    async def get_avg_response_time(self) -> float:
        """Récupère le temps de réponse moyen"""
        if not self.redis_client:
            return 0.5  # Valeur par défaut
        
        try:
            # Récupérer les métriques depuis Redis
            response_times = await self.redis_client.lrange("metrics:response_times", 0, -1)
            if response_times:
                times = [float(rt) for rt in response_times[-100:]]  # Dernières 100 valeurs
                return sum(times) / len(times)
        except Exception as e:
            logger.error(f"Failed to get response times: {e}")
        
        return 0.5  # Valeur par défaut
    
    async def get_error_rate(self) -> float:
        """Récupère le taux d'erreur"""
        if not self.redis_client:
            return 0.01  # Valeur par défaut
        
        try:
            total_requests = await self.redis_client.get("metrics:total_requests") or "0"
            error_requests = await self.redis_client.get("metrics:error_requests") or "0"
            
            if int(total_requests) > 0:
                return int(error_requests) / int(total_requests)
        except Exception as e:
            logger.error(f"Failed to get error rate: {e}")
        
        return 0.01  # Valeur par défaut
    
    async def get_throughput(self) -> float:
        """Récupère le débit (requêtes/seconde)"""
        if not self.redis_client:
            return 10.0  # Valeur par défaut
        
        try:
            # Récupérer les requêtes par minute
            current_minute = datetime.utcnow().strftime("%Y%m%d%H%M")
            requests = await self.redis_client.get(f"metrics:requests:{current_minute}") or "0"
            return int(requests) / 60.0
        except Exception as e:
            logger.error(f"Failed to get throughput: {e}")
        
        return 10.0  # Valeur par défaut
    
    def calculate_performance_score(self, metrics: SystemMetrics) -> float:
        """Calcule un score de performance (0-100)"""
        score = 100.0
        
        # Pénalités CPU
        if metrics.cpu_percent > 80:
            score -= (metrics.cpu_percent - 80) * 2
        elif metrics.cpu_percent > 60:
            score -= (metrics.cpu_percent - 60) * 1
        
        # Pénalités mémoire
        if metrics.memory_percent > 85:
            score -= (metrics.memory_percent - 85) * 3
        elif metrics.memory_percent > 70:
            score -= (metrics.memory_percent - 70) * 1.5
        
        # Pénalités temps de réponse
        if metrics.response_time_avg > 2.0:
            score -= (metrics.response_time_avg - 2.0) * 20
        elif metrics.response_time_avg > 1.0:
            score -= (metrics.response_time_avg - 1.0) * 10
        
        # Pénalités taux d'erreur
        if metrics.error_rate > 0.05:
            score -= metrics.error_rate * 500
        elif metrics.error_rate > 0.01:
            score -= metrics.error_rate * 200
        
        # Bonus débit
        if metrics.throughput > 50:
            score += min(10, (metrics.throughput - 50) * 0.2)
        
        return max(0, min(100, score))
    
    async def analyze_and_optimize(self, metrics: SystemMetrics) -> List[OptimizationAction]:
        """Analyse les métriques et propose des optimisations"""
        actions = []
        
        # Optimisation CPU
        if metrics.cpu_percent > 80:
            actions.append(OptimizationAction(
                action_type="cpu_optimization",
                description="High CPU usage detected - enabling request throttling",
                impact="Reduce CPU load by limiting concurrent requests",
                timestamp=datetime.utcnow(),
                metrics_before={"cpu_percent": metrics.cpu_percent}
            ))
            await self.apply_cpu_optimization()
        
        # Optimisation mémoire
        if metrics.memory_percent > 85:
            actions.append(OptimizationAction(
                action_type="memory_optimization",
                description="High memory usage - clearing caches and reducing cache size",
                impact="Free memory by clearing caches and reducing cache limits",
                timestamp=datetime.utcnow(),
                metrics_before={"memory_percent": metrics.memory_percent}
            ))
            await self.apply_memory_optimization()
        
        # Optimisation temps de réponse
        if metrics.response_time_avg > 2.0:
            actions.append(OptimizationAction(
                action_type="response_time_optimization",
                description="Slow response times - enabling aggressive caching",
                impact="Improve response times with enhanced caching",
                timestamp=datetime.utcnow(),
                metrics_before={"response_time_avg": metrics.response_time_avg}
            ))
            await self.apply_response_time_optimization()
        
        # Optimisation taux d'erreur
        if metrics.error_rate > 0.05:
            actions.append(OptimizationAction(
                action_type="error_rate_optimization",
                description="High error rate - enabling circuit breaker and retries",
                impact="Reduce errors with circuit breaker pattern",
                timestamp=datetime.utcnow(),
                metrics_before={"error_rate": metrics.error_rate}
            ))
            await self.apply_error_rate_optimization()
        
        # Optimisation débit faible
        if metrics.throughput < 5 and metrics.cpu_percent < 50:
            actions.append(OptimizationAction(
                action_type="throughput_optimization",
                description="Low throughput - increasing worker pool size",
                impact="Increase throughput by adding more workers",
                timestamp=datetime.utcnow(),
                metrics_before={"throughput": metrics.throughput}
            ))
            await self.apply_throughput_optimization()
        
        return actions
    
    async def apply_cpu_optimization(self):
        """Applique l'optimisation CPU"""
        try:
            # Activer le throttling des requêtes
            if self.redis_client:
                await self.redis_client.set("config:max_concurrent_requests", "10")
                await self.redis_client.set("config:enable_throttling", "true")
            
            OPTIMIZATION_ACTIONS.labels(action_type="cpu_optimization").inc()
            logger.info("Applied CPU optimization - enabled request throttling")
        except Exception as e:
            logger.error(f"Failed to apply CPU optimization: {e}")
    
    async def apply_memory_optimization(self):
        """Applique l'optimisation mémoire"""
        try:
            # Réduire la taille du cache
            if self.redis_client:
                await self.redis_client.set("config:cache_size", "50")
                await self.redis_client.set("config:cache_ttl", "60")
                
                # Nettoyer les anciennes clés
                keys = await self.redis_client.keys("cache:*")
                if keys:
                    await self.redis_client.delete(*keys[:len(keys)//2])
            
            OPTIMIZATION_ACTIONS.labels(action_type="memory_optimization").inc()
            logger.info("Applied memory optimization - reduced cache size and cleared old entries")
        except Exception as e:
            logger.error(f"Failed to apply memory optimization: {e}")
    
    async def apply_response_time_optimization(self):
        """Applique l'optimisation du temps de réponse"""
        try:
            if self.redis_client:
                await self.redis_client.set("config:aggressive_caching", "true")
                await self.redis_client.set("config:cache_ttl", "300")  # 5 minutes
            
            OPTIMIZATION_ACTIONS.labels(action_type="response_time_optimization").inc()
            logger.info("Applied response time optimization - enabled aggressive caching")
        except Exception as e:
            logger.error(f"Failed to apply response time optimization: {e}")
    
    async def apply_error_rate_optimization(self):
        """Applique l'optimisation du taux d'erreur"""
        try:
            if self.redis_client:
                await self.redis_client.set("config:circuit_breaker_enabled", "true")
                await self.redis_client.set("config:max_retries", "3")
                await self.redis_client.set("config:retry_delay", "1.0")
            
            OPTIMIZATION_ACTIONS.labels(action_type="error_rate_optimization").inc()
            logger.info("Applied error rate optimization - enabled circuit breaker")
        except Exception as e:
            logger.error(f"Failed to apply error rate optimization: {e}")
    
    async def apply_throughput_optimization(self):
        """Applique l'optimisation du débit"""
        try:
            if self.redis_client:
                await self.redis_client.set("config:max_workers", "4")
                await self.redis_client.set("config:max_concurrent_requests", "20")
            
            OPTIMIZATION_ACTIONS.labels(action_type="throughput_optimization").inc()
            logger.info("Applied throughput optimization - increased worker pool")
        except Exception as e:
            logger.error(f"Failed to apply throughput optimization: {e}")
    
    async def store_metrics(self, metrics: SystemMetrics):
        """Stocke les métriques dans Redis"""
        if not self.redis_client:
            return
        
        try:
            # Stocker les métriques actuelles
            metrics_data = {
                "cpu_percent": metrics.cpu_percent,
                "memory_percent": metrics.memory_percent,
                "memory_available_gb": metrics.memory_available_gb,
                "disk_usage_percent": metrics.disk_usage_percent,
                "active_connections": metrics.active_connections,
                "response_time_avg": metrics.response_time_avg,
                "error_rate": metrics.error_rate,
                "throughput": metrics.throughput,
                "timestamp": metrics.timestamp.isoformat()
            }
            
            await self.redis_client.setex(
                "metrics:current",
                300,  # 5 minutes TTL
                json.dumps(metrics_data)
            )
            
            # Stocker dans l'historique (pour les graphiques)
            await self.redis_client.lpush(
                "metrics:history",
                json.dumps(metrics_data)
            )
            await self.redis_client.ltrim("metrics:history", 0, 1000)  # Garder 1000 entrées
            
            # Mettre à jour les métriques Prometheus
            RESOURCE_USAGE.labels(resource="cpu").set(metrics.cpu_percent)
            RESOURCE_USAGE.labels(resource="memory").set(metrics.memory_percent)
            RESOURCE_USAGE.labels(resource="disk").set(metrics.disk_usage_percent)
            
            performance_score = self.calculate_performance_score(metrics)
            PERFORMANCE_SCORE.set(performance_score)
            
        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")
    
    async def run_optimization_cycle(self):
        """Exécute un cycle d'optimisation"""
        if not ENABLE_AUTO_OPTIMIZATION:
            return
        
        try:
            OPTIMIZATION_CYCLES.inc()
            logger.info("Starting optimization cycle...")
            
            # Collecter les métriques
            metrics = await self.collect_metrics()
            await self.store_metrics(metrics)
            
            # Calculer le score de performance
            performance_score = self.calculate_performance_score(metrics)
            logger.info(f"Performance score: {performance_score:.1f}/100")
            
            # Analyser et optimiser
            actions = await self.analyze_and_optimize(metrics)
            
            # Stocker les actions d'optimisation
            for action in actions:
                self.optimization_history.append(action)
                await self.store_optimization_action(action)
            
            if actions:
                logger.info(f"Applied {len(actions)} optimization actions")
            else:
                logger.info("No optimization needed - system performing well")
            
        except Exception as e:
            logger.error(f"Optimization cycle failed: {e}")
    
    async def store_optimization_action(self, action: OptimizationAction):
        """Stocke une action d'optimisation"""
        if not self.redis_client:
            return
        
        try:
            action_data = {
                "action_type": action.action_type,
                "description": action.description,
                "impact": action.impact,
                "timestamp": action.timestamp.isoformat(),
                "metrics_before": action.metrics_before,
                "metrics_after": action.metrics_after
            }
            
            await self.redis_client.lpush(
                "optimization:history",
                json.dumps(action_data)
            )
            await self.redis_client.ltrim("optimization:history", 0, 100)  # Garder 100 actions
            
        except Exception as e:
            logger.error(f"Failed to store optimization action: {e}")
    
    async def get_optimization_status(self) -> Dict[str, Any]:
        """Récupère le statut d'optimisation"""
        try:
            current_metrics = await self.collect_metrics()
            performance_score = self.calculate_performance_score(current_metrics)
            
            # Récupérer l'historique récent
            recent_actions = []
            if self.redis_client:
                action_data = await self.redis_client.lrange("optimization:history", 0, 9)
                recent_actions = [json.loads(action) for action in action_data]
            
            return {
                "status": "active" if ENABLE_AUTO_OPTIMIZATION else "disabled",
                "performance_score": performance_score,
                "current_metrics": {
                    "cpu_percent": current_metrics.cpu_percent,
                    "memory_percent": current_metrics.memory_percent,
                    "response_time_avg": current_metrics.response_time_avg,
                    "error_rate": current_metrics.error_rate,
                    "throughput": current_metrics.throughput
                },
                "recent_actions": recent_actions,
                "total_cycles": OPTIMIZATION_CYCLES._value.get(),
                "last_cycle": current_metrics.timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get optimization status: {e}")
            return {"error": str(e)}


class AutoOptimizer:
    """Gestionnaire principal de l'auto-optimisation"""
    
    def __init__(self):
        self.resource_optimizer = ResourceOptimizer()
        self.running = False
        self.task = None
    
    async def start(self):
        """Démarre l'optimiseur automatique"""
        if self.running:
            return
        
        self.running = True
        await self.resource_optimizer.initialize()
        
        # Si c'est le premier démarrage, établir une baseline
        baseline_metrics = await self.resource_optimizer.collect_metrics()
        self.resource_optimizer.baseline_metrics = baseline_metrics
        
        logger.info("Auto-optimizer started")
        
        # Démarrer la boucle d'optimisation
        self.task = asyncio.create_task(self.optimization_loop())
    
    async def stop(self):
        """Arrête l'optimiseur"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logger.info("Auto-optimizer stopped")
    
    async def optimization_loop(self):
        """Boucle principale d'optimisation"""
        while self.running:
            try:
                await self.resource_optimizer.run_optimization_cycle()
                await asyncio.sleep(OPTIMIZATION_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Optimization loop error: {e}")
                await asyncio.sleep(OPTIMIZATION_INTERVAL)
    
    async def get_status(self) -> Dict[str, Any]:
        """Récupère le statut de l'optimiseur"""
        return await self.resource_optimizer.get_optimization_status()


# Instance globale
auto_optimizer = AutoOptimizer()


@asynccontextmanager
async def lifespan_manager(app):
    """Gestionnaire de cycle de vie pour FastAPI"""
    await auto_optimizer.start()
    yield
    await auto_optimizer.stop()


# Point d'entrée pour le service d'optimisation
if __name__ == "__main__":
    async def main():
        optimizer = AutoOptimizer()
        await optimizer.start()
        
        try:
            # Garder le service en cours d'exécution
            while True:
                await asyncio.sleep(60)
                status = await optimizer.get_status()
                logger.info(f"Optimization status: {status['performance_score']:.1f}/100")
        except KeyboardInterrupt:
            logger.info("Shutting down optimizer...")
        finally:
            await optimizer.stop()
    
    asyncio.run(main())
