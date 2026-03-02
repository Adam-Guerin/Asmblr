"""
Reality Simulation Engine for Asmblr
Complete reality simulation, creation, and manipulation system
"""

import asyncio
import logging
from datetime import datetime
from typing import Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import numpy as np
import math

logger = logging.getLogger(__name__)

class RealityType(Enum):
    """Types of realities"""
    BASE_REALITY = "base_reality"
    SIMULATED_REALITY = "simulated_reality"
    VIRTUAL_REALITY = "virtual_reality"
    AUGMENTED_REALITY = "augmented_reality"
    MIXED_REALITY = "mixed_reality"
    DREAM_REALITY = "dream_reality"
    QUANTUM_REALITY = "quantum_reality"
    PARALLEL_REALITY = "parallel_reality"
    ALTERNATE_REALITY = "alternate_reality"
    SYNTHETIC_REALITY = "synthetic_reality"

class SimulationComplexity(Enum):
    """Simulation complexity levels"""
    BASIC = "basic"
    STANDARD = "standard"
    ADVANCED = "advanced"
    QUANTUM = "quantum"
    NEURAL = "neural"
    CONSCIOUSNESS = "consciousness"
    OMNIPRESENT = "omnipresent"
    TRANSCENDENT = "transcendent"
    ABSOLUTE = "absolute"

class PhysicsEngine(Enum):
    """Physics engine types"""
    NEWTONIAN = "newtonian"
    RELATIVISTIC = "relativistic"
    QUANTUM = "quantum"
    STRING_THEORY = "string_theory"
    M_THEORY = "m_theory"
    LOOP_QUANTUM = "loop_quantum"
    CAUSAL_SET = "causal_set"
    INFORMATION_BASED = "information_based"
    CONSCIOUSNESS_BASED = "consciousness_based"
    CUSTOM = "custom"

class RealityParameter(Enum):
    """Reality parameters"""
    GRAVITY = "gravity"
    TIME_FLOW = "time_flow"
    SPACE_DIMENSIONS = "space_dimensions"
    SPEED_OF_LIGHT = "speed_of_light"
    PLANCK_CONSTANT = "planck_constant"
    ENTROPY = "entropy"
    CAUSALITY = "causality"
    CONSCIOUSNESS_INFLUENCE = "consciousness_influence"
    QUANTUM_COHERENCE = "quantum_coherence"
    REALITY_STABILITY = "reality_stability"

@dataclass
class RealityInstance:
    """Reality instance"""
    id: str
    name: str
    reality_type: RealityType
    complexity: SimulationComplexity
    physics_engine: PhysicsEngine
    parameters: dict[RealityParameter, float]
    entities: list[str]
    size: tuple[float, ...]  # Dimensions in meters
    time_scale: float  # Time scaling factor
    is_active: bool
    created_at: datetime
    last_updated: datetime

@dataclass
class SimulationEntity:
    """Entity within reality simulation"""
    id: str
    name: str
    entity_type: str
    position: np.ndarray
    velocity: np.ndarray
    properties: dict[str, Any]
    consciousness_level: float
    reality_influence: float
    is_active: bool
    created_at: datetime

@dataclass
class RealityEvent:
    """Event within reality"""
    id: str
    timestamp: datetime
    event_type: str
    entities_involved: list[str]
    location: np.ndarray
    parameters: dict[str, Any]
    causality_chain: list[str]
    probability: float
    occurred: bool

@dataclass
class SimulationState:
    """Current simulation state"""
    id: str
    reality_id: str
    time_step: int
    simulation_time: float
    total_entities: int
    active_events: int
    computational_load: float
    stability: float
    created_at: datetime

class PhysicsSimulation:
    """Physics simulation engine"""
    
    def __init__(self, physics_engine: PhysicsEngine):
        self.engine_type = physics_engine
        self.G = 6.67430e-11  # Gravitational constant
        self.c = 299792458.0  # Speed of light
        self.h = 6.62607015e-34  # Planck constant
        self.k_B = 1.380649e-23  # Boltzmann constant
        
    def update_entities(self, entities: list[SimulationEntity], 
                        dt: float, reality_params: dict[RealityParameter, float]) -> list[SimulationEntity]:
        """Update entity positions and velocities"""
        try:
            updated_entities = []
            
            for entity in entities:
                if not entity.is_active:
                    updated_entities.append(entity)
                    continue
                
                # Calculate forces based on physics engine
                if self.engine_type == PhysicsEngine.NEWTONIAN:
                    acceleration = self._newtonian_forces(entity, entities, reality_params)
                elif self.engine_type == PhysicsEngine.RELATIVISTIC:
                    acceleration = self._relativistic_forces(entity, entities, reality_params)
                elif self.engine_type == PhysicsEngine.QUANTUM:
                    acceleration = self._quantum_forces(entity, entities, reality_params)
                elif self.engine_type == PhysicsEngine.CONSCIOUSNESS_BASED:
                    acceleration = self._consciousness_forces(entity, entities, reality_params)
                else:
                    acceleration = np.zeros_like(entity.position)
                
                # Update velocity and position
                new_velocity = entity.velocity + acceleration * dt
                new_position = entity.position + new_velocity * dt
                
                # Create updated entity
                updated_entity = SimulationEntity(
                    id=entity.id,
                    name=entity.name,
                    entity_type=entity.entity_type,
                    position=new_position,
                    velocity=new_velocity,
                    properties=entity.properties,
                    consciousness_level=entity.consciousness_level,
                    reality_influence=entity.reality_influence,
                    is_active=entity.is_active,
                    created_at=entity.created_at
                )
                
                updated_entities.append(updated_entity)
            
            return updated_entities
            
        except Exception as e:
            logger.error(f"Error updating entities: {e}")
            return entities
    
    def _newtonian_forces(self, entity: SimulationEntity, 
                          all_entities: list[SimulationEntity],
                          reality_params: dict[RealityParameter, float]) -> np.ndarray:
        """Calculate Newtonian forces"""
        try:
            force = np.zeros_like(entity.position)
            
            # Gravitational force
            gravity = reality_params.get(RealityParameter.GRAVITY, 9.81)
            if len(entity.position) >= 3:
                force[2] -= gravity  # Downward gravity in z-direction
            
            # Inter-entity forces
            for other in all_entities:
                if other.id != entity.id and other.is_active:
                    # Calculate distance
                    r_vec = other.position - entity.position
                    r = np.linalg.norm(r_vec)
                    
                    if r > 0.01:  # Avoid singularity
                        # Gravitational attraction
                        if "mass" in entity.properties and "mass" in other.properties:
                            F_gravity = self.G * entity.properties["mass"] * other.properties["mass"] / (r**2)
                            force += F_gravity * r_vec / r
            
            return force / entity.properties.get("mass", 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating Newtonian forces: {e}")
            return np.zeros_like(entity.position)
    
    def _relativistic_forces(self, entity: SimulationEntity,
                            all_entities: list[SimulationEntity],
                            reality_params: dict[RealityParameter, float]) -> np.ndarray:
        """Calculate relativistic forces"""
        try:
            # Start with Newtonian forces
            force = self._newtonian_forces(entity, all_entities, reality_params)
            
            # Add relativistic corrections
            c = reality_params.get(RealityParameter.SPEED_OF_LIGHT, self.c)
            v = np.linalg.norm(entity.velocity)
            
            if v > 0:
                # Lorentz factor
                gamma = 1.0 / math.sqrt(1.0 - (v/c)**2)
                
                # Relativistic mass increase
                relativistic_mass = entity.properties.get("mass", 1.0) * gamma
                
                # Adjust force for relativistic effects
                force = force / gamma
            
            return force
            
        except Exception as e:
            logger.error(f"Error calculating relativistic forces: {e}")
            return np.zeros_like(entity.position)
    
    def _quantum_forces(self, entity: SimulationEntity,
                        all_entities: list[SimulationEntity],
                        reality_params: dict[RealityParameter, float]) -> np.ndarray:
        """Calculate quantum forces"""
        try:
            # Quantum uncertainty
            h = reality_params.get(RealityParameter.PLANCK_CONSTANT, self.h)
            
            # Heisenberg uncertainty principle
            if "mass" in entity.properties:
                delta_x = 1e-10  # Position uncertainty
                delta_p = h / (2 * delta_x)  # Momentum uncertainty
                
                # Random quantum force
                quantum_force = np.random.randn(len(entity.position)) * delta_p
                
                return quantum_force / entity.properties["mass"]
            
            return np.zeros_like(entity.position)
            
        except Exception as e:
            logger.error(f"Error calculating quantum forces: {e}")
            return np.zeros_like(entity.position)
    
    def _consciousness_forces(self, entity: SimulationEntity,
                              all_entities: list[SimulationEntity],
                              reality_params: dict[RealityParameter, float]) -> np.ndarray:
        """Calculate consciousness-based forces"""
        try:
            force = np.zeros_like(entity.position)
            
            # Consciousness influence on reality
            consciousness_influence = reality_params.get(RealityParameter.CONSCIOUSNESS_INFLUENCE, 0.0)
            
            if entity.consciousness_level > 0.5:
                # Conscious entities can influence reality
                intention_force = entity.reality_influence * consciousness_influence
                
                # Random direction based on consciousness
                if np.linalg.norm(entity.position) > 0:
                    direction = entity.position / np.linalg.norm(entity.position)
                else:
                    direction = np.random.randn(len(entity.position))
                    direction = direction / np.linalg.norm(direction)
                
                force = intention_force * direction
            
            return force
            
        except Exception as e:
            logger.error(f"Error calculating consciousness forces: {e}")
            return np.zeros_like(entity.position)

class RealityGenerator:
    """Reality generation and creation"""
    
    def __init__(self):
        self.reality_templates = self._initialize_templates()
        
    def _initialize_templates(self) -> dict[str, dict[str, Any]]:
        """Initialize reality templates"""
        return {
            "earth_like": {
                "gravity": 9.81,
                "time_flow": 1.0,
                "space_dimensions": 3,
                "speed_of_light": 299792458.0,
                "planck_constant": 6.62607015e-34,
                "entropy": 1.0,
                "causality": 1.0,
                "consciousness_influence": 0.0,
                "quantum_coherence": 0.5,
                "reality_stability": 1.0
            },
            "quantum_reality": {
                "gravity": 0.0,
                "time_flow": 0.5,
                "space_dimensions": 11,
                "speed_of_light": 299792458.0,
                "planck_constant": 6.62607015e-34,
                "entropy": 0.5,
                "causality": 0.5,
                "consciousness_influence": 0.8,
                "quantum_coherence": 0.9,
                "reality_stability": 0.7
            },
            "dream_reality": {
                "gravity": 5.0,
                "time_flow": 0.3,
                "space_dimensions": 4,
                "speed_of_light": 100000.0,
                "planck_constant": 1e-33,
                "entropy": 0.3,
                "causality": 0.2,
                "consciousness_influence": 0.9,
                "quantum_coherence": 0.8,
                "reality_stability": 0.4
            },
            "synthetic_reality": {
                "gravity": 15.0,
                "time_flow": 2.0,
                "space_dimensions": 2,
                "speed_of_light": 500000.0,
                "planck_constant": 1e-35,
                "entropy": 2.0,
                "causality": 1.5,
                "consciousness_influence": 0.1,
                "quantum_coherence": 0.2,
                "reality_stability": 1.2
            }
        }
    
    def create_reality(self, name: str, reality_type: RealityType,
                      complexity: SimulationComplexity,
                      physics_engine: PhysicsEngine,
                      template: str = "earth_like") -> RealityInstance:
        """Create new reality instance"""
        try:
            # Get template parameters
            template_params = self.reality_templates.get(template, self.reality_templates["earth_like"])
            
            # Convert to RealityParameter enum
            parameters = {}
            for param_name, value in template_params.items():
                try:
                    param_enum = RealityParameter(param_name)
                    parameters[param_enum] = value
                except ValueError:
                    continue
            
            # Determine reality size based on complexity
            if complexity == SimulationComplexity.BASIC:
                size = (100.0, 100.0, 100.0)  # 100m cube
            elif complexity == SimulationComplexity.STANDARD:
                size = (1000.0, 1000.0, 1000.0)  # 1km cube
            elif complexity == SimulationComplexity.ADVANCED:
                size = (10000.0, 10000.0, 10000.0)  # 10km cube
            elif complexity == SimulationComplexity.QUANTUM:
                size = tuple([1e-10] * 11)  # Quantum scale, 11 dimensions
            else:
                size = (1e6, 1e6, 1e6)  # Large scale
            
            # Create reality instance
            reality = RealityInstance(
                id=str(uuid.uuid4()),
                name=name,
                reality_type=reality_type,
                complexity=complexity,
                physics_engine=physics_engine,
                parameters=parameters,
                entities=[],
                size=size,
                time_scale=1.0,
                is_active=True,
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
            
            logger.info(f"Created reality: {reality.id}")
            return reality
            
        except Exception as e:
            logger.error(f"Error creating reality: {e}")
            raise
    
    def generate_entities(self, reality: RealityInstance, 
                         num_entities: int = 100) -> list[SimulationEntity]:
        """Generate entities for reality"""
        try:
            entities = []
            
            for i in range(num_entities):
                # Random position within reality bounds
                position = np.array([
                    np.random.uniform(-size/2, size/2) 
                    for size in reality.size
                ])
                
                # Random velocity
                velocity = np.random.randn(len(position)) * 10.0
                
                # Entity properties
                entity_type = np.random.choice(["particle", "organism", "conscious_being", "object"])
                properties = {
                    "mass": np.random.uniform(1.0, 100.0),
                    "charge": np.random.uniform(-1.0, 1.0),
                    "energy": np.random.uniform(100.0, 1000.0)
                }
                
                # Consciousness level based on entity type
                if entity_type == "conscious_being":
                    consciousness_level = np.random.uniform(0.7, 1.0)
                    reality_influence = np.random.uniform(0.5, 1.0)
                elif entity_type == "organism":
                    consciousness_level = np.random.uniform(0.3, 0.7)
                    reality_influence = np.random.uniform(0.1, 0.5)
                else:
                    consciousness_level = 0.0
                    reality_influence = 0.0
                
                entity = SimulationEntity(
                    id=str(uuid.uuid4()),
                    name=f"entity_{i}",
                    entity_type=entity_type,
                    position=position,
                    velocity=velocity,
                    properties=properties,
                    consciousness_level=consciousness_level,
                    reality_influence=reality_influence,
                    is_active=True,
                    created_at=datetime.now()
                )
                
                entities.append(entity)
            
            logger.info(f"Generated {len(entities)} entities for reality {reality.id}")
            return entities
            
        except Exception as e:
            logger.error(f"Error generating entities: {e}")
            return []

class RealitySimulation:
    """Main reality simulation system"""
    
    def __init__(self):
        self.realities: dict[str, RealityInstance] = {}
        self.entities: dict[str, list[SimulationEntity]] = {}
        self.physics_engines: dict[str, PhysicsSimulation] = {}
        self.reality_generator = RealityGenerator()
        self.simulation_states: dict[str, SimulationState] = {}
        
        # Start background processes
        asyncio.create_task(self._simulation_loop())
        asyncio.create_task(self._reality_stability_monitoring())
        asyncio.create_task(self._consciousness_integration())
    
    async def create_reality(self, name: str, reality_type: RealityType,
                             complexity: SimulationComplexity,
                             physics_engine: PhysicsEngine,
                             template: str = "earth_like") -> RealityInstance:
        """Create new reality"""
        try:
            # Create reality instance
            reality = self.reality_generator.create_reality(
                name, reality_type, complexity, physics_engine, template
            )
            
            # Generate entities
            entities = self.reality_generator.generate_entities(reality)
            
            # Create physics engine
            physics_sim = PhysicsSimulation(physics_engine)
            
            # Store everything
            self.realities[reality.id] = reality
            self.entities[reality.id] = entities
            self.physics_engines[reality.id] = physics_sim
            
            # Create initial simulation state
            sim_state = SimulationState(
                id=str(uuid.uuid4()),
                reality_id=reality.id,
                time_step=0,
                simulation_time=0.0,
                total_entities=len(entities),
                active_events=0,
                computational_load=0.0,
                stability=1.0,
                created_at=datetime.now()
            )
            
            self.simulation_states[reality.id] = sim_state
            
            logger.info(f"Created and initialized reality: {reality.id}")
            return reality
            
        except Exception as e:
            logger.error(f"Error creating reality: {e}")
            raise
    
    async def simulate_step(self, reality_id: str, dt: float = 0.01) -> SimulationState:
        """Simulate one time step"""
        try:
            reality = self.realities.get(reality_id)
            if not reality or not reality.is_active:
                raise ValueError(f"Reality {reality_id} not found or inactive")
            
            entities = self.entities.get(reality_id, [])
            physics_sim = self.physics_engines.get(reality_id)
            
            if not physics_sim:
                raise ValueError(f"Physics engine not found for reality {reality_id}")
            
            # Update entities
            updated_entities = physics_sim.update_entities(
                entities, dt, reality.parameters
            )
            
            # Update entities storage
            self.entities[reality_id] = updated_entities
            
            # Update simulation state
            sim_state = self.simulation_states[reality_id]
            sim_state.time_step += 1
            sim_state.simulation_time += dt * reality.time_scale
            sim_state.total_entities = len(updated_entities)
            sim_state.computational_load = self._calculate_computational_load(reality, updated_entities)
            sim_state.stability = self._calculate_stability(reality, updated_entities)
            sim_state.last_updated = datetime.now()
            
            return sim_state
            
        except Exception as e:
            logger.error(f"Error simulating step: {e}")
            raise
    
    def _calculate_computational_load(self, reality: RealityInstance,
                                      entities: list[SimulationEntity]) -> float:
        """Calculate computational load"""
        try:
            # Base load based on complexity
            complexity_load = {
                SimulationComplexity.BASIC: 1.0,
                SimulationComplexity.STANDARD: 10.0,
                SimulationComplexity.ADVANCED: 100.0,
                SimulationComplexity.QUANTUM: 1000.0,
                SimulationComplexity.NEURAL: 10000.0,
                SimulationComplexity.CONSCIOUSNESS: 100000.0,
                SimulationComplexity.OMNIPRESENT: 1000000.0,
                SimulationComplexity.TRANSCENDENT: 10000000.0,
                SimulationComplexity.ABSOLUTE: 100000000.0
            }
            
            base_load = complexity_load.get(reality.complexity, 1.0)
            
            # Entity load
            entity_load = len(entities) * 0.1
            
            # Physics engine load
            physics_load = {
                PhysicsEngine.NEWTONIAN: 1.0,
                PhysicsEngine.RELATIVISTIC: 10.0,
                PhysicsEngine.QUANTUM: 100.0,
                PhysicsEngine.STRING_THEORY: 1000.0,
                PhysicsEngine.M_THEORY: 10000.0,
                PhysicsEngine.CONSCIOUSNESS_BASED: 100000.0
            }
            
            physics_multiplier = physics_load.get(reality.physics_engine, 1.0)
            
            total_load = base_load + entity_load
            total_load *= physics_multiplier
            
            return total_load
            
        except Exception as e:
            logger.error(f"Error calculating computational load: {e}")
            return 1.0
    
    def _calculate_stability(self, reality: RealityInstance,
                             entities: list[SimulationEntity]) -> float:
        """Calculate reality stability"""
        try:
            stability = 1.0
            
            # Base stability from parameters
            stability *= reality.parameters.get(RealityParameter.REALITY_STABILITY, 1.0)
            
            # Consciousness influence
            total_consciousness = sum(e.consciousness_level for e in entities)
            avg_consciousness = total_consciousness / len(entities) if entities else 0.0
            
            if reality.parameters.get(RealityParameter.CONSCIOUSNESS_INFLUENCE, 0.0) > 0.5:
                # High consciousness influence can destabilize reality
                stability *= (1.0 - avg_consciousness * 0.1)
            else:
                # Low consciousness influence, consciousness stabilizes
                stability *= (1.0 + avg_consciousness * 0.05)
            
            # Quantum coherence effects
            quantum_coherence = reality.parameters.get(RealityParameter.QUANTUM_COHERENCE, 0.5)
            if reality.physics_engine == PhysicsEngine.QUANTUM:
                stability *= (0.5 + quantum_coherence * 0.5)
            
            # Ensure stability is within bounds
            return max(0.0, min(1.0, stability))
            
        except Exception as e:
            logger.error(f"Error calculating stability: {e}")
            return 0.5
    
    async def _simulation_loop(self):
        """Background simulation loop"""
        while True:
            try:
                # Simulate all active realities
                for reality_id, reality in self.realities.items():
                    if reality.is_active:
                        await self.simulate_step(reality_id, 0.01)
                
                # Wait before next simulation step
                await asyncio.sleep(0.1)  # 10 Hz simulation
                
            except Exception as e:
                logger.error(f"Error in simulation loop: {e}")
                await asyncio.sleep(1)
    
    async def _reality_stability_monitoring(self):
        """Background reality stability monitoring"""
        while True:
            try:
                # Monitor stability of all realities
                for reality_id, reality in self.realities.items():
                    sim_state = self.simulation_states.get(reality_id)
                    
                    if sim_state and sim_state.stability < 0.3:
                        logger.warning(f"Reality {reality_id} stability critical: {sim_state.stability}")
                        
                        # Attempt stabilization
                        await self._stabilize_reality(reality_id)
                
                # Wait before next monitoring
                await asyncio.sleep(60)  # Monitor every minute
                
            except Exception as e:
                logger.error(f"Error in stability monitoring: {e}")
                await asyncio.sleep(10)
    
    async def _stabilize_reality(self, reality_id: str):
        """Stabilize unstable reality"""
        try:
            reality = self.realities.get(reality_id)
            if not reality:
                return
            
            # Increase reality stability parameter
            current_stability = reality.parameters.get(RealityParameter.REALITY_STABILITY, 1.0)
            reality.parameters[RealityParameter.REALITY_STABILITY] = min(1.0, current_stability + 0.1)
            
            # Reduce consciousness influence if too high
            consciousness_influence = reality.parameters.get(RealityParameter.CONSCIOUSNESS_INFLUENCE, 0.0)
            if consciousness_influence > 0.7:
                reality.parameters[RealityParameter.CONSCIOUSNESS_INFLUENCE] *= 0.9
            
            logger.info(f"Stabilized reality: {reality_id}")
            
        except Exception as e:
            logger.error(f"Error stabilizing reality: {e}")
    
    async def _consciousness_integration(self):
        """Background consciousness integration"""
        while True:
            try:
                # Integrate consciousness effects
                for reality_id, entities in self.entities.items():
                    reality = self.realities.get(reality_id)
                    
                    if reality and reality.parameters.get(RealityParameter.CONSCIOUSNESS_INFLUENCE, 0.0) > 0:
                        # Update consciousness levels
                        for entity in entities:
                            if entity.entity_type == "conscious_being":
                                # Consciousness evolves
                                entity.consciousness_level = min(1.0, 
                                    entity.consciousness_level + 0.001)
                                entity.reality_influence = min(1.0,
                                    entity.reality_influence + 0.001)
                
                # Wait before next integration
                await asyncio.sleep(30)  # Integrate every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in consciousness integration: {e}")
                await asyncio.sleep(5)
    
    def get_reality_info(self, reality_id: str) -> dict[str, Any]:
        """Get reality information"""
        try:
            reality = self.realities.get(reality_id)
            if not reality:
                return {"error": "Reality not found"}
            
            sim_state = self.simulation_states.get(reality_id)
            entities = self.entities.get(reality_id, [])
            
            return {
                "id": reality.id,
                "name": reality.name,
                "reality_type": reality.reality_type.value,
                "complexity": reality.complexity.value,
                "physics_engine": reality.physics_engine.value,
                "parameters": {param.value: value for param, value in reality.parameters.items()},
                "size": reality.size,
                "time_scale": reality.time_scale,
                "is_active": reality.is_active,
                "total_entities": len(entities),
                "conscious_entities": len([e for e in entities if e.consciousness_level > 0.5]),
                "simulation_state": {
                    "time_step": sim_state.time_step if sim_state else 0,
                    "simulation_time": sim_state.simulation_time if sim_state else 0.0,
                    "stability": sim_state.stability if sim_state else 1.0,
                    "computational_load": sim_state.computational_load if sim_state else 0.0
                } if sim_state else {},
                "created_at": reality.created_at.isoformat(),
                "last_updated": reality.last_updated.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting reality info: {e}")
            return {"error": str(e)}
    
    def list_realities(self) -> list[dict[str, Any]]:
        """List all realities"""
        try:
            realities = []
            
            for reality in self.realities.values():
                sim_state = self.simulation_states.get(reality.id)
                entities = self.entities.get(reality.id, [])
                
                realities.append({
                    "id": reality.id,
                    "name": reality.name,
                    "reality_type": reality.reality_type.value,
                    "complexity": reality.complexity.value,
                    "is_active": reality.is_active,
                    "total_entities": len(entities),
                    "stability": sim_state.stability if sim_state else 1.0,
                    "computational_load": sim_state.computational_load if sim_state else 0.0
                })
            
            return realities
            
        except Exception as e:
            logger.error(f"Error listing realities: {e}")
            return []

# Global reality simulation system
reality_simulation_system = RealitySimulation()

# API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/reality_simulation", tags=["reality_simulation"])

class RealityCreationRequest(BaseModel):
    name: str
    reality_type: str
    complexity: str
    physics_engine: str
    template: str = "earth_like"

class EntityGenerationRequest(BaseModel):
    reality_id: str
    num_entities: int = 100

@router.post("/realities/create")
async def create_reality(request: RealityCreationRequest):
    """Create new reality"""
    try:
        reality_type = RealityType(request.reality_type)
        complexity = SimulationComplexity(request.complexity)
        physics_engine = PhysicsEngine(request.physics_engine)
        
        reality = await reality_simulation_system.create_reality(
            request.name, reality_type, complexity, physics_engine, request.template
        )
        
        return asdict(reality)
    except Exception as e:
        logger.error(f"Error creating reality: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/realities/{reality_id}/simulate")
async def simulate_step(reality_id: str, dt: float = 0.01):
    """Simulate one time step"""
    try:
        sim_state = await reality_simulation_system.simulate_step(reality_id, dt)
        return asdict(sim_state)
    except Exception as e:
        logger.error(f"Error simulating step: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/entities/generate")
async def generate_entities(request: EntityGenerationRequest):
    """Generate entities for reality"""
    try:
        reality = reality_simulation_system.realities.get(request.reality_id)
        if not reality:
            raise HTTPException(status_code=404, detail="Reality not found")
        
        entities = reality_simulation_system.reality_generator.generate_entities(
            reality, request.num_entities
        )
        
        reality_simulation_system.entities[request.reality_id] = entities
        
        return {
            "reality_id": request.reality_id,
            "num_entities": len(entities),
            "entities": [{"id": e.id, "name": e.name, "type": e.entity_type} for e in entities[:10]]
        }
    except Exception as e:
        logger.error(f"Error generating entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/realities/{reality_id}")
async def get_reality_info(reality_id: str):
    """Get reality information"""
    try:
        info = reality_simulation_system.get_reality_info(reality_id)
        return info
    except Exception as e:
        logger.error(f"Error getting reality info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/realities")
async def list_realities():
    """List all realities"""
    try:
        realities = reality_simulation_system.list_realities()
        return {"realities": realities}
    except Exception as e:
        logger.error(f"Error listing realities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reality-types")
async def list_reality_types():
    """List supported reality types"""
    try:
        types = [rtype.value for rtype in RealityType]
        return {"reality_types": types}
    except Exception as e:
        logger.error(f"Error listing reality types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/complexity-levels")
async def list_complexity_levels():
    """List simulation complexity levels"""
    try:
        levels = [level.value for level in SimulationComplexity]
        return {"complexity_levels": levels}
    except Exception as e:
        logger.error(f"Error listing complexity levels: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/physics-engines")
async def list_physics_engines():
    """List supported physics engines"""
    try:
        engines = [engine.value for engine in PhysicsEngine]
        return {"physics_engines": engines}
    except Exception as e:
        logger.error(f"Error listing physics engines: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reality-templates")
async def list_reality_templates():
    """List reality templates"""
    try:
        templates = list(reality_simulation_system.reality_generator.reality_templates.keys())
        return {"reality_templates": templates}
    except Exception as e:
        logger.error(f"Error listing reality templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_system_status():
    """Get reality simulation system status"""
    try:
        total_entities = sum(len(entities) for entities in reality_simulation_system.entities.values())
        total_load = sum(
            state.computational_load 
            for state in reality_simulation_system.simulation_states.values()
        )
        avg_stability = 0.0
        if reality_simulation_system.simulation_states:
            avg_stability = sum(
                state.stability 
                for state in reality_simulation_system.simulation_states.values()
            ) / len(reality_simulation_system.simulation_states)
        
        return {
            "total_realities": len(reality_simulation_system.realities),
            "active_realities": len([r for r in reality_simulation_system.realities.values() if r.is_active]),
            "total_entities": total_entities,
            "total_computational_load": total_load,
            "average_stability": avg_stability,
            "supported_reality_types": len(RealityType),
            "supported_physics_engines": len(PhysicsEngine),
            "complexity_levels": len(SimulationComplexity)
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
