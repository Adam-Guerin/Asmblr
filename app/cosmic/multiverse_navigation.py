"""
Multiverse Navigation System for Asmblr
Navigation between parallel universes and alternate realities
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

class UniverseType(Enum):
    """Types of universes"""
    PRIME_UNIVERSE = "prime_universe"
    PARALLEL_UNIVERSE = "parallel_universe"
    ALTERNATE_UNIVERSE = "alternate_universe"
    MIRROR_UNIVERSE = "mirror_universe"
    INVERSE_UNIVERSE = "inverse_universe"
    DREAM_UNIVERSE = "dream_universe"
    QUANTUM_UNIVERSE = "quantum_universe"
    STRING_UNIVERSE = "string_universe"
    SIMULATION_UNIVERSE = "simulation_universe"
    VIRTUAL_UNIVERSE = "virtual_universe"

class NavigationMethod(Enum):
    """Methods of multiverse navigation"""
    QUANTUM_TUNNELING = "quantum_tunneling"
    WORMHOLE_TRAVEL = "wormhole_travel"
    DIMENSIONAL_SHIFT = "dimensional_shift"
    CONSCIOUSNESS_PROJECTION = "consciousness_projection"
    REALITY_BREACH = "reality_breach"
    TEMPORAL_ANOMALY = "temporal_anomaly"
    ENERGY_PORTAL = "energy_portal"
    HYPERSPACE_JUMP = "hyperspace_jump"

class UniverseParameter(Enum):
    """Universal parameters"""
    GRAVITATIONAL_CONSTANT = "gravitational_constant"
    SPEED_OF_LIGHT = "speed_of_light"
    PLANCK_CONSTANT = "planck_constant"
    FINE_STRUCTURE_CONSTANT = "fine_structure_constant"
    DIMENSIONS = "dimensions"
    TIME_DILATION = "time_dilation"
    ENTROPY_LEVEL = "entropy_level"
    CONSCIOUSNESS_DENSITY = "consciousness_density"
    QUANTUM_COHERENCE = "quantum_coherence"
    REALITY_STABILITY = "reality_stability"

@dataclass
class Universe:
    """Universe representation"""
    id: str
    name: str
    universe_type: UniverseType
    parameters: Dict[UniverseParameter, float]
    dimensions: int
    age: float  # billions of years
    size: float  # billions of light years
    is_accessible: bool
    is_stable: bool
    connection_points: List[str]
    created_at: datetime
    discovered_at: datetime

@dataclass
class Wormhole:
    """Wormhole connection between universes"""
    id: str
    name: str
    entrance_universe: str
    exit_universe: str
    stability: float
    length: float  # light years
    traversal_time: float  # seconds
    energy_cost: float  # joules
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]

@dataclass
class NavigationRoute:
    """Navigation route between universes"""
    id: str
    start_universe: str
    end_universe: str
    path: List[str]  # Universe IDs
    total_distance: float  # light years
    traversal_time: float  # seconds
    energy_cost: float  # joules
    difficulty: float  # 0-1
    created_at: datetime

@dataclass
class MultiverseTraveler:
    """Multiverse traveler"""
    id: str
    name: str
    current_universe: str
    home_universe: str
    visited_universes: List[str]
    travel_history: List[Dict[str, Any]]
    energy_reserves: float  # joules
    navigation_skill: float  # 0-1
    consciousness_level: float  # 0-1
    is_active: bool
    created_at: datetime

class MultiverseTopology:
    """Multiverse topology and connectivity"""
    
    def __init__(self):
        self.universe_graph = nx.Graph()
        self.wormholes: Dict[str, Wormhole] = {}
        self.universe_distances: Dict[Tuple[str, str], float] = {}
        
    def add_universe(self, universe: Universe):
        """Add universe to topology"""
        try:
            self.universe_graph.add_node(universe.id, **asdict(universe))
            
            # Calculate distances to other universes
            for other_id in self.universe_graph.nodes:
                if other_id != universe.id:
                    distance = self._calculate_universe_distance(universe.id, other_id)
                    self.universe_distances[(universe.id, other_id)] = distance
                    self.universe_distances[(other_id, universe.id)] = distance
                    
                    # Add edge with distance weight
                    self.universe_graph.add_edge(
                        universe.id, other_id, 
                        weight=distance,
                        connection_type="quantum_entanglement"
                    )
            
            logger.info(f"Added universe {universe.id} to topology")
            
        except Exception as e:
            logger.error(f"Error adding universe to topology: {e}")
    
    def _calculate_universe_distance(self, universe1_id: str, universe2_id: str) -> float:
        """Calculate distance between universes"""
        try:
            # Get universe parameters
            u1_data = self.universe_graph.nodes[universe1_id]
            u2_data = self.universe_graph.nodes[universe2_id]
            
            # Calculate parameter differences
            param_diff = 0.0
            for param in UniverseParameter:
                val1 = u1_data.get("parameters", {}).get(param, 0.0)
                val2 = u2_data.get("parameters", {}).get(param, 0.0)
                param_diff += abs(val1 - val2)
            
            # Dimensional difference
            dim_diff = abs(u1_data.get("dimensions", 3) - u2_data.get("dimensions", 3))
            
            # Reality stability difference
            stability_diff = abs(u1_data.get("is_stable", True) - u2_data.get("is_stable", True))
            
            # Calculate total distance (in light years)
            distance = param_diff * 1000 + dim_diff * 100 + stability_diff * 500
            
            return max(1.0, distance)  # Minimum 1 light year
            
        except Exception as e:
            logger.error(f"Error calculating universe distance: {e}")
            return 1000.0  # Default distance
    
    def create_wormhole(self, entrance_universe: str, exit_universe: str,
                       stability: float = 0.8) -> Wormhole:
        """Create wormhole between universes"""
        try:
            # Calculate wormhole properties
            distance = self.universe_distances.get((entrance_universe, exit_universe), 1000.0)
            
            # Wormhole length is much shorter than actual distance
            wormhole_length = distance * 0.001  # 0.1% of actual distance
            
            # Traversal time based on stability
            traversal_time = wormhole_length / (299792458.0 * stability)  # Speed of light * stability
            
            # Energy cost based on distance and stability
            energy_cost = distance * 1e30 / stability  # Joules
            
            wormhole = Wormhole(
                id=str(uuid.uuid4()),
                name=f"Wormhole_{entrance_universe[:8]}_{exit_universe[:8]}",
                entrance_universe=entrance_universe,
                exit_universe=exit_universe,
                stability=stability,
                length=wormhole_length,
                traversal_time=traversal_time,
                energy_cost=energy_cost,
                is_active=True,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=24)  # 24 hour lifetime
            )
            
            self.wormholes[wormhole.id] = wormhole
            
            # Add wormhole connection to graph
            self.universe_graph.add_edge(
                entrance_universe, exit_universe,
                weight=wormhole_length,
                connection_type="wormhole",
                wormhole_id=wormhole.id
            )
            
            logger.info(f"Created wormhole: {wormhole.id}")
            return wormhole
            
        except Exception as e:
            logger.error(f"Error creating wormhole: {e}")
            raise
    
    def find_shortest_path(self, start_universe: str, end_universe: str) -> Optional[List[str]]:
        """Find shortest path between universes"""
        try:
            if start_universe not in self.universe_graph or end_universe not in self.universe_graph:
                return None
            
            # Use Dijkstra's algorithm
            path = nx.shortest_path(self.universe_graph, start_universe, end_universe, weight='weight')
            
            return path
            
        except Exception as e:
            logger.error(f"Error finding shortest path: {e}")
            return None
    
    def calculate_route_metrics(self, path: List[str]) -> Dict[str, float]:
        """Calculate route metrics"""
        try:
            if len(path) < 2:
                return {"distance": 0.0, "time": 0.0, "energy": 0.0, "difficulty": 0.0}
            
            total_distance = 0.0
            total_time = 0.0
            total_energy = 0.0
            total_difficulty = 0.0
            
            for i in range(len(path) - 1):
                u1, u2 = path[i], path[i + 1]
                
                # Get edge data
                edge_data = self.universe_graph.edges[u1, u2]
                
                # Check if wormhole
                if edge_data.get("connection_type") == "wormhole":
                    wormhole_id = edge_data.get("wormhole_id")
                    wormhole = self.wormholes.get(wormhole_id)
                    
                    if wormhole and wormhole.is_active:
                        total_distance += wormhole.length
                        total_time += wormhole.traversal_time
                        total_energy += wormhole.energy_cost
                        total_difficulty += (1.0 - wormhole.stability)
                else:
                    # Quantum entanglement travel
                    distance = edge_data.get("weight", 1000.0)
                    total_distance += distance
                    total_time += distance / 299792458.0  # Speed of light
                    total_energy += distance * 1e30
                    total_difficulty += 0.5
            
            return {
                "distance": total_distance,
                "time": total_time,
                "energy": total_energy,
                "difficulty": total_difficulty / (len(path) - 1) if len(path) > 1 else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error calculating route metrics: {e}")
            return {"distance": 0.0, "time": 0.0, "energy": 0.0, "difficulty": 0.0}

class MultiverseNavigator:
    """Multiverse navigation system"""
    
    def __init__(self):
        self.topology = MultiverseTopology()
        self.travelers: Dict[str, MultiverseTraveler] = {}
        self.navigation_routes: Dict[str, NavigationRoute] = {}
        self.active_travels: Dict[str, Dict[str, Any]] = {}
        
        # Initialize with prime universe
        self._initialize_prime_universe()
        
        # Start background processes
        asyncio.create_task(self._wormhole_maintenance())
        asyncio.create_task(self._traveler_monitoring())
        asyncio.create_task(self._topology_evolution())
    
    def _initialize_prime_universe(self):
        """Initialize prime universe"""
        try:
            prime_universe = Universe(
                id="prime_universe",
                name="Prime Universe",
                universe_type=UniverseType.PRIME_UNIVERSE,
                parameters={
                    UniverseParameter.GRAVITATIONAL_CONSTANT: 6.67430e-11,
                    UniverseParameter.SPEED_OF_LIGHT: 299792458.0,
                    UniverseParameter.PLANCK_CONSTANT: 6.62607015e-34,
                    UniverseParameter.FINE_STRUCTURE_CONSTANT: 1/137.0,
                    UniverseParameter.DIMENSIONS: 4,
                    UniverseParameter.TIME_DILATION: 1.0,
                    UniverseParameter.ENTROPY_LEVEL: 1.0,
                    UniverseParameter.CONSCIOUSNESS_DENSITY: 0.1,
                    UniverseParameter.QUANTUM_COHERENCE: 0.5,
                    UniverseParameter.REALITY_STABILITY: 1.0
                },
                dimensions=4,
                age=13.8,  # billions of years
                size=93.0,  # billions of light years
                is_accessible=True,
                is_stable=True,
                connection_points=[],
                created_at=datetime.now(),
                discovered_at=datetime.now()
            )
            
            self.topology.add_universe(prime_universe)
            
            logger.info("Initialized prime universe")
            
        except Exception as e:
            logger.error(f"Error initializing prime universe: {e}")
    
    async def discover_universe(self, name: str, universe_type: UniverseType,
                                parameter_variations: Dict[UniverseParameter, float]) -> Universe:
        """Discover new universe"""
        try:
            # Get prime universe parameters as base
            prime_params = self.topology.universe_graph.nodes["prime_universe"]["parameters"]
            
            # Create new parameters with variations
            new_params = {}
            for param in UniverseParameter:
                base_value = prime_params.get(param, 1.0)
                variation = parameter_variations.get(param, 0.0)
                new_params[param] = base_value * (1.0 + variation)
            
            # Determine universe properties based on type
            if universe_type == UniverseType.PARALLEL_UNIVERSE:
                dimensions = 4
                age = 13.8
                size = 93.0
                is_stable = True
            elif universe_type == UniverseType.QUANTUM_UNIVERSE:
                dimensions = 11
                age = 15.0
                size = 100.0
                is_stable = False
            elif universe_type == UniverseType.DREAM_UNIVERSE:
                dimensions = 5
                age = 10.0
                size = 80.0
                is_stable = False
            elif universe_type == UniverseType.SIMULATION_UNIVERSE:
                dimensions = 3
                age = 0.1
                size = 10.0
                is_stable = True
            else:
                dimensions = 4
                age = 13.8
                size = 93.0
                is_stable = True
            
            universe = Universe(
                id=str(uuid.uuid4()),
                name=name,
                universe_type=universe_type,
                parameters=new_params,
                dimensions=dimensions,
                age=age,
                size=size,
                is_accessible=True,
                is_stable=is_stable,
                connection_points=[],
                created_at=datetime.now(),
                discovered_at=datetime.now()
            )
            
            self.topology.add_universe(universe)
            
            logger.info(f"Discovered new universe: {universe.id}")
            return universe
            
        except Exception as e:
            logger.error(f"Error discovering universe: {e}")
            raise
    
    async def create_wormhole(self, entrance_universe: str, exit_universe: str,
                             stability: float = 0.8) -> Wormhole:
        """Create wormhole between universes"""
        try:
            wormhole = self.topology.create_wormhole(entrance_universe, exit_universe, stability)
            
            # Update connection points
            for universe_id in [entrance_universe, exit_universe]:
                if universe_id in self.topology.universe_graph.nodes:
                    universe_data = self.topology.universe_graph.nodes[universe_id]
                    connection_points = universe_data.get("connection_points", [])
                    if wormhole.id not in connection_points:
                        connection_points.append(wormhole.id)
                        universe_data["connection_points"] = connection_points
            
            return wormhole
            
        except Exception as e:
            logger.error(f"Error creating wormhole: {e}")
            raise
    
    async def register_traveler(self, name: str, home_universe: str = "prime_universe") -> MultiverseTraveler:
        """Register multiverse traveler"""
        try:
            traveler = MultiverseTraveler(
                id=str(uuid.uuid4()),
                name=name,
                current_universe=home_universe,
                home_universe=home_universe,
                visited_universes=[home_universe],
                travel_history=[],
                energy_reserves=1e35,  # Large energy reserves
                navigation_skill=0.5,
                consciousness_level=0.5,
                is_active=True,
                created_at=datetime.now()
            )
            
            self.travelers[traveler.id] = traveler
            
            logger.info(f"Registered traveler: {traveler.id}")
            return traveler
            
        except Exception as e:
            logger.error(f"Error registering traveler: {e}")
            raise
    
    async def navigate_to_universe(self, traveler_id: str, target_universe: str,
                                  method: NavigationMethod) -> NavigationRoute:
        """Navigate traveler to target universe"""
        try:
            traveler = self.travelers.get(traveler_id)
            if not traveler:
                raise ValueError(f"Traveler {traveler_id} not found")
            
            # Find path
            path = self.topology.find_shortest_path(traveler.current_universe, target_universe)
            if not path:
                raise ValueError(f"No path found from {traveler.current_universe} to {target_universe}")
            
            # Calculate route metrics
            metrics = self.topology.calculate_route_metrics(path)
            
            # Check if traveler has enough energy
            if traveler.energy_reserves < metrics["energy"]:
                raise ValueError("Insufficient energy reserves")
            
            # Check navigation skill
            if traveler.navigation_skill < metrics["difficulty"]:
                raise ValueError("Insufficient navigation skill")
            
            # Create navigation route
            route = NavigationRoute(
                id=str(uuid.uuid4()),
                start_universe=traveler.current_universe,
                end_universe=target_universe,
                path=path,
                total_distance=metrics["distance"],
                traversal_time=metrics["time"],
                energy_cost=metrics["energy"],
                difficulty=metrics["difficulty"],
                created_at=datetime.now()
            )
            
            # Start navigation
            self.navigation_routes[route.id] = route
            asyncio.create_task(self._execute_navigation(traveler_id, route))
            
            logger.info(f"Started navigation: {route.id}")
            return route
            
        except Exception as e:
            logger.error(f"Error navigating to universe: {e}")
            raise
    
    async def _execute_navigation(self, traveler_id: str, route: NavigationRoute):
        """Execute navigation between universes"""
        try:
            traveler = self.travelers.get(traveler_id)
            if not traveler:
                return
            
            # Record travel start
            travel_record = {
                "route_id": route.id,
                "start_time": datetime.now(),
                "start_universe": route.start_universe,
                "end_universe": route.end_universe,
                "status": "in_progress"
            }
            
            self.active_travels[traveler_id] = travel_record
            
            # Navigate through path
            for i in range(len(route.path) - 1):
                current_universe = route.path[i]
                next_universe = route.path[i + 1]
                
                # Get edge data
                edge_data = self.topology.universe_graph.edges[current_universe, next_universe]
                
                # Check if wormhole
                if edge_data.get("connection_type") == "wormhole":
                    wormhole_id = edge_data.get("wormhole_id")
                    wormhole = self.topology.wormholes.get(wormhole_id)
                    
                    if wormhole and wormhole.is_active:
                        # Travel through wormhole
                        await asyncio.sleep(1.0)  # Simulated travel time
                        
                        # Update traveler
                        traveler.current_universe = next_universe
                        traveler.energy_reserves -= wormhole.energy_cost
                        traveler.visited_universes.append(next_universe)
                        
                        # Update travel record
                        travel_record["current_step"] = i + 1
                        travel_record["current_universe"] = next_universe
                else:
                    # Quantum entanglement travel
                    await asyncio.sleep(2.0)  # Simulated travel time
                    
                    # Update traveler
                    traveler.current_universe = next_universe
                    traveler.visited_universes.append(next_universe)
                    
                    # Update travel record
                    travel_record["current_step"] = i + 1
                    travel_record["current_universe"] = next_universe
                
                # Add to travel history
                traveler.travel_history.append({
                    "from_universe": current_universe,
                    "to_universe": next_universe,
                    "timestamp": datetime.now(),
                    "method": "wormhole" if edge_data.get("connection_type") == "wormhole" else "quantum_entanglement"
                })
            
            # Complete travel
            travel_record["status"] = "completed"
            travel_record["end_time"] = datetime.now()
            
            # Improve navigation skill
            traveler.navigation_skill = min(1.0, traveler.navigation_skill + 0.01)
            
            logger.info(f"Completed navigation: {route.id}")
            
        except Exception as e:
            logger.error(f"Error executing navigation: {e}")
            if traveler_id in self.active_travels:
                self.active_travels[traveler_id]["status"] = "failed"
    
    async def _wormhole_maintenance(self):
        """Background wormhole maintenance"""
        while True:
            try:
                current_time = datetime.now()
                expired_wormholes = []
                
                # Check for expired wormholes
                for wormhole_id, wormhole in self.topology.wormholes.items():
                    if wormhole.expires_at and current_time > wormhole.expires_at:
                        expired_wormholes.append(wormhole_id)
                
                # Remove expired wormholes
                for wormhole_id in expired_wormholes:
                    wormhole = self.topology.wormholes[wormhole_id]
                    
                    # Remove from graph
                    if self.topology.universe_graph.has_edge(wormhole.entrance_universe, wormhole.exit_universe):
                        self.topology.universe_graph.remove_edge(wormhole.entrance_universe, wormhole.exit_universe)
                    
                    # Remove from wormholes
                    del self.topology.wormholes[wormhole_id]
                    
                    logger.info(f"Expired wormhole: {wormhole_id}")
                
                # Degrade wormhole stability
                for wormhole in self.topology.wormholes.values():
                    if wormhole.is_active:
                        wormhole.stability *= 0.999  # Gradual degradation
                        
                        if wormhole.stability < 0.1:
                            wormhole.is_active = False
                
                # Wait for next maintenance
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in wormhole maintenance: {e}")
                await asyncio.sleep(60)
    
    async def _traveler_monitoring(self):
        """Background traveler monitoring"""
        while True:
            try:
                # Monitor traveler status
                for traveler in self.travelers.values():
                    if traveler.is_active:
                        # Regenerate energy slowly
                        traveler.energy_reserves *= 1.000001  # Very slow regeneration
                        
                        # Update consciousness level based on visited universes
                        if len(traveler.visited_universes) > 10:
                            traveler.consciousness_level = min(1.0, traveler.consciousness_level + 0.0001)
                
                # Wait for next monitoring
                await asyncio.sleep(60)  # Monitor every minute
                
            except Exception as e:
                logger.error(f"Error in traveler monitoring: {e}")
                await asyncio.sleep(10)
    
    async def _topology_evolution(self):
        """Background topology evolution"""
        while True:
            try:
                # Occasionally discover new universes
                if np.random.random() < 0.1:  # 10% chance
                    universe_types = [
                        UniverseType.PARALLEL_UNIVERSE,
                        UniverseType.ALTERNATE_UNIVERSE,
                        UniverseType.QUANTUM_UNIVERSE,
                        UniverseType.DREAM_UNIVERSE
                    ]
                    
                    new_type = np.random.choice(universe_types)
                    
                    # Generate parameter variations
                    variations = {}
                    for param in UniverseParameter:
                        variations[param] = np.random.uniform(-0.5, 0.5)
                    
                    await self.discover_universe(
                        f"Discovered_Universe_{int(time.time())}",
                        new_type,
                        variations
                    )
                
                # Occasionally create new wormholes
                if len(self.topology.universe_graph.nodes) > 1 and np.random.random() < 0.05:  # 5% chance
                    nodes = list(self.topology.universe_graph.nodes)
                    if len(nodes) >= 2:
                        u1, u2 = np.random.choice(nodes, 2, replace=False)
                        stability = np.random.uniform(0.5, 0.9)
                        
                        await self.create_wormhole(u1, u2, stability)
                
                # Wait for next evolution
                await asyncio.sleep(600)  # Evolve every 10 minutes
                
            except Exception as e:
                logger.error(f"Error in topology evolution: {e}")
                await asyncio.sleep(60)
    
    def get_universe_info(self, universe_id: str) -> Dict[str, Any]:
        """Get universe information"""
        try:
            if universe_id not in self.topology.universe_graph.nodes:
                return {"error": "Universe not found"}
            
            universe_data = self.topology.universe_graph.nodes[universe_id]
            
            return {
                "id": universe_id,
                "name": universe_data.get("name", "Unknown"),
                "universe_type": universe_data.get("universe_type", "unknown"),
                "parameters": {param.value: value for param, value in universe_data.get("parameters", {}).items()},
                "dimensions": universe_data.get("dimensions", 3),
                "age": universe_data.get("age", 0.0),
                "size": universe_data.get("size", 0.0),
                "is_accessible": universe_data.get("is_accessible", False),
                "is_stable": universe_data.get("is_stable", False),
                "connection_points": universe_data.get("connection_points", []),
                "created_at": universe_data.get("created_at", datetime.now()).isoformat(),
                "discovered_at": universe_data.get("discovered_at", datetime.now()).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting universe info: {e}")
            return {"error": str(e)}
    
    def list_universes(self) -> List[Dict[str, Any]]:
        """List all universes"""
        try:
            universes = []
            
            for universe_id, universe_data in self.topology.universe_graph.nodes.items():
                universes.append({
                    "id": universe_id,
                    "name": universe_data.get("name", "Unknown"),
                    "universe_type": universe_data.get("universe_type", "unknown"),
                    "dimensions": universe_data.get("dimensions", 3),
                    "is_accessible": universe_data.get("is_accessible", False),
                    "is_stable": universe_data.get("is_stable", False),
                    "connection_count": len(universe_data.get("connection_points", []))
                })
            
            return universes
            
        except Exception as e:
            logger.error(f"Error listing universes: {e}")
            return []
    
    def get_traveler_info(self, traveler_id: str) -> Dict[str, Any]:
        """Get traveler information"""
        try:
            traveler = self.travelers.get(traveler_id)
            if not traveler:
                return {"error": "Traveler not found"}
            
            return {
                "id": traveler.id,
                "name": traveler.name,
                "current_universe": traveler.current_universe,
                "home_universe": traveler.home_universe,
                "visited_universes": traveler.visited_universes,
                "travel_count": len(traveler.travel_history),
                "energy_reserves": traveler.energy_reserves,
                "navigation_skill": traveler.navigation_skill,
                "consciousness_level": traveler.consciousness_level,
                "is_active": traveler.is_active,
                "created_at": traveler.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting traveler info: {e}")
            return {"error": str(e)}
    
    def list_travelers(self) -> List[Dict[str, Any]]:
        """List all travelers"""
        try:
            travelers = []
            
            for traveler in self.travelers.values():
                travelers.append({
                    "id": traveler.id,
                    "name": traveler.name,
                    "current_universe": traveler.current_universe,
                    "visited_count": len(traveler.visited_universes),
                    "travel_count": len(traveler.travel_history),
                    "energy_reserves": traveler.energy_reserves,
                    "navigation_skill": traveler.navigation_skill,
                    "consciousness_level": traveler.consciousness_level,
                    "is_active": traveler.is_active
                })
            
            return travelers
            
        except Exception as e:
            logger.error(f"Error listing travelers: {e}")
            return []
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get multiverse navigation system status"""
        try:
            return {
                "total_universes": len(self.topology.universe_graph.nodes),
                "accessible_universes": len([
                    u for u in self.topology.universe_graph.nodes.values()
                    if u.get("is_accessible", False)
                ]),
                "stable_universes": len([
                    u for u in self.topology.universe_graph.nodes.values()
                    if u.get("is_stable", False)
                ]),
                "active_wormholes": len([w for w in self.topology.wormholes.values() if w.is_active]),
                "total_travelers": len(self.travelers),
                "active_travelers": len([t for t in self.travelers.values() if t.is_active]),
                "active_travels": len(self.active_travels),
                "supported_universe_types": len(UniverseType),
                "supported_navigation_methods": len(NavigationMethod)
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {}

# Global multiverse navigation system
multiverse_navigation_system = MultiverseNavigator()

# API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/multiverse", tags=["multiverse_navigation"])

class UniverseDiscoveryRequest(BaseModel):
    name: str
    universe_type: str
    parameter_variations: Dict[str, float]

class WormholeCreationRequest(BaseModel):
    entrance_universe: str
    exit_universe: str
    stability: float = 0.8

class TravelerRegistrationRequest(BaseModel):
    name: str
    home_universe: str = "prime_universe"

class NavigationRequest(BaseModel):
    traveler_id: str
    target_universe: str
    method: str

@router.post("/universes/discover")
async def discover_universe(request: UniverseDiscoveryRequest):
    """Discover new universe"""
    try:
        universe_type = UniverseType(request.universe_type)
        
        # Convert string parameter keys to enum
        parameter_variations = {}
        for param_str, value in request.parameter_variations.items():
            try:
                param_enum = UniverseParameter(param_str)
                parameter_variations[param_enum] = value
            except ValueError:
                continue
        
        universe = await multiverse_navigation_system.discover_universe(
            request.name, universe_type, parameter_variations
        )
        
        return asdict(universe)
    except Exception as e:
        logger.error(f"Error discovering universe: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/wormholes/create")
async def create_wormhole(request: WormholeCreationRequest):
    """Create wormhole between universes"""
    try:
        wormhole = await multiverse_navigation_system.create_wormhole(
            request.entrance_universe, request.exit_universe, request.stability
        )
        return asdict(wormhole)
    except Exception as e:
        logger.error(f"Error creating wormhole: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/travelers/register")
async def register_traveler(request: TravelerRegistrationRequest):
    """Register multiverse traveler"""
    try:
        traveler = await multiverse_navigation_system.register_traveler(
            request.name, request.home_universe
        )
        return asdict(traveler)
    except Exception as e:
        logger.error(f"Error registering traveler: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/navigate")
async def navigate_to_universe(request: NavigationRequest):
    """Navigate traveler to target universe"""
    try:
        method = NavigationMethod(request.method)
        route = await multiverse_navigation_system.navigate_to_universe(
            request.traveler_id, request.target_universe, method
        )
        return asdict(route)
    except Exception as e:
        logger.error(f"Error navigating to universe: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/universes/{universe_id}")
async def get_universe_info(universe_id: str):
    """Get universe information"""
    try:
        info = multiverse_navigation_system.get_universe_info(universe_id)
        return info
    except Exception as e:
        logger.error(f"Error getting universe info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/universes")
async def list_universes():
    """List all universes"""
    try:
        universes = multiverse_navigation_system.list_universes()
        return {"universes": universes}
    except Exception as e:
        logger.error(f"Error listing universes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/travelers/{traveler_id}")
async def get_traveler_info(traveler_id: str):
    """Get traveler information"""
    try:
        info = multiverse_navigation_system.get_traveler_info(traveler_id)
        return info
    except Exception as e:
        logger.error(f"Error getting traveler info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/travelers")
async def list_travelers():
    """List all travelers"""
    try:
        travelers = multiverse_navigation_system.list_travelers()
        return {"travelers": travelers}
    except Exception as e:
        logger.error(f"Error listing travelers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/universe-types")
async def list_universe_types():
    """List supported universe types"""
    try:
        types = [utype.value for utype in UniverseType]
        return {"universe_types": types}
    except Exception as e:
        logger.error(f"Error listing universe types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/navigation-methods")
async def list_navigation_methods():
    """List supported navigation methods"""
    try:
        methods = [method.value for method in NavigationMethod]
        return {"navigation_methods": methods}
    except Exception as e:
        logger.error(f"Error listing navigation methods: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_system_status():
    """Get multiverse navigation system status"""
    try:
        status = multiverse_navigation_system.get_system_status()
        return status
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
