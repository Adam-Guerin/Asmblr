"""
ML Ops Pipeline for Asmblr
Automated model training, evaluation, deployment, and monitoring
"""

import json
import time
import logging
from datetime import datetime
from typing import Any
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
from kubernetes import client, config
import mlflow
import mlflow.sklearn
import mlflow.pytorch
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

logger = logging.getLogger(__name__)

@dataclass
class ModelMetadata:
    """Model metadata for tracking"""
    name: str
    version: str
    model_type: str
    framework: str
    created_at: datetime
    performance_metrics: dict[str, float]
    hyperparameters: dict[str, Any]
    training_data_hash: str
    model_size_mb: float
    deployment_status: str
    endpoint_url: str | None = None

@dataclass
class TrainingConfig:
    """Training configuration"""
    model_name: str
    framework: str
    hyperparameters: dict[str, Any]
    training_data_path: str
    validation_split: float = 0.2
    test_split: float = 0.1
    random_seed: int = 42
    max_epochs: int = 100
    early_stopping_patience: int = 10
    batch_size: int = 32
    learning_rate: float = 0.001

class ModelRegistry:
    """Model registry for tracking and versioning"""
    
    def __init__(self, registry_path: str = "ml_ops/model_registry.json"):
        self.registry_path = registry_path
        self.models: dict[str, list[ModelMetadata]] = {}
        self._load_registry()
    
    def _load_registry(self):
        """Load model registry from file"""
        if Path(self.registry_path).exists():
            with open(self.registry_path) as f:
                data = json.load(f)
                for name, models in data.items():
                    self.models[name] = [
                        ModelMetadata(**{**model, 'created_at': datetime.fromisoformat(model['created_at'])})
                        for model in models
                    ]
    
    def _save_registry(self):
        """Save model registry to file"""
        Path(self.registry_path).parent.mkdir(parents=True, exist_ok=True)
        data = {}
        for name, models in self.models.items():
            data[name] = [
                {**asdict(model), 'created_at': model.created_at.isoformat()}
                for model in models
            ]
        with open(self.registry_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def register_model(self, metadata: ModelMetadata):
        """Register a new model"""
        if metadata.name not in self.models:
            self.models[metadata.name] = []
        
        # Check if version already exists
        existing_versions = {m.version for m in self.models[metadata.name]}
        if metadata.version in existing_versions:
            raise ValueError(f"Model {metadata.name} version {metadata.version} already exists")
        
        self.models[metadata.name].append(metadata)
        self._save_registry()
        logger.info(f"Registered model {metadata.name} version {metadata.version}")
    
    def get_latest_model(self, name: str) -> ModelMetadata | None:
        """Get latest version of a model"""
        if name not in self.models or not self.models[name]:
            return None
        
        return max(self.models[name], key=lambda m: m.created_at)
    
    def get_model(self, name: str, version: str) -> ModelMetadata | None:
        """Get specific version of a model"""
        if name not in self.models:
            return None
        
        for model in self.models[name]:
            if model.version == version:
                return model
        return None
    
    def list_models(self) -> dict[str, list[str]]:
        """List all models and their versions"""
        return {
            name: [m.version for m in models]
            for name, models in self.models.items()
        }

class ModelTrainer:
    """Model training with MLflow tracking"""
    
    def __init__(self, config: TrainingConfig, registry: ModelRegistry):
        self.config = config
        self.registry = registry
        self.experiment_name = f"asmblr_{config.model_name}"
        
        # Initialize MLflow
        mlflow.set_experiment(self.experiment_name)
        
        # Calculate data hash
        self.training_data_hash = self._calculate_data_hash()
    
    def _calculate_data_hash(self) -> str:
        """Calculate hash of training data for reproducibility"""
        hash_md5 = hashlib.md5()
        with open(self.config.training_data_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def prepare_data(self) -> tuple[Any, Any, Any, Any]:
        """Prepare training, validation, and test data"""
        logger.info(f"Loading data from {self.config.training_data_path}")
        
        # Load data (example with CSV)
        df = pd.read_csv(self.config.training_data_path)
        
        # Split features and target
        X = df.drop('target', axis=1)
        y = df['target']
        
        # Split data
        X_train, X_temp, y_train, y_temp = train_test_split(
            X, y, test_size=self.config.validation_split + self.config.test_split,
            random_state=self.config.random_seed
        )
        
        X_val, X_test, y_val, y_test = train_test_split(
            X_temp, y_temp, test_size=self.config.test_split / (self.config.validation_split + self.config.test_split),
            random_state=self.config.random_seed
        )
        
        return X_train, X_val, X_test, y_train, y_val, y_test
    
    def train_model(self) -> ModelMetadata:
        """Train model with MLflow tracking"""
        with mlflow.start_run(run_name=f"{self.config.model_name}_v{int(time.time())}") as run:
            # Log hyperparameters
            mlflow.log_params(self.config.hyperparameters)
            mlflow.log_param("data_hash", self.training_data_hash)
            
            # Prepare data
            X_train, X_val, X_test, y_train, y_val, y_test = self.prepare_data()
            
            # Train model based on framework
            if self.config.framework == "sklearn":
                model, metrics = self._train_sklearn(X_train, X_val, y_train, y_val)
            elif self.config.framework == "pytorch":
                model, metrics = self._train_pytorch(X_train, X_val, y_train, y_val)
            else:
                raise ValueError(f"Unsupported framework: {self.config.framework}")
            
            # Evaluate on test set
            test_metrics = self._evaluate_model(model, X_test, y_test)
            metrics.update(test_metrics)
            
            # Log metrics
            for metric_name, value in metrics.items():
                mlflow.log_metric(metric_name, value)
            
            # Log model
            model_path = f"models/{self.config.model_name}"
            if self.config.framework == "sklearn":
                mlflow.sklearn.log_model(model, model_path)
            elif self.config.framework == "pytorch":
                mlflow.pytorch.log_model(model, model_path)
            
            # Create metadata
            metadata = ModelMetadata(
                name=self.config.model_name,
                version=run.info.run_id[:8],  # Use first 8 chars of run ID
                model_type=self.config.hyperparameters.get("model_type", "unknown"),
                framework=self.config.framework,
                created_at=datetime.now(),
                performance_metrics=metrics,
                hyperparameters=self.config.hyperparameters,
                training_data_hash=self.training_data_hash,
                model_size_mb=self._get_model_size(model),
                deployment_status="trained"
            )
            
            # Register model
            self.registry.register_model(metadata)
            
            logger.info(f"Training completed for {self.config.model_name}")
            return metadata
    
    def _train_sklearn(self, X_train, X_val, y_train, y_val) -> tuple[Any, dict[str, float]]:
        """Train sklearn model"""
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.linear_model import LogisticRegression
        from sklearn.svm import SVC
        
        model_type = self.config.hyperparameters.get("model_type", "random_forest")
        
        if model_type == "random_forest":
            model = RandomForestClassifier(
                n_estimators=self.config.hyperparameters.get("n_estimators", 100),
                max_depth=self.config.hyperparameters.get("max_depth", 10),
                random_state=self.config.random_seed
            )
        elif model_type == "logistic_regression":
            model = LogisticRegression(
                C=self.config.hyperparameters.get("C", 1.0),
                random_state=self.config.random_seed
            )
        elif model_type == "svm":
            model = SVC(
                C=self.config.hyperparameters.get("C", 1.0),
                kernel=self.config.hyperparameters.get("kernel", "rbf"),
                random_state=self.config.random_seed
            )
        else:
            raise ValueError(f"Unsupported sklearn model type: {model_type}")
        
        # Train
        model.fit(X_train, y_train)
        
        # Validate
        y_pred = model.predict(X_val)
        metrics = {
            "val_accuracy": accuracy_score(y_val, y_pred),
            "val_precision": precision_score(y_val, y_pred, average='weighted'),
            "val_recall": recall_score(y_val, y_pred, average='weighted'),
            "val_f1": f1_score(y_val, y_pred, average='weighted')
        }
        
        return model, metrics
    
    def _train_pytorch(self, X_train, X_val, y_train, y_val) -> tuple[Any, dict[str, float]]:
        """Train PyTorch model"""
        import torch
        import torch.nn as nn
        import torch.optim as optim
        from torch.utils.data import DataLoader, TensorDataset
        
        # Convert to tensors
        X_train_tensor = torch.FloatTensor(X_train.values if hasattr(X_train, 'values') else X_train)
        y_train_tensor = torch.LongTensor(y_train.values if hasattr(y_train, 'values') else y_train)
        X_val_tensor = torch.FloatTensor(X_val.values if hasattr(X_val, 'values') else X_val)
        y_val_tensor = torch.LongTensor(y_val.values if hasattr(y_val, 'values') else y_val)
        
        # Create datasets
        train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
        val_dataset = TensorDataset(X_val_tensor, y_val_tensor)
        
        train_loader = DataLoader(train_dataset, batch_size=self.config.batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=self.config.batch_size)
        
        # Define model
        input_size = X_train.shape[1]
        hidden_size = self.config.hyperparameters.get("hidden_size", 64)
        num_classes = len(np.unique(y_train))
        
        class SimpleNN(nn.Module):
            def __init__(self, input_size, hidden_size, num_classes):
                super().__init__()
                self.fc1 = nn.Linear(input_size, hidden_size)
                self.fc2 = nn.Linear(hidden_size, hidden_size)
                self.fc3 = nn.Linear(hidden_size, num_classes)
                self.dropout = nn.Dropout(0.2)
                self.relu = nn.ReLU()
            
            def forward(self, x):
                x = self.relu(self.fc1(x))
                x = self.dropout(x)
                x = self.relu(self.fc2(x))
                x = self.dropout(x)
                x = self.fc3(x)
                return x
        
        model = SimpleNN(input_size, hidden_size, num_classes)
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters(), lr=self.config.learning_rate)
        
        # Training loop
        best_val_loss = float('inf')
        patience_counter = 0
        
        for epoch in range(self.config.max_epochs):
            model.train()
            train_loss = 0.0
            
            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                train_loss += loss.item()
            
            # Validation
            model.eval()
            val_loss = 0.0
            val_correct = 0
            val_total = 0
            
            with torch.no_grad():
                for batch_X, batch_y in val_loader:
                    outputs = model(batch_X)
                    loss = criterion(outputs, batch_y)
                    val_loss += loss.item()
                    
                    _, predicted = torch.max(outputs.data, 1)
                    val_total += batch_y.size(0)
                    val_correct += (predicted == batch_y).sum().item()
            
            val_accuracy = val_correct / val_total
            
            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                best_model_state = model.state_dict().copy()
            else:
                patience_counter += 1
                if patience_counter >= self.config.early_stopping_patience:
                    break
            
            if epoch % 10 == 0:
                logger.info(f"Epoch {epoch}, Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}, Val Acc: {val_accuracy:.4f}")
        
        # Load best model
        model.load_state_dict(best_model_state)
        
        # Calculate final metrics
        model.eval()
        val_predictions = []
        val_targets = []
        
        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                outputs = model(batch_X)
                _, predicted = torch.max(outputs.data, 1)
                val_predictions.extend(predicted.numpy())
                val_targets.extend(batch_y.numpy())
        
        metrics = {
            "val_accuracy": accuracy_score(val_targets, val_predictions),
            "val_precision": precision_score(val_targets, val_predictions, average='weighted'),
            "val_recall": recall_score(val_targets, val_predictions, average='weighted'),
            "val_f1": f1_score(val_targets, val_predictions, average='weighted'),
            "val_loss": best_val_loss
        }
        
        return model, metrics
    
    def _evaluate_model(self, model, X_test, y_test) -> dict[str, float]:
        """Evaluate model on test set"""
        if self.config.framework == "sklearn":
            y_pred = model.predict(X_test)
        elif self.config.framework == "pytorch":
            import torch
            X_test_tensor = torch.FloatTensor(X_test.values if hasattr(X_test, 'values') else X_test)
            model.eval()
            with torch.no_grad():
                outputs = model(X_test_tensor)
                _, y_pred = torch.max(outputs.data, 1)
            y_pred = y_pred.numpy()
        
        return {
            "test_accuracy": accuracy_score(y_test, y_pred),
            "test_precision": precision_score(y_test, y_pred, average='weighted'),
            "test_recall": recall_score(y_test, y_pred, average='weighted'),
            "test_f1": f1_score(y_test, y_pred, average='weighted')
        }
    
    def _get_model_size(self, model) -> float:
        """Get model size in MB"""
        import pickle
        import os
        
        temp_path = "/tmp/model_temp.pkl"
        with open(temp_path, 'wb') as f:
            pickle.dump(model, f)
        
        size_mb = os.path.getsize(temp_path) / (1024 * 1024)
        os.remove(temp_path)
        
        return size_mb

class ModelDeployer:
    """Model deployment to Kubernetes"""
    
    def __init__(self, namespace: str = "asmblr"):
        self.namespace = namespace
        config.load_kube_config()
        self.apps_v1 = client.AppsV1Api()
        self.core_v1 = client.CoreV1Api()
        self.custom_api = client.CustomObjectsApi()
    
    def deploy_model(self, metadata: ModelMetadata) -> str:
        """Deploy model to Kubernetes"""
        deployment_name = f"{metadata.name}-{metadata.version}"
        
        # Create deployment
        deployment = self._create_deployment(metadata, deployment_name)
        
        # Create service
        service = self._create_service(metadata, deployment_name)
        
        # Apply to cluster
        self.apps_v1.create_namespaced_deployment(
            namespace=self.namespace,
            body=deployment
        )
        
        self.core_v1.create_namespaced_service(
            namespace=self.namespace,
            body=service
        )
        
        # Update metadata
        metadata.deployment_status = "deployed"
        metadata.endpoint_url = f"http://{deployment_name}.{self.namespace}.svc.cluster.local:8000"
        
        logger.info(f"Deployed model {metadata.name} version {metadata.version}")
        return deployment_name
    
    def _create_deployment(self, metadata: ModelMetadata, deployment_name: str) -> client.V1Deployment:
        """Create Kubernetes deployment"""
        container = client.V1Container(
            name=deployment_name,
            image=f"asmblr/{metadata.name}:{metadata.version}",
            ports=[client.V1ContainerPort(container_port=8000)],
            resources=client.V1ResourceRequirements(
                requests={"cpu": "100m", "memory": "256Mi"},
                limits={"cpu": "500m", "memory": "512Mi"}
            ),
            env=[
                client.V1EnvVar(name="MODEL_NAME", value=metadata.name),
                client.V1EnvVar(name="MODEL_VERSION", value=metadata.version),
                client.V1EnvVar(name="FRAMEWORK", value=metadata.framework)
            ],
            liveness_probe=client.V1Probe(
                http_get=client.V1HTTPGetAction(path="/health", port=8000),
                initial_delay_seconds=30,
                period_seconds=10
            ),
            readiness_probe=client.V1Probe(
                http_get=client.V1HTTPGetAction(path="/ready", port=8000),
                initial_delay_seconds=5,
                period_seconds=5
            )
        )
        
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(
                labels={"app": deployment_name, "version": metadata.version}
            ),
            spec=client.V1PodSpec(containers=[container])
        )
        
        spec = client.V1DeploymentSpec(
            replicas=2,
            selector=client.V1LabelSelector(
                match_labels={"app": deployment_name}
            ),
            template=template
        )
        
        return client.V1Deployment(
            metadata=client.V1ObjectMeta(
                name=deployment_name,
                namespace=self.namespace,
                labels={"app": deployment_name, "version": metadata.version}
            ),
            spec=spec
        )
    
    def _create_service(self, metadata: ModelMetadata, deployment_name: str) -> client.V1Service:
        """Create Kubernetes service"""
        service = client.V1Service(
            metadata=client.V1ObjectMeta(
                name=deployment_name,
                namespace=self.namespace,
                labels={"app": deployment_name}
            ),
            spec=client.V1ServiceSpec(
                selector={"app": deployment_name},
                ports=[client.V1ServicePort(port=8000, target_port=8000)],
                type="ClusterIP"
            )
        )
        return service
    
    def rollback_model(self, metadata: ModelMetadata) -> str:
        """Rollback model to previous version"""
        # Get previous version
        previous_models = [
            m for m in self.registry.models.get(metadata.name, [])
            if m.created_at < metadata.created_at
        ]
        
        if not previous_models:
            raise ValueError("No previous version found for rollback")
        
        previous_model = max(previous_models, key=lambda m: m.created_at)
        
        # Deploy previous version
        return self.deploy_model(previous_model)

class ModelMonitor:
    """Model performance monitoring"""
    
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self.alert_thresholds = {
            "accuracy_drop": 0.05,
            "latency_p95": 1000,  # ms
            "error_rate": 0.01
        }
    
    def monitor_model_performance(self, model_name: str, version: str) -> dict[str, Any]:
        """Monitor model performance"""
        metadata = self.registry.get_model(model_name, version)
        if not metadata:
            raise ValueError(f"Model {model_name} version {version} not found")
        
        # Get current metrics from deployment
        current_metrics = self._get_deployment_metrics(model_name, version)
        
        # Compare with training metrics
        performance_drift = self._calculate_performance_drift(
            metadata.performance_metrics,
            current_metrics
        )
        
        # Check for alerts
        alerts = self._check_alerts(performance_drift)
        
        return {
            "model_name": model_name,
            "version": version,
            "training_metrics": metadata.performance_metrics,
            "current_metrics": current_metrics,
            "performance_drift": performance_drift,
            "alerts": alerts,
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_deployment_metrics(self, model_name: str, version: str) -> dict[str, float]:
        """Get metrics from deployed model"""
        # This would typically query Prometheus or other monitoring system
        # For now, return simulated metrics
        return {
            "accuracy": 0.85,
            "latency_p95": 800,
            "error_rate": 0.005,
            "throughput": 1000
        }
    
    def _calculate_performance_drift(self, training_metrics: dict[str, float], 
                                   current_metrics: dict[str, float]) -> dict[str, float]:
        """Calculate performance drift"""
        drift = {}
        for metric in training_metrics:
            if metric in current_metrics:
                drift[metric] = current_metrics[metric] - training_metrics[metric]
        return drift
    
    def _check_alerts(self, performance_drift: dict[str, float]) -> list[str]:
        """Check for performance alerts"""
        alerts = []
        
        if "accuracy" in performance_drift:
            if performance_drift["accuracy"] < -self.alert_thresholds["accuracy_drop"]:
                alerts.append(f"Accuracy dropped by {abs(performance_drift['accuracy']):.3f}")
        
        if "latency_p95" in performance_drift:
            if performance_drift["latency_p95"] > self.alert_thresholds["latency_p95"]:
                alerts.append(f"P95 latency is {performance_drift['latency_p95']}ms")
        
        if "error_rate" in performance_drift:
            if performance_drift["error_rate"] > self.alert_thresholds["error_rate"]:
                alerts.append(f"Error rate is {performance_drift['error_rate']:.3f}")
        
        return alerts

class MLOpsPipeline:
    """Complete ML Ops pipeline orchestrator"""
    
    def __init__(self):
        self.registry = ModelRegistry()
        self.deployer = ModelDeployer()
        self.monitor = ModelMonitor(self.registry)
    
    def run_training_pipeline(self, config: TrainingConfig) -> ModelMetadata:
        """Run complete training pipeline"""
        logger.info(f"Starting training pipeline for {config.model_name}")
        
        # Train model
        trainer = ModelTrainer(config, self.registry)
        metadata = trainer.train_model()
        
        # Deploy if performance meets threshold
        if metadata.performance_metrics.get("val_accuracy", 0) > 0.8:
            deployment_name = self.deployer.deploy_model(metadata)
            logger.info(f"Model deployed as {deployment_name}")
        else:
            logger.warning(f"Model performance below threshold, not deploying")
        
        return metadata
    
    def run_monitoring_pipeline(self, model_name: str, version: str) -> dict[str, Any]:
        """Run monitoring pipeline"""
        return self.monitor.monitor_model_performance(model_name, version)
    
    def run_retraining_pipeline(self, model_name: str, new_data_path: str) -> ModelMetadata:
        """Run retraining pipeline with new data"""
        # Get latest model
        latest_model = self.registry.get_latest_model(model_name)
        if not latest_model:
            raise ValueError(f"No model found for {model_name}")
        
        # Create new training config
        config = TrainingConfig(
            model_name=model_name,
            framework=latest_model.framework,
            hyperparameters=latest_model.hyperparameters,
            training_data_path=new_data_path
        )
        
        # Train new model
        trainer = ModelTrainer(config, self.registry)
        new_metadata = trainer.train_model()
        
        # Compare performance
        if (new_metadata.performance_metrics.get("val_accuracy", 0) > 
            latest_model.performance_metrics.get("val_accuracy", 0)):
            # Deploy new model
            self.deployer.deploy_model(new_metadata)
            logger.info(f"Retrained model deployed with improved performance")
        else:
            logger.info(f"Retrained model performance not improved, keeping current model")
        
        return new_metadata

# Global pipeline instance
ml_ops_pipeline = MLOpsPipeline()

# API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/ml-ops", tags=["ml-ops"])

class TrainingRequest(BaseModel):
    model_name: str
    framework: str
    hyperparameters: dict[str, Any]
    training_data_path: str

class MonitoringRequest(BaseModel):
    model_name: str
    version: str

@router.post("/train")
async def train_model(request: TrainingRequest):
    """Train a new model"""
    try:
        config = TrainingConfig(
            model_name=request.model_name,
            framework=request.framework,
            hyperparameters=request.hyperparameters,
            training_data_path=request.training_data_path
        )
        
        metadata = ml_ops_pipeline.run_training_pipeline(config)
        return asdict(metadata)
    except Exception as e:
        logger.error(f"Error training model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/monitor")
async def monitor_model(request: MonitoringRequest):
    """Monitor model performance"""
    try:
        results = ml_ops_pipeline.run_monitoring_pipeline(request.model_name, request.version)
        return results
    except Exception as e:
        logger.error(f"Error monitoring model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/retrain")
async def retrain_model(model_name: str, new_data_path: str):
    """Retrain an existing model with new data"""
    try:
        metadata = ml_ops_pipeline.run_retraining_pipeline(model_name, new_data_path)
        return asdict(metadata)
    except Exception as e:
        logger.error(f"Error retraining model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def list_models():
    """List all models"""
    try:
        return ml_ops_pipeline.registry.list_models()
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{model_name}")
async def get_model(model_name: str, version: str | None = None):
    """Get model details"""
    try:
        if version:
            metadata = ml_ops_pipeline.registry.get_model(model_name, version)
        else:
            metadata = ml_ops_pipeline.registry.get_latest_model(model_name)
        
        if not metadata:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return asdict(metadata)
    except Exception as e:
        logger.error(f"Error getting model: {e}")
        raise HTTPException(status_code=500, detail=str(e))
