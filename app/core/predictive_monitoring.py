"""
Predictive Monitoring System for Asmblr
Advanced monitoring with AI-powered predictions and anomaly detection
"""

import asyncio
import time
import json
import numpy as np
from typing import Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
from loguru import logger
import redis.asyncio as redis
import psutil
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import joblib

class MetricType(Enum):
    """Types of metrics to monitor"""
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    NETWORK_IO = "network_io"
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    QUEUE_SIZE = "queue_size"
    CACHE_HIT_RATE = "cache_hit_rate"
    DATABASE_CONNECTIONS = "database_connections"

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class PredictionHorizon(Enum):
    """Prediction time horizons"""
    IMMEDIATE = "immediate"  # 5 minutes
    SHORT_TERM = "short_term"  # 30 minutes
    MEDIUM_TERM = "medium_term"  # 2 hours
    LONG_TERM = "long_term"  # 24 hours

@dataclass
class MetricData:
    """Single metric data point"""
    metric_type: MetricType
    value: float
    timestamp: datetime
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'metric_type': self.metric_type.value,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'metadata': self.metadata
        }

@dataclass
class Prediction:
    """Prediction result"""
    metric_type: MetricType
    predicted_value: float
    confidence: float
    horizon: PredictionHorizon
    timestamp: datetime
    model_used: str
    features: dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'metric_type': self.metric_type.value,
            'predicted_value': self.predicted_value,
            'confidence': self.confidence,
            'horizon': self.horizon.value,
            'timestamp': self.timestamp.isoformat(),
            'model_used': self.model_used,
            'features': self.features
        }

@dataclass
class Alert:
    """Alert definition"""
    id: str
    metric_type: MetricType
    severity: AlertSeverity
    message: str
    threshold: float
    actual_value: float
    predicted_value: float | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    resolved: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'id': self.id,
            'metric_type': self.metric_type.value,
            'severity': self.severity.value,
            'message': self.message,
            'threshold': self.threshold,
            'actual_value': self.actual_value,
            'predicted_value': self.predicted_value,
            'timestamp': self.timestamp.isoformat(),
            'acknowledged': self.acknowledged,
            'resolved': self.resolved,
            'metadata': self.metadata
        }

@dataclass
class MonitoringMetrics:
    """Monitoring system metrics"""
    total_metrics_collected: int = 0
    total_predictions_made: int = 0
    total_alerts_generated: int = 0
    anomaly_detection_accuracy: float = 0.0
    prediction_accuracy: float = 0.0
    avg_prediction_time: float = 0.0
    system_overhead: float = 0.0

class PredictiveMonitoringSystem:
    """AI-powered predictive monitoring system"""
    
    def __init__(self):
        self.metrics_data = defaultdict(deque)
        self.predictions = defaultdict(deque)
        self.alerts = {}
        self.models = {}
        self.scalers = {}
        
        # Monitoring configuration
        self.collection_interval = 30  # seconds
        self.prediction_interval = 300  # 5 minutes
        self.anomaly_threshold = 0.1  # 10% anomaly threshold
        self.alert_cooldown = 300  # 5 minutes
        
        # Data retention
        self.data_retention_hours = 24 * 7  # 1 week
        self.prediction_retention_hours = 24 * 3  # 3 days
        
        # Alert thresholds
        self.thresholds = {
            MetricType.CPU_USAGE: {'warning': 70, 'critical': 90},
            MetricType.MEMORY_USAGE: {'warning': 75, 'critical': 90},
            MetricType.DISK_USAGE: {'warning': 80, 'critical': 95},
            MetricType.RESPONSE_TIME: {'warning': 2.0, 'critical': 5.0},
            MetricType.ERROR_RATE: {'warning': 0.05, 'critical': 0.1},
            MetricType.QUEUE_SIZE: {'warning': 100, 'critical': 500}
        }
        
        # Redis for distributed monitoring
        self.redis_client = None
        self.redis_enabled = False
        
        # Background tasks
        self.collection_task = None
        self.prediction_task = None
        self.anomaly_task = None
        self.alert_task = None
        
        # Performance tracking
        self.metrics = MonitoringMetrics()
        self.performance_history = deque(maxlen=1000)
        
    async def initialize(self):
        """Initialize predictive monitoring system"""
        try:
            # Initialize Redis connection
            try:
                self.redis_client = redis.from_url(
                    "redis://localhost:6379/7",
                    max_connections=20
                )
                await self.redis_client.ping()
                self.redis_enabled = True
                logger.info("Redis connection established for predictive monitoring")
            except Exception as e:
                logger.warning(f"Redis not available, using local monitoring: {e}")
            
            # Initialize prediction models
            await self._initialize_models()
            
            # Start background tasks
            await self.start_background_tasks()
            
            logger.info("Predictive monitoring system initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize predictive monitoring: {e}")
            raise
    
    async def _initialize_models(self):
        """Initialize prediction models"""
        try:
            for metric_type in MetricType:
                # Initialize prediction model
                model = RandomForestRegressor(
                    n_estimators=100,
                    random_state=42,
                    max_depth=10
                )
                self.models[metric_type] = model
                
                # Initialize scaler
                scaler = StandardScaler()
                self.scalers[metric_type] = scaler
                
                logger.info(f"Initialized prediction model for {metric_type.value}")
            
        except Exception as e:
            logger.error(f"Model initialization error: {e}")
            raise
    
    async def collect_metric(
        self,
        metric_type: MetricType,
        value: float,
        source: str = "system",
        metadata: dict[str, Any] = None
    ):
        """Collect a metric data point"""
        try:
            metric_data = MetricData(
                metric_type=metric_type,
                value=value,
                timestamp=datetime.now(),
                source=source,
                metadata=metadata or {}
            )
            
            # Store in local deque
            self.metrics_data[metric_type].append(metric_data)
            
            # Store in Redis if enabled
            if self.redis_enabled:
                await self._store_metric(metric_data)
            
            # Update metrics
            self.metrics.total_metrics_collected += 1
            
            # Check for immediate alerts
            await self._check_threshold_alerts(metric_data)
            
            logger.debug(f"Collected metric {metric_type.value}: {value} from {source}")
            
        except Exception as e:
            logger.error(f"Failed to collect metric {metric_type.value}: {e}")
    
    async def predict_metric(
        self,
        metric_type: MetricType,
        horizon: PredictionHorizon = PredictionHorizon.SHORT_TERM,
        features: dict[str, float] | None = None
    ) -> Prediction | None:
        """Predict future metric value"""
        try:
            # Get historical data
            data_points = list(self.metrics_data[metric_type])
            
            if len(data_points) < 10:
                logger.warning(f"Insufficient data for prediction of {metric_type.value}: {len(data_points)} < 10")
                return None
            
            # Prepare features
            if features is None:
                features = await self._extract_features(metric_type, data_points)
            
            # Get model and scaler
            model = self.models[metric_type]
            scaler = self.scalers[metric_type]
            
            # Prepare feature vector
            feature_names = list(features.keys())
            feature_vector = np.array([features[name] for name in feature_names]).reshape(1, -1)
            
            # Scale features
            if hasattr(scaler, 'mean_'):
                feature_vector = scaler.transform(feature_vector)
            
            # Make prediction
            start_time = time.time()
            predicted_value = model.predict(feature_vector)[0]
            prediction_time = time.time() - start_time
            
            # Calculate confidence (simplified)
            if hasattr(model, 'predict_proba'):
                confidence = 0.8  # Placeholder
            else:
                # Use prediction variance as confidence proxy
                confidence = max(0.5, 1.0 - abs(predicted_value - features.get('current_value', 0)) / max(features.get('current_value', 1), 1))
            
            # Create prediction
            prediction = Prediction(
                metric_type=metric_type,
                predicted_value=predicted_value,
                confidence=confidence,
                horizon=horizon,
                timestamp=datetime.now(),
                model_used=type(model).__name__,
                features=features
            )
            
            # Store prediction
            self.predictions[metric_type].append(prediction)
            
            # Update metrics
            self.metrics.total_predictions_made += 1
            self.metrics.avg_prediction_time = (
                (self.metrics.avg_prediction_time * (self.metrics.total_predictions_made - 1) + prediction_time) /
                self.metrics.total_predictions_made
            )
            
            # Store in Redis if enabled
            if self.redis_enabled:
                await self._store_prediction(prediction)
            
            # Check for predictive alerts
            await self._check_predictive_alerts(prediction)
            
            logger.info(f"Predicted {metric_type.value} for {horizon.value}: {predicted_value:.2f} (confidence: {confidence:.2f})")
            
            return prediction
            
        except Exception as e:
            logger.error(f"Prediction error for {metric_type.value}: {e}")
            return None
    
    async def _extract_features(self, metric_type: MetricType, data_points: list[MetricData]) -> dict[str, float]:
        """Extract features from historical data"""
        try:
            if not data_points:
                return {}
            
            values = [dp.value for dp in data_points]
            timestamps = [dp.timestamp for dp in data_points]
            
            # Basic statistical features
            features = {
                'current_value': values[-1],
                'mean_5': np.mean(values[-5:]),
                'mean_10': np.mean(values[-10:]),
                'mean_30': np.mean(values[-30:]) if len(values) >= 30 else np.mean(values),
                'std_5': np.std(values[-5:]),
                'std_10': np.std(values[-10:]),
                'min_10': min(values[-10:]),
                'max_10': max(values[-10:]),
                'trend_5': (values[-1] - values[-5]) / 5 if len(values) >= 5 else 0,
                'trend_10': (values[-1] - values[-10]) / 10 if len(values) >= 10 else 0,
                'volatility_10': np.std(values[-10:]) / np.mean(values[-10:]) if np.mean(values[-10:]) > 0 else 0,
            }
            
            # Time-based features
            current_time = datetime.now()
            features['hour_of_day'] = current_time.hour / 24.0
            features['day_of_week'] = current_time.weekday() / 7.0
            features['is_weekend'] = 1.0 if current_time.weekday() >= 5 else 0.0
            
            # System features
            features['cpu_usage'] = psutil.cpu_percent() / 100.0
            features['memory_usage'] = psutil.virtual_memory().percent / 100.0
            
            return features
            
        except Exception as e:
            logger.error(f"Feature extraction error for {metric_type.value}: {e}")
            return {}
    
    async def detect_anomalies(self, metric_type: MetricType) -> list[MetricData]:
        """Detect anomalies in metric data"""
        try:
            data_points = list(self.metrics_data[metric_type])
            
            if len(data_points) < 20:
                return []
            
            # Use Isolation Forest for anomaly detection
            values = np.array([dp.value for dp in data_points]).reshape(-1, 1)
            
            # Fit model
            isolation_forest = IsolationForest(contamination=self.anomaly_threshold, random_state=42)
            anomaly_scores = isolation_forest.fit_predict(values)
            
            # Identify anomalies
            anomalies = []
            for i, (data_point, score) in enumerate(zip(data_points, anomaly_scores)):
                if score == -1:  # Anomaly
                    anomalies.append(data_point)
                    
                    # Generate anomaly alert
                    await self._generate_anomaly_alert(data_point, metric_type)
            
            logger.info(f"Detected {len(anomalies)} anomalies for {metric_type.value}")
            return anomalies
            
        except Exception as e:
            logger.error(f"Anomaly detection error for {metric_type.value}: {e}")
            return []
    
    async def _check_threshold_alerts(self, metric_data: MetricData):
        """Check for threshold-based alerts"""
        try:
            metric_type = metric_data.metric_type
            value = metric_data.value
            
            if metric_type not in self.thresholds:
                return
            
            thresholds = self.thresholds[metric_type]
            
            # Check critical threshold
            if value >= thresholds['critical']:
                await self._create_alert(
                    metric_type=metric_type,
                    severity=AlertSeverity.CRITICAL,
                    threshold=thresholds['critical'],
                    actual_value=value,
                    message=f"Critical threshold exceeded for {metric_type.value}: {value:.2f} >= {thresholds['critical']}"
                )
            
            # Check warning threshold
            elif value >= thresholds['warning']:
                await self._create_alert(
                    metric_type=metric_type,
                    severity=AlertSeverity.WARNING,
                    threshold=thresholds['warning'],
                    actual_value=value,
                    message=f"Warning threshold exceeded for {metric_type.value}: {value:.2f} >= {thresholds['warning']}"
                )
            
        except Exception as e:
            logger.error(f"Threshold alert check error: {e}")
    
    async def _check_predictive_alerts(self, prediction: Prediction):
        """Check for predictive alerts"""
        try:
            metric_type = prediction.metric_type
            predicted_value = prediction.predicted_value
            confidence = prediction.confidence
            
            if metric_type not in self.thresholds:
                return
            
            thresholds = self.thresholds[metric_type]
            
            # Only alert if confidence is high enough
            if confidence < 0.7:
                return
            
            # Check critical prediction
            if predicted_value >= thresholds['critical']:
                await self._create_alert(
                    metric_type=metric_type,
                    severity=AlertSeverity.CRITICAL,
                    threshold=thresholds['critical'],
                    actual_value=None,
                    predicted_value=predicted_value,
                    message=f"Critical threshold predicted for {metric_type.value} in {prediction.horizon.value}: {predicted_value:.2f} >= {thresholds['critical']} (confidence: {confidence:.2f})"
                )
            
            # Check warning prediction
            elif predicted_value >= thresholds['warning']:
                await self._create_alert(
                    metric_type=metric_type,
                    severity=AlertSeverity.WARNING,
                    threshold=thresholds['warning'],
                    actual_value=None,
                    predicted_value=predicted_value,
                    message=f"Warning threshold predicted for {metric_type.value} in {prediction.horizon.value}: {predicted_value:.2f} >= {thresholds['warning']} (confidence: {confidence:.2f})"
                )
            
        except Exception as e:
            logger.error(f"Predictive alert check error: {e}")
    
    async def _generate_anomaly_alert(self, metric_data: MetricData, metric_type: MetricType):
        """Generate anomaly alert"""
        try:
            await self._create_alert(
                metric_type=metric_type,
                severity=AlertSeverity.WARNING,
                threshold=0.0,  # Anomalies don't have thresholds
                actual_value=metric_data.value,
                message=f"Anomaly detected for {metric_type.value}: {metric_data.value:.2f} at {metric_data.timestamp.isoformat()}"
            )
            
        except Exception as e:
            logger.error(f"Anomaly alert generation error: {e}")
    
    async def _create_alert(
        self,
        metric_type: MetricType,
        severity: AlertSeverity,
        threshold: float,
        actual_value: float | None,
        predicted_value: float | None = None,
        message: str = ""
    ):
        """Create an alert"""
        try:
            alert_id = f"{metric_type.value}_{severity.value}_{int(time.time())}"
            
            # Check cooldown
            recent_alerts = [
                alert for alert in self.alerts.values()
                if alert.metric_type == metric_type and
                alert.severity == severity and
                (datetime.now() - alert.timestamp).total_seconds() < self.alert_cooldown
            ]
            
            if recent_alerts:
                logger.debug(f"Alert cooldown active for {metric_type.value} {severity.value}")
                return
            
            alert = Alert(
                id=alert_id,
                metric_type=metric_type,
                severity=severity,
                message=message,
                threshold=threshold,
                actual_value=actual_value or 0.0,
                predicted_value=predicted_value
            )
            
            self.alerts[alert_id] = alert
            self.metrics.total_alerts_generated += 1
            
            # Store in Redis if enabled
            if self.redis_enabled:
                await self._store_alert(alert)
            
            logger.warning(f"Alert generated: {message}")
            
        except Exception as e:
            logger.error(f"Alert creation error: {e}")
    
    async def start_background_tasks(self):
        """Start background monitoring tasks"""
        self.collection_task = asyncio.create_task(self._collection_loop())
        self.prediction_task = asyncio.create_task(self._prediction_loop())
        self.anomaly_task = asyncio.create_task(self._anomaly_detection_loop())
        self.alert_task = asyncio.create_task(self._alert_management_loop())
        
        logger.info("Background monitoring tasks started")
    
    async def _collection_loop(self):
        """Background metric collection loop"""
        while True:
            try:
                # Collect system metrics
                await self._collect_system_metrics()
                
                await asyncio.sleep(self.collection_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metric collection error: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _prediction_loop(self):
        """Background prediction loop"""
        while True:
            try:
                # Make predictions for all metrics
                for metric_type in MetricType:
                    await self.predict_metric(metric_type)
                
                await asyncio.sleep(self.prediction_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Prediction loop error: {e}")
                await asyncio.sleep(self.prediction_interval)
    
    async def _anomaly_detection_loop(self):
        """Background anomaly detection loop"""
        while True:
            try:
                # Detect anomalies for all metrics
                for metric_type in MetricType:
                    await self.detect_anomalies(metric_type)
                
                await asyncio.sleep(600)  # Check every 10 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Anomaly detection loop error: {e}")
                await asyncio.sleep(600)
    
    async def _alert_management_loop(self):
        """Background alert management loop"""
        while True:
            try:
                # Clean up old alerts
                await self._cleanup_old_alerts()
                
                # Update alert status
                await self._update_alert_status()
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Alert management loop error: {e}")
                await asyncio.sleep(300)
    
    async def _collect_system_metrics(self):
        """Collect system metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            await self.collect_metric(MetricType.CPU_USAGE, cpu_percent, "system")
            
            # Memory usage
            memory = psutil.virtual_memory()
            await self.collect_metric(MetricType.MEMORY_USAGE, memory.percent, "system")
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            await self.collect_metric(MetricType.DISK_USAGE, disk_percent, "system")
            
            # Network I/O
            network = psutil.net_io_counters()
            network_bytes = network.bytes_sent + network.bytes_recv
            await self.collect_metric(MetricType.NETWORK_IO, network_bytes, "system")
            
        except Exception as e:
            logger.error(f"System metrics collection error: {e}")
    
    async def _cleanup_old_alerts(self):
        """Clean up old alerts"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            old_alerts = [
                alert_id for alert_id, alert in self.alerts.items()
                if alert.timestamp < cutoff_time
            ]
            
            for alert_id in old_alerts:
                del self.alerts[alert_id]
            
            if old_alerts:
                logger.info(f"Cleaned up {len(old_alerts)} old alerts")
            
        except Exception as e:
            logger.error(f"Alert cleanup error: {e}")
    
    async def _update_alert_status(self):
        """Update alert status based on current conditions"""
        try:
            for alert in self.alerts.values():
                if alert.resolved:
                    continue
                
                # Check if condition is still present
                if alert.actual_value is not None:
                    # Check if current value is still above threshold
                    current_data = list(self.metrics_data[alert.metric_type])
                    if current_data:
                        current_value = current_data[-1].value
                        if current_value < alert.threshold:
                            alert.resolved = True
                            alert.metadata['resolved_at'] = datetime.now().isoformat()
                            logger.info(f"Alert resolved: {alert.id}")
            
        except Exception as e:
            logger.error(f"Alert status update error: {e}")
    
    async def _store_metric(self, metric_data: MetricData):
        """Store metric in Redis"""
        try:
            key = f"metric:{metric_data.metric_type.value}:{metric_data.timestamp.isoformat()}"
            await self.redis_client.setex(
                key,
                self.data_retention_hours * 3600,
                json.dumps(metric_data.to_dict())
            )
        except Exception as e:
            logger.error(f"Redis metric storage error: {e}")
    
    async def _store_prediction(self, prediction: Prediction):
        """Store prediction in Redis"""
        try:
            key = f"prediction:{prediction.metric_type.value}:{prediction.timestamp.isoformat()}"
            await self.redis_client.setex(
                key,
                self.prediction_retention_hours * 3600,
                json.dumps(prediction.to_dict())
            )
        except Exception as e:
            logger.error(f"Redis prediction storage error: {e}")
    
    async def _store_alert(self, alert: Alert):
        """Store alert in Redis"""
        try:
            key = f"alert:{alert.id}"
            await self.redis_client.setex(
                key,
                24 * 3600,  # 24 hours
                json.dumps(alert.to_dict())
            )
        except Exception as e:
            logger.error(f"Redis alert storage error: {e}")
    
    async def get_metrics_summary(self, metric_type: MetricType | None = None) -> dict[str, Any]:
        """Get metrics summary"""
        try:
            summary = {
                'total_metrics': self.metrics.total_metrics_collected,
                'total_predictions': self.metrics.total_predictions_made,
                'total_alerts': self.metrics.total_alerts_generated,
                'active_alerts': len([a for a in self.alerts.values() if not a.resolved]),
                'metrics_by_type': {}
            }
            
            if metric_type:
                data_points = list(self.metrics_data[metric_type])
                if data_points:
                    values = [dp.value for dp in data_points]
                    summary['metrics_by_type'][metric_type.value] = {
                        'count': len(values),
                        'current': values[-1],
                        'min': min(values),
                        'max': max(values),
                        'avg': np.mean(values),
                        'std': np.std(values)
                    }
            else:
                for mt in MetricType:
                    data_points = list(self.metrics_data[mt])
                    if data_points:
                        values = [dp.value for dp in data_points]
                        summary['metrics_by_type'][mt.value] = {
                            'count': len(values),
                            'current': values[-1],
                            'min': min(values),
                            'max': max(values),
                            'avg': np.mean(values),
                            'std': np.std(values)
                        }
            
            return summary
            
        except Exception as e:
            logger.error(f"Metrics summary error: {e}")
            return {}
    
    async def get_predictions_summary(self, metric_type: MetricType | None = None) -> dict[str, Any]:
        """Get predictions summary"""
        try:
            summary = {
                'total_predictions': self.metrics.total_predictions_made,
                'avg_confidence': 0.0,
                'predictions_by_type': {}
            }
            
            all_predictions = []
            for mt in MetricType:
                predictions = list(self.predictions[mt])
                if predictions:
                    all_predictions.extend(predictions)
                    
                    if metric_type is None or metric_type == mt:
                        confidences = [p.confidence for p in predictions]
                        summary['predictions_by_type'][mt.value] = {
                            'count': len(predictions),
                            'avg_confidence': np.mean(confidences),
                            'latest': predictions[-1].to_dict() if predictions else None
                        }
            
            if all_predictions:
                summary['avg_confidence'] = np.mean([p.confidence for p in all_predictions])
            
            return summary
            
        except Exception as e:
            logger.error(f"Predictions summary error: {e}")
            return {}
    
    async def get_alerts_summary(self) -> dict[str, Any]:
        """Get alerts summary"""
        try:
            alerts = list(self.alerts.values())
            
            summary = {
                'total_alerts': len(alerts),
                'active_alerts': len([a for a in alerts if not a.resolved]),
                'critical_alerts': len([a for a in alerts if a.severity == AlertSeverity.CRITICAL and not a.resolved]),
                'warning_alerts': len([a for a in alerts if a.severity == AlertSeverity.WARNING and not a.resolved]),
                'alerts_by_severity': {},
                'recent_alerts': []
            }
            
            # Group by severity
            for severity in AlertSeverity:
                severity_alerts = [a for a in alerts if a.severity == severity]
                summary['alerts_by_severity'][severity.value] = {
                    'total': len(severity_alerts),
                    'active': len([a for a in severity_alerts if not a.resolved])
                }
            
            # Recent alerts (last 24 hours)
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_alerts = [a for a in alerts if a.timestamp > cutoff_time]
            recent_alerts.sort(key=lambda a: a.timestamp, reverse=True)
            summary['recent_alerts'] = [a.to_dict() for a in recent_alerts[:10]]
            
            return summary
            
        except Exception as e:
            logger.error(f"Alerts summary error: {e}")
            return {}
    
    async def train_models(self):
        """Train prediction models with collected data"""
        try:
            for metric_type in MetricType:
                data_points = list(self.metrics_data[metric_type])
                
                if len(data_points) < 50:
                    logger.info(f"Insufficient data for training {metric_type.value}: {len(data_points)} < 50")
                    continue
                
                logger.info(f"Training model for {metric_type.value} with {len(data_points)} samples")
                
                # Prepare training data
                features_list = []
                targets = []
                
                for i in range(10, len(data_points)):
                    # Extract features from historical data
                    historical_data = data_points[:i]
                    features = await self._extract_features(metric_type, historical_data)
                    
                    # Target is the next value
                    target = data_points[i].value
                    
                    features_list.append(features)
                    targets.append(target)
                
                if len(features_list) < 20:
                    continue
                
                # Convert to arrays
                feature_names = list(features_list[0].keys())
                X = np.array([[f[name] for name in feature_names] for f in features_list])
                y = np.array(targets)
                
                # Scale features
                scaler = self.scalers[metric_type]
                X_scaled = scaler.fit_transform(X)
                
                # Train model
                model = self.models[metric_type]
                model.fit(X_scaled, y)
                
                logger.info(f"Model training completed for {metric_type.value}")
            
        except Exception as e:
            logger.error(f"Model training error: {e}")
    
    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        try:
            if alert_id in self.alerts:
                self.alerts[alert_id].acknowledged = True
                self.alerts[alert_id].metadata['acknowledged_at'] = datetime.now().isoformat()
                
                if self.redis_enabled:
                    await self._store_alert(self.alerts[alert_id])
                
                logger.info(f"Alert acknowledged: {alert_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Alert acknowledgment error: {e}")
            return False
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        try:
            if alert_id in self.alerts:
                self.alerts[alert_id].resolved = True
                self.alerts[alert_id].metadata['resolved_at'] = datetime.now().isoformat()
                
                if self.redis_enabled:
                    await self._store_alert(self.alerts[alert_id])
                
                logger.info(f"Alert resolved: {alert_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Alert resolution error: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown predictive monitoring system"""
        logger.info("Shutting down predictive monitoring system...")
        
        # Cancel background tasks
        if self.collection_task:
            self.collection_task.cancel()
        if self.prediction_task:
            self.prediction_task.cancel()
        if self.anomaly_task:
            self.anomaly_task.cancel()
        if self.alert_task:
            self.alert_task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*[
            self.collection_task,
            self.prediction_task,
            self.anomaly_task,
            self.alert_task
        ], return_exceptions=True)
        
        # Save models
        await self._save_models()
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Predictive monitoring system shutdown complete")
    
    async def _save_models(self):
        """Save trained models"""
        try:
            import os
            os.makedirs("models", exist_ok=True)
            
            for metric_type in MetricType:
                if metric_type in self.models:
                    model_path = f"models/predictive_{metric_type.value}_model.pkl"
                    scaler_path = f"models/predictive_{metric_type.value}_scaler.pkl"
                    
                    joblib.dump(self.models[metric_type], model_path)
                    joblib.dump(self.scalers[metric_type], scaler_path)
                    
                    logger.info(f"Model saved for {metric_type.value}")
            
        except Exception as e:
            logger.error(f"Model saving error: {e}")

# Global predictive monitoring system instance
predictive_monitoring = PredictiveMonitoringSystem()
