"""
Intelligent Task Scheduler for Asmblr
AI-powered task scheduling with adaptive algorithms and optimization
"""

import asyncio
import time
import json
import numpy as np
from typing import Dict, Any, Optional, List, Union, Callable, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque, Counter
import heapq
import psutil
from loguru import logger
import redis.asyncio as redis

class SchedulingStrategy(Enum):
    """Scheduling strategies"""
    FIFO = "fifo"
    PRIORITY = "priority"
    SHORTEST_JOB_FIRST = "shortest_job_first"
    LONGEST_JOB_FIRST = "longest_job_first"
    ROUND_ROBIN = "round_robin"
    ADAPTIVE = "adaptive"
    ML_BASED = "ml_based"
    DEADLINE_AWARE = "deadline_aware"
    RESOURCE_AWARE = "resource_aware"

class TaskState(Enum):
    """Task states"""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"

@dataclass
class SchedulingTask:
    """Enhanced task for intelligent scheduling"""
    id: str
    name: str
    priority: int  # 1-10, lower is higher priority
    estimated_duration: float
    deadline: Optional[datetime] = None
    resource_requirements: Dict[str, float] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Scheduling metadata
    created_at: datetime = field(default_factory=datetime.now)
    submitted_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    state: TaskState = TaskState.PENDING
    
    # Performance metrics
    actual_duration: float = 0.0
    wait_time: float = 0.0
    turnaround_time: float = 0.0
    slack_time: float = 0.0
    
    # ML features
    features: Dict[str, float] = field(default_factory=dict)
    predicted_success: float = 0.0
    predicted_duration: float = 0.0
    
    def __lt__(self, other):
        """Comparison for heap queue"""
        return self.priority < other.priority
    
    @property
    def is_ready(self) -> bool:
        """Check if task is ready to run"""
        return self.state == TaskState.READY
    
    @property
    def is_running(self) -> bool:
        """Check if task is running"""
        return self.state == TaskState.RUNNING
    
    @property
    def is_completed(self) -> bool:
        """Check if task is completed"""
        return self.state == TaskState.COMPLETED
    
    @property
    def urgency_score(self) -> float:
        """Calculate urgency score based on deadline"""
        if not self.deadline:
            return 0.0
        
        time_to_deadline = (self.deadline - datetime.now()).total_seconds()
        if time_to_deadline <= 0:
            return 1.0
        
        # Normalize urgency (0-1)
        urgency = 1.0 - min(time_to_deadline / 3600.0, 1.0)  # 1 hour window
        return urgency
    
    @property
    def slack_time(self) -> float:
        """Calculate slack time (deadline - estimated duration)"""
        if not self.deadline:
            return float('inf')
        
        time_to_deadline = (self.deadline - datetime.now()).total_seconds()
        return time_to_deadline - self.estimated_duration

@dataclass
class SchedulingMetrics:
    """Scheduling performance metrics"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    avg_wait_time: float = 0.0
    avg_turnaround_time: float = 0.0
    avg_slack_time: float = 0.0
    cpu_utilization: float = 0.0
    memory_utilization: float = 0.0
    throughput: float = 0.0
    deadline_misses: int = 0
    prediction_accuracy: float = 0.0
    scheduling_efficiency: float = 0.0

class IntelligentTaskScheduler:
    """AI-powered intelligent task scheduler"""
    
    def __init__(self, max_concurrent_tasks: int = 10):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.scheduling_strategy = SchedulingStrategy.ADAPTIVE
        
        # Task management
        self.tasks = {}
        self.ready_queue = []
        self.running_tasks = {}
        self.completed_tasks = {}
        self.dependency_graph = defaultdict(set)
        
        # Scheduling components
        self.ml_predictor = MLPredictor()
        self.resource_monitor = ResourceMonitor()
        self.performance_analyzer = PerformanceAnalyzer()
        
        # Adaptive parameters
        self.adaptive_window = 100
        self.learning_rate = 0.01
        self.strategy_weights = {strategy: 1.0 for strategy in SchedulingStrategy}
        
        # Performance tracking
        self.metrics = SchedulingMetrics()
        self.performance_history = deque(maxlen=1000)
        self.strategy_performance = defaultdict(list)
        
        # Redis for distributed coordination
        self.redis_client = None
        self.redis_enabled = False
        
        # Background tasks
        self.scheduler_task = None
        self.optimizer_task = None
        self.monitor_task = None
        
    async def initialize(self):
        """Initialize the intelligent scheduler"""
        try:
            # Initialize Redis connection
            try:
                self.redis_client = redis.from_url(
                    "redis://localhost:6379/5",
                    max_connections=20
                )
                await self.redis_client.ping()
                self.redis_enabled = True
                logger.info("Redis connection established for task scheduler")
            except Exception as e:
                logger.warning(f"Redis not available, using local scheduler: {e}")
            
            # Initialize components
            await self.ml_predictor.initialize()
            await self.resource_monitor.initialize()
            await self.performance_analyzer.initialize()
            
            # Start background tasks
            await self.start_background_tasks()
            
            logger.info(f"Intelligent task scheduler initialized with max concurrency: {self.max_concurrent_tasks}")
            
        except Exception as e:
            logger.error(f"Failed to initialize task scheduler: {e}")
            raise
    
    async def submit_task(
        self,
        name: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        priority: int = 5,
        estimated_duration: Optional[float] = None,
        deadline: Optional[datetime] = None,
        resource_requirements: Dict[str, float] = None,
        dependencies: List[str] = None,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Submit a task to the intelligent scheduler"""
        try:
            task_id = str(uuid.uuid4())
            
            # Create task
            task = SchedulingTask(
                id=task_id,
                name=name,
                priority=priority,
                estimated_duration=estimated_duration or 1.0,
                deadline=deadline,
                resource_requirements=resource_requirements or {},
                dependencies=dependencies or [],
                tags=tags or [],
                metadata=metadata or {},
                submitted_at=datetime.now()
            )
            
            # Store function for execution
            task.metadata['func'] = func
            task.metadata['args'] = args
            task.metadata['kwargs'] = kwargs or {}
            
            # AI-powered task analysis
            await self._analyze_task(task)
            
            # Add to task management
            self.tasks[task_id] = task
            
            # Update dependency graph
            for dep_id in task.dependencies:
                self.dependency_graph[dep_id].add(task_id)
            
            # Check if task is ready
            if self._check_dependencies(task):
                task.state = TaskState.READY
                await self._add_to_ready_queue(task)
            else:
                task.state = TaskState.BLOCKED
            
            # Update metrics
            self.metrics.total_tasks += 1
            
            logger.info(f"Task {task_id} submitted to intelligent scheduler: {name}")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to submit task: {e}")
            raise
    
    async def _analyze_task(self, task: SchedulingTask):
        """AI-powered task analysis"""
        try:
            # Extract features for ML
            func = task.metadata.get('func')
            args = task.metadata.get('args', ())
            kwargs = task.metadata.get('kwargs', {})
            
            # Calculate features
            features = await self._extract_task_features(func, args, kwargs)
            task.features = features
            
            # Predict duration and success
            task.predicted_duration = await self.ml_predictor.predict_duration(features)
            task.predicted_success = await self.ml_predictor.predict_success(features)
            
            # Update estimated duration if better prediction available
            if task.predicted_duration > 0:
                task.estimated_duration = task.predicted_duration
            
            # Estimate resource requirements
            if not task.resource_requirements:
                task.resource_requirements = await self._estimate_resources(features)
            
        except Exception as e:
            logger.error(f"Task analysis error: {e}")
    
    async def _extract_task_features(self, func: Callable, args: tuple, kwargs: dict) -> Dict[str, float]:
        """Extract features from task for ML"""
        features = {}
        
        try:
            # Function features
            if hasattr(func, '__code__'):
                features['arg_count'] = len(func.__code__.co_varnames)
                features['code_size'] = len(func.__code__.co_code)
            
            # Argument features
            features['args_count'] = len(args)
            features['kwargs_count'] = len(kwargs)
            
            # Data size features
            total_data_size = 0
            for arg in args:
                if hasattr(arg, '__len__'):
                    total_data_size += len(arg)
            for value in kwargs.values():
                if hasattr(value, '__len__'):
                    total_data_size += len(value)
            
            features['data_size'] = total_data_size
            features['has_large_data'] = 1.0 if total_data_size > 1000 else 0.0
            
            # Complexity features
            features['complexity_score'] = min(features.get('arg_count', 0) * 0.1 + features.get('data_size', 0) * 0.001, 1.0)
            
            # Time-based features
            features['hour_of_day'] = datetime.now().hour / 24.0
            features['day_of_week'] = datetime.now().weekday() / 7.0
            
        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
            features = {'complexity_score': 0.5}
        
        return features
    
    async def _estimate_resources(self, features: Dict[str, float]) -> Dict[str, float]:
        """Estimate resource requirements based on features"""
        complexity = features.get('complexity_score', 0.5)
        data_size = features.get('data_size', 0)
        
        return {
            'cpu': min(0.1 + complexity * 0.5, 1.0),
            'memory': min(0.1 + data_size * 0.0001 + complexity * 0.3, 1.0),
            'disk': 0.01,
            'network': 0.01
        }
    
    def _check_dependencies(self, task: SchedulingTask) -> bool:
        """Check if task dependencies are satisfied"""
        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks:
                return False
            if self.completed_tasks[dep_id].state != TaskState.COMPLETED:
                return False
        return True
    
    async def _add_to_ready_queue(self, task: SchedulingTask):
        """Add task to ready queue with appropriate priority"""
        if self.scheduling_strategy == SchedulingStrategy.ML_BASED:
            # Use ML prediction for ordering
            task.priority = int((1.0 - task.predicted_success) * 10)
        
        heapq.heappush(self.ready_queue, task)
    
    async def start_background_tasks(self):
        """Start background scheduling tasks"""
        self.scheduler_task = asyncio.create_task(self._scheduling_loop())
        self.optimizer_task = asyncio.create_task(self._optimization_loop())
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Background scheduling tasks started")
    
    async def _scheduling_loop(self):
        """Main scheduling loop"""
        while True:
            try:
                # Get next task to schedule
                task = await self._get_next_task()
                
                if task and len(self.running_tasks) < self.max_concurrent_tasks:
                    # Check resource availability
                    if await self._check_resources(task):
                        # Execute task
                        asyncio.create_task(self._execute_task(task))
                    else:
                        # Not enough resources, wait
                        await asyncio.sleep(0.1)
                else:
                    # No tasks or max concurrency reached
                    await asyncio.sleep(0.1)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduling loop error: {e}")
                await asyncio.sleep(1)
    
    async def _get_next_task(self) -> Optional[SchedulingTask]:
        """Get next task based on scheduling strategy"""
        try:
            if not self.ready_queue:
                return None
            
            if self.scheduling_strategy == SchedulingStrategy.FIFO:
                return heapq.heappop(self.ready_queue)
            
            elif self.scheduling_strategy == SchedulingStrategy.PRIORITY:
                return heapq.heappop(self.ready_queue)
            
            elif self.scheduling_strategy == SchedulingStrategy.SHORTEST_JOB_FIRST:
                # Sort by estimated duration
                tasks = []
                while self.ready_queue:
                    tasks.append(heapq.heappop(self.ready_queue))
                
                tasks.sort(key=lambda t: t.estimated_duration)
                selected_task = tasks[0]
                
                # Put back other tasks
                for task in tasks[1:]:
                    heapq.heappush(self.ready_queue, task)
                
                return selected_task
            
            elif self.scheduling_strategy == SchedulingStrategy.DEADLINE_AWARE:
                # Sort by urgency
                tasks = []
                while self.ready_queue:
                    tasks.append(heapq.heappop(self.ready_queue))
                
                tasks.sort(key=lambda t: t.urgency_score, reverse=True)
                selected_task = tasks[0]
                
                # Put back other tasks
                for task in tasks[1:]:
                    heapq.heappush(self.ready_queue, task)
                
                return selected_task
            
            elif self.scheduling_strategy == SchedulingStrategy.RESOURCE_AWARE:
                # Select task that fits current resources
                current_resources = await self.resource_monitor.get_current_resources()
                
                tasks = []
                while self.ready_queue:
                    tasks.append(heapq.heappop(self.ready_queue))
                
                # Find task that fits
                selected_task = None
                for task in tasks:
                    if self._task_fits_resources(task, current_resources):
                        selected_task = task
                        break
                
                # Put back other tasks
                for task in tasks:
                    if task != selected_task:
                        heapq.heappush(self.ready_queue, task)
                
                return selected_task
            
            elif self.scheduling_strategy == SchedulingStrategy.ADAPTIVE:
                # Use adaptive strategy selection
                return await self._adaptive_selection()
            
            elif self.scheduling_strategy == SchedulingStrategy.ML_BASED:
                # Use ML-based selection
                return await self._ml_based_selection()
            
            else:
                return heapq.heappop(self.ready_queue)
            
        except Exception as e:
            logger.error(f"Task selection error: {e}")
            return None
    
    def _task_fits_resources(self, task: SchedulingTask, resources: Dict[str, float]) -> bool:
        """Check if task fits in available resources"""
        for resource, required in task.resource_requirements.items():
            available = resources.get(resource, 1.0)
            if required > available:
                return False
        return True
    
    async def _adaptive_selection(self) -> Optional[SchedulingTask]:
        """Adaptive strategy selection"""
        try:
            # Analyze current system state
            system_state = await self.resource_monitor.get_current_resources()
            queue_size = len(self.ready_queue)
            
            # Select best strategy for current conditions
            if queue_size > 50:
                # High load - use shortest job first
                self.scheduling_strategy = SchedulingStrategy.SHORTEST_JOB_FIRST
            elif system_state.get('cpu', 0) > 0.8:
                # High CPU usage - use resource aware
                self.scheduling_strategy = SchedulingStrategy.RESOURCE_AWARE
            elif any(task.deadline for task in self.ready_queue):
                # Has deadlines - use deadline aware
                self.scheduling_strategy = SchedulingStrategy.DEADLINE_AWARE
            else:
                # Normal conditions - use priority
                self.scheduling_strategy = SchedulingStrategy.PRIORITY
            
            # Get task using selected strategy
            return await self._get_next_task()
            
        except Exception as e:
            logger.error(f"Adaptive selection error: {e}")
            return heapq.heappop(self.ready_queue) if self.ready_queue else None
    
    async def _ml_based_selection(self) -> Optional[SchedulingTask]:
        """ML-based task selection"""
        try:
            if not self.ready_queue:
                return None
            
            # Get all ready tasks
            tasks = []
            while self.ready_queue:
                tasks.append(heapq.heappop(self.ready_queue))
            
            # Score each task using ML model
            task_scores = []
            for task in tasks:
                score = await self.ml_predictor.score_task(task, await self.resource_monitor.get_current_resources())
                task_scores.append((task, score))
            
            # Select highest scoring task
            task_scores.sort(key=lambda x: x[1], reverse=True)
            selected_task = task_scores[0][0]
            
            # Put back other tasks
            for task, score in task_scores[1:]:
                heapq.heappush(self.ready_queue, task)
            
            return selected_task
            
        except Exception as e:
            logger.error(f"ML-based selection error: {e}")
            return heapq.heappop(self.ready_queue) if self.ready_queue else None
    
    async def _check_resources(self, task: SchedulingTask) -> bool:
        """Check if resources are available for task"""
        try:
            current_resources = await self.resource_monitor.get_current_resources()
            return self._task_fits_resources(task, current_resources)
        except Exception as e:
            logger.error(f"Resource check error: {e}")
            return True
    
    async def _execute_task(self, task: SchedulingTask):
        """Execute a scheduled task"""
        try:
            # Update task state
            task.state = TaskState.RUNNING
            task.started_at = datetime.now()
            task.wait_time = (task.started_at - task.submitted_at).total_seconds()
            self.running_tasks[task.id] = task
            
            # Get function and arguments
            func = task.metadata.get('func')
            args = task.metadata.get('args', ())
            kwargs = task.metadata.get('kwargs', {})
            
            if not func:
                raise ValueError("Task function not found")
            
            # Execute task
            start_time = time.time()
            
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    # Run CPU-bound function in thread pool
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, func, *args, **kwargs)
                
                # Update task
                task.state = TaskState.COMPLETED
                task.completed_at = datetime.now()
                task.actual_duration = time.time() - start_time
                task.turnaround_time = (task.completed_at - task.submitted_at).total_seconds()
                
                # Store result
                task.metadata['result'] = result
                
                # Update metrics
                self.metrics.completed_tasks += 1
                
                # Check deadline
                if task.deadline and task.completed_at > task.deadline:
                    self.metrics.deadline_misses += 1
                
                logger.info(f"Task {task.id} completed in {task.actual_duration:.2f}s")
                
            except Exception as e:
                task.state = TaskState.FAILED
                task.completed_at = datetime.now()
                task.actual_duration = time.time() - start_time
                task.metadata['error'] = str(e)
                
                self.metrics.failed_tasks += 1
                logger.error(f"Task {task.id} failed: {e}")
            
            finally:
                # Remove from running tasks
                if task.id in self.running_tasks:
                    del self.running_tasks[task.id]
                
                # Add to completed tasks
                self.completed_tasks[task.id] = task
                
                # Update metrics
                self._update_metrics(task)
                
                # Check and unblock dependent tasks
                await self._check_dependent_tasks(task)
                
                # Update ML models
                await self.ml_predictor.update_models(task)
            
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            task.state = TaskState.FAILED
            task.completed_at = datetime.now()
    
    async def _check_dependent_tasks(self, completed_task: SchedulingTask):
        """Check and unblock tasks dependent on completed task"""
        try:
            dependent_ids = self.dependency_graph.get(completed_task.id, set())
            
            for dep_id in dependent_ids:
                if dep_id in self.tasks:
                    dep_task = self.tasks[dep_id]
                    
                    if dep_task.state == TaskState.BLOCKED and self._check_dependencies(dep_task):
                        dep_task.state = TaskState.READY
                        await self._add_to_ready_queue(dep_task)
                        logger.info(f"Unblocked dependent task: {dep_id}")
            
        except Exception as e:
            logger.error(f"Dependent task check error: {e}")
    
    def _update_metrics(self, task: SchedulingTask):
        """Update scheduling metrics"""
        try:
            # Update average wait time
            if self.metrics.completed_tasks > 0:
                total_wait_time = sum(
                    t.wait_time for t in self.completed_tasks.values()
                    if t.state == TaskState.COMPLETED
                )
                self.metrics.avg_wait_time = total_wait_time / self.metrics.completed_tasks
            
            # Update average turnaround time
            if self.metrics.completed_tasks > 0:
                total_turnaround = sum(
                    t.turnaround_time for t in self.completed_tasks.values()
                    if t.state == TaskState.COMPLETED
                )
                self.metrics.avg_turnaround_time = total_turnaround / self.metrics.completed_tasks
            
            # Update throughput
            if self.performance_history:
                time_span = (
                    self.performance_history[-1]['timestamp'] -
                    self.performance_history[0]['timestamp']
                ).total_seconds()
                if time_span > 0:
                    self.metrics.throughput = len(self.performance_history) / time_span
            
            # Store performance snapshot
            self.performance_history.append({
                'timestamp': datetime.now(),
                'task_id': task.id,
                'wait_time': task.wait_time,
                'turnaround_time': task.turnaround_time,
                'actual_duration': task.actual_duration,
                'predicted_duration': task.predicted_duration,
                'success': task.state == TaskState.COMPLETED
            })
            
        except Exception as e:
            logger.error(f"Metrics update error: {e}")
    
    async def _optimization_loop(self):
        """Background optimization loop"""
        while True:
            try:
                # Optimize scheduling parameters
                await self._optimize_scheduling()
                
                # Update strategy weights
                await self._update_strategy_weights()
                
                # Adjust concurrency
                await self._adjust_concurrency()
                
                await asyncio.sleep(300)  # Optimize every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Optimization loop error: {e}")
                await asyncio.sleep(300)
    
    async def _optimize_scheduling(self):
        """Optimize scheduling parameters"""
        try:
            # Analyze recent performance
            recent_tasks = list(self.completed_tasks.values())[-self.adaptive_window:]
            
            if len(recent_tasks) < 10:
                return
            
            # Calculate performance metrics for each strategy
            strategy_performance = {}
            
            for strategy in SchedulingStrategy:
                strategy_tasks = [t for t in recent_tasks if t.metadata.get('strategy') == strategy.value]
                
                if strategy_tasks:
                    avg_turnaround = sum(t.turnaround_time for t in strategy_tasks) / len(strategy_tasks)
                    success_rate = sum(1 for t in strategy_tasks if t.state == TaskState.COMPLETED) / len(strategy_tasks)
                    
                    # Combined score (lower turnaround and higher success rate are better)
                    strategy_performance[strategy] = (1.0 / avg_turnaround) * success_rate
            
            # Update strategy weights
            if strategy_performance:
                best_strategy = max(strategy_performance, key=strategy_performance.get)
                logger.info(f"Best performing strategy: {best_strategy.value}")
                
                # Adjust weights
                for strategy in SchedulingStrategy:
                    if strategy == best_strategy:
                        self.strategy_weights[strategy] = min(self.strategy_weights[strategy] * 1.1, 2.0)
                    else:
                        self.strategy_weights[strategy] = max(self.strategy_weights[strategy] * 0.95, 0.1)
            
        except Exception as e:
            logger.error(f"Scheduling optimization error: {e}")
    
    async def _update_strategy_weights(self):
        """Update strategy weights based on performance"""
        try:
            # Normalize weights
            total_weight = sum(self.strategy_weights.values())
            if total_weight > 0:
                for strategy in self.strategy_weights:
                    self.strategy_weights[strategy] /= total_weight
            
        except Exception as e:
            logger.error(f"Strategy weight update error: {e}")
    
    async def _adjust_concurrency(self):
        """Adjust maximum concurrency based on system load"""
        try:
            current_resources = await self.resource_monitor.get_current_resources()
            queue_size = len(self.ready_queue)
            
            cpu_usage = current_resources.get('cpu', 0)
            memory_usage = current_resources.get('memory', 0)
            
            # Adjust concurrency based on load
            if cpu_usage > 0.9 or memory_usage > 0.9:
                # High load - reduce concurrency
                self.max_concurrent_tasks = max(5, self.max_concurrent_tasks - 1)
            elif cpu_usage < 0.5 and memory_usage < 0.5 and queue_size > 20:
                # Low load and queue buildup - increase concurrency
                self.max_concurrent_tasks = min(50, self.max_concurrent_tasks + 1)
            
            logger.debug(f"Adjusted max concurrency to: {self.max_concurrent_tasks}")
            
        except Exception as e:
            logger.error(f"Concurrency adjustment error: {e}")
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                # Update resource monitoring
                await self.resource_monitor.update()
                
                # Update performance metrics
                self.metrics.cpu_utilization = psutil.cpu_percent() / 100.0
                self.metrics.memory_utilization = psutil.virtual_memory().percent / 100.0
                
                # Calculate scheduling efficiency
                await self._calculate_scheduling_efficiency()
                
                await asyncio.sleep(60)  # Monitor every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(60)
    
    async def _calculate_scheduling_efficiency(self):
        """Calculate scheduling efficiency"""
        try:
            if self.metrics.completed_tasks == 0:
                return
            
            # Efficiency = (predicted_duration / actual_duration) * success_rate
            recent_tasks = list(self.completed_tasks.values())[-50:]
            
            if recent_tasks:
                efficiency_sum = 0.0
                for task in recent_tasks:
                    if task.state == TaskState.COMPLETED and task.predicted_duration > 0:
                        task_efficiency = task.predicted_duration / max(task.actual_duration, 0.001)
                        efficiency_sum += min(task_efficiency, 2.0)  # Cap at 2.0
                
                self.metrics.scheduling_efficiency = efficiency_sum / len(recent_tasks)
            
        except Exception as e:
            logger.error(f"Scheduling efficiency calculation error: {e}")
    
    async def get_task_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """Get task result"""
        try:
            start_time = time.time()
            
            while True:
                # Check if task is completed
                if task_id in self.completed_tasks:
                    task = self.completed_tasks[task_id]
                    if task.state == TaskState.COMPLETED:
                        return task.metadata.get('result')
                    elif task.state == TaskState.FAILED:
                        raise Exception(f"Task {task_id} failed: {task.metadata.get('error')}")
                
                # Check timeout
                if timeout and (time.time() - start_time) > timeout:
                    raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")
                
                await asyncio.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Failed to get task result {task_id}: {e}")
            raise
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get scheduler metrics"""
        try:
            # Update prediction accuracy
            self.metrics.prediction_accuracy = await self.ml_predictor.get_accuracy()
            
            return asdict(self.metrics)
            
        except Exception as e:
            logger.error(f"Metrics retrieval error: {e}")
            return asdict(self.metrics)
    
    async def set_strategy(self, strategy: SchedulingStrategy):
        """Set scheduling strategy"""
        self.scheduling_strategy = strategy
        logger.info(f"Scheduling strategy changed to: {strategy.value}")
    
    async def shutdown(self):
        """Shutdown the intelligent scheduler"""
        logger.info("Shutting down intelligent task scheduler...")
        
        # Cancel background tasks
        if self.scheduler_task:
            self.scheduler_task.cancel()
        if self.optimizer_task:
            self.optimizer_task.cancel()
        if self.monitor_task:
            self.monitor_task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*[
            self.scheduler_task,
            self.optimizer_task,
            self.monitor_task
        ], return_exceptions=True)
        
        # Shutdown components
        await self.ml_predictor.shutdown()
        await self.resource_monitor.shutdown()
        await self.performance_analyzer.shutdown()
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Intelligent task scheduler shutdown complete")

# Supporting Classes

class MLPredictor:
    """ML predictor for task scheduling"""
    
    def __init__(self):
        self.duration_model = None
        self.success_model = None
        self.accuracy_history = deque(maxlen=100)
    
    async def initialize(self):
        """Initialize ML models"""
        logger.info("ML predictor initialized")
    
    async def predict_duration(self, features: Dict[str, float]) -> float:
        """Predict task duration"""
        # Simplified duration prediction
        complexity = features.get('complexity_score', 0.5)
        data_size = features.get('data_size', 0)
        
        base_duration = 0.1
        complexity_factor = complexity ** 2
        data_factor = data_size * 0.001
        
        return base_duration + complexity_factor * 2.0 + data_factor
    
    async def predict_success(self, features: Dict[str, float]) -> float:
        """Predict task success probability"""
        # Simplified success prediction
        complexity = features.get('complexity_score', 0.5)
        return max(0.5, 1.0 - complexity * 0.3)
    
    async def score_task(self, task: SchedulingTask, resources: Dict[str, float]) -> float:
        """Score task for selection"""
        # Combined score based on multiple factors
        priority_score = (11 - task.priority) / 10.0  # Higher priority = higher score
        urgency_score = task.urgency_score
        success_score = task.predicted_success
        resource_score = 1.0 - sum(task.resource_requirements.values()) / 4.0  # Lower resource usage = higher score
        
        return (
            priority_score * 0.3 +
            urgency_score * 0.3 +
            success_score * 0.2 +
            resource_score * 0.2
        )
    
    async def get_accuracy(self) -> float:
        """Get prediction accuracy"""
        if self.accuracy_history:
            return sum(self.accuracy_history) / len(self.accuracy_history)
        return 0.0
    
    async def update_models(self, task: SchedulingTask):
        """Update ML models with task results"""
        # Placeholder for model training
        pass
    
    async def shutdown(self):
        """Shutdown ML predictor"""
        logger.info("ML predictor shutdown")

class ResourceMonitor:
    """Resource monitoring for scheduling"""
    
    def __init__(self):
        self.resource_history = deque(maxlen=100)
    
    async def initialize(self):
        """Initialize resource monitor"""
        logger.info("Resource monitor initialized")
    
    async def get_current_resources(self) -> Dict[str, float]:
        """Get current resource availability"""
        try:
            return {
                'cpu': 1.0 - (psutil.cpu_percent() / 100.0),
                'memory': 1.0 - (psutil.virtual_memory().percent / 100.0),
                'disk': 1.0 - (psutil.disk_usage('/').percent / 100.0),
                'network': 0.8  # Placeholder
            }
        except Exception as e:
            logger.error(f"Resource monitoring error: {e}")
            return {}
    
    async def update(self):
        """Update resource monitoring"""
        try:
            current_resources = await self.get_current_resources()
            self.resource_history.append({
                'timestamp': datetime.now(),
                'resources': current_resources
            })
        except Exception as e:
            logger.error(f"Resource update error: {e}")
    
    async def shutdown(self):
        """Shutdown resource monitor"""
        logger.info("Resource monitor shutdown")

class PerformanceAnalyzer:
    """Performance analysis for scheduling"""
    
    def __init__(self):
        self.performance_data = deque(maxlen=1000)
    
    async def initialize(self):
        """Initialize performance analyzer"""
        logger.info("Performance analyzer initialized")
    
    async def analyze_performance(self, tasks: List[SchedulingTask]) -> Dict[str, float]:
        """Analyze task performance"""
        # Placeholder for performance analysis
        return {}
    
    async def shutdown(self):
        """Shutdown performance analyzer"""
        logger.info("Performance analyzer shutdown")

# Global intelligent task scheduler instance
intelligent_scheduler = IntelligentTaskScheduler()
