"""
Intelligent Load Balancer for Asmblr
Advanced load balancing with health checks and circuit breakers
"""

import asyncio
import time
import random
from typing import Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from collections import deque
import statistics
from loguru import logger
import aiohttp
import redis.asyncio as redis

class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    RANDOM = "random"
    HEALTH_AWARE = "health_aware"

class HealthStatus(Enum):
    """Health status of endpoints"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class Endpoint:
    """Represents a backend endpoint"""
    id: str
    host: str
    port: int
    weight: float = 1.0
    max_connections: int = 100
    health_status: HealthStatus = HealthStatus.UNKNOWN
    last_health_check: datetime | None = None
    response_times: deque = None
    active_connections: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    circuit_breaker_open: bool = False
    circuit_breaker_failures: int = 0
    circuit_breaker_last_failure: datetime | None = None
    metadata: dict[str, Any] | None = None
    
    def __post_init__(self):
        if self.response_times is None:
            self.response_times = deque(maxlen=100)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 1.0
        return (self.total_requests - self.failed_requests) / self.total_requests
    
    @property
    def avg_response_time(self) -> float:
        """Calculate average response time"""
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times)
    
    @property
    def is_available(self) -> bool:
        """Check if endpoint is available"""
        return (
            self.health_status == HealthStatus.HEALTHY and
            not self.circuit_breaker_open and
            self.active_connections < self.max_connections
        )

@dataclass
class LoadBalancerMetrics:
    """Load balancer metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    requests_per_second: float = 0.0
    endpoint_distribution: dict[str, int] = None
    circuit_breaker_activations: int = 0
    health_check_failures: int = 0
    load_balancing_efficiency: float = 0.0
    
    def __post_init__(self):
        if self.endpoint_distribution is None:
            self.endpoint_distribution = {}
    
    @property
    def success_rate(self) -> float:
        """Calculate overall success rate"""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests

class IntelligentLoadBalancer:
    """Intelligent load balancer with health checks and circuit breakers"""
    
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_CONNECTIONS):
        self.strategy = strategy
        self.endpoints: list[Endpoint] = []
        self.round_robin_index = 0
        self.metrics = LoadBalancerMetrics()
        
        # Health checking
        self.health_check_interval = 30.0
        self.health_check_timeout = 5.0
        self.health_check_task = None
        
        # Circuit breaker settings
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_timeout = 60.0
        self.circuit_breaker_recovery_timeout = 30.0
        
        # Performance tracking
        self.request_times = deque(maxlen=1000)
        self.endpoint_weights = {}
        
        # Redis for distributed load balancing
        self.redis_client = None
        self.redis_enabled = False
        
        # Adaptive features
        self.adaptive_weights = True
        self.health_aware_routing = True
        self.sticky_sessions = False
        self.session_affinity = {}
        
    async def initialize(self):
        """Initialize the load balancer"""
        try:
            # Initialize Redis connection
            try:
                self.redis_client = redis.from_url(
                    "redis://localhost:6379/2",
                    max_connections=10
                )
                await self.redis_client.ping()
                self.redis_enabled = True
                logger.info("Redis connection established for distributed load balancing")
            except Exception as e:
                logger.warning(f"Redis not available, using local load balancing: {e}")
            
            # Start health monitoring
            await self.start_health_monitoring()
            
            logger.info(f"Load balancer initialized with {len(self.endpoints)} endpoints")
            
        except Exception as e:
            logger.error(f"Failed to initialize load balancer: {e}")
            raise
    
    def add_endpoint(self, endpoint: Endpoint):
        """Add an endpoint to the load balancer"""
        self.endpoints.append(endpoint)
        self.endpoint_weights[endpoint.id] = endpoint.weight
        logger.info(f"Added endpoint {endpoint.id} ({endpoint.host}:{endpoint.port})")
    
    def remove_endpoint(self, endpoint_id: str):
        """Remove an endpoint from the load balancer"""
        self.endpoints = [ep for ep in self.endpoints if ep.id != endpoint_id]
        if endpoint_id in self.endpoint_weights:
            del self.endpoint_weights[endpoint_id]
        logger.info(f"Removed endpoint {endpoint_id}")
    
    async def get_endpoint(self, session_id: str | None = None) -> Endpoint | None:
        """Get the best endpoint for a request"""
        if not self.endpoints:
            return None
        
        # Filter available endpoints
        available_endpoints = [ep for ep in self.endpoints if ep.is_available]
        
        if not available_endpoints:
            logger.warning("No available endpoints")
            return None
        
        # Apply sticky sessions if enabled
        if self.sticky_sessions and session_id:
            sticky_endpoint = self.session_affinity.get(session_id)
            if sticky_endpoint:
                for ep in available_endpoints:
                    if ep.id == sticky_endpoint and ep.is_available:
                        return ep
        
        # Select endpoint based on strategy
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            endpoint = self._round_robin_select(available_endpoints)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            endpoint = self._least_connections_select(available_endpoints)
        elif self.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
            endpoint = self._least_response_time_select(available_endpoints)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            endpoint = self._weighted_round_robin_select(available_endpoints)
        elif self.strategy == LoadBalancingStrategy.RANDOM:
            endpoint = self._random_select(available_endpoints)
        elif self.strategy == LoadBalancingStrategy.HEALTH_AWARE:
            endpoint = self._health_aware_select(available_endpoints)
        else:
            endpoint = available_endpoints[0]
        
        # Update sticky session if enabled
        if self.sticky_sessions and session_id and endpoint:
            self.session_affinity[session_id] = endpoint.id
        
        return endpoint
    
    def _round_robin_select(self, endpoints: list[Endpoint]) -> Endpoint:
        """Round robin selection"""
        endpoint = endpoints[self.round_robin_index % len(endpoints)]
        self.round_robin_index += 1
        return endpoint
    
    def _least_connections_select(self, endpoints: list[Endpoint]) -> Endpoint:
        """Select endpoint with least connections"""
        return min(endpoints, key=lambda ep: ep.active_connections)
    
    def _least_response_time_select(self, endpoints: list[Endpoint]) -> Endpoint:
        """Select endpoint with least response time"""
        return min(endpoints, key=lambda ep: ep.avg_response_time)
    
    def _weighted_round_robin_select(self, endpoints: list[Endpoint]) -> Endpoint:
        """Weighted round robin selection"""
        # Create weighted list
        weighted_endpoints = []
        for endpoint in endpoints:
            weight = int(endpoint.weight * 10)  # Convert to integer
            weighted_endpoints.extend([endpoint] * weight)
        
        if not weighted_endpoints:
            return endpoints[0]
        
        endpoint = weighted_endpoints[self.round_robin_index % len(weighted_endpoints)]
        self.round_robin_index += 1
        return endpoint
    
    def _random_select(self, endpoints: list[Endpoint]) -> Endpoint:
        """Random selection"""
        return random.choice(endpoints)
    
    def _health_aware_select(self, endpoints: list[Endpoint]) -> Endpoint:
        """Health-aware selection"""
        # Prioritize healthy endpoints
        healthy_endpoints = [ep for ep in endpoints if ep.health_status == HealthStatus.HEALTHY]
        if healthy_endpoints:
            return self._least_response_time_select(healthy_endpoints)
        
        # Fall back to degraded endpoints
        degraded_endpoints = [ep for ep in endpoints if ep.health_status == HealthStatus.DEGRADED]
        if degraded_endpoints:
            return self._least_response_time_select(degraded_endpoints)
        
        # Last resort
        return endpoints[0]
    
    @asynccontextmanager
    async def execute_request(self, session_id: str | None = None):
        """Execute a request with load balancing"""
        endpoint = await self.get_endpoint(session_id)
        
        if not endpoint:
            raise Exception("No available endpoints")
        
        start_time = time.time()
        
        try:
            # Increment active connections
            endpoint.active_connections += 1
            endpoint.total_requests += 1
            self.metrics.total_requests += 1
            
            # Update distribution
            self.metrics.endpoint_distribution[endpoint.id] = self.metrics.endpoint_distribution.get(endpoint.id, 0) + 1
            
            # Create HTTP session for the request
            async with aiohttp.ClientSession() as session:
                # Perform health check if needed
                if endpoint.health_status == HealthStatus.UNKNOWN:
                    await self._check_endpoint_health(endpoint)
                
                # Execute request (placeholder - actual implementation would depend on use case)
                url = f"http://{endpoint.host}:{endpoint.port}/health"
                async with session.get(url, timeout=self.health_check_timeout) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.metrics.successful_requests += 1
                    else:
                        raise Exception(f"Request failed with status {response.status}")
            
            # Update metrics
            response_time = time.time() - start_time
            endpoint.response_times.append(response_time)
            self.request_times.append(response_time)
            self.metrics.avg_response_time = statistics.mean(self.request_times)
            
            # Calculate requests per second
            if len(self.request_times) > 1:
                time_span = self.request_times[-1] - self.request_times[0]
                if time_span > 0:
                    self.metrics.requests_per_second = len(self.request_times) / time_span
            
            yield result
            
        except Exception as e:
            endpoint.failed_requests += 1
            self.metrics.failed_requests += 1
            
            # Update circuit breaker
            endpoint.circuit_breaker_failures += 1
            endpoint.circuit_breaker_last_failure = datetime.now()
            
            if endpoint.circuit_breaker_failures >= self.circuit_breaker_threshold:
                endpoint.circuit_breaker_open = True
                self.metrics.circuit_breaker_activations += 1
                logger.warning(f"Circuit breaker opened for endpoint {endpoint.id}")
            
            raise
        finally:
            # Decrement active connections
            endpoint.active_connections = max(0, endpoint.active_connections - 1)
    
    async def start_health_monitoring(self):
        """Start health monitoring"""
        self.health_check_task = asyncio.create_task(self._health_monitoring_loop())
        logger.info("Health monitoring started")
    
    async def stop_health_monitoring(self):
        """Stop health monitoring"""
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitoring stopped")
    
    async def _health_monitoring_loop(self):
        """Health monitoring loop"""
        while True:
            try:
                await self._check_all_endpoints_health()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(self.health_check_interval)
    
    async def _check_all_endpoints_health(self):
        """Check health of all endpoints"""
        tasks = []
        for endpoint in self.endpoints:
            tasks.append(self._check_endpoint_health(endpoint))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_endpoint_health(self, endpoint: Endpoint):
        """Check health of a specific endpoint"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.health_check_timeout)) as session:
                url = f"http://{endpoint.host}:{endpoint.port}/health"
                async with session.get(url) as response:
                    if response.status == 200:
                        endpoint.health_status = HealthStatus.HEALTHY
                    else:
                        endpoint.health_status = HealthStatus.DEGRADED
        except Exception as e:
            endpoint.health_status = HealthStatus.UNHEALTHY
            self.metrics.health_check_failures += 1
            logger.warning(f"Health check failed for {endpoint.id}: {e}")
        
        endpoint.last_health_check = datetime.now()
        
        # Check circuit breaker recovery
        if endpoint.circuit_breaker_open:
            time_since_failure = (datetime.now() - endpoint.circuit_breaker_last_failure).total_seconds()
            if time_since_failure > self.circuit_breaker_recovery_timeout:
                endpoint.circuit_breaker_open = False
                endpoint.circuit_breaker_failures = 0
                logger.info(f"Circuit breaker recovered for endpoint {endpoint.id}")
    
    def update_weights(self):
        """Update endpoint weights based on performance"""
        if not self.adaptive_weights:
            return
        
        for endpoint in self.endpoints:
            # Calculate performance score
            success_rate = endpoint.success_rate
            response_time = endpoint.avg_response_time
            
            # Normalize response time (lower is better)
            max_response_time = max(ep.avg_response_time for ep in self.endpoints if ep.avg_response_time > 0)
            normalized_response_time = 1.0 - (response_time / max_response_time if max_response_time > 0 else 0)
            
            # Calculate weight
            performance_score = (success_rate * 0.7) + (normalized_response_time * 0.3)
            endpoint.weight = max(0.1, performance_score * 2.0)  # Scale to 0.1-2.0 range
            
            self.endpoint_weights[endpoint.id] = endpoint.weight
    
    def get_metrics(self) -> LoadBalancerMetrics:
        """Get load balancer metrics"""
        # Update efficiency
        if self.metrics.total_requests > 0:
            ideal_distribution = 1.0 / len(self.endpoints) if self.endpoints else 1.0
            actual_distribution = max(self.metrics.endpoint_distribution.values()) / self.metrics.total_requests if self.metrics.total_requests > 0 else 0
            self.metrics.load_balancing_efficiency = 1.0 - abs(ideal_distribution - actual_distribution)
        
        return self.metrics
    
    async def set_strategy(self, strategy: LoadBalancingStrategy):
        """Change load balancing strategy"""
        self.strategy = strategy
        self.round_robin_index = 0  # Reset round robin index
        logger.info(f"Load balancing strategy changed to {strategy.value}")
    
    def enable_sticky_sessions(self, enabled: bool):
        """Enable or disable sticky sessions"""
        self.sticky_sessions = enabled
        if not enabled:
            self.session_affinity.clear()
        logger.info(f"Sticky sessions {'enabled' if enabled else 'disabled'}")
    
    async def shutdown(self):
        """Shutdown the load balancer"""
        logger.info("Shutting down load balancer...")
        
        # Stop health monitoring
        await self.stop_health_monitoring()
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Load balancer shutdown complete")

# Global load balancer instance
load_balancer = IntelligentLoadBalancer()
