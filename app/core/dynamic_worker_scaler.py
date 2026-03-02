"""
Scaling Dynamique des Workers avec Auto-Scaling Intelligent
Gestion adaptative du nombre de workers basée sur la charge et les métriques
"""

import asyncio
import time
import json
import logging
from typing import Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import numpy as np
from collections import deque
import psutil
import docker
from prometheus_client import Gauge, Counter, Histogram
import redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScalingDecision(Enum):
    """Décisions de scaling possibles"""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    MAINTAIN = "maintain"
    EMERGENCY_SCALE = "emergency_scale"


@dataclass
class WorkerMetrics:
    """Métriques d'un worker"""
    worker_id: str
    cpu_usage: float
    memory_usage: float
    active_tasks: int
    queue_size: int
    avg_processing_time: float
    error_rate: float
    last_heartbeat: datetime
    tasks_completed: int = 0
    uptime: float = 0.0


@dataclass
class ScalingMetrics:
    """Métriques globales pour le scaling"""
    total_workers: int
    total_queue_size: int
    avg_cpu_usage: float
    avg_memory_usage: float
    avg_processing_time: float
    total_error_rate: float
    throughput: float
    response_time_p95: float
    system_load: float


@dataclass
class ScalingPolicy:
    """Politique de scaling"""
    min_workers: int = 1
    max_workers: int = 10
    scale_up_threshold: float = 0.8  # CPU/Queue
    scale_down_threshold: float = 0.3
    emergency_threshold: float = 0.95
    cooldown_period: int = 300  # seconds
    scale_up_factor: float = 1.5
    scale_down_factor: float = 0.7
    target_response_time: float = 2.0  # seconds
    target_throughput: float = 100.0  # tasks/minute


class DynamicWorkerScaler:
    """Gestionnaire de scaling dynamique des workers"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        policy: ScalingPolicy = None,
        docker_client: docker.DockerClient = None,
        metrics_window: int = 300  # 5 minutes
    ):
        self.redis_url = redis_url
        self.policy = policy or ScalingPolicy()
        self.docker_client = docker_client or docker.from_env()
        self.metrics_window = metrics_window
        
        # Redis pour les métriques
        self.redis_client = redis.from_url(redis_url)
        
        # État des workers
        self.workers: dict[str, WorkerMetrics] = {}
        self.worker_containers: dict[str, docker.models.containers.Container] = {}
        
        # Historique des métriques
        self.metrics_history = deque(maxlen=100)
        self.scaling_history = deque(maxlen=50)
        
        # Cooldown du scaling
        self.last_scaling_time = datetime.min
        
        # Métriques Prometheus
        self.setup_prometheus_metrics()
        
        # Lock pour éviter les scaling concurrents
        self._scaling_lock = asyncio.Lock()
        
        logger.info("Dynamic Worker Scaler initialisé")
    
    def setup_prometheus_metrics(self):
        """Configure les métriques Prometheus"""
        self.prometheus_metrics = {
            'workers_total': Gauge('asmblr_workers_total', 'Nombre total de workers'),
            'workers_active': Gauge('asmblr_workers_active', 'Nombre de workers actifs'),
            'queue_size': Gauge('asmblr_queue_size', 'Taille de la queue'),
            'scaling_decisions': Counter('asmblr_scaling_decisions', 'Décisions de scaling', ['decision']),
            'scaling_duration': Histogram('asmblr_scaling_duration', 'Durée du scaling'),
            'response_time': Histogram('asmblr_response_time_seconds', 'Temps de réponse'),
            'throughput': Gauge('asmblr_throughput', 'Débit de traitement')
        }
    
    async def start_monitoring(self):
        """Démarre le monitoring continu"""
        logger.info("Démarrage du monitoring du scaling")
        
        # Tâches de monitoring
        tasks = [
            asyncio.create_task(self._monitor_workers()),
            asyncio.create_task(self._evaluate_scaling()),
            asyncio.create_task(self._cleanup_dead_workers()),
            asyncio.create_task(self._update_prometheus_metrics())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Erreur dans le monitoring: {e}")
    
    async def _monitor_workers(self):
        """Surveille l'état des workers"""
        while True:
            try:
                await self._collect_worker_metrics()
                await self._update_global_metrics()
                await asyncio.sleep(10)  # Monitoring toutes les 10 secondes
            except Exception as e:
                logger.error(f"Erreur lors du monitoring des workers: {e}")
                await asyncio.sleep(30)
    
    async def _collect_worker_metrics(self):
        """Collecte les métriques de chaque worker"""
        current_time = datetime.now()
        
        # Récupérer les métriques depuis Redis
        worker_keys = self.redis_client.keys("worker_metrics:*")
        
        for key in worker_keys:
            try:
                data = self.redis_client.get(key)
                if data:
                    metrics_data = json.loads(data)
                    worker_id = key.decode().split(":")[1]
                    
                    # Mettre à jour les métriques du worker
                    self.workers[worker_id] = WorkerMetrics(
                        worker_id=worker_id,
                        cpu_usage=metrics_data.get('cpu_usage', 0.0),
                        memory_usage=metrics_data.get('memory_usage', 0.0),
                        active_tasks=metrics_data.get('active_tasks', 0),
                        queue_size=metrics_data.get('queue_size', 0),
                        avg_processing_time=metrics_data.get('avg_processing_time', 0.0),
                        error_rate=metrics_data.get('error_rate', 0.0),
                        last_heartbeat=current_time,
                        tasks_completed=metrics_data.get('tasks_completed', 0),
                        uptime=metrics_data.get('uptime', 0.0)
                    )
                    
            except Exception as e:
                logger.warning(f"Erreur lors de la lecture des métriques du worker {key}: {e}")
    
    async def _update_global_metrics(self):
        """Met à jour les métriques globales"""
        if not self.workers:
            return
        
        # Calculer les moyennes
        total_workers = len(self.workers)
        avg_cpu = np.mean([w.cpu_usage for w in self.workers.values()])
        avg_memory = np.mean([w.memory_usage for w in self.workers.values()])
        avg_processing_time = np.mean([w.avg_processing_time for w in self.workers.values()])
        total_error_rate = np.mean([w.error_rate for w in self.workers.values()])
        total_queue_size = sum([w.queue_size for w in self.workers.values()])
        
        # Calculer le throughput
        total_tasks = sum([w.tasks_completed for w in self.workers.values()])
        throughput = total_tasks / max(1, total_workers * 60)  # tasks/worker/minute
        
        # Calculer le système load
        system_load = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0
        
        # Créer les métriques globales
        global_metrics = ScalingMetrics(
            total_workers=total_workers,
            total_queue_size=total_queue_size,
            avg_cpu_usage=avg_cpu,
            avg_memory_usage=avg_memory,
            avg_processing_time=avg_processing_time,
            total_error_rate=total_error_rate,
            throughput=throughput,
            response_time_p95=self._calculate_p95_response_time(),
            system_load=system_load
        )
        
        # Ajouter à l'historique
        self.metrics_history.append({
            'timestamp': datetime.now(),
            'metrics': global_metrics
        })
        
        logger.debug(f"Métriques globales: {global_metrics}")
    
    def _calculate_p95_response_time(self) -> float:
        """Calcule le 95ème percentile du temps de réponse"""
        if not self.workers:
            return 0.0
        
        response_times = [w.avg_processing_time for w in self.workers.values()]
        return np.percentile(response_times, 95) if response_times else 0.0
    
    async def _evaluate_scaling(self):
        """Évalue si un scaling est nécessaire"""
        while True:
            try:
                decision = await self._make_scaling_decision()
                
                if decision != ScalingDecision.MAINTAIN:
                    await self._execute_scaling(decision)
                
                await asyncio.sleep(30)  # Évaluation toutes les 30 secondes
                
            except Exception as e:
                logger.error(f"Erreur lors de l'évaluation du scaling: {e}")
                await asyncio.sleep(60)
    
    async def _make_scaling_decision(self) -> ScalingDecision:
        """Prend une décision de scaling basée sur les métriques"""
        if not self.metrics_history:
            return ScalingDecision.MAINTAIN
        
        latest_metrics = self.metrics_history[-1]['metrics']
        current_time = datetime.now()
        
        # Vérifier le cooldown
        if (current_time - self.last_scaling_time).total_seconds() < self.policy.cooldown_period:
            return ScalingDecision.MAINTAIN
        
        # Conditions d'urgence
        if (latest_metrics.avg_cpu_usage >= self.policy.emergency_threshold or
            latest_metrics.total_queue_size > 100 or
            latest_metrics.response_time_p95 > self.policy.target_response_time * 2):
            logger.warning("Conditions d'urgence détectées!")
            return ScalingDecision.EMERGENCY_SCALE
        
        # Scale up conditions
        scale_up_conditions = [
            latest_metrics.avg_cpu_usage >= self.policy.scale_up_threshold,
            latest_metrics.total_queue_size > 20,
            latest_metrics.response_time_p95 > self.policy.target_response_time,
            latest_metrics.throughput < self.policy.target_throughput
        ]
        
        if any(scale_up_conditions) and latest_metrics.total_workers < self.policy.max_workers:
            return ScalingDecision.SCALE_UP
        
        # Scale down conditions
        scale_down_conditions = [
            latest_metrics.avg_cpu_usage <= self.policy.scale_down_threshold,
            latest_metrics.total_queue_size < 5,
            latest_metrics.response_time_p95 < self.policy.target_response_time * 0.5,
            latest_metrics.total_workers > self.policy.min_workers
        ]
        
        if all(scale_down_conditions):
            return ScalingDecision.SCALE_DOWN
        
        return ScalingDecision.MAINTAIN
    
    async def _execute_scaling(self, decision: ScalingDecision):
        """Exécute la décision de scaling"""
        async with self._scaling_lock:
            start_time = time.time()
            
            try:
                if decision == ScalingDecision.SCALE_UP:
                    await self._scale_up()
                elif decision == ScalingDecision.SCALE_DOWN:
                    await self._scale_down()
                elif decision == ScalingDecision.EMERGENCY_SCALE:
                    await self._emergency_scale()
                
                # Enregistrer la décision
                self.last_scaling_time = datetime.now()
                self.scaling_history.append({
                    'timestamp': self.last_scaling_time,
                    'decision': decision.value,
                    'workers_before': len(self.workers),
                    'workers_after': len(self.workers)
                })
                
                # Métriques Prometheus
                self.prometheus_metrics['scaling_decisions'].labels(decision=decision.value).inc()
                self.prometheus_metrics['scaling_duration'].observe(time.time() - start_time)
                
                logger.info(f"Scaling exécuté: {decision.value}")
                
            except Exception as e:
                logger.error(f"Erreur lors de l'exécution du scaling {decision.value}: {e}")
    
    async def _scale_up(self):
        """Augmente le nombre de workers"""
        current_workers = len(self.workers)
        
        # Calculer le nombre de workers à ajouter
        if current_workers == 0:
            target_workers = self.policy.min_workers
        else:
            target_workers = min(
                int(current_workers * self.policy.scale_up_factor),
                self.policy.max_workers
            )
        
        workers_to_add = target_workers - current_workers
        
        if workers_to_add <= 0:
            return
        
        logger.info(f"Scale up: ajout de {workers_to_add} workers")
        
        # Créer les nouveaux workers
        for i in range(workers_to_add):
            worker_id = f"worker-{int(time.time())}-{i}"
            await self._create_worker(worker_id)
    
    async def _scale_down(self):
        """Réduit le nombre de workers"""
        current_workers = len(self.workers)
        
        # Calculer le nombre de workers à supprimer
        target_workers = max(
            int(current_workers * self.policy.scale_down_factor),
            self.policy.min_workers
        )
        
        workers_to_remove = current_workers - target_workers
        
        if workers_to_remove <= 0:
            return
        
        logger.info(f"Scale down: suppression de {workers_to_remove} workers")
        
        # Identifier les workers à supprimer (ceux avec le moins de charge)
        workers_by_load = sorted(
            self.workers.values(),
            key=lambda w: (w.active_tasks, w.cpu_usage)
        )
        
        for worker in workers_by_load[:workers_to_remove]:
            await self._remove_worker(worker.worker_id)
    
    async def _emergency_scale(self):
        """Scaling d'urgence"""
        logger.warning("Emergency scale: ajout maximal de workers")
        
        # Ajouter le maximum de workers possibles
        current_workers = len(self.workers)
        workers_to_add = self.policy.max_workers - current_workers
        
        for i in range(workers_to_add):
            worker_id = f"emergency-worker-{int(time.time())}-{i}"
            await self._create_worker(worker_id)
    
    async def _create_worker(self, worker_id: str):
        """Crée un nouveau worker"""
        try:
            # Configuration du container
            container_config = {
                'image': 'asmblr/asmblr-workers:latest',
                'name': worker_id,
                'detach': True,
                'environment': {
                    'WORKER_ID': worker_id,
                    'REDIS_URL': self.redis_url,
                    'LOG_LEVEL': 'INFO'
                },
                'restart_policy': {'Name': 'unless-stopped'},
                'labels': {
                    'asmblr.worker': 'true',
                    'asmblr.worker.id': worker_id
                }
            }
            
            # Lancer le container
            container = self.docker_client.containers.run(**container_config)
            self.worker_containers[worker_id] = container
            
            # Initialiser les métriques du worker
            self.workers[worker_id] = WorkerMetrics(
                worker_id=worker_id,
                cpu_usage=0.0,
                memory_usage=0.0,
                active_tasks=0,
                queue_size=0,
                avg_processing_time=0.0,
                error_rate=0.0,
                last_heartbeat=datetime.now()
            )
            
            logger.info(f"Worker {worker_id} créé")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du worker {worker_id}: {e}")
    
    async def _remove_worker(self, worker_id: str):
        """Supprime un worker"""
        try:
            # Arrêter et supprimer le container
            if worker_id in self.worker_containers:
                container = self.worker_containers[worker_id]
                container.stop()
                container.remove()
                del self.worker_containers[worker_id]
            
            # Supprimer les métriques
            if worker_id in self.workers:
                del self.workers[worker_id]
            
            # Nettoyer Redis
            self.redis_client.delete(f"worker_metrics:{worker_id}")
            
            logger.info(f"Worker {worker_id} supprimé")
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du worker {worker_id}: {e}")
    
    async def _cleanup_dead_workers(self):
        """Nettoie les workers morts"""
        while True:
            try:
                current_time = datetime.now()
                dead_workers = []
                
                # Identifier les workers sans heartbeat récent
                for worker_id, metrics in self.workers.items():
                    heartbeat_age = (current_time - metrics.last_heartbeat).total_seconds()
                    
                    if heartbeat_age > 120:  # 2 minutes sans heartbeat
                        dead_workers.append(worker_id)
                
                # Supprimer les workers morts
                for worker_id in dead_workers:
                    logger.warning(f"Worker {worker_id} considéré comme mort, suppression...")
                    await self._remove_worker(worker_id)
                
                await asyncio.sleep(60)  # Vérification toutes les minutes
                
            except Exception as e:
                logger.error(f"Erreur lors du nettoyage des workers morts: {e}")
                await asyncio.sleep(120)
    
    async def _update_prometheus_metrics(self):
        """Met à jour les métriques Prometheus"""
        while True:
            try:
                if self.workers:
                    self.prometheus_metrics['workers_total'].set(len(self.workers))
                    self.prometheus_metrics['workers_active'].set(
                        sum(1 for w in self.workers.values() if w.active_tasks > 0)
                    )
                    self.prometheus_metrics['queue_size'].set(
                        sum(w.queue_size for w in self.workers.values())
                    )
                    
                    if self.metrics_history:
                        latest = self.metrics_history[-1]['metrics']
                        self.prometheus_metrics['throughput'].set(latest.throughput)
                
                await asyncio.sleep(15)  # Mise à jour toutes les 15 secondes
                
            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour des métriques Prometheus: {e}")
                await asyncio.sleep(60)
    
    async def get_scaling_status(self) -> dict[str, Any]:
        """Retourne le statut actuel du scaling"""
        if not self.metrics_history:
            return {'status': 'initializing'}
        
        latest_metrics = self.metrics_history[-1]['metrics']
        
        return {
            'status': 'active',
            'current_workers': latest_metrics.total_workers,
            'target_workers': self._calculate_target_workers(),
            'queue_size': latest_metrics.total_queue_size,
            'avg_cpu_usage': latest_metrics.avg_cpu_usage,
            'avg_memory_usage': latest_metrics.avg_memory_usage,
            'throughput': latest_metrics.throughput,
            'response_time_p95': latest_metrics.response_time_p95,
            'last_scaling': self.last_scaling_time.isoformat() if self.last_scaling_time != datetime.min else None,
            'scaling_history': [
                {
                    'timestamp': entry['timestamp'].isoformat(),
                    'decision': entry['decision'],
                    'workers_before': entry['workers_before'],
                    'workers_after': entry['workers_after']
                }
                for entry in list(self.scaling_history)[-10:]  # 10 dernières décisions
            ]
        }
    
    def _calculate_target_workers(self) -> int:
        """Calcule le nombre optimal de workers"""
        if not self.metrics_history:
            return self.policy.min_workers
        
        latest_metrics = self.metrics_history[-1]['metrics']
        
        # Basé sur la charge CPU et la taille de la queue
        cpu_based = max(
            self.policy.min_workers,
            int(latest_metrics.avg_cpu_usage * 10)  # Approximation
        )
        
        queue_based = max(
            self.policy.min_workers,
            int(latest_metrics.total_queue_size / 5)  # 5 tâches par worker
        )
        
        # Prendre le maximum des deux
        target = max(cpu_based, queue_based)
        
        return min(target, self.policy.max_workers)
    
    async def update_policy(self, new_policy: ScalingPolicy):
        """Met à jour la politique de scaling"""
        self.policy = new_policy
        logger.info(f"Politique de scaling mise à jour: {new_policy}")
    
    async def force_scaling(self, target_workers: int):
        """Force le scaling à un nombre spécifique de workers"""
        target_workers = max(self.policy.min_workers, min(target_workers, self.policy.max_workers))
        
        current_workers = len(self.workers)
        
        if target_workers > current_workers:
            # Scale up
            for i in range(target_workers - current_workers):
                worker_id = f"forced-worker-{int(time.time())}-{i}"
                await self._create_worker(worker_id)
        
        elif target_workers < current_workers:
            # Scale down
            workers_to_remove = current_workers - target_workers
            workers_by_load = sorted(
                self.workers.values(),
                key=lambda w: (w.active_tasks, w.cpu_usage)
            )
            
            for worker in workers_by_load[:workers_to_remove]:
                await self._remove_worker(worker.worker_id)
        
        logger.info(f"Scaling forcé: {current_workers} → {target_workers} workers")


# Singleton global
_dynamic_scaler: DynamicWorkerScaler | None = None


async def get_dynamic_scaler() -> DynamicWorkerScaler:
    """Retourne l'instance singleton du scaler dynamique"""
    global _dynamic_scaler
    
    if _dynamic_scaler is None:
        _dynamic_scaler = DynamicWorkerScaler()
    
    return _dynamic_scaler


# Exemple d'utilisation
async def example_usage():
    """Exemple d'utilisation du scaling dynamique"""
    scaler = await get_dynamic_scaler()
    
    # Démarrer le monitoring
    monitoring_task = asyncio.create_task(scaler.start_monitoring())
    
    try:
        # Simuler une charge
        for i in range(100):
            status = await scaler.get_scaling_status()
            print(f"Statut: {status['current_workers']} workers, queue: {status['queue_size']}")
            await asyncio.sleep(5)
            
    finally:
        monitoring_task.cancel()


if __name__ == "__main__":
    asyncio.run(example_usage())
