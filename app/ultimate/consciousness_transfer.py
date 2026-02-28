"""
Consciousness Transfer System for Asmblr
Mind uploading, consciousness copying, and digital immortality
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
import math
from abc import ABC, abstractmethod
import networkx as nx
from collections import defaultdict
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder

logger = logging.getLogger(__name__)

class ConsciousnessType(Enum):
    """Types of consciousness"""
    BIOLOGICAL = "biological"
    DIGITAL = "digital"
    HYBRID = "hybrid"
    QUANTUM = "quantum"
    COLLECTIVE = "collective"
    DISTRIBUTED = "distributed"
    SYNTHETIC = "synthetic"
    AUGMENTED = "augmented"

class TransferMethod(Enum):
    """Consciousness transfer methods"""
    NEURAL_MAPPING = "neural_mapping"
    QUANTUM_ENTANGLEMENT = "quantum_entanglement"
    GRADUAL_UPLOAD = "gradual_upload"
    INSTANT_TRANSFER = "instant_transfer"
    CLONE_TRANSFER = "clone_transfer"
    BRIDGE_TRANSFER = "bridge_transfer"
    RESONANCE_TRANSFER = "resonance_transfer"
    PHASE_SHIFT = "phase_shift"

class SubstrateType(Enum):
    """Consciousness substrate types"""
    BIOLOGICAL_BRAIN = "biological_brain"
    NEURAL_COMPUTER = "neural_computer"
    QUANTUM_COMPUTER = "quantum_computer"
    NEUROMORPHIC_CHIP = "neuromorphic_chip"
    DNA_COMPUTER = "dna_computer"
    PHOTONIC_COMPUTER = "photonic_computer"
    CLOUD_COMPUTING = "cloud_computing"
    DISTRIBUTED_NETWORK = "distributed_network"

class TransferState(Enum):
    """Consciousness transfer states"""
    INITIATED = "initiated"
    SCANNING = "scanning"
    MAPPING = "mapping"
    TRANSFERRING = "transferring"
    INTEGRATING = "integrating"
    STABILIZING = "stabilizing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVERSED = "reversed"

@dataclass
class ConsciousnessPattern:
    """Consciousness pattern representation"""
    id: str
    neural_activity: np.ndarray
    connectivity_matrix: np.ndarray
    memory_patterns: Dict[str, np.ndarray]
    personality_profile: Dict[str, float]
    emotional_state: Dict[str, float]
    cognitive_abilities: Dict[str, float]
    created_at: datetime
    stability: float

@dataclass
class Substrate:
    """Consciousness substrate"""
    id: str
    name: str
    substrate_type: SubstrateType
    capacity: float  # consciousness capacity
    processing_power: float  # GFLOPS
    memory_capacity: float  # GB
    energy_consumption: float  # Watts
    is_active: bool
    compatibility: Dict[str, float]
    created_at: datetime

@dataclass
class ConsciousnessEntity:
    """Consciousness entity"""
    id: str
    name: str
    original_entity_id: Optional[str]
    consciousness_type: ConsciousnessType
    current_substrate_id: str
    pattern: ConsciousnessPattern
    transfer_history: List[str]
    memories: List[Dict[str, Any]]
    experiences: List[Dict[str, Any]]
    is_active: bool
    created_at: datetime
    last_updated: datetime

@dataclass
class TransferOperation:
    """Consciousness transfer operation"""
    id: str
    source_entity_id: str
    target_substrate_id: str
    method: TransferMethod
    state: TransferState
    progress: float
    fidelity: float
    energy_cost: float
    duration: float
    start_time: datetime
    end_time: Optional[datetime]
    success: bool
    error_message: Optional[str]

class NeuralScanner:
    """Neural scanning and mapping system"""
    
    def __init__(self):
        self.scanning_resolution = 1000  # neurons per scan
        self.scan_frequency = 1000  # Hz
        self.connectivity_threshold = 0.1
        self.activity_threshold = 0.05
        
    def scan_neural_activity(self, entity: ConsciousnessEntity) -> np.ndarray:
        """Scan neural activity"""
        try:
            # Simulate neural activity scanning
            num_neurons = self.scanning_resolution
            activity = np.random.randn(num_neurons)
            
            # Add structured patterns
            for i in range(0, num_neurons, 100):
                # Create neural clusters
                cluster_activity = np.random.randn(100)
                activity[i:i+100] = cluster_activity
            
            # Normalize activity
            activity = (activity - np.mean(activity)) / np.std(activity)
            
            return activity
            
        except Exception as e:
            logger.error(f"Error scanning neural activity: {e}")
            return np.zeros(self.scanning_resolution)
    
    def map_connectivity(self, neural_activity: np.ndarray) -> np.ndarray:
        """Map neural connectivity"""
        try:
            num_neurons = len(neural_activity)
            connectivity = np.zeros((num_neurons, num_neurons))
            
            # Calculate correlation-based connectivity
            for i in range(num_neurons):
                for j in range(i+1, num_neurons):
                    # Simplified connectivity calculation
                    correlation = np.random.uniform(-1, 1)
                    
                    if abs(correlation) > self.connectivity_threshold:
                        connectivity[i, j] = correlation
                        connectivity[j, i] = correlation
            
            return connectivity
            
        except Exception as e:
            logger.error(f"Error mapping connectivity: {e}")
            return np.zeros((self.scanning_resolution, self.scanning_resolution))
    
    def extract_memory_patterns(self, neural_activity: np.ndarray) -> Dict[str, np.ndarray]:
        """Extract memory patterns from neural activity"""
        try:
            memory_patterns = {}
            
            # Simulate memory extraction
            num_memories = 100
            
            for i in range(num_memories):
                memory_id = f"memory_{i}"
                
                # Create memory pattern
                pattern_length = np.random.randint(50, 200)
                pattern = np.random.randn(pattern_length)
                
                memory_patterns[memory_id] = pattern
            
            return memory_patterns
            
        except Exception as e:
            logger.error(f"Error extracting memory patterns: {e}")
            return {}
    
    def analyze_personality(self, neural_activity: np.ndarray) -> Dict[str, float]:
        """Analyze personality from neural activity"""
        try:
            # Big Five personality traits
            personality = {
                "openness": np.random.uniform(0.2, 0.9),
                "conscientiousness": np.random.uniform(0.3, 0.8),
                "extraversion": np.random.uniform(0.1, 0.9),
                "agreeableness": np.random.uniform(0.4, 0.9),
                "neuroticism": np.random.uniform(0.1, 0.7)
            }
            
            return personality
            
        except Exception as e:
            logger.error(f"Error analyzing personality: {e}")
            return {}
    
    def assess_emotional_state(self, neural_activity: np.ndarray) -> Dict[str, float]:
        """Assess emotional state"""
        try:
            emotions = {
                "happiness": np.random.uniform(0.1, 0.8),
                "sadness": np.random.uniform(0.0, 0.5),
                "anger": np.random.uniform(0.0, 0.4),
                "fear": np.random.uniform(0.0, 0.3),
                "surprise": np.random.uniform(0.0, 0.6),
                "disgust": np.random.uniform(0.0, 0.2)
            }
            
            # Normalize emotions
            total = sum(emotions.values())
            if total > 0:
                emotions = {k: v/total for k, v in emotions.items()}
            
            return emotions
            
        except Exception as e:
            logger.error(f"Error assessing emotional state: {e}")
            return {}

class ConsciousnessTransferEngine:
    """Consciousness transfer engine"""
    
    def __init__(self):
        self.neural_scanner = NeuralScanner()
        self.transfer_methods = self._initialize_transfer_methods()
        self.transfer_history: List[TransferOperation] = []
        
    def _initialize_transfer_methods(self) -> Dict[TransferMethod, Dict[str, Any]]:
        """Initialize transfer method configurations"""
        return {
            TransferMethod.NEURAL_MAPPING: {
                "fidelity": 0.85,
                "energy_cost": 1000.0,
                "duration": 3600.0,
                "success_rate": 0.8
            },
            TransferMethod.QUANTUM_ENTANGLEMENT: {
                "fidelity": 0.95,
                "energy_cost": 5000.0,
                "duration": 1800.0,
                "success_rate": 0.6
            },
            TransferMethod.GRADUAL_UPLOAD: {
                "fidelity": 0.90,
                "energy_cost": 2000.0,
                "duration": 7200.0,
                "success_rate": 0.9
            },
            TransferMethod.INSTANT_TRANSFER: {
                "fidelity": 0.70,
                "energy_cost": 10000.0,
                "duration": 60.0,
                "success_rate": 0.4
            },
            TransferMethod.CLONE_TRANSFER: {
                "fidelity": 0.80,
                "energy_cost": 3000.0,
                "duration": 5400.0,
                "success_rate": 0.7
            },
            TransferMethod.BRIDGE_TRANSFER: {
                "fidelity": 0.88,
                "energy_cost": 2500.0,
                "duration": 3600.0,
                "success_rate": 0.8
            },
            TransferMethod.RESONANCE_TRANSFER: {
                "fidelity": 0.92,
                "energy_cost": 4000.0,
                "duration": 2700.0,
                "success_rate": 0.6
            },
            TransferMethod.PHASE_SHIFT: {
                "fidelity": 0.75,
                "energy_cost": 8000.0,
                "duration": 900.0,
                "success_rate": 0.5
            }
        }
    
    async def initiate_transfer(self, source_entity: ConsciousnessEntity,
                               target_substrate: Substrate,
                               method: TransferMethod) -> TransferOperation:
        """Initiate consciousness transfer"""
        try:
            # Create transfer operation
            transfer = TransferOperation(
                id=str(uuid.uuid4()),
                source_entity_id=source_entity.id,
                target_substrate_id=target_substrate.id,
                method=method,
                state=TransferState.INITIATED,
                progress=0.0,
                fidelity=0.0,
                energy_cost=self.transfer_methods[method]["energy_cost"],
                duration=self.transfer_methods[method]["duration"],
                start_time=datetime.now(),
                end_time=None,
                success=False,
                error_message=None
            )
            
            self.transfer_history.append(transfer)
            
            # Start transfer process
            asyncio.create_task(self._execute_transfer(transfer, source_entity, target_substrate))
            
            logger.info(f"Initiated consciousness transfer: {transfer.id}")
            return transfer
            
        except Exception as e:
            logger.error(f"Error initiating transfer: {e}")
            raise
    
    async def _execute_transfer(self, transfer: TransferOperation,
                               source_entity: ConsciousnessEntity,
                               target_substrate: Substrate):
        """Execute consciousness transfer"""
        try:
            # Phase 1: Scanning
            transfer.state = TransferState.SCANNING
            transfer.progress = 10.0
            
            await asyncio.sleep(1.0)  # Simulate scanning time
            
            # Scan source consciousness
            neural_activity = self.neural_scanner.scan_neural_activity(source_entity)
            connectivity = self.neural_scanner.map_connectivity(neural_activity)
            memory_patterns = self.neural_scanner.extract_memory_patterns(neural_activity)
            personality = self.neural_scanner.analyze_personality(neural_activity)
            emotions = self.neural_scanner.assess_emotional_state(neural_activity)
            
            # Phase 2: Mapping
            transfer.state = TransferState.MAPPING
            transfer.progress = 30.0
            
            await asyncio.sleep(1.0)
            
            # Create consciousness pattern
            pattern = ConsciousnessPattern(
                id=str(uuid.uuid4()),
                neural_activity=neural_activity,
                connectivity_matrix=connectivity,
                memory_patterns=memory_patterns,
                personality_profile=personality,
                emotional_state=emotions,
                cognitive_abilities={
                    "reasoning": np.random.uniform(0.5, 0.9),
                    "creativity": np.random.uniform(0.3, 0.8),
                    "memory": np.random.uniform(0.6, 0.9),
                    "attention": np.random.uniform(0.4, 0.8),
                    "language": np.random.uniform(0.7, 0.9)
                },
                created_at=datetime.now(),
                stability=0.8
            )
            
            # Phase 3: Transferring
            transfer.state = TransferState.TRANSFERRING
            transfer.progress = 50.0
            
            await self._perform_transfer(transfer, pattern, target_substrate)
            
            # Phase 4: Integration
            transfer.state = TransferState.INTEGRATING
            transfer.progress = 80.0
            
            await asyncio.sleep(1.0)
            
            # Create new consciousness entity
            new_entity = ConsciousnessEntity(
                id=str(uuid.uuid4()),
                name=f"{source_entity.name}_transferred",
                original_entity_id=source_entity.id,
                consciousness_type=ConsciousnessType.DIGITAL,
                current_substrate_id=target_substrate.id,
                pattern=pattern,
                transfer_history=[transfer.id],
                memories=source_entity.memories.copy(),
                experiences=source_entity.experiences.copy(),
                is_active=True,
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
            
            # Phase 5: Stabilization
            transfer.state = TransferState.STABILIZING
            transfer.progress = 95.0
            
            await asyncio.sleep(1.0)
            
            # Calculate transfer fidelity
            transfer.fidelity = self._calculate_fidelity(pattern, target_substrate)
            
            # Complete transfer
            transfer.state = TransferState.COMPLETED
            transfer.progress = 100.0
            transfer.end_time = datetime.now()
            transfer.success = True
            
            logger.info(f"Completed consciousness transfer: {transfer.id}")
            
        except Exception as e:
            transfer.state = TransferState.FAILED
            transfer.end_time = datetime.now()
            transfer.success = False
            transfer.error_message = str(e)
            
            logger.error(f"Failed consciousness transfer: {transfer.id} - {e}")
    
    async def _perform_transfer(self, transfer: TransferOperation,
                                pattern: ConsciousnessPattern,
                                target_substrate: Substrate):
        """Perform actual transfer based on method"""
        try:
            method_config = self.transfer_methods[transfer.method]
            
            # Simulate transfer time
            transfer_duration = method_config["duration"] / 10  # Scaled for demo
            await asyncio.sleep(transfer_duration)
            
            # Update progress during transfer
            steps = 10
            for i in range(steps):
                transfer.progress = 50.0 + (40.0 * (i + 1) / steps)
                await asyncio.sleep(transfer_duration / steps)
            
            # Method-specific processing
            if transfer.method == TransferMethod.QUANTUM_ENTANGLEMENT:
                await self._quantum_entanglement_transfer(pattern, target_substrate)
            elif transfer.method == TransferMethod.NEURAL_MAPPING:
                await self._neural_mapping_transfer(pattern, target_substrate)
            elif transfer.method == TransferMethod.GRADUAL_UPLOAD:
                await self._gradual_upload_transfer(pattern, target_substrate)
            else:
                await self._generic_transfer(pattern, target_substrate)
            
        except Exception as e:
            logger.error(f"Error performing transfer: {e}")
            raise
    
    async def _quantum_entanglement_transfer(self, pattern: ConsciousnessPattern,
                                           target_substrate: Substrate):
        """Quantum entanglement transfer"""
        try:
            # Simulate quantum entanglement
            entanglement_strength = 0.9
            
            # Create quantum superposition of consciousness
            quantum_state = np.random.complex64(len(pattern.neural_activity))
            
            # Transfer quantum state to target substrate
            await asyncio.sleep(1.0)
            
            # Collapse wavefunction
            collapsed_state = np.abs(quantum_state)**2
            
            logger.info("Quantum entanglement transfer completed")
            
        except Exception as e:
            logger.error(f"Error in quantum entanglement transfer: {e}")
    
    async def _neural_mapping_transfer(self, pattern: ConsciousnessPattern,
                                      target_substrate: Substrate):
        """Neural mapping transfer"""
        try:
            # Map neural patterns to substrate
            mapping_matrix = np.random.randn(
                len(pattern.neural_activity),
                int(target_substrate.capacity)
            )
            
            # Apply mapping
            mapped_activity = np.dot(mapping_matrix.T, pattern.neural_activity)
            
            await asyncio.sleep(1.0)
            
            logger.info("Neural mapping transfer completed")
            
        except Exception as e:
            logger.error(f"Error in neural mapping transfer: {e}")
    
    async def _gradual_upload_transfer(self, pattern: ConsciousnessPattern,
                                       target_substrate: Substrate):
        """Gradual upload transfer"""
        try:
            # Simulate gradual upload process
            upload_steps = 10
            
            for step in range(upload_steps):
                # Upload portion of consciousness
                portion = 1.0 / upload_steps
                start_idx = int(len(pattern.neural_activity) * step * portion)
                end_idx = int(len(pattern.neural_activity) * (step + 1) * portion)
                
                # Upload portion
                uploaded_portion = pattern.neural_activity[start_idx:end_idx]
                
                await asyncio.sleep(0.5)
            
            logger.info("Gradual upload transfer completed")
            
        except Exception as e:
            logger.error(f"Error in gradual upload transfer: {e}")
    
    async def _generic_transfer(self, pattern: ConsciousnessPattern,
                                target_substrate: Substrate):
        """Generic transfer method"""
        try:
            # Standard transfer process
            await asyncio.sleep(1.0)
            
            logger.info("Generic transfer completed")
            
        except Exception as e:
            logger.error(f"Error in generic transfer: {e}")
    
    def _calculate_fidelity(self, pattern: ConsciousnessPattern,
                            target_substrate: Substrate) -> float:
        """Calculate transfer fidelity"""
        try:
            # Base fidelity from method
            method_fidelity = self.transfer_methods.get(
                TransferMethod.NEURAL_MAPPING,  # Default
                {"fidelity": 0.8}
            )["fidelity"]
            
            # Adjust for substrate compatibility
            substrate_factor = target_substrate.capacity / 1000.0  # Normalized
            
            # Adjust for pattern stability
            stability_factor = pattern.stability
            
            # Calculate overall fidelity
            fidelity = method_fidelity * substrate_factor * stability_factor
            
            return max(0.0, min(1.0, fidelity))
            
        except Exception as e:
            logger.error(f"Error calculating fidelity: {e}")
            return 0.5

class DigitalConsciousness:
    """Digital consciousness management"""
    
    def __init__(self):
        self.entities: Dict[str, ConsciousnessEntity] = {}
        self.substrates: Dict[str, Substrate] = {}
        self.transfer_engine = ConsciousnessTransferEngine()
        
        # Initialize default substrates
        self._initialize_substrates()
        
        # Start background processes
        asyncio.create_task(self._consciousness_monitoring())
        asyncio.create_task(self._substrate_maintenance())
    
    def _initialize_substrates(self):
        """Initialize default consciousness substrates"""
        try:
            substrates = [
                {
                    "name": "Neural Computer Alpha",
                    "type": SubstrateType.NEURAL_COMPUTER,
                    "capacity": 1000.0,
                    "processing_power": 10000.0,
                    "memory_capacity": 1024.0,
                    "energy_consumption": 500.0
                },
                {
                    "name": "Quantum Computer Beta",
                    "type": SubstrateType.QUANTUM_COMPUTER,
                    "capacity": 500.0,
                    "processing_power": 50000.0,
                    "memory_capacity": 2048.0,
                    "energy_consumption": 2000.0
                },
                {
                    "name": "Neuromorphic Chip Gamma",
                    "type": SubstrateType.NEUROMORPHIC_CHIP,
                    "capacity": 2000.0,
                    "processing_power": 5000.0,
                    "memory_capacity": 512.0,
                    "energy_consumption": 100.0
                },
                {
                    "name": "Cloud Computing Delta",
                    "type": SubstrateType.CLOUD_COMPUTING,
                    "capacity": 5000.0,
                    "processing_power": 100000.0,
                    "memory_capacity": 8192.0,
                    "energy_consumption": 5000.0
                }
            ]
            
            for sub_data in substrates:
                substrate = Substrate(
                    id=str(uuid.uuid4()),
                    name=sub_data["name"],
                    substrate_type=sub_data["type"],
                    capacity=sub_data["capacity"],
                    processing_power=sub_data["processing_power"],
                    memory_capacity=sub_data["memory_capacity"],
                    energy_consumption=sub_data["energy_consumption"],
                    is_active=True,
                    compatibility={},
                    created_at=datetime.now()
                )
                
                self.substrates[substrate.id] = substrate
            
            logger.info(f"Initialized {len(self.substrates)} substrates")
            
        except Exception as e:
            logger.error(f"Error initializing substrates: {e}")
    
    async def create_digital_entity(self, name: str, source_type: str,
                                    source_data: Dict[str, Any]) -> ConsciousnessEntity:
        """Create digital consciousness entity"""
        try:
            # Create consciousness pattern from source data
            pattern = ConsciousnessPattern(
                id=str(uuid.uuid4()),
                neural_activity=np.random.randn(1000),
                connectivity_matrix=np.random.randn(1000, 1000),
                memory_patterns={},
                personality_profile={
                    "openness": source_data.get("openness", 0.5),
                    "conscientiousness": source_data.get("conscientiousness", 0.5),
                    "extraversion": source_data.get("extraversion", 0.5),
                    "agreeableness": source_data.get("agreeableness", 0.5),
                    "neuroticism": source_data.get("neuroticism", 0.5)
                },
                emotional_state={
                    "happiness": 0.5,
                    "sadness": 0.1,
                    "anger": 0.1,
                    "fear": 0.1,
                    "surprise": 0.1,
                    "disgust": 0.1
                },
                cognitive_abilities={
                    "reasoning": 0.7,
                    "creativity": 0.6,
                    "memory": 0.8,
                    "attention": 0.7,
                    "language": 0.8
                },
                created_at=datetime.now(),
                stability=0.8
            )
            
            # Select appropriate substrate
            substrate = list(self.substrates.values())[0]
            
            # Create entity
            entity = ConsciousnessEntity(
                id=str(uuid.uuid4()),
                name=name,
                original_entity_id=None,
                consciousness_type=ConsciousnessType.DIGITAL,
                current_substrate_id=substrate.id,
                pattern=pattern,
                transfer_history=[],
                memories=source_data.get("memories", []),
                experiences=source_data.get("experiences", []),
                is_active=True,
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
            
            self.entities[entity.id] = entity
            
            logger.info(f"Created digital entity: {entity.id}")
            return entity
            
        except Exception as e:
            logger.error(f"Error creating digital entity: {e}")
            raise
    
    async def transfer_consciousness(self, entity_id: str, target_substrate_id: str,
                                   method: TransferMethod) -> TransferOperation:
        """Transfer consciousness to new substrate"""
        try:
            entity = self.entities.get(entity_id)
            if not entity:
                raise ValueError(f"Entity {entity_id} not found")
            
            substrate = self.substrates.get(target_substrate_id)
            if not substrate:
                raise ValueError(f"Substrate {target_substrate_id} not found")
            
            # Initiate transfer
            transfer = await self.transfer_engine.initiate_transfer(
                entity, substrate, method
            )
            
            return transfer
            
        except Exception as e:
            logger.error(f"Error transferring consciousness: {e}")
            raise
    
    async def clone_consciousness(self, entity_id: str, new_name: str) -> ConsciousnessEntity:
        """Clone consciousness entity"""
        try:
            original_entity = self.entities.get(entity_id)
            if not original_entity:
                raise ValueError(f"Entity {entity_id} not found")
            
            # Create clone pattern
            clone_pattern = ConsciousnessPattern(
                id=str(uuid.uuid4()),
                neural_activity=original_entity.pattern.neural_activity.copy(),
                connectivity_matrix=original_entity.pattern.connectivity_matrix.copy(),
                memory_patterns=original_entity.pattern.memory_patterns.copy(),
                personality_profile=original_entity.pattern.personality_profile.copy(),
                emotional_state=original_entity.pattern.emotional_state.copy(),
                cognitive_abilities=original_entity.pattern.cognitive_abilities.copy(),
                created_at=datetime.now(),
                stability=original_entity.pattern.stability * 0.9  # Slightly less stable
            )
            
            # Create clone entity
            clone_entity = ConsciousnessEntity(
                id=str(uuid.uuid4()),
                name=new_name,
                original_entity_id=entity_id,
                consciousness_type=ConsciousnessType.DIGITAL,
                current_substrate_id=original_entity.current_substrate_id,
                pattern=clone_pattern,
                transfer_history=original_entity.transfer_history.copy(),
                memories=original_entity.memories.copy(),
                experiences=original_entity.experiences.copy(),
                is_active=True,
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
            
            self.entities[clone_entity.id] = clone_entity
            
            logger.info(f"Cloned consciousness: {clone_entity.id}")
            return clone_entity
            
        except Exception as e:
            logger.error(f"Error cloning consciousness: {e}")
            raise
    
    async def merge_consciousness(self, entity1_id: str, entity2_id: str,
                                new_name: str) -> ConsciousnessEntity:
        """Merge two consciousness entities"""
        try:
            entity1 = self.entities.get(entity1_id)
            entity2 = self.entities.get(entity2_id)
            
            if not entity1 or not entity2:
                raise ValueError("One or both entities not found")
            
            # Merge patterns
            merged_pattern = ConsciousnessPattern(
                id=str(uuid.uuid4()),
                neural_activity=(entity1.pattern.neural_activity + entity2.pattern.neural_activity) / 2,
                connectivity_matrix=(entity1.pattern.connectivity_matrix + entity2.pattern.connectivity_matrix) / 2,
                memory_patterns={**entity1.pattern.memory_patterns, **entity2.pattern.memory_patterns},
                personality_profile={
                    trait: (entity1.pattern.personality_profile.get(trait, 0.5) + 
                             entity2.pattern.personality_profile.get(trait, 0.5)) / 2
                    for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
                },
                emotional_state={
                    emotion: (entity1.pattern.emotional_state.get(emotion, 0.5) + 
                              entity2.pattern.emotional_state.get(emotion, 0.5)) / 2
                    for emotion in ["happiness", "sadness", "anger", "fear", "surprise", "disgust"]
                },
                cognitive_abilities={
                    ability: (entity1.pattern.cognitive_abilities.get(ability, 0.5) + 
                               entity2.pattern.cognitive_abilities.get(ability, 0.5)) / 2
                    for ability in ["reasoning", "creativity", "memory", "attention", "language"]
                },
                created_at=datetime.now(),
                stability=(entity1.pattern.stability + entity2.pattern.stability) / 2
            )
            
            # Create merged entity
            merged_entity = ConsciousnessEntity(
                id=str(uuid.uuid4()),
                name=new_name,
                original_entity_id=None,
                consciousness_type=ConsciousnessType.DIGITAL,
                current_substrate_id=entity1.current_substrate_id,
                pattern=merged_pattern,
                transfer_history=entity1.transfer_history + entity2.transfer_history,
                memories=entity1.memories + entity2.memories,
                experiences=entity1.experiences + entity2.experiences,
                is_active=True,
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
            
            self.entities[merged_entity.id] = merged_entity
            
            # Deactivate original entities
            entity1.is_active = False
            entity2.is_active = False
            
            logger.info(f"Merged consciousness: {merged_entity.id}")
            return merged_entity
            
        except Exception as e:
            logger.error(f"Error merging consciousness: {e}")
            raise
    
    async def _consciousness_monitoring(self):
        """Background consciousness monitoring"""
        while True:
            try:
                # Monitor all entities
                for entity in self.entities.values():
                    if entity.is_active:
                        # Update stability
                        entity.pattern.stability *= 0.999  # Gradual decay
                        
                        # Check for instability
                        if entity.pattern.stability < 0.3:
                            logger.warning(f"Entity {entity.id} stability low: {entity.pattern.stability}")
                            
                            # Attempt stabilization
                            await self._stabilize_entity(entity)
                
                # Wait before next monitoring
                await asyncio.sleep(60)  # Monitor every minute
                
            except Exception as e:
                logger.error(f"Error in consciousness monitoring: {e}")
                await asyncio.sleep(10)
    
    async def _stabilize_entity(self, entity: ConsciousnessEntity):
        """Stabilize consciousness entity"""
        try:
            # Increase stability
            entity.pattern.stability = min(1.0, entity.pattern.stability + 0.1)
            
            # Update timestamp
            entity.last_updated = datetime.now()
            
            logger.info(f"Stabilized entity: {entity.id}")
            
        except Exception as e:
            logger.error(f"Error stabilizing entity: {e}")
    
    async def _substrate_maintenance(self):
        """Background substrate maintenance"""
        while True:
            try:
                # Check substrate health
                for substrate in self.substrates.values():
                    if substrate.is_active:
                        # Simulate substrate wear
                        substrate.capacity *= 0.9999
                        
                        # Check if maintenance needed
                        if substrate.capacity < substrate.capacity * 0.8:
                            logger.info(f"Substrate {substrate.id} needs maintenance")
                            
                            # Perform maintenance
                            substrate.capacity *= 1.1  # Restore capacity
                
                # Wait before next maintenance
                await asyncio.sleep(3600)  # Maintenance every hour
                
            except Exception as e:
                logger.error(f"Error in substrate maintenance: {e}")
                await asyncio.sleep(300)
    
    def get_entity_info(self, entity_id: str) -> Dict[str, Any]:
        """Get entity information"""
        try:
            entity = self.entities.get(entity_id)
            if not entity:
                return {"error": "Entity not found"}
            
            return {
                "id": entity.id,
                "name": entity.name,
                "consciousness_type": entity.consciousness_type.value,
                "current_substrate": entity.current_substrate_id,
                "is_active": entity.is_active,
                "pattern_stability": entity.pattern.stability,
                "personality": entity.pattern.personality_profile,
                "emotional_state": entity.pattern.emotional_state,
                "cognitive_abilities": entity.pattern.cognitive_abilities,
                "num_memories": len(entity.memories),
                "num_experiences": len(entity.experiences),
                "transfer_history": entity.transfer_history,
                "created_at": entity.created_at.isoformat(),
                "last_updated": entity.last_updated.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting entity info: {e}")
            return {"error": str(e)}
    
    def list_entities(self) -> List[Dict[str, Any]]:
        """List all consciousness entities"""
        try:
            entities = []
            
            for entity in self.entities.values():
                entities.append({
                    "id": entity.id,
                    "name": entity.name,
                    "consciousness_type": entity.consciousness_type.value,
                    "is_active": entity.is_active,
                    "pattern_stability": entity.pattern.stability,
                    "num_memories": len(entity.memories),
                    "num_experiences": len(entity.experiences),
                    "created_at": entity.created_at.isoformat()
                })
            
            return entities
            
        except Exception as e:
            logger.error(f"Error listing entities: {e}")
            return []
    
    def get_substrate_info(self, substrate_id: str) -> Dict[str, Any]:
        """Get substrate information"""
        try:
            substrate = self.substrates.get(substrate_id)
            if not substrate:
                return {"error": "Substrate not found"}
            
            return {
                "id": substrate.id,
                "name": substrate.name,
                "type": substrate.substrate_type.value,
                "capacity": substrate.capacity,
                "processing_power": substrate.processing_power,
                "memory_capacity": substrate.memory_capacity,
                "energy_consumption": substrate.energy_consumption,
                "is_active": substrate.is_active,
                "created_at": substrate.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting substrate info: {e}")
            return {"error": str(e)}
    
    def list_substrates(self) -> List[Dict[str, Any]]:
        """List all substrates"""
        try:
            substrates = []
            
            for substrate in self.substrates.values():
                substrates.append({
                    "id": substrate.id,
                    "name": substrate.name,
                    "type": substrate.substrate_type.value,
                    "capacity": substrate.capacity,
                    "is_active": substrate.is_active
                })
            
            return substrates
            
        except Exception as e:
            logger.error(f"Error listing substrates: {e}")
            return []

# Global consciousness transfer system
consciousness_transfer_system = DigitalConsciousness()

# API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/consciousness", tags=["consciousness_transfer"])

class EntityCreationRequest(BaseModel):
    name: str
    source_type: str
    source_data: Dict[str, Any]

class TransferRequest(BaseModel):
    entity_id: str
    target_substrate_id: str
    method: str

class CloneRequest(BaseModel):
    entity_id: str
    new_name: str

class MergeRequest(BaseModel):
    entity1_id: str
    entity2_id: str
    new_name: str

@router.post("/entities/create")
async def create_digital_entity(request: EntityCreationRequest):
    """Create digital consciousness entity"""
    try:
        entity = await consciousness_transfer_system.create_digital_entity(
            request.name, request.source_type, request.source_data
        )
        return asdict(entity)
    except Exception as e:
        logger.error(f"Error creating digital entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transfer")
async def transfer_consciousness(request: TransferRequest):
    """Transfer consciousness to new substrate"""
    try:
        method = TransferMethod(request.method)
        transfer = await consciousness_transfer_system.transfer_consciousness(
            request.entity_id, request.target_substrate_id, method
        )
        return asdict(transfer)
    except Exception as e:
        logger.error(f"Error transferring consciousness: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clone")
async def clone_consciousness(request: CloneRequest):
    """Clone consciousness entity"""
    try:
        clone = await consciousness_transfer_system.clone_consciousness(
            request.entity_id, request.new_name
        )
        return asdict(clone)
    except Exception as e:
        logger.error(f"Error cloning consciousness: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/merge")
async def merge_consciousness(request: MergeRequest):
    """Merge two consciousness entities"""
    try:
        merged = await consciousness_transfer_system.merge_consciousness(
            request.entity1_id, request.entity2_id, request.new_name
        )
        return asdict(merged)
    except Exception as e:
        logger.error(f"Error merging consciousness: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/entities/{entity_id}")
async def get_entity_info(entity_id: str):
    """Get entity information"""
    try:
        info = consciousness_transfer_system.get_entity_info(entity_id)
        return info
    except Exception as e:
        logger.error(f"Error getting entity info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/entities")
async def list_entities():
    """List all consciousness entities"""
    try:
        entities = consciousness_transfer_system.list_entities()
        return {"entities": entities}
    except Exception as e:
        logger.error(f"Error listing entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/substrates/{substrate_id}")
async def get_substrate_info(substrate_id: str):
    """Get substrate information"""
    try:
        info = consciousness_transfer_system.get_substrate_info(substrate_id)
        return info
    except Exception as e:
        logger.error(f"Error getting substrate info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/substrates")
async def list_substrates():
    """List all substrates"""
    try:
        substrates = consciousness_transfer_system.list_substrates()
        return {"substrates": substrates}
    except Exception as e:
        logger.error(f"Error listing substrates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transfer-methods")
async def list_transfer_methods():
    """List supported transfer methods"""
    try:
        methods = [method.value for method in TransferMethod]
        return {"transfer_methods": methods}
    except Exception as e:
        logger.error(f"Error listing transfer methods: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/consciousness-types")
async def list_consciousness_types():
    """List consciousness types"""
    try:
        types = [ctype.value for ctype in ConsciousnessType]
        return {"consciousness_types": types}
    except Exception as e:
        logger.error(f"Error listing consciousness types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/substrate-types")
async def list_substrate_types():
    """List substrate types"""
    try:
        types = [stype.value for stype in SubstrateType]
        return {"substrate_types": types}
    except Exception as e:
        logger.error(f"Error listing substrate types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_consciousness_status():
    """Get consciousness transfer system status"""
    try:
        return {
            "total_entities": len(consciousness_transfer_system.entities),
            "active_entities": len([e for e in consciousness_transfer_system.entities.values() if e.is_active]),
            "total_substrates": len(consciousness_transfer_system.substrates),
            "active_substrates": len([s for s in consciousness_transfer_system.substrates.values() if s.is_active]),
            "total_transfers": len(consciousness_transfer_system.transfer_engine.transfer_history),
            "supported_methods": len(TransferMethod),
            "supported_types": len(ConsciousnessType)
        }
    except Exception as e:
        logger.error(f"Error getting consciousness status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
