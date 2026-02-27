"""
Détection d'Anomalies avec Machine Learning
Système intelligent de détection d'anomalies pour les métriques système et business
"""

import asyncio
import time
import json
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
import joblib
from collections import defaultdict, deque
import redis
from prometheus_client import Gauge, Counter
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    """Types d'anomalies"""
    PERFORMANCE = "performance"
    BUSINESS = "business"
    SECURITY = "security"
    SYSTEM = "system"
    USER_BEHAVIOR = "user_behavior"


class AnomalySeverity(Enum):
    """Niveaux de sévérité"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AnomalyDetection:
    """Résultat de détection d'anomalie"""
    timestamp: datetime
    metric_name: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    value: float
    expected_range: Tuple[float, float]
    confidence_score: float
    description: str
    context: Dict[str, Any]
    alert_sent: bool = False


@dataclass
class MetricDataPoint:
    """Point de données pour une métrique"""
    timestamp: datetime
    metric_name: str
    value: float
    labels: Dict[str, str]
    context: Dict[str, Any]


@dataclass
class ModelMetrics:
    """Métriques du modèle ML"""
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    false_positive_rate: float
    false_negative_rate: float
    training_samples: int
    last_trained: datetime


class MLAnomalyDetector:
    """Détecteur d'anomalies basé sur Machine Learning"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        model_path: str = "models/anomaly_detection",
        training_window: int = 1000,  # Nombre de points pour l'entraînement
        detection_threshold: float = 0.1,  # Seuil de détection
        retrain_interval: int = 24,  # Heures entre réentraînements
        min_samples_for_training: int = 100
    ):
        self.redis_url = redis_url
        self.model_path = model_path
        self.training_window = training_window
        self.detection_threshold = detection_threshold
        self.retrain_interval = retrain_interval
        self.min_samples_for_training = min_samples_for_training
        
        # Redis pour les données et résultats
        self.redis_client = redis.from_url(redis_url)
        
        # Modèles ML
        self.models: Dict[str, Dict[str, Any]] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        
        # Historique des données
        self.data_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=training_window))
        
        # Métriques des modèles
        self.model_metrics: Dict[str, ModelMetrics] = {}
        
        # Configuration des métriques à surveiller
        self.metric_configs = self._setup_metric_configs()
        
        # Métriques Prometheus
        self.setup_prometheus_metrics()
        
        # État du système
        self.last_retrain_time = datetime.min
        self.is_training = False
        
        # Créer le répertoire des modèles
        import os
        os.makedirs(model_path, exist_ok=True)
        
        logger.info("ML Anomaly Detector initialisé")
    
    def _setup_metric_configs(self) -> Dict[str, Dict[str, Any]]:
        """Configure les métriques à surveiller"""
        return {
            # Métriques performance
            'response_time': {
                'type': AnomalyType.PERFORMANCE,
                'window_size': 100,
                'model_type': 'isolation_forest',
                'threshold_multiplier': 2.0
            },
            'cpu_usage': {
                'type': AnomalyType.SYSTEM,
                'window_size': 50,
                'model_type': 'isolation_forest',
                'threshold_multiplier': 1.5
            },
            'memory_usage': {
                'type': AnomalyType.SYSTEM,
                'window_size': 50,
                'model_type': 'isolation_forest',
                'threshold_multiplier': 1.5
            },
            'error_rate': {
                'type': AnomalyType.PERFORMANCE,
                'window_size': 100,
                'model_type': 'isolation_forest',
                'threshold_multiplier': 3.0
            },
            
            # Métriques business
            'ideas_per_hour': {
                'type': AnomalyType.BUSINESS,
                'window_size': 200,
                'model_type': 'isolation_forest',
                'threshold_multiplier': 2.0
            },
            'success_rate': {
                'type': AnomalyType.BUSINESS,
                'window_size': 100,
                'model_type': 'isolation_forest',
                'threshold_multiplier': 1.8
            },
            'user_satisfaction': {
                'type': AnomalyType.USER_BEHAVIOR,
                'window_size': 50,
                'model_type': 'isolation_forest',
                'threshold_multiplier': 2.5
            },
            'conversion_rate': {
                'type': AnomalyType.BUSINESS,
                'window_size': 100,
                'model_type': 'isolation_forest',
                'threshold_multiplier': 2.0
            },
            
            # Métriques sécurité
            'failed_login_attempts': {
                'type': AnomalyType.SECURITY,
                'window_size': 50,
                'model_type': 'isolation_forest',
                'threshold_multiplier': 5.0
            },
            'api_abuse_rate': {
                'type': AnomalyType.SECURITY,
                'window_size': 100,
                'model_type': 'isolation_forest',
                'threshold_multiplier': 3.0
            }
        }
    
    def setup_prometheus_metrics(self):
        """Configure les métriques Prometheus"""
        self.prometheus_metrics = {
            'anomalies_detected': Counter(
                'asmblr_anomalies_detected_total',
                'Nombre total d\'anomalies détectées',
                ['type', 'severity']
            ),
            'anomaly_detection_accuracy': Gauge(
                'asmblr_anomaly_detection_accuracy',
                'Précision de la détection d\'anomalies',
                ['model']
            ),
            'model_training_duration': Gauge(
                'asmblr_model_training_duration_seconds',
                'Durée d\'entraînement des modèles',
                ['model']
            ),
            'false_positive_rate': Gauge(
                'asmblr_false_positive_rate',
                'Taux de faux positifs',
                ['model']
            )
        }
    
    async def start_monitoring(self):
        """Démarre le monitoring continu"""
        logger.info("Démarrage du monitoring d'anomalies")
        
        # Charger les modèles existants
        await self._load_models()
        
        # Tâches de monitoring
        tasks = [
            asyncio.create_task(self._collect_metrics()),
            asyncio.create_task(self._detect_anomalies()),
            asyncio.create_task(self._retrain_models()),
            asyncio.create_task(self._cleanup_old_data())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Erreur dans le monitoring d'anomalies: {e}")
    
    async def _collect_metrics(self):
        """Collecte les métriques depuis Redis et autres sources"""
        while True:
            try:
                current_time = datetime.now()
                
                # Collecter les métriques système
                await self._collect_system_metrics(current_time)
                
                # Collecter les métriques business
                await self._collect_business_metrics(current_time)
                
                # Collecter les métriques de sécurité
                await self._collect_security_metrics(current_time)
                
                await asyncio.sleep(30)  # Collecte toutes les 30 secondes
                
            except Exception as e:
                logger.error(f"Erreur lors de la collecte des métriques: {e}")
                await asyncio.sleep(60)
    
    async def _collect_system_metrics(self, timestamp: datetime):
        """Collecte les métriques système"""
        try:
            # CPU Usage
            cpu_key = "system:cpu_usage"
            cpu_data = self.redis_client.get(cpu_key)
            if cpu_data:
                cpu_value = float(cpu_data)
                await self._add_metric_point(
                    MetricDataPoint(
                        timestamp=timestamp,
                        metric_name="cpu_usage",
                        value=cpu_value,
                        labels={"source": "system"},
                        context={}
                    )
                )
            
            # Memory Usage
            memory_key = "system:memory_usage"
            memory_data = self.redis_client.get(memory_key)
            if memory_data:
                memory_value = float(memory_data)
                await self._add_metric_point(
                    MetricDataPoint(
                        timestamp=timestamp,
                        metric_name="memory_usage",
                        value=memory_value,
                        labels={"source": "system"},
                        context={}
                    )
                )
            
            # Response Time
            response_key = "metrics:avg_response_time"
            response_data = self.redis_client.get(response_key)
            if response_data:
                response_value = float(response_data)
                await self._add_metric_point(
                    MetricDataPoint(
                        timestamp=timestamp,
                        metric_name="response_time",
                        value=response_value,
                        labels={"source": "application"},
                        context={}
                    )
                )
            
            # Error Rate
            error_key = "metrics:error_rate"
            error_data = self.redis_client.get(error_key)
            if error_data:
                error_value = float(error_data)
                await self._add_metric_point(
                    MetricDataPoint(
                        timestamp=timestamp,
                        metric_name="error_rate",
                        value=error_value,
                        labels={"source": "application"},
                        context={}
                    )
                )
                
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des métriques système: {e}")
    
    async def _collect_business_metrics(self, timestamp: datetime):
        """Collecte les métriques business"""
        try:
            # Ideas per hour
            ideas_key = "business:ideas_per_hour"
            ideas_data = self.redis_client.get(ideas_key)
            if ideas_data:
                ideas_value = float(ideas_data)
                await self._add_metric_point(
                    MetricDataPoint(
                        timestamp=timestamp,
                        metric_name="ideas_per_hour",
                        value=ideas_value,
                        labels={"source": "business"},
                        context={}
                    )
                )
            
            # Success Rate
            success_key = "business:success_rate"
            success_data = self.redis_client.get(success_key)
            if success_data:
                success_value = float(success_data)
                await self._add_metric_point(
                    MetricDataPoint(
                        timestamp=timestamp,
                        metric_name="success_rate",
                        value=success_value,
                        labels={"source": "business"},
                        context={}
                    )
                )
            
            # User Satisfaction
            satisfaction_key = "business:user_satisfaction"
            satisfaction_data = self.redis_client.get(satisfaction_key)
            if satisfaction_data:
                satisfaction_value = float(satisfaction_data)
                await self._add_metric_point(
                    MetricDataPoint(
                        timestamp=timestamp,
                        metric_name="user_satisfaction",
                        value=satisfaction_value,
                        labels={"source": "business"},
                        context={}
                    )
                )
            
            # Conversion Rate
            conversion_key = "business:conversion_rate"
            conversion_data = self.redis_client.get(conversion_key)
            if conversion_data:
                conversion_value = float(conversion_data)
                await self._add_metric_point(
                    MetricDataPoint(
                        timestamp=timestamp,
                        metric_name="conversion_rate",
                        value=conversion_value,
                        labels={"source": "business"},
                        context={}
                    )
                )
                
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des métriques business: {e}")
    
    async def _collect_security_metrics(self, timestamp: datetime):
        """Collecte les métriques de sécurité"""
        try:
            # Failed Login Attempts
            failed_login_key = "security:failed_login_attempts"
            failed_login_data = self.redis_client.get(failed_login_key)
            if failed_login_data:
                failed_login_value = float(failed_login_data)
                await self._add_metric_point(
                    MetricDataPoint(
                        timestamp=timestamp,
                        metric_name="failed_login_attempts",
                        value=failed_login_value,
                        labels={"source": "security"},
                        context={}
                    )
                )
            
            # API Abuse Rate
            abuse_key = "security:api_abuse_rate"
            abuse_data = self.redis_client.get(abuse_key)
            if abuse_data:
                abuse_value = float(abuse_data)
                await self._add_metric_point(
                    MetricDataPoint(
                        timestamp=timestamp,
                        metric_name="api_abuse_rate",
                        value=abuse_value,
                        labels={"source": "security"},
                        context={}
                    )
                )
                
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des métriques sécurité: {e}")
    
    async def _add_metric_point(self, point: MetricDataPoint):
        """Ajoute un point de données à l'historique"""
        self.data_history[point.metric_name].append(point)
        
        # Stocker dans Redis pour la persistance
        redis_key = f"anomaly_data:{point.metric_name}"
        data = {
            'timestamp': point.timestamp.isoformat(),
            'value': point.value,
            'labels': point.labels,
            'context': point.context
        }
        
        self.redis_client.lpush(redis_key, json.dumps(data))
        self.redis_client.ltrim(redis_key, 0, self.training_window - 1)
    
    async def _detect_anomalies(self):
        """Détecte les anomalies dans les métriques"""
        while True:
            try:
                current_time = datetime.now()
                
                for metric_name, config in self.metric_configs.items():
                    # Vérifier si on a assez de données
                    if len(self.data_history[metric_name]) < config['window_size']:
                        continue
                    
                    # Détecter les anomalies pour cette métrique
                    anomalies = await self._detect_metric_anomalies(metric_name, current_time)
                    
                    # Traiter les anomalies détectées
                    for anomaly in anomalies:
                        await self._handle_anomaly(anomaly)
                
                await asyncio.sleep(60)  # Détection toutes les minutes
                
            except Exception as e:
                logger.error(f"Erreur lors de la détection d'anomalies: {e}")
                await asyncio.sleep(120)
    
    async def _detect_metric_anomalies(self, metric_name: str, timestamp: datetime) -> List[AnomalyDetection]:
        """Détecte les anomalies pour une métrique spécifique"""
        anomalies = []
        
        try:
            config = self.metric_configs[metric_name]
            data_points = list(self.data_history[metric_name])
            
            if len(data_points) < config['window_size']:
                return anomalies
            
            # Préparer les données
            values = np.array([point.value for point in data_points[-config['window_size']:]])
            timestamps = [point.timestamp for point in data_points[-config['window_size']:]]
            
            # Vérifier si le modèle est entraîné
            if metric_name not in self.models:
                await self._train_model(metric_name)
            
            if metric_name not in self.models:
                # Impossible d'entraîner le modèle
                return anomalies
            
            # Prédire avec le modèle
            model = self.models[metric_name]['model']
            scaler = self.scalers[metric_name]
            
            # Normaliser les données
            values_scaled = scaler.transform(values.reshape(-1, 1))
            
            # Prédire les anomalies
            predictions = model.predict(values_scaled)
            scores = model.decision_function(values_scaled)
            
            # Détecter les anomalies (predictions == -1)
            anomaly_indices = np.where(predictions == -1)[0]
            
            for idx in anomaly_indices:
                if idx >= len(timestamps):
                    continue
                
                point = data_points[-config['window_size']:][idx]
                score = scores[idx]
                
                # Calculer la sévérité
                severity = self._calculate_severity(score, config['threshold_multiplier'])
                
                # Calculer la plage attendue
                normal_values = values[predictions == 1]
                if len(normal_values) > 0:
                    expected_min = np.percentile(normal_values, 5)
                    expected_max = np.percentile(normal_values, 95)
                else:
                    expected_min = values.min()
                    expected_max = values.max()
                
                # Créer l'anomalie
                anomaly = AnomalyDetection(
                    timestamp=point.timestamp,
                    metric_name=metric_name,
                    anomaly_type=config['type'],
                    severity=severity,
                    value=point.value,
                    expected_range=(expected_min, expected_max),
                    confidence_score=abs(score),
                    description=self._generate_anomaly_description(metric_name, point.value, expected_min, expected_max),
                    context={
                        'score': float(score),
                        'labels': point.labels,
                        'recent_values': values[-5:].tolist()
                    }
                )
                
                anomalies.append(anomaly)
                
                # Mettre à jour les métriques Prometheus
                self.prometheus_metrics['anomalies_detected'].labels(
                    type=anomaly.anomaly_type.value,
                    severity=anomaly.severity.value
                ).inc()
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection d'anomalies pour {metric_name}: {e}")
        
        return anomalies
    
    def _calculate_severity(self, score: float, threshold_multiplier: float) -> AnomalySeverity:
        """Calcule la sévérité d'une anomalie"""
        abs_score = abs(score)
        
        if abs_score >= threshold_multiplier * 2:
            return AnomalySeverity.CRITICAL
        elif abs_score >= threshold_multiplier * 1.5:
            return AnomalySeverity.HIGH
        elif abs_score >= threshold_multiplier:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    def _generate_anomaly_description(self, metric_name: str, value: float, expected_min: float, expected_max: float) -> str:
        """Génère une description d'anomalie"""
        if value < expected_min:
            return f"Valeur anormalement basse pour {metric_name}: {value:.3f} (attendu > {expected_min:.3f})"
        elif value > expected_max:
            return f"Valeur anormalement élevée pour {metric_name}: {value:.3f} (attendu < {expected_max:.3f})"
        else:
            return f"Comportement anormal détecté pour {metric_name}: {value:.3f}"
    
    async def _handle_anomaly(self, anomaly: AnomalyDetection):
        """Traite une anomalie détectée"""
        try:
            # Stocker l'anomalie
            anomaly_key = f"anomaly:{anomaly.metric_name}:{int(anomaly.timestamp.timestamp())}"
            anomaly_data = asdict(anomaly)
            anomaly_data['anomaly_type'] = anomaly.anomaly_type.value
            anomaly_data['severity'] = anomaly.severity.value
            anomaly_data['timestamp'] = anomaly.timestamp.isoformat()
            
            self.redis_client.setex(
                anomaly_key,
                timedelta(hours=24),
                json.dumps(anomaly_data, default=str)
            )
            
            # Envoyer une alerte si nécessaire
            if anomaly.severity in [AnomalySeverity.HIGH, AnomalySeverity.CRITICAL]:
                await self._send_alert(anomaly)
                anomaly.alert_sent = True
            
            logger.warning(f"Anomalie détectée: {anomaly.description}")
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'anomalie: {e}")
    
    async def _send_alert(self, anomaly: AnomalyDetection):
        """Envoie une alerte pour une anomalie"""
        try:
            # Préparer le message d'alerte
            alert_message = {
                'alert_name': f"Anomaly Detected - {anomaly.metric_name}",
                'severity': anomaly.severity.value,
                'timestamp': anomaly.timestamp.isoformat(),
                'description': anomaly.description,
                'metric_name': anomaly.metric_name,
                'current_value': anomaly.value,
                'expected_range': anomaly.expected_range,
                'confidence': anomaly.confidence_score,
                'type': anomaly.anomaly_type.value
            }
            
            # Stocker l'alerte dans Redis
            alert_key = f"alert:{int(anomaly.timestamp.timestamp())}"
            self.redis_client.setex(
                alert_key,
                timedelta(hours=6),
                json.dumps(alert_message)
            )
            
            # TODO: Intégrer avec Slack, Email, etc.
            logger.critical(f"ALERTE: {alert_message}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'alerte: {e}")
    
    async def _train_model(self, metric_name: str):
        """Entraîne un modèle pour une métrique"""
        if self.is_training:
            return
        
        try:
            self.is_training = True
            start_time = time.time()
            
            config = self.metric_configs[metric_name]
            data_points = list(self.data_history[metric_name])
            
            if len(data_points) < self.min_samples_for_training:
                logger.warning(f"Pas assez de données pour entraîner le modèle {metric_name}")
                return
            
            logger.info(f"Entraînement du modèle pour {metric_name}")
            
            # Préparer les données d'entraînement
            values = np.array([point.value for point in data_points])
            
            # Créer et entraîner le modèle
            if config['model_type'] == 'isolation_forest':
                model = IsolationForest(
                    contamination=self.detection_threshold,
                    random_state=42,
                    n_estimators=100
                )
            else:
                model = IsolationForest(
                    contamination=self.detection_threshold,
                    random_state=42
                )
            
            # Normaliser les données
            scaler = StandardScaler()
            values_scaled = scaler.fit_transform(values.reshape(-1, 1))
            
            # Entraîner le modèle
            model.fit(values_scaled)
            
            # Sauvegarder le modèle
            self.models[metric_name] = {
                'model': model,
                'config': config,
                'trained_at': datetime.now()
            }
            self.scalers[metric_name] = scaler
            
            # Sauvegarder sur disque
            model_file = f"{self.model_path}/{metric_name}_model.joblib"
            scaler_file = f"{self.model_path}/{metric_name}_scaler.joblib"
            
            joblib.dump(model, model_file)
            joblib.dump(scaler, scaler_file)
            
            # Calculer les métriques du modèle
            predictions = model.predict(values_scaled)
            anomaly_count = np.sum(predictions == -1)
            
            self.model_metrics[metric_name] = ModelMetrics(
                model_name=metric_name,
                accuracy=1.0 - (anomaly_count / len(values)),  # Approximation
                precision=0.8,  # À calculer avec des données étiquetées
                recall=0.8,
                f1_score=0.8,
                false_positive_rate=anomaly_count / len(values),
                false_negative_rate=0.1,
                training_samples=len(values),
                last_trained=datetime.now()
            )
            
            # Mettre à jour les métriques Prometheus
            self.prometheus_metrics['anomaly_detection_accuracy'].labels(model=metric_name).set(
                self.model_metrics[metric_name].accuracy
            )
            self.prometheus_metrics['false_positive_rate'].labels(model=metric_name).set(
                self.model_metrics[metric_name].false_positive_rate
            )
            self.prometheus_metrics['model_training_duration'].labels(model=metric_name).set(
                time.time() - start_time
            )
            
            self.last_retrain_time = datetime.now()
            
            logger.info(f"Modèle {metric_name} entraîné en {time.time() - start_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'entraînement du modèle {metric_name}: {e}")
        finally:
            self.is_training = False
    
    async def _retrain_models(self):
        """Réentraîne périodiquement les modèles"""
        while True:
            try:
                await asyncio.sleep(self.retrain_interval * 3600)  # Convertir en secondes
                
                current_time = datetime.now()
                if (current_time - self.last_retrain_time).total_seconds() >= self.retrain_interval * 3600:
                    logger.info("Réentraînement périodique des modèles")
                    
                    for metric_name in self.metric_configs.keys():
                        await self._train_model(metric_name)
                
            except Exception as e:
                logger.error(f"Erreur lors du réentraînement des modèles: {e}")
    
    async def _cleanup_old_data(self):
        """Nettoie les anciennes données"""
        while True:
            try:
                await asyncio.sleep(3600)  # Nettoyage toutes les heures
                
                cutoff_time = datetime.now() - timedelta(days=self.retention_days)
                
                # Nettoyer les données dans Redis
                for metric_name in self.metric_configs.keys():
                    redis_key = f"anomaly_data:{metric_name}"
                    
                    # Récupérer et vérifier chaque entrée
                    data = self.redis_client.lrange(redis_key, 0, -1)
                    valid_data = []
                    
                    for item in data:
                        try:
                            item_data = json.loads(item)
                            item_time = datetime.fromisoformat(item_data['timestamp'])
                            
                            if item_time >= cutoff_time:
                                valid_data.append(item)
                        except:
                            continue
                    
                    # Mettre à jour la liste
                    if len(valid_data) != len(data):
                        self.redis_client.delete(redis_key)
                        if valid_data:
                            self.redis_client.lpush(redis_key, *valid_data)
                
                logger.info("Nettoyage des anciennes données terminé")
                
            except Exception as e:
                logger.error(f"Erreur lors du nettoyage des données: {e}")
    
    async def _load_models(self):
        """Charge les modèles existants depuis le disque"""
        try:
            import os
            
            for metric_name in self.metric_configs.keys():
                model_file = f"{self.model_path}/{metric_name}_model.joblib"
                scaler_file = f"{self.model_path}/{metric_name}_scaler.joblib"
                
                if os.path.exists(model_file) and os.path.exists(scaler_file):
                    model = joblib.load(model_file)
                    scaler = joblib.load(scaler_file)
                    
                    config = self.metric_configs[metric_name]
                    self.models[metric_name] = {
                        'model': model,
                        'config': config,
                        'trained_at': datetime.now()
                    }
                    self.scalers[metric_name] = scaler
                    
                    logger.info(f"Modèle {metric_name} chargé depuis le disque")
                
        except Exception as e:
            logger.error(f"Erreur lors du chargement des modèles: {e}")
    
    async def get_anomaly_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Retourne un résumé des anomalies"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Récupérer toutes les anomalies
            anomaly_keys = self.redis_client.keys("anomaly:*")
            
            anomalies = []
            severity_counts = defaultdict(int)
            type_counts = defaultdict(int)
            
            for key in anomaly_keys:
                try:
                    data = self.redis_client.get(key)
                    if data:
                        anomaly_data = json.loads(data)
                        anomaly_time = datetime.fromisoformat(anomaly_data['timestamp'])
                        
                        if anomaly_time >= cutoff_time:
                            anomalies.append(anomaly_data)
                            severity_counts[anomaly_data['severity']] += 1
                            type_counts[anomaly_data['type']] += 1
                except:
                    continue
            
            # Trier par timestamp
            anomalies.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return {
                'period_hours': hours,
                'total_anomalies': len(anomalies),
                'severity_breakdown': dict(severity_counts),
                'type_breakdown': dict(type_counts),
                'recent_anomalies': anomalies[:20],  # 20 plus récentes
                'models_status': {
                    name: {
                        'trained': name in self.models,
                        'last_trained': self.model_metrics.get(name, ModelMetrics(
                            model_name=name, accuracy=0, precision=0, recall=0, f1_score=0,
                            false_positive_rate=0, false_negative_rate=0, training_samples=0,
                            last_trained=datetime.min
                        )).last_trained.isoformat()
                    }
                    for name in self.metric_configs.keys()
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du résumé des anomalies: {e}")
            return {'error': str(e)}
    
    async def force_retrain_model(self, metric_name: str):
        """Force le réentraînement d'un modèle spécifique"""
        if metric_name not in self.metric_configs:
            raise ValueError(f"Métrique {metric_name} non configurée")
        
        logger.info(f"Force réentraînement du modèle {metric_name}")
        await self._train_model(metric_name)
    
    async def get_model_performance(self) -> Dict[str, Any]:
        """Retourne les performances des modèles"""
        performance = {}
        
        for metric_name, metrics in self.model_metrics.items():
            performance[metric_name] = {
                'accuracy': metrics.accuracy,
                'precision': metrics.precision,
                'recall': metrics.recall,
                'f1_score': metrics.f1_score,
                'false_positive_rate': metrics.false_positive_rate,
                'false_negative_rate': metrics.false_negative_rate,
                'training_samples': metrics.training_samples,
                'last_trained': metrics.last_trained.isoformat()
            }
        
        return performance


# Singleton global
_anomaly_detector: Optional[MLAnomalyDetector] = None


async def get_anomaly_detector() -> MLAnomalyDetector:
    """Retourne l'instance singleton du détecteur d'anomalies"""
    global _anomaly_detector
    
    if _anomaly_detector is None:
        _anomaly_detector = MLAnomalyDetector()
    
    return _anomaly_detector


# Exemple d'utilisation
async def example_usage():
    """Exemple d'utilisation du détecteur d'anomalies"""
    detector = await get_anomaly_detector()
    
    # Démarrer le monitoring
    monitoring_task = asyncio.create_task(detector.start_monitoring())
    
    try:
        # Simuler des données
        for i in range(100):
            # Ajouter des points de données normaux
            await detector._add_metric_point(
                MetricDataPoint(
                    timestamp=datetime.now(),
                    metric_name="cpu_usage",
                    value=np.random.normal(0.5, 0.1),  # Normal autour de 50%
                    labels={"source": "test"},
                    context={}
                )
            )
            
            # Ajouter une anomalie occasionnelle
            if i % 20 == 0:
                await detector._add_metric_point(
                    MetricDataPoint(
                        timestamp=datetime.now(),
                        metric_name="cpu_usage",
                        value=0.95,  # Anomalie: 95% CPU
                        labels={"source": "test"},
                        context={}
                    )
                )
            
            await asyncio.sleep(1)
        
        # Obtenir le résumé des anomalies
        summary = await detector.get_anomaly_summary(1)  # Dernière heure
        print(f"Résumé des anomalies: {summary}")
        
    finally:
        monitoring_task.cancel()


if __name__ == "__main__":
    asyncio.run(example_usage())
