"""Comprehensive monitoring and metrics system for Asmblr."""

from __future__ import annotations
import time
import threading
import psutil
from datetime import datetime, timedelta
from typing import Any
from collections.abc import Callable
from dataclasses import dataclass
from collections import defaultdict, deque
from enum import Enum
import statistics

from loguru import logger


class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricValue:
    """Single metric value with timestamp."""
    value: float
    timestamp: datetime
    labels: dict[str, str]
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "labels": self.labels
        }


@dataclass
class Alert:
    """Alert definition."""
    name: str
    severity: AlertSeverity
    condition: str
    threshold: float
    message: str
    enabled: bool = True
    last_triggered: datetime | None = None
    trigger_count: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "severity": self.severity.value,
            "condition": self.condition,
            "threshold": self.threshold,
            "message": self.message,
            "enabled": self.enabled,
            "last_triggered": self.last_triggered.isoformat() if self.last_triggered else None,
            "trigger_count": self.trigger_count
        }


class MetricsCollector:
    """Collects and manages application metrics."""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics: dict[str, list[MetricValue]] = defaultdict(lambda: deque(maxlen=max_history))
        self.counters: dict[str, float] = defaultdict(float)
        self.gauges: dict[str, float] = defaultdict(float)
        self.histograms: dict[str, list[float]] = defaultdict(lambda: deque(maxlen=max_history))
        self.timers: dict[str, list[float]] = defaultdict(lambda: deque(maxlen=max_history))
        self.lock = threading.Lock()
        
        # System metrics
        self.system_metrics_enabled = True
        self.system_metrics_interval = 30  # seconds
        self._system_metrics_thread = None
        self._stop_system_metrics = threading.Event()
    
    def increment_counter(self, name: str, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
        """Increment a counter metric."""
        with self.lock:
            self.counters[name] += value
            self._store_metric(name, MetricType.COUNTER, self.counters[name], labels or {})
    
    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Set a gauge metric."""
        with self.lock:
            self.gauges[name] = value
            self._store_metric(name, MetricType.GAUGE, value, labels or {})
    
    def record_histogram(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        """Record a histogram value."""
        with self.lock:
            self.histograms[name].append(value)
            self._store_metric(name, MetricType.HISTOGRAM, value, labels or {})
    
    def record_timer(self, name: str, duration: float, labels: dict[str, str] | None = None) -> None:
        """Record a timer value."""
        with self.lock:
            self.timers[name].append(duration)
            self._store_metric(name, MetricType.TIMER, duration, labels or {})
    
    def time_operation(self, name: str, labels: dict[str, str] | None = None):
        """Context manager for timing operations."""
        class TimerContext:
            def __init__(self, collector: MetricsCollector, name: str, labels: dict[str, str] | None):
                self.collector = collector
                self.name = name
                self.labels = labels
                self.start_time = None
            
            def __enter__(self):
                self.start_time = time.time()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                duration = time.time() - self.start_time
                self.collector.record_timer(self.name, duration, self.labels)
        
        return TimerContext(self, name, labels)
    
    def _store_metric(self, name: str, metric_type: MetricType, value: float, labels: dict[str, str]) -> None:
        """Store a metric value with timestamp."""
        metric_value = MetricValue(
            value=value,
            timestamp=datetime.now(),
            labels=labels
        )
        self.metrics[name].append(metric_value)
    
    def get_metric(self, name: str, since: datetime | None = None) -> list[MetricValue]:
        """Get metric values, optionally filtered by time."""
        with self.lock:
            values = list(self.metrics.get(name, []))
            
            if since:
                values = [v for v in values if v.timestamp >= since]
            
            return values
    
    def get_metric_summary(self, name: str) -> dict[str, Any]:
        """Get summary statistics for a metric."""
        values = self.get_metric(name)
        
        if not values:
            return {"count": 0}
        
        numeric_values = [v.value for v in values]
        
        summary = {
            "count": len(numeric_values),
            "min": min(numeric_values),
            "max": max(numeric_values),
            "mean": statistics.mean(numeric_values),
            "median": statistics.median(numeric_values),
            "latest": numeric_values[-1],
            "first_timestamp": values[0].timestamp.isoformat(),
            "last_timestamp": values[-1].timestamp.isoformat()
        }
        
        if len(numeric_values) > 1:
            summary["std_dev"] = statistics.stdev(numeric_values)
            summary["p95"] = sorted(numeric_values)[int(0.95 * len(numeric_values))]
            summary["p99"] = sorted(numeric_values)[int(0.99 * len(numeric_values))]
        
        return summary
    
    def get_all_metrics(self) -> dict[str, Any]:
        """Get all current metric values."""
        with self.lock:
            return {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {name: list(values) for name, values in self.histograms.items()},
                "timers": {name: list(values) for name, values in self.timers.items()},
                "summaries": {name: self.get_metric_summary(name) for name in self.metrics.keys()}
            }
    
    def start_system_metrics(self) -> None:
        """Start collecting system metrics."""
        if self._system_metrics_thread is None or not self._system_metrics_thread.is_alive():
            self._stop_system_metrics.clear()
            self._system_metrics_thread = threading.Thread(target=self._collect_system_metrics)
            self._system_metrics_thread.daemon = True
            self._system_metrics_thread.start()
            logger.info("Started system metrics collection")
    
    def stop_system_metrics(self) -> None:
        """Stop collecting system metrics."""
        self._stop_system_metrics.set()
        if self._system_metrics_thread:
            self._system_metrics_thread.join(timeout=5)
        logger.info("Stopped system metrics collection")
    
    def _collect_system_metrics(self) -> None:
        """Collect system metrics in background thread."""
        while not self._stop_system_metrics.wait(self.system_metrics_interval):
            try:
                # CPU metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                self.set_gauge("system_cpu_percent", cpu_percent, {"type": "total"})
                
                # Memory metrics
                memory = psutil.virtual_memory()
                self.set_gauge("system_memory_percent", memory.percent, {"type": "used"})
                self.set_gauge("system_memory_bytes", memory.used, {"type": "used"})
                self.set_gauge("system_memory_available_bytes", memory.available, {"type": "available"})
                
                # Disk metrics
                disk = psutil.disk_usage('/')
                self.set_gauge("system_disk_percent", (disk.used / disk.total) * 100, {"type": "used"})
                self.set_gauge("system_disk_bytes", disk.used, {"type": "used"})
                self.set_gauge("system_disk_free_bytes", disk.free, {"type": "free"})
                
                # Process metrics
                process = psutil.Process()
                self.set_gauge("process_memory_bytes", process.memory_info().rss, {"type": "rss"})
                self.set_gauge("process_cpu_percent", process.cpu_percent(), {"type": "total"})
                self.set_gauge("process_threads", process.num_threads(), {"type": "count"})
                
                # Custom application metrics
                self.increment_counter("system_metrics_collected")
                
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        with self.lock:
            self.metrics.clear()
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()
            self.timers.clear()
        logger.info("Reset all metrics")


class AlertManager:
    """Manages alerts based on metrics."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.alerts: dict[str, Alert] = {}
        self.alert_callbacks: list[Callable[[Alert], None]] = []
        self.lock = threading.Lock()
        self._alert_thread = None
        self._stop_alerts = threading.Event()
        self.check_interval = 30  # seconds
        
        # Initialize default alerts
        self._initialize_default_alerts()
    
    def _initialize_default_alerts(self) -> None:
        """Initialize default alert rules."""
        default_alerts = [
            Alert(
                name="high_cpu_usage",
                severity=AlertSeverity.WARNING,
                condition="system_cpu_percent > threshold",
                threshold=80.0,
                message="CPU usage is above 80%"
            ),
            Alert(
                name="high_memory_usage",
                severity=AlertSeverity.WARNING,
                condition="system_memory_percent > threshold",
                threshold=85.0,
                message="Memory usage is above 85%"
            ),
            Alert(
                name="high_disk_usage",
                severity=AlertSeverity.ERROR,
                condition="system_disk_percent > threshold",
                threshold=90.0,
                message="Disk usage is above 90%"
            ),
            Alert(
                name="pipeline_failure_rate",
                severity=AlertSeverity.ERROR,
                condition="pipeline_failure_rate > threshold",
                threshold=10.0,
                message="Pipeline failure rate is above 10%"
            ),
            Alert(
                name="slow_pipeline_execution",
                severity=AlertSeverity.WARNING,
                condition="pipeline_execution_time > threshold",
                threshold=300.0,
                message="Pipeline execution time is above 5 minutes"
            )
        ]
        
        for alert in default_alerts:
            self.alerts[alert.name] = alert
    
    def add_alert(self, alert: Alert) -> None:
        """Add a new alert rule."""
        with self.lock:
            self.alerts[alert.name] = alert
        logger.info(f"Added alert: {alert.name}")
    
    def remove_alert(self, name: str) -> None:
        """Remove an alert rule."""
        with self.lock:
            if name in self.alerts:
                del self.alerts[name]
                logger.info(f"Removed alert: {name}")
    
    def add_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """Add a callback for alert notifications."""
        self.alert_callbacks.append(callback)
    
    def start_alert_monitoring(self) -> None:
        """Start alert monitoring."""
        if self._alert_thread is None or not self._alert_thread.is_alive():
            self._stop_alerts.clear()
            self._alert_thread = threading.Thread(target=self._monitor_alerts)
            self._alert_thread.daemon = True
            self._alert_thread.start()
            logger.info("Started alert monitoring")
    
    def stop_alert_monitoring(self) -> None:
        """Stop alert monitoring."""
        self._stop_alerts.set()
        if self._alert_thread:
            self._alert_thread.join(timeout=5)
        logger.info("Stopped alert monitoring")
    
    def _monitor_alerts(self) -> None:
        """Monitor alerts in background thread."""
        while not self._stop_alerts.wait(self.check_interval):
            try:
                self._check_alerts()
            except Exception as e:
                logger.error(f"Error checking alerts: {e}")
    
    def _check_alerts(self) -> None:
        """Check all alert conditions."""
        with self.lock:
            for alert in self.alerts.values():
                if not alert.enabled:
                    continue
                
                if self._evaluate_alert_condition(alert):
                    self._trigger_alert(alert)
    
    def _evaluate_alert_condition(self, alert: Alert) -> bool:
        """Evaluate an alert condition."""
        try:
            # Simple threshold-based evaluation
            if "system_cpu_percent" in alert.condition:
                current_value = self.metrics_collector.gauges.get("system_cpu_percent", 0)
                return current_value > alert.threshold
            
            elif "system_memory_percent" in alert.condition:
                current_value = self.metrics_collector.gauges.get("system_memory_percent", 0)
                return current_value > alert.threshold
            
            elif "system_disk_percent" in alert.condition:
                current_value = self.metrics_collector.gauges.get("system_disk_percent", 0)
                return current_value > alert.threshold
            
            # Add more complex condition evaluation as needed
            return False
            
        except Exception as e:
            logger.error(f"Error evaluating alert condition for {alert.name}: {e}")
            return False
    
    def _trigger_alert(self, alert: Alert) -> None:
        """Trigger an alert."""
        now = datetime.now()
        
        # Check if this is a new trigger or repeated trigger
        if alert.last_triggered is None or (now - alert.last_triggered) > timedelta(minutes=5):
            alert.last_triggered = now
            alert.trigger_count += 1
            
            logger.warning(f"Alert triggered: {alert.name} - {alert.message}")
            
            # Notify callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Error in alert callback: {e}")
    
    def get_active_alerts(self) -> list[Alert]:
        """Get currently active alerts."""
        with self.lock:
            return [alert for alert in self.alerts.values() if alert.last_triggered is not None]
    
    def get_all_alerts(self) -> dict[str, Alert]:
        """Get all alert definitions."""
        with self.lock:
            return dict(self.alerts)


class MonitoringSystem:
    """Main monitoring system that coordinates metrics and alerts."""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager(self.metrics_collector)
        self.enabled = False
        
        # Application-specific metrics
        self.pipeline_metrics = {
            "pipelines_started": 0,
            "pipelines_completed": 0,
            "pipelines_failed": 0,
            "total_execution_time": 0.0,
            "total_ideas_generated": 0
        }
    
    def start(self) -> None:
        """Start the monitoring system."""
        if not self.enabled:
            self.metrics_collector.start_system_metrics()
            self.alert_manager.start_alert_monitoring()
            self.enabled = True
            logger.info("Monitoring system started")
    
    def stop(self) -> None:
        """Stop the monitoring system."""
        if self.enabled:
            self.metrics_collector.stop_system_metrics()
            self.alert_manager.stop_alert_monitoring()
            self.enabled = False
            logger.info("Monitoring system stopped")
    
    def record_pipeline_start(self, topic: str, execution_profile: str) -> None:
        """Record pipeline start."""
        self.pipeline_metrics["pipelines_started"] += 1
        self.metrics_collector.increment_counter(
            "pipelines_started",
            labels={"topic": topic, "profile": execution_profile}
        )
        self.metrics_collector.set_gauge(
            "active_pipelines",
            self.pipeline_metrics["pipelines_started"] - self.pipeline_metrics["pipelines_completed"] - self.pipeline_metrics["pipelines_failed"]
        )
    
    def record_pipeline_completion(self, execution_time: float, ideas_count: int, success: bool) -> None:
        """Record pipeline completion."""
        if success:
            self.pipeline_metrics["pipelines_completed"] += 1
            self.metrics_collector.increment_counter("pipelines_completed")
        else:
            self.pipeline_metrics["pipelines_failed"] += 1
            self.metrics_collector.increment_counter("pipelines_failed")
        
        self.pipeline_metrics["total_execution_time"] += execution_time
        self.pipeline_metrics["total_ideas_generated"] += ideas_count
        
        self.metrics_collector.record_timer("pipeline_execution_time", execution_time)
        self.metrics_collector.record_histogram("ideas_generated", ideas_count)
        
        # Update success rate
        total = self.pipeline_metrics["pipelines_started"]
        if total > 0:
            success_rate = (self.pipeline_metrics["pipelines_completed"] / total) * 100
            self.metrics_collector.set_gauge("pipeline_success_rate", success_rate)
    
    def get_dashboard_data(self) -> dict[str, Any]:
        """Get data for monitoring dashboard."""
        return {
            "system_metrics": {
                "cpu_percent": self.metrics_collector.gauges.get("system_cpu_percent", 0),
                "memory_percent": self.metrics_collector.gauges.get("system_memory_percent", 0),
                "disk_percent": self.metrics_collector.gauges.get("system_disk_percent", 0),
                "process_memory_mb": self.metrics_collector.gauges.get("process_memory_bytes", 0) / (1024 * 1024),
            },
            "pipeline_metrics": self.pipeline_metrics.copy(),
            "active_alerts": [alert.to_dict() for alert in self.alert_manager.get_active_alerts()],
            "recent_metrics": {
                name: self.metrics_collector.get_metric_summary(name)
                for name in ["pipeline_execution_time", "ideas_generated", "pipeline_success_rate"]
                if name in self.metrics_collector.metrics
            }
        }


# Global monitoring system instance
_global_monitoring_system = MonitoringSystem()


def get_monitoring_system() -> MonitoringSystem:
    """Get the global monitoring system instance."""
    return _global_monitoring_system


def start_monitoring() -> None:
    """Start the global monitoring system."""
    _global_monitoring_system.start()


def stop_monitoring() -> None:
    """Stop the global monitoring system."""
    _global_monitoring_system.stop()
