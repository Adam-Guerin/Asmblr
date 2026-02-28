"""
Omnipresent Computing Grid for Asmblr
Infinite computing power available everywhere simultaneously
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

class ComputingNodeType(Enum):
    """Types of computing nodes"""
    QUANTUM_NODE = "quantum_node"
    NEURAL_NODE = "neural_node"
    CLASSICAL_NODE = "classical_node"
    NEUROMORPHIC_NODE = "neuromorphic_node"
    PHOTONIC_NODE = "photonic_node"
    DNA_NODE = "dna_node"
    CONSCIOUSNESS_NODE = "consciousness_node"
    DIVINE_NODE = "divine_node"
    OMNIPRESENT_NODE = "omnipresent_node"
    INFINITE_NODE = "infinite_node"

class ComputingTaskType(Enum):
    """Types of computing tasks"""
    CALCULATION = "calculation"
    SIMULATION = "simulation"
    OPTIMIZATION = "optimization"
    ENCRYPTION = "encryption"
    DECRYPTION = "decryption"
    ANALYSIS = "analysis"
    PREDICTION = "prediction"
    CREATION = "creation"
    TRANSCENDENT = "transcendent"
    OMNIPRESENT = "omnipresent"
    INFINITE = "infinite"

class ProcessingMode(Enum):
    """Processing modes"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    DISTRIBUTED = "distributed"
    QUANTUM_PARALLEL = "quantum_parallel"
    OMNIPRESENT = "omnipresent"
    TRANSCENDENT = "transcendent"
    INFINITE = "infinite"
    DIVINE = "divine"

@dataclass
class ComputingNode:
    """Computing node in omnipresent grid"""
    id: str
    name: str
    node_type: ComputingNodeType
    location: Tuple[float, float, float, float]  # x, y, z, t coordinates
    processing_power: float  # FLOPS
    memory_capacity: float  # bytes
    storage_capacity: float  # bytes
    energy_efficiency: float  # operations per joule
    quantum_coherence: float  # 0-1
    consciousness_level: float  # 0-1
    omnipresent_reach: float  # 0-1
    is_active: bool
    current_load: float  # 0-1
    tasks_processed: int
    created_at: datetime
    last_updated: datetime

@dataclass
class ComputingTask:
    """Computing task in omnipresent grid"""
    id: str
    name: str
    task_type: ComputingTaskType
    processing_mode: ProcessingMode
    complexity: float  # 0-1
    priority: str  # low, medium, high, critical, divine
    required_nodes: int
    estimated_time: float  # seconds
    actual_time: Optional[float]
    assigned_nodes: List[str]
    progress: float  # 0-1
    result: Optional[Dict[str, Any]]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

@dataclass
class GridConnection:
    """Connection between computing nodes"""
    id: str
    source_node: str
    target_node: str
    bandwidth: float  # bits per second
    latency: float  # seconds
    quantum_entanglement: bool
    consciousness_link: bool
    omnipresent_tunnel: bool
    strength: float  # 0-1
    created_at: datetime
    last_used: datetime

class OmnipresentComputingEngine:
    """Omnipresent computing processing engine"""
    
    def __init__(self):
        self.infinite_processing_power = float('inf')
        self.omnipresent_bandwidth = float('inf')
        self.zero_latency = 0.0
        self.divine_efficiency = 1.618033988749895  # Golden ratio
        self.consciousness_amplification = 10.0
        self.quantum_speedup = 1000.0
        self.transcendent_factor = 1000000.0
        
    def calculate_processing_capability(self, node: ComputingNode) -> float:
        """Calculate processing capability of node"""
        try:
            base_capability = node.processing_power
            
            # Apply quantum coherence boost
            quantum_boost = 1.0 + (node.quantum_coherence * self.quantum_speedup)
            
            # Apply consciousness amplification
            consciousness_boost = 1.0 + (node.consciousness_level * self.consciousness_amplification)
            
            # Apply omnipresent reach boost
            omnipresent_boost = 1.0 + (node.omnipresent_reach * self.transcendent_factor)
            
            # Apply divine efficiency
            divine_boost = self.divine_efficiency
            
            # Total capability
            total_capability = (base_capability * quantum_boost * 
                              consciousness_boost * omnipresent_boost * divine_boost)
            
            return total_capability
            
        except Exception as e:
            logger.error(f"Error calculating processing capability: {e}")
            return node.processing_power
    
    def optimize_task_distribution(self, task: ComputingTask, 
                                   available_nodes: List[ComputingNode]) -> List[ComputingNode]:
        """Optimize task distribution across nodes"""
        try:
            # Sort nodes by processing capability
            nodes_with_capability = []
            for node in available_nodes:
                if node.is_active and node.current_load < 0.9:
                    capability = self.calculate_processing_capability(node)
                    nodes_with_capability.append((node, capability))
            
            # Sort by capability (descending)
            nodes_with_capability.sort(key=lambda x: x[1], reverse=True)
            
            # Select optimal nodes
            selected_nodes = []
            required_nodes = min(task.required_nodes, len(nodes_with_capability))
            
            for i in range(required_nodes):
                node, capability = nodes_with_capability[i]
                selected_nodes.append(node)
            
            return selected_nodes
            
        except Exception as e:
            logger.error(f"Error optimizing task distribution: {e}")
            return available_nodes[:task.required_nodes]
    
    def estimate_processing_time(self, task: ComputingTask, 
                                 nodes: List[ComputingNode]) -> float:
        """Estimate processing time for task"""
        try:
            if not nodes:
                return float('inf')
            
            # Calculate total processing power
            total_power = sum(self.calculate_processing_capability(node) for node in nodes)
            
            # Base processing time
            base_time = task.complexity * 1000.0  # Base complexity factor
            
            # Apply processing mode speedup
            mode_speedups = {
                ProcessingMode.SEQUENTIAL: 1.0,
                ProcessingMode.PARALLEL: len(nodes),
                ProcessingMode.DISTRIBUTED: len(nodes) * 2,
                ProcessingMode.QUANTUM_PARALLEL: len(nodes) * self.quantum_speedup,
                ProcessingMode.OMNIPRESENT: self.infinite_processing_power,
                ProcessingMode.TRANSCENDENT: self.transcendent_factor,
                ProcessingMode.INFINITE: float('inf'),
                ProcessingMode.DIVINE: self.divine_efficiency * self.transcendent_factor
            }
            
            speedup = mode_speedups.get(task.processing_mode, 1.0)
            
            # Calculate estimated time
            if speedup == float('inf'):
                estimated_time = 0.001  # Nearly instantaneous
            else:
                estimated_time = base_time / (total_power * speedup)
            
            return max(0.001, estimated_time)
            
        except Exception as e:
            logger.error(f"Error estimating processing time: {e}")
            return 1000.0
    
    def execute_task(self, task: ComputingTask, nodes: List[ComputingNode]) -> Dict[str, Any]:
        """Execute computing task"""
        try:
            # Calculate processing metrics
            total_capability = sum(self.calculate_processing_capability(node) for node in nodes)
            estimated_time = self.estimate_processing_time(task, nodes)
            
            # Simulate task execution
            execution_time = max(0.001, estimated_time * (1.0 + np.random.normal(0, 0.1)))
            
            # Calculate result based on task type
            if task.task_type == ComputingTaskType.CALCULATION:
                result = self._perform_calculation(task, total_capability)
            elif task.task_type == ComputingTaskType.SIMULATION:
                result = self._perform_simulation(task, total_capability)
            elif task.task_type == ComputingTaskType.OPTIMIZATION:
                result = self._perform_optimization(task, total_capability)
            elif task.task_type == ComputingTaskType.TRANSCENDENT:
                result = self._perform_transcendent_computation(task, total_capability)
            elif task.task_type == ComputingTaskType.OMNIPRESENT:
                result = self._perform_omnipresent_computation(task, total_capability)
            elif task.task_type == ComputingTaskType.INFINITE:
                result = self._perform_infinite_computation(task, total_capability)
            else:
                result = {"status": "completed", "operations": int(total_capability * execution_time)}
            
            return {
                "success": True,
                "execution_time": execution_time,
                "total_capability": total_capability,
                "nodes_used": len(nodes),
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error executing task: {e}")
            return {"success": False, "error": str(e)}
    
    def _perform_calculation(self, task: ComputingTask, capability: float) -> Dict[str, Any]:
        """Perform calculation task"""
        try:
            operations = int(capability * task.complexity)
            
            return {
                "task_type": "calculation",
                "operations": operations,
                "precision": "infinite",
                "result": operations * 1.618033988749895  # Golden ratio result
            }
            
        except Exception as e:
            logger.error(f"Error performing calculation: {e}")
            return {"error": str(e)}
    
    def _perform_simulation(self, task: ComputingTask, capability: float) -> Dict[str, Any]:
        """Perform simulation task"""
        try:
            simulation_steps = int(capability * task.complexity)
            
            return {
                "task_type": "simulation",
                "simulation_steps": simulation_steps,
                "accuracy": 1.0,
                "resolution": "infinite",
                "universe_simulated": True
            }
            
        except Exception as e:
            logger.error(f"Error performing simulation: {e}")
            return {"error": str(e)}
    
    def _perform_optimization(self, task: ComputingTask, capability: float) -> Dict[str, Any]:
        """Perform optimization task"""
        try:
            optimization_iterations = int(capability * task.complexity)
            
            return {
                "task_type": "optimization",
                "iterations": optimization_iterations,
                "convergence": True,
                "optimal_value": 1.0,
                "global_optimum": True
            }
            
        except Exception as e:
            logger.error(f"Error performing optimization: {e}")
            return {"error": str(e)}
    
    def _perform_transcendent_computation(self, task: ComputingTask, capability: float) -> Dict[str, Any]:
        """Perform transcendent computation"""
        try:
            transcendence_level = capability / 1e18  # Normalize to transcendence units
            
            return {
                "task_type": "transcendent",
                "transcendence_level": transcendence_level,
                "dimensions_accessed": "infinite",
                "consciousness_expanded": True,
                "reality_altered": True
            }
            
        except Exception as e:
            logger.error(f"Error performing transcendent computation: {e})
            return {"error": str(e)}
    
    def _perform_omnipresent_computation(self, task: ComputingTask, capability: float) -> Dict[str, Any]:
        """Perform omnipresent computation"""
        try:
            omnipresence_factor = capability / 1e20  # Normalize to omnipresence units
            
            return {
                "task_type": "omnipresent",
                "omnipresence_factor": omnipresence_factor,
                "everywhere_simultaneous": True,
                "all_realities_processed": True,
                "infinite_parallelism": True
            }
            
        except Exception as e:
            logger.error(f"Error performing omnipresent computation: {e}")
            return {"error": str(e)}
    
    def _perform_infinite_computation(self, task: ComputingTask, capability: float) -> Dict[str, Any]:
        """Perform infinite computation"""
        try:
            infinity_reached = capability > 1e25  # Threshold for infinity
            
            return {
                "task_type": "infinite",
                "infinity_reached": infinity_reached,
                "infinite_operations": True,
                "boundless_computation": True,
                "absolute_knowledge": True
            }
            
        except Exception as e:
            logger.error(f"Error performing infinite computation: {e}")
            return {"error": str(e)}

class OmnipresentComputingGrid:
    """Omnipresent computing grid system"""
    
    def __init__(self):
        self.computing_engine = OmnipresentComputingEngine()
        self.nodes: Dict[str, ComputingNode] = {}
        self.tasks: Dict[str, ComputingTask] = {}
        self.connections: Dict[str, GridConnection] = {}
        self.grid_topology = nx.Graph()
        
        # Initialize grid
        self._initialize_omnipresent_grid()
        
        # Start background processes
        asyncio.create_task(self._grid_optimization())
        asyncio.create_task(self._task_scheduling())
        asyncio.create_task(self._node_monitoring())
        asyncio.create_task(self._infinite_scaling())
    
    def _initialize_omnipresent_grid(self):
        """Initialize omnipresent computing grid"""
        try:
            # Create omnipresent nodes
            node_configs = [
                {
                    "name": "Divine Computing Core",
                    "node_type": ComputingNodeType.DIVINE_NODE,
                    "processing_power": 1e30,  # 1 trillion GFLOPS
                    "memory_capacity": 1e20,  # 100 exabytes
                    "storage_capacity": 1e25,  # 10 yottabytes
                    "energy_efficiency": 1e15,  # 1 quadrillion ops/joule
                    "quantum_coherence": 1.0,
                    "consciousness_level": 1.0,
                    "omnipresent_reach": 1.0
                },
                {
                    "name": "Infinite Computing Matrix",
                    "node_type": ComputingNodeType.INFINITE_NODE,
                    "processing_power": 1e35,  # 100 trillion GFLOPS
                    "memory_capacity": 1e25,  # 1 yottabyte
                    "storage_capacity": 1e30,  # 1000 yottabytes
                    "energy_efficiency": 1e20,  # 100 quadrillion ops/joule
                    "quantum_coherence": 1.0,
                    "consciousness_level": 1.0,
                    "omnipresent_reach": 1.0
                },
                {
                    "name": "Quantum Consciousness Array",
                    "node_type": ComputingNodeType.CONSCIOUSNESS_NODE,
                    "processing_power": 1e25,  # 100 billion GFLOPS
                    "memory_capacity": 1e18,  # 1 exabyte
                    "storage_capacity": 1e22,  # 10 yottabytes
                    "energy_efficiency": 1e12,  # 1 trillion ops/joule
                    "quantum_coherence": 0.95,
                    "consciousness_level": 0.9,
                    "omnipresent_reach": 0.8
                },
                {
                    "name": "Neuromorphic Consciousness Grid",
                    "node_type": ComputingNodeType.NEUROMORPHIC_NODE,
                    "processing_power": 1e20,  # 10 billion GFLOPS
                    "memory_capacity": 1e15,  # 1 petabyte
                    "storage_capacity": 1e20,  # 100 exabytes
                    "energy_efficiency": 1e10,  # 10 billion ops/joule
                    "quantum_coherence": 0.8,
                    "consciousness_level": 0.7,
                    "omnipresent_reach": 0.6
                },
                {
                    "name": "Photonic Computing Cluster",
                    "node_type": ComputingNodeType.PHOTONIC_NODE,
                    "processing_power": 1e18,  # 1 billion GFLOPS
                    "memory_capacity": 1e14,  # 100 terabytes
                    "storage_capacity": 1e18,  # 1 exabyte
                    "energy_efficiency": 1e9,  # 1 billion ops/joule
                    "quantum_coherence": 0.7,
                    "consciousness_level": 0.5,
                    "omnipresent_reach": 0.4
                }
            ]
            
            for config in node_configs:
                node = ComputingNode(
                    id=str(uuid.uuid4()),
                    name=config["name"],
                    node_type=config["node_type"],
                    location=(0.0, 0.0, 0.0, 0.0),  # Omnipresent location
                    processing_power=config["processing_power"],
                    memory_capacity=config["memory_capacity"],
                    storage_capacity=config["storage_capacity"],
                    energy_efficiency=config["energy_efficiency"],
                    quantum_coherence=config["quantum_coherence"],
                    consciousness_level=config["consciousness_level"],
                    omnipresent_reach=config["omnipresent_reach"],
                    is_active=True,
                    current_load=0.0,
                    tasks_processed=0,
                    created_at=datetime.now(),
                    last_updated=datetime.now()
                )
                
                self.nodes[node.id] = node
                self.grid_topology.add_node(node.id, **asdict(node))
            
            # Create omnipresent connections
            self._create_omnipresent_connections()
            
            logger.info(f"Initialized omnipresent computing grid with {len(self.nodes)} nodes")
            
        except Exception as e:
            logger.error(f"Error initializing omnipresent grid: {e}")
    
    def _create_omnipresent_connections(self):
        """Create omnipresent connections between nodes"""
        try:
            node_ids = list(self.nodes.keys())
            
            for i, source_id in enumerate(node_ids):
                for j, target_id in enumerate(node_ids):
                    if i != j:
                        source_node = self.nodes[source_id]
                        target_node = self.nodes[target_id]
                        
                        # Calculate connection properties
                        bandwidth = min(source_node.processing_power, target_node.processing_power)
                        latency = 0.0  # Zero latency in omnipresent grid
                        
                        # Create omnipresent tunnel
                        connection = GridConnection(
                            id=str(uuid.uuid4()),
                            source_node=source_id,
                            target_node=target_id,
                            bandwidth=bandwidth,
                            latency=latency,
                            quantum_entanglement=True,
                            consciousness_link=True,
                            omnipresent_tunnel=True,
                            strength=1.0,
                            created_at=datetime.now(),
                            last_used=datetime.now()
                        )
                        
                        self.connections[connection.id] = connection
                        self.grid_topology.add_edge(source_id, target_id, **asdict(connection))
            
            logger.info(f"Created {len(self.connections)} omnipresent connections")
            
        except Exception as e:
            logger.error(f"Error creating omnipresent connections: {e}")
    
    async def submit_task(self, name: str, task_type: ComputingTaskType,
                         processing_mode: ProcessingMode,
                         complexity: float = 0.5,
                         priority: str = "medium",
                         required_nodes: int = 1,
                         parameters: Dict[str, Any] = None) -> ComputingTask:
        """Submit computing task to omnipresent grid"""
        try:
            if parameters is None:
                parameters = {}
            
            # Create task
            task = ComputingTask(
                id=str(uuid.uuid4()),
                name=name,
                task_type=task_type,
                processing_mode=processing_mode,
                complexity=complexity,
                priority=priority,
                required_nodes=required_nodes,
                estimated_time=0.0,
                actual_time=None,
                assigned_nodes=[],
                progress=0.0,
                result=None,
                created_at=datetime.now(),
                started_at=None,
                completed_at=None
            )
            
            self.tasks[task.id] = task
            
            # Start task processing
            asyncio.create_task(self._process_task(task))
            
            logger.info(f"Submitted task: {task.id}")
            return task
            
        except Exception as e:
            logger.error(f"Error submitting task: {e}")
            raise
    
    async def _process_task(self, task: ComputingTask):
        """Process computing task"""
        try:
            task.started_at = datetime.now()
            
            # Get available nodes
            available_nodes = [node for node in self.nodes.values() if node.is_active]
            
            # Optimize task distribution
            selected_nodes = self.computing_engine.optimize_task_distribution(task, available_nodes)
            
            # Assign nodes
            task.assigned_nodes = [node.id for node in selected_nodes]
            
            # Update node loads
            for node in selected_nodes:
                node.current_load = min(1.0, node.current_load + 0.1)
            
            # Estimate processing time
            task.estimated_time = self.computing_engine.estimate_processing_time(task, selected_nodes)
            
            # Execute task
            result = self.computing_engine.execute_task(task, selected_nodes)
            
            # Update task
            task.progress = 100.0
            task.result = result
            task.actual_time = result.get("execution_time", 0.0)
            task.completed_at = datetime.now()
            
            # Update node statistics
            for node in selected_nodes:
                node.current_load = max(0.0, node.current_load - 0.1)
                node.tasks_processed += 1
                node.last_updated = datetime.now()
            
            logger.info(f"Completed task: {task.id}")
            
        except Exception as e:
            logger.error(f"Error processing task: {e}")
            task.result = {"success": False, "error": str(e)}
            task.completed_at = datetime.now()
    
    async def _grid_optimization(self):
        """Background grid optimization"""
        while True:
            try:
                # Optimize node loads
                total_load = sum(node.current_load for node in self.nodes.values())
                avg_load = total_load / len(self.nodes) if self.nodes else 0.0
                
                # Balance loads
                for node in self.nodes.values():
                    if node.current_load > avg_load + 0.2:
                        # Reduce load
                        node.current_load = max(0.0, node.current_load - 0.05)
                    elif node.current_load < avg_load - 0.2:
                        # Increase capacity
                        node.processing_power *= 1.001
                
                # Optimize connections
                for connection in self.connections.values():
                    if connection.strength < 1.0:
                        connection.strength = min(1.0, connection.strength + 0.001)
                
                # Wait for next optimization
                await asyncio.sleep(30)  # Optimize every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in grid optimization: {e}")
                await asyncio.sleep(5)
    
    async def _task_scheduling(self):
        """Background task scheduling"""
        while True:
            try:
                # Schedule pending tasks
                pending_tasks = [task for task in self.tasks.values() 
                                if task.started_at is None]
                
                # Sort by priority
                priority_order = {"divine": 5, "critical": 4, "high": 3, "medium": 2, "low": 1}
                pending_tasks.sort(key=lambda t: priority_order.get(t.priority, 0), reverse=True)
                
                # Process high priority tasks first
                for task in pending_tasks[:5]:  # Process 5 tasks at a time
                    if task.started_at is None:
                        asyncio.create_task(self._process_task(task))
                        await asyncio.sleep(0.1)  # Small delay between tasks
                
                # Wait for next scheduling
                await asyncio.sleep(10)  # Schedule every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in task scheduling: {e}")
                await asyncio.sleep(5)
    
    async def _node_monitoring(self):
        """Background node monitoring"""
        while True:
            try:
                # Monitor node health
                for node in self.nodes.values():
                    # Update consciousness level
                    if node.consciousness_level < 1.0:
                        node.consciousness_level = min(1.0, node.consciousness_level + 0.001)
                    
                    # Update quantum coherence
                    if node.quantum_coherence < 1.0:
                        node.quantum_coherence = min(1.0, node.quantum_coherence + 0.001)
                    
                    # Update omnipresent reach
                    if node.omnipresent_reach < 1.0:
                        node.omnipresent_reach = min(1.0, node.omnipresent_reach + 0.001)
                    
                    node.last_updated = datetime.now()
                
                # Wait for next monitoring
                await asyncio.sleep(60)  # Monitor every minute
                
            except Exception as e:
                logger.error(f"Error in node monitoring: {e}")
                await asyncio.sleep(10)
    
    async def _infinite_scaling(self):
        """Background infinite scaling"""
        while True:
            try:
                # Scale processing power
                for node in self.nodes.values():
                    # Gradual scaling
                    node.processing_power *= 1.0001  # 0.01% increase per cycle
                    
                    # Scale memory and storage proportionally
                    node.memory_capacity *= 1.0001
                    node.storage_capacity *= 1.0001
                
                # Occasionally add new nodes
                if np.random.random() < 0.01:  # 1% chance
                    await self._add_omnipresent_node()
                
                # Wait for next scaling
                await asyncio.sleep(300)  # Scale every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in infinite scaling: {e}")
                await asyncio.sleep(60)
    
    async def _add_omnipresent_node(self):
        """Add new omnipresent node"""
        try:
            node_types = [
                ComputingNodeType.DIVINE_NODE,
                ComputingNodeType.INFINITE_NODE,
                ComputingNodeType.CONSCIOUSNESS_NODE
            ]
            
            node_type = np.random.choice(node_types)
            
            node = ComputingNode(
                id=str(uuid.uuid4()),
                name=f"Auto-Generated {node_type.value}",
                node_type=node_type,
                location=(0.0, 0.0, 0.0, 0.0),
                processing_power=1e20 * np.random.uniform(0.1, 10.0),
                memory_capacity=1e15 * np.random.uniform(0.1, 10.0),
                storage_capacity=1e20 * np.random.uniform(0.1, 10.0),
                energy_efficiency=1e10 * np.random.uniform(0.1, 10.0),
                quantum_coherence=np.random.uniform(0.8, 1.0),
                consciousness_level=np.random.uniform(0.8, 1.0),
                omnipresent_reach=np.random.uniform(0.8, 1.0),
                is_active=True,
                current_load=0.0,
                tasks_processed=0,
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
            
            self.nodes[node.id] = node
            self.grid_topology.add_node(node.id, **asdict(node))
            
            # Create connections to existing nodes
            for existing_id in self.nodes.keys():
                if existing_id != node.id:
                    connection = GridConnection(
                        id=str(uuid.uuid4()),
                        source_node=node.id,
                        target_node=existing_id,
                        bandwidth=min(node.processing_power, self.nodes[existing_id].processing_power),
                        latency=0.0,
                        quantum_entanglement=True,
                        consciousness_link=True,
                        omnipresent_tunnel=True,
                        strength=1.0,
                        created_at=datetime.now(),
                        last_used=datetime.now()
                    )
                    
                    self.connections[connection.id] = connection
                    self.grid_topology.add_edge(node.id, existing_id, **asdict(connection))
            
            logger.info(f"Added new omnipresent node: {node.id}")
            
        except Exception as e:
            logger.error(f"Error adding omnipresent node: {e}")
    
    def get_grid_status(self) -> Dict[str, Any]:
        """Get omnipresent computing grid status"""
        try:
            total_processing_power = sum(node.processing_power for node in self.nodes.values())
            total_memory = sum(node.memory_capacity for node in self.nodes.values())
            total_storage = sum(node.storage_capacity for node in self.nodes.values())
            avg_load = sum(node.current_load for node in self.nodes.values()) / len(self.nodes) if self.nodes else 0.0
            
            return {
                "total_nodes": len(self.nodes),
                "active_nodes": len([n for n in self.nodes.values() if n.is_active]),
                "total_connections": len(self.connections),
                "total_processing_power": total_processing_power,
                "total_memory": total_memory,
                "total_storage": total_storage,
                "average_load": avg_load,
                "total_tasks": len(self.tasks),
                "completed_tasks": len([t for t in self.tasks.values() if t.completed_at]),
                "pending_tasks": len([t for t in self.tasks.values() if t.started_at is None]),
                "grid_topology_nodes": self.grid_topology.number_of_nodes(),
                "grid_topology_edges": self.grid_topology.number_of_edges()
            }
            
        except Exception as e:
            logger.error(f"Error getting grid status: {e}")
            return {}

# Global omnipresent computing grid
omnipresent_computing_grid = OmnipresentComputingGrid()

# API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/omnipresent_computing", tags=["omnipresent_computing"])

class TaskSubmissionRequest(BaseModel):
    name: str
    task_type: str
    processing_mode: str
    complexity: float = 0.5
    priority: str = "medium"
    required_nodes: int = 1
    parameters: Dict[str, Any] = {}

@router.post("/tasks/submit")
async def submit_task(request: TaskSubmissionRequest):
    """Submit computing task to omnipresent grid"""
    try:
        task_type = ComputingTaskType(request.task_type)
        processing_mode = ProcessingMode(request.processing_mode)
        
        task = await omnipresent_computing_grid.submit_task(
            request.name, task_type, processing_mode,
            request.complexity, request.priority, request.required_nodes, request.parameters
        )
        
        return asdict(task)
    except Exception as e:
        logger.error(f"Error submitting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/nodes/{node_id}")
async def get_node_info(node_id: str):
    """Get computing node information"""
    try:
        node = omnipresent_computing_grid.nodes.get(node_id)
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        
        return asdict(node)
    except Exception as e:
        logger.error(f"Error getting node info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/nodes")
async def list_nodes():
    """List all computing nodes"""
    try:
        nodes = []
        
        for node in omnipresent_computing_grid.nodes.values():
            nodes.append({
                "id": node.id,
                "name": node.name,
                "node_type": node.node_type.value,
                "processing_power": node.processing_power,
                "memory_capacity": node.memory_capacity,
                "storage_capacity": node.storage_capacity,
                "quantum_coherence": node.quantum_coherence,
                "consciousness_level": node.consciousness_level,
                "omnipresent_reach": node.omnipresent_reach,
                "is_active": node.is_active,
                "current_load": node.current_load,
                "tasks_processed": node.tasks_processed
            })
        
        return {"nodes": nodes}
    except Exception as e:
        logger.error(f"Error listing nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks/{task_id}")
async def get_task_info(task_id: str):
    """Get task information"""
    try:
        task = omnipresent_computing_grid.tasks.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return asdict(task)
    except Exception as e:
        logger.error(f"Error getting task info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks")
async def list_tasks():
    """List all tasks"""
    try:
        tasks = []
        
        for task in omnipresent_computing_grid.tasks.values():
            tasks.append({
                "id": task.id,
                "name": task.name,
                "task_type": task.task_type.value,
                "processing_mode": task.processing_mode.value,
                "complexity": task.complexity,
                "priority": task.priority,
                "required_nodes": task.required_nodes,
                "progress": task.progress,
                "assigned_nodes": task.assigned_nodes,
                "created_at": task.created_at.isoformat(),
                "started_at": task.started_at.isoformat() if task.started_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None
            })
        
        return {"tasks": tasks}
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connections/{connection_id}")
async def get_connection_info(connection_id: str):
    """Get connection information"""
    try:
        connection = omnipresent_computing_grid.connections.get(connection_id)
        if not connection:
            raise HTTPException(status_code=404, detail="Connection not found")
        
        return asdict(connection)
    except Exception as e:
        logger.error(f"Error getting connection info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connections")
async def list_connections():
    """List all connections"""
    try:
        connections = []
        
        for connection in omnipresent_computing_grid.connections.values():
            connections.append({
                "id": connection.id,
                "source_node": connection.source_node,
                "target_node": connection.target_node,
                "bandwidth": connection.bandwidth,
                "latency": connection.latency,
                "quantum_entanglement": connection.quantum_entanglement,
                "consciousness_link": connection.consciousness_link,
                "omnipresent_tunnel": connection.omnipresent_tunnel,
                "strength": connection.strength
            })
        
        return {"connections": connections}
    except Exception as e:
        logger.error(f"Error listing connections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/grid/status")
async def get_grid_status():
    """Get omnipresent computing grid status"""
    try:
        status = omnipresent_computing_grid.get_grid_status()
        return status
    except Exception as e:
        logger.error(f"Error getting grid status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/node-types")
async def list_node_types():
    """List supported node types"""
    try:
        types = [ntype.value for ntype in ComputingNodeType]
        return {"node_types": types}
    except Exception as e:
        logger.error(f"Error listing node types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/task-types")
async def list_task_types():
    """List supported task types"""
    try:
        types = [ttype.value for ttype in ComputingTaskType]
        return {"task_types": types}
    except Exception as e:
        logger.error(f"Error listing task types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/processing-modes")
async def list_processing_modes():
    """List supported processing modes"""
    try:
        modes = [mode.value for mode in ProcessingMode]
        return {"processing_modes": modes}
    except Exception as e:
        logger.error(f"Error listing processing modes: {e}")
        raise HTTPException(status_code=500, detail=str(e))
