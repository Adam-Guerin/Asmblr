"""
Neuromorphic Computing Architecture for Asmblr
Brain-inspired computing systems with spiking neural networks
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

class NeuronType(Enum):
    """Types of neurons in neuromorphic systems"""
    LIF = "lif"  # Leaky Integrate-and-Fire
    IZHIKEVICH = "izhikevich"
    ADAPTIVE_EXP = "adaptive_exponential"
    HODGKIN_HUXLEY = "hodgkin_huxley"
    SPIKE_RATE = "spike_rate"
    RECEPTIVE_FIELD = "receptive_field"

class SynapseType(Enum):
    """Types of synapses"""
    EXCITATORY = "excitatory"
    INHIBITORY = "inhibitory"
    MODULATORY = "modulatory"
    PLASTIC = "plastic"
    ELECTRICAL = "electrical"
    CHEMICAL = "chemical"

class LearningRule(Enum):
    """Learning rules for neuromorphic systems"""
    STDP = "stdp"  # Spike-Timing Dependent Plasticity
    RSTDP = "rstdp"  # Reward-Modulated STDP
    HEBBIAN = "hebbian"
    ANTI_HEBBIAN = "anti_hebbian"
    OJA = "oja"
    BCM = "bcm"
    HOMEOSTATIC = "homeostatic"

class EventType(Enum):
    """Event types in neuromorphic systems"""
    SPIKE = "spike"
    BURST = "burst"
    SYNAPTIC_EVENT = "synaptic_event"
    PLASTICITY_EVENT = "plasticity_event"
    RESET_EVENT = "reset_event"
    MODULATION_EVENT = "modulation_event"

@dataclass
class SpikeEvent:
    """Spike event in neuromorphic system"""
    neuron_id: str
    timestamp: float
    spike_amplitude: float
    metadata: Dict[str, Any]

@dataclass
class SynapticConnection:
    """Synaptic connection between neurons"""
    id: str
    pre_neuron_id: str
    post_neuron_id: str
    synapse_type: SynapseType
    weight: float
    delay: float
    plasticity: bool
    last_spike_time: float
    spike_count: int
    learning_rule: Optional[LearningRule]

@dataclass
class Neuron:
    """Neuron in neuromorphic system"""
    id: str
    neuron_type: NeuronType
    position: Tuple[float, float, float]
    membrane_potential: float
    threshold: float
    refractory_period: float
    last_spike_time: float
    spike_times: List[float]
    parameters: Dict[str, Any]
    connections_in: List[str]
    connections_out: List[str]
    is_active: bool

@dataclass
class NeuromorphicLayer:
    """Layer of neurons in neuromorphic system"""
    id: str
    name: str
    neuron_type: NeuronType
    neurons: List[Neuron]
    connections: List[SynapticConnection]
    learning_enabled: bool
    plasticity_rules: List[LearningRule]
    created_at: datetime

@dataclass
class NeuromorphicNetwork:
    """Complete neuromorphic network"""
    id: str
    name: str
    layers: List[NeuromorphicLayer]
    global_connections: List[SynapticConnection]
    input_neurons: List[str]
    output_neurons: List[str]
    simulation_time: float
    time_step: float
    spike_events: List[SpikeEvent]
    learning_enabled: bool
    created_at: datetime
    updated_at: datetime

class LIFNeuron:
    """Leaky Integrate-and-Fire neuron model"""
    
    def __init__(self, neuron_id: str, parameters: Dict[str, Any]):
        self.id = neuron_id
        self.membrane_potential = parameters.get("v_rest", -70.0)  # mV
        self.threshold = parameters.get("v_threshold", -50.0)  # mV
        self.refractory_period = parameters.get("refractory_period", 2.0)  # ms
        self.tau_m = parameters.get("tau_m", 10.0)  # ms
        self.resistance = parameters.get("resistance", 1.0)  # MΩ
        self.capacitance = parameters.get("capacitance", 10.0)  # pF
        
        self.last_spike_time = -1000.0
        self.spike_times = []
        self.is_refractory = False
        
    def update(self, input_current: float, dt: float, current_time: float) -> bool:
        """Update neuron state and return True if spike occurs"""
        try:
            # Check refractory period
            if current_time - self.last_spike_time < self.refractory_period:
                self.is_refractory = True
                return False
            
            self.is_refractory = False
            
            # Update membrane potential
            dv_dt = (-self.membrane_potential + self.resistance * input_current) / self.tau_m
            self.membrane_potential += dv_dt * dt
            
            # Check for spike
            if self.membrane_potential >= self.threshold:
                self.spike_times.append(current_time)
                self.last_spike_time = current_time
                self.membrane_potential = self.parameters.get("v_reset", -70.0)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating LIF neuron: {e}")
            return False
    
    def reset(self):
        """Reset neuron to resting state"""
        self.membrane_potential = self.parameters.get("v_rest", -70.0)
        self.last_spike_time = -1000.0
        self.spike_times = []
        self.is_refractory = False

class IzhikevichNeuron:
    """Izhikevich neuron model"""
    
    def __init__(self, neuron_id: str, parameters: Dict[str, Any]):
        self.id = neuron_id
        self.a = parameters.get("a", 0.02)
        self.b = parameters.get("b", 0.2)
        self.c = parameters.get("c", -65.0)
        self.d = parameters.get("d", 8.0)
        
        self.v = parameters.get("v_init", -65.0)
        self.u = self.b * self.v
        self.threshold = 30.0
        
        self.last_spike_time = -1000.0
        self.spike_times = []
        
    def update(self, input_current: float, dt: float, current_time: float) -> bool:
        """Update Izhikevich neuron state"""
        try:
            # Izhikevich equations
            dv = (0.04 * self.v**2 + 5 * self.v + 140 - self.u + input_current) * dt
            du = self.a * (self.b * self.v - self.u) * dt
            
            self.v += dv
            self.u += du
            
            # Check for spike
            if self.v >= self.threshold:
                self.spike_times.append(current_time)
                self.last_spike_time = current_time
                self.v = self.c
                self.u += self.d
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating Izhikevich neuron: {e}")
            return False
    
    def reset(self):
        """Reset neuron to initial state"""
        self.v = self.c
        self.u = self.b * self.v
        self.last_spike_time = -1000.0
        self.spike_times = []

class AdaptiveExponentialNeuron:
    """Adaptive Exponential neuron model"""
    
    def __init__(self, neuron_id: str, parameters: Dict[str, Any]):
        self.id = neuron_id
        self.C_m = parameters.get("C_m", 281.0)  # pF
        self.g_L = parameters.get("g_L", 30.0)  # nS
        self.E_L = parameters.get("E_L", -70.6)  # mV
        self.V_T = parameters.get("V_T", -50.4)  # mV
        self.Delta_T = parameters.get("Delta_T", 2.0)  # mV
        self.tau_w = parameters.get("tau_w", 144.0)  # ms
        self.a = parameters.get("a", 4.0)  # nS
        self.b = parameters.get("b", 80.5)  # pA
        self.V_r = parameters.get("V_r", -70.6)  # mV
        self.V_peak = parameters.get("V_peak", 20.0)  # mV
        
        self.v = self.E_L
        self.w = 0.0
        self.last_spike_time = -1000.0
        self.spike_times = []
        
    def update(self, input_current: float, dt: float, current_time: float) -> bool:
        """Update Adaptive Exponential neuron state"""
        try:
            # Adaptive Exponential equations
            I = input_current
            
            # Membrane potential equation
            dv_dt = (-self.g_L * (self.v - self.E_L) + 
                     self.g_L * self.Delta_T * np.exp((self.v - self.V_T) / self.Delta_T) -
                     self.w + I) / self.C_m
            
            # Adaptation current equation
            dw_dt = (self.a * (self.v - self.E_L) - self.w) / self.tau_w
            
            self.v += dv_dt * dt
            self.w += dw_dt * dt
            
            # Check for spike
            if self.v >= self.V_peak:
                self.spike_times.append(current_time)
                self.last_spike_time = current_time
                self.v = self.V_r
                self.w += self.b
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating Adaptive Exponential neuron: {e}")
            return False
    
    def reset(self):
        """Reset neuron to initial state"""
        self.v = self.E_L
        self.w = 0.0
        self.last_spike_time = -1000.0
        self.spike_times = []

class STDPPlasticity:
    """Spike-Timing Dependent Plasticity learning rule"""
    
    def __init__(self, parameters: Dict[str, Any]):
        self.A_plus = parameters.get("A_plus", 0.1)
        self.A_minus = parameters.get("A_minus", -0.1)
        self.tau_plus = parameters.get("tau_plus", 20.0)  # ms
        self.tau_minus = parameters.get("tau_minus", 20.0)  # ms
        self.w_max = parameters.get("w_max", 1.0)
        self.w_min = parameters.get("w_min", 0.0)
        
        self.pre_spike_times = {}
        self.post_spike_times = {}
        
    def update_weight(self, weight: float, pre_spike_time: float, 
                     post_spike_time: float, current_time: float) -> float:
        """Update synaptic weight based on STDP"""
        try:
            delta_t = post_spike_time - pre_spike_time
            
            if delta_t > 0:  # Pre before Post (potentiation)
                dw = self.A_plus * np.exp(-delta_t / self.tau_plus)
            else:  # Post before Pre (depression)
                dw = self.A_minus * np.exp(delta_t / self.tau_minus)
            
            # Update weight with bounds
            new_weight = weight + dw
            return max(self.w_min, min(self.w_max, new_weight))
            
        except Exception as e:
            logger.error(f"Error updating STDP weight: {e}")
            return weight

class NeuromorphicProcessor:
    """Neuromorphic computing processor"""
    
    def __init__(self):
        self.neurons: Dict[str, Union[LIFNeuron, IzhikevichNeuron, AdaptiveExponentialNeuron]] = {}
        self.connections: Dict[str, SynapticConnection] = {}
        self.spike_events: List[SpikeEvent] = []
        self.plasticity_rules: Dict[str, STDPPlasticity] = {}
        self.current_time = 0.0
        self.time_step = 0.1  # ms
        
    def add_neuron(self, neuron_id: str, neuron_type: NeuronType, 
                   parameters: Dict[str, Any]) -> bool:
        """Add neuron to processor"""
        try:
            if neuron_type == NeuronType.LIF:
                neuron = LIFNeuron(neuron_id, parameters)
            elif neuron_type == NeuronType.IZHIKEVICH:
                neuron = IzhikevichNeuron(neuron_id, parameters)
            elif neuron_type == NeuronType.ADAPTIVE_EXP:
                neuron = AdaptiveExponentialNeuron(neuron_id, parameters)
            else:
                raise ValueError(f"Neuron type {neuron_type} not supported")
            
            self.neurons[neuron_id] = neuron
            logger.info(f"Added neuron: {neuron_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding neuron: {e}")
            return False
    
    def add_connection(self, connection_id: str, pre_neuron_id: str, 
                        post_neuron_id: str, synapse_type: SynapseType,
                        weight: float, delay: float, 
                        learning_rule: Optional[LearningRule] = None) -> bool:
        """Add synaptic connection"""
        try:
            if pre_neuron_id not in self.neurons or post_neuron_id not in self.neurons:
                return False
            
            connection = SynapticConnection(
                id=connection_id,
                pre_neuron_id=pre_neuron_id,
                post_neuron_id=post_neuron_id,
                synapse_type=synapse_type,
                weight=weight,
                delay=delay,
                plasticity=learning_rule is not None,
                last_spike_time=-1000.0,
                spike_count=0,
                learning_rule=learning_rule
            )
            
            self.connections[connection_id] = connection
            
            # Add plasticity rule if specified
            if learning_rule == LearningRule.STDP:
                self.plasticity_rules[connection_id] = STDPPlasticity({
                    "A_plus": 0.1,
                    "A_minus": -0.1,
                    "tau_plus": 20.0,
                    "tau_minus": 20.0
                })
            
            logger.info(f"Added connection: {connection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding connection: {e}")
            return False
    
    def simulate_step(self, external_inputs: Dict[str, float]) -> List[SpikeEvent]:
        """Simulate one time step"""
        try:
            spike_events = []
            
            # Update each neuron
            for neuron_id, neuron in self.neurons.items():
                # Calculate input current
                input_current = external_inputs.get(neuron_id, 0.0)
                
                # Add synaptic inputs
                for conn_id, connection in self.connections.items():
                    if connection.post_neuron_id == neuron_id:
                        pre_neuron = self.neurons[connection.pre_neuron_id]
                        
                        # Check if pre-synaptic neuron spiked recently
                        if (self.current_time - pre_neuron.last_spike_time) < connection.delay:
                            input_current += connection.weight
                
                # Update neuron
                spiked = neuron.update(input_current, self.time_step, self.current_time)
                
                if spiked:
                    spike_event = SpikeEvent(
                        neuron_id=neuron_id,
                        timestamp=self.current_time,
                        spike_amplitude=1.0,
                        metadata={}
                    )
                    spike_events.append(spike_event)
                    self.spike_events.append(spike_event)
            
            # Update plasticity
            for spike_event in spike_events:
                self._update_plasticity(spike_event)
            
            # Advance time
            self.current_time += self.time_step
            
            return spike_events
            
        except Exception as e:
            logger.error(f"Error in simulation step: {e}")
            return []
    
    def _update_plasticity(self, spike_event: SpikeEvent):
        """Update synaptic plasticity based on spike events"""
        try:
            neuron_id = spike_event.neuron_id
            spike_time = spike_event.timestamp
            
            # Check outgoing connections
            for conn_id, connection in self.connections.items():
                if connection.pre_neuron_id == neuron_id:
                    if conn_id in self.plasticity_rules:
                        # Update pre-synaptic spike time
                        plasticity = self.plasticity_rules[conn_id]
                        
                        # Check for post-synaptic spike
                        post_neuron = self.neurons[connection.post_neuron_id]
                        if post_neuron.spike_times:
                            last_post_spike = post_neuron.spike_times[-1]
                            
                            # Update weight
                            new_weight = plasticity.update_weight(
                                connection.weight,
                                spike_time,
                                last_post_spike,
                                self.current_time
                            )
                            connection.weight = new_weight
            
            # Check incoming connections
            for conn_id, connection in self.connections.items():
                if connection.post_neuron_id == neuron_id:
                    if conn_id in self.plasticity_rules:
                        # Update post-synaptic spike time
                        plasticity = self.plasticity_rules[conn_id]
                        
                        # Check for pre-synaptic spike
                        pre_neuron = self.neurons[connection.pre_neuron_id]
                        if pre_neuron.spike_times:
                            last_pre_spike = pre_neuron.spike_times[-1]
                            
                            # Update weight
                            new_weight = plasticity.update_weight(
                                connection.weight,
                                last_pre_spike,
                                spike_time,
                                self.current_time
                            )
                            connection.weight = new_weight
            
        except Exception as e:
            logger.error(f"Error updating plasticity: {e}")
    
    def simulate(self, duration: float, external_inputs: Dict[str, float]) -> Dict[str, Any]:
        """Run simulation for specified duration"""
        try:
            num_steps = int(duration / self.time_step)
            all_spike_events = []
            
            for step in range(num_steps):
                step_events = self.simulate_step(external_inputs)
                all_spike_events.extend(step_events)
            
            # Calculate statistics
            spike_counts = {}
            for neuron_id in self.neurons:
                neuron = self.neurons[neuron_id]
                spike_counts[neuron_id] = len(neuron.spike_times)
            
            firing_rates = {}
            for neuron_id, count in spike_counts.items():
                firing_rates[neuron_id] = count / (duration / 1000.0)  # Hz
            
            return {
                "simulation_time": self.current_time,
                "num_steps": num_steps,
                "total_spikes": len(all_spike_events),
                "spike_counts": spike_counts,
                "firing_rates": firing_rates,
                "spike_events": [
                    {
                        "neuron_id": event.neuron_id,
                        "timestamp": event.timestamp,
                        "amplitude": event.spike_amplitude
                    }
                    for event in all_spike_events
                ]
            }
            
        except Exception as e:
            logger.error(f"Error in simulation: {e}")
            return {}
    
    def get_network_graph(self) -> Dict[str, Any]:
        """Get network graph representation"""
        try:
            graph = nx.DiGraph()
            
            # Add nodes
            for neuron_id, neuron in self.neurons.items():
                graph.add_node(neuron_id, 
                             type=type(neuron).__name__,
                             membrane_potential=neuron.membrane_potential)
            
            # Add edges
            for conn_id, connection in self.connections.items():
                graph.add_edge(connection.pre_neuron_id, 
                             connection.post_neuron_id,
                             weight=connection.weight,
                             synapse_type=connection.synapse_type.value,
                             delay=connection.delay)
            
            # Calculate network metrics
            metrics = {
                "num_nodes": graph.number_of_nodes(),
                "num_edges": graph.number_of_edges(),
                "density": nx.density(graph),
                "in_degree": dict(graph.in_degree()),
                "out_degree": dict(graph.out_degree()),
                "clustering_coefficient": nx.average_clustering(graph)
            }
            
            return {
                "graph": graph,
                "metrics": metrics
            }
            
        except Exception as e:
            logger.error(f"Error getting network graph: {e}")
            return {}
    
    def reset(self):
        """Reset all neurons to initial state"""
        try:
            for neuron in self.neurons.values():
                neuron.reset()
            
            self.spike_events = []
            self.current_time = 0.0
            
            logger.info("Reset neuromorphic processor")
            
        except Exception as e:
            logger.error(f"Error resetting processor: {e}")

class NeuromorphicNetworkBuilder:
    """Builder for creating neuromorphic networks"""
    
    def __init__(self):
        self.processor = NeuromorphicNetworkBuilder()
        self.network_config = {}
    
    def create_feedforward_network(self, input_size: int, hidden_sizes: List[int], 
                                  output_size: int, neuron_type: NeuronType = NeuronType.LIF) -> NeuromorphicProcessor:
        """Create feedforward neuromorphic network"""
        try:
            processor = NeuromorphicProcessor()
            
            # Create layers
            layer_sizes = [input_size] + hidden_sizes + [output_size]
            layer_neurons = []
            
            for layer_idx, size in enumerate(layer_sizes):
                layer_neuron_ids = []
                
                for neuron_idx in range(size):
                    neuron_id = f"layer_{layer_idx}_neuron_{neuron_idx}"
                    
                    # Neuron parameters
                    if neuron_type == NeuronType.LIF:
                        params = {
                            "v_rest": -70.0,
                            "v_threshold": -50.0,
                            "refractory_period": 2.0,
                            "tau_m": 10.0
                        }
                    elif neuron_type == NeuronType.IZHIKEVICH:
                        params = {
                            "a": 0.02,
                            "b": 0.2,
                            "c": -65.0,
                            "d": 8.0
                        }
                    else:
                        params = {}
                    
                    processor.add_neuron(neuron_id, neuron_type, params)
                    layer_neuron_ids.append(neuron_id)
                
                layer_neurons.append(layer_neuron_ids)
            
            # Create connections between layers
            for layer_idx in range(len(layer_neurons) - 1):
                current_layer = layer_neurons[layer_idx]
                next_layer = layer_neurons[layer_idx + 1]
                
                for pre_idx, pre_neuron_id in enumerate(current_layer):
                    for post_idx, post_neuron_id in enumerate(next_layer):
                        # Random connectivity (sparse)
                        if np.random.random() < 0.3:  # 30% connectivity
                            connection_id = f"{pre_neuron_id}_to_{post_neuron_id}"
                            
                            # Random weight
                            weight = np.random.uniform(0.1, 1.0)
                            
                            # Random delay
                            delay = np.random.uniform(1.0, 5.0)
                            
                            processor.add_connection(
                                connection_id,
                                pre_neuron_id,
                                post_neuron_id,
                                SynapseType.EXCITATORY,
                                weight,
                                delay,
                                LearningRule.STDP
                            )
            
            logger.info(f"Created feedforward network: {len(layer_neurons)} layers")
            return processor
            
        except Exception as e:
            logger.error(f"Error creating feedforward network: {e}")
            raise
    
    def create_recurrent_network(self, size: int, connectivity: float = 0.2,
                               neuron_type: NeuronType = NeuronType.LIF) -> NeuromorphicProcessor:
        """Create recurrent neuromorphic network"""
        try:
            processor = NeuromorphicProcessor()
            
            # Create neurons
            neuron_ids = []
            for i in range(size):
                neuron_id = f"recurrent_neuron_{i}"
                
                if neuron_type == NeuronType.LIF:
                    params = {
                        "v_rest": -65.0,
                        "v_threshold": -50.0,
                        "refractory_period": 2.0,
                        "tau_m": 20.0
                    }
                else:
                    params = {}
                
                processor.add_neuron(neuron_id, neuron_type, params)
                neuron_ids.append(neuron_id)
            
            # Create recurrent connections
            for i, pre_neuron_id in enumerate(neuron_ids):
                for j, post_neuron_id in enumerate(neuron_ids):
                    if i != j and np.random.random() < connectivity:
                        connection_id = f"{pre_neuron_id}_to_{post_neuron_id}"
                        
                        # Random weight (excitatory or inhibitory)
                        if np.random.random() < 0.8:
                            weight = np.random.uniform(0.1, 1.0)
                            synapse_type = SynapseType.EXCITATORY
                        else:
                            weight = np.random.uniform(-1.0, -0.1)
                            synapse_type = SynapseType.INHIBITORY
                        
                        delay = np.random.uniform(1.0, 3.0)
                        
                        processor.add_connection(
                            connection_id,
                            pre_neuron_id,
                            post_neuron_id,
                            synapse_type,
                            weight,
                            delay,
                            LearningRule.STDP
                        )
            
            logger.info(f"Created recurrent network: {size} neurons, {connectivity:.1%} connectivity")
            return processor
            
        except Exception as e:
            logger.error(f"Error creating recurrent network: {e}")
            raise
    
    def create_liquid_state_machine(self, size: int = 100, input_size: int = 10,
                                    output_size: int = 5) -> NeuromorphicProcessor:
        """Create Liquid State Machine (LSM)"""
        try:
            processor = NeuromorphicProcessor()
            
            # Create liquid (reservoir)
            liquid_neurons = []
            for i in range(size):
                neuron_id = f"liquid_neuron_{i}"
                
                # Random neuron parameters for diversity
                params = {
                    "v_rest": np.random.uniform(-70, -60),
                    "v_threshold": np.random.uniform(-55, -45),
                    "refractory_period": np.random.uniform(1.0, 5.0),
                    "tau_m": np.random.uniform(10.0, 30.0)
                }
                
                processor.add_neuron(neuron_id, NeuronType.LIF, params)
                liquid_neurons.append(neuron_id)
            
            # Create input neurons
            input_neurons = []
            for i in range(input_size):
                neuron_id = f"input_neuron_{i}"
                params = {
                    "v_rest": -70.0,
                    "v_threshold": -50.0,
                    "refractory_period": 1.0,
                    "tau_m": 10.0
                }
                
                processor.add_neuron(neuron_id, NeuronType.LIF, params)
                input_neurons.append(neuron_id)
            
            # Create output neurons
            output_neurons = []
            for i in range(output_size):
                neuron_id = f"output_neuron_{i}"
                params = {
                    "v_rest": -70.0,
                    "v_threshold": -50.0,
                    "refractory_period": 2.0,
                    "tau_m": 20.0
                }
                
                processor.add_neuron(neuron_id, NeuronType.LIF, params)
                output_neurons.append(neuron_id)
            
            # Connect input to liquid
            for input_neuron in input_neurons:
                for liquid_neuron in liquid_neurons:
                    if np.random.random() < 0.3:  # 30% connectivity
                        connection_id = f"{input_neuron}_to_{liquid_neuron}"
                        weight = np.random.uniform(0.1, 1.0)
                        delay = np.random.uniform(1.0, 3.0)
                        
                        processor.add_connection(
                            connection_id,
                            input_neuron,
                            liquid_neuron,
                            SynapseType.EXCITATORY,
                            weight,
                            delay
                        )
            
            # Create sparse recurrent connections in liquid
            for i, pre_neuron in enumerate(liquid_neurons):
                for j, post_neuron in enumerate(liquid_neurons):
                    if i != j and np.random.random() < 0.1:  # 10% connectivity
                        connection_id = f"{pre_neuron}_to_{post_neuron}"
                        
                        if np.random.random() < 0.8:
                            weight = np.random.uniform(0.1, 1.0)
                            synapse_type = SynapseType.EXCITATORY
                        else:
                            weight = np.random.uniform(-1.0, -0.1)
                            synapse_type = SynapseType.INHIBITORY
                        
                        delay = np.random.uniform(1.0, 5.0)
                        
                        processor.add_connection(
                            connection_id,
                            pre_neuron,
                            post_neuron,
                            synapse_type,
                            weight,
                            delay,
                            LearningRule.STDP
                        )
            
            # Connect liquid to output
            for liquid_neuron in liquid_neurons:
                for output_neuron in output_neurons:
                    if np.random.random() < 0.2:  # 20% connectivity
                        connection_id = f"{liquid_neuron}_to_{output_neuron}"
                        weight = np.random.uniform(0.1, 1.0)
                        delay = np.random.uniform(1.0, 3.0)
                        
                        processor.add_connection(
                            connection_id,
                            liquid_neuron,
                            output_neuron,
                            SynapseType.EXCITATORY,
                            weight,
                            delay,
                            LearningRule.STDP
                        )
            
            logger.info(f"Created LSM: {size} liquid neurons, {input_size} inputs, {output_size} outputs")
            return processor
            
        except Exception as e:
            logger.error(f"Error creating LSM: {e}")
            raise

class NeuromorphicManager:
    """Manager for neuromorphic computing systems"""
    
    def __init__(self):
        self.processors: Dict[str, NeuromorphicProcessor] = {}
        self.networks: Dict[str, NeuromorphicNetwork] = {}
        self.builder = NeuromorphicNetworkBuilder()
        
        # Start background tasks
        asyncio.create_task(self._continuous_simulation())
        asyncio.create_task(self._performance_monitoring())
    
    async def create_processor(self, processor_id: str) -> NeuromorphicProcessor:
        """Create new neuromorphic processor"""
        try:
            processor = NeuromorphicProcessor()
            self.processors[processor_id] = processor
            
            logger.info(f"Created neuromorphic processor: {processor_id}")
            return processor
            
        except Exception as e:
            logger.error(f"Error creating processor: {e}")
            raise
    
    async def create_feedforward_network(self, network_id: str, input_size: int,
                                        hidden_sizes: List[int], output_size: int) -> NeuromorphicProcessor:
        """Create feedforward neuromorphic network"""
        try:
            processor = self.builder.create_feedforward_network(
                input_size, hidden_sizes, output_size
            )
            self.processors[network_id] = processor
            
            logger.info(f"Created feedforward network: {network_id}")
            return processor
            
        except Exception as e:
            logger.error(f"Error creating feedforward network: {e}")
            raise
    
    async def create_recurrent_network(self, network_id: str, size: int,
                                      connectivity: float = 0.2) -> NeuromorphicProcessor:
        """Create recurrent neuromorphic network"""
        try:
            processor = self.builder.create_recurrent_network(size, connectivity)
            self.processors[network_id] = processor
            
            logger.info(f"Created recurrent network: {network_id}")
            return processor
            
        except Exception as e:
            logger.error(f"Error creating recurrent network: {e}")
            raise
    
    async def create_liquid_state_machine(self, network_id: str, size: int = 100,
                                          input_size: int = 10, output_size: int = 5) -> NeuromorphicProcessor:
        """Create Liquid State Machine"""
        try:
            processor = self.builder.create_liquid_state_machine(size, input_size, output_size)
            self.processors[network_id] = processor
            
            logger.info(f"Created LSM: {network_id}")
            return processor
            
        except Exception as e:
            logger.error(f"Error creating LSM: {e}")
            raise
    
    async def run_simulation(self, processor_id: str, duration: float,
                            external_inputs: Dict[str, float]) -> Dict[str, Any]:
        """Run neuromorphic simulation"""
        try:
            processor = self.processors.get(processor_id)
            if not processor:
                raise ValueError(f"Processor {processor_id} not found")
            
            results = processor.simulate(duration, external_inputs)
            
            logger.info(f"Completed simulation: {processor_id}, duration: {duration}ms")
            return results
            
        except Exception as e:
            logger.error(f"Error running simulation: {e}")
            raise
    
    async def get_network_visualization(self, processor_id: str) -> Dict[str, Any]:
        """Get network visualization data"""
        try:
            processor = self.processors.get(processor_id)
            if not processor:
                raise ValueError(f"Processor {processor_id} not found")
            
            graph_data = processor.get_network_graph()
            
            # Convert to visualization format
            nodes = []
            edges = []
            
            if "graph" in graph_data:
                graph = graph_data["graph"]
                
                # Extract nodes
                for node_id in graph.nodes():
                    node_data = graph.nodes[node_id]
                    nodes.append({
                        "id": node_id,
                        "type": node_data.get("type", "Unknown"),
                        "membrane_potential": node_data.get("membrane_potential", 0.0)
                    })
                
                # Extract edges
                for edge in graph.edges():
                    edge_data = graph[edge]
                    edges.append({
                        "source": edge[0],
                        "target": edge[1],
                        "weight": edge_data.get("weight", 0.0),
                        "synapse_type": edge_data.get("synapse_type", "unknown"),
                        "delay": edge_data.get("delay", 0.0)
                    })
            
            return {
                "nodes": nodes,
                "edges": edges,
                "metrics": graph_data.get("metrics", {})
            }
            
        except Exception as e:
            logger.error(f"Error getting network visualization: {e}")
            return {}
    
    async def _continuous_simulation(self):
        """Background continuous simulation"""
        while True:
            try:
                # Run simulation for all active processors
                for processor_id, processor in self.processors.items():
                    # Simple test input
                    external_inputs = {}
                    for neuron_id in processor.neurons.keys():
                        if np.random.random() < 0.1:  # 10% chance of input
                            external_inputs[neuron_id] = np.random.uniform(0.1, 2.0)
                    
                    # Run short simulation
                    processor.simulate_step(external_inputs)
                
                # Wait before next simulation
                await asyncio.sleep(0.1)  # 10 Hz
                
            except Exception as e:
                logger.error(f"Error in continuous simulation: {e}")
                await asyncio.sleep(1)
    
    async def _performance_monitoring(self):
        """Background performance monitoring"""
        while True:
            try:
                # Collect performance metrics
                metrics = {
                    "total_processors": len(self.processors),
                    "total_neurons": sum(len(p.neurons) for p in self.processors.values()),
                    "total_connections": sum(len(p.connections) for p in self.processors.values()),
                    "total_spike_events": sum(len(p.spike_events) for p in self.processors.values()),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Log metrics
                logger.info(f"Neuromorphic metrics: {metrics}")
                
                # Wait before next monitoring
                await asyncio.sleep(60)  # 1 minute
                
            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                await asyncio.sleep(10)
    
    def get_processor_status(self, processor_id: str) -> Dict[str, Any]:
        """Get processor status"""
        try:
            processor = self.processors.get(processor_id)
            if not processor:
                return {"error": "Processor not found"}
            
            return {
                "processor_id": processor_id,
                "num_neurons": len(processor.neurons),
                "num_connections": len(processor.connections),
                "simulation_time": processor.current_time,
                "total_spike_events": len(processor.spike_events),
                "plasticity_rules": len(processor.plasticity_rules)
            }
            
        except Exception as e:
            logger.error(f"Error getting processor status: {e}")
            return {"error": str(e)}

# Global neuromorphic manager
neuro_manager = NeuromorphicManager()

# API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/neuromorphic", tags=["neuromorphic_computing"])

class FeedforwardNetworkRequest(BaseModel):
    input_size: int
    hidden_sizes: List[int]
    output_size: int
    neuron_type: str = "lif"

class RecurrentNetworkRequest(BaseModel):
    size: int
    connectivity: float = 0.2
    neuron_type: str = "lif"

class LSMRequest(BaseModel):
    size: int = 100
    input_size: int = 10
    output_size: int = 5

class SimulationRequest(BaseModel):
    processor_id: str
    duration: float
    external_inputs: Dict[str, float] = {}

@router.post("/processors/create")
async def create_processor(processor_id: str):
    """Create neuromorphic processor"""
    try:
        processor = await neuro_manager.create_processor(processor_id)
        return {"processor_id": processor_id, "status": "created"}
    except Exception as e:
        logger.error(f"Error creating processor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/networks/feedforward")
async def create_feedforward_network(network_id: str, request: FeedforwardNetworkRequest):
    """Create feedforward neuromorphic network"""
    try:
        neuron_type = NeuronType(request.neuron_type)
        processor = await neuro_manager.create_feedforward_network(
            network_id, request.input_size, request.hidden_sizes, request.output_size
        )
        return {"network_id": network_id, "status": "created"}
    except Exception as e:
        logger.error(f"Error creating feedforward network: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/networks/recurrent")
async def create_recurrent_network(network_id: str, request: RecurrentNetworkRequest):
    """Create recurrent neuromorphic network"""
    try:
        neuron_type = NeuronType(request.neuron_type)
        processor = await neuro_manager.create_recurrent_network(
            network_id, request.size, request.connectivity
        )
        return {"network_id": network_id, "status": "created"}
    except Exception as e:
        logger.error(f"Error creating recurrent network: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/networks/lsm")
async def create_liquid_state_machine(network_id: str, request: LSMRequest):
    """Create Liquid State Machine"""
    try:
        processor = await neuro_manager.create_liquid_state_machine(
            network_id, request.size, request.input_size, request.output_size
        )
        return {"network_id": network_id, "status": "created"}
    except Exception as e:
        logger.error(f"Error creating LSM: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulate")
async def run_simulation(request: SimulationRequest):
    """Run neuromorphic simulation"""
    try:
        results = await neuro_manager.run_simulation(
            request.processor_id, request.duration, request.external_inputs
        )
        return results
    except Exception as e:
        logger.error(f"Error running simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/processors/{processor_id}/visualization")
async def get_network_visualization(processor_id: str):
    """Get network visualization"""
    try:
        viz_data = await neuro_manager.get_network_visualization(processor_id)
        return viz_data
    except Exception as e:
        logger.error(f"Error getting visualization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/processors/{processor_id}/status")
async def get_processor_status(processor_id: str):
    """Get processor status"""
    try:
        status = neuro_manager.get_processor_status(processor_id)
        return status
    except Exception as e:
        logger.error(f"Error getting processor status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/processors")
async def list_processors():
    """List all processors"""
    try:
        processors = []
        for processor_id in neuro_manager.processors.keys():
            status = neuro_manager.get_processor_status(processor_id)
            processors.append(status)
        
        return {"processors": processors}
    except Exception as e:
        logger.error(f"Error listing processors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/neuron-types")
async def list_neuron_types():
    """List supported neuron types"""
    try:
        types = [ntype.value for ntype in NeuronType]
        return {"neuron_types": types}
    except Exception as e:
        logger.error(f"Error listing neuron types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_neuromorphic_status():
    """Get neuromorphic computing status"""
    try:
        return {
            "total_processors": len(neuro_manager.processors),
            "total_neurons": sum(len(p.neurons) for p in neuro_manager.processors.values()),
            "total_connections": sum(len(p.connections) for p in neuro_manager.processors.values()),
            "supported_neuron_types": len(NeuronType),
            "supported_learning_rules": len(LearningRule)
        }
    except Exception as e:
        logger.error(f"Error getting neuromorphic status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
