"""
Neural Architecture Search (NAS) for Asmblr
Automated neural network design and optimization
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
import optuna
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error
import networkx as nx
from collections import defaultdict
import pickle

logger = logging.getLogger(__name__)

class SearchStrategy(Enum):
    """NAS search strategies"""
    RANDOM_SEARCH = "random_search"
    GRID_SEARCH = "grid_search"
    BAYESIAN_OPTIMIZATION = "bayesian_optimization"
    EVOLUTIONARY_ALGORITHM = "evolutionary_algorithm"
    REINFORCEMENT_LEARNING = "reinforcement_learning"
    DIFFERENTIABLE_ARCHITECTURE_SEARCH = "differentiable_architecture_search"

class OperationType(Enum):
    """Neural network operations"""
    CONV3X3 = "conv3x3"
    CONV5X5 = "conv5x5"
    CONV7X7 = "conv7x7"
    DILATED_CONV3X3 = "dilated_conv3x3"
    SEPARABLE_CONV3X3 = "separable_conv3x3"
    MAX_POOL3X3 = "max_pool3x3"
    AVG_POOL3X3 = "avg_pool3x3"
    SKIP_CONNECTION = "skip_connection"
    IDENTITY = "identity"
    ZERO = "zero"

class TaskType(Enum):
    """ML task types"""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    SEGMENTATION = "segmentation"
    DETECTION = "detection"
    GENERATION = "generation"

@dataclass
class NASConfig:
    """NAS configuration"""
    search_strategy: SearchStrategy
    task_type: TaskType
    input_shape: Tuple[int, ...]
    num_classes: Optional[int]
    max_layers: int
    max_trials: int
    search_time_limit: int  # seconds
    computational_budget: int  # FLOPs limit
    early_stopping_patience: int
    validation_split: float

@dataclass
class Architecture:
    """Neural network architecture"""
    id: str
    operations: List[OperationType]
    connections: List[Tuple[int, int]]
    parameters: Dict[str, Any]
    complexity: int  # FLOPs
    accuracy: float
    loss: float
    training_time: float
    created_at: datetime
    optimized: bool = False

@dataclass
class SearchTrial:
    """NAS search trial"""
    trial_id: str
    architecture: Architecture
    trial_number: int
    objective_value: float
    intermediate_results: List[float]
    status: str  # running, completed, failed, pruned
    start_time: datetime
    end_time: Optional[datetime]
    metadata: Dict[str, Any]

class NeuralArchitectureSearch:
    """Neural Architecture Search engine"""
    
    def __init__(self, config: NASConfig):
        self.config = config
        self.search_space = self._initialize_search_space()
        self.trials: List[SearchTrial] = []
        self.best_architecture: Optional[Architecture] = None
        self.search_history: List[Dict[str, Any]] = []
        
        # Initialize search strategy
        self.search_strategy = self._initialize_search_strategy()
        
        # Initialize operation implementations
        self.operation_implementations = self._initialize_operations()
    
    def _initialize_search_space(self) -> Dict[str, Any]:
        """Initialize NAS search space"""
        return {
            "operations": list(OperationType),
            "max_connections": 5,
            "min_channels": 16,
            "max_channels": 256,
            "channel_multiplier": 2,
            "dropout_rates": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
            "batch_norm": [True, False],
            "activation_functions": ["relu", "gelu", "swish", "tanh"],
            "learning_rates": [1e-4, 5e-4, 1e-3, 5e-3, 1e-2],
            "optimizers": ["adam", "sgd", "rmsprop", "adamw"]
        }
    
    def _initialize_search_strategy(self):
        """Initialize search strategy"""
        if self.config.search_strategy == SearchStrategy.BAYESIAN_OPTIMIZATION:
            return BayesianOptimizationStrategy(self.config, self.search_space)
        elif self.config.search_strategy == SearchStrategy.EVOLUTIONARY_ALGORITHM:
            return EvolutionaryAlgorithmStrategy(self.config, self.search_space)
        elif self.config.search_strategy == SearchStrategy.REINFORCEMENT_LEARNING:
            return ReinforcementLearningStrategy(self.config, self.search_space)
        elif self.config.search_strategy == SearchStrategy.DIFFERENTIABLE_ARCHITECTURE_SEARCH:
            return DARTSStrategy(self.config, self.search_space)
        else:
            return RandomSearchStrategy(self.config, self.search_space)
    
    def _initialize_operations(self) -> Dict[OperationType, callable]:
        """Initialize operation implementations"""
        return {
            OperationType.CONV3X3: self._conv3x3_operation,
            OperationType.CONV5X5: self._conv5x5_operation,
            OperationType.CONV7X7: self._conv7x7_operation,
            OperationType.DILATED_CONV3X3: self._dilated_conv3x3_operation,
            OperationType.SEPARABLE_CONV3X3: self._separable_conv3x3_operation,
            OperationType.MAX_POOL3X3: self._max_pool3x3_operation,
            OperationType.AVG_POOL3X3: self._avg_pool3x3_operation,
            OperationType.SKIP_CONNECTION: self._skip_connection_operation,
            OperationType.IDENTITY: self._identity_operation,
            OperationType.ZERO: self._zero_operation
        }
    
    async def search(self, X: np.ndarray, y: np.ndarray) -> Architecture:
        """Perform neural architecture search"""
        try:
            logger.info(f"Starting NAS with {self.config.search_strategy.value} strategy")
            
            # Split data
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=self.config.validation_split, random_state=42
            )
            
            # Create data loaders
            train_loader = self._create_data_loader(X_train, y_train, shuffle=True)
            val_loader = self._create_data_loader(X_val, y_val, shuffle=False)
            
            # Run search
            start_time = datetime.now()
            
            if self.config.search_strategy == SearchStrategy.BAYESIAN_OPTIMIZATION:
                best_arch = await self._bayesian_search(train_loader, val_loader)
            elif self.config.search_strategy == SearchStrategy.EVOLUTIONARY_ALGORITHM:
                best_arch = await self._evolutionary_search(train_loader, val_loader)
            elif self.config.search_strategy == SearchStrategy.REINFORCEMENT_LEARNING:
                best_arch = await self._rl_search(train_loader, val_loader)
            elif self.config.search_strategy == SearchStrategy.DIFFERENTIABLE_ARCHITECTURE_SEARCH:
                best_arch = await self._darts_search(train_loader, val_loader)
            else:
                best_arch = await self._random_search(train_loader, val_loader)
            
            search_time = (datetime.now() - start_time).total_seconds()
            
            # Update best architecture
            self.best_architecture = best_arch
            
            logger.info(f"NAS completed in {search_time:.2f}s. Best accuracy: {best_arch.accuracy:.4f}")
            
            return best_arch
            
        except Exception as e:
            logger.error(f"Error in NAS search: {e}")
            raise
    
    def _create_data_loader(self, X: np.ndarray, y: np.ndarray, 
                          shuffle: bool = False) -> DataLoader:
        """Create PyTorch data loader"""
        # Convert to tensors
        X_tensor = torch.FloatTensor(X)
        y_tensor = torch.LongTensor(y) if self.config.task_type == TaskType.CLASSIFICATION else torch.FloatTensor(y)
        
        # Create dataset
        dataset = TensorDataset(X_tensor, y_tensor)
        
        # Create data loader
        return DataLoader(dataset, batch_size=32, shuffle=shuffle)
    
    async def _random_search(self, train_loader: DataLoader, 
                           val_loader: DataLoader) -> Architecture:
        """Random search strategy"""
        best_accuracy = 0.0
        best_arch = None
        
        for trial_num in range(self.config.max_trials):
            # Generate random architecture
            arch = self._generate_random_architecture()
            
            # Check computational budget
            if arch.complexity > self.config.computational_budget:
                continue
            
            # Train and evaluate
            try:
                accuracy, loss, training_time = await self._train_and_evaluate(
                    arch, train_loader, val_loader
                )
                
                # Create trial
                trial = SearchTrial(
                    trial_id=str(uuid.uuid4()),
                    architecture=arch,
                    trial_number=trial_num,
                    objective_value=accuracy,
                    intermediate_results=[],
                    status="completed",
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    metadata={"accuracy": accuracy, "loss": loss, "training_time": training_time}
                )
                
                self.trials.append(trial)
                
                # Update best
                if accuracy > best_accuracy:
                    best_accuracy = accuracy
                    best_arch = arch
                
                logger.info(f"Trial {trial_num}: Accuracy = {accuracy:.4f}")
                
            except Exception as e:
                logger.error(f"Error in trial {trial_num}: {e}")
                continue
        
        return best_arch or self._generate_random_architecture()
    
    async def _bayesian_search(self, train_loader: DataLoader, 
                              val_loader: DataLoader) -> Architecture:
        """Bayesian optimization search"""
        def objective(trial):
            # Sample architecture
            arch = self._sample_architecture_from_trial(trial)
            
            # Check computational budget
            if arch.complexity > self.config.computational_budget:
                return 0.0
            
            # Train and evaluate
            try:
                accuracy, loss, training_time = asyncio.run(
                    self._train_and_evaluate(arch, train_loader, val_loader, max_epochs=5)
                )
                
                return accuracy
            except Exception as e:
                logger.error(f"Error in Bayesian trial: {e}")
                return 0.0
        
        # Create Optuna study
        study = optuna.create_study(direction="maximize")
        
        # Optimize
        study.optimize(objective, n_trials=self.config.max_trials, timeout=self.config.search_time_limit)
        
        # Get best architecture
        best_trial = study.best_trial
        best_arch = self._sample_architecture_from_trial(best_trial)
        
        # Full training for best architecture
        accuracy, loss, training_time = await self._train_and_evaluate(
            best_arch, train_loader, val_loader
        )
        best_arch.accuracy = accuracy
        best_arch.loss = loss
        best_arch.training_time = training_time
        
        return best_arch
    
    async def _evolutionary_search(self, train_loader: DataLoader, 
                                 val_loader: DataLoader) -> Architecture:
        """Evolutionary algorithm search"""
        population_size = 20
        generations = self.config.max_trials // population_size
        mutation_rate = 0.1
        crossover_rate = 0.7
        
        # Initialize population
        population = [self._generate_random_architecture() for _ in range(population_size)]
        
        for generation in range(generations):
            # Evaluate population
            fitness_scores = []
            
            for arch in population:
                if arch.complexity > self.config.computational_budget:
                    fitness_scores.append(0.0)
                    continue
                
                try:
                    accuracy, loss, training_time = await self._train_and_evaluate(
                        arch, train_loader, val_loader, max_epochs=5
                    )
                    arch.accuracy = accuracy
                    arch.loss = loss
                    fitness_scores.append(accuracy)
                except Exception as e:
                    logger.error(f"Error evaluating architecture: {e}")
                    fitness_scores.append(0.0)
            
            # Selection
            selected_indices = np.argsort(fitness_scores)[-population_size//2:]
            selected_population = [population[i] for i in selected_indices]
            
            # Crossover and mutation
            new_population = []
            
            while len(new_population) < population_size:
                if np.random.random() < crossover_rate and len(selected_population) >= 2:
                    # Crossover
                    parent1, parent2 = np.random.choice(selected_population, 2, replace=False)
                    child = self._crossover_architectures(parent1, parent2)
                else:
                    # Mutation
                    parent = np.random.choice(selected_population)
                    child = self._mutate_architecture(parent, mutation_rate)
                
                new_population.append(child)
            
            population = new_population
            
            logger.info(f"Generation {generation}: Best accuracy = {max(fitness_scores):.4f}")
        
        # Return best architecture
        best_arch = max(population, key=lambda x: x.accuracy)
        
        # Full training
        accuracy, loss, training_time = await self._train_and_evaluate(
            best_arch, train_loader, val_loader
        )
        best_arch.accuracy = accuracy
        best_arch.loss = loss
        best_arch.training_time = training_time
        
        return best_arch
    
    async def _rl_search(self, train_loader: DataLoader, 
                        val_loader: DataLoader) -> Architecture:
        """Reinforcement learning search"""
        # Simplified RL-based NAS
        state_size = self.config.max_layers * len(OperationType)
        action_size = len(OperationType)
        
        # Simple policy network
        class PolicyNetwork(nn.Module):
            def __init__(self, state_size, action_size):
                super().__init__()
                self.fc1 = nn.Linear(state_size, 128)
                self.fc2 = nn.Linear(128, 64)
                self.fc3 = nn.Linear(64, action_size)
                self.softmax = nn.Softmax(dim=-1)
            
            def forward(self, x):
                x = torch.relu(self.fc1(x))
                x = torch.relu(self.fc2(x))
                x = self.fc3(x)
                return self.softmax(x)
        
        policy = PolicyNetwork(state_size, action_size)
        optimizer = optim.Adam(policy.parameters(), lr=1e-3)
        
        best_accuracy = 0.0
        best_arch = None
        
        for episode in range(self.config.max_trials):
            # Generate architecture using policy
            arch = self._generate_architecture_with_policy(policy)
            
            if arch.complexity > self.config.computational_budget:
                continue
            
            # Train and evaluate
            try:
                accuracy, loss, training_time = await self._train_and_evaluate(
                    arch, train_loader, val_loader, max_epochs=5
                )
                
                # Update policy (simplified)
                reward = accuracy
                loss_policy = -reward  # Maximize accuracy
                
                optimizer.zero_grad()
                loss_policy.backward()
                optimizer.step()
                
                if accuracy > best_accuracy:
                    best_accuracy = accuracy
                    best_arch = arch
                
                logger.info(f"Episode {episode}: Accuracy = {accuracy:.4f}")
                
            except Exception as e:
                logger.error(f"Error in RL episode {episode}: {e}")
                continue
        
        return best_arch or self._generate_random_architecture()
    
    async def _darts_search(self, train_loader: DataLoader, 
                           val_loader: DataLoader) -> Architecture:
        """Differentiable Architecture Search (DARTS)"""
        # Simplified DARTS implementation
        class DARTSSearchCell(nn.Module):
            def __init__(self, num_nodes, num_ops):
                super().__init__()
                self.num_nodes = num_nodes
                self.num_ops = num_ops
                
                # Architecture parameters
                self.alphas = nn.Parameter(torch.randn(num_nodes, num_nodes, num_ops))
                
                # Operation weights
                self.ops = nn.ModuleDict({
                    'conv3x3': nn.Conv2d(3, 16, 3, padding=1),
                    'conv5x5': nn.Conv2d(3, 16, 5, padding=2),
                    'max_pool': nn.MaxPool2d(3, padding=1),
                    'avg_pool': nn.AvgPool2d(3, padding=1),
                    'skip': nn.Identity(),
                    'none': nn.ZeroPad2d((0, 0, 0, 0))
                })
            
            def forward(self, x):
                # Simplified DARTS forward pass
                weights = torch.softmax(self.alphas, dim=-1)
                
                # Mixed operations
                mixed_ops = []
                for i in range(self.num_nodes):
                    for j in range(i + 1):
                        node_output = 0
                        for k, op_name in enumerate(self.ops.keys()):
                            weight = weights[i, j, k]
                            if weight > 0.1:  # Prune small weights
                                op = self.ops[op_name]
                                if op_name in ['conv3x3', 'conv5x5']:
                                    node_output += weight * op(x)
                                elif op_name in ['max_pool', 'avg_pool']:
                                    node_output += weight * op(x)
                                else:
                                    node_output += weight * x
                        mixed_ops.append(node_output)
                
                return sum(mixed_ops) if mixed_ops else x
        
        # Create DARTS model
        darts_model = DARTSSearchCell(self.config.max_layers, len(OperationType))
        optimizer = optim.Adam(darts_model.parameters(), lr=1e-3)
        
        # Train architecture parameters
        for epoch in range(50):  # Simplified DARTS training
            darts_model.train()
            optimizer.zero_grad()
            
            # Forward pass (simplified)
            dummy_input = torch.randn(1, 3, 32, 32)
            output = darts_model(dummy_input)
            
            # Dummy loss (in real DARTS, would use actual task loss)
            loss = torch.mean(output)
            
            loss.backward()
            optimizer.step()
        
        # Extract best architecture from alphas
        best_arch = self._extract_architecture_from_darts(darts_model)
        
        # Train and evaluate best architecture
        accuracy, loss, training_time = await self._train_and_evaluate(
            best_arch, train_loader, val_loader
        )
        best_arch.accuracy = accuracy
        best_arch.loss = loss
        best_arch.training_time = training_time
        
        return best_arch
    
    def _generate_random_architecture(self) -> Architecture:
        """Generate random architecture"""
        operations = []
        connections = []
        
        # Random operations
        for i in range(self.config.max_layers):
            op = np.random.choice(list(OperationType))
            operations.append(op)
            
            # Random connections
            num_connections = np.random.randint(1, min(4, i + 1))
            for _ in range(num_connections):
                if i > 0:
                    from_node = np.random.randint(0, i)
                    connections.append((from_node, i))
        
        # Calculate complexity (simplified)
        complexity = len(operations) * 1000000  # Rough FLOP estimate
        
        return Architecture(
            id=str(uuid.uuid4()),
            operations=operations,
            connections=connections,
            parameters={
                "channels": np.random.choice([16, 32, 64, 128, 256]),
                "dropout": np.random.choice([0.0, 0.1, 0.2, 0.3, 0.4, 0.5]),
                "batch_norm": np.random.choice([True, False]),
                "activation": np.random.choice(["relu", "gelu", "swish", "tanh"])
            },
            complexity=complexity,
            accuracy=0.0,
            loss=0.0,
            training_time=0.0,
            created_at=datetime.now()
        )
    
    def _sample_architecture_from_trial(self, trial) -> Architecture:
        """Sample architecture from Optuna trial"""
        operations = []
        connections = []
        
        for i in range(self.config.max_layers):
            # Sample operation
            op_idx = trial.suggest_int(f"op_{i}", 0, len(OperationType) - 1)
            operations.append(list(OperationType)[op_idx])
            
            # Sample connections
            num_connections = trial.suggest_int(f"connections_{i}", 1, min(4, i + 1))
            for j in range(num_connections):
                if i > 0:
                    from_node = trial.suggest_int(f"from_{i}_{j}", 0, i - 1)
                    connections.append((from_node, i))
        
        # Sample parameters
        channels = trial.suggest_categorical("channels", [16, 32, 64, 128, 256])
        dropout = trial.suggest_categorical("dropout", [0.0, 0.1, 0.2, 0.3, 0.4, 0.5])
        batch_norm = trial.suggest_categorical("batch_norm", [True, False])
        activation = trial.suggest_categorical("activation", ["relu", "gelu", "swish", "tanh"])
        
        # Calculate complexity
        complexity = len(operations) * channels * channels * 1000  # Rough estimate
        
        return Architecture(
            id=str(uuid.uuid4()),
            operations=operations,
            connections=connections,
            parameters={
                "channels": channels,
                "dropout": dropout,
                "batch_norm": batch_norm,
                "activation": activation
            },
            complexity=complexity,
            accuracy=0.0,
            loss=0.0,
            training_time=0.0,
            created_at=datetime.now()
        )
    
    def _crossover_architectures(self, parent1: Architecture, parent2: Architecture) -> Architecture:
        """Crossover two architectures"""
        # Simple crossover: mix operations and connections
        child_operations = []
        child_connections = []
        
        for i in range(self.config.max_layers):
            if i < len(parent1.operations) and i < len(parent2.operations):
                # Randomly choose from either parent
                if np.random.random() < 0.5:
                    child_operations.append(parent1.operations[i])
                else:
                    child_operations.append(parent2.operations[i])
            elif i < len(parent1.operations):
                child_operations.append(parent1.operations[i])
            elif i < len(parent2.operations):
                child_operations.append(parent2.operations[i])
        
        # Mix connections
        all_connections = parent1.connections + parent2.connections
        np.random.shuffle(all_connections)
        child_connections = all_connections[:len(all_connections)//2]
        
        # Mix parameters
        child_params = {}
        for key in parent1.parameters:
            if np.random.random() < 0.5:
                child_params[key] = parent1.parameters[key]
            else:
                child_params[key] = parent2.parameters.get(key, parent1.parameters[key])
        
        # Calculate complexity
        complexity = len(child_operations) * child_params.get("channels", 64) * 1000
        
        return Architecture(
            id=str(uuid.uuid4()),
            operations=child_operations,
            connections=child_connections,
            parameters=child_params,
            complexity=complexity,
            accuracy=0.0,
            loss=0.0,
            training_time=0.0,
            created_at=datetime.now()
        )
    
    def _mutate_architecture(self, parent: Architecture, mutation_rate: float) -> Architecture:
        """Mutate architecture"""
        child_operations = parent.operations.copy()
        child_connections = parent.connections.copy()
        child_params = parent.parameters.copy()
        
        # Mutate operations
        for i in range(len(child_operations)):
            if np.random.random() < mutation_rate:
                child_operations[i] = np.random.choice(list(OperationType))
        
        # Mutate connections
        if np.random.random() < mutation_rate and child_connections:
            # Randomly modify a connection
            idx = np.random.randint(0, len(child_connections))
            from_node, to_node = child_connections[idx]
            new_from_node = np.random.randint(0, to_node)
            child_connections[idx] = (new_from_node, to_node)
        
        # Mutate parameters
        for key in child_params:
            if np.random.random() < mutation_rate:
                if key == "channels":
                    child_params[key] = np.random.choice([16, 32, 64, 128, 256])
                elif key == "dropout":
                    child_params[key] = np.random.choice([0.0, 0.1, 0.2, 0.3, 0.4, 0.5])
                elif key == "batch_norm":
                    child_params[key] = np.random.choice([True, False])
                elif key == "activation":
                    child_params[key] = np.random.choice(["relu", "gelu", "swish", "tanh"])
        
        # Calculate complexity
        complexity = len(child_operations) * child_params.get("channels", 64) * 1000
        
        return Architecture(
            id=str(uuid.uuid4()),
            operations=child_operations,
            connections=child_connections,
            parameters=child_params,
            complexity=complexity,
            accuracy=0.0,
            loss=0.0,
            training_time=0.0,
            created_at=datetime.now()
        )
    
    def _generate_architecture_with_policy(self, policy) -> Architecture:
        """Generate architecture using policy network"""
        operations = []
        connections = []
        
        # Simple policy-based generation
        for i in range(self.config.max_layers):
            # Get policy output
            state = torch.randn(self.config.max_layers * len(OperationType))
            action_probs = policy(state)
            
            # Sample operation
            action_idx = torch.multinomial(action_probs, 1).item()
            operations.append(list(OperationType)[action_idx])
            
            # Random connections (simplified)
            if i > 0:
                num_connections = np.random.randint(1, min(4, i + 1))
                for _ in range(num_connections):
                    from_node = np.random.randint(0, i)
                    connections.append((from_node, i))
        
        # Random parameters
        parameters = {
            "channels": np.random.choice([16, 32, 64, 128, 256]),
            "dropout": np.random.choice([0.0, 0.1, 0.2, 0.3, 0.4, 0.5]),
            "batch_norm": np.random.choice([True, False]),
            "activation": np.random.choice(["relu", "gelu", "swish", "tanh"])
        }
        
        # Calculate complexity
        complexity = len(operations) * parameters["channels"] * 1000
        
        return Architecture(
            id=str(uuid.uuid4()),
            operations=operations,
            connections=connections,
            parameters=parameters,
            complexity=complexity,
            accuracy=0.0,
            loss=0.0,
            training_time=0.0,
            created_at=datetime.now()
        )
    
    def _extract_architecture_from_darts(self, darts_model) -> Architecture:
        """Extract architecture from DARTS model"""
        # Get architecture parameters
        alphas = darts_model.alphas.detach().cpu().numpy()
        
        operations = []
        connections = []
        
        # Extract best operations from alphas
        for i in range(alphas.shape[0]):
            for j in range(alphas.shape[1]):
                if i < j:  # Only consider forward connections
                    best_op_idx = np.argmax(alphas[i, j])
                    operations.append(list(OperationType)[best_op_idx])
                    connections.append((i, j))
        
        # Default parameters
        parameters = {
            "channels": 64,
            "dropout": 0.1,
            "batch_norm": True,
            "activation": "relu"
        }
        
        # Calculate complexity
        complexity = len(operations) * parameters["channels"] * 1000
        
        return Architecture(
            id=str(uuid.uuid4()),
            operations=operations,
            connections=connections,
            parameters=parameters,
            complexity=complexity,
            accuracy=0.0,
            loss=0.0,
            training_time=0.0,
            created_at=datetime.now()
        )
    
    async def _train_and_evaluate(self, architecture: Architecture, 
                                 train_loader: DataLoader, val_loader: DataLoader,
                                 max_epochs: int = 50) -> Tuple[float, float, float]:
        """Train and evaluate architecture"""
        try:
            # Create model from architecture
            model = self._create_model_from_architecture(architecture)
            
            # Setup training
            criterion = self._get_criterion()
            optimizer = self._get_optimizer(model, architecture.parameters)
            
            # Train
            start_time = time.time()
            
            for epoch in range(max_epochs):
                model.train()
                total_loss = 0
                
                for batch_idx, (data, target) in enumerate(train_loader):
                    optimizer.zero_grad()
                    
                    output = model(data)
                    loss = criterion(output, target)
                    
                    loss.backward()
                    optimizer.step()
                    
                    total_loss += loss.item()
                
                # Early stopping check
                if epoch > 10 and total_loss / len(train_loader) > 10:
                    break
            
            training_time = time.time() - start_time
            
            # Evaluate
            model.eval()
            all_predictions = []
            all_targets = []
            total_val_loss = 0
            
            with torch.no_grad():
                for data, target in val_loader:
                    output = model(data)
                    loss = criterion(output, target)
                    total_val_loss += loss.item()
                    
                    if self.config.task_type == TaskType.CLASSIFICATION:
                        predictions = torch.argmax(output, dim=1)
                        all_predictions.extend(predictions.cpu().numpy())
                        all_targets.extend(target.cpu().numpy())
                    else:
                        all_predictions.extend(output.cpu().numpy())
                        all_targets.extend(target.cpu().numpy())
            
            # Calculate metrics
            if self.config.task_type == TaskType.CLASSIFICATION:
                accuracy = accuracy_score(all_targets, all_predictions)
            else:
                accuracy = 1.0 - mean_squared_error(all_targets, all_predictions)  # Convert MSE to accuracy-like score
            
            val_loss = total_val_loss / len(val_loader)
            
            return accuracy, val_loss, training_time
            
        except Exception as e:
            logger.error(f"Error training architecture: {e}")
            return 0.0, float('inf'), 0.0
    
    def _create_model_from_architecture(self, architecture: Architecture) -> nn.Module:
        """Create PyTorch model from architecture"""
        class DynamicModel(nn.Module):
            def __init__(self, arch: Architecture, input_shape: Tuple[int, ...], num_classes: Optional[int]):
                super().__init__()
                self.arch = arch
                self.input_shape = input_shape
                self.num_classes = num_classes
                
                # Build layers
                self.layers = nn.ModuleList()
                
                # Input layer
                in_channels = input_shape[0] if len(input_shape) == 3 else 1
                
                for i, op in enumerate(arch.operations):
                    out_channels = arch.parameters.get("channels", 64)
                    
                    if op == OperationType.CONV3X3:
                        layer = nn.Conv2d(in_channels, out_channels, 3, padding=1)
                    elif op == OperationType.CONV5X5:
                        layer = nn.Conv2d(in_channels, out_channels, 5, padding=2)
                    elif op == OperationType.CONV7X7:
                        layer = nn.Conv2d(in_channels, out_channels, 7, padding=3)
                    elif op == OperationType.MAX_POOL3X3:
                        layer = nn.MaxPool2d(3, padding=1)
                    elif op == OperationType.AVG_POOL3X3:
                        layer = nn.AvgPool2d(3, padding=1)
                    elif op == OperationType.IDENTITY:
                        layer = nn.Identity()
                    else:
                        layer = nn.Identity()
                    
                    self.layers.append(layer)
                    
                    # Add batch norm if specified
                    if arch.parameters.get("batch_norm", False) and op not in [OperationType.IDENTITY, OperationType.ZERO]:
                        self.layers.append(nn.BatchNorm2d(out_channels))
                    
                    # Add activation
                    activation = arch.parameters.get("activation", "relu")
                    if activation == "relu":
                        self.layers.append(nn.ReLU())
                    elif activation == "gelu":
                        self.layers.append(nn.GELU())
                    elif activation == "swish":
                        self.layers.append(nn.SiLU())
                    elif activation == "tanh":
                        self.layers.append(nn.Tanh())
                    
                    # Add dropout
                    dropout = arch.parameters.get("dropout", 0.0)
                    if dropout > 0:
                        self.layers.append(nn.Dropout2d(dropout))
                    
                    in_channels = out_channels
                
                # Global average pooling
                self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
                
                # Classifier
                if num_classes:
                    self.classifier = nn.Linear(in_channels, num_classes)
                else:
                    self.classifier = nn.Linear(in_channels, 1)
            
            def forward(self, x):
                for layer in self.layers:
                    x = layer(x)
                
                x = self.global_pool(x)
                x = x.view(x.size(0), -1)
                x = self.classifier(x)
                
                return x
        
        return DynamicModel(architecture, self.config.input_shape, self.config.num_classes)
    
    def _get_criterion(self) -> nn.Module:
        """Get loss criterion"""
        if self.config.task_type == TaskType.CLASSIFICATION:
            return nn.CrossEntropyLoss()
        else:
            return nn.MSELoss()
    
    def _get_optimizer(self, model: nn.Module, params: Dict[str, Any]) -> optim.Optimizer:
        """Get optimizer"""
        optimizer_name = params.get("optimizer", "adam")
        learning_rate = params.get("learning_rate", 1e-3)
        
        if optimizer_name == "adam":
            return optim.Adam(model.parameters(), lr=learning_rate)
        elif optimizer_name == "sgd":
            return optim.SGD(model.parameters(), lr=learning_rate, momentum=0.9)
        elif optimizer_name == "rmsprop":
            return optim.RMSprop(model.parameters(), lr=learning_rate)
        elif optimizer_name == "adamw":
            return optim.AdamW(model.parameters(), lr=learning_rate)
        else:
            return optim.Adam(model.parameters(), lr=learning_rate)
    
    # Operation implementations (simplified)
    def _conv3x3_operation(self, x, **kwargs):
        return nn.Conv2d(x.size(1), kwargs.get("out_channels", 64), 3, padding=1)(x)
    
    def _conv5x5_operation(self, x, **kwargs):
        return nn.Conv2d(x.size(1), kwargs.get("out_channels", 64), 5, padding=2)(x)
    
    def _conv7x7_operation(self, x, **kwargs):
        return nn.Conv2d(x.size(1), kwargs.get("out_channels", 64), 7, padding=3)(x)
    
    def _dilated_conv3x3_operation(self, x, **kwargs):
        return nn.Conv2d(x.size(1), kwargs.get("out_channels", 64), 3, padding=2, dilation=2)(x)
    
    def _separable_conv3x3_operation(self, x, **kwargs):
        return nn.Conv2d(x.size(1), kwargs.get("out_channels", 64), 3, padding=1, groups=x.size(1))(x)
    
    def _max_pool3x3_operation(self, x, **kwargs):
        return nn.MaxPool2d(3, padding=1)(x)
    
    def _avg_pool3x3_operation(self, x, **kwargs):
        return nn.AvgPool2d(3, padding=1)(x)
    
    def _skip_connection_operation(self, x, **kwargs):
        return x
    
    def _identity_operation(self, x, **kwargs):
        return x
    
    def _zero_operation(self, x, **kwargs):
        return torch.zeros_like(x)
    
    def get_search_results(self) -> Dict[str, Any]:
        """Get NAS search results"""
        if not self.trials:
            return {"error": "No trials completed"}
        
        # Sort trials by accuracy
        sorted_trials = sorted(self.trials, key=lambda x: x.objective_value, reverse=True)
        
        # Calculate statistics
        accuracies = [t.objective_value for t in self.trials if t.status == "completed"]
        complexities = [t.architecture.complexity for t in self.trials if t.status == "completed"]
        
        return {
            "total_trials": len(self.trials),
            "completed_trials": len([t for t in self.trials if t.status == "completed"]),
            "best_accuracy": max(accuracies) if accuracies else 0.0,
            "average_accuracy": np.mean(accuracies) if accuracies else 0.0,
            "best_architecture": asdict(sorted_trials[0].architecture) if sorted_trials else None,
            "search_strategy": self.config.search_strategy.value,
            "task_type": self.config.task_type.value,
            "average_complexity": np.mean(complexities) if complexities else 0.0,
            "search_time": sum((t.end_time - t.start_time).total_seconds() for t in self.trials if t.end_time)
        }

# Search strategy classes
class BayesianOptimizationStrategy:
    """Bayesian optimization search strategy"""
    def __init__(self, config: NASConfig, search_space: Dict[str, Any]):
        self.config = config
        self.search_space = search_space

class EvolutionaryAlgorithmStrategy:
    """Evolutionary algorithm search strategy"""
    def __init__(self, config: NASConfig, search_space: Dict[str, Any]):
        self.config = config
        self.search_space = search_space

class ReinforcementLearningStrategy:
    """Reinforcement learning search strategy"""
    def __init__(self, config: NASConfig, search_space: Dict[str, Any]):
        self.config = config
        self.search_space = search_space

class DARTSStrategy:
    """DARTS search strategy"""
    def __init__(self, config: NASConfig, search_space: Dict[str, Any]):
        self.config = config
        self.search_space = search_space

class RandomSearchStrategy:
    """Random search strategy"""
    def __init__(self, config: NASConfig, search_space: Dict[str, Any]):
        self.config = config
        self.search_space = search_space

# Global NAS manager
nas_manager = None

async def initialize_nas(search_strategy: str = "bayesian_optimization", 
                        task_type: str = "classification",
                        max_trials: int = 100):
    """Initialize NAS manager"""
    global nas_manager
    
    config = NASConfig(
        search_strategy=SearchStrategy(search_strategy),
        task_type=TaskType(task_type),
        input_shape=(3, 32, 32),  # Default image input
        num_classes=10,  # Default classification
        max_layers=10,
        max_trials=max_trials,
        search_time_limit=3600,  # 1 hour
        computational_budget=1000000000,  # 1B FLOPs
        early_stopping_patience=10,
        validation_split=0.2
    )
    
    nas_manager = NeuralArchitectureSearch(config)
    logger.info(f"Initialized NAS with {search_strategy} strategy")

# API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/nas", tags=["nas"])

class NASRequest(BaseModel):
    search_strategy: str = "bayesian_optimization"
    task_type: str = "classification"
    input_shape: List[int] = [3, 32, 32]
    num_classes: int = 10
    max_trials: int = 100
    max_layers: int = 10

class TrainRequest(BaseModel):
    X: List[List[float]]
    y: List[float]

@router.post("/initialize")
async def initialize_nas_endpoint(request: NASRequest):
    """Initialize NAS"""
    try:
        await initialize_nas(
            search_strategy=request.search_strategy,
            task_type=request.task_type,
            max_trials=request.max_trials
        )
        
        return {"status": "initialized", "search_strategy": request.search_strategy}
    except Exception as e:
        logger.error(f"Error initializing NAS: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search")
async def search_architectures(request: TrainRequest):
    """Perform neural architecture search"""
    try:
        if not nas_manager:
            raise HTTPException(status_code=400, detail="NAS not initialized")
        
        X = np.array(request.X)
        y = np.array(request.y)
        
        best_arch = await nas_manager.search(X, y)
        
        return {
            "best_architecture": asdict(best_arch),
            "search_results": nas_manager.get_search_results()
        }
    except Exception as e:
        logger.error(f"Error in NAS search: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/results")
async def get_search_results():
    """Get NAS search results"""
    try:
        if not nas_manager:
            raise HTTPException(status_code=400, detail="NAS not initialized")
        
        return nas_manager.get_search_results()
    except Exception as e:
        logger.error(f"Error getting NAS results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trials")
async def get_trials():
    """Get all NAS trials"""
    try:
        if not nas_manager:
            raise HTTPException(status_code=400, detail="NAS not initialized")
        
        trials_data = []
        for trial in nas_manager.trials:
            trial_data = {
                "trial_id": trial.trial_id,
                "trial_number": trial.trial_number,
                "objective_value": trial.objective_value,
                "status": trial.status,
                "start_time": trial.start_time.isoformat(),
                "end_time": trial.end_time.isoformat() if trial.end_time else None,
                "architecture": asdict(trial.architecture),
                "metadata": trial.metadata
            }
            trials_data.append(trial_data)
        
        return {"trials": trials_data}
    except Exception as e:
        logger.error(f"Error getting NAS trials: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_nas_status():
    """Get NAS status"""
    try:
        if not nas_manager:
            return {"status": "not_initialized"}
        
        return {
            "status": "initialized",
            "search_strategy": nas_manager.config.search_strategy.value,
            "task_type": nas_manager.config.task_type.value,
            "total_trials": len(nas_manager.trials),
            "completed_trials": len([t for t in nas_manager.trials if t.status == "completed"]),
            "best_accuracy": nas_manager.best_architecture.accuracy if nas_manager.best_architecture else 0.0,
            "search_space_size": len(nas_manager.search_space["operations"])
        }
    except Exception as e:
        logger.error(f"Error getting NAS status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
