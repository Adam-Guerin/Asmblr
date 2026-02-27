"""
Scaling Prédictif Basé sur les Tendances
Système de prédiction de charge et scaling anticipatif avec Machine Learning
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
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
from collections import defaultdict, deque
import redis
from prometheus_client import Gauge, Counter, Histogram
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PredictionModel(Enum):
    """Types de modèles de prédiction"""
    LINEAR = "linear"
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    ENSEMBLE = "ensemble"


class ScalingAction(Enum):
    """Actions de scaling prédictif"""
    PREEMPTIVE_SCALE_UP = "preemptive_scale_up"
    PREEMPTIVE_SCALE_DOWN = "preemptive_scale_down"
    SCHEDULED_SCALE = "scheduled_scale"
    MAINTAIN = "maintain"


@dataclass
class LoadPrediction:
    """Prédiction de charge"""
    timestamp: datetime
    predicted_load: float
    confidence_interval: Tuple[float, float]  # (min, max)
    model_used: str
    accuracy_score: float
    features_used: List[str]
    prediction_horizon: int  # minutes


@dataclass
class ScalingPlan:
    """Plan de scaling prédictif"""
    created_at: datetime
    action: ScalingAction
    target_workers: int
    execution_time: datetime
    confidence: float
    reasoning: str
    estimated_cost_impact: float
    estimated_performance_impact: float


@dataclass
class FeatureData:
    """Données de caractéristiques pour la prédiction"""
    timestamp: datetime
    hour_of_day: int
    day_of_week: int
    day_of_month: int
    month: int
    is_weekend: bool
    is_holiday: bool
    current_load: float
    avg_load_last_hour: float
    avg_load_last_6h: float
    avg_load_last_24h: float
    load_trend_1h: float
    load_trend_6h: float
    load_trend_24h: float
    queue_size: float
    error_rate: float
    response_time: float
    active_users: float
    business_hour: bool
    seasonal_factor: float


class PredictiveScaler:
    """Scaler prédictif basé sur les tendances et ML"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        model_path: str = "models/predictive_scaling",
        prediction_horizon: int = 60,  # minutes
        historical_window: int = 30,  # jours
        retrain_interval: int = 6,  # heures
        min_samples_for_training: int = 500,
        confidence_threshold: float = 0.7
    ):
        self.redis_url = redis_url
        self.model_path = model_path
        self.prediction_horizon = prediction_horizon
        self.historical_window = historical_window
        self.retrain_interval = retrain_interval
        self.min_samples_for_training = min_samples_for_training
        self.confidence_threshold = confidence_threshold
        
        # Redis pour les données et prédictions
        self.redis_client = redis.from_url(redis_url)
        
        # Modèles ML
        self.models: Dict[str, Dict[str, Any]] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.feature_columns: List[str] = []
        
        # Historique des données
        self.historical_data: deque = deque(maxlen=historical_window * 24 * 60)  # Par minute
        
        # Prédictions et plans
        self.predictions: deque = deque(maxlen=1000)
        self.scaling_plans: deque = deque(maxlen=100)
        
        # Performance des modèles
        self.model_performance: Dict[str, Dict[str, float]] = {}
        
        # Configuration des modèles
        self.model_configs = self._setup_model_configs()
        
        # Métriques Prometheus
        self.setup_prometheus_metrics()
        
        # État du système
        self.last_retrain_time = datetime.min
        self.is_training = False
        self.last_prediction_time = datetime.min
        
        # Créer le répertoire des modèles
        import os
        os.makedirs(model_path, exist_ok=True)
        
        logger.info("Predictive Scaler initialisé")
    
    def _setup_model_configs(self) -> Dict[str, Dict[str, Any]]:
        """Configure les modèles de prédiction"""
        return {
            'linear_regression': {
                'model_class': LinearRegression,
                'params': {},
                'weight': 0.2
            },
            'random_forest': {
                'model_class': RandomForestRegressor,
                'params': {
                    'n_estimators': 100,
                    'random_state': 42,
                    'max_depth': 10
                },
                'weight': 0.4
            },
            'gradient_boosting': {
                'model_class': GradientBoostingRegressor,
                'params': {
                    'n_estimators': 100,
                    'random_state': 42,
                    'max_depth': 6,
                    'learning_rate': 0.1
                },
                'weight': 0.4
            }
        }
    
    def setup_prometheus_metrics(self):
        """Configure les métriques Prometheus"""
        self.prometheus_metrics = {
            'predictions_made': Counter(
                'asmblr_predictive_scaler_predictions_total',
                'Nombre total de prédictions effectuées'
            ),
            'prediction_accuracy': Gauge(
                'asmblr_predictive_scaler_accuracy',
                'Précision des prédictions',
                ['model']
            ),
            'scaling_plans_executed': Counter(
                'asmblr_predictive_scaler_plans_executed_total',
                'Nombre de plans de scaling exécutés',
                ['action']
            ),
            'prediction_horizon_minutes': Gauge(
                'asmblr_predictive_scaler_horizon_minutes',
                'Horizon de prédiction en minutes'
            ),
            'model_training_duration': Gauge(
                'asmblr_predictive_scaler_training_duration_seconds',
                'Durée d\'entraînement des modèles',
                ['model']
            )
        }
    
    async def start_predictive_scaling(self):
        """Démarre le scaling prédictif"""
        logger.info("Démarrage du scaling prédictif")
        
        # Charger les modèles existants
        await self._load_models()
        
        # Tâches de scaling prédictif
        tasks = [
            asyncio.create_task(self._collect_historical_data()),
            asyncio.create_task(self._generate_predictions()),
            asyncio.create_task(self._create_scaling_plans()),
            asyncio.create_task(self._execute_scaling_plans()),
            asyncio.create_task(self._retrain_models()),
            asyncio.create_task(self._evaluate_performance())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Erreur dans le scaling prédictif: {e}")
    
    async def _collect_historical_data(self):
        """Collecte les données historiques pour l'entraînement"""
        while True:
            try:
                current_time = datetime.now()
                
                # Collecter les métriques actuelles
                feature_data = await self._collect_current_metrics(current_time)
                
                if feature_data:
                    self.historical_data.append(feature_data)
                    
                    # Stocker dans Redis
                    redis_key = f"predictive_data:{int(current_time.timestamp())}"
                    self.redis_client.setex(
                        redis_key,
                        timedelta(days=self.historical_window + 7),
                        json.dumps(asdict(feature_data), default=str)
                    )
                
                await asyncio.sleep(60)  # Collecte chaque minute
                
            except Exception as e:
                logger.error(f"Erreur lors de la collecte des données historiques: {e}")
                await asyncio.sleep(120)
    
    async def _collect_current_metrics(self, timestamp: datetime) -> Optional[FeatureData]:
        """Collecte les métriques actuelles pour créer les caractéristiques"""
        try:
            # Métriques de base
            current_load = await self._get_current_load()
            queue_size = await self._get_queue_size()
            error_rate = await self._get_error_rate()
            response_time = await self._get_response_time()
            active_users = await self._get_active_users()
            
            # Calculer les moyennes et tendances
            avg_load_last_hour = await self._calculate_avg_load(timestamp, timedelta(hours=1))
            avg_load_last_6h = await self._calculate_avg_load(timestamp, timedelta(hours=6))
            avg_load_last_24h = await self._calculate_avg_load(timestamp, timedelta(hours=1))
            
            load_trend_1h = await self._calculate_load_trend(timestamp, timedelta(hours=1))
            load_trend_6h = await self._calculate_load_trend(timestamp, timedelta(hours=6))
            load_trend_24h = await self._calculate_load_trend(timestamp, timedelta(hours=24))
            
            # Caractéristiques temporelles
            feature_data = FeatureData(
                timestamp=timestamp,
                hour_of_day=timestamp.hour,
                day_of_week=timestamp.weekday(),
                day_of_month=timestamp.day,
                month=timestamp.month,
                is_weekend=timestamp.weekday() >= 5,
                is_holiday=await self._is_holiday(timestamp),
                current_load=current_load,
                avg_load_last_hour=avg_load_last_hour,
                avg_load_last_6h=avg_load_last_6h,
                avg_load_last_24h=avg_load_last_24h,
                load_trend_1h=load_trend_1h,
                load_trend_6h=load_trend_6h,
                load_trend_24h=load_trend_24h,
                queue_size=queue_size,
                error_rate=error_rate,
                response_time=response_time,
                active_users=active_users,
                business_hour=8 <= timestamp.hour <= 18,
                seasonal_factor=await self._calculate_seasonal_factor(timestamp)
            )
            
            return feature_data
            
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des métriques: {e}")
            return None
    
    async def _get_current_load(self) -> float:
        """Récupère la charge actuelle"""
        # Utiliser les métriques existantes
        load_data = self.redis_client.get("system:current_load")
        return float(load_data) if load_data else 0.0
    
    async def _get_queue_size(self) -> float:
        """Récupère la taille de la queue"""
        queue_data = self.redis_client.get("system:queue_size")
        return float(queue_data) if queue_data else 0.0
    
    async def _get_error_rate(self) -> float:
        """Récupère le taux d'erreur"""
        error_data = self.redis_client.get("metrics:error_rate")
        return float(error_data) if error_data else 0.0
    
    async def _get_response_time(self) -> float:
        """Récupère le temps de réponse"""
        response_data = self.redis_client.get("metrics:avg_response_time")
        return float(response_data) if response_data else 0.0
    
    async def _get_active_users(self) -> float:
        """Récupère le nombre d'utilisateurs actifs"""
        users_data = self.redis_client.get("business:active_users")
        return float(users_data) if users_data else 0.0
    
    async def _calculate_avg_load(self, timestamp: datetime, period: timedelta) -> float:
        """Calcule la charge moyenne sur une période"""
        try:
            cutoff_time = timestamp - period
            
            # Récupérer les données historiques
            loads = []
            for data in self.historical_data:
                if data.timestamp >= cutoff_time:
                    loads.append(data.current_load)
            
            return np.mean(loads) if loads else 0.0
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la charge moyenne: {e}")
            return 0.0
    
    async def _calculate_load_trend(self, timestamp: datetime, period: timedelta) -> float:
        """Calcule la tendance de charge sur une période"""
        try:
            cutoff_time = timestamp - period
            
            # Récupérer les données historiques
            timestamps = []
            loads = []
            for data in self.historical_data:
                if data.timestamp >= cutoff_time:
                    timestamps.append(data.timestamp)
                    loads.append(data.current_load)
            
            if len(loads) < 2:
                return 0.0
            
            # Calculer la tendance (pente de la régression linéaire)
            X = np.array([(t - timestamps[0]).total_seconds() for t in timestamps])
            y = np.array(loads)
            
            if len(X) > 1:
                slope = np.polyfit(X, y, 1)[0]
                return slope
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la tendance: {e}")
            return 0.0
    
    async def _is_holiday(self, timestamp: datetime) -> bool:
        """Vérifie si c'est un jour férié"""
        # Simplifié - pourrait utiliser une bibliothèque de jours fériés
        # Pour l'instant, juste les week-ends
        return timestamp.weekday() >= 5
    
    async def _calculate_seasonal_factor(self, timestamp: datetime) -> float:
        """Calcule un facteur saisonnier"""
        # Simplifié - basé sur le mois
        month_factors = {
            1: 0.8,   # Janvier - faible activité
            2: 0.85,  # Février
            3: 0.9,   # Mars
            4: 0.95,  # Avril
            5: 1.0,   # Mai
            6: 1.1,   # Juin - début d'été
            7: 1.2,   # Juillet - été
            8: 1.15,  # Août
            9: 1.05,  # Septembre
            10: 1.0,  # Octobre
            11: 0.95, # Novembre
            12: 0.9   # Décembre - fêtes
        }
        
        return month_factors.get(timestamp.month, 1.0)
    
    async def _generate_predictions(self):
        """Génère des prédictions de charge"""
        while True:
            try:
                current_time = datetime.now()
                
                # Vérifier si on a assez de données
                if len(self.historical_data) < self.min_samples_for_training:
                    logger.info(f"Pas assez de données pour les prédictions: {len(self.historical_data)}/{self.min_samples_for_training}")
                    await asyncio.sleep(300)  # Attendre 5 minutes
                    continue
                
                # Générer des prédictions pour différents horizons
                predictions = await self._predict_load(current_time)
                
                for prediction in predictions:
                    self.predictions.append(prediction)
                    
                    # Stocker dans Redis
                    redis_key = f"prediction:{int(prediction.timestamp.timestamp())}"
                    self.redis_client.setex(
                        redis_key,
                        timedelta(hours=2),
                        json.dumps(asdict(prediction), default=str)
                    )
                
                # Mettre à jour les métriques
                self.prometheus_metrics['predictions_made'].inc()
                self.prometheus_metrics['prediction_horizon_minutes'].set(self.prediction_horizon)
                
                self.last_prediction_time = current_time
                
                await asyncio.sleep(300)  # Prédictions toutes les 5 minutes
                
            except Exception as e:
                logger.error(f"Erreur lors de la génération des prédictions: {e}")
                await asyncio.sleep(300)
    
    async def _predict_load(self, current_time: datetime) -> List[LoadPrediction]:
        """Prédit la charge pour différents horizons"""
        predictions = []
        
        try:
            # Préparer les caractéristiques
            feature_data = await self._collect_current_metrics(current_time)
            
            if not feature_data:
                return predictions
            
            # Créer les caractéristiques futures
            future_timestamps = [
                current_time + timedelta(minutes=30),
                current_time + timedelta(minutes=60),
                current_time + timedelta(minutes=120),
                current_time + timedelta(minutes=240)
            ]
            
            for future_time in future_timestamps:
                future_features = self._create_future_features(feature_data, future_time)
                
                # Prédire avec chaque modèle
                model_predictions = {}
                
                for model_name, model_config in self.model_configs.items():
                    if model_name in self.models:
                        prediction = await self._predict_with_model(
                            model_name, future_features, future_time
                        )
                        if prediction is not None:
                            model_predictions[model_name] = prediction
                
                # Combiner les prédictions (ensemble)
                if model_predictions:
                    ensemble_prediction = self._ensemble_predictions(model_predictions)
                    
                    prediction = LoadPrediction(
                        timestamp=future_time,
                        predicted_load=ensemble_prediction['value'],
                        confidence_interval=ensemble_prediction['confidence_interval'],
                        model_used='ensemble',
                        accuracy_score=ensemble_prediction['accuracy'],
                        features_used=list(future_features.keys()),
                        prediction_horizon=int((future_time - current_time).total_seconds() / 60)
                    )
                    
                    predictions.append(prediction)
            
        except Exception as e:
            logger.error(f"Erreur lors de la prédiction de charge: {e}")
        
        return predictions
    
    def _create_future_features(self, current_features: FeatureData, future_time: datetime) -> Dict[str, float]:
        """Crée les caractéristiques pour un timestamp futur"""
        # Copier les caractéristiques temporelles
        features = {
            'hour_of_day': future_time.hour,
            'day_of_week': future_time.weekday(),
            'day_of_month': future_time.day,
            'month': future_time.month,
            'is_weekend': future_time.weekday() >= 5,
            'is_holiday': 0,  # Simplifié
            'business_hour': 8 <= future_time.hour <= 18,
            'seasonal_factor': 1.0  # Simplifié
        }
        
        # Utiliser les tendances actuelles comme estimation
        features.update({
            'current_load': current_features.current_load,
            'avg_load_last_hour': current_features.avg_load_last_hour,
            'avg_load_last_6h': current_features.avg_load_last_6h,
            'avg_load_last_24h': current_features.avg_load_last_24h,
            'load_trend_1h': current_features.load_trend_1h,
            'load_trend_6h': current_features.load_trend_6h,
            'load_trend_24h': current_features.load_trend_24h,
            'queue_size': current_features.queue_size,
            'error_rate': current_features.error_rate,
            'response_time': current_features.response_time,
            'active_users': current_features.active_users
        })
        
        return features
    
    async def _predict_with_model(self, model_name: str, features: Dict[str, float], timestamp: datetime) -> Optional[Dict[str, Any]]:
        """Prédit avec un modèle spécifique"""
        try:
            if model_name not in self.models:
                return None
            
            model = self.models[model_name]['model']
            scaler = self.scalers[model_name]
            
            # Préparer les caractéristiques
            feature_values = np.array([features.get(col, 0) for col in self.feature_columns])
            feature_values_scaled = scaler.transform(feature_values.reshape(1, -1))
            
            # Prédire
            prediction = model.predict(feature_values_scaled)[0]
            
            # Calculer l'intervalle de confiance (simplifié)
            confidence = self.model_performance.get(model_name, {}).get('r2_score', 0.5)
            margin = (1 - confidence) * prediction * 0.5
            
            return {
                'value': max(0, prediction),  # Pas de charge négative
                'confidence_interval': (max(0, prediction - margin), prediction + margin),
                'confidence': confidence
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la prédiction avec le modèle {model_name}: {e}")
            return None
    
    def _ensemble_predictions(self, model_predictions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Combine les prédictions de plusieurs modèles"""
        if not model_predictions:
            return {'value': 0, 'confidence_interval': (0, 0), 'accuracy': 0}
        
        # Pondérer les prédictions
        weighted_sum = 0
        total_weight = 0
        confidence_sum = 0
        
        for model_name, prediction in model_predictions.items():
            weight = self.model_configs[model_name]['weight']
            weighted_sum += prediction['value'] * weight
            total_weight += weight
            confidence_sum += prediction['confidence'] * weight
        
        # Calculer la moyenne pondérée
        ensemble_value = weighted_sum / total_weight if total_weight > 0 else 0
        ensemble_confidence = confidence_sum / total_weight if total_weight > 0 else 0
        
        # Calculer l'intervalle de confiance
        all_intervals = [pred['confidence_interval'] for pred in model_predictions.values()]
        min_confidence = min(interval[0] for interval in all_intervals)
        max_confidence = max(interval[1] for interval in all_intervals)
        
        return {
            'value': ensemble_value,
            'confidence_interval': (min_confidence, max_confidence),
            'accuracy': ensemble_confidence
        }
    
    async def _create_scaling_plans(self):
        """Crée des plans de scaling basés sur les prédictions"""
        while True:
            try:
                current_time = datetime.now()
                
                # Récupérer les prédictions pertinentes
                relevant_predictions = [
                    p for p in self.predictions
                    if p.timestamp > current_time and p.confidence_score >= self.confidence_threshold
                ]
                
                if not relevant_predictions:
                    await asyncio.sleep(60)
                    continue
                
                # Analyser les prédictions et créer des plans
                scaling_plan = await self._analyze_predictions_and_plan(relevant_predictions, current_time)
                
                if scaling_plan:
                    self.scaling_plans.append(scaling_plan)
                    
                    # Stocker dans Redis
                    redis_key = f"scaling_plan:{int(scaling_plan.created_at.timestamp())}"
                    self.redis_client.setex(
                        redis_key,
                        timedelta(hours=6),
                        json.dumps(asdict(scaling_plan), default=str)
                    )
                
                await asyncio.sleep(60)  # Analyse chaque minute
                
            except Exception as e:
                logger.error(f"Erreur lors de la création des plans de scaling: {e}")
                await asyncio.sleep(120)
    
    async def _analyze_predictions_and_plan(self, predictions: List[LoadPrediction], current_time: datetime) -> Optional[ScalingPlan]:
        """Analyse les prédictions et crée un plan de scaling"""
        try:
            # Trier les prédictions par timestamp
            predictions.sort(key=lambda p: p.timestamp)
            
            # Identifier les pics de charge
            current_load = await self._get_current_load()
            current_workers = await self._get_current_workers()
            
            # Analyser la prédiction la plus proche
            next_prediction = predictions[0]
            predicted_load = next_prediction.predicted_load
            
            # Calculer le nombre optimal de workers
            optimal_workers = await self._calculate_optimal_workers(predicted_load)
            
            # Décider de l'action
            if optimal_workers > current_workers * 1.2:  # 20% de marge
                action = ScalingAction.PREEMPTIVE_SCALE_UP
                target_workers = optimal_workers
                reasoning = f"Pic de charge prévu: {predicted_load:.2f} (actuel: {current_load:.2f})"
            elif optimal_workers < current_workers * 0.8:  # 20% de marge
                action = ScalingAction.PREEMPTIVE_SCALE_DOWN
                target_workers = optimal_workers
                reasoning = f"Baisse de charge prévue: {predicted_load:.2f} (actuel: {current_load:.2f})"
            else:
                return None  # Pas de scaling nécessaire
            
            # Calculer les impacts
            cost_impact = await self._estimate_cost_impact(current_workers, target_workers)
            performance_impact = await self._estimate_performance_impact(current_workers, target_workers, predicted_load)
            
            # Créer le plan
            plan = ScalingPlan(
                created_at=current_time,
                action=action,
                target_workers=target_workers,
                execution_time=next_prediction.timestamp - timedelta(minutes=5),  # 5 minutes avant
                confidence=next_prediction.confidence_score,
                reasoning=reasoning,
                estimated_cost_impact=cost_impact,
                estimated_performance_impact=performance_impact
            )
            
            return plan
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des prédictions: {e}")
            return None
    
    async def _get_current_workers(self) -> int:
        """Récupère le nombre actuel de workers"""
        workers_data = self.redis_client.get("system:current_workers")
        return int(workers_data) if workers_data else 1
    
    async def _calculate_optimal_workers(self, predicted_load: float) -> int:
        """Calcule le nombre optimal de workers pour une charge donnée"""
        # Simplifié - pourrait être plus sophistiqué
        # Assume qu'un worker peut gérer une charge de 1.0
        base_capacity = 1.0
        workers_needed = max(1, int(predicted_load / base_capacity))
        
        # Ajouter une marge de sécurité
        return int(workers_needed * 1.1)
    
    async def _estimate_cost_impact(self, current_workers: int, target_workers: int) -> float:
        """Estime l'impact sur les coûts"""
        # Simplifié - coût par worker par heure
        cost_per_worker_hour = 0.10  # $0.10 par worker par heure
        
        worker_diff = target_workers - current_workers
        hours_impact = 1.0  # Impact sur 1 heure
        
        return worker_diff * cost_per_worker_hour * hours_impact
    
    async def _estimate_performance_impact(self, current_workers: int, target_workers: int, predicted_load: float) -> float:
        """Estime l'impact sur les performances"""
        # Simplifié - basé sur le ratio workers/load
        current_ratio = current_workers / max(predicted_load, 0.1)
        target_ratio = target_workers / max(predicted_load, 0.1)
        
        # Impact positif si le ratio s'améliore
        return (target_ratio - current_ratio) * 100  # Pourcentage
    
    async def _execute_scaling_plans(self):
        """Exécute les plans de scaling au moment approprié"""
        while True:
            try:
                current_time = datetime.now()
                
                # Vérifier les plans à exécuter
                ready_plans = [
                    plan for plan in self.scaling_plans
                    if plan.execution_time <= current_time and not hasattr(plan, 'executed')
                ]
                
                for plan in ready_plans:
                    await self._execute_scaling_plan(plan)
                    plan.executed = True
                    
                    # Mettre à jour les métriques
                    self.prometheus_metrics['scaling_plans_executed'].labels(action=plan.action.value).inc()
                
                await asyncio.sleep(30)  # Vérification toutes les 30 secondes
                
            except Exception as e:
                logger.error(f"Erreur lors de l'exécution des plans de scaling: {e}")
                await asyncio.sleep(60)
    
    async def _execute_scaling_plan(self, plan: ScalingPlan):
        """Exécute un plan de scaling"""
        try:
            logger.info(f"Exécution du plan de scaling: {plan.action.value} -> {plan.target_workers} workers")
            
            # Ici, intégration avec le système de scaling existant
            # Par exemple, appeler l'API du scaler dynamique
            
            # Simuler l'exécution
            current_workers = await self._get_current_workers()
            
            if plan.action == ScalingAction.PREEMPTIVE_SCALE_UP:
                logger.info(f"Scale up préemptif: {current_workers} -> {plan.target_workers}")
                # await dynamic_scaler.scale_up(plan.target_workers)
            elif plan.action == ScalingAction.PREEMPTIVE_SCALE_DOWN:
                logger.info(f"Scale down préemptif: {current_workers} -> {plan.target_workers}")
                # await dynamic_scaler.scale_down(plan.target_workers)
            
            logger.info(f"Plan de scaling exécuté: {plan.reasoning}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du plan de scaling: {e}")
    
    async def _retrain_models(self):
        """Réentraîne périodiquement les modèles"""
        while True:
            try:
                await asyncio.sleep(self.retrain_interval * 3600)  # Convertir en secondes
                
                current_time = datetime.now()
                if (current_time - self.last_retrain_time).total_seconds() >= self.retrain_interval * 3600:
                    if len(self.historical_data) >= self.min_samples_for_training:
                        logger.info("Réentraînement périodique des modèles")
                        await self._train_all_models()
                
            except Exception as e:
                logger.error(f"Erreur lors du réentraînement des modèles: {e}")
    
    async def _train_all_models(self):
        """Entraîne tous les modèles"""
        try:
            self.is_training = True
            
            # Préparer les données d'entraînement
            X, y = await self._prepare_training_data()
            
            if len(X) < self.min_samples_for_training:
                logger.warning(f"Pas assez de données pour l'entraînement: {len(X)}")
                return
            
            # Définir les colonnes de caractéristiques
            if not self.feature_columns:
                self.feature_columns = [f"feature_{i}" for i in range(X.shape[1])]
            
            # Diviser les données
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Entraîner chaque modèle
            for model_name, config in self.model_configs.items():
                await self._train_single_model(model_name, config, X_train, X_test, y_train, y_test)
            
            self.last_retrain_time = datetime.now()
            logger.info("Réentraînement des modèles terminé")
            
        except Exception as e:
            logger.error(f"Erreur lors du réentraînement des modèles: {e}")
        finally:
            self.is_training = False
    
    async def _prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Prépare les données d'entraînement"""
        try:
            # Convertir l'historique en DataFrame
            data_list = []
            for data in self.historical_data:
                data_dict = asdict(data)
                data_list.append(data_dict)
            
            if not data_list:
                return np.array([]), np.array([])
            
            df = pd.DataFrame(data_list)
            
            # Caractéristiques (X)
            feature_columns = [
                'hour_of_day', 'day_of_week', 'day_of_month', 'month',
                'is_weekend', 'is_holiday', 'current_load',
                'avg_load_last_hour', 'avg_load_last_6h', 'avg_load_last_24h',
                'load_trend_1h', 'load_trend_6h', 'load_trend_24h',
                'queue_size', 'error_rate', 'response_time', 'active_users',
                'business_hour', 'seasonal_factor'
            ]
            
            X = df[feature_columns].values
            
            # Cible (y) - charge future (1 heure plus tard)
            y = df['current_load'].shift(-1).fillna(df['current_load']).values
            
            # Supprimer les dernières lignes sans cible
            X = X[:-1]
            y = y[:-1]
            
            return X, y
            
        except Exception as e:
            logger.error(f"Erreur lors de la préparation des données: {e}")
            return np.array([]), np.array([])
    
    async def _train_single_model(self, model_name: str, config: Dict[str, Any], X_train: np.ndarray, X_test: np.ndarray, y_train: np.ndarray, y_test: np.ndarray):
        """Entraîne un modèle spécifique"""
        try:
            start_time = time.time()
            
            # Créer le modèle
            model_class = config['model_class']
            model = model_class(**config['params'])
            
            # Normaliser les données
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Entraîner le modèle
            model.fit(X_train_scaled, y_train)
            
            # Évaluer le modèle
            y_pred = model.predict(X_test_scaled)
            
            mae = mean_absolute_error(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # Sauvegarder le modèle
            self.models[model_name] = {
                'model': model,
                'config': config,
                'trained_at': datetime.now()
            }
            self.scalers[model_name] = scaler
            
            # Sauvegarder les performances
            self.model_performance[model_name] = {
                'mae': mae,
                'mse': mse,
                'r2_score': r2,
                'training_samples': len(X_train)
            }
            
            # Sauvegarder sur disque
            model_file = f"{self.model_path}/{model_name}_model.joblib"
            scaler_file = f"{self.model_path}/{model_name}_scaler.joblib"
            
            joblib.dump(model, model_file)
            joblib.dump(scaler, scaler_file)
            
            # Mettre à jour les métriques Prometheus
            self.prometheus_metrics['prediction_accuracy'].labels(model=model_name).set(r2)
            self.prometheus_metrics['model_training_duration'].labels(model=model_name).set(
                time.time() - start_time
            )
            
            logger.info(f"Modèle {model_name} entraîné - R²: {r2:.3f}, MAE: {mae:.3f}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'entraînement du modèle {model_name}: {e}")
    
    async def _evaluate_performance(self):
        """Évalue les performances des prédictions"""
        while True:
            try:
                await asyncio.sleep(3600)  # Évaluation chaque heure
                
                # Comparer les prédictions avec la réalité
                await self._evaluate_prediction_accuracy()
                
            except Exception as e:
                logger.error(f"Erreur lors de l'évaluation des performances: {e}")
    
    async def _evaluate_prediction_accuracy(self):
        """Évalue l'exactitude des prédictions"""
        try:
            current_time = datetime.now()
            
            # Récupérer les anciennes prédictions
            old_predictions = [
                p for p in self.predictions
                if p.timestamp < current_time - timedelta(minutes=30)
            ]
            
            if not old_predictions:
                return
            
            # Comparer avec les charges réelles
            accuracies = []
            for prediction in old_predictions:
                actual_load = await self._get_historical_load(prediction.timestamp)
                if actual_load is not None:
                    error = abs(prediction.predicted_load - actual_load)
                    relative_error = error / max(actual_load, 0.1)
                    accuracies.append(1 - relative_error)
            
            if accuracies:
                avg_accuracy = np.mean(accuracies)
                logger.info(f"Précision moyenne des prédictions: {avg_accuracy:.3f}")
                
                # Mettre à jour les métriques
                self.prometheus_metrics['prediction_accuracy'].labels(model='ensemble').set(avg_accuracy)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation de l'exactitude: {e}")
    
    async def _get_historical_load(self, timestamp: datetime) -> Optional[float]:
        """Récupère la charge réelle à un timestamp donné"""
        try:
            # Chercher dans l'historique
            for data in self.historical_data:
                if abs((data.timestamp - timestamp).total_seconds()) < 60:  # ±1 minute
                    return data.current_load
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la charge historique: {e}")
            return None
    
    async def _load_models(self):
        """Charge les modèles existants depuis le disque"""
        try:
            import os
            
            for model_name in self.model_configs.keys():
                model_file = f"{self.model_path}/{model_name}_model.joblib"
                scaler_file = f"{self.model_path}/{model_name}_scaler.joblib"
                
                if os.path.exists(model_file) and os.path.exists(scaler_file):
                    model = joblib.load(model_file)
                    scaler = joblib.load(scaler_file)
                    
                    config = self.model_configs[model_name]
                    self.models[model_name] = {
                        'model': model,
                        'config': config,
                        'trained_at': datetime.now()
                    }
                    self.scalers[model_name] = scaler
                    
                    logger.info(f"Modèle {model_name} chargé depuis le disque")
                
        except Exception as e:
            logger.error(f"Erreur lors du chargement des modèles: {e}")
    
    async def get_predictive_status(self) -> Dict[str, Any]:
        """Retourne le statut du scaling prédictif"""
        try:
            current_time = datetime.now()
            
            # Prédictions récentes
            recent_predictions = [
                p for p in self.predictions
                if p.timestamp > current_time - timedelta(hours=2)
            ]
            
            # Plans récents
            recent_plans = [
                p for p in self.scaling_plans
                if p.created_at > current_time - timedelta(hours=6)
            ]
            
            # Performance des modèles
            model_performance = {}
            for model_name, performance in self.model_performance.items():
                model_performance[model_name] = {
                    'r2_score': performance.get('r2_score', 0),
                    'mae': performance.get('mae', 0),
                    'training_samples': performance.get('training_samples', 0)
                }
            
            return {
                'status': 'active',
                'current_time': current_time.isoformat(),
                'data_points': len(self.historical_data),
                'predictions_count': len(recent_predictions),
                'plans_count': len(recent_plans),
                'models_trained': list(self.models.keys()),
                'model_performance': model_performance,
                'last_retrain': self.last_retrain_time.isoformat() if self.last_retrain_time != datetime.min else None,
                'next_predictions': [
                    {
                        'timestamp': p.timestamp.isoformat(),
                        'predicted_load': p.predicted_load,
                        'confidence': p.confidence_score,
                        'horizon_minutes': p.prediction_horizon
                    }
                    for p in recent_predictions[:5]
                ],
                'recent_plans': [
                    {
                        'created_at': p.created_at.isoformat(),
                        'action': p.action.value,
                        'target_workers': p.target_workers,
                        'confidence': p.confidence,
                        'reasoning': p.reasoning
                    }
                    for p in recent_plans[:5]
                ]
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut: {e}")
            return {'error': str(e)}


# Singleton global
_predictive_scaler: Optional[PredictiveScaler] = None


async def get_predictive_scaler() -> PredictiveScaler:
    """Retourne l'instance singleton du scaler prédictif"""
    global _predictive_scaler
    
    if _predictive_scaler is None:
        _predictive_scaler = PredictiveScaler()
    
    return _predictive_scaler


# Exemple d'utilisation
async def example_usage():
    """Exemple d'utilisation du scaling prédictif"""
    scaler = await get_predictive_scaler()
    
    # Démarrer le scaling prédictif
    scaling_task = asyncio.create_task(scaler.start_predictive_scaling())
    
    try:
        # Simuler des données
        for i in range(1000):
            # Simuler des données de charge avec des patterns
            current_time = datetime.now()
            
            # Pattern quotidien
            hour_factor = 0.5 + 0.5 * np.sin(2 * np.pi * current_time.hour / 24)
            
            # Pattern hebdomadaire
            week_factor = 1.2 if current_time.weekday() < 5 else 0.8
            
            # Charge simulée
            simulated_load = hour_factor * week_factor * np.random.normal(1.0, 0.1)
            
            # Ajouter les données
            await scaler._add_metric_point(
                FeatureData(
                    timestamp=current_time,
                    hour_of_day=current_time.hour,
                    day_of_week=current_time.weekday(),
                    day_of_month=current_time.day,
                    month=current_time.month,
                    is_weekend=current_time.weekday() >= 5,
                    is_holiday=False,
                    current_load=simulated_load,
                    avg_load_last_hour=simulated_load,
                    avg_load_last_6h=simulated_load,
                    avg_load_last_24h=simulated_load,
                    load_trend_1h=0,
                    load_trend_6h=0,
                    load_trend_24h=0,
                    queue_size=simulated_load * 10,
                    error_rate=0.01,
                    response_time=1.0,
                    active_users=simulated_load * 100,
                    business_hour=8 <= current_time.hour <= 18,
                    seasonal_factor=1.0
                )
            )
            
            await asyncio.sleep(1)
        
        # Obtenir le statut
        status = await scaler.get_predictive_status()
        print(f"Statut du scaling prédictif: {status}")
        
    finally:
        scaling_task.cancel()


if __name__ == "__main__":
    asyncio.run(example_usage())
