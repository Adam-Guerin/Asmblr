"""
Async Task Processing for Long-Running Operations
Handles MVP generation, media processing, and other intensive tasks in background
"""

import asyncio
import uuid
from typing import Any
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import traceback

from loguru import logger
import redis.asyncio as redis
from app.core.config import get_settings


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class AsyncTask:
    """Background task definition"""
    id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    progress: float = 0.0
    result: Any | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timeout: int | None = None  # Timeout in seconds
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> dict[str, Any]:
        """Convert task to dictionary for storage"""
        return {
            "id": self.id,
            "name": self.name,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
            "result": str(self.result) if self.result else None,
            "error": self.error,
            "metadata": self.metadata,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries
        }


class AsyncTaskManager:
    """Manages asynchronous background tasks"""
    
    def __init__(self):
        settings = get_settings()
        self.redis_url = settings.redis_url
        self.max_concurrent_tasks = 5
        self.task_timeout = 3600  # 1 hour default
        self.cleanup_interval = 300  # 5 minutes
        self._running_tasks: dict[str, asyncio.Task] = {}
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._redis_client: redis.Redis | None = None
        self._worker_tasks: list[asyncio.Task] = []
        self._shutdown = False
        
    async def _get_redis_client(self) -> redis.Redis:
        """Get or create Redis client"""
        if self._redis_client is None:
            self._redis_client = redis.from_url(self.redis_url)
        return self._redis_client
    
    async def submit_task(
        self,
        name: str,
        func: Callable,
        *args,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: int | None = None,
        max_retries: int = 3,
        metadata: dict[str, Any] | None = None,
        **kwargs
    ) -> str:
        """Submit a new background task"""
        task_id = str(uuid.uuid4())
        
        task = AsyncTask(
            id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timeout=timeout or self.task_timeout,
            max_retries=max_retries,
            metadata=metadata or {}
        )
        
        # Store task in Redis
        await self._store_task(task)
        
        # Add to queue based on priority
        await self._task_queue.put((priority.value, task))
        
        logger.info(f"Submitted task: {name} (ID: {task_id})")
        return task_id
    
    async def _store_task(self, task: AsyncTask) -> None:
        """Store task in Redis"""
        try:
            redis_client = await self._get_redis_client()
            await redis_client.setex(
                f"task:{task.id}",
                86400,  # 24 hours TTL
                json.dumps(task.to_dict())
            )
        except Exception as e:
            logger.warning(f"Failed to store task {task.id}: {e}")
    
    async def _update_task_status(self, task_id: str, **updates) -> None:
        """Update task status in Redis"""
        try:
            redis_client = await self._get_redis_client()
            task_data = await redis_client.get(f"task:{task_id}")
            
            if task_data:
                task_dict = json.loads(task_data)
                task_dict.update(updates)
                
                await redis_client.setex(
                    f"task:{task_id}",
                    86400,
                    json.dumps(task_dict)
                )
        except Exception as e:
            logger.warning(f"Failed to update task {task_id}: {e}")
    
    async def get_task_status(self, task_id: str) -> dict[str, Any] | None:
        """Get task status"""
        try:
            redis_client = await self._get_redis_client()
            task_data = await redis_client.get(f"task:{task_id}")
            
            if task_data:
                return json.loads(task_data)
            return None
        except Exception as e:
            logger.warning(f"Failed to get task {task_id}: {e}")
            return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task"""
        try:
            # Update status
            await self._update_task_status(
                task_id,
                status=TaskStatus.CANCELLED.value,
                completed_at=datetime.now().isoformat()
            )
            
            # Cancel if running
            if task_id in self._running_tasks:
                self._running_tasks[task_id].cancel()
                del self._running_tasks[task_id]
                logger.info(f"Cancelled task: {task_id}")
                return True
            
            return False
        except Exception as e:
            logger.warning(f"Failed to cancel task {task_id}: {e}")
            return False
    
    async def _execute_task(self, task: AsyncTask) -> None:
        """Execute a single task"""
        task_id = task.id
        
        try:
            # Update status to running
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            await self._update_task_status(
                task_id,
                status=TaskStatus.RUNNING.value,
                started_at=task.started_at.isoformat()
            )
            
            logger.info(f"Starting task execution: {task.name} (ID: {task_id})")
            
            # Execute with timeout
            if asyncio.iscoroutinefunction(task.func):
                result = await asyncio.wait_for(
                    task.func(*task.args, **task.kwargs),
                    timeout=task.timeout
                )
            else:
                # Run sync function in executor
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, task.func, *task.args, **task.kwargs
                    ),
                    timeout=task.timeout
                )
            
            # Update status to completed
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            task.progress = 100.0
            
            await self._update_task_status(
                task_id,
                status=TaskStatus.COMPLETED.value,
                completed_at=task.completed_at.isoformat(),
                progress=100.0,
                result=str(result) if result else None
            )
            
            logger.info(f"Task completed: {task.name} (ID: {task_id})")
            
        except TimeoutError:
            error_msg = f"Task timed out after {task.timeout}s"
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = error_msg
            
            await self._update_task_status(
                task_id,
                status=TaskStatus.FAILED.value,
                completed_at=task.completed_at.isoformat(),
                error=error_msg
            )
            
            logger.error(f"Task timeout: {task.name} (ID: {task_id})")
            
        except Exception as e:
            error_msg = f"Task failed: {str(e)}\n{traceback.format_exc()}"
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = error_msg
            
            await self._update_task_status(
                task_id,
                status=TaskStatus.FAILED.value,
                completed_at=task.completed_at.isoformat(),
                error=error_msg
            )
            
            logger.error(f"Task failed: {task.name} (ID: {task_id}) - {e}")
            
        finally:
            # Remove from running tasks
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]
    
    async def _worker(self) -> None:
        """Worker process that executes tasks from queue"""
        while not self._shutdown:
            try:
                # Get task from queue
                priority_task = await asyncio.wait_for(
                    self._task_queue.get(),
                    timeout=1.0
                )
                
                priority, task = priority_task
                
                # Check if we can run more tasks
                if len(self._running_tasks) >= self.max_concurrent_tasks:
                    # Put it back and wait
                    await self._task_queue.put(priority_task)
                    await asyncio.sleep(0.1)
                    continue
                
                # Execute task
                execution_task = asyncio.create_task(self._execute_task(task))
                self._running_tasks[task.id] = execution_task
                
            except TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(1.0)
    
    async def start_workers(self) -> None:
        """Start worker processes"""
        logger.info(f"Starting {self.max_concurrent_tasks} task workers")
        
        for i in range(self.max_concurrent_tasks):
            worker_task = asyncio.create_task(self._worker())
            self._worker_tasks.append(worker_task)
        
        # Start cleanup task
        cleanup_task = asyncio.create_task(self._cleanup_worker())
        self._worker_tasks.append(cleanup_task)
    
    async def stop_workers(self) -> None:
        """Stop all workers"""
        logger.info("Stopping task workers...")
        self._shutdown = True
        
        # Cancel all running tasks
        for task_id, task in self._running_tasks.items():
            task.cancel()
            logger.info(f"Cancelled running task: {task_id}")
        
        # Wait for workers to finish
        for worker_task in self._worker_tasks:
            try:
                await worker_task
            except asyncio.CancelledError:
                pass
        
        logger.info("All workers stopped")
    
    async def _cleanup_worker(self) -> None:
        """Cleanup old completed tasks"""
        while not self._shutdown:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                redis_client = await self._get_redis_client()
                pattern = "task:*"
                keys = await redis_client.keys(pattern)
                
                current_time = datetime.now()
                cutoff_time = current_time - timedelta(hours=24)
                
                deleted_count = 0
                for key in keys:
                    try:
                        task_data = await redis_client.get(key)
                        if task_data:
                            task_dict = json.loads(task_data)
                            completed_at = task_dict.get("completed_at")
                            
                            if completed_at:
                                completed_time = datetime.fromisoformat(completed_at)
                                if completed_time < cutoff_time:
                                    await redis_client.delete(key)
                                    deleted_count += 1
                    except Exception:
                        continue
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old tasks")
                    
            except Exception as e:
                logger.warning(f"Cleanup error: {e}")
    
    async def get_queue_stats(self) -> dict[str, Any]:
        """Get queue statistics"""
        try:
            redis_client = await self._get_redis_client()
            pattern = "task:*"
            keys = await redis_client.keys(pattern)
            
            stats = {
                "total_tasks": len(keys),
                "pending": 0,
                "running": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0,
                "running_count": len(self._running_tasks),
                "queue_size": self._task_queue.qsize()
            }
            
            for key in keys:
                try:
                    task_data = await redis_client.get(key)
                    if task_data:
                        task_dict = json.loads(task_data)
                        status = task_dict.get("status", "unknown")
                        stats[status] = stats.get(status, 0) + 1
                except Exception:
                    continue
            
            return stats
            
        except Exception as e:
            logger.warning(f"Failed to get queue stats: {e}")
            return {"error": str(e)}


# Global task manager instance
task_manager = AsyncTaskManager()


# Decorator for async task execution
def background_task(
    name: str,
    priority: TaskPriority = TaskPriority.NORMAL,
    timeout: int | None = None,
    max_retries: int = 3
):
    """Decorator to run function as background task"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            return await task_manager.submit_task(
                name=name,
                func=func,
                *args,
                priority=priority,
                timeout=timeout,
                max_retries=max_retries,
                **kwargs
            )
        return wrapper
    return decorator


# Progress tracking helper
class ProgressTracker:
    """Helper for tracking task progress"""
    
    def __init__(self, task_id: str, total_steps: int):
        self.task_id = task_id
        self.total_steps = total_steps
        self.current_step = 0
    
    async def update_progress(self, step: int, message: str = "") -> None:
        """Update task progress"""
        self.current_step = step
        progress = (step / self.total_steps) * 100
        
        await task_manager._update_task_status(
            self.task_id,
            progress=progress,
            metadata={"current_step": step, "message": message}
        )
    
    async def increment(self, message: str = "") -> None:
        """Increment progress by 1"""
        await self.update_progress(self.current_step + 1, message)
