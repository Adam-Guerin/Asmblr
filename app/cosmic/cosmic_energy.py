"""
Cosmic Energy Harvesting System for Asmblr
Harvesting and utilization of cosmic energy from universal sources
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

class EnergySourceType(Enum):
    """Types of cosmic energy sources"""
    SOLAR = "solar"
    STELLAR = "stellar"
    QUASAR = "quasar"
    PULSAR = "pulsar"
    BLACK_HOLE = "black_hole"
    NEUTRON_STAR = "neutron_star"
    DARK_MATTER = "dark_matter"
    DARK_ENERGY = "dark_energy"
    ZERO_POINT = "zero_point"
    VACUUM_ENERGY = "vacuum_energy"
    COSMIC_BACKGROUND = "cosmic_background"
    GRAVITATIONAL_WAVES = "gravitational_waves"
    QUANTUM_FLUCTUATIONS = "quantum_fluctuations"

class EnergyForm(Enum):
    """Forms of cosmic energy"""
    ELECTROMAGNETIC = "electromagnetic"
    GRAVITATIONAL = "gravitational"
    QUANTUM = "quantum"
    THERMAL = "thermal"
    KINETIC = "kinetic"
    POTENTIAL = "potential"
    RADIATION = "radiation"
    PARTICLE = "particle"
    WAVE = "wave"
    FIELD = "field"

class HarvestingMethod(Enum):
    """Methods of energy harvesting"""
    PHOTOVOLTAIC = "photovoltaic"
    THERMODYNAMIC = "thermodynamic"
    ELECTROMAGNETIC = "electromagnetic"
    GRAVITATIONAL_WAVE = "gravitational_wave"
    QUANTUM_TUNNELING = "quantum_tunneling"
    CASIMIR_EFFECT = "casimir_effect"
    ZERO_POINT_EXTRACTION = "zero_point_extraction"
    STIRLING_ENGINE = "stirling_engine"
    TESLA_COIL = "tesla_coil"
    PLASMA_CONVERSION = "plasma_conversion"
    FUSION_REACTOR = "fusion_reactor"
    ANTIMATTER_ANNIHILATION = "antimatter_annihilation"

@dataclass
class EnergySource:
    """Cosmic energy source"""
    id: str
    name: str
    source_type: EnergySourceType
    energy_form: EnergyForm
    location: Tuple[float, float, float]  # 3D coordinates in light years
    distance: float  # Distance from Earth in light years
    power_output: float  # Watts
    energy_density: float  # J/m³
    accessibility: float  # 0-1
    stability: float  # 0-1
    harvesting_methods: List[HarvestingMethod]
    discovered_at: datetime
    last_measured: datetime

@dataclass
class EnergyHarvester:
    """Energy harvesting device"""
    id: str
    name: str
    harvesting_method: HarvestingMethod
    efficiency: float  # 0-1
    capacity: float  # Watts
    energy_sources: List[str]
    operational_status: str
    energy_collected: float  # Joules
    operating_time: float  # seconds
    maintenance_required: bool
    created_at: datetime
    last_maintenance: datetime

@dataclass
class EnergyStorage:
    """Energy storage system"""
    id: str
    name: str
    storage_type: str
    capacity: float  # Joules
    current_charge: float  # Joules
    charge_rate: float  # Watts
    discharge_rate: float  # Watts
    efficiency: float  # 0-1
    temperature: float  # Kelvin
    is_active: bool
    created_at: datetime
    last_updated: datetime

@dataclass
class EnergyTransaction:
    """Energy transaction record"""
    id: str
    source_id: str
    harvester_id: str
    storage_id: str
    energy_amount: float  # Joules
    harvesting_method: HarvestingMethod
    efficiency: float
    timestamp: datetime
    duration: float  # seconds
    cost: float  # Credits/units

class CosmicEnergyDetector:
    """Cosmic energy detection and analysis"""
    
    def __init__(self):
        self.detection_range = 1000.0  # light years
        self.sensitivity = 1e-20  # Watts
        self.known_sources: Dict[str, EnergySource] = {}
        
    def scan_for_energy_sources(self, center: Tuple[float, float, float],
                                radius: float) -> List[EnergySource]:
        """Scan for cosmic energy sources"""
        try:
            discovered_sources = []
            
            # Generate synthetic energy sources based on realistic distributions
            num_sources = np.random.poisson(radius / 100)  # Average 1 source per 100 light years
            
            for i in range(num_sources):
                # Random position within radius
                theta = np.random.uniform(0, 2 * np.pi)
                phi = np.random.uniform(0, np.pi)
                r = np.random.uniform(0, radius)
                
                x = center[0] + r * np.sin(phi) * np.cos(theta)
                y = center[1] + r * np.sin(phi) * np.sin(theta)
                z = center[2] + r * np.cos(phi)
                
                # Random source type
                source_type = np.random.choice(list(EnergySourceType))
                
                # Calculate properties based on source type
                properties = self._calculate_source_properties(source_type, r)
                
                source = EnergySource(
                    id=str(uuid.uuid4()),
                    name=f"{source_type.value.title()}_{i}",
                    source_type=source_type,
                    energy_form=properties["energy_form"],
                    location=(x, y, z),
                    distance=r,
                    power_output=properties["power_output"],
                    energy_density=properties["energy_density"],
                    accessibility=properties["accessibility"],
                    stability=properties["stability"],
                    harvesting_methods=properties["harvesting_methods"],
                    discovered_at=datetime.now(),
                    last_measured=datetime.now()
                )
                
                discovered_sources.append(source)
                self.known_sources[source.id] = source
            
            logger.info(f"Discovered {len(discovered_sources)} energy sources")
            return discovered_sources
            
        except Exception as e:
            logger.error(f"Error scanning for energy sources: {e}")
            return []
    
    def _calculate_source_properties(self, source_type: EnergySourceType, 
                                   distance: float) -> Dict[str, Any]:
        """Calculate properties for energy source"""
        try:
            properties = {
                "energy_form": EnergyForm.ELECTROMAGNETIC,
                "power_output": 1e26,  # Watts
                "energy_density": 1e-10,  # J/m³
                "accessibility": 0.5,
                "stability": 0.8,
                "harvesting_methods": [HarvestingMethod.PHOTOVOLTAIC]
            }
            
            if source_type == EnergySourceType.SOLAR:
                properties.update({
                    "energy_form": EnergyForm.ELECTROMAGNETIC,
                    "power_output": 3.828e26,  # Solar luminosity
                    "energy_density": 1e-6,
                    "accessibility": 0.9 / (1 + distance / 100),  # Decreases with distance
                    "stability": 0.95,
                    "harvesting_methods": [HarvestingMethod.PHOTOVOLTAIC, HarvestingMethod.THERMODYNAMIC]
                })
            elif source_type == EnergySourceType.QUASAR:
                properties.update({
                    "energy_form": EnergyForm.ELECTROMAGNETIC,
                    "power_output": 1e40,  # Extremely powerful
                    "energy_density": 1e-5,
                    "accessibility": 0.1 / (1 + distance / 1000),  # Very hard to access
                    "stability": 0.7,
                    "harvesting_methods": [HarvestingMethod.ELECTROMAGNETIC, HarvestingMethod.PLASMA_CONVERSION]
                })
            elif source_type == EnergySourceType.PULSAR:
                properties.update({
                    "energy_form": EnergyForm.ELECTROMAGNETIC,
                    "power_output": 1e31,  # Pulsar power
                    "energy_density": 1e-8,
                    "accessibility": 0.3 / (1 + distance / 500),
                    "stability": 0.9,
                    "harvesting_methods": [HarvestingMethod.ELECTROMAGNETIC, HarvestingMethod.TESLA_COIL]
                })
            elif source_type == EnergySourceType.BLACK_HOLE:
                properties.update({
                    "energy_form": EnergyForm.GRAVITATIONAL,
                    "power_output": 1e35,  # Hawking radiation
                    "energy_density": 1e-15,
                    "accessibility": 0.05 / (1 + distance / 2000),  # Extremely hard
                    "stability": 0.99,
                    "harvesting_methods": [HarvestingMethod.GRAVITATIONAL_WAVE, HarvestingMethod.QUANTUM_TUNNELING]
                })
            elif source_type == EnergySourceType.DARK_ENERGY:
                properties.update({
                    "energy_form": EnergyForm.FIELD,
                    "power_output": 1e37,  # Dark energy power
                    "energy_density": 1e-9,
                    "accessibility": 0.01,  # Very hard to detect
                    "stability": 1.0,
                    "harvesting_methods": [HarvestingMethod.ZERO_POINT_EXTRACTION, HarvestingMethod.CASIMIR_EFFECT]
                })
            elif source_type == EnergySourceType.ZERO_POINT:
                properties.update({
                    "energy_form": EnergyForm.QUANTUM,
                    "power_output": 1e25,  # Zero point energy
                    "energy_density": 1e-12,
                    "accessibility": 0.2,
                    "stability": 1.0,
                    "harvesting_methods": [HarvestingMethod.ZERO_POINT_EXTRACTION, HarvestingMethod.QUANTUM_TUNNELING]
                })
            elif source_type == EnergySourceType.COSMIC_BACKGROUND:
                properties.update({
                    "energy_form": EnergyForm.RADIATION,
                    "power_output": 1e23,  # Cosmic background radiation
                    "energy_density": 1e-14,
                    "accessibility": 0.8,
                    "stability": 0.95,
                    "harvesting_methods": [HarvestingMethod.THERMODYNAMIC, HarvestingMethod.STIRLING_ENGINE]
                })
            
            return properties
            
        except Exception as e:
            logger.error(f"Error calculating source properties: {e}")
            return properties
    
    def analyze_energy_spectrum(self, source_id: str) -> Dict[str, Any]:
        """Analyze energy spectrum of source"""
        try:
            source = self.known_sources.get(source_id)
            if not source:
                return {"error": "Source not found"}
            
            # Generate synthetic spectrum data
            frequencies = np.logspace(6, 20, 100)  # 1MHz to 100THz
            spectrum = np.zeros_like(frequencies)
            
            # Add peaks based on source type
            if source.source_type == EnergySourceType.SOLAR:
                # Solar spectrum peaks
                spectrum += 1e20 * np.exp(-(frequencies - 1e14)**2 / (1e28))  # Visible light
                spectrum += 5e19 * np.exp(-(frequencies - 1e13)**2 / (1e26))  # Infrared
                spectrum += 1e19 * np.exp(-(frequencies - 1e15)**2 / (1e30))  # UV
            elif source.source_type == EnergySourceType.QUASAR:
                # Quasar spectrum - broad spectrum
                spectrum += 1e30 * np.exp(-(np.log10(frequencies) - 14)**2 / 4)
            elif source.source_type == EnergySourceType.PULSAR:
                # Pulsar spectrum - periodic pulses
                spectrum += 1e28 * np.exp(-(frequencies - 1e8)**2 / (1e16))
                spectrum += 1e27 * np.exp(-(frequencies - 1e9)**2 / (1e18))
            
            # Add noise
            spectrum += np.random.exponential(1e15, len(frequencies))
            
            return {
                "source_id": source_id,
                "frequencies": frequencies.tolist(),
                "spectrum": spectrum.tolist(),
                "peak_frequency": frequencies[np.argmax(spectrum)],
                "total_power": np.sum(spectrum),
                "analyzed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing energy spectrum: {e}")
            return {"error": str(e)}

class EnergyHarvester:
    """Energy harvesting device"""
    
    def __init__(self, harvester_config: Dict[str, Any]):
        self.id = harvester_config["id"]
        self.name = harvester_config["name"]
        self.harvesting_method = HarvestingMethod(harvester_config["harvesting_method"])
        self.efficiency = harvester_config.get("efficiency", 0.5)
        self.capacity = harvester_config.get("capacity", 1e9)  # 1 GW default
        self.energy_sources = harvester_config.get("energy_sources", [])
        self.operational_status = "idle"
        self.energy_collected = 0.0
        self.operating_time = 0.0
        self.maintenance_required = False
        self.created_at = datetime.now()
        self.last_maintenance = datetime.now()
        
    def harvest_energy(self, source: EnergySource, duration: float) -> float:
        """Harvest energy from source"""
        try:
            if self.harvesting_method not in source.harvesting_methods:
                return 0.0
            
            # Calculate harvestable energy
            available_power = source.power_output * source.accessibility
            
            # Distance attenuation
            if source.distance > 0:
                attenuation = 1.0 / (4 * np.pi * source.distance**2)
                available_power *= attenuation
            
            # Apply efficiency and capacity limits
            harvestable_power = min(available_power * self.efficiency, self.capacity)
            
            # Calculate energy collected
            energy_collected = harvestable_power * duration
            
            # Update harvester
            self.energy_collected += energy_collected
            self.operating_time += duration
            
            # Maintenance check
            if self.operating_time > 86400 * 30:  # 30 days
                self.maintenance_required = True
            
            return energy_collected
            
        except Exception as e:
            logger.error(f"Error harvesting energy: {e}")
            return 0.0
    
    def get_status(self) -> Dict[str, Any]:
        """Get harvester status"""
        try:
            return {
                "id": self.id,
                "name": self.name,
                "harvesting_method": self.harvesting_method.value,
                "efficiency": self.efficiency,
                "capacity": self.capacity,
                "energy_collected": self.energy_collected,
                "operating_time": self.operating_time,
                "operational_status": self.operational_status,
                "maintenance_required": self.maintenance_required,
                "created_at": self.created_at.isoformat(),
                "last_maintenance": self.last_maintenance.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting harvester status: {e}")
            return {}

class EnergyStorageSystem:
    """Energy storage and management"""
    
    def __init__(self):
        self.storage_units: Dict[str, EnergyStorage] = {}
        self.total_capacity = 0.0
        self.total_charge = 0.0
        
    def create_storage_unit(self, name: str, storage_type: str,
                           capacity: float) -> EnergyStorage:
        """Create energy storage unit"""
        try:
            storage = EnergyStorage(
                id=str(uuid.uuid4()),
                name=name,
                storage_type=storage_type,
                capacity=capacity,
                current_charge=0.0,
                charge_rate=0.0,
                discharge_rate=0.0,
                efficiency=0.95,
                temperature=293.15,  # Room temperature
                is_active=True,
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
            
            self.storage_units[storage.id] = storage
            self.total_capacity += capacity
            
            logger.info(f"Created storage unit: {storage.id}")
            return storage
            
        except Exception as e:
            logger.error(f"Error creating storage unit: {e}")
            raise
    
    def store_energy(self, storage_id: str, energy: float) -> bool:
        """Store energy in storage unit"""
        try:
            storage = self.storage_units.get(storage_id)
            if not storage:
                return False
            
            # Check capacity
            available_space = storage.capacity - storage.current_charge
            energy_to_store = min(energy, available_space)
            
            # Apply efficiency
            stored_energy = energy_to_store * storage.efficiency
            
            # Update storage
            storage.current_charge += stored_energy
            storage.charge_rate = energy_to_store / 1.0  # Assuming 1 second
            storage.last_updated = datetime.now()
            
            # Update totals
            self.total_charge += stored_energy
            
            # Temperature increase
            storage.temperature += energy_to_store * 1e-6  # Simplified thermal model
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing energy: {e}")
            return False
    
    def discharge_energy(self, storage_id: str, energy: float) -> float:
        """Discharge energy from storage unit"""
        try:
            storage = self.storage_units.get(storage_id)
            if not storage:
                return 0.0
            
            # Check available charge
            available_energy = storage.current_charge
            energy_to_discharge = min(energy, available_energy)
            
            # Apply efficiency
            discharged_energy = energy_to_discharge * storage.efficiency
            
            # Update storage
            storage.current_charge -= energy_to_discharge
            storage.discharge_rate = energy_to_discharge / 1.0  # Assuming 1 second
            storage.last_updated = datetime.now()
            
            # Update totals
            self.total_charge -= energy_to_discharge
            
            # Temperature decrease
            storage.temperature -= energy_to_discharge * 1e-6
            
            return discharged_energy
            
        except Exception as e:
            logger.error(f"Error discharging energy: {e}")
            return 0.0
    
    def get_storage_status(self) -> Dict[str, Any]:
        """Get storage system status"""
        try:
            return {
                "total_units": len(self.storage_units),
                "total_capacity": self.total_capacity,
                "total_charge": self.total_charge,
                "charge_percentage": (self.total_charge / self.total_capacity * 100) if self.total_capacity > 0 else 0.0,
                "active_units": len([s for s in self.storage_units.values() if s.is_active]),
                "average_temperature": np.mean([s.temperature for s in self.storage_units.values()]) if self.storage_units else 293.15
            }
            
        except Exception as e:
            logger.error(f"Error getting storage status: {e}")
            return {}

class CosmicEnergySystem:
    """Main cosmic energy harvesting system"""
    
    def __init__(self):
        self.detector = CosmicEnergyDetector()
        self.harvesters: Dict[str, EnergyHarvester] = {}
        self.storage_system = EnergyStorageSystem()
        self.transactions: List[EnergyTransaction] = []
        self.total_energy_harvested = 0.0
        self.harvesting_rate = 0.0  # Watts
        
        # Initialize with some default harvesters
        self._initialize_default_harvesters()
        
        # Initialize storage
        self._initialize_storage()
        
        # Start background processes
        asyncio.create_task(self._continuous_harvesting())
        asyncio.create_task(self._energy_source_monitoring())
        asyncio.create_task(self._storage_management())
        asyncio.create_task(self._system_optimization())
    
    def _initialize_default_harvesters(self):
        """Initialize default energy harvesters"""
        try:
            harvester_configs = [
                {
                    "id": "solar_harvester_1",
                    "name": "Solar Array Alpha",
                    "harvesting_method": "photovoltaic",
                    "efficiency": 0.85,
                    "capacity": 1e8,  # 100 MW
                    "energy_sources": []
                },
                {
                    "id": "quantum_harvester_1",
                    "name": "Quantum Collector Beta",
                    "harvesting_method": "quantum_tunneling",
                    "efficiency": 0.3,
                    "capacity": 1e7,  # 10 MW
                    "energy_sources": []
                },
                {
                    "id": "zero_point_harvester_1",
                    "name": "Zero Point Extractor Gamma",
                    "harvesting_method": "zero_point_extraction",
                    "efficiency": 0.15,
                    "capacity": 5e6,  # 5 MW
                    "energy_sources": []
                }
            ]
            
            for config in harvester_configs:
                harvester = EnergyHarvester(config)
                self.harvesters[harvester.id] = harvester
            
            logger.info(f"Initialized {len(self.harvesters)} default harvesters")
            
        except Exception as e:
            logger.error(f"Error initializing default harvesters: {e}")
    
    def _initialize_storage(self):
        """Initialize energy storage"""
        try:
            # Create main storage battery
            main_storage = self.storage_system.create_storage_unit(
                "Main Energy Battery",
                "Lithium-Ion",
                1e12  # 1 TWh
            )
            
            # Create backup storage
            backup_storage = self.storage_system.create_storage_unit(
                "Backup Energy Storage",
                "Supercapacitor",
                1e11  # 100 GWh
            )
            
            logger.info("Initialized energy storage system")
            
        except Exception as e:
            logger.error(f"Error initializing storage: {e}")
    
    async def scan_for_energy_sources(self, center: Tuple[float, float, float] = (0, 0, 0),
                                      radius: float = 500.0) -> List[EnergySource]:
        """Scan for cosmic energy sources"""
        try:
            sources = self.detector.scan_for_energy_sources(center, radius)
            
            # Update harvesters with new sources
            for harvester in self.harvesters.values():
                for source in sources:
                    if harvester.harvesting_method in source.harvesting_methods:
                        if source.id not in harvester.energy_sources:
                            harvester.energy_sources.append(source.id)
            
            return sources
            
        except Exception as e:
            logger.error(f"Error scanning for energy sources: {e}")
            return []
    
    async def harvest_from_source(self, harvester_id: str, source_id: str,
                                 duration: float = 3600.0) -> float:
        """Harvest energy from specific source"""
        try:
            harvester = self.harvesters.get(harvester_id)
            source = self.detector.known_sources.get(source_id)
            
            if not harvester or not source:
                return 0.0
            
            # Harvest energy
            energy_collected = harvester.harvest_energy(source, duration)
            
            # Store energy
            if energy_collected > 0:
                # Find suitable storage
                storage_id = self._find_best_storage()
                if storage_id:
                    self.storage_system.store_energy(storage_id, energy_collected)
                
                    # Create transaction record
                    transaction = EnergyTransaction(
                        id=str(uuid.uuid4()),
                        source_id=source_id,
                        harvester_id=harvester_id,
                        storage_id=storage_id,
                        energy_amount=energy_collected,
                        harvesting_method=harvester.harvesting_method,
                        efficiency=harvester.efficiency,
                        timestamp=datetime.now(),
                        duration=duration,
                        cost=energy_collected * 1e-6  # 1 credit per MJ
                    )
                    
                    self.transactions.append(transaction)
                    self.total_energy_harvested += energy_collected
            
            return energy_collected
            
        except Exception as e:
            logger.error(f"Error harvesting from source: {e}")
            return 0.0
    
    def _find_best_storage(self) -> Optional[str]:
        """Find best storage unit for energy"""
        try:
            best_storage = None
        best_space = 0.0
        
        for storage_id, storage in self.storage_system.storage_units.items():
            if storage.is_active:
                available_space = storage.capacity - storage.current_charge
                if available_space > best_space:
                    best_space = available_space
                    best_storage = storage_id
        
        return best_storage
        
        except Exception as e:
            logger.error(f"Error finding best storage: {e}")
            return None
    
    async def _continuous_harvesting(self):
        """Background continuous energy harvesting"""
        while True:
            try:
                # Harvest from all active harvesters
                for harvester_id, harvester in self.harvesters.items():
                    if not harvester.maintenance_required:
                        # Find best source for this harvester
                        best_source = None
                        max_power = 0.0
                        
                        for source_id in harvester.energy_sources:
                            source = self.detector.known_sources.get(source_id)
                            if source:
                                power = source.power_output * source.accessibility
                                if power > max_power:
                                    max_power = power
                                    best_source = source
                        
                        if best_source:
                            # Harvest for a short duration
                            energy = await self.harvest_from_source(
                                harvester_id, best_source.id, 60.0  # 1 minute
                            )
                            
                            # Update harvesting rate
                            self.harvesting_rate = energy / 60.0
                
                # Wait before next harvest cycle
                await asyncio.sleep(300)  # Harvest every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in continuous harvesting: {e}")
                await asyncio.sleep(60)
    
    async def _energy_source_monitoring(self):
        """Background energy source monitoring"""
        while True:
            try:
                # Update source measurements
                for source in self.detector.known_sources.values():
                    # Simulate measurement updates
                    source.last_measured = datetime.now()
                    
                    # Small random variations in power output
                    variation = np.random.normal(1.0, 0.01)
                    source.power_output *= variation
                    
                    # Update stability
                    if source.stability > 0.5:
                        source.stability *= 0.9999  # Gradual degradation
                    else:
                        source.stability *= 1.0001  # Recovery
                
                    source.stability = max(0.1, min(1.0, source.stability))
                
                # Wait before next monitoring
                await asyncio.sleep(3600)  # Monitor every hour
                
            except Exception as e:
                logger.error(f"Error in source monitoring: {e}")
                await asyncio.sleep(300)
    
    async def _storage_management(self):
        """Background storage management"""
        while True:
            try:
                # Check storage temperatures
                for storage in self.storage_system.storage_units.values():
                    # Temperature regulation
                    if storage.temperature > 350.0:  # Too hot
                        storage.temperature -= 5.0  # Cooling
                    elif storage.temperature < 250.0:  # Too cold
                        storage.temperature += 2.0  # Heating
                    
                    # Efficiency based on temperature
                    optimal_temp = 293.15  # Room temperature
                    temp_diff = abs(storage.temperature - optimal_temp)
                    storage.efficiency = max(0.8, 0.95 - temp_diff * 0.0001)
                
                # Wait for next management cycle
                await asyncio.sleep(600)  # Manage every 10 minutes
                
            except Exception as e:
                logger.error(f"Error in storage management: {e}")
                await asyncio.sleep(60)
    
    async def _system_optimization(self):
        """Background system optimization"""
        while True:
            try:
                # Optimize harvester assignments
                for harvester in self.harvesters.values():
                    # Re-evaluate source assignments
                    if len(harvester.energy_sources) > 10:
                        # Keep only top 10 sources
                        sources_with_power = []
                        for source_id in harvester.energy_sources:
                            source = self.detector.known_sources.get(source_id)
                            if source:
                                power = source.power_output * source.accessibility
                                sources_with_power.append((source_id, power))
                        
                        # Sort by power and keep top 10
                        sources_with_power.sort(key=lambda x: x[1], reverse=True)
                        harvester.energy_sources = [s[0] for s in sources_with_power[:10]]
                
                # Perform maintenance if needed
                for harvester in self.harvesters.values():
                    if harvester.maintenance_required:
                        # Simulate maintenance
                        harvester.maintenance_required = False
                        harvester.efficiency = min(1.0, harvester.efficiency + 0.01)
                        harvester.last_maintenance = datetime.now()
                        logger.info(f"Performed maintenance on harvester: {harvester.id}")
                
                # Wait for next optimization
                await asyncio.sleep(3600)  # Optimize every hour
                
            except Exception as e:
                logger.error(f"Error in system optimization: {e}")
                await asyncio.sleep(300)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get cosmic energy system status"""
        try:
            return {
                "total_energy_sources": len(self.detector.known_sources),
                "active_harvesters": len(self.harvesters),
                "total_energy_harvested": self.total_energy_harvested,
                "harvesting_rate": self.harvesting_rate,
                "storage_status": self.storage_system.get_storage_status(),
                "total_transactions": len(self.transactions),
                "supported_source_types": len(EnergySourceType),
                "supported_harvesting_methods": len(HarvestingMethod)
            }
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {}

# Global cosmic energy system
cosmic_energy_system = CosmicEnergySystem()

# API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/cosmic_energy", tags=["cosmic_energy"])

class ScanRequest(BaseModel):
    center: List[float]
    radius: float

class HarvestRequest(BaseModel):
    harvester_id: str
    source_id: str
    duration: float = 3600.0

class StorageRequest(BaseModel):
    name: str
    storage_type: str
    capacity: float

@router.post("/scan")
async def scan_for_energy_sources(request: ScanRequest):
    """Scan for cosmic energy sources"""
    try:
        center = tuple(request.center)
        sources = await cosmic_energy_system.scan_for_energy_sources(center, request.radius)
        
        return {
            "center": center,
            "radius": request.radius,
            "sources_found": len(sources),
            "sources": [
                {
                    "id": s.id,
                    "name": s.name,
                    "type": s.source_type.value,
                    "form": s.energy_form.value,
                    "distance": s.distance,
                    "power_output": s.power_output,
                    "accessibility": s.accessibility
                }
                for s in sources
            ]
        }
    except Exception as e:
        logger.error(f"Error scanning for energy sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/harvest")
async def harvest_energy(request: HarvestRequest):
    """Harvest energy from source"""
    try:
        energy = await cosmic_energy_system.harvest_from_source(
            request.harvester_id, request.source_id, request.duration
        )
        
        return {
            "harvester_id": request.harvester_id,
            "source_id": request.source_id,
            "duration": request.duration,
            "energy_harvested": energy,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error harvesting energy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/storage/create")
async def create_storage_unit(request: StorageRequest):
    """Create energy storage unit"""
    try:
        storage = cosmic_energy_system.storage_system.create_storage_unit(
            request.name, request.storage_type, request.capacity
        )
        
        return asdict(storage)
    except Exception as e:
        logger.error(f"Error creating storage unit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sources/{source_id}/spectrum")
async def analyze_energy_spectrum(source_id: str):
    """Analyze energy spectrum of source"""
    try:
        spectrum = cosmic_energy_system.detector.analyze_energy_spectrum(source_id)
        return spectrum
    except Exception as e:
        logger.error(f"Error analyzing energy spectrum: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/harvesters/{harvester_id}")
async def get_harvester_status(harvester_id: str):
    """Get harvester status"""
    try:
        harvester = cosmic_energy_system.harvesters.get(harvester_id)
        if not harvester:
            raise HTTPException(status_code=404, detail="Harvester not found")
        
        return harvester.get_status()
    except Exception as e:
        logger.error(f"Error getting harvester status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/harvesters")
async def list_harvesters():
    """List all harvesters"""
    try:
        harvesters = []
        for harvester in cosmic_energy_system.harvesters.values():
            harvesters.append({
                "id": harvester.id,
                "name": harvester.name,
                "method": harvester.harvesting_method.value,
                "efficiency": harvester.efficiency,
                "capacity": harvester.capacity,
                "energy_collected": harvester.energy_collected,
                "maintenance_required": harvester.maintenance_required
            })
        
        return {"harvesters": harvesters}
    except Exception as e:
        logger.error(f"Error listing harvesters: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/storage/status")
async def get_storage_status():
    """Get storage system status"""
    try:
        status = cosmic_energy_system.storage_system.get_storage_status()
        return status
    except Exception as e:
        logger.error(f"Error getting storage status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sources")
async def list_energy_sources():
    """List all known energy sources"""
    try:
        sources = []
        for source in cosmic_energy_system.detector.known_sources.values():
            sources.append({
                "id": source.id,
                "name": source.name,
                "type": source.source_type.value,
                "form": source.energy_form.value,
                "distance": source.distance,
                "power_output": source.power_output,
                "accessibility": source.accessibility,
                "stability": source.stability
            })
        
        return {"energy_sources": sources}
    except Exception as e:
        logger.error(f"Error listing energy sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/source-types")
async def list_source_types():
    """List supported energy source types"""
    try:
        types = [stype.value for stype in EnergySourceType]
        return {"source_types": types}
    except Exception as e:
        logger.error(f"Error listing source types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/harvesting-methods")
async def list_harvesting_methods():
    """List supported harvesting methods"""
    try:
        methods = [method.value for method in HarvestingMethod]
        return {"harvesting_methods": methods}
    except Exception as e:
        logger.error(f"Error listing harvesting methods: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_system_status():
    """Get cosmic energy system status"""
    try:
        status = cosmic_energy_system.get_system_status()
        return status
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
