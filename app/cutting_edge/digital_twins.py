"""
Digital Twins and Real-time Simulation for Asmblr
Virtual replicas of physical systems with real-time synchronization
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import numpy as np
from scipy.integrate import odeint
from scipy.optimize import minimize
from collections import defaultdict

logger = logging.getLogger(__name__)

class TwinType(Enum):
    """Digital twin types"""
    PHYSICAL_ASSET = "physical_asset"
    PROCESS = "process"
    SYSTEM = "system"
    ORGANIZATION = "organization"
    CITY = "city"
    BUILDING = "building"
    VEHICLE = "vehicle"
    HUMAN = "human"
    ENVIRONMENT = "environment"

class SimulationType(Enum):
    """Simulation types"""
    PHYSICS_BASED = "physics_based"
    DATA_DRIVEN = "data_driven"
    HYBRID = "hybrid"
    STOCHASTIC = "stochastic"
    DETERMINISTIC = "deterministic"
    REAL_TIME = "real_time"
    PREDICTIVE = "predictive"
    WHAT_IF = "what_if"

class SensorType(Enum):
    """Sensor types"""
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    HUMIDITY = "humidity"
    VIBRATION = "vibration"
    POSITION = "position"
    VELOCITY = "velocity"
    ACCELERATION = "acceleration"
    FLOW_RATE = "flow_rate"
    POWER = "power"
    VOLTAGE = "voltage"
    CURRENT = "current"
    CHEMICAL = "chemical"
    BIOLOGICAL = "biological"

@dataclass
class SensorReading:
    """Sensor reading data"""
    sensor_id: str
    sensor_type: SensorType
    value: float
    unit: str
    timestamp: datetime
    location: tuple[float, float, float]
    quality_score: float
    metadata: dict[str, Any]

@dataclass
class DigitalTwin:
    """Digital twin definition"""
    id: str
    name: str
    twin_type: TwinType
    description: str
    physical_object_id: str
    geometry: dict[str, Any]
    properties: dict[str, Any]
    behaviors: dict[str, Any]
    sensors: list[str]
    simulation_models: list[str]
    created_at: datetime
    updated_at: datetime
    is_active: bool
    sync_frequency: float  # Hz

@dataclass
class SimulationModel:
    """Simulation model definition"""
    id: str
    name: str
    twin_id: str
    model_type: SimulationType
    equations: list[str]
    parameters: dict[str, Any]
    initial_conditions: dict[str, Any]
    boundary_conditions: dict[str, Any]
    validation_metrics: dict[str, float]
    created_at: datetime
    updated_at: datetime

@dataclass
class SimulationState:
    """Simulation state"""
    twin_id: str
    timestamp: datetime
    state_variables: dict[str, float]
    sensor_readings: list[SensorReading]
    predictions: dict[str, Any]
    anomalies: list[dict[str, Any]]
    performance_metrics: dict[str, float]

class DigitalTwinManager:
    """Digital twin management system"""
    
    def __init__(self):
        self.twins: dict[str, DigitalTwin] = {}
        self.simulation_models: dict[str, SimulationModel] = {}
        self.simulation_states: dict[str, list[SimulationState]] = {}
        self.sensor_data: dict[str, list[SensorReading]] = {}
        self.anomaly_detectors: dict[str, Any] = {}
        
        # Initialize simulation engines
        self.physics_engine = PhysicsEngine()
        self.data_driven_engine = DataDrivenEngine()
        self.hybrid_engine = HybridEngine()
        
        # Initialize synchronization
        self.sync_manager = SynchronizationManager()
        
        # Start background tasks
        asyncio.create_task(self._continuous_simulation())
        asyncio.create_task(self._data_ingestion())
        asyncio.create_task(self._anomaly_detection())
    
    async def create_digital_twin(self, twin_config: dict[str, Any]) -> DigitalTwin:
        """Create digital twin"""
        try:
            twin_id = str(uuid.uuid4())
            
            twin = DigitalTwin(
                id=twin_id,
                name=twin_config["name"],
                twin_type=TwinType(twin_config["twin_type"]),
                description=twin_config.get("description", ""),
                physical_object_id=twin_config["physical_object_id"],
                geometry=twin_config.get("geometry", {}),
                properties=twin_config.get("properties", {}),
                behaviors=twin_config.get("behaviors", {}),
                sensors=twin_config.get("sensors", []),
                simulation_models=twin_config.get("simulation_models", []),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_active=True,
                sync_frequency=twin_config.get("sync_frequency", 1.0)
            )
            
            self.twins[twin_id] = twin
            self.simulation_states[twin_id] = []
            
            logger.info(f"Created digital twin: {twin_id}")
            return twin
            
        except Exception as e:
            logger.error(f"Error creating digital twin: {e}")
            raise
    
    async def create_simulation_model(self, model_config: dict[str, Any]) -> SimulationModel:
        """Create simulation model"""
        try:
            model_id = str(uuid.uuid4())
            
            model = SimulationModel(
                id=model_id,
                name=model_config["name"],
                twin_id=model_config["twin_id"],
                model_type=SimulationType(model_config["model_type"]),
                equations=model_config.get("equations", []),
                parameters=model_config.get("parameters", {}),
                initial_conditions=model_config.get("initial_conditions", {}),
                boundary_conditions=model_config.get("boundary_conditions", {}),
                validation_metrics=model_config.get("validation_metrics", {}),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.simulation_models[model_id] = model
            
            logger.info(f"Created simulation model: {model_id}")
            return model
            
        except Exception as e:
            logger.error(f"Error creating simulation model: {e}")
            raise
    
    async def ingest_sensor_data(self, twin_id: str, sensor_readings: list[SensorReading]):
        """Ingest sensor data for digital twin"""
        try:
            if twin_id not in self.sensor_data:
                self.sensor_data[twin_id] = []
            
            # Add new readings
            self.sensor_data[twin_id].extend(sensor_readings)
            
            # Keep only last 1000 readings per sensor
            if len(self.sensor_data[twin_id]) > 1000:
                self.sensor_data[twin_id] = self.sensor_data[twin_id][-1000:]
            
            # Update twin state
            twin = self.twins.get(twin_id)
            if twin:
                twin.updated_at = datetime.now()
            
            logger.info(f"Ingested {len(sensor_readings)} sensor readings for twin {twin_id}")
            
        except Exception as e:
            logger.error(f"Error ingesting sensor data: {e}")
            raise
    
    async def run_simulation(self, twin_id: str, model_id: str, 
                           duration: float, time_step: float = 0.1) -> SimulationState:
        """Run simulation for digital twin"""
        try:
            twin = self.twins.get(twin_id)
            model = self.simulation_models.get(model_id)
            
            if not twin or not model:
                raise ValueError(f"Twin {twin_id} or model {model_id} not found")
            
            # Get simulation engine
            if model.model_type == SimulationType.PHYSICS_BASED:
                engine = self.physics_engine
            elif model.model_type == SimulationType.DATA_DRIVEN:
                engine = self.data_driven_engine
            elif model.model_type == SimulationType.HYBRID:
                engine = self.hybrid_engine
            else:
                engine = self.physics_engine  # Default
            
            # Run simulation
            simulation_result = await engine.simulate(
                twin, model, duration, time_step
            )
            
            # Create simulation state
            state = SimulationState(
                twin_id=twin_id,
                timestamp=datetime.now(),
                state_variables=simulation_result["state_variables"],
                sensor_readings=simulation_result.get("sensor_readings", []),
                predictions=simulation_result.get("predictions", {}),
                anomalies=simulation_result.get("anomalies", []),
                performance_metrics=simulation_result.get("performance_metrics", {})
            )
            
            # Store state
            if twin_id not in self.simulation_states:
                self.simulation_states[twin_id] = []
            
            self.simulation_states[twin_id].append(state)
            
            # Keep only last 100 states
            if len(self.simulation_states[twin_id]) > 100:
                self.simulation_states[twin_id] = self.simulation_states[twin_id][-100:]
            
            logger.info(f"Completed simulation for twin {twin_id}")
            return state
            
        except Exception as e:
            logger.error(f"Error running simulation: {e}")
            raise
    
    async def predict_future_state(self, twin_id: str, horizon: float, 
                                 confidence_level: float = 0.95) -> dict[str, Any]:
        """Predict future state of digital twin"""
        try:
            twin = self.twins.get(twin_id)
            if not twin:
                raise ValueError(f"Twin {twin_id} not found")
            
            # Get historical states
            states = self.simulation_states.get(twin_id, [])
            if len(states) < 10:
                raise ValueError("Insufficient historical data for prediction")
            
            # Use data-driven engine for prediction
            predictions = await self.data_driven_engine.predict_future_state(
                twin, states, horizon, confidence_level
            )
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error predicting future state: {e}")
            raise
    
    async def detect_anomalies(self, twin_id: str, threshold: float = 0.95) -> list[dict[str, Any]]:
        """Detect anomalies in digital twin"""
        try:
            twin = self.twins.get(twin_id)
            if not twin:
                raise ValueError(f"Twin {twin_id} not found")
            
            # Get recent sensor data
            sensor_data = self.sensor_data.get(twin_id, [])
            if len(sensor_data) < 50:
                return []
            
            # Detect anomalies
            anomalies = []
            
            # Group by sensor type
            sensor_groups = defaultdict(list)
            for reading in sensor_data:
                sensor_groups[reading.sensor_type].append(reading)
            
            # Check each sensor group
            for sensor_type, readings in sensor_groups.items():
                if len(readings) < 10:
                    continue
                
                # Extract values
                values = [r.value for r in readings]
                timestamps = [r.timestamp for r in readings]
                
                # Statistical anomaly detection
                mean_val = np.mean(values)
                std_val = np.std(values)
                
                # Find outliers
                for i, reading in enumerate(readings):
                    z_score = abs(reading.value - mean_val) / (std_val + 1e-8)
                    
                    if z_score > 2.5:  # Outlier threshold
                        anomaly = {
                            "sensor_id": reading.sensor_id,
                            "sensor_type": sensor_type.value,
                            "timestamp": reading.timestamp.isoformat(),
                            "value": reading.value,
                            "expected_range": [mean_val - 2*std_val, mean_val + 2*std_val],
                            "z_score": z_score,
                            "severity": "high" if z_score > 3 else "medium",
                            "description": f"Anomalous {sensor_type.value} reading detected"
                        }
                        anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []
    
    async def optimize_parameters(self, twin_id: str, model_id: str, 
                                objective_function: str, 
                                constraints: dict[str, Any]) -> dict[str, Any]:
        """Optimize digital twin parameters"""
        try:
            twin = self.twins.get(twin_id)
            model = self.simulation_models.get(model_id)
            
            if not twin or not model:
                raise ValueError(f"Twin {twin_id} or model {model_id} not found")
            
            # Define optimization problem
            def objective(params):
                # Update model parameters
                updated_params = model.parameters.copy()
                for i, param_name in enumerate(model.parameters):
                    updated_params[param_name] = params[i]
                
                # Run simulation with updated parameters
                try:
                    result = await self.physics_engine.simulate(
                        twin, model, duration=10.0, time_step=0.1
                    )
                    
                    # Extract objective value
                    if objective_function == "minimize_energy":
                        return result["state_variables"].get("energy_consumption", 0)
                    elif objective_function == "maximize_efficiency":
                        return -result["state_variables"].get("efficiency", 0)
                    elif objective_function == "minimize_error":
                        return result["state_variables"].get("tracking_error", 0)
                    else:
                        return 0
                except:
                    return float('inf')
            
            # Initial parameters
            initial_params = list(model.parameters.values())
            
            # Constraints
            bounds = []
            for param_name, param_value in model.parameters.items():
                if param_name in constraints:
                    bounds.append(constraints[param_name])
                else:
                    # Default bounds
                    bounds.append((param_value * 0.5, param_value * 1.5))
            
            # Optimize
            result = minimize(
                objective,
                initial_params,
                method='L-BFGS-B',
                bounds=bounds,
                options={'maxiter': 100}
            )
            
            if result.success:
                # Update model with optimized parameters
                optimized_params = {}
                for i, param_name in enumerate(model.parameters):
                    optimized_params[param_name] = result.x[i]
                
                model.parameters = optimized_params
                model.updated_at = datetime.now()
                
                return {
                    "success": True,
                    "optimized_parameters": optimized_params,
                    "objective_value": result.fun,
                    "iterations": result.nit,
                    "message": result.message
                }
            else:
                return {
                    "success": False,
                    "message": result.message
                }
            
        except Exception as e:
            logger.error(f"Error optimizing parameters: {e}")
            return {"success": False, "error": str(e)}
    
    async def sync_with_physical(self, twin_id: str) -> dict[str, Any]:
        """Synchronize digital twin with physical object"""
        try:
            twin = self.twins.get(twin_id)
            if not twin:
                raise ValueError(f"Twin {twin_id} not found")
            
            # Get latest sensor data
            sensor_data = self.sensor_data.get(twin_id, [])
            if not sensor_data:
                return {"status": "no_data", "message": "No sensor data available"}
            
            # Calculate sync quality
            sync_quality = await self.sync_manager.calculate_sync_quality(
                twin, sensor_data
            )
            
            # Update twin state
            await self._update_twin_state(twin_id, sensor_data)
            
            return {
                "status": "synced",
                "sync_quality": sync_quality,
                "last_sync": datetime.now().isoformat(),
                "sensor_count": len(sensor_data),
                "data_freshness": (datetime.now() - sensor_data[-1].timestamp).total_seconds()
            }
            
        except Exception as e:
            logger.error(f"Error syncing with physical: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _update_twin_state(self, twin_id: str, sensor_data: list[SensorReading]):
        """Update twin state based on sensor data"""
        try:
            twin = self.twins.get(twin_id)
            if not twin:
                return
            
            # Aggregate sensor data
            aggregated_data = {}
            for reading in sensor_data:
                sensor_type = reading.sensor_type.value
                if sensor_type not in aggregated_data:
                    aggregated_data[sensor_type] = []
                aggregated_data[sensor_type].append(reading.value)
            
            # Calculate averages
            for sensor_type, values in aggregated_data.items():
                avg_value = np.mean(values)
                twin.properties[f"current_{sensor_type}"] = avg_value
            
            twin.updated_at = datetime.now()
            
        except Exception as e:
            logger.error(f"Error updating twin state: {e}")
    
    async def _continuous_simulation(self):
        """Background continuous simulation"""
        while True:
            try:
                for twin_id, twin in self.twins.items():
                    if twin.is_active:
                        # Run continuous simulation at specified frequency
                        if twin.sync_frequency > 0:
                            await asyncio.sleep(1.0 / twin.sync_frequency)
                            
                            # Get simulation models for twin
                            twin_models = [
                                model for model in self.simulation_models.values()
                                if model.twin_id == twin_id
                            ]
                            
                            if twin_models:
                                # Run simulation with first model
                                await self.run_simulation(
                                    twin_id, twin_models[0].id, 1.0
                                )
                
                # Wait before next cycle
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in continuous simulation: {e}")
                await asyncio.sleep(5)
    
    async def _data_ingestion(self):
        """Background data ingestion"""
        while True:
            try:
                # Simulate data ingestion from sensors
                for twin_id in self.twins.keys():
                    # Generate random sensor data
                    sensor_readings = self._generate_sensor_data(twin_id)
                    
                    if sensor_readings:
                        await self.ingest_sensor_data(twin_id, sensor_readings)
                
                # Wait before next ingestion
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in data ingestion: {e}")
                await asyncio.sleep(10)
    
    async def _anomaly_detection(self):
        """Background anomaly detection"""
        while True:
            try:
                for twin_id in self.twins.keys():
                    anomalies = await self.detect_anomalies(twin_id)
                    
                    if anomalies:
                        logger.warning(f"Detected {len(anomalies)} anomalies in twin {twin_id}")
                        
                        # Store anomalies in latest state
                        states = self.simulation_states.get(twin_id, [])
                        if states:
                            states[-1].anomalies = anomalies
                
                # Wait before next detection
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in anomaly detection: {e}")
                await asyncio.sleep(60)
    
    def _generate_sensor_data(self, twin_id: str) -> list[SensorReading]:
        """Generate simulated sensor data"""
        try:
            twin = self.twins.get(twin_id)
            if not twin:
                return []
            
            sensor_readings = []
            
            # Generate data for each sensor
            for sensor_id in twin.sensors:
                # Simulate different sensor types
                sensor_type = np.random.choice(list(SensorType))
                
                # Generate realistic values based on sensor type
                if sensor_type == SensorType.TEMPERATURE:
                    value = np.random.normal(25, 5)  # Room temperature
                    unit = "°C"
                elif sensor_type == SensorType.PRESSURE:
                    value = np.random.normal(101325, 1000)  # Atmospheric pressure
                    unit = "Pa"
                elif sensor_type == SensorType.HUMIDITY:
                    value = np.random.normal(50, 10)  # Humidity
                    unit = "%"
                elif sensor_type == SensorType.VIBRATION:
                    value = np.random.exponential(0.1)  # Vibration
                    unit = "mm/s"
                elif sensor_type == SensorType.POWER:
                    value = np.random.normal(1000, 100)  # Power consumption
                    unit = "W"
                else:
                    value = np.random.normal(0, 1)  # Generic sensor
                    unit = "unit"
                
                reading = SensorReading(
                    sensor_id=sensor_id,
                    sensor_type=sensor_type,
                    value=value,
                    unit=unit,
                    timestamp=datetime.now(),
                    location=(0, 0, 0),  # Default location
                    quality_score=np.random.uniform(0.8, 1.0),
                    metadata={}
                )
                
                sensor_readings.append(reading)
            
            return sensor_readings
            
        except Exception as e:
            logger.error(f"Error generating sensor data: {e}")
            return []
    
    def get_twin_visualization(self, twin_id: str) -> dict[str, Any]:
        """Get visualization data for digital twin"""
        try:
            twin = self.twins.get(twin_id)
            if not twin:
                raise ValueError(f"Twin {twin_id} not found")
            
            # Get latest state
            states = self.simulation_states.get(twin_id, [])
            latest_state = states[-1] if states else None
            
            # Get sensor data
            sensor_data = self.sensor_data.get(twin_id, [])
            
            # Create visualization data
            viz_data = {
                "twin_info": {
                    "id": twin.id,
                    "name": twin.name,
                    "type": twin.twin_type.value,
                    "description": twin.description
                },
                "geometry": twin.geometry,
                "current_state": asdict(latest_state) if latest_state else None,
                "sensor_data": [
                    {
                        "sensor_id": r.sensor_id,
                        "sensor_type": r.sensor_type.value,
                        "value": r.value,
                        "unit": r.unit,
                        "timestamp": r.timestamp.isoformat(),
                        "location": r.location,
                        "quality_score": r.quality_score
                    }
                    for r in sensor_data[-100:]  # Last 100 readings
                ],
                "performance_metrics": latest_state.performance_metrics if latest_state else {},
                "anomalies": latest_state.anomalies if latest_state else []
            }
            
            return viz_data
            
        except Exception as e:
            logger.error(f"Error getting twin visualization: {e}")
            return {}

class PhysicsEngine:
    """Physics-based simulation engine"""
    
    async def simulate(self, twin: DigitalTwin, model: SimulationModel, 
                      duration: float, time_step: float) -> dict[str, Any]:
        """Run physics-based simulation"""
        try:
            # Initialize state variables
            state = model.initial_conditions.copy()
            
            # Time array
            t = np.arange(0, duration, time_step)
            
            # Solve differential equations
            if model.equations:
                # Define ODE system
                def ode_system(y, t):
                    dydt = np.zeros_like(y)
                    
                    # Simple harmonic oscillator example
                    if len(y) >= 2:
                        dydt[0] = y[1]  # velocity
                        dydt[1] = -model.parameters.get("omega", 1.0)**2 * y[0]  # acceleration
                    
                    return dydt
                
                # Solve ODE
                y0 = np.array(list(state.values()))
                solution = odeint(ode_system, y0, t)
                
                # Extract results
                state_variables = {}
                for i, key in enumerate(state.keys()):
                    state_variables[key] = solution[:, i].tolist()
            else:
                # Simple physics simulation
                state_variables = self._simple_physics_simulation(twin, model, t)
            
            # Generate sensor readings
            sensor_readings = self._generate_sensor_readings(twin, state_variables, t)
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(state_variables)
            
            return {
                "state_variables": state_variables,
                "sensor_readings": sensor_readings,
                "performance_metrics": performance_metrics,
                "time_array": t.tolist()
            }
            
        except Exception as e:
            logger.error(f"Error in physics simulation: {e}")
            return {}
    
    def _simple_physics_simulation(self, twin: DigitalTwin, model: SimulationModel, 
                                t: np.ndarray) -> dict[str, Any]:
        """Simple physics simulation"""
        state_variables = {}
        
        # Position simulation
        if "position" in model.initial_conditions:
            initial_pos = model.initial_conditions["position"]
            velocity = model.parameters.get("velocity", 1.0)
            
            # Simple motion: x = x0 + v*t
            positions = initial_pos + velocity * t
            state_variables["position"] = positions.tolist()
        
        # Temperature simulation
        if "temperature" in model.initial_conditions:
            initial_temp = model.initial_conditions["temperature"]
            ambient_temp = model.parameters.get("ambient_temperature", 20.0)
            cooling_rate = model.parameters.get("cooling_rate", 0.1)
            
            # Newton's law of cooling
            temperatures = ambient_temp + (initial_temp - ambient_temp) * np.exp(-cooling_rate * t)
            state_variables["temperature"] = temperatures.tolist()
        
        return state_variables
    
    def _generate_sensor_readings(self, twin: DigitalTwin, state_variables: dict[str, Any], 
                                 t: np.ndarray) -> list[SensorReading]:
        """Generate sensor readings from simulation"""
        sensor_readings = []
        
        for i, timestamp in enumerate(t):
            sim_time = datetime.now() + timedelta(seconds=timestamp)
            
            # Generate readings based on state variables
            for state_var, values in state_variables.items():
                if i < len(values):
                    value = values[i]
                    
                    # Determine sensor type
                    sensor_type = self._map_state_to_sensor(state_var)
                    
                    reading = SensorReading(
                        sensor_id=f"sim_{state_var}_{i}",
                        sensor_type=sensor_type,
                        value=value,
                        unit=self._get_unit_for_sensor(sensor_type),
                        timestamp=sim_time,
                        location=(0, 0, 0),
                        quality_score=1.0,
                        metadata={"simulation": True}
                    )
                    
                    sensor_readings.append(reading)
        
        return sensor_readings
    
    def _map_state_to_sensor(self, state_var: str) -> SensorType:
        """Map state variable to sensor type"""
        mapping = {
            "position": SensorType.POSITION,
            "velocity": SensorType.VELOCITY,
            "acceleration": SensorType.ACCELERATION,
            "temperature": SensorType.TEMPERATURE,
            "pressure": SensorType.PRESSURE,
            "humidity": SensorType.HUMIDITY,
            "flow_rate": SensorType.FLOW_RATE,
            "power": SensorType.POWER,
            "voltage": SensorType.VOLTAGE,
            "current": SensorType.CURRENT
        }
        
        return mapping.get(state_var, SensorType.TEMPERATURE)
    
    def _get_unit_for_sensor(self, sensor_type: SensorType) -> str:
        """Get unit for sensor type"""
        units = {
            SensorType.TEMPERATURE: "°C",
            SensorType.PRESSURE: "Pa",
            SensorType.HUMIDITY: "%",
            SensorType.VIBRATION: "mm/s",
            SensorType.POSITION: "m",
            SensorType.VELOCITY: "m/s",
            SensorType.ACCELERATION: "m/s²",
            SensorType.FLOW_RATE: "L/min",
            SensorType.POWER: "W",
            SensorType.VOLTAGE: "V",
            SensorType.CURRENT: "A"
        }
        
        return units.get(sensor_type, "unit")
    
    def _calculate_performance_metrics(self, state_variables: dict[str, Any]) -> dict[str, float]:
        """Calculate performance metrics"""
        metrics = {}
        
        for var_name, values in state_variables.items():
            if values:
                values_array = np.array(values)
                
                metrics[f"{var_name}_mean"] = np.mean(values_array)
                metrics[f"{var_name}_std"] = np.std(values_array)
                metrics[f"{var_name}_min"] = np.min(values_array)
                metrics[f"{var_name}_max"] = np.max(values_array)
        
        return metrics

class DataDrivenEngine:
    """Data-driven simulation engine"""
    
    async def simulate(self, twin: DigitalTwin, model: SimulationModel, 
                      duration: float, time_step: float) -> dict[str, Any]:
        """Run data-driven simulation"""
        try:
            # Get historical data
            historical_data = self._get_historical_data(twin)
            
            if len(historical_data) < 10:
                return self._fallback_simulation(twin, model, duration, time_step)
            
            # Use time series forecasting
            predictions = self._time_series_forecast(historical_data, duration, time_step)
            
            # Generate sensor readings
            sensor_readings = self._generate_sensor_readings_from_predictions(
                twin, predictions, duration, time_step
            )
            
            # Calculate performance metrics
            performance_metrics = self._calculate_ml_metrics(predictions)
            
            return {
                "state_variables": predictions,
                "sensor_readings": sensor_readings,
                "performance_metrics": performance_metrics,
                "model_accuracy": self._calculate_model_accuracy(historical_data, predictions)
            }
            
        except Exception as e:
            logger.error(f"Error in data-driven simulation: {e}")
            return {}
    
    def _get_historical_data(self, twin: DigitalTwin) -> list[dict[str, Any]]:
        """Get historical data for twin"""
        # In real implementation, would query database
        # For now, return simulated historical data
        historical_data = []
        
        for i in range(100):
            timestamp = datetime.now() - timedelta(hours=i)
            
            data_point = {
                "timestamp": timestamp,
                "temperature": 20 + 5 * np.sin(i * 0.1) + np.random.normal(0, 1),
                "pressure": 101325 + 100 * np.sin(i * 0.05) + np.random.normal(0, 50),
                "humidity": 50 + 10 * np.cos(i * 0.08) + np.random.normal(0, 2)
            }
            
            historical_data.append(data_point)
        
        return historical_data
    
    def _time_series_forecast(self, historical_data: list[dict[str, Any]], 
                              duration: float, time_step: float) -> dict[str, Any]:
        """Time series forecasting"""
        try:
            # Extract time series for each variable
            variables = {}
            for data_point in historical_data:
                for key, value in data_point.items():
                    if key != "timestamp":
                        if key not in variables:
                            variables[key] = []
                        variables[key].append(value)
            
            # Simple forecasting using linear extrapolation
            predictions = {}
            time_points = int(duration / time_step)
            
            for var_name, values in variables.items():
                if len(values) < 2:
                    predictions[var_name] = [values[0]] * time_points
                    continue
                
                # Linear trend
                x = np.arange(len(values))
                coeffs = np.polyfit(x, values, 1)
                
                # Forecast
                future_x = np.arange(len(values), len(values) + time_points)
                forecast_values = np.polyval(coeffs, future_x)
                
                # Add some noise
                noise = np.random.normal(0, np.std(values) * 0.1, time_points)
                predictions[var_name] = (forecast_values + noise).tolist()
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error in time series forecast: {e}")
            return {}
    
    def _generate_sensor_readings_from_predictions(self, twin: DigitalTwin, 
                                                   predictions: dict[str, Any], 
                                                   duration: float, time_step: float) -> list[SensorReading]:
        """Generate sensor readings from predictions"""
        sensor_readings = []
        
        time_points = int(duration / time_step)
        
        for i in range(time_points):
            timestamp = datetime.now() + timedelta(seconds=i * time_step)
            
            for var_name, values in predictions.items():
                if i < len(values):
                    value = values[i]
                    
                    sensor_type = self._map_variable_to_sensor(var_name)
                    
                    reading = SensorReading(
                        sensor_id=f"pred_{var_name}_{i}",
                        sensor_type=sensor_type,
                        value=value,
                        unit=self._get_unit_for_sensor(sensor_type),
                        timestamp=timestamp,
                        location=(0, 0, 0),
                        quality_score=0.9,  # Slightly lower quality for predictions
                        metadata={"prediction": True}
                    )
                    
                    sensor_readings.append(reading)
        
        return sensor_readings
    
    def _map_variable_to_sensor(self, var_name: str) -> SensorType:
        """Map variable name to sensor type"""
        mapping = {
            "temperature": SensorType.TEMPERATURE,
            "pressure": SensorType.PRESSURE,
            "humidity": SensorType.HUMIDITY,
            "position": SensorType.POSITION,
            "velocity": SensorType.VELOCITY,
            "acceleration": SensorType.ACCELERATION
        }
        
        return mapping.get(var_name, SensorType.TEMPERATURE)
    
    def _get_unit_for_sensor(self, sensor_type: SensorType) -> str:
        """Get unit for sensor type"""
        units = {
            SensorType.TEMPERATURE: "°C",
            SensorType.PRESSURE: "Pa",
            SensorType.HUMIDITY: "%",
            SensorType.POSITION: "m",
            SensorType.VELOCITY: "m/s",
            SensorType.ACCELERATION: "m/s²"
        }
        
        return units.get(sensor_type, "unit")
    
    def _calculate_ml_metrics(self, predictions: dict[str, Any]) -> dict[str, float]:
        """Calculate ML performance metrics"""
        metrics = {}
        
        for var_name, values in predictions.items():
            if values:
                values_array = np.array(values)
                
                metrics[f"{var_name}_mean"] = np.mean(values_array)
                metrics[f"{var_name}_variance"] = np.var(values_array)
                metrics[f"{var_name}_trend"] = (values_array[-1] - values_array[0]) / len(values_array)
        
        return metrics
    
    def _calculate_model_accuracy(self, historical_data: list[dict[str, Any]], 
                                predictions: dict[str, Any]) -> float:
        """Calculate model accuracy"""
        try:
            # Simple accuracy calculation
            total_error = 0
            total_points = 0
            
            for var_name in predictions:
                if var_name in historical_data[0]:
                    historical_values = [d[var_name] for d in historical_data]
                    predicted_values = predictions[var_name][:len(historical_values)]
                    
                    if len(predicted_values) > 0:
                        mse = np.mean((np.array(historical_values) - np.array(predicted_values))**2)
                        total_error += mse
                        total_points += 1
            
            if total_points > 0:
                accuracy = 1.0 / (1.0 + total_error / total_points)
                return accuracy
            
            return 0.5  # Default accuracy
            
        except Exception as e:
            logger.error(f"Error calculating model accuracy: {e}")
            return 0.5
    
    def _fallback_simulation(self, twin: DigitalTwin, model: SimulationModel, 
                            duration: float, time_step: float) -> dict[str, Any]:
        """Fallback simulation"""
        # Simple linear interpolation
        time_points = int(duration / time_step)
        
        predictions = {}
        for var_name, initial_value in model.initial_conditions.items():
            # Simple linear trend
            trend = model.parameters.get("trend", 0)
            values = [initial_value + trend * i * time_step for i in range(time_points)]
            predictions[var_name] = values
        
        return {
            "state_variables": predictions,
            "sensor_readings": [],
            "performance_metrics": {},
            "model_accuracy": 0.5
        }
    
    async def predict_future_state(self, twin: DigitalTwin, states: list[SimulationState], 
                                  horizon: float, confidence_level: float) -> dict[str, Any]:
        """Predict future state using ML"""
        try:
            if len(states) < 10:
                return {"error": "Insufficient historical data"}
            
            # Extract time series from states
            time_series = {}
            for state in states:
                for var_name, value in state.state_variables.items():
                    if isinstance(value, list) and value:
                        if var_name not in time_series:
                            time_series[var_name] = []
                        time_series[var_name].append(value[-1])  # Use last value
            
            # Predict future values
            future_predictions = {}
            for var_name, values in time_series.items():
                if len(values) < 2:
                    continue
                
                # Use ARIMA-like prediction (simplified)
                future_values = self._predict_arima(values, horizon)
                future_predictions[var_name] = future_values
            
            # Calculate confidence intervals
            confidence_intervals = {}
            for var_name, values in future_predictions.items():
                std_dev = np.std(values)
                margin = std_dev * 1.96  # 95% confidence interval
                
                confidence_intervals[var_name] = {
                    "lower": [v - margin for v in values],
                    "upper": [v + margin for v in values]
                }
            
            return {
                "predictions": future_predictions,
                "confidence_intervals": confidence_intervals,
                "confidence_level": confidence_level,
                "horizon": horizon
            }
            
        except Exception as e:
            logger.error(f"Error predicting future state: {e}")
            return {"error": str(e)}
    
    def _predict_arima(self, values: list[float], horizon: int) -> list[float]:
        """Simple ARIMA-like prediction"""
        try:
            if len(values) < 2:
                return [values[-1]] * horizon
            
            # Simple AR(1) model
            # Calculate autocorrelation
            n = len(values)
            autocorr = np.corrcoef(values[:-1], values[1:])[0, 1]
            
            # Predict
            predictions = []
            last_value = values[-1]
            
            for i in range(horizon):
                if i == 0:
                    pred = autocorr * last_value + (1 - autocorr) * np.mean(values)
                else:
                    pred = autocorr * predictions[-1] + (1 - autocorr) * np.mean(values)
                
                predictions.append(pred)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error in ARIMA prediction: {e}")
            return [values[-1]] * horizon

class HybridEngine:
    """Hybrid simulation engine combining physics and data-driven approaches"""
    
    async def simulate(self, twin: DigitalTwin, model: SimulationModel, 
                      duration: float, time_step: float) -> dict[str, Any]:
        """Run hybrid simulation"""
        try:
            # Run physics simulation
            physics_engine = PhysicsEngine()
            physics_result = await physics_engine.simulate(twin, model, duration, time_step)
            
            # Run data-driven simulation
            data_engine = DataDrivenEngine()
            data_result = await data_engine.simulate(twin, model, duration, time_step)
            
            # Combine results
            combined_result = self._combine_simulation_results(physics_result, data_result)
            
            return combined_result
            
        except Exception as e:
            logger.error(f"Error in hybrid simulation: {e}")
            return {}
    
    def _combine_simulation_results(self, physics_result: dict[str, Any], 
                                   data_result: dict[str, Any]) -> dict[str, Any]:
        """Combine physics and data-driven results"""
        try:
            combined = {
                "state_variables": {},
                "sensor_readings": [],
                "performance_metrics": {},
                "physics_accuracy": physics_result.get("model_accuracy", 0.5),
                "data_accuracy": data_result.get("model_accuracy", 0.5)
            }
            
            # Combine state variables
            physics_vars = physics_result.get("state_variables", {})
            data_vars = data_result.get("state_variables", {})
            
            for var_name in set(physics_vars.keys()) | set(data_vars.keys()):
                if var_name in physics_vars and var_name in data_vars:
                    # Weighted average
                    physics_weight = 0.6
                    data_weight = 0.4
                    
                    physics_values = np.array(physics_vars[var_name])
                    data_values = np.array(data_vars[var_name])
                    
                    # Ensure same length
                    min_len = min(len(physics_values), len(data_values))
                    combined_values = (physics_weight * physics_values[:min_len] + 
                                    data_weight * data_values[:min_len])
                    
                    combined["state_variables"][var_name] = combined_values.tolist()
                elif var_name in physics_vars:
                    combined["state_variables"][var_name] = physics_vars[var_name]
                else:
                    combined["state_variables"][var_name] = data_vars[var_name]
            
            # Combine sensor readings
            combined["sensor_readings"] = physics_result.get("sensor_readings", [])
            combined["sensor_readings"].extend(data_result.get("sensor_readings", []))
            
            # Combine performance metrics
            physics_metrics = physics_result.get("performance_metrics", {})
            data_metrics = data_result.get("performance_metrics", {})
            
            for metric_name in set(physics_metrics.keys()) | set(data_metrics.keys()):
                if metric_name in physics_metrics and metric_name in data_metrics:
                    combined["performance_metrics"][metric_name] = (
                        physics_metrics[metric_name] + data_metrics[metric_name]
                    ) / 2
                elif metric_name in physics_metrics:
                    combined["performance_metrics"][metric_name] = physics_metrics[metric_name]
                else:
                    combined["performance_metrics"][metric_name] = data_metrics[metric_name]
            
            return combined
            
        except Exception as e:
            logger.error(f"Error combining results: {e}")
            return {}

class SynchronizationManager:
    """Synchronization manager for digital twins"""
    
    def __init__(self):
        self.sync_strategies = {
            "real_time": self._real_time_sync,
            "batch": self._batch_sync,
            "event_driven": self._event_driven_sync
        }
    
    async def calculate_sync_quality(self, twin: DigitalTwin, 
                                    sensor_data: list[SensorReading]) -> float:
        """Calculate synchronization quality"""
        try:
            if not sensor_data:
                return 0.0
            
            # Calculate data freshness
            latest_timestamp = max(reading.timestamp for reading in sensor_data)
            data_age = (datetime.now() - latest_timestamp).total_seconds()
            freshness_score = max(0, 1 - data_age / 3600)  # 1 hour max
            
            # Calculate data completeness
            expected_sensors = len(twin.sensors)
            actual_sensors = len(set(reading.sensor_id for reading in sensor_data))
            completeness_score = actual_sensors / max(expected_sensors, 1)
            
            # Calculate data quality
            quality_scores = [reading.quality_score for reading in sensor_data]
            quality_score = np.mean(quality_scores) if quality_scores else 0.0
            
            # Calculate overall sync quality
            sync_quality = (freshness_score * 0.4 + 
                           completeness_score * 0.3 + 
                           quality_score * 0.3)
            
            return sync_quality
            
        except Exception as e:
            logger.error(f"Error calculating sync quality: {e}")
            return 0.0
    
    async def _real_time_sync(self, twin: DigitalTwin):
        """Real-time synchronization"""
        # Implementation for real-time sync
        pass
    
    async def _batch_sync(self, twin: DigitalTwin):
        """Batch synchronization"""
        # Implementation for batch sync
        pass
    
    async def _event_driven_sync(self, twin: DigitalTwin):
        """Event-driven synchronization"""
        # Implementation for event-driven sync
        pass

# Global digital twin manager
dt_manager = DigitalTwinManager()

# API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/digital_twins", tags=["digital_twins"])

class TwinCreationRequest(BaseModel):
    name: str
    twin_type: str
    description: str
    physical_object_id: str
    geometry: dict[str, Any] = {}
    properties: dict[str, Any] = {}
    behaviors: dict[str, Any] = {}
    sensors: list[str] = []
    simulation_models: list[str] = []
    sync_frequency: float = 1.0

class ModelCreationRequest(BaseModel):
    name: str
    twin_id: str
    model_type: str
    equations: list[str] = []
    parameters: dict[str, Any] = {}
    initial_conditions: dict[str, Any] = {}
    boundary_conditions: dict[str, Any] = {}

class SimulationRequest(BaseModel):
    twin_id: str
    model_id: str
    duration: float = 10.0
    time_step: float = 0.1

@router.post("/twins/create")
async def create_digital_twin(request: TwinCreationRequest):
    """Create digital twin"""
    try:
        twin = await dt_manager.create_digital_twin({
            "name": request.name,
            "twin_type": request.twin_type,
            "description": request.description,
            "physical_object_id": request.physical_object_id,
            "geometry": request.geometry,
            "properties": request.properties,
            "behaviors": request.behaviors,
            "sensors": request.sensors,
            "simulation_models": request.simulation_models,
            "sync_frequency": request.sync_frequency
        })
        
        return asdict(twin)
    except Exception as e:
        logger.error(f"Error creating digital twin: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/create")
async def create_simulation_model(request: ModelCreationRequest):
    """Create simulation model"""
    try:
        model = await dt_manager.create_simulation_model({
            "name": request.name,
            "twin_id": request.twin_id,
            "model_type": request.model_type,
            "equations": request.equations,
            "parameters": request.parameters,
            "initial_conditions": request.initial_conditions,
            "boundary_conditions": request.boundary_conditions
        })
        
        return asdict(model)
    except Exception as e:
        logger.error(f"Error creating simulation model: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/simulation/run")
async def run_simulation(request: SimulationRequest):
    """Run simulation"""
    try:
        state = await dt_manager.run_simulation(
            request.twin_id,
            request.model_id,
            request.duration,
            request.time_step
        )
        
        return asdict(state)
    except Exception as e:
        logger.error(f"Error running simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/twins")
async def list_twins():
    """List all digital twins"""
    try:
        twins = []
        for twin in dt_manager.twins.values():
            twins.append({
                "id": twin.id,
                "name": twin.name,
                "twin_type": twin.twin_type.value,
                "description": twin.description,
                "physical_object_id": twin.physical_object_id,
                "is_active": twin.is_active,
                "sync_frequency": twin.sync_frequency,
                "created_at": twin.created_at.isoformat(),
                "updated_at": twin.updated_at.isoformat(),
                "sensor_count": len(twin.sensors)
            })
        
        return {"twins": twins}
    except Exception as e:
        logger.error(f"Error listing twins: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/twins/{twin_id}/visualization")
async def get_twin_visualization(twin_id: str):
    """Get twin visualization data"""
    try:
        viz_data = dt_manager.get_twin_visualization(twin_id)
        return viz_data
    except Exception as e:
        logger.error(f"Error getting twin visualization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/twins/{twin_id}/predict")
async def predict_future_state(twin_id: str, horizon: float, confidence_level: float = 0.95):
    """Predict future state"""
    try:
        predictions = await dt_manager.predict_future_state(twin_id, horizon, confidence_level)
        return predictions
    except Exception as e:
        logger.error(f"Error predicting future state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/twins/{twin_id}/anomalies")
async def detect_anomalies(twin_id: str, threshold: float = 0.95):
    """Detect anomalies"""
    try:
        anomalies = await dt_manager.detect_anomalies(twin_id, threshold)
        return {"anomalies": anomalies}
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/twins/{twin_id}/optimize")
async def optimize_parameters(twin_id: str, model_id: str, objective_function: str, 
                              constraints: dict[str, Any]):
    """Optimize twin parameters"""
    try:
        result = await dt_manager.optimize_parameters(twin_id, model_id, objective_function, constraints)
        return result
    except Exception as e:
        logger.error(f"Error optimizing parameters: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/twins/{twin_id}/sync")
async def sync_with_physical(twin_id: str):
    """Sync with physical object"""
    try:
        sync_result = await dt_manager.sync_with_physical(twin_id)
        return sync_result
    except Exception as e:
        logger.error(f"Error syncing with physical: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_digital_twin_status():
    """Get digital twin system status"""
    try:
        return {
            "total_twins": len(dt_manager.twins),
            "active_twins": len([t for t in dt_manager.twins.values() if t.is_active]),
            "total_models": len(dt_manager.simulation_models),
            "total_states": sum(len(states) for states in dt_manager.simulation_states.values()),
            "sensor_data_points": sum(len(data) for data in dt_manager.sensor_data.values())
        }
    except Exception as e:
        logger.error(f"Error getting digital twin status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
