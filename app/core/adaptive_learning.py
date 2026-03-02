"""
Adaptive Learning Engine for Asmblr
Machine learning algorithms for continuous system improvement and optimization
"""

import asyncio
import time
import json
import numpy as np
from typing import Any
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
from loguru import logger
import redis.asyncio as redis
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, accuracy_score
import joblib

class LearningType(Enum):
    """Types of learning algorithms"""
    SUPERVISED = "supervised"
    UNSUPERVISED = "unsupervised"
    REINFORCEMENT = "reinforcement"
    ONLINE = "online"
    BATCH = "batch"

class ModelType(Enum):
    """Model types for different predictions"""
    PERFORMANCE_PREDICTION = "performance_prediction"
    RESOURCE_PREDICTION = "resource_prediction"
    ERROR_PREDICTION = "error_prediction"
    OPTIMIZATION_RECOMMENDATION = "optimization_recommendation"
    ANOMALY_DETECTION = "anomaly_detection"
    USER_BEHAVIOR = "user_behavior"

@dataclass
class LearningData:
    """Learning data point"""
    features: dict[str, float]
    target: float | int | str
    timestamp: datetime
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_vector(self, feature_names: list[str]) -> np.ndarray:
        """Convert to feature vector"""
        return np.array([self.features.get(name, 0.0) for name in feature_names])

@dataclass
class ModelMetrics:
    """Model performance metrics"""
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    mse: float = 0.0
    mae: float = 0.0
    r2_score: float = 0.0
    training_time: float = 0.0
    prediction_time: float = 0.0
    last_updated: datetime | None = None

class AdaptiveLearningEngine:
    """Adaptive learning engine for continuous system improvement"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_names = {}
        self.model_metrics = {}
        
        # Learning configuration
        self.learning_rate = 0.01
        self.batch_size = 100
        self.min_samples_for_training = 50
        self.retraining_interval = 3600  # 1 hour
        self.model_retention_period = 7 * 24 * 3600  # 7 days
        
        # Data storage
        self.learning_data = defaultdict(deque)
        self.feature_history = defaultdict(deque)
        self.prediction_history = defaultdict(deque)
        
        # Learning strategies
        self.learning_strategies = {
            ModelType.PERFORMANCE_PREDICTION: LearningType.SUPERVISED,
            ModelType.RESOURCE_PREDICTION: LearningType.SUPERVISED,
            ModelType.ERROR_PREDICTION: LearningType.SUPERVISED,
            ModelType.OPTIMIZATION_RECOMMENDATION: LearningType.REINFORCEMENT,
            ModelType.ANOMALY_DETECTION: LearningType.UNSUPERVISED,
            ModelType.USER_BEHAVIOR: LearningType.ONLINE
        }
        
        # Model configurations
        self.model_configs = {
            ModelType.PERFORMANCE_PREDICTION: {
                'model_class': RandomForestRegressor,
                'params': {'n_estimators': 100, 'random_state': 42}
            },
            ModelType.RESOURCE_PREDICTION: {
                'model_class': RandomForestRegressor,
                'params': {'n_estimators': 50, 'random_state': 42}
            },
            ModelType.ERROR_PREDICTION: {
                'model_class': RandomForestClassifier,
                'params': {'n_estimators': 100, 'random_state': 42}
            },
            ModelType.OPTIMIZATION_RECOMMENDATION: {
                'model_class': LinearRegression,
                'params': {}
            },
            ModelType.ANOMALY_DETECTION: {
                'model_class': 'IsolationForest',  # Special case
                'params': {'contamination': 0.1}
            },
            ModelType.USER_BEHAVIOR: {
                'model_class': LogisticRegression,
                'params': {'random_state': 42}
            }
        }
        
        # Redis for distributed learning
        self.redis_client = None
        self.redis_enabled = False
        
        # Background tasks
        self.training_task = None
        self.cleanup_task = None
        self.evaluation_task = None
        
        # Performance tracking
        self.global_metrics = {
            'total_predictions': 0,
            'accurate_predictions': 0,
            'model_updates': 0,
            'learning_cycles': 0,
            'avg_accuracy': 0.0
        }
    
    async def initialize(self):
        """Initialize the adaptive learning engine"""
        try:
            # Initialize Redis connection
            try:
                self.redis_client = redis.from_url(
                    "redis://localhost:6379/6",
                    max_connections=20
                )
                await self.redis_client.ping()
                self.redis_enabled = True
                logger.info("Redis connection established for adaptive learning")
            except Exception as e:
                logger.warning(f"Redis not available, using local learning: {e}")
            
            # Initialize models
            await self._initialize_models()
            
            # Load existing models if available
            await self._load_models()
            
            # Start background tasks
            await self.start_background_tasks()
            
            logger.info("Adaptive learning engine initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize adaptive learning engine: {e}")
            raise
    
    async def _initialize_models(self):
        """Initialize ML models"""
        try:
            for model_type, config in self.model_configs.items():
                model_class = config['model_class']
                params = config['params']
                
                if model_class == 'IsolationForest':
                    # Special case for anomaly detection
                    from sklearn.ensemble import IsolationForest
                    model = IsolationForest(**params)
                else:
                    model = model_class(**params)
                
                self.models[model_type] = model
                self.scalers[model_type] = StandardScaler()
                self.feature_names[model_type] = []
                self.model_metrics[model_type] = ModelMetrics()
                
                logger.info(f"Initialized model for {model_type.value}")
            
        except Exception as e:
            logger.error(f"Model initialization error: {e}")
            raise
    
    async def add_learning_data(
        self,
        model_type: ModelType,
        features: dict[str, float],
        target: float | int | str,
        source: str = "unknown",
        metadata: dict[str, Any] = None
    ):
        """Add learning data point"""
        try:
            data_point = LearningData(
                features=features,
                target=target,
                timestamp=datetime.now(),
                source=source,
                metadata=metadata or {}
            )
            
            self.learning_data[model_type].append(data_point)
            
            # Update feature names
            for feature_name in features:
                if feature_name not in self.feature_names[model_type]:
                    self.feature_names[model_type].append(feature_name)
            
            # Store in Redis if enabled
            if self.redis_enabled:
                await self._store_learning_data(model_type, data_point)
            
            # Check if we should trigger training
            if len(self.learning_data[model_type]) >= self.batch_size:
                await self._trigger_training(model_type)
            
        except Exception as e:
            logger.error(f"Failed to add learning data: {e}")
    
    async def predict(
        self,
        model_type: ModelType,
        features: dict[str, float],
        return_confidence: bool = False
    ) -> float | int | str | tuple[float | int | str, float]:
        """Make prediction using trained model"""
        try:
            if model_type not in self.models:
                raise ValueError(f"Model {model_type.value} not initialized")
            
            model = self.models[model_type]
            feature_names = self.feature_names[model_type]
            
            if not feature_names:
                raise ValueError(f"No features available for model {model_type.value}")
            
            # Convert features to vector
            feature_vector = np.array([features.get(name, 0.0) for name in feature_names])
            
            # Scale features if scaler is fitted
            if hasattr(self.scalers[model_type], 'mean_'):
                feature_vector = self.scalers[model_type].transform([feature_vector])[0]
            
            # Make prediction
            start_time = time.time()
            
            if model_type == ModelType.ANOMALY_DETECTION:
                # Anomaly detection returns -1 for anomalies, 1 for normal
                prediction = model.predict([feature_vector])[0]
                prediction = 1 if prediction == 1 else 0  # Convert to binary
            else:
                prediction = model.predict([feature_vector])[0]
            
            prediction_time = time.time() - start_time
            
            # Calculate confidence if requested
            confidence = 0.5
            if return_confidence and hasattr(model, 'predict_proba'):
                try:
                    probabilities = model.predict_proba([feature_vector])[0]
                    confidence = max(probabilities)
                except:
                    pass
            
            # Update prediction history
            self.prediction_history[model_type].append({
                'timestamp': datetime.now(),
                'features': features,
                'prediction': prediction,
                'confidence': confidence,
                'prediction_time': prediction_time
            })
            
            # Update global metrics
            self.global_metrics['total_predictions'] += 1
            
            # Store in Redis if enabled
            if self.redis_enabled:
                await self._store_prediction(model_type, features, prediction, confidence)
            
            if return_confidence:
                return prediction, confidence
            else:
                return prediction
            
        except Exception as e:
            logger.error(f"Prediction error for {model_type.value}: {e}")
            # Return default prediction
            if model_type in [ModelType.ERROR_PREDICTION, ModelType.ANOMALY_DETECTION]:
                return 0 if not return_confidence else (0, 0.5)
            else:
                return 0.0 if not return_confidence else (0.0, 0.5)
    
    async def train_model(self, model_type: ModelType, force: bool = False):
        """Train model for specific type"""
        try:
            data_points = list(self.learning_data[model_type])
            
            if len(data_points) < self.min_samples_for_training and not force:
                logger.info(f"Insufficient data for training {model_type.value}: {len(data_points)} < {self.min_samples_for_training}")
                return
            
            logger.info(f"Training model for {model_type.value} with {len(data_points)} samples")
            
            start_time = time.time()
            
            # Prepare training data
            feature_names = self.feature_names[model_type]
            X = np.array([dp.to_vector(feature_names) for dp in data_points])
            y = np.array([dp.target for dp in data_points])
            
            # Scale features
            self.scalers[model_type].fit(X)
            X_scaled = self.scalers[model_type].transform(X)
            
            # Train model
            model = self.models[model_type]
            
            if model_type == ModelType.ANOMALY_DETECTION:
                # Anomaly detection is unsupervised
                model.fit(X_scaled)
            else:
                # Split data for evaluation
                if len(data_points) > 20:
                    X_train, X_test, y_train, y_test = train_test_split(
                        X_scaled, y, test_size=0.2, random_state=42
                    )
                    
                    # Train model
                    model.fit(X_train, y_train)
                    
                    # Evaluate model
                    y_pred = model.predict(X_test)
                    
                    # Calculate metrics
                    if model_type in [ModelType.ERROR_PREDICTION, ModelType.USER_BEHAVIOR]:
                        # Classification metrics
                        accuracy = accuracy_score(y_test, y_pred)
                        self.model_metrics[model_type].accuracy = accuracy
                        
                        # Calculate precision, recall, F1 if possible
                        try:
                            from sklearn.metrics import precision_score, recall_score, f1_score
                            self.model_metrics[model_type].precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
                            self.model_metrics[model_type].recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
                            self.model_metrics[model_type].f1_score = f1_score(y_test, y_pred, average='weighted', zero_division=0)
                        except:
                            pass
                    else:
                        # Regression metrics
                        mse = mean_squared_error(y_test, y_pred)
                        self.model_metrics[model_type].mse = mse
                        self.model_metrics[model_type].mae = np.mean(np.abs(y_test - y_pred))
                        
                        # Calculate R² score
                        try:
                            from sklearn.metrics import r2_score
                            self.model_metrics[model_type].r2_score = r2_score(y_test, y_pred)
                        except:
                            pass
                else:
                    # Not enough data for split, train on all data
                    model.fit(X_scaled)
            
            training_time = time.time() - start_time
            self.model_metrics[model_type].training_time = training_time
            self.model_metrics[model_type].last_updated = datetime.now()
            
            # Update global metrics
            self.global_metrics['model_updates'] += 1
            
            # Save model
            await self._save_model(model_type)
            
            logger.info(f"Model training completed for {model_type.value} in {training_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Model training error for {model_type.value}: {e}")
    
    async def evaluate_model(self, model_type: ModelType) -> ModelMetrics:
        """Evaluate model performance"""
        try:
            if model_type not in self.model_metrics:
                return ModelMetrics()
            
            metrics = self.model_metrics[model_type]
            
            # Calculate additional metrics from prediction history
            predictions = list(self.prediction_history[model_type])
            
            if len(predictions) > 10:
                # Calculate average prediction time
                avg_prediction_time = np.mean([p['prediction_time'] for p in predictions])
                metrics.prediction_time = avg_prediction_time
                
                # Calculate accuracy if we have ground truth
                # This would require comparing with actual outcomes
                # For now, use the training accuracy as approximation
            
            return metrics
            
        except Exception as e:
            logger.error(f"Model evaluation error for {model_type.value}: {e}")
            return ModelMetrics()
    
    async def get_feature_importance(self, model_type: ModelType) -> dict[str, float]:
        """Get feature importance for model"""
        try:
            if model_type not in self.models:
                return {}
            
            model = self.models[model_type]
            feature_names = self.feature_names[model_type]
            
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
                return dict(zip(feature_names, importances))
            elif hasattr(model, 'coef_'):
                # Linear models
                coef = model.coef_
                if len(coef.shape) > 1:
                    coef = coef[0]
                return dict(zip(feature_names, np.abs(coef)))
            else:
                return {}
            
        except Exception as e:
            logger.error(f"Feature importance error for {model_type.value}: {e}")
            return {}
    
    async def optimize_hyperparameters(self, model_type: ModelType):
        """Optimize hyperparameters for model"""
        try:
            from sklearn.model_selection import GridSearchCV
            
            data_points = list(self.learning_data[model_type])
            
            if len(data_points) < self.min_samples_for_training * 2:
                logger.info(f"Insufficient data for hyperparameter optimization: {len(data_points)}")
                return
            
            logger.info(f"Optimizing hyperparameters for {model_type.value}")
            
            # Prepare data
            feature_names = self.feature_names[model_type]
            X = np.array([dp.to_vector(feature_names) for dp in data_points])
            y = np.array([dp.target for dp in data_points])
            
            # Scale features
            X_scaled = self.scalers[model_type].fit_transform(X)
            
            # Define parameter grid
            model_class = self.model_configs[model_type]['model_class']
            
            if model_class == RandomForestRegressor or model_class == RandomForestClassifier:
                param_grid = {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [None, 10, 20],
                    'min_samples_split': [2, 5, 10]
                }
            elif model_class == LinearRegression or model_class == LogisticRegression:
                param_grid = {
                    'C': [0.1, 1.0, 10.0] if model_class == LogisticRegression else {}
                }
            else:
                logger.info(f"Hyperparameter optimization not supported for {model_class}")
                return
            
            # Perform grid search
            model = model_class()
            grid_search = GridSearchCV(
                model, param_grid, cv=3, scoring='accuracy' if model_type in [ModelType.ERROR_PREDICTION, ModelType.USER_BEHAVIOR] else 'neg_mean_squared_error'
            )
            
            grid_search.fit(X_scaled, y)
            
            # Update model with best parameters
            best_params = grid_search.best_params_
            self.model_configs[model_type]['params'] = best_params
            
            # Retrain model with best parameters
            self.models[model_type] = model_class(**best_params)
            await self.train_model(model_type, force=True)
            
            logger.info(f"Hyperparameter optimization completed for {model_type.value}: {best_params}")
            
        except Exception as e:
            logger.error(f"Hyperparameter optimization error for {model_type.value}: {e}")
    
    async def start_background_tasks(self):
        """Start background learning tasks"""
        self.training_task = asyncio.create_task(self._training_loop())
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        self.evaluation_task = asyncio.create_task(self._evaluation_loop())
        
        logger.info("Background learning tasks started")
    
    async def _training_loop(self):
        """Background training loop"""
        while True:
            try:
                # Train all models that have enough data
                for model_type in ModelType:
                    if len(self.learning_data[model_type]) >= self.batch_size:
                        await self.train_model(model_type)
                
                await asyncio.sleep(self.retraining_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Training loop error: {e}")
                await asyncio.sleep(self.retraining_interval)
    
    async def _cleanup_loop(self):
        """Background cleanup loop"""
        while True:
            try:
                # Clean old data
                cutoff_time = datetime.now() - timedelta(seconds=self.model_retention_period)
                
                for model_type in ModelType:
                    # Clean learning data
                    original_size = len(self.learning_data[model_type])
                    self.learning_data[model_type] = deque(
                        (dp for dp in self.learning_data[model_type] if dp.timestamp > cutoff_time),
                        maxlen=1000
                    )
                    
                    cleaned_count = original_size - len(self.learning_data[model_type])
                    if cleaned_count > 0:
                        logger.info(f"Cleaned {cleaned_count} old data points for {model_type.value}")
                    
                    # Clean prediction history
                    original_size = len(self.prediction_history[model_type])
                    self.prediction_history[model_type] = deque(
                        (p for p in self.prediction_history[model_type] if p['timestamp'] > cutoff_time),
                        maxlen=1000
                    )
                
                await asyncio.sleep(3600)  # Clean every hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(3600)
    
    async def _evaluation_loop(self):
        """Background evaluation loop"""
        while True:
            try:
                # Evaluate all models
                for model_type in ModelType:
                    metrics = await self.evaluate_model(model_type)
                    self.model_metrics[model_type] = metrics
                
                # Update global metrics
                await self._update_global_metrics()
                
                await asyncio.sleep(1800)  # Evaluate every 30 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Evaluation loop error: {e}")
                await asyncio.sleep(1800)
    
    async def _update_global_metrics(self):
        """Update global learning metrics"""
        try:
            # Calculate average accuracy across all models
            accuracies = []
            for metrics in self.model_metrics.values():
                if metrics.accuracy > 0:
                    accuracies.append(metrics.accuracy)
            
            if accuracies:
                self.global_metrics['avg_accuracy'] = np.mean(accuracies)
            
            # Update learning cycles
            self.global_metrics['learning_cycles'] += 1
            
        except Exception as e:
            logger.error(f"Global metrics update error: {e}")
    
    async def _trigger_training(self, model_type: ModelType):
        """Trigger training for specific model type"""
        try:
            # Check if we should train immediately or wait for batch
            if len(self.learning_data[model_type]) >= self.batch_size * 2:
                # Train immediately if we have lots of data
                await self.train_model(model_type)
            
        except Exception as e:
            logger.error(f"Training trigger error for {model_type.value}: {e}")
    
    async def _store_learning_data(self, model_type: ModelType, data: LearningData):
        """Store learning data in Redis"""
        try:
            key = f"learning_data:{model_type.value}:{data.timestamp.isoformat()}"
            value = {
                'features': data.features,
                'target': data.target,
                'source': data.source,
                'metadata': data.metadata
            }
            
            await self.redis_client.setex(
                key,
                self.model_retention_period,
                json.dumps(value)
            )
            
        except Exception as e:
            logger.error(f"Redis learning data storage error: {e}")
    
    async def _store_prediction(self, model_type: ModelType, features: dict[str, float], prediction: Any, confidence: float):
        """Store prediction in Redis"""
        try:
            key = f"prediction:{model_type.value}:{datetime.now().isoformat()}"
            value = {
                'features': features,
                'prediction': prediction,
                'confidence': confidence
            }
            
            await self.redis_client.setex(
                key,
                self.model_retention_period,
                json.dumps(value)
            )
            
        except Exception as e:
            logger.error(f"Redis prediction storage error: {e}")
    
    async def _save_model(self, model_type: ModelType):
        """Save model to disk"""
        try:
            model_path = f"models/{model_type.value}_model.pkl"
            scaler_path = f"models/{model_type.value}_scaler.pkl"
            
            # Create models directory if it doesn't exist
            import os
            os.makedirs("models", exist_ok=True)
            
            # Save model
            joblib.dump(self.models[model_type], model_path)
            
            # Save scaler
            joblib.dump(self.scalers[model_type], scaler_path)
            
            # Save metadata
            metadata = {
                'feature_names': self.feature_names[model_type],
                'model_metrics': asdict(self.model_metrics[model_type]),
                'model_config': self.model_configs[model_type]
            }
            
            metadata_path = f"models/{model_type.value}_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            logger.info(f"Model saved for {model_type.value}")
            
        except Exception as e:
            logger.error(f"Model save error for {model_type.value}: {e}")
    
    async def _load_models(self):
        """Load models from disk"""
        try:
            import os
            
            for model_type in ModelType:
                model_path = f"models/{model_type.value}_model.pkl"
                scaler_path = f"models/{model_type.value}_scaler.pkl"
                metadata_path = f"models/{model_type.value}_metadata.json"
                
                if os.path.exists(model_path) and os.path.exists(scaler_path):
                    # Load model
                    self.models[model_type] = joblib.load(model_path)
                    
                    # Load scaler
                    self.scalers[model_type] = joblib.load(scaler_path)
                    
                    # Load metadata
                    if os.path.exists(metadata_path):
                        with open(metadata_path) as f:
                            metadata = json.load(f)
                        
                        self.feature_names[model_type] = metadata.get('feature_names', [])
                        self.model_metrics[model_type] = ModelMetrics(**metadata.get('model_metrics', {}))
                        
                        # Update model config if available
                        if 'model_config' in metadata:
                            self.model_configs[model_type] = metadata['model_config']
                    
                    logger.info(f"Model loaded for {model_type.value}")
            
        except Exception as e:
            logger.error(f"Model loading error: {e}")
    
    async def get_learning_insights(self) -> dict[str, Any]:
        """Get insights from learning data"""
        try:
            insights = {
                'global_metrics': self.global_metrics,
                'model_metrics': {},
                'feature_importance': {},
                'data_quality': {},
                'recommendations': []
            }
            
            # Model-specific insights
            for model_type in ModelType:
                if model_type in self.model_metrics:
                    insights['model_metrics'][model_type.value] = asdict(self.model_metrics[model_type])
                    
                    # Feature importance
                    importance = await self.get_feature_importance(model_type)
                    if importance:
                        insights['feature_importance'][model_type.value] = importance
                    
                    # Data quality metrics
                    data_points = list(self.learning_data[model_type])
                    if data_points:
                        insights['data_quality'][model_type.value] = {
                            'total_samples': len(data_points),
                            'date_range': {
                                'start': min(dp.timestamp for dp in data_points).isoformat(),
                                'end': max(dp.timestamp for dp in data_points).isoformat()
                            },
                            'sources': list(set(dp.source for dp in data_points))
                        }
            
            # Generate recommendations
            insights['recommendations'] = await self._generate_recommendations()
            
            return insights
            
        except Exception as e:
            logger.error(f"Learning insights error: {e}")
            return {}
    
    async def _generate_recommendations(self) -> list[str]:
        """Generate learning recommendations"""
        recommendations = []
        
        try:
            # Check data quality
            for model_type in ModelType:
                data_count = len(self.learning_data[model_type])
                
                if data_count < self.min_samples_for_training:
                    recommendations.append(
                        f"Insufficient data for {model_type.value}: {data_count} < {self.min_samples_for_training}. "
                        f"Collect more training data."
                    )
                
                # Check model performance
                metrics = self.model_metrics.get(model_type)
                if metrics and metrics.accuracy < 0.7:
                    recommendations.append(
                        f"Low accuracy for {model_type.value}: {metrics.accuracy:.2f}. "
                        f"Consider feature engineering or hyperparameter optimization."
                    )
            
            # Check global metrics
            if self.global_metrics['avg_accuracy'] < 0.8:
                recommendations.append(
                    "Overall model accuracy is low. Consider collecting more diverse training data."
                )
            
            if self.global_metrics['model_updates'] < 10:
                recommendations.append(
                    "Models have been updated few times. Consider increasing training frequency."
                )
            
        except Exception as e:
            logger.error(f"Recommendation generation error: {e}")
        
        return recommendations
    
    async def shutdown(self):
        """Shutdown the adaptive learning engine"""
        logger.info("Shutting down adaptive learning engine...")
        
        # Cancel background tasks
        if self.training_task:
            self.training_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()
        if self.evaluation_task:
            self.evaluation_task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*[
            self.training_task,
            self.cleanup_task,
            self.evaluation_task
        ], return_exceptions=True)
        
        # Save all models
        for model_type in ModelType:
            if model_type in self.models:
                await self._save_model(model_type)
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Adaptive learning engine shutdown complete")

# Global adaptive learning engine instance
adaptive_learning_engine = AdaptiveLearningEngine()
