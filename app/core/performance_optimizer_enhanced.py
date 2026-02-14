"""
Performance optimization utilities for Asmblr
Connection pooling, request batching, and resource management
"""

import asyncio
import time
import json
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from collections import defaultdict, deque
import threading
from concurrent.futures import ThreadPoolExecutor
import httpx
import redis.asyncio as redis
from loguru import logger
from prometheus_client import Histogram, Counter, Gauge


@dataclass
class ConnectionPoolConfig:
    """Configuration for connection pools"""
    max_connections: int = 20
    min_connections: int = 2
    max_idle_time: int = 300  # seconds
    connection_timeout: int = 30
    read_timeout: int = 60
    write_timeout: int = 60
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class BatchConfig:
    """Configuration for request batching"""
    max_batch_size: int = 100
    batch_timeout: float = 5.0  # seconds
    max_wait_time: float = 10.0  # seconds
    enable_compression: bool = True


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    batch_size: Optional[int] = None
    connection_pool_hits: int = 0
    connection_pool_misses: int = 0


class EnhancedConnectionPool:
    """Enhanced connection pool with health checks and metrics"""
    
    def __init__(self, config: ConnectionPoolConfig, pool_type: str = "http"):
        self.config = config
        self.pool_type = pool_type
        self._pool = None
        self._lock = threading.RLock()
        self._metrics = defaultdict(int)
        
        # Prometheus metrics
        self.pool_size_gauge = Gauge(f'asmblr_{pool_type}_pool_size', 'Connection pool size')
        self.pool_active_gauge = Gauge(f'asmblr_{pool_type}_pool_active', 'Active connections')
        self.pool_requests_total = Counter(f'asmblr_{pool_type}_requests_total', 'Total requests')
        self.pool_request_duration = Histogram(f'asmblr_{pool_type}_request_duration_seconds', 'Request duration')
        
    async def initialize(self):
        """Initialize the connection pool"""
        if self.pool_type == "http":
            self._pool = httpx.AsyncClient(
                limits=httpx.Limits(
                    max_connections=self.config.max_connections,
                    max_keepalive_connections=self.config.min_connections
                ),
                timeout=httpx.Timeout(
                    connect=self.config.connection_timeout,
                    read=self.config.read_timeout,
                    write=self.config.write_timeout,
                    pool=self.config.max_idle_time
                )
            )
        elif self.pool_type == "redis":
            self._pool = redis.from_url(
                "redis://redis:6379/0",
                max_connections=self.config.max_connections,
                retry_on_timeout=True,
                socket_connect_timeout=self.config.connection_timeout,
                socket_timeout=self.config.read_timeout,
                health_check_interval=30
            )
        
        logger.info(f"Initialized {self.pool_type} connection pool")
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool"""
        if not self._pool:
            await self.initialize()
        
        start_time = time.time()
        try:
            yield self._pool
            self._metrics['hits'] += 1
            self.pool_requests_total.inc()
        except Exception as e:
            self._metrics['errors'] += 1
            raise
        finally:
            duration = time.time() - start_time
            self.pool_request_duration.observe(duration)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get pool metrics"""
        return dict(self._metrics)
    
    async def close(self):
        """Close the connection pool"""
        if self._pool:
            if self.pool_type == "http":
                await self._pool.aclose()
            elif self.pool_type == "redis":
                await self._pool.close()
            logger.info(f"Closed {self.pool_type} connection pool")


class RequestBatcher:
    """Request batching utility for improved performance"""
    
    def __init__(self, config: BatchConfig):
        self.config = config
        self._pending_requests: deque = deque()
        self._batch_timer = None
        self._lock = asyncio.Lock()
        self._metrics = defaultdict(int)
        
        # Prometheus metrics
        self.batch_size_histogram = Histogram('asmblr_batch_size', 'Batch sizes')
        self.batch_duration_histogram = Histogram('asmblr_batch_duration_seconds', 'Batch processing duration')
        self.batch_requests_total = Counter('asmblr_batch_requests_total', 'Total batched requests')
    
    async def add_request(self, request_data: Dict[str, Any], 
                         process_func: Callable) -> Any:
        """Add a request to the batch"""
        future = asyncio.Future()
        
        async with self._lock:
            self._pending_requests.append({
                'data': request_data,
                'future': future,
                'process_func': process_func,
                'timestamp': time.time()
            })
            
            # Check if we should process the batch
            if (len(self._pending_requests) >= self.config.max_batch_size or
                not self._batch_timer):
                self._batch_timer = asyncio.create_task(self._process_batch())
        
        return await future
    
    async def _process_batch(self):
        """Process a batch of requests"""
        await asyncio.sleep(self.config.batch_timeout)
        
        async with self._lock:
            if not self._pending_requests:
                self._batch_timer = None
                return
            
            # Extract batch
            batch_size = min(len(self._pending_requests), self.config.max_batch_size)
            batch = []
            for _ in range(batch_size):
                batch.append(self._pending_requests.popleft())
            
            self._batch_timer = None if self._pending_requests else self._batch_timer
        
        # Process batch
        start_time = time.time()
        try:
            # Group by process function for efficiency
            process_groups = defaultdict(list)
            for req in batch:
                process_groups[req['process_func']].append(req)
            
            # Process each group
            for process_func, requests in process_groups.items():
                try:
                    # Extract data for batch processing
                    batch_data = [req['data'] for req in requests]
                    
                    # Process batch (this should be implemented by the specific process_func)
                    if asyncio.iscoroutinefunction(process_func):
                        results = await process_func(batch_data)
                    else:
                        results = process_func(batch_data)
                    
                    # Set results for futures
                    for i, req in enumerate(requests):
                        if i < len(results):
                            req['future'].set_result(results[i])
                        else:
                            req['future'].set_exception(IndexError("Result index out of range"))
                    
                    self._metrics['successful_batches'] += 1
                    
                except Exception as e:
                    # Set exception for all requests in this group
                    for req in requests:
                        req['future'].set_exception(e)
                    
                    self._metrics['failed_batches'] += 1
                    logger.error(f"Batch processing failed: {e}")
            
            # Update metrics
            self.batch_size_histogram.observe(batch_size)
            self.batch_requests_total.inc()
            
        except Exception as e:
            # Set exception for all requests
            for req in batch:
                req['future'].set_exception(e)
            
            self._metrics['batch_errors'] += 1
            logger.error(f"Batch processing error: {e}")
        
        finally:
            duration = time.time() - start_time
            self.batch_duration_histogram.observe(duration)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get batcher metrics"""
        return dict(self._metrics)


class PerformanceOptimizer:
    """Main performance optimization coordinator"""
    
    def __init__(self):
        self.connection_pools: Dict[str, EnhancedConnectionPool] = {}
        self.request_batchers: Dict[str, RequestBatcher] = {}
        self._executor = ThreadPoolExecutor(max_workers=10)
        self._metrics: List[PerformanceMetrics] = []
        self._lock = threading.RLock()
        
        # Default configurations
        self.http_pool_config = ConnectionPoolConfig(max_connections=50, min_connections=5)
        self.redis_pool_config = ConnectionPoolConfig(max_connections=20, min_connections=2)
        self.batch_config = BatchConfig(max_batch_size=50, batch_timeout=2.0)
        
        # Prometheus metrics
        self.optimization_operations_total = Counter('asmblr_optimization_operations_total', 'Total optimization operations', ['operation_type'])
        self.optimization_duration = Histogram('asmblr_optimization_duration_seconds', 'Optimization operation duration', ['operation_type'])
    
    async def initialize(self):
        """Initialize all performance optimization components"""
        # Initialize connection pools
        self.connection_pools['http'] = EnhancedConnectionPool(self.http_pool_config, "http")
        self.connection_pools['redis'] = EnhancedConnectionPool(self.redis_pool_config, "redis")
        
        await self.connection_pools['http'].initialize()
        await self.connection_pools['redis'].initialize()
        
        # Initialize request batchers
        self.request_batchers['default'] = RequestBatcher(self.batch_config)
        
        logger.info("Performance optimizer initialized")
    
    @asynccontextmanager
    async def http_client(self):
        """Get HTTP client from pool"""
        async with self.connection_pools['http'].get_connection() as client:
            yield client
    
    @asynccontextmanager
    async def redis_client(self):
        """Get Redis client from pool"""
        async with self.connection_pools['redis'].get_connection() as client:
            yield client
    
    async def batch_request(self, request_data: Dict[str, Any], 
                          process_func: Callable, 
                          batcher_name: str = "default") -> Any:
        """Submit a request for batch processing"""
        if batcher_name not in self.request_batchers:
            self.request_batchers[batcher_name] = RequestBatcher(self.batch_config)
        
        return await self.request_batchers[batcher_name].add_request(request_data, process_func)
    
    @contextmanager
    def measure_performance(self, operation_name: str):
        """Context manager for measuring performance"""
        start_time = time.time()
        metrics = PerformanceMetrics(operation_name=operation_name, start_time=start_time)
        
        try:
            yield metrics
            metrics.success = True
        except Exception as e:
            metrics.success = False
            metrics.error_message = str(e)
            raise
        finally:
            metrics.end_time = time.time()
            metrics.duration = metrics.end_time - metrics.start_time
            
            with self._lock:
                self._metrics.append(metrics)
            
            # Update Prometheus metrics
            self.optimization_operations_total.labels(operation_type=operation_name).inc()
            self.optimization_duration.labels(operation_type=operation_name).observe(metrics.duration)
    
    async def execute_parallel(self, tasks: List[Callable], max_concurrency: int = 10) -> List[Any]:
        """Execute tasks in parallel with concurrency control"""
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def limited_execute(task):
            async with semaphore:
                if asyncio.iscoroutinefunction(task):
                    return await task()
                else:
                    # Run in thread pool for sync functions
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(self._executor, task)
        
        return await asyncio.gather(*[limited_execute(task) for task in tasks])
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        with self._lock:
            if not self._metrics:
                return {"message": "No performance data available"}
            
            # Calculate statistics
            total_operations = len(self._metrics)
            successful_operations = sum(1 for m in self._metrics if m.success)
            failed_operations = total_operations - successful_operations
            
            # Duration statistics
            durations = [m.duration for m in self._metrics if m.duration is not None]
            avg_duration = sum(durations) / len(durations) if durations else 0
            max_duration = max(durations) if durations else 0
            min_duration = min(durations) if durations else 0
            
            # Operations by type
            operations_by_type = defaultdict(list)
            for metric in self._metrics:
                operations_by_type[metric.operation_name].append(metric)
            
            # Pool metrics
            pool_metrics = {}
            for name, pool in self.connection_pools.items():
                pool_metrics[name] = pool.get_metrics()
            
            # Batcher metrics
            batcher_metrics = {}
            for name, batcher in self.request_batchers.items():
                batcher_metrics[name] = batcher.get_metrics()
            
            return {
                "summary": {
                    "total_operations": total_operations,
                    "successful_operations": successful_operations,
                    "failed_operations": failed_operations,
                    "success_rate": successful_operations / total_operations if total_operations > 0 else 0,
                    "avg_duration": round(avg_duration, 3),
                    "max_duration": round(max_duration, 3),
                    "min_duration": round(min_duration, 3)
                },
                "operations_by_type": {
                    name: {
                        "count": len(metrics),
                        "success_rate": sum(1 for m in metrics if m.success) / len(metrics),
                        "avg_duration": round(sum(m.duration or [0] for m in metrics) / len(metrics), 3)
                    }
                    for name, metrics in operations_by_type.items()
                },
                "connection_pools": pool_metrics,
                "request_batchers": batcher_metrics
            }
    
    async def cleanup(self):
        """Cleanup resources"""
        # Close connection pools
        for pool in self.connection_pools.values():
            await pool.close()
        
        # Shutdown executor
        self._executor.shutdown(wait=True)
        
        logger.info("Performance optimizer cleanup completed")


# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()
