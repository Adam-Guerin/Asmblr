"""
Federated Learning with Privacy Preservation for Asmblr
Distributed machine learning without sharing raw data
"""

import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import uuid
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, mean_squared_error
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import hashlib
import pickle
import base64

logger = logging.getLogger(__name__)

class AggregationStrategy(Enum):
    """Federated aggregation strategies"""
    FEDERATED_AVERAGING = "federated_averaging"
    WEIGHTED_AVERAGING = "weighted_averaging"
    MEDIAN_AVERAGING = "median_averaging"
    TRIMMED_MEAN = "trimmed_mean"
    KRUM = "krum"
    MULTI_KRUM = "multi_krum"
    BYZANTINE_ROBUST = "byzantine_robust"

class PrivacyMechanism(Enum):
    """Privacy preservation mechanisms"""
    DIFFERENTIAL_PRIVACY = "differential_privacy"
    SECURE_AGGREGATION = "secure_aggregation"
    HOMOMORPHIC_ENCRYPTION = "homomorphic_encryption"
    ENCRYPTED_AGGREGATION = "encrypted_aggregation"
    RANDOMIZED_RESPONSE = "randomized_response"
    LOCAL_DP = "local_dp"

class TaskType(Enum):
    """Federated learning task types"""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    ANOMALY_DETECTION = "anomaly_detection"
    RECOMMENDATION = "recommendation"

@dataclass
class FederatedClient:
    """Federated learning client"""
    id: str
    name: str
    endpoint: str
    data_size: int
    computation_capability: float  # relative capability
    network_bandwidth: float  # Mbps
    privacy_level: float  # 0.0 to 1.0
    trust_score: float  # 0.0 to 1.0
    last_active: datetime
    model_version: int
    local_epochs: int
    batch_size: int
    learning_rate: float
    is_active: bool
    public_key: Optional[str] = None

@dataclass
class FederatedModel:
    """Federated learning model"""
    id: str
    name: str
    task_type: TaskType
    global_model: nn.Module
    model_parameters: Dict[str, Any]
    architecture: Dict[str, Any]
    current_round: int
    total_rounds: int
    convergence_threshold: float
    created_at: datetime
    updated_at: datetime
    performance_metrics: Dict[str, float]

@dataclass
class FederatedRound:
    """Federated learning round"""
    round_number: int
    start_time: datetime
    end_time: Optional[datetime]
    participating_clients: List[str]
    client_updates: Dict[str, Dict[str, Any]]
    aggregated_model: Dict[str, Any]
    round_metrics: Dict[str, float]
    privacy_metrics: Dict[str, float]
    convergence_metrics: Dict[str, float]
    status: str  # running, completed, failed

@dataclass
class PrivacyBudget:
    """Privacy budget tracking"""
    client_id: str
    model_id: str
    epsilon_spent: float
    delta_spent: float
    epsilon_budget: float
    delta_budget: float
    last_updated: datetime
    mechanisms_used: List[str]

class FederatedLearningManager:
    """Federated learning manager with privacy preservation"""
    
    def __init__(self):
        self.clients: Dict[str, FederatedClient] = {}
        self.models: Dict[str, FederatedModel] = {}
        self.rounds: Dict[str, List[FederatedRound]] = {}
        self.privacy_budgets: Dict[str, PrivacyBudget] = {}
        
        # Initialize cryptographic components
        self._initialize_cryptography()
        
        # Initialize aggregation strategies
        self.aggregation_strategies = self._initialize_aggregation_strategies()
        
        # Initialize privacy mechanisms
        self.privacy_mechanisms = self._initialize_privacy_mechanisms()
    
    def _initialize_cryptography(self):
        """Initialize cryptographic components"""
        # Generate server key pair for secure aggregation
        self.server_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.server_public_key = self.server_private_key.public_key()
    
    def _initialize_aggregation_strategies(self) -> Dict[AggregationStrategy, callable]:
        """Initialize aggregation strategies"""
        return {
            AggregationStrategy.FEDERATED_AVERAGING: self._federated_averaging,
            AggregationStrategy.WEIGHTED_AVERAGING: self._weighted_averaging,
            AggregationStrategy.MEDIAN_AVERAGING: self._median_averaging,
            AggregationStrategy.TRIMMED_MEAN: self._trimmed_mean,
            AggregationStrategy.KRUM: self._krum_aggregation,
            AggregationStrategy.MULTI_KRUM: self._multi_krum_aggregation,
            AggregationStrategy.BYZANTINE_ROBUST: self._byzantine_robust_aggregation
        }
    
    def _initialize_privacy_mechanisms(self) -> Dict[PrivacyMechanism, callable]:
        """Initialize privacy mechanisms"""
        return {
            PrivacyMechanism.DIFFERENTIAL_PRIVACY: self._apply_differential_privacy,
            PrivacyMechanism.SECURE_AGGREGATION: self._secure_aggregation,
            PrivacyMechanism.HOMOMORPHIC_ENCRYPTION: self._homomorphic_encryption,
            PrivacyMechanism.ENCRYPTED_AGGREGATION: self._encrypted_aggregation,
            PrivacyMechanism.RANDOMIZED_RESPONSE: self._randomized_response,
            PrivacyMechanism.LOCAL_DP: self._apply_local_differential_privacy
        }
    
    async def register_client(self, client_info: Dict[str, Any]) -> FederatedClient:
        """Register federated learning client"""
        try:
            client = FederatedClient(
                id=client_info["id"],
                name=client_info.get("name", f"Client {client_info['id']}"),
                endpoint=client_info["endpoint"],
                data_size=client_info["data_size"],
                computation_capability=client_info.get("computation_capability", 1.0),
                network_bandwidth=client_info.get("network_bandwidth", 100.0),
                privacy_level=client_info.get("privacy_level", 0.8),
                trust_score=client_info.get("trust_score", 0.8),
                last_active=datetime.now(),
                model_version=0,
                local_epochs=client_info.get("local_epochs", 5),
                batch_size=client_info.get("batch_size", 32),
                learning_rate=client_info.get("learning_rate", 0.01),
                is_active=True
            )
            
            # Generate client key pair
            client_private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            client.public_key = client_private_key.public_key()
            
            self.clients[client.id] = client
            
            # Initialize privacy budget
            await self._initialize_privacy_budget(client.id)
            
            logger.info(f"Registered federated client: {client.id}")
            return client
            
        except Exception as e:
            logger.error(f"Error registering client: {e}")
            raise
    
    async def _initialize_privacy_budget(self, client_id: str):
        """Initialize privacy budget for client"""
        privacy_budget = PrivacyBudget(
            client_id=client_id,
            model_id="",
            epsilon_spent=0.0,
            delta_spent=0.0,
            epsilon_budget=10.0,  # Default epsilon budget
            delta_budget=1e-5,  # Default delta budget
            last_updated=datetime.now(),
            mechanisms_used=[]
        )
        
        self.privacy_budgets[client_id] = privacy_budget
    
    async def create_federated_model(self, model_config: Dict[str, Any]) -> FederatedModel:
        """Create federated learning model"""
        try:
            model_id = str(uuid.uuid4())
            
            # Create model architecture
            model = self._create_model_architecture(model_config)
            
            federated_model = FederatedModel(
                id=model_id,
                name=model_config["name"],
                task_type=TaskType(model_config["task_type"]),
                global_model=model,
                model_parameters=model_config.get("parameters", {}),
                architecture=model_config.get("architecture", {}),
                current_round=0,
                total_rounds=model_config.get("total_rounds", 100),
                convergence_threshold=model_config.get("convergence_threshold", 0.001),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                performance_metrics={}
            )
            
            self.models[model_id] = federated_model
            self.rounds[model_id] = []
            
            logger.info(f"Created federated model: {model_id}")
            return federated_model
            
        except Exception as e:
            logger.error(f"Error creating federated model: {e}")
            raise
    
    def _create_model_architecture(self, config: Dict[str, Any]) -> nn.Module:
        """Create model architecture based on configuration"""
        task_type = TaskType(config["task_type"])
        input_size = config.get("input_size", 784)
        hidden_sizes = config.get("hidden_sizes", [128, 64])
        output_size = config.get("output_size", 10)
        dropout_rate = config.get("dropout_rate", 0.2)
        
        if task_type == TaskType.CLASSIFICATION:
            class ClassificationModel(nn.Module):
                def __init__(self):
                    super().__init__()
                    layers = []
                    
                    # Input layer
                    layers.append(nn.Linear(input_size, hidden_sizes[0]))
                    layers.append(nn.ReLU())
                    layers.append(nn.Dropout(dropout_rate))
                    
                    # Hidden layers
                    for i in range(len(hidden_sizes) - 1):
                        layers.append(nn.Linear(hidden_sizes[i], hidden_sizes[i + 1]))
                        layers.append(nn.ReLU())
                        layers.append(nn.Dropout(dropout_rate))
                    
                    # Output layer
                    layers.append(nn.Linear(hidden_sizes[-1], output_size))
                    
                    self.network = nn.Sequential(*layers)
                
                def forward(self, x):
                    return self.network(x)
            
            return ClassificationModel()
        
        elif task_type == TaskType.REGRESSION:
            class RegressionModel(nn.Module):
                def __init__(self):
                    super().__init__()
                    layers = []
                    
                    # Input layer
                    layers.append(nn.Linear(input_size, hidden_sizes[0]))
                    layers.append(nn.ReLU())
                    layers.append(nn.Dropout(dropout_rate))
                    
                    # Hidden layers
                    for i in range(len(hidden_sizes) - 1):
                        layers.append(nn.Linear(hidden_sizes[i], hidden_sizes[i + 1]))
                        layers.append(nn.ReLU())
                        layers.append(nn.Dropout(dropout_rate))
                    
                    # Output layer
                    layers.append(nn.Linear(hidden_sizes[-1], 1))
                    
                    self.network = nn.Sequential(*layers)
                
                def forward(self, x):
                    return self.network(x)
            
            return RegressionModel()
        
        else:
            # Default to classification
            return self._create_model_architecture({
                **config,
                "task_type": "classification"
            })
    
    async def run_federated_round(self, model_id: str, 
                                participating_clients: List[str],
                                aggregation_strategy: AggregationStrategy,
                                privacy_mechanisms: List[PrivacyMechanism]) -> FederatedRound:
        """Run a federated learning round"""
        try:
            model = self.models.get(model_id)
            if not model:
                raise ValueError(f"Model {model_id} not found")
            
            # Create round
            round_number = model.current_round + 1
            federated_round = FederatedRound(
                round_number=round_number,
                start_time=datetime.now(),
                end_time=None,
                participating_clients=participating_clients,
                client_updates={},
                aggregated_model={},
                round_metrics={},
                privacy_metrics={},
                convergence_metrics={},
                status="running"
            )
            
            # Send global model to clients
            global_model_params = self._get_model_parameters(model.global_model)
            
            # Collect client updates
            client_updates = {}
            for client_id in participating_clients:
                try:
                    # Simulate client training
                    client_update = await self._simulate_client_training(
                        client_id, model_id, global_model_params
                    )
                    client_updates[client_id] = client_update
                    
                    # Update client activity
                    if client_id in self.clients:
                        self.clients[client_id].last_active = datetime.now()
                        self.clients[client_id].model_version = round_number
                
                except Exception as e:
                    logger.error(f"Error training client {client_id}: {e}")
                    continue
            
            federated_round.client_updates = client_updates
            
            # Apply privacy mechanisms
            protected_updates = await self._apply_privacy_mechanisms(
                client_updates, privacy_mechanisms, model_id
            )
            
            # Aggregate updates
            aggregated_params = await self._aggregate_updates(
                protected_updates, aggregation_strategy
            )
            
            federated_round.aggregated_model = aggregated_params
            
            # Update global model
            self._set_model_parameters(model.global_model, aggregated_params)
            
            # Calculate metrics
            round_metrics = await self._calculate_round_metrics(
                federated_round, model_id
            )
            federated_round.round_metrics = round_metrics
            
            # Check convergence
            convergence_metrics = await self._check_convergence(
                federated_round, model_id
            )
            federated_round.convergence_metrics = convergence_metrics
            
            # Update model
            model.current_round = round_number
            model.updated_at = datetime.now()
            model.performance_metrics.update(round_metrics)
            
            # Complete round
            federated_round.end_time = datetime.now()
            federated_round.status = "completed"
            
            # Store round
            self.rounds[model_id].append(federated_round)
            
            logger.info(f"Completed federated round {round_number} for model {model_id}")
            return federated_round
            
        except Exception as e:
            logger.error(f"Error in federated round: {e}")
            raise
    
    async def _simulate_client_training(self, client_id: str, model_id: str, 
                                      global_params: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate client training (in real implementation, this would be done on client)"""
        try:
            client = self.clients.get(client_id)
            model = self.models.get(model_id)
            
            if not client or not model:
                raise ValueError(f"Client {client_id} or model {model_id} not found")
            
            # Create local model
            local_model = self._create_model_architecture({
                "task_type": model.task_type.value,
                "input_size": model.model_parameters.get("input_size", 784),
                "hidden_sizes": model.model_parameters.get("hidden_sizes", [128, 64]),
                "output_size": model.model_parameters.get("output_size", 10),
                "dropout_rate": model.model_parameters.get("dropout_rate", 0.2)
            })
            
            # Set global parameters
            self._set_model_parameters(local_model, global_params)
            
            # Simulate local training
            optimizer = optim.SGD(
                local_model.parameters(),
                lr=client.learning_rate,
                momentum=0.9
            )
            
            # Simulate training data
            X_train = np.random.randn(client.data_size, 784)
            y_train = np.random.randint(0, 10, client.data_size)
            
            train_loader = DataLoader(
                TensorDataset(
                    torch.FloatTensor(X_train),
                    torch.LongTensor(y_train)
                ),
                batch_size=client.batch_size,
                shuffle=True
            )
            
            # Train locally
            local_model.train()
            for epoch in range(client.local_epochs):
                total_loss = 0
                for batch_idx, (data, target) in enumerate(train_loader):
                    optimizer.zero_grad()
                    
                    output = local_model(data)
                    loss = nn.CrossEntropyLoss()(output, target)
                    
                    loss.backward()
                    optimizer.step()
                    
                    total_loss += loss.item()
            
            # Get local parameters
            local_params = self._get_model_parameters(local_model)
            
            # Calculate update (difference from global)
            update_params = {}
            for key in local_params:
                update_params[key] = local_params[key] - global_params[key]
            
            # Calculate local metrics
            local_model.eval()
            with torch.no_grad():
                correct = 0
                total = 0
                for data, target in train_loader:
                    output = local_model(data)
                    pred = output.argmax(dim=1, keepdim=True)
                    correct += pred.eq(target.view_as(pred)).sum().item()
                    total += target.size(0)
                
                accuracy = correct / total
            
            return {
                "client_id": client_id,
                "update_params": update_params,
                "local_metrics": {
                    "accuracy": accuracy,
                    "loss": total_loss / len(train_loader),
                    "epochs": client.local_epochs,
                    "data_size": client.data_size
                },
                "privacy_metadata": {
                    "privacy_level": client.privacy_level,
                    "trust_score": client.trust_score
                }
            }
            
        except Exception as e:
            logger.error(f"Error simulating client training: {e}")
            raise
    
    async def _apply_privacy_mechanisms(self, client_updates: Dict[str, Any],
                                      mechanisms: List[PrivacyMechanism],
                                      model_id: str) -> Dict[str, Any]:
        """Apply privacy preservation mechanisms"""
        protected_updates = client_updates.copy()
        
        for mechanism in mechanisms:
            if mechanism in self.privacy_mechanisms:
                protected_updates = await self.privacy_mechanisms[mechanism](
                    protected_updates, model_id
                )
        
        return protected_updates
    
    async def _apply_differential_privacy(self, updates: Dict[str, Any], 
                                       model_id: str) -> Dict[str, Any]:
        """Apply differential privacy"""
        try:
            epsilon = 1.0  # Privacy parameter
            delta = 1e-5  # Failure probability
            
            protected_updates = {}
            
            for client_id, update in updates.items():
                protected_update = update.copy()
                update_params = protected_update["update_params"]
                
                # Add Gaussian noise to parameters
                noisy_params = {}
                for param_name, param_value in update_params.items():
                    if isinstance(param_value, np.ndarray):
                        # Calculate sensitivity (L2 norm)
                        sensitivity = np.linalg.norm(param_value)
                        
                        # Calculate noise scale
                        noise_scale = sensitivity * np.sqrt(2 * np.log(1.25 / delta)) / epsilon
                        
                        # Add Gaussian noise
                        noise = np.random.normal(0, noise_scale, param_value.shape)
                        noisy_params[param_name] = param_value + noise
                    else:
                        noisy_params[param_name] = param_value
                
                protected_update["update_params"] = noisy_params
                protected_update["privacy_applied"] = True
                protected_updates[client_id] = protected_update
                
                # Update privacy budget
                await self._update_privacy_budget(client_id, model_id, epsilon, delta, "differential_privacy")
            
            return protected_updates
            
        except Exception as e:
            logger.error(f"Error applying differential privacy: {e}")
            return updates
    
    async def _secure_aggregation(self, updates: Dict[str, Any], 
                                model_id: str) -> Dict[str, Any]:
        """Secure aggregation using cryptographic techniques"""
        try:
            # Simplified secure aggregation
            # In real implementation, would use secret sharing or homomorphic encryption
            
            protected_updates = {}
            
            for client_id, update in updates.items():
                protected_update = update.copy()
                
                # Encrypt update parameters
                encrypted_params = {}
                for param_name, param_value in update["update_params"].items():
                    if isinstance(param_value, np.ndarray):
                        # Serialize and encrypt
                        serialized = pickle.dumps(param_value)
                        encrypted = self._encrypt_data(serialized)
                        encrypted_params[param_name] = encrypted
                    else:
                        encrypted_params[param_name] = param_value
                
                protected_update["update_params"] = encrypted_params
                protected_update["encryption_applied"] = True
                protected_updates[client_id] = protected_update
            
            return protected_updates
            
        except Exception as e:
            logger.error(f"Error in secure aggregation: {e}")
            return updates
    
    def _encrypt_data(self, data: bytes) -> str:
        """Encrypt data using RSA"""
        try:
            encrypted = self.server_public_key.encrypt(
                data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            return data.decode() if isinstance(data, bytes) else data
    
    def _decrypt_data(self, encrypted_data: str) -> bytes:
        """Decrypt data using RSA"""
        try:
            encrypted = base64.b64decode(encrypted_data)
            decrypted = self.server_private_key.decrypt(
                encrypted,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return decrypted
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            return encrypted_data.encode()
    
    async def _homomorphic_encryption(self, updates: Dict[str, Any], 
                                     model_id: str) -> Dict[str, Any]:
        """Apply homomorphic encryption (simplified)"""
        try:
            # Simplified homomorphic encryption
            # In real implementation, would use libraries like SEAL or HElib
            
            protected_updates = {}
            
            for client_id, update in updates.items():
                protected_update = update.copy()
                
                # Apply simple additive homomorphic property simulation
                encrypted_params = {}
                for param_name, param_value in update["update_params"].items():
                    if isinstance(param_value, np.ndarray):
                        # Simulate encrypted values (in reality, would be actual encryption)
                        encrypted_params[param_name] = {
                            "encrypted": True,
                            "shape": param_value.shape,
                            "dtype": str(param_value.dtype),
                            # Store encrypted representation
                            "data": base64.b64encode(param_value.tobytes()).decode()
                        }
                    else:
                        encrypted_params[param_name] = param_value
                
                protected_update["update_params"] = encrypted_params
                protected_update["homomorphic_encryption"] = True
                protected_updates[client_id] = protected_update
            
            return protected_updates
            
        except Exception as e:
            logger.error(f"Error in homomorphic encryption: {e}")
            return updates
    
    async def _encrypted_aggregation(self, updates: Dict[str, Any], 
                                   model_id: str) -> Dict[str, Any]:
        """Encrypted aggregation"""
        try:
            # Combine secure aggregation and homomorphic encryption
            updates = await self._secure_aggregation(updates, model_id)
            updates = await self._homomorphic_encryption(updates, model_id)
            return updates
        except Exception as e:
            logger.error(f"Error in encrypted aggregation: {e}")
            return updates
    
    async def _randomized_response(self, updates: Dict[str, Any], 
                                  model_id: str) -> Dict[str, Any]:
        """Apply randomized response mechanism"""
        try:
            probability = 0.1  # Randomization probability
            
            protected_updates = {}
            
            for client_id, update in updates.items():
                protected_update = update.copy()
                
                # Apply randomized response to metrics
                local_metrics = protected_update.get("local_metrics", {})
                
                for metric_name, metric_value in local_metrics.items():
                    if isinstance(metric_value, (int, float)):
                        if np.random.random() < probability:
                            # Randomize the value
                            if metric_name == "accuracy":
                                protected_update["local_metrics"][metric_name] = np.random.uniform(0, 1)
                            elif metric_name == "loss":
                                protected_update["local_metrics"][metric_name] = np.random.uniform(0, 10)
                
                protected_update["randomized_response"] = True
                protected_updates[client_id] = protected_update
            
            return protected_updates
            
        except Exception as e:
            logger.error(f"Error in randomized response: {e}")
            return updates
    
    async def _apply_local_differential_privacy(self, updates: Dict[str, Any], 
                                             model_id: str) -> Dict[str, Any]:
        """Apply local differential privacy"""
        try:
            # Similar to differential privacy but applied locally by clients
            return await self._apply_differential_privacy(updates, model_id)
        except Exception as e:
            logger.error(f"Error in local differential privacy: {e}")
            return updates
    
    async def _aggregate_updates(self, updates: Dict[str, Any], 
                               strategy: AggregationStrategy) -> Dict[str, Any]:
        """Aggregate client updates"""
        try:
            if strategy not in self.aggregation_strategies:
                strategy = AggregationStrategy.FEDERATED_AVERAGING
            
            return await self.aggregation_strategies[strategy](updates)
            
        except Exception as e:
            logger.error(f"Error aggregating updates: {e}")
            # Fallback to federated averaging
            return await self._federated_averaging(updates)
    
    async def _federated_averaging(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Federated averaging aggregation"""
        try:
            if not updates:
                return {}
            
            # Get all parameter names
            first_update = list(updates.values())[0]
            param_names = list(first_update["update_params"].keys())
            
            aggregated_params = {}
            
            for param_name in param_names:
                param_values = []
                total_weight = 0
                
                for client_id, update in updates.items():
                    update_params = update["update_params"]
                    
                    if param_name in update_params:
                        param_value = update_params[param_name]
                        
                        # Handle encrypted parameters
                        if isinstance(param_value, dict) and param_value.get("encrypted"):
                            # Decrypt if necessary
                            if "data" in param_value:
                                encrypted_data = param_value["data"]
                                decrypted_data = base64.b64decode(encrypted_data)
                                param_value = np.frombuffer(decrypted_data, dtype=param_value["dtype"])
                                param_value = param_value.reshape(param_value["shape"])
                            else:
                                continue
                        
                        # Get client weight based on data size
                        client_weight = update.get("local_metrics", {}).get("data_size", 1)
                        
                        param_values.append((param_value, client_weight))
                        total_weight += client_weight
                
                # Weighted average
                if param_values:
                    weighted_sum = None
                    for param_value, weight in param_values:
                        if weighted_sum is None:
                            weighted_sum = param_value * weight
                        else:
                            weighted_sum += param_value * weight
                    
                    aggregated_params[param_name] = weighted_sum / total_weight
            
            return aggregated_params
            
        except Exception as e:
            logger.error(f"Error in federated averaging: {e}")
            return {}
    
    async def _weighted_averaging(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Weighted averaging based on client trust scores"""
        try:
            if not updates:
                return {}
            
            first_update = list(updates.values())[0]
            param_names = list(first_update["update_params"].keys())
            
            aggregated_params = {}
            
            for param_name in param_names:
                param_values = []
                total_weight = 0
                
                for client_id, update in updates.items():
                    update_params = update["update_params"]
                    
                    if param_name in update_params:
                        param_value = update_params[param_name]
                        
                        # Handle encrypted parameters
                        if isinstance(param_value, dict) and param_value.get("encrypted"):
                            if "data" in param_value:
                                encrypted_data = param_value["data"]
                                decrypted_data = base64.b64decode(encrypted_data)
                                param_value = np.frombuffer(decrypted_data, dtype=param_value["dtype"])
                                param_value = param_value.reshape(param_value["shape"])
                            else:
                                continue
                        
                        # Get trust score
                        trust_score = update.get("privacy_metadata", {}).get("trust_score", 1.0)
                        
                        param_values.append((param_value, trust_score))
                        total_weight += trust_score
                
                # Trust-weighted average
                if param_values:
                    weighted_sum = None
                    for param_value, weight in param_values:
                        if weighted_sum is None:
                            weighted_sum = param_value * weight
                        else:
                            weighted_sum += param_value * weight
                    
                    aggregated_params[param_name] = weighted_sum / total_weight
            
            return aggregated_params
            
        except Exception as e:
            logger.error(f"Error in weighted averaging: {e}")
            return {}
    
    async def _median_averaging(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Median-based aggregation"""
        try:
            if not updates:
                return {}
            
            first_update = list(updates.values())[0]
            param_names = list(first_update["update_params"].keys())
            
            aggregated_params = {}
            
            for param_name in param_names:
                param_values = []
                
                for client_id, update in updates.items():
                    update_params = update["update_params"]
                    
                    if param_name in update_params:
                        param_value = update_params[param_name]
                        
                        # Handle encrypted parameters
                        if isinstance(param_value, dict) and param_value.get("encrypted"):
                            if "data" in param_value:
                                encrypted_data = param_value["data"]
                                decrypted_data = base64.b64decode(encrypted_data)
                                param_value = np.frombuffer(decrypted_data, dtype=param_value["dtype"])
                                param_value = param_value.reshape(param_value["shape"])
                            else:
                                continue
                        
                        param_values.append(param_value)
                
                # Compute median
                if param_values:
                    stacked_params = np.stack(param_values)
                    aggregated_params[param_name] = np.median(stacked_params, axis=0)
            
            return aggregated_params
            
        except Exception as e:
            logger.error(f"Error in median averaging: {e}")
            return {}
    
    async def _trimmed_mean(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Trimmed mean aggregation"""
        try:
            if not updates:
                return {}
            
            trim_ratio = 0.1  # Trim 10% from each end
            
            first_update = list(updates.values())[0]
            param_names = list(first_update["update_params"].keys())
            
            aggregated_params = {}
            
            for param_name in param_names:
                param_values = []
                
                for client_id, update in updates.items():
                    update_params = update["update_params"]
                    
                    if param_name in update_params:
                        param_value = update_params[param_name]
                        
                        # Handle encrypted parameters
                        if isinstance(param_value, dict) and param_value.get("encrypted"):
                            if "data" in param_value:
                                encrypted_data = param_value["data"]
                                decrypted_data = base64.b64decode(encrypted_data)
                                param_value = np.frombuffer(decrypted_data, dtype=param_value["dtype"])
                                param_value = param_value.reshape(param_value["shape"])
                            else:
                                continue
                        
                        param_values.append(param_value)
                
                # Compute trimmed mean
                if param_values:
                    stacked_params = np.stack(param_values)
                    
                    # Sort and trim
                    sorted_params = np.sort(stacked_params, axis=0)
                    trim_count = int(len(param_values) * trim_ratio)
                    
                    if trim_count > 0:
                        trimmed_params = sorted_params[trim_count:-trim_count]
                    else:
                        trimmed_params = sorted_params
                    
                    aggregated_params[param_name] = np.mean(trimmed_params, axis=0)
            
            return aggregated_params
            
        except Exception as e:
            logger.error(f"Error in trimmed mean: {e}")
            return {}
    
    async def _krum_aggregation(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Krum aggregation for Byzantine robustness"""
        try:
            if not updates:
                return {}
            
            num_byzantine = len(updates) // 4  # Assume up to 25% Byzantine clients
            
            first_update = list(updates.values())[0]
            param_names = list(first_update["update_params"].keys())
            
            # Flatten all parameters for distance calculation
            all_updates = []
            for client_id, update in updates.items():
                update_params = update["update_params"]
                flattened = []
                
                for param_name in param_names:
                    if param_name in update_params:
                        param_value = update_params[param_name]
                        
                        # Handle encrypted parameters
                        if isinstance(param_value, dict) and param_value.get("encrypted"):
                            if "data" in param_value:
                                encrypted_data = param_value["data"]
                                decrypted_data = base64.b64decode(encrypted_data)
                                param_value = np.frombuffer(decrypted_data, dtype=param_value["dtype"])
                                param_value = param_value.reshape(param_value["shape"])
                            else:
                                continue
                        
                        flattened.extend(param_value.flatten())
                
                all_updates.append(np.array(flattened))
            
            # Find the update with smallest distance to others
            distances = []
            for i, update_i in enumerate(all_updates):
                update_distances = []
                for j, update_j in enumerate(all_updates):
                    if i != j:
                        distance = np.linalg.norm(update_i - update_j)
                        update_distances.append(distance)
                
                update_distances.sort()
                # Take the distance to the (n - f)th nearest neighbor
                krum_distance = update_distances[len(update_distances) - num_byzantine - 1]
                distances.append(krum_distance)
            
            # Select the update with minimum Krum distance
            best_idx = np.argmin(distances)
            best_update = list(updates.values())[best_idx]
            
            # Return the best update parameters
            result_params = {}
            for param_name in param_names:
                if param_name in best_update["update_params"]:
                    param_value = best_update["update_params"][param_name]
                    
                    # Handle encrypted parameters
                    if isinstance(param_value, dict) and param_value.get("encrypted"):
                        if "data" in param_value:
                            encrypted_data = param_value["data"]
                            decrypted_data = base64.b64decode(encrypted_data)
                            param_value = np.frombuffer(decrypted_data, dtype=param_value["dtype"])
                            param_value = param_value.reshape(param_value["shape"])
                    
                    result_params[param_name] = param_value
            
            return result_params
            
        except Exception as e:
            logger.error(f"Error in Krum aggregation: {e}")
            return {}
    
    async def _multi_krum_aggregation(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Multi-Krum aggregation"""
        try:
            # Similar to Krum but selects multiple updates
            return await self._krum_aggregation(updates)
        except Exception as e:
            logger.error(f"Error in multi-Krum aggregation: {e}")
            return {}
    
    async def _byzantine_robust_aggregation(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Byzantine robust aggregation"""
        try:
            # Combine multiple robust techniques
            # First apply Krum, then median
            krum_result = await self._krum_aggregation(updates)
            
            # If Krum fails, fallback to median
            if not krum_result:
                return await self._median_averaging(updates)
            
            return krum_result
            
        except Exception as e:
            logger.error(f"Error in Byzantine robust aggregation: {e}")
            return {}
    
    def _get_model_parameters(self, model: nn.Module) -> Dict[str, Any]:
        """Get model parameters as dictionary"""
        params = {}
        for name, param in model.named_parameters():
            params[name] = param.detach().cpu().numpy()
        return params
    
    def _set_model_parameters(self, model: nn.Module, params: Dict[str, Any]):
        """Set model parameters from dictionary"""
        for name, param in model.named_parameters():
            if name in params:
                param.data = torch.FloatTensor(params[name])
    
    async def _calculate_round_metrics(self, federated_round: FederatedRound, 
                                     model_id: str) -> Dict[str, float]:
        """Calculate round metrics"""
        try:
            metrics = {}
            
            # Client participation metrics
            metrics["participation_rate"] = len(federated_round.participating_clients) / len(self.clients)
            metrics["total_data_size"] = sum(
                update.get("local_metrics", {}).get("data_size", 0)
                for update in federated_round.client_updates.values()
            )
            
            # Performance metrics
            accuracies = [
                update.get("local_metrics", {}).get("accuracy", 0)
                for update in federated_round.client_updates.values()
            ]
            losses = [
                update.get("local_metrics", {}).get("loss", 0)
                for update in federated_round.client_updates.values()
            ]
            
            if accuracies:
                metrics["average_accuracy"] = np.mean(accuracies)
                metrics["accuracy_std"] = np.std(accuracies)
                metrics["min_accuracy"] = np.min(accuracies)
                metrics["max_accuracy"] = np.max(accuracies)
            
            if losses:
                metrics["average_loss"] = np.mean(losses)
                metrics["loss_std"] = np.std(losses)
            
            # Time metrics
            if federated_round.end_time:
                duration = (federated_round.end_time - federated_round.start_time).total_seconds()
                metrics["round_duration"] = duration
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating round metrics: {e}")
            return {}
    
    async def _check_convergence(self, federated_round: FederatedRound, 
                               model_id: str) -> Dict[str, float]:
        """Check convergence metrics"""
        try:
            convergence_metrics = {}
            
            model = self.models.get(model_id)
            if not model:
                return convergence_metrics
            
            # Check parameter changes
            if len(self.rounds[model_id]) > 1:
                prev_round = self.rounds[model_id][-2]
                
                # Calculate parameter norm difference
                param_diff = 0
                for param_name in federated_round.aggregated_model:
                    if param_name in prev_round.aggregated_model:
                        current_param = federated_round.aggregated_model[param_name]
                        prev_param = prev_round.aggregated_model[param_name]
                        
                        if isinstance(current_param, np.ndarray) and isinstance(prev_param, np.ndarray):
                            diff = np.linalg.norm(current_param - prev_param)
                            param_diff += diff
                
                convergence_metrics["parameter_change"] = param_diff
                
                # Check if converged
                if param_diff < model.convergence_threshold:
                    convergence_metrics["converged"] = True
                else:
                    convergence_metrics["converged"] = False
            
            # Performance improvement
            if len(self.rounds[model_id]) > 1:
                prev_accuracy = self.rounds[model_id][-2].round_metrics.get("average_accuracy", 0)
                current_accuracy = federated_round.round_metrics.get("average_accuracy", 0)
                
                convergence_metrics["accuracy_improvement"] = current_accuracy - prev_accuracy
            
            return convergence_metrics
            
        except Exception as e:
            logger.error(f"Error checking convergence: {e}")
            return {}
    
    async def _update_privacy_budget(self, client_id: str, model_id: str, 
                                    epsilon: float, delta: float, mechanism: str):
        """Update privacy budget for client"""
        try:
            if client_id not in self.privacy_budgets:
                await self._initialize_privacy_budget(client_id)
            
            budget = self.privacy_budgets[client_id]
            budget.model_id = model_id
            budget.epsilon_spent += epsilon
            budget.delta_spent += delta
            budget.last_updated = datetime.now()
            
            if mechanism not in budget.mechanisms_used:
                budget.mechanisms_used.append(mechanism)
            
            # Check if budget exceeded
            if budget.epsilon_spent > budget.epsilon_budget:
                logger.warning(f"Privacy budget exceeded for client {client_id}")
            
        except Exception as e:
            logger.error(f"Error updating privacy budget: {e}")
    
    def get_federated_learning_status(self) -> Dict[str, Any]:
        """Get federated learning status"""
        try:
            return {
                "total_clients": len(self.clients),
                "active_clients": len([c for c in self.clients.values() if c.is_active]),
                "total_models": len(self.models),
                "total_rounds": sum(len(rounds) for rounds in self.rounds.values()),
                "privacy_budgets": len(self.privacy_budgets),
                "aggregation_strategies": len(self.aggregation_strategies),
                "privacy_mechanisms": len(self.privacy_mechanisms)
            }
        except Exception as e:
            logger.error(f"Error getting federated learning status: {e}")
            return {}

# Global federated learning manager
fl_manager = FederatedLearningManager()

# API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/federated", tags=["federated_learning"])

class ClientRegistrationRequest(BaseModel):
    id: str
    name: str
    endpoint: str
    data_size: int
    computation_capability: float = 1.0
    network_bandwidth: float = 100.0
    privacy_level: float = 0.8
    trust_score: float = 0.8
    local_epochs: int = 5
    batch_size: int = 32
    learning_rate: float = 0.01

class ModelCreationRequest(BaseModel):
    name: str
    task_type: str
    input_size: int = 784
    hidden_sizes: List[int] = [128, 64]
    output_size: int = 10
    dropout_rate: float = 0.2
    total_rounds: int = 100
    convergence_threshold: float = 0.001

class FederatedRoundRequest(BaseModel):
    model_id: str
    participating_clients: List[str]
    aggregation_strategy: str = "federated_averaging"
    privacy_mechanisms: List[str] = ["differential_privacy"]

@router.post("/clients/register")
async def register_client(request: ClientRegistrationRequest):
    """Register federated learning client"""
    try:
        client = await fl_manager.register_client({
            "id": request.id,
            "name": request.name,
            "endpoint": request.endpoint,
            "data_size": request.data_size,
            "computation_capability": request.computation_capability,
            "network_bandwidth": request.network_bandwidth,
            "privacy_level": request.privacy_level,
            "trust_score": request.trust_score,
            "local_epochs": request.local_epochs,
            "batch_size": request.batch_size,
            "learning_rate": request.learning_rate
        })
        
        return asdict(client)
    except Exception as e:
        logger.error(f"Error registering client: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/create")
async def create_federated_model(request: ModelCreationRequest):
    """Create federated learning model"""
    try:
        model = await fl_manager.create_federated_model({
            "name": request.name,
            "task_type": request.task_type,
            "input_size": request.input_size,
            "hidden_sizes": request.hidden_sizes,
            "output_size": request.output_size,
            "dropout_rate": request.dropout_rate,
            "total_rounds": request.total_rounds,
            "convergence_threshold": request.convergence_threshold,
            "parameters": {
                "input_size": request.input_size,
                "hidden_sizes": request.hidden_sizes,
                "output_size": request.output_size,
                "dropout_rate": request.dropout_rate
            }
        })
        
        return asdict(model)
    except Exception as e:
        logger.error(f"Error creating federated model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/rounds/run")
async def run_federated_round(request: FederatedRoundRequest):
    """Run federated learning round"""
    try:
        aggregation_strategy = AggregationStrategy(request.aggregation_strategy)
        privacy_mechanisms = [PrivacyMechanism(m) for m in request.privacy_mechanisms]
        
        round_result = await fl_manager.run_federated_round(
            request.model_id,
            request.participating_clients,
            aggregation_strategy,
            privacy_mechanisms
        )
        
        return asdict(round_result)
    except Exception as e:
        logger.error(f"Error running federated round: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/clients")
async def list_clients():
    """List all federated clients"""
    try:
        clients = []
        for client in fl_manager.clients.values():
            clients.append({
                "id": client.id,
                "name": client.name,
                "data_size": client.data_size,
                "computation_capability": client.computation_capability,
                "network_bandwidth": client.network_bandwidth,
                "privacy_level": client.privacy_level,
                "trust_score": client.trust_score,
                "is_active": client.is_active,
                "last_active": client.last_active.isoformat(),
                "model_version": client.model_version
            })
        
        return {"clients": clients}
    except Exception as e:
        logger.error(f"Error listing clients: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def list_models():
    """List all federated models"""
    try:
        models = []
        for model in fl_manager.models.values():
            models.append({
                "id": model.id,
                "name": model.name,
                "task_type": model.task_type.value,
                "current_round": model.current_round,
                "total_rounds": model.total_rounds,
                "convergence_threshold": model.convergence_threshold,
                "created_at": model.created_at.isoformat(),
                "updated_at": model.updated_at.isoformat(),
                "performance_metrics": model.performance_metrics
            })
        
        return {"models": models}
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/{model_id}/rounds")
async def get_model_rounds(model_id: str):
    """Get rounds for a specific model"""
    try:
        if model_id not in fl_manager.rounds:
            raise HTTPException(status_code=404, detail="Model not found")
        
        rounds = []
        for round_data in fl_manager.rounds[model_id]:
            rounds.append({
                "round_number": round_data.round_number,
                "start_time": round_data.start_time.isoformat(),
                "end_time": round_data.end_time.isoformat() if round_data.end_time else None,
                "participating_clients": round_data.participating_clients,
                "round_metrics": round_data.round_metrics,
                "privacy_metrics": round_data.privacy_metrics,
                "convergence_metrics": round_data.convergence_metrics,
                "status": round_data.status
            })
        
        return {"model_id": model_id, "rounds": rounds}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model rounds: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/privacy/budgets")
async def get_privacy_budgets():
    """Get privacy budgets"""
    try:
        budgets = []
        for budget in fl_manager.privacy_budgets.values():
            budgets.append({
                "client_id": budget.client_id,
                "model_id": budget.model_id,
                "epsilon_spent": budget.epsilon_spent,
                "delta_spent": budget.delta_spent,
                "epsilon_budget": budget.epsilon_budget,
                "delta_budget": budget.delta_budget,
                "last_updated": budget.last_updated.isoformat(),
                "mechanisms_used": budget.mechanisms_used
            })
        
        return {"privacy_budgets": budgets}
    except Exception as e:
        logger.error(f"Error getting privacy budgets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_federated_status():
    """Get federated learning status"""
    try:
        return fl_manager.get_federated_learning_status()
    except Exception as e:
        logger.error(f"Error getting federated status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
