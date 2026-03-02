"""
Resource Monitoring for Asmblr
Tracks CPU, memory, and performance metrics
"""

import psutil
import time
import threading
from typing import Dict, Any
from loguru import logger

class ResourceMonitor:
    """Monitor system resources and performance"""
    
    def __init__(self, alert_thresholds: Dict[str, float] = None):
        self.alert_thresholds = alert_thresholds or {
            "memory_percent": 85.0,
            "cpu_percent": 90.0,
            "disk_percent": 90.0
        }
        self._monitoring = False
        self._thread = None
        self._metrics = []
        
    def start_monitoring(self, interval: int = 30):
        """Start resource monitoring"""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._thread = threading.Thread(target=self._monitor_loop, args=(interval,))
        self._thread.daemon = True
        self._thread.start()
        logger.info("Resource monitoring started")
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self._monitoring = False
        if self._thread:
            self._thread.join()
        logger.info("Resource monitoring stopped")
    
    def _monitor_loop(self, interval: int):
        """Main monitoring loop"""
        while self._monitoring:
            try:
                metrics = self.get_current_metrics()
                self._metrics.append(metrics)
                
                # Keep only last 1000 metrics
                if len(self._metrics) > 1000:
                    self._metrics = self._metrics[-1000:]
                
                # Check alerts
                self._check_alerts(metrics)
                
                time.sleep(interval)
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                time.sleep(interval)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "timestamp": time.time(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "disk_percent": (disk.used / disk.total) * 100,
            "disk_free_gb": disk.free / (1024**3),
            "process_count": len(psutil.pids())
        }
    
    def _check_alerts(self, metrics: Dict[str, Any]):
        """Check for resource alerts"""
        for metric, threshold in self.alert_thresholds.items():
            if metrics.get(metric, 0) > threshold:
                logger.warning(
                    f"Resource alert: {metric} = {metrics[metric]:.1f}% "
                    f"(threshold: {threshold}%)"
                )
    
    def get_metrics_summary(self, minutes: int = 60) -> Dict[str, Any]:
        """Get metrics summary for last N minutes"""
        cutoff_time = time.time() - (minutes * 60)
        recent_metrics = [
            m for m in self._metrics 
            if m["timestamp"] > cutoff_time
        ]
        
        if not recent_metrics:
            return {}
        
        return {
            "period_minutes": minutes,
            "samples": len(recent_metrics),
            "avg_cpu_percent": sum(m["cpu_percent"] for m in recent_metrics) / len(recent_metrics),
            "avg_memory_percent": sum(m["memory_percent"] for m in recent_metrics) / len(recent_metrics),
            "max_memory_percent": max(m["memory_percent"] for m in recent_metrics),
            "min_memory_available_gb": min(m["memory_available_gb"] for m in recent_metrics)
        }

# Global monitor instance
_monitor: ResourceMonitor = None

def get_resource_monitor() -> ResourceMonitor:
    """Get global resource monitor"""
    global _monitor
    if _monitor is None:
        _monitor = ResourceMonitor()
    return _monitor
