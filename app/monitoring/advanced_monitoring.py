"""
Advanced Monitoring System with AI-Powered Insights
Real-time monitoring, anomaly detection, and predictive analytics
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging
from collections import defaultdict, deque
import numpy as np
import pandas as pd
from scipy import stats
import redis
from pathlib import Path
import pickle
from concurrent.futures import ThreadPoolExecutor
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Metric:
    """Metric data point"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    labels: Dict[str, str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = {}
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'value': self.value,
            'type': self.metric_type.value,
            'timestamp': self.timestamp.isoformat(),
            'labels': self.labels,
            'tags': self.tags
        }


@dataclass
class Alert:
    """Alert data"""
    alert_id: str
    name: str
    severity: AlertSeverity
    message: str
    metric_name: str
    current_value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'name': self.name,
            'severity': self.severity.value,
            'message': self.message,
            'metric_name': self.metric_name,
            'current_value': self.current_value,
            'threshold': self.threshold,
            'timestamp': self.timestamp.isoformat(),
            'resolved': self.resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }


@dataclass
class MonitoringConfig:
    """Monitoring system configuration"""
    metrics_retention_days: int = 30
    alerts_retention_days: int = 7
    anomaly_detection_enabled: bool = True
    predictive_analytics_enabled: bool = True
    alert_thresholds: Dict[str, Dict[str, float]] = None
    sampling_interval: float = 60.0  # seconds
    anomaly_threshold: float = 0.1
    prediction_horizon_hours: int = 24
    
    def __post_init__(self):
        if self.alert_thresholds is None:
            self.alert_thresholds = {
                'cpu_usage': {'warning': 70, 'critical': 90},
                'memory_usage': {'warning': 80, 'critical': 95},
                'response_time': {'warning': 2.0, 'critical': 5.0},
                'error_rate': {'warning': 0.05, 'critical': 0.10},
                'throughput': {'warning': 100, 'critical': 50}
            }


class MetricsCollector:
    """Advanced metrics collector with time-series storage"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", config: MonitoringConfig = None):
        self.redis_client = redis.from_url(redis_url)
        self.config = config or MonitoringConfig()
        self.metrics_buffer: deque = deque(maxlen=10000)
        self.aggregated_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
    def record_metric(self, name: str, value: float, metric_type: MetricType = MetricType.GAUGE,
                      labels: Dict[str, str] = None, tags: List[str] = None) -> None:
        """Record a metric"""
        
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            timestamp=datetime.utcnow(),
            labels=labels or {},
            tags=tags or []
        )
        
        # Add to buffer
        self.metrics_buffer.append(metric)
        
        # Store in Redis with time-series key
        self._store_metric(metric)
        
        # Update aggregates
        self._update_aggregates(metric)
    
    def _store_metric(self, metric: Metric) -> None:
        """Store metric in Redis time-series"""
        
        # Create time-series key
        ts_key = f"metrics:{metric.name}"
        
        # Store with timestamp as score
        timestamp_score = metric.timestamp.timestamp()
        
        # Store metric data
        metric_data = json.dumps({
            'value': metric.value,
            'type': metric.metric_type.value,
            'labels': metric.labels,
            'tags': metric.tags
        })
        
        self.redis_client.zadd(ts_key, {metric_data: timestamp_score})
        
        # Set expiration for retention
        self.redis_client.expire(ts_key, self.config.metrics_retention_days * 24 * 3600)
    
    def _update_aggregates(self, metric: Metric) -> None:
        """Update aggregated metrics"""
        
        key = f"{metric.name}:{':'.join(f'{k}={v}' for k, v in metric.labels.items())}"
        
        if key not in self.aggregated_metrics:
            self.aggregated_metrics[key] = {
                'count': 0,
                'sum': 0.0,
                'min': float('inf'),
                'max': float('-inf'),
                'values': deque(maxlen=1000)  # Keep last 1000 values for stats
            }
        
        agg = self.aggregated_metrics[key]
        agg['count'] += 1
        agg['sum'] += metric.value
        agg['min'] = min(agg['min'], metric.value)
        agg['max'] = max(agg['max'], metric.value)
        agg['values'].append(metric.value)
    
    def get_metrics(self, name: str, start_time: datetime = None, end_time: datetime = None,
                    labels: Dict[str, str] = None) -> List[Metric]:
        """Get metrics with optional filtering"""
        
        start_score = start_time.timestamp() if start_time else 0
        end_score = end_time.timestamp() if end_time else float('inf')
        
        # Get from Redis
        ts_key = f"metrics:{name}"
        metric_data = self.redis_client.zrangebyscore(ts_key, start_score, end_score)
        
        metrics = []
        for data in metric_data:
            try:
                parsed = json.loads(data)
                metric = Metric(
                    name=name,
                    value=parsed['value'],
                    metric_type=MetricType(parsed['type']),
                    timestamp=datetime.fromtimestamp(float(data.split(' ')[-1])),
                    labels=parsed.get('labels', {}),
                    tags=parsed.get('tags', [])
                )
                
                # Apply label filter if provided
                if labels:
                    for k, v in labels.items():
                        if metric.labels.get(k) != v:
                            break
                    else:
                        metrics.append(metric)
                else:
                    metrics.append(metric)
                    
            except Exception as e:
                logger.warning(f"Error parsing metric data: {e}")
        
        return metrics
    
    def get_aggregated_metrics(self, name: str, labels: Dict[str, str] = None) -> Dict[str, Any]:
        """Get aggregated metrics"""
        
        key = f"{name}:{':'.join(f'{k}={v}' for k, v in labels.items())}" if labels else name
        
        if key in self.aggregated_metrics:
            agg = self.aggregated_metrics[key]
            values = list(agg['values'])
            
            if values:
                return {
                    'count': agg['count'],
                    'sum': agg['sum'],
                    'min': agg['min'],
                    'max': agg['max'],
                    'avg': agg['sum'] / agg['count'],
                    'median': np.median(values),
                    'std': np.std(values),
                    'p95': np.percentile(values, 95),
                    'p99': np.percentile(values, 99)
                }
        
        return {}
    
    def get_metric_names(self) -> List[str]:
        """Get all available metric names"""
        
        pattern = "metrics:*"
        keys = self.redis_client.keys(pattern)
        
        return [key.decode().replace('metrics:', '') for key in keys]


class AnomalyDetector:
    """AI-powered anomaly detection for metrics"""
    
    def __init__(self, config: MonitoringConfig = None):
        self.config = config or MonitoringConfig()
        self.models: Dict[str, IsolationForest] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.anomaly_history: List[Dict[str, Any]] = []
        
    def train_anomaly_model(self, metric_name: str, historical_data: List[float]) -> bool:
        """Train anomaly detection model for a metric"""
        
        if len(historical_data) < 100:
            logger.warning(f"Insufficient data for anomaly detection model for {metric_name}")
            return False
        
        try:
            # Prepare data
            data = np.array(historical_data).reshape(-1, 1)
            
            # Scale data
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(data)
            
            # Train model
            model = IsolationForest(
                contamination=self.config.anomaly_threshold,
                random_state=42,
                n_estimators=100
            )
            model.fit(scaled_data)
            
            # Store model and scaler
            self.models[metric_name] = model
            self.scalers[metric_name] = scaler
            
            logger.info(f"Trained anomaly detection model for {metric_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error training anomaly model for {metric_name}: {e}")
            return False
    
    def detect_anomaly(self, metric_name: str, value: float) -> Dict[str, Any]:
        """Detect if a metric value is anomalous"""
        
        if metric_name not in self.models:
            return {'anomaly': False, 'score': 0.0, 'reason': 'No model trained'}
        
        try:
            # Scale the value
            scaler = self.scalers[metric_name]
            scaled_value = scaler.transform([[value]])[0][0]
            
            # Predict anomaly
            model = self.models[metric_name]
            prediction = model.predict([[scaled_value]])[0]
            score = model.decision_function([[scaled_value]])[0]
            
            is_anomaly = prediction == -1
            
            result = {
                'anomaly': is_anomaly,
                'score': float(score),
                'value': value,
                'threshold': self.config.anomaly_threshold,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if is_anomaly:
                result['reason'] = f"Value {value} is anomalous (score: {score:.3f})"
                self.anomaly_history.append(result)
            else:
                result['reason'] = f"Value {value} is normal (score: {score:.3f})"
            
            return result
            
        except Exception as e:
            logger.error(f"Error detecting anomaly for {metric_name}: {e}")
            return {'anomaly': False, 'score': 0.0, 'reason': f'Error: {str(e)}'}
    
    def get_anomaly_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get anomaly summary for recent period"""
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_anomalies = [
            a for a in self.anomaly_history
            if datetime.fromisoformat(a['timestamp']) > cutoff_time
        ]
        
        # Group by metric
        anomalies_by_metric = defaultdict(list)
        for anomaly in recent_anomalies:
            metric_name = anomaly.get('metric_name', 'unknown')
            anomalies_by_metric[metric_name].append(anomaly)
        
        return {
            'total_anomalies': len(recent_anomalies),
            'anomalies_by_metric': {
                metric: len(anomalies)
                for metric, anomalies in anomalies_by_metric.items()
            },
            'most_anomalous_metrics': sorted(
                anomalies_by_metric.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:5],
            'anomaly_rate': len(recent_anomalies) / (hours * 60) if hours > 0 else 0  # per minute
        }


class AlertManager:
    """Advanced alert management system"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", config: MonitoringConfig = None):
        self.redis_client = redis.from_url(redis_url)
        self.config = config or MonitoringConfig()
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.alert_rules: Dict[str, Dict[str, Any]] = self._load_alert_rules()
        
    def _load_alert_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load alert rules"""
        rules = {}
        
        for metric_name, thresholds in self.config.alert_thresholds.items():
            rules[metric_name] = {
                'warning_threshold': thresholds.get('warning', 70),
                'critical_threshold': thresholds.get('critical', 90),
                'evaluation_window': 300,  # 5 minutes
                'consecutive_breaches': 2
            }
        
        return rules
    
    def evaluate_metric(self, metric: Metric) -> List[Alert]:
        """Evaluate metric against alert rules"""
        
        alerts = []
        
        if metric.name not in self.alert_rules:
            return alerts
        
        rule = self.alert_rules[metric.name]
        
        # Check thresholds
        if metric.value >= rule['critical_threshold']:
            severity = AlertSeverity.CRITICAL
            threshold = rule['critical_threshold']
        elif metric.value >= rule['warning_threshold']:
            severity = AlertSeverity.WARNING
            threshold = rule['warning_threshold']
        else:
            return alerts
        
        # Create alert
        alert_id = f"{metric.name}_{severity.value}_{int(metric.timestamp.timestamp())}"
        
        alert = Alert(
            alert_id=alert_id,
            name=f"{metric.name} {severity.value.upper()}",
            severity=severity,
            message=f"{metric.name} is {metric.value} (threshold: {threshold})",
            metric_name=metric.name,
            current_value=metric.value,
            threshold=threshold,
            timestamp=metric.timestamp
        )
        
        alerts.append(alert)
        
        # Store alert
        self._store_alert(alert)
        
        return alerts
    
    def _store_alert(self, alert: Alert) -> None:
        """Store alert in Redis"""
        
        # Store active alert
        if not alert.resolved:
            self.active_alerts[alert.alert_id] = alert
        
        # Store in Redis
        alert_data = json.dumps(alert.to_dict())
        self.redis_client.set(f"alert:{alert.alert_id}", alert_data)
        self.redis_client.expire(f"alert:{alert.alert_id}", self.config.alerts_retention_days * 24 * 3600)
        
        # Add to history
        self.alert_history.append(alert)
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            
            # Update in Redis
            alert_data = json.dumps(alert.to_dict())
            self.redis_client.set(f"alert:{alert_id}", alert_data)
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
            
            logger.info(f"Resolved alert: {alert_id}")
            return True
        
        return False
    
    def get_active_alerts(self, severity: AlertSeverity = None) -> List[Alert]:
        """Get active alerts"""
        
        alerts = list(self.active_alerts.values())
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    def get_alert_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert summary for recent period"""
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_alerts = [
            a for a in self.alert_history
            if a.timestamp > cutoff_time
        ]
        
        # Group by severity
        alerts_by_severity = defaultdict(int)
        alerts_by_metric = defaultdict(int)
        
        for alert in recent_alerts:
            alerts_by_severity[alert.severity.value] += 1
            alerts_by_metric[alert.metric_name] += 1
        
        return {
            'total_alerts': len(recent_alerts),
            'active_alerts': len(self.active_alerts),
            'alerts_by_severity': dict(alerts_by_severity),
            'alerts_by_metric': dict(alerts_by_metric),
            'most_alerting_metrics': sorted(
                alerts_by_metric.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }


class PredictiveAnalytics:
    """Predictive analytics for metrics forecasting"""
    
    def __init__(self, config: MonitoringConfig = None):
        self.config = config or MonitoringConfig()
        self.forecast_models: Dict[str, Dict[str, Any]] = {}
        
    def train_forecast_model(self, metric_name: str, historical_data: List[float]) -> bool:
        """Train forecasting model for a metric"""
        
        if len(historical_data) < 50:
            logger.warning(f"Insufficient data for forecasting model for {metric_name}")
            return False
        
        try:
            # Simple linear regression for trend
            x = np.arange(len(historical_data))
            y = np.array(historical_data)
            
            # Fit linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            # Calculate seasonal patterns (simple approach)
            if len(historical_data) >= 24:  # Need at least 24 points for hourly patterns
                seasonal_pattern = self._calculate_seasonal_pattern(historical_data)
            else:
                seasonal_pattern = []
            
            # Store model
            self.forecast_models[metric_name] = {
                'slope': slope,
                'intercept': intercept,
                'r_squared': r_value ** 2,
                'p_value': p_value,
                'std_err': std_err,
                'seasonal_pattern': seasonal_pattern,
                'last_values': historical_data[-10:],  # Keep last 10 values
                'trained_at': datetime.utcnow()
            }
            
            logger.info(f"Trained forecast model for {metric_name} (R²: {r_value ** 2:.3f})")
            return True
            
        except Exception as e:
            logger.error(f"Error training forecast model for {metric_name}: {e}")
            return False
    
    def _calculate_seasonal_pattern(self, data: List[float]) -> List[float]:
        """Calculate seasonal pattern (24-hour cycle)"""
        
        if len(data) < 24:
            return []
        
        # Calculate hourly averages
        hourly_avgs = []
        for hour in range(24):
            hour_values = []
            for i, value in enumerate(data):
                if i % 24 == hour:
                    hour_values.append(value)
            
            if hour_values:
                hourly_avgs.append(np.mean(hour_values))
            else:
                hourly_avgs.append(0)
        
        # Normalize pattern
        if hourly_avgs:
            avg = np.mean(hourly_avgs)
            if avg > 0:
                hourly_avgs = [h / avg for h in hourly_avgs]
        
        return hourly_avgs
    
    def forecast_metric(self, metric_name: str, hours_ahead: int = 24) -> Dict[str, Any]:
        """Forecast metric values"""
        
        if metric_name not in self.forecast_models:
            return {'error': 'No forecast model available'}
        
        try:
            model = self.forecast_models[metric_name]
            
            # Generate forecast
            forecast = []
            current_time = len(model['last_values'])
            
            for i in range(hours_ahead):
                # Linear trend
                trend_value = model['slope'] * (current_time + i) + model['intercept']
                
                # Add seasonal pattern if available
                seasonal_multiplier = 1.0
                if model['seasonal_pattern']:
                    hour = (current_time + i) % 24
                    seasonal_multiplier = model['seasonal_pattern'][hour]
                
                forecast_value = trend_value * seasonal_multiplier
                forecast.append(forecast_value)
            
            # Calculate confidence intervals (simple approach)
            std_error = model['std_err']
            confidence_interval = 1.96 * std_error  # 95% confidence
            
            return {
                'metric_name': metric_name,
                'forecast_hours': hours_ahead,
                'forecast_values': forecast,
                'confidence_interval': confidence_interval,
                'model_r_squared': model['r_squared'],
                'forecast_generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error forecasting {metric_name}: {e}")
            return {'error': str(e)}
    
    def get_capacity_prediction(self, metric_name: str, threshold: float) -> Dict[str, Any]:
        """Predict when metric will reach threshold"""
        
        forecast_result = self.forecast_metric(metric_name, 72)  # 3 days ahead
        
        if 'error' in forecast_result:
            return forecast_result
        
        forecast_values = forecast_result['forecast_values']
        
        # Find when threshold will be reached
        for i, value in enumerate(forecast_values):
            if value >= threshold:
                hours_to_threshold = i + 1
                threshold_time = datetime.utcnow() + timedelta(hours=hours_to_threshold)
                
                return {
                    'metric_name': metric_name,
                    'threshold': threshold,
                    'hours_to_threshold': hours_to_threshold,
                    'threshold_time': threshold_time.isoformat(),
                    'predicted_value': value,
                    'confidence': 'medium' if forecast_result['model_r_squared'] > 0.7 else 'low'
                }
        
        return {
            'metric_name': metric_name,
            'threshold': threshold,
            'hours_to_threshold': None,
            'threshold_time': None,
            'message': f'Threshold not expected to be reached in next 72 hours'
        }


class AdvancedMonitoringSystem:
    """Complete advanced monitoring system"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", config: MonitoringConfig = None):
        self.config = config or MonitoringConfig()
        self.metrics_collector = MetricsCollector(redis_url, config)
        self.anomaly_detector = AnomalyDetector(config)
        self.alert_manager = AlertManager(redis_url, config)
        self.predictive_analytics = PredictiveAnalytics(config)
        self.monitoring_active = False
        
    async def start_monitoring(self) -> None:
        """Start the monitoring system"""
        
        self.monitoring_active = True
        logger.info("Advanced monitoring system started")
        
        # Start background tasks
        asyncio.create_task(self._monitoring_loop())
        asyncio.create_task(self._anomaly_detection_loop())
        asyncio.create_task(self._predictive_analytics_loop())
    
    async def stop_monitoring(self) -> None:
        """Stop the monitoring system"""
        
        self.monitoring_active = False
        logger.info("Advanced monitoring system stopped")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        
        while self.monitoring_active:
            try:
                # Collect system metrics
                await self._collect_system_metrics()
                
                # Evaluate alerts
                await self._evaluate_alerts()
                
                # Sleep until next collection
                await asyncio.sleep(self.config.sampling_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)
    
    async def _collect_system_metrics(self) -> None:
        """Collect system metrics"""
        
        import psutil
        
        # CPU usage
        cpu_percent = psutil.cpu_percent()
        self.metrics_collector.record_metric('cpu_usage', cpu_percent, MetricType.GAUGE)
        
        # Memory usage
        memory = psutil.virtual_memory()
        self.metrics_collector.record_metric('memory_usage', memory.percent, MetricType.GAUGE)
        self.metrics_collector.record_metric('memory_available', memory.available, MetricType.GAUGE)
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        self.metrics_collector.record_metric('disk_usage', disk_percent, MetricType.GAUGE)
        
        # Network I/O
        network = psutil.net_io_counters()
        self.metrics_collector.record_metric('network_bytes_sent', network.bytes_sent, MetricType.COUNTER)
        self.metrics_collector.record_metric('network_bytes_recv', network.bytes_recv, MetricType.COUNTER)
    
    async def _evaluate_alerts(self) -> None:
        """Evaluate metrics for alerts"""
        
        # Get recent metrics
        metric_names = self.metrics_collector.get_metric_names()
        
        for metric_name in metric_names:
            # Get latest metric
            recent_metrics = self.metrics_collector.get_metrics(
                metric_name,
                start_time=datetime.utcnow() - timedelta(minutes=5)
            )
            
            if recent_metrics:
                latest_metric = recent_metrics[-1]
                alerts = self.alert_manager.evaluate_metric(latest_metric)
                
                # Log alerts
                for alert in alerts:
                    logger.warning(f"ALERT: {alert.message}")
    
    async def _anomaly_detection_loop(self) -> None:
        """Anomaly detection loop"""
        
        while self.monitoring_active:
            try:
                # Run every 10 minutes
                await asyncio.sleep(600)
                
                if not self.config.anomaly_detection_enabled:
                    continue
                
                # Get metrics for anomaly detection
                metric_names = self.metrics_collector.get_metric_names()
                
                for metric_name in metric_names:
                    # Get historical data
                    historical_metrics = self.metrics_collector.get_metrics(
                        metric_name,
                        start_time=datetime.utcnow() - timedelta(days=7)
                    )
                    
                    if len(historical_metrics) >= 100:
                        # Train or update model
                        values = [m.value for m in historical_metrics]
                        self.anomaly_detector.train_anomaly_model(metric_name, values)
                        
                        # Check latest value for anomaly
                        latest_metric = historical_metrics[-1]
                        anomaly_result = self.anomaly_detector.detect_anomaly(
                            metric_name, latest_metric.value
                        )
                        
                        if anomaly_result['anomaly']:
                            logger.warning(f"ANOMALY DETECTED: {metric_name} = {latest_metric.value}")
                
            except Exception as e:
                logger.error(f"Error in anomaly detection loop: {e}")
    
    async def _predictive_analytics_loop(self) -> None:
        """Predictive analytics loop"""
        
        while self.monitoring_active:
            try:
                # Run every hour
                await asyncio.sleep(3600)
                
                if not self.config.predictive_analytics_enabled:
                    continue
                
                # Get metrics for prediction
                metric_names = self.metrics_collector.get_metric_names()
                
                for metric_name in metric_names:
                    # Get historical data
                    historical_metrics = self.metrics_collector.get_metrics(
                        metric_name,
                        start_time=datetime.utcnow() - timedelta(days=7)
                    )
                    
                    if len(historical_metrics) >= 50:
                        # Train forecast model
                        values = [m.value for m in historical_metrics]
                        self.predictive_analytics.train_forecast_model(metric_name, values)
                
            except Exception as e:
                logger.error(f"Error in predictive analytics loop: {e}")
    
    def record_custom_metric(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Record a custom metric"""
        
        self.metrics_collector.record_metric(name, value, MetricType.GAUGE, labels)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard"""
        
        return {
            'system_metrics': {
                'cpu_usage': self.metrics_collector.get_aggregated_metrics('cpu_usage'),
                'memory_usage': self.metrics_collector.get_aggregated_metrics('memory_usage'),
                'disk_usage': self.metrics_collector.get_aggregated_metrics('disk_usage')
            },
            'active_alerts': [alert.to_dict() for alert in self.alert_manager.get_active_alerts()],
            'alert_summary': self.alert_manager.get_alert_summary(),
            'anomaly_summary': self.anomaly_detector.get_anomaly_summary(),
            'metric_names': self.metrics_collector.get_metric_names()
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        
        active_alerts = self.alert_manager.get_active_alerts()
        critical_alerts = [a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]
        
        # Determine health status
        if critical_alerts:
            status = 'critical'
            status_color = 'red'
        elif active_alerts:
            status = 'warning'
            status_color = 'yellow'
        else:
            status = 'healthy'
            status_color = 'green'
        
        return {
            'status': status,
            'color': status_color,
            'active_alerts_count': len(active_alerts),
            'critical_alerts_count': len(critical_alerts),
            'last_check': datetime.utcnow().isoformat(),
            'monitoring_active': self.monitoring_active
        }


# Example usage
async def example_usage():
    """Example of advanced monitoring usage"""
    
    config = MonitoringConfig(
        anomaly_detection_enabled=True,
        predictive_analytics_enabled=True,
        sampling_interval=30.0
    )
    
    monitoring = AdvancedMonitoringSystem(config=config)
    
    # Start monitoring
    await monitoring.start_monitoring()
    
    try:
        # Record some custom metrics
        for i in range(10):
            monitoring.record_custom_metric('response_time', 0.5 + i * 0.1, {'endpoint': '/api/ideas'})
            monitoring.record_custom_metric('throughput', 100 + i * 5, {'service': 'api-gateway'})
            await asyncio.sleep(1)
        
        # Get dashboard data
        dashboard_data = monitoring.get_dashboard_data()
        print(f"Dashboard data: {dashboard_data}")
        
        # Get health status
        health = monitoring.get_health_status()
        print(f"Health status: {health}")
        
        # Wait for some monitoring cycles
        await asyncio.sleep(120)
        
    finally:
        await monitoring.stop_monitoring()


if __name__ == "__main__":
    asyncio.run(example_usage())
