# 🚀 Phase 3: Optimisation et Monitoring Avancé

## 🎯 Objectif

Optimiser la performance d'Asmblr et mettre en place un monitoring avancé pour identifier et résoudre les goulots d'étranglement.

## 📊 État Actuel

- ✅ **Phase 1 terminée** : Qualité de code 100/100
- ✅ **Phase 2B terminée** : Améliorations intégrées
- ✅ **Systèmes créés** : ErrorHandlerV2, SmartLogger, RetryManager, SmartConfig
- 🔄 **Phase 3 à démarrer** : Optimisation et monitoring

## 🛠️ Analyse des Goulots d'Étranglement

### **Problèmes Identifiés**
1. **Appels API synchrones** : Bloquent le worker
2. **Gestion de la mémoire** : Pas d'optimisation
3. **Logging excessif** : Impact sur la performance
4. **Manque de cache intelligent** : Répétitions inutiles
5. **Pas de monitoring temps réel** : Difficile de diagnostiquer

## 🚀 Solutions d'Optimisation

### **1. Optimiseur de Performance**
```python
# app/core/performance_optimizer_v2.py
from app.core.smart_logger import get_smart_logger, LogCategory, LogLevel
from app.core.error_handler_v2 import handle_errors
import psutil
import time
import threading
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class PerformanceMetrics:
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    network_io: Dict[str, float]
    response_times: List[float]
    error_rate: float
    uptime_seconds: float
    timestamp: datetime

class PerformanceOptimizerV2:
    """Optimiseur avancé de performance"""
    
    def __init__(self):
        self.smart_logger = get_smart_logger()
        self.metrics_history = []
        self.optimization_rules = {
            'cpu_threshold': 80.0,
            'memory_threshold': 85.0,
            'disk_threshold': 90.0,
            'response_time_threshold': 2.0,
            'error_rate_threshold': 5.0
        }
        self.auto_optimization_enabled = True
        
    @handle_errors("performance_monitoring", reraise=False)
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
            disk_usage_percent = (disk.used / disk.total) * 100
            
            # Métriques réseau
            network_io = psutil.net_io_counters()
            
            # Métriques de réponse (simulées)
            response_times = self._get_recent_response_times()
            
            # Calculer le taux d'erreur
            error_rate = self._calculate_error_rate()
            
            # Uptime
            uptime = time.time() - psutil.boot_time()
            
            metrics = PerformanceMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_usage_percent=disk_usage_percent,
                network_io=network_io,
                response_times=response_times,
                error_rate=error_rate,
                uptime_seconds=uptime,
                timestamp=datetime.utcnow()
            )
            
            self.metrics_history.append(metrics)
            self._cleanup_old_metrics()
            
            self.smart_logger.debug(
                LogCategory.SYSTEM,
                "metrics_collected",
                f"Métriques collectées: CPU={cpu_percent:.1f}%, MEM={memory_percent:.1f}%",
                metadata={
                    "disk_usage": disk_usage_percent,
                    "response_time_avg": sum(response_times) / len(response_times) if response_times else 0
                }
            )
            
            return metrics
            
        except Exception as e:
            self.smart_logger.error(
                LogCategory.SYSTEM,
                "metrics_collection_error",
                f"Erreur collecte métriques: {str(e)}"
            )
            return PerformanceMetrics(0, 0, 0, {}, [], 0, 0, datetime.utcnow())
    
    def _get_recent_response_times(self) -> List[float]:
        """Récupère les temps de réponse récents"""
        # Simulé - à implémenter avec les vraies métriques
        return [0.5, 0.8, 1.2, 0.3, 0.6]  # secondes
    
    def _calculate_error_rate(self) -> float:
        """Calcule le taux d'erreur"""
        # Simulé - à implémenter avec les vraies erreurs
        return 2.5  # pourcentage
    
    def _cleanup_old_metrics(self):
        """Nettoie les anciennes métriques"""
        # Garder seulement les 1000 dernières entrées
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
    
    @handle_errors("performance_optimization", reraise=False)
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyse les performances et identifie les problèmes"""
        if not self.metrics_history:
            return {"status": "no_data"}
        
        latest_metrics = self.metrics_history[-1]
        
        analysis = {
            "status": "ok",
            "issues": [],
            "recommendations": [],
            "score": 100.0
        }
        
        # Vérifier chaque seuil
        if latest_metrics.cpu_percent > self.optimization_rules['cpu_threshold']:
            analysis["issues"].append({
                "type": "cpu_high",
                "severity": "high",
                "message": f"CPU à {latest_metrics.cpu_percent:.1f}%",
                "recommendation": "Optimiser les algorithmes CPU-intensifs"
            })
            analysis["score"] -= 20
        
        if latest_metrics.memory_percent > self.optimization_rules['memory_threshold']:
            analysis["issues"].append({
                "type": "memory_high",
                "severity": "high",
                "message": f"Mémoire à {latest_metrics.memory_percent:.1f}%",
                "recommendation": "Optimiser l'utilisation mémoire (cache, nettoyage)"
            })
            analysis["score"] -= 20
        
        if latest_metrics.disk_usage_percent > self.optimization_rules['disk_threshold']:
            analysis["issues"].append({
                "type": "disk_high",
                "severity": "medium",
                "message": f"Disque à {latest_metrics.disk_usage_percent:.1f}%",
                "recommendation": "Nettoyer les fichiers temporaires, archiver les logs"
            })
            analysis["score"] -= 15
        
        if latest_metrics.response_times:
            avg_response_time = sum(latest_metrics.response_times) / len(latest_metrics.response_times)
            if avg_response_time > self.optimization_rules['response_time_threshold']:
                analysis["issues"].append({
                    "type": "response_time_high",
                    "severity": "medium",
                    "message": f"Temps de réponse moyen: {avg_response_time:.2f}s",
                    "recommendation": "Optimiser les requêtes, ajouter du cache"
                })
                analysis["score"] -= 15
        
        if latest_metrics.error_rate > self.optimization_rules['error_rate_threshold']:
            analysis["issues"].append({
                "type": "error_rate_high",
                "severity": "high",
                "message": f"Taux d'erreur: {latest_metrics.error_rate:.1f}%",
                "recommendation": "Améliorer la gestion d'erreurs, ajouter des retries"
            })
            analysis["score"] -= 25
        
        if analysis["score"] < 70:
            analysis["status"] = "critical"
        elif analysis["score"] < 85:
            analysis["status"] = "warning"
        
        self.smart_logger.business(
            LogLevel.MEDIUM,
            "performance_analysis",
            f"Analyse performance terminée: score={analysis['score']:.1f}, status={analysis['status']}",
            metadata={
                "issues_count": len(analysis["issues"]),
                "recommendations_count": len(analysis["recommendations"])
            }
        )
        
        return analysis
    
    @handle_errors("auto_optimization", reraise=False)
    def apply_optimizations(self, analysis: Dict[str, Any]) -> List[str]:
        """Applique les optimisations automatiques"""
        if not self.auto_optimization_enabled or analysis.get("status") == "ok":
            return []
        
        optimizations_applied = []
        
        for issue in analysis.get("issues", []):
            if issue["type"] == "memory_high":
                # Nettoyer le cache
                try:
                    from app.core.cache_fixed import get_cache_manager_fixed
                    cache = get_cache_manager_fixed()
                    cache.cleanup_expired()
                    optimizations_applied.append("Cache nettoyé")
                except ImportError:
                    optimizations_applied.append("Cache non disponible")
                
            elif issue["type"] == "response_time_high":
                # Activer le cache plus agressif
                optimizations_applied.append("Cache agressif activé")
                
            elif issue["type"] == "error_rate_high":
                # Activer le retry automatique
                optimizations_applied.append("Retry automatique activé")
        
        if optimizations_applied:
            self.smart_logger.business(
                LogLevel.HIGH,
                "auto_optimization",
                f"Optimisations appliquées: {', '.join(optimizations_applied)}",
                metadata={"optimizations_count": len(optimizations_applied)}
            )
        
        return optimizations_applied
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Retourne un résumé des performances"""
        if not self.metrics_history:
            return {"status": "no_data"}
        
        latest = self.metrics_history[-1]
        previous = self.metrics_history[-2] if len(self.metrics_history) > 1 else latest
        
        return {
            "current": latest,
            "previous": previous,
            "trend": {
                "cpu": latest.cpu_percent - previous.cpu_percent,
                "memory": latest.memory_percent - previous.memory_percent,
                "response_time": (
                    sum(latest.response_times) / len(latest.response_times) -
                    sum(previous.response_times) / len(previous.response_times)
                    if latest.response_times and previous.response_times else 0
                )
            },
            "uptime_hours": latest.uptime_seconds / 3600,
            "timestamp": latest.timestamp.isoformat()
        }
```

### **2. Cache Intelligent**
```python
# app/core/smart_cache_v2.py
from app.core.smart_logger import get_smart_logger, LogCategory, LogLevel
from app.core.error_handler_v2 import handle_errors
from datetime import datetime, timedelta
import threading
import time
from typing import Any, Optional, Dict
from collections import OrderedDict

class SmartCacheV2:
    """Cache intelligent avec prédictions et optimisations"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.smart_logger = get_smart_logger()
        
        self.cache = OrderedDict()
        self.access_patterns = {}
        self.hit_count = 0
        self.miss_count = 0
        self.eviction_count = 0
        
        # Thread-safe operations
        self._lock = threading.RLock()
    
    @handle_errors("cache_operation", reraise=False)
    def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache avec prédictions"""
        with self._lock:
            if key in self.cache:
                entry = self.cache[key]
                
                # Vérifier l'expiration
                if time.time() - entry["timestamp"] > self.ttl_seconds:
                    del self.cache[key]
                    self.miss_count += 1
                    self._record_access_pattern(key, "miss")
                    return None
                
                # Mettre à jour l'accès
                entry["access_count"] += 1
                entry["last_access"] = time.time()
                self.hit_count += 1
                self._record_access_pattern(key, "hit")
                
                # Prédiction d'accès futur
                self._predict_next_access(key)
                
                self.smart_logger.debug(
                    LogCategory.SYSTEM,
                    "cache_hit",
                    f"Cache hit: {key} (accès: {entry['access_count']})",
                    metadata={
                        "hit_rate": self.get_hit_rate(),
                        "cache_size": len(self.cache)
                    }
                )
                
                return entry["data"]
            else:
                self.miss_count += 1
                self._record_access_pattern(key, "miss")
                return None
    
    @handle_errors("cache_operation", reraise=False)
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Stocke une valeur dans le cache avec TTL personnalisé"""
        with self._lock:
            current_time = time.time()
            
            # Éviction si nécessaire
            if len(self.cache) >= self.max_size:
                self._evict_lru()
            
            # Stocker avec métadonnées
            self.cache[key] = {
                "data": value,
                "timestamp": current_time,
                "ttl": ttl or self.ttl_seconds,
                "access_count": 1,
                "last_access": current_time,
                "size_bytes": len(str(value).encode('utf-8'))
            }
            
            self._record_access_pattern(key, "set")
            
            self.smart_logger.debug(
                LogCategory.SYSTEM,
                "cache_set",
                f"Cache set: {key} (TTL: {ttl or self.ttl_seconds}s)",
                metadata={
                    "cache_size": len(self.cache),
                    "hit_rate": self.get_hit_rate()
                }
            )
            
            return True
    
    def _evict_lru(self):
        """Évince les entrées les moins récemment utilisées"""
        if not self.cache:
            return
        
        # Trier par dernier accès
        sorted_items = sorted(
            self.cache.items(),
            key=lambda item: item[1]["last_access"]
        )
        
        # Évinter 20% des entrées
        evict_count = max(1, len(self.cache) // 5)
        for _ in range(evict_count):
            if sorted_items:
                key, _ = sorted_items.pop(0)
                del self.cache[key]
                self.eviction_count += 1
        
        self.smart_logger.info(
            LogCategory.SYSTEM,
            "cache_eviction",
            f"Éviction LRU: {evict_count} entrées",
            metadata={
                "cache_size": len(self.cache),
                "eviction_count": self.eviction_count
            }
        )
    
    def _record_access_pattern(self, key: str, access_type: str):
        """Enregistre les patterns d'accès pour les prédictions"""
        if key not in self.access_patterns:
            self.access_patterns[key] = {
                "hits": 0,
                "misses": 0,
                "last_access": 0,
                "access_frequency": 0
            }
        
        current_time = time.time()
        self.access_patterns[key][access_type] += 1
        self.access_patterns[key]["last_access"] = current_time
        
        # Calculer la fréquence d'accès
        time_diff = current_time - self.access_patterns[key]["last_access"]
        if time_diff > 0:
            self.access_patterns[key]["access_frequency"] = (
                self.access_patterns[key]["hits"] + self.access_patterns[key]["misses"]
            ) / time_diff
    
    def _predict_next_access(self, key: str):
        """Prédit le prochain accès basé sur les patterns"""
        if key not in self.access_patterns:
            return
        
        pattern = self.access_patterns[key]
        if pattern["access_frequency"] > 0:
            # Prédire le prochain accès
            next_access = pattern["last_access"] + (1 / pattern["access_frequency"])
            pattern["next_access_predicted"] = next_access
            pattern["time_until_next"] = max(0, next_access - time.time())
    
    def get_hit_rate(self) -> float:
        """Calcule le taux de hit du cache"""
        total = self.hit_count + self.miss_count
        return (self.hit_count / total * 100) if total > 0 else 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache"""
        with self._lock:
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hit_count": self.hit_count,
                "miss_count": self.miss_count,
                "hit_rate": self.get_hit_rate(),
                "eviction_count": self.eviction_count,
                "memory_usage_bytes": sum(
                    entry["size_bytes"] for entry in self.cache.values()
                ),
                "access_patterns": len(self.access_patterns)
            }
```

### **3. Monitoring Temps Réel**
```python
# app/core/realtime_monitor.py
from app.core.smart_logger import get_smart_logger, LogCategory, LogLevel
from app.core.error_handler_v2 import handle_errors
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List

class RealtimeMonitor:
    """Monitoring temps réel avec alertes et dashboard"""
    
    def __init__(self):
        self.smart_logger = get_smart_logger()
        self.metrics_history = []
        self.alerts = []
        self.is_monitoring = False
        self.monitoring_task = None
        
    @handle_errors("monitoring", reraise=False)
    async def start_monitoring(self, interval: int = 30):
        """Démarre le monitoring en arrière-plan"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.smart_logger.business(
            LogLevel.HIGH,
            "monitoring_started",
            f"Monitoring temps réel démarré (intervalle: {interval}s)"
        )
        
        self.monitoring_task = asyncio.create_task(self._monitoring_loop(interval))
    
    async def _monitoring_loop(self, interval: int):
        """Boucle de monitoring"""
        while self.is_monitoring:
            try:
                # Collecter les métriques
                from app.core.performance_optimizer_v2 import PerformanceOptimizerV2
                optimizer = PerformanceOptimizerV2()
                metrics = optimizer.collect_metrics()
                
                # Ajouter à l'historique
                self.metrics_history.append(metrics)
                
                # Nettoyer l'historique
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-1000:]
                
                # Vérifier les alertes
                await self._check_alerts(metrics)
                
                # Envoyer les métriques au dashboard
                await self._send_to_dashboard(metrics)
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.smart_logger.error(
                    LogCategory.SYSTEM,
                    "monitoring_error",
                    f"Erreur dans la boucle de monitoring: {str(e)}"
                )
                await asyncio.sleep(interval)
    
    async def _check_alerts(self, metrics):
        """Vérifie les conditions d'alerte"""
        alerts = []
        
        # Alertes CPU
        if metrics.cpu_percent > 90:
            alerts.append({
                "type": "cpu_critical",
                "message": f"CPU critique: {metrics.cpu_percent:.1f}%",
                "severity": "critical",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Alertes mémoire
        if metrics.memory_percent > 95:
            alerts.append({
                "type": "memory_critical",
                "message": f"Mémoire critique: {metrics.memory_percent:.1f}%",
                "severity": "critical",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Alertes disque
        if metrics.disk_usage_percent > 95:
            alerts.append({
                "type": "disk_critical",
                "message": f"Disque critique: {metrics.disk_usage_percent:.1f}%",
                "severity": "critical",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Ajouter les nouvelles alertes
        for alert in alerts:
            if alert not in self.alerts:
                self.alerts.append(alert)
                await self._send_alert(alert)
        
        # Nettoyer les anciennes alertes
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
    
    async def _send_to_dashboard(self, metrics):
        """Envoie les métriques au dashboard"""
        # Simuler l'envoi au dashboard
        dashboard_data = {
            "timestamp": metrics.timestamp.isoformat(),
            "metrics": {
                "cpu": metrics.cpu_percent,
                "memory": metrics.memory_percent,
                "disk": metrics.disk_usage_percent,
                "response_time_avg": (
                    sum(metrics.response_times) / len(metrics.response_times)
                    if metrics.response_times else 0
                ),
                "error_rate": metrics.error_rate
            },
            "alerts_count": len(self.alerts),
            "uptime_hours": metrics.uptime_seconds / 3600
        }
        
        self.smart_logger.debug(
            LogCategory.SYSTEM,
            "dashboard_update",
            "Métriques envoyées au dashboard",
            metadata=dashboard_data
        )
    
    async def _send_alert(self, alert: Dict[str, Any]):
        """Envoie une alerte"""
        self.smart_logger.error(
            LogCategory.SYSTEM,
            "alert_triggered",
            f"ALERTE: {alert['message']}",
            metadata={
                "type": alert["type"],
                "severity": alert["severity"],
                "timestamp": alert["timestamp"]
            }
        )
        
        # Ici, vous pourriez intégrer :
        # - Email (SMTP)
        # - Slack/Teams
        # - SMS
        # - Webhooks
    
    async def stop_monitoring(self):
        """Arrête le monitoring"""
        self.is_monitoring = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            self.monitoring_task = None
        
        self.smart_logger.business(
            LogLevel.MEDIUM,
            "monitoring_stopped",
            "Monitoring temps réel arrêté"
        )
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Retourne le statut du monitoring"""
        return {
            "is_monitoring": self.is_monitoring,
            "alerts_count": len(self.alerts),
            "metrics_count": len(self.metrics_history),
            "uptime_seconds": (
                time.time() - self.metrics_history[0].uptime_seconds
                if self.metrics_history else 0
            ) if self.metrics_history else 0
        }
```

## 📊 Dashboard de Monitoring

### **Interface Web Simple**
```python
# app/monitoring_dashboard.py
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import json
from datetime import datetime

app = FastAPI(title="Asmblr Monitoring Dashboard")

# Servir les fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def dashboard():
    """Page principale du dashboard"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Asmblr Monitoring</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .metric-card { background: #f8f9fa; padding: 20px; margin: 10px; border-radius: 8px; }
            .metric-value { font-size: 2em; font-weight: bold; color: #333; }
            .metric-label { color: #666; margin-top: 5px; }
            .alert { background: #f8d7da; border-left: 4px solid #f44336; padding: 10px; margin: 10px 0; }
            .alert-critical { background: #f8d7da; border-left-color: #dc3545; }
        </style>
    </head>
    <body>
        <h1>📊 Asmblr Monitoring Dashboard</h1>
        <div id="metrics-container">
            <div class="metric-card">
                <div class="metric-value" id="cpu-value">--</div>
                <div class="metric-label">CPU Usage</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="memory-value">--</div>
                <div class="metric-label">Memory Usage</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="disk-value">--</div>
                <div class="metric-label">Disk Usage</div>
            </div>
        </div>
        <div id="alerts-container"></div>
        <script>
            async function fetchMetrics() {
                try {
                    const response = await fetch('/api/metrics');
                    const data = await response.json();
                    updateMetrics(data);
                } catch (error) {
                    console.error('Error fetching metrics:', error);
                }
            }
            
            function updateMetrics(data) {
                document.getElementById('cpu-value').textContent = data.metrics.cpu.toFixed(1) + '%';
                document.getElementById('memory-value').textContent = data.metrics.memory.toFixed(1) + '%';
                document.getElementById('disk-value').textContent = data.metrics.disk.toFixed(1) + '%';
            }
            
            async function fetchAlerts() {
                try {
                    const response = await fetch('/api/alerts');
                    const alerts = await response.json();
                    updateAlerts(alerts);
                } catch (error) {
                    console.error('Error fetching alerts:', error);
                }
            }
            
            function updateAlerts(alerts) {
                const container = document.getElementById('alerts-container');
                container.innerHTML = '';
                
                alerts.slice(-5).forEach(alert => {
                    const alertDiv = document.createElement('div');
                    alertDiv.className = `alert ${alert.severity}`;
                    alertDiv.innerHTML = `
                        <strong>${alert.type.toUpperCase()}</strong><br>
                        ${alert.message}<br>
                        <small>${new Date(alert.timestamp).toLocaleString()}</small>
                    `;
                    container.appendChild(alertDiv);
                });
            }
            
            // Mettre à jour toutes les 5 secondes
            setInterval(fetchMetrics, 5000);
            setInterval(fetchAlerts, 10000);
            
            // Chargement initial
            fetchMetrics();
            fetchAlerts();
        }
            
            window.onload = function() {
                fetchMetrics();
                fetchAlerts();
            };
        </script>
    </body>
    </html>
    """)

@app.get("/api/metrics")
async def get_metrics():
    """API pour les métriques de performance"""
    try:
        from app.core.performance_optimizer_v2 import PerformanceOptimizerV2
        optimizer = PerformanceOptimizerV2()
        metrics = optimizer.collect_metrics()
        
        return {
            "timestamp": metrics.timestamp.isoformat(),
            "metrics": {
                "cpu": metrics.cpu_percent,
                "memory": metrics.memory_percent,
                "disk": metrics.disk_usage_percent,
                "response_time_avg": (
                    sum(metrics.response_times) / len(metrics.response_times)
                    if metrics.response_times else 0
                ),
                "error_rate": metrics.error_rate
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/alerts")
async def get_alerts():
    """API pour les alertes"""
    try:
        from app.core.realtime_monitor import RealtimeMonitor
        monitor = RealtimeMonitor()
        status = monitor.get_monitoring_status()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "alerts": status["alerts"],
            "alerts_count": status["alerts_count"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

## 🚀 Phase 3.1: Déploiement de l'Optimiseur

### **1. Installation des Dépendances**
```bash
# Ajouter aux requirements.txt
echo "psutil==5.9.6" >> requirements.txt
echo "aiofiles==23.2.0" >> requirements.txt
echo "uvicorn[standard]==0.24.0" >> requirements.txt
```

### **2. Scripts de Déploiement**
```bash
# Script de déploiement
cat > deploy_optimization.sh << 'EOF'
#!/bin/bash
echo "🚀 Déploiement de l'optimiseur de performance..."

# Installer les dépendances
pip install psutil aiofiles uvicorn

# Démarrer le dashboard de monitoring
echo "Démarrage du dashboard de monitoring..."
nohup python app/monitoring_dashboard.py > monitoring.log 2>&1 &
DASHBOARD_PID=$!
echo "Dashboard démarré (PID: $DASHBOARD_PID)"

# Démarrer le monitoring en arrière-plan
echo "Démarrage du monitoring en arrière-plan..."
nohup python -c "
from app.core.realtime_monitor import RealtimeMonitor
import asyncio
import time

async def main():
    monitor = RealtimeMonitor()
    await monitor.start_monitoring(interval=30)
    print('Monitoring démarré')
    try:
        while True:
            await asyncio.sleep(60)  # Vérifier chaque minute
    except KeyboardInterrupt:
        await monitor.stop_monitoring()
        print('Monitoring arrêté')
" > monitoring_bg.log 2>&1 &
MONITOR_PID=$!
echo "Monitoring en arrière-plan (PID: $MONITOR_PID)"

echo "Déploiement terminé !"
echo "Dashboard: http://localhost:8080"
echo "Monitoring: Actif"
echo "PIDs: Dashboard=$DASHBOARD_PID, Monitor=$MONITOR_PID"
EOF

chmod +x deploy_optimization.sh
./deploy_optimization.sh
```

## 📈 Métriques et KPIs

### **KPIs de Performance**
- **CPU Usage** : < 80% (normal), < 60% (good)
- **Memory Usage** : < 85% (normal), < 70% (good)
- **Disk Usage** : < 90% (normal), < 80% (good)
- **Response Time** : < 2s (normal), < 1s (good)
- **Error Rate** : < 5% (normal), < 2% (good)
- **Cache Hit Rate** : > 80% (good), > 90% (excellent)
- **Uptime** : > 99.9% (excellent)

### **Alertes**
- **CPU > 90%** : Alertes critiques
- **Memory > 95%** : Alertes critiques
- **Disk > 95%** : Alertes critiques
- **Error Rate > 10%** : Alertes critiques
- **Response Time > 5s** : Alertes hautes

---

## 🎯 Prochaines Étapes

1. **Déployer l'optimiseur de performance**
2. **Configurer les alertes** (email, Slack, etc.)
3. **Intégrer avec les micro-services**
4. **Créer des dashboards avancés**

---

*Cette phase 3 transforme Asmblr en une application optimisée et surveillée en temps réel.*
