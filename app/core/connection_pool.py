"""
Advanced Connection Pool Manager for Asmblr
High-performance connection pooling with intelligent load balancing
"""

import asyncio
import time
import json
import hashlib
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from contextlib import asynccontextmanager
import aioredis
import aiohttp
import asyncpg
import motor.motor_asyncio
from loguru import logger
import psutil

class ConnectionType(Enum):
    """Connection types"""
    REDIS = "redis"
    HTTP = "http"
    POSTGRESQL = "postgresql"
    MONGODB = "mongodb"
    CUSTOM = "custom"

class PoolStatus(Enum):
    """Pool status states"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"

@dataclass
class ConnectionConfig:
    """Connection configuration"""
    host: str
    port: int
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ssl: bool = False
    timeout: float = 30.0
    max_connections: int = 20
    min_connections: int = 5
    connection_timeout: float = 10.0
    command_timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 1.0
    health_check_interval: float = 30.0
    idle_timeout: float = 300.0
    max_lifetime: float = 3600.0

@dataclass
class PoolMetrics:
    """Pool performance metrics"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    failed_connections: int = 0
    avg_response_time: float = 0.0
    throughput_per_second: float = 0.0
    error_rate: float = 0.0
    last_health_check: Optional[datetime] = None
    uptime_percentage: float = 100.0

class AdvancedConnectionPool:
    """Advanced connection pool with intelligent management"""
    
    def __init__(self, connection_type: ConnectionType, config: ConnectionConfig):
        self.connection_type = connection_type
        self.config = config
        self.pool_status = PoolStatus.HEALTHY
        
        # Connection pools
        self.connections = []
        self.available_connections = asyncio.Queue()
        self.active_connections = set()
        
        # Performance metrics
        self.metrics = PoolMetrics()
        self.response_times = []
        self.error_count = 0
        self.total_requests = 0
        
        # Health monitoring
        self.health_check_task = None
        self.maintenance_mode = False
        
        # Load balancing
        self.connection_weights = {}
        self.round_robin_index = 0
        
        # Circuit breaker
        self.circuit_breaker_threshold = 10
        self.circuit_breaker_timeout = 60.0
        self.circuit_breaker_failures = 0
        self.circuit_breaker_last_failure = 0.0
        
        # Connection lifecycle
        self.connection_creation_time = {}
        self.connection_last_used = {}
        
    async def initialize(self):
        """Initialize the connection pool"""
        try:
            logger.info(f"Initializing {self.connection_type.value} connection pool...")
            
            # Create initial connections
            await self._create_initial_connections()
            
            # Start health monitoring
            await self.start_health_monitoring()
            
            # Start connection maintenance
            await self.start_connection_maintenance()
            
            logger.info(f"Connection pool initialized with {len(self.connections)} connections")
            
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            self.pool_status = PoolStatus.UNHEALTHY
            raise
    
    async def _create_initial_connections(self):
        """Create initial connections"""
        for _ in range(self.config.min_connections):
            try:
                connection = await self._create_connection()
                self.connections.append(connection)
                await self.available_connections.put(connection)
                self.connection_creation_time[connection] = time.time()
                self.connection_last_used[connection] = time.time()
            except Exception as e:
                logger.error(f"Failed to create initial connection: {e}")
                raise
    
    async def _create_connection(self):
        """Create a single connection"""
        if self.connection_type == ConnectionType.REDIS:
            return await self._create_redis_connection()
        elif self.connection_type == ConnectionType.HTTP:
            return await self._create_http_connection()
        elif self.connection_type == ConnectionType.POSTGRESQL:
            return await self._create_postgresql_connection()
        elif self.connection_type == ConnectionType.MONGODB:
            return await self._create_mongodb_connection()
        else:
            raise ValueError(f"Unsupported connection type: {self.connection_type}")
    
    async def _create_redis_connection(self):
        """Create Redis connection"""
        return aioredis.from_url(
            f"redis://{self.config.host}:{self.config.port}/{self.config.database or 0}",
            password=self.config.password,
            ssl=self.config.ssl,
            socket_timeout=self.config.timeout,
            socket_connect_timeout=self.config.connection_timeout,
            max_connections=self.config.max_connections,
            retry_on_timeout=True,
            retry_on_error=[ConnectionError, TimeoutError]
        )
    
    async def _create_http_connection(self):
        """Create HTTP connection"""
        connector = aiohttp.TCPConnector(
            limit=self.config.max_connections,
            limit_per_host=self.config.max_connections,
            ttl_dns_cache=300,
            use_dns_cache=True,
            ssl=self.config.ssl,
            timeout=aiohttp.ClientTimeout(
                total=self.config.timeout,
                connect=self.config.connection_timeout,
                sock_read=self.config.command_timeout
            )
        )
        
        session = aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(
                total=self.config.timeout,
                connect=self.config.connection_timeout,
                sock_read=self.config.command_timeout
            )
        )
        
        return session
    
    async def _create_postgresql_connection(self):
        """Create PostgreSQL connection"""
        return await asyncpg.create_pool(
            host=self.config.host,
            port=self.config.port,
            user=self.config.username,
            password=self.config.password,
            database=self.config.database,
            min_size=self.config.min_connections,
            max_size=self.config.max_connections,
            command_timeout=self.config.command_timeout,
            server_settings={
                'application_name': 'asmblr_connection_pool',
                'jit': 'off'
            }
        )
    
    async def _create_mongodb_connection(self):
        """Create MongoDB connection"""
        client = motor.motor_asyncio.AsyncIOMotorClient(
            f"mongodb://{self.config.host}:{self.config.port}",
            maxPoolSize=self.config.max_connections,
            minPoolSize=self.config.min_connections,
            serverSelectionTimeoutMS=int(self.config.timeout * 1000),
            socketTimeoutMS=int(self.config.command_timeout * 1000),
            connectTimeoutMS=int(self.config.connection_timeout * 1000)
        )
        
        return client
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool"""
        if self.pool_status == PoolStatus.UNHEALTHY:
            raise Exception("Connection pool is unhealthy")
        
        if self.maintenance_mode:
            raise Exception("Connection pool is in maintenance mode")
        
        # Check circuit breaker
        if self._is_circuit_breaker_open():
            raise Exception("Circuit breaker is open")
        
        start_time = time.time()
        
        try:
            # Get available connection
            connection = await asyncio.wait_for(
                self.available_connections.get(),
                timeout=self.config.connection_timeout
            )
            
            # Mark as active
            self.active_connections.add(connection)
            self.connection_last_used[connection] = time.time()
            
            # Update metrics
            self.metrics.active_connections = len(self.active_connections)
            self.metrics.idle_connections = self.available_connections.qsize()
            
            yield connection
            
        except Exception as e:
            self.error_count += 1
            self.total_requests += 1
            self._update_circuit_breaker()
            raise
        finally:
            # Return connection to pool
            if 'connection' in locals():
                self.active_connections.discard(connection)
                await self.available_connections.put(connection)
                
                # Update metrics
                self.metrics.active_connections = len(self.active_connections)
                self.metrics.idle_connections = self.available_connections.qsize()
                
                # Record response time
                response_time = time.time() - start_time
                self.response_times.append(response_time)
                if len(self.response_times) > 1000:
                    self.response_times = self.response_times[-1000:]
                
                self.metrics.avg_response_time = sum(self.response_times) / len(self.response_times)
                self.metrics.throughput_per_second = self.total_requests / max(time.time() - self.metrics.last_health_check.timestamp() if self.metrics.last_health_check else time.time(), 1)
                self.metrics.error_rate = self.error_count / max(self.total_requests, 1)
    
    async def execute_query(self, query: str, *args, **kwargs):
        """Execute a query using the connection pool"""
        async with self.get_connection() as connection:
            if self.connection_type == ConnectionType.REDIS:
                return await self._execute_redis_query(connection, query, *args, **kwargs)
            elif self.connection_type == ConnectionType.HTTP:
                return await self._execute_http_query(connection, query, *args, **kwargs)
            elif self.connection_type == ConnectionType.POSTGRESQL:
                return await self._execute_postgresql_query(connection, query, *args, **kwargs)
            elif self.connection_type == ConnectionType.MONGODB:
                return await self._execute_mongodb_query(connection, query, *args, **kwargs)
            else:
                raise ValueError(f"Query execution not supported for {self.connection_type}")
    
    async def _execute_redis_query(self, connection, query: str, *args, **kwargs):
        """Execute Redis query"""
        if query.upper().startswith('GET'):
            return await connection.get(*args, **kwargs)
        elif query.upper().startswith('SET'):
            return await connection.set(*args, **kwargs)
        elif query.upper().startswith('DEL'):
            return await connection.delete(*args, **kwargs)
        elif query.upper().startswith('EXISTS'):
            return await connection.exists(*args, **kwargs)
        else:
            # For complex queries, use the connection directly
            method = getattr(connection, query.lower(), None)
            if method:
                return await method(*args, **kwargs)
            else:
                raise ValueError(f"Unsupported Redis query: {query}")
    
    async def _execute_http_query(self, connection, query: str, *args, **kwargs):
        """Execute HTTP query"""
        method = query.upper()
        url = args[0] if args else kwargs.get('url')
        
        if method == 'GET':
            return await connection.get(url, **kwargs)
        elif method == 'POST':
            return await connection.post(url, **kwargs)
        elif method == 'PUT':
            return await connection.put(url, **kwargs)
        elif method == 'DELETE':
            return await connection.delete(url, **kwargs)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
    
    async def _execute_postgresql_query(self, connection, query: str, *args, **kwargs):
        """Execute PostgreSQL query"""
        return await connection.fetch(query, *args, **kwargs)
    
    async def _execute_mongodb_query(self, connection, query: str, *args, **kwargs):
        """Execute MongoDB query"""
        db = connection[self.config.database]
        collection = db[args[0] if args else kwargs.get('collection')]
        
        if query.upper() == 'FIND':
            return await collection.find(kwargs.get('filter', {})).to_list(None)
        elif query.upper() == 'INSERT':
            return await collection.insert_one(kwargs.get('document', {}))
        elif query.upper() == 'UPDATE':
            return await collection.update_one(
                kwargs.get('filter', {}),
                kwargs.get('update', {})
            )
        elif query.upper() == 'DELETE':
            return await collection.delete_one(kwargs.get('filter', {}))
        else:
            raise ValueError(f"Unsupported MongoDB query: {query}")
    
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
                await self._perform_health_check()
                await asyncio.sleep(self.config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(self.config.health_check_interval)
    
    async def _perform_health_check(self):
        """Perform health check"""
        try:
            # Test connection availability
            if self.connections:
                test_connection = self.connections[0]
                await self._test_connection(test_connection)
            
            # Update pool status
            self._update_pool_status()
            
            # Update metrics
            self.metrics.last_health_check = datetime.now()
            self.metrics.total_connections = len(self.connections)
            
            # Reset circuit breaker if healthy
            if self.pool_status == PoolStatus.HEALTHY:
                self.circuit_breaker_failures = 0
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.pool_status = PoolStatus.UNHEALTHY
            self._update_circuit_breaker()
    
    async def _test_connection(self, connection):
        """Test a specific connection"""
        if self.connection_type == ConnectionType.REDIS:
            await connection.ping()
        elif self.connection_type == ConnectionType.HTTP:
            async with connection.get(f"http://{self.config.host}:{self.config.port}/health") as response:
                response.raise_for_status()
        elif self.connection_type == ConnectionType.POSTGRESQL:
            await connection.fetch("SELECT 1")
        elif self.connection_type == ConnectionType.MONGODB:
            await connection.admin.command('ping')
    
    def _update_pool_status(self):
        """Update pool status based on metrics"""
        error_rate = self.metrics.error_rate
        
        if error_rate > 0.5:
            self.pool_status = PoolStatus.UNHEALTHY
        elif error_rate > 0.1:
            self.pool_status = PoolStatus.DEGRADED
        elif self.maintenance_mode:
            self.pool_status = PoolStatus.MAINTENANCE
        else:
            self.pool_status = PoolStatus.HEALTHY
    
    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open"""
        return (
            self.circuit_breaker_failures >= self.circuit_breaker_threshold and
            time.time() - self.circuit_breaker_last_failure < self.circuit_breaker_timeout
        )
    
    def _update_circuit_breaker(self):
        """Update circuit breaker state"""
        self.circuit_breaker_failures += 1
        self.circuit_breaker_last_failure = time.time()
    
    async def start_connection_maintenance(self):
        """Start connection maintenance"""
        asyncio.create_task(self._connection_maintenance_loop())
        logger.info("Connection maintenance started")
    
    async def _connection_maintenance_loop(self):
        """Connection maintenance loop"""
        while True:
            try:
                await self._maintain_connections()
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Connection maintenance error: {e}")
                await asyncio.sleep(60)
    
    async def _maintain_connections(self):
        """Maintain connection pool"""
        current_time = time.time()
        
        # Remove old connections
        connections_to_remove = []
        for connection in self.connections:
            creation_time = self.connection_creation_time.get(connection, 0)
            if current_time - creation_time > self.config.max_lifetime:
                connections_to_remove.append(connection)
        
        # Remove old connections
        for connection in connections_to_remove:
            await self._close_connection(connection)
            self.connections.remove(connection)
            del self.connection_creation_time[connection]
            del self.connection_last_used[connection]
        
        # Create new connections to maintain minimum
        while len(self.connections) < self.config.min_connections:
            try:
                connection = await self._create_connection()
                self.connections.append(connection)
                await self.available_connections.put(connection)
                self.connection_creation_time[connection] = time.time()
                self.connection_last_used[connection] = time.time()
            except Exception as e:
                logger.error(f"Failed to create maintenance connection: {e}")
                break
    
    async def _close_connection(self, connection):
        """Close a connection"""
        try:
            if self.connection_type == ConnectionType.HTTP:
                await connection.close()
            elif self.connection_type == ConnectionType.POSTGRESQL:
                await connection.close()
            elif self.connection_type == ConnectionType.MONGODB:
                connection.close()
            # Redis connections are managed by the pool
        except Exception as e:
            logger.error(f"Error closing connection: {e}")
    
    async def get_metrics(self) -> PoolMetrics:
        """Get pool metrics"""
        self.metrics.total_connections = len(self.connections)
        self.metrics.active_connections = len(self.active_connections)
        self.metrics.idle_connections = self.available_connections.qsize()
        
        if self.total_requests > 0:
            self.metrics.error_rate = self.error_count / self.total_requests
        
        return self.metrics
    
    async def set_maintenance_mode(self, enabled: bool):
        """Enable or disable maintenance mode"""
        self.maintenance_mode = enabled
        if enabled:
            self.pool_status = PoolStatus.MAINTENANCE
            logger.info("Connection pool entered maintenance mode")
        else:
            self.pool_status = PoolStatus.HEALTHY
            logger.info("Connection pool exited maintenance mode")
    
    async def shutdown(self):
        """Shutdown the connection pool"""
        logger.info("Shutting down connection pool...")
        
        # Stop health monitoring
        await self.stop_health_monitoring()
        
        # Close all connections
        for connection in self.connections:
            await self._close_connection(connection)
        
        self.connections.clear()
        self.available_connections = asyncio.Queue()
        self.active_connections.clear()
        
        logger.info("Connection pool shutdown complete")

# Connection pool registry
connection_pools = {}

def get_connection_pool(connection_type: ConnectionType, config: ConnectionConfig) -> AdvancedConnectionPool:
    """Get or create a connection pool"""
    key = f"{connection_type.value}_{config.host}_{config.port}"
    
    if key not in connection_pools:
        pool = AdvancedConnectionPool(connection_type, config)
        connection_pools[key] = pool
    
    return connection_pools[key]
