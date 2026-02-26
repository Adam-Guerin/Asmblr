"""
Tests for Async Task Processing
Validates background task management, queuing, and execution
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch
from pathlib import Path

from app.core.async_tasks import (
    AsyncTaskManager, AsyncTask, TaskStatus, TaskPriority,
    background_task, ProgressTracker
)


class TestAsyncTask:
    """Test suite for AsyncTask dataclass"""
    
    def test_task_creation(self):
        """Test AsyncTask creation and properties"""
        task = AsyncTask(
            id="test-task-1",
            name="Test Task",
            func=lambda: "test result",
            priority=TaskPriority.HIGH,
            timeout=300
        )
        
        assert task.id == "test-task-1"
        assert task.name == "Test Task"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.HIGH
        assert task.timeout == 300
        assert task.progress == 0.0
        assert task.result is None
        assert task.error is None
    
    def test_task_to_dict(self):
        """Test AsyncTask serialization"""
        task = AsyncTask(
            id="test-task-2",
            name="Test Task 2",
            func=lambda: "test result",
            priority=TaskPriority.NORMAL
        )
        
        task_dict = task.to_dict()
        
        assert task_dict["id"] == "test-task-2"
        assert task_dict["name"] == "Test Task 2"
        assert task_dict["status"] == TaskStatus.PENDING.value
        assert task_dict["priority"] == TaskPriority.NORMAL.value
        assert "timestamp" in task_dict


class TestAsyncTaskManager:
    """Test suite for AsyncTaskManager"""
    
    @pytest.fixture
    async def task_manager(self):
        """Create task manager for testing"""
        with patch('app.core.async_tasks.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            manager = AsyncTaskManager()
            manager._redis_client = mock_client
            return manager
    
    @pytest.mark.asyncio
    async def test_submit_task(self, task_manager):
        """Test task submission"""
        async def test_function(x, y):
            await asyncio.sleep(0.1)
            return x + y
        
        task_id = await task_manager.submit_task(
            name="Test Addition",
            func=test_function,
            args=(2, 3),
            priority=TaskPriority.HIGH
        )
        
        assert task_id is not None
        assert len(task_id) == 36  # UUID length
        
        # Verify task was stored in Redis
        task_manager._redis_client.setex.assert_called_once()
        
        # Verify task was queued
        assert not task_manager._task_queue.empty()
    
    @pytest.mark.asyncio
    async def test_get_task_status(self, task_manager):
        """Test getting task status"""
        task_id = "test-task-status"
        
        # Mock Redis response
        mock_task_data = {
            "id": task_id,
            "name": "Test Task",
            "status": TaskStatus.RUNNING.value,
            "progress": 50.0,
            "timestamp": time.time()
        }
        
        task_manager._redis_client.get.return_value = json.dumps(mock_task_data)
        
        status = await task_manager.get_task_status(task_id)
        
        assert status is not None
        assert status["id"] == task_id
        assert status["status"] == TaskStatus.RUNNING.value
        assert status["progress"] == 50.0
    
    @pytest.mark.asyncio
    async def test_cancel_task(self, task_manager):
        """Test task cancellation"""
        task_id = "test-task-cancel"
        
        # Mock task in running tasks
        mock_task = asyncio.create_task(asyncio.sleep(10))
        task_manager._running_tasks[task_id] = mock_task
        
        result = await task_manager.cancel_task(task_id)
        
        assert result is True
        assert task_id not in task_manager._running_tasks
        assert mock_task.cancelled()
        
        # Verify Redis was updated
        task_manager._redis_client.setex.assert_called()
    
    @pytest.mark.asyncio
    async def test_execute_task_success(self, task_manager):
        """Test successful task execution"""
        async def successful_task():
            await asyncio.sleep(0.1)
            return "success"
        
        task = AsyncTask(
            id="success-task",
            name="Success Task",
            func=successful_task,
            priority=TaskPriority.NORMAL
        )
        
        await task_manager._execute_task(task)
        
        assert task.status == TaskStatus.COMPLETED
        assert task.result == "success"
        assert task.progress == 100.0
        assert task.error is None
    
    @pytest.mark.asyncio
    async def test_execute_task_timeout(self, task_manager):
        """Test task execution timeout"""
        async def timeout_task():
            await asyncio.sleep(10)  # Longer than timeout
            return "should not reach"
        
        task = AsyncTask(
            id="timeout-task",
            name="Timeout Task",
            func=timeout_task,
            priority=TaskPriority.NORMAL,
            timeout=0.1  # Very short timeout
        )
        
        await task_manager._execute_task(task)
        
        assert task.status == TaskStatus.FAILED
        assert "timed out" in task.error.lower()
    
    @pytest.mark.asyncio
    async def test_execute_task_exception(self, task_manager):
        """Test task execution with exception"""
        async def failing_task():
            await asyncio.sleep(0.1)
            raise ValueError("Test error")
        
        task = AsyncTask(
            id="failing-task",
            name="Failing Task",
            func=failing_task,
            priority=TaskPriority.NORMAL
        )
        
        await task_manager._execute_task(task)
        
        assert task.status == TaskStatus.FAILED
        assert "Test error" in task.error
    
    @pytest.mark.asyncio
    async def test_worker_process(self, task_manager):
        """Test worker processing tasks from queue"""
        processed_tasks = []
        
        async def test_task(task_id):
            processed_tasks.append(task_id)
            return f"processed {task_id}"
        
        # Submit tasks
        task_ids = []
        for i in range(3):
            task_id = await task_manager.submit_task(
                name=f"Test Task {i}",
                func=test_task,
                args=(f"task-{i}",),
                priority=TaskPriority.NORMAL
            )
            task_ids.append(task_id)
        
        # Start worker briefly
        worker_task = asyncio.create_task(task_manager._worker())
        
        # Let worker process tasks
        await asyncio.sleep(0.2)
        
        # Stop worker
        task_manager._shutdown = True
        worker_task.cancel()
        
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
        
        # Verify tasks were processed
        assert len(processed_tasks) > 0
    
    @pytest.mark.asyncio
    async def test_queue_stats(self, task_manager):
        """Test queue statistics"""
        # Mock Redis data
        mock_tasks = [
            {
                "id": "task-1",
                "status": TaskStatus.COMPLETED.value,
                "timestamp": time.time()
            },
            {
                "id": "task-2",
                "status": TaskStatus.RUNNING.value,
                "timestamp": time.time()
            },
            {
                "id": "task-3",
                "status": TaskStatus.FAILED.value,
                "timestamp": time.time()
            }
        ]
        
        task_manager._redis_client.keys.return_value = ["task:task-1", "task:task-2", "task:task-3"]
        task_manager._redis_client.get.side_effect = [json.dumps(task) for task in mock_tasks]
        
        stats = await task_manager.get_queue_stats()
        
        assert "total_tasks" in stats
        assert "completed" in stats
        assert "running" in stats
        assert "failed" in stats
        assert "queue_size" in stats


class TestBackgroundTaskDecorator:
    """Test suite for background task decorator"""
    
    @pytest.mark.asyncio
    async def test_background_task_decorator(self):
        """Test background task decorator"""
        with patch('app.core.async_tasks.task_manager') as mock_manager:
            mock_manager.submit_task = AsyncMock(return_value="task-id-123")
            
            @background_task(name="Test Background Task", priority=TaskPriority.HIGH)
            async def test_function(x, y):
                return x + y
            
            result = await test_function(2, 3)
            
            assert result == "task-id-123"
            mock_manager.submit_task.assert_called_once_with(
                "Test Background Task",
                test_function,
                2, 3,
                priority=TaskPriority.HIGH,
                timeout=None,
                max_retries=3
            )


class TestProgressTracker:
    """Test suite for ProgressTracker"""
    
    @pytest.mark.asyncio
    async def test_progress_tracker(self):
        """Test progress tracking functionality"""
        with patch('app.core.async_tasks.task_manager') as mock_manager:
            task_id = "test-progress-task"
            tracker = ProgressTracker(task_id, total_steps=5)
            
            # Test progress updates
            await tracker.update_progress(2, "Processing step 2")
            
            mock_manager._update_task_status.assert_called_with(
                task_id,
                progress=40.0,  # 2/5 * 100
                metadata={"current_step": 2, "message": "Processing step 2"}
            )
            
            # Test increment
            await tracker.increment("Step 3 completed")
            
            # Should be called with progress 60% (3/5 * 100)
            call_args = mock_manager._update_task_status.call_args
            assert call_args[0][0] == task_id
            assert call_args[0][1]["progress"] == 60.0


class TestTaskManagerIntegration:
    """Integration tests for task manager"""
    
    @pytest.mark.asyncio
    async def test_concurrent_task_execution(self):
        """Test concurrent task execution"""
        with patch('app.core.async_tasks.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            manager = AsyncTaskManager()
            manager._redis_client = mock_client
            manager.max_concurrent_tasks = 3
            
            # Submit multiple tasks
            task_results = []
            
            async def slow_task(task_id, duration=0.1):
                await asyncio.sleep(duration)
                return f"result-{task_id}"
            
            # Submit 5 tasks
            task_ids = []
            for i in range(5):
                task_id = await manager.submit_task(
                    name=f"Slow Task {i}",
                    func=slow_task,
                    args=(i, 0.05),
                    priority=TaskPriority.NORMAL
                )
                task_ids.append(task_id)
            
            # Start workers
            await manager.start_workers()
            
            # Wait for tasks to complete
            await asyncio.sleep(0.3)
            
            # Stop workers
            await manager.stop_workers()
            
            # Verify tasks were processed
            assert len(task_ids) == 5
    
    @pytest.mark.asyncio
    async def test_task_priority_ordering(self):
        """Test that tasks are executed in priority order"""
        with patch('app.core.async_tasks.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            manager = AsyncTaskManager()
            manager._redis_client = mock_client
            
            execution_order = []
            
            async def priority_task(name):
                execution_order.append(name)
                return name
            
            # Submit tasks with different priorities
            await manager.submit_task(
                name="Low Priority",
                func=priority_task,
                args=("Low",),
                priority=TaskPriority.LOW
            )
            
            await manager.submit_task(
                name="High Priority",
                func=priority_task,
                args=("High",),
                priority=TaskPriority.HIGH
            )
            
            await manager.submit_task(
                name="Normal Priority",
                func=priority_task,
                args=("Normal",),
                priority=TaskPriority.NORMAL
            )
            
            # Check queue order (should be prioritized)
            items = []
            while not manager._task_queue.empty():
                items.append(manager._task_queue.get_nowait())
            
            # High priority should be first
            assert items[0][0] == TaskPriority.HIGH.value
            assert items[0][1].name == "High Priority"
            
            # Normal priority second
            assert items[1][0] == TaskPriority.NORMAL.value
            assert items[1][1].name == "Normal Priority"
            
            # Low priority last
            assert items[2][0] == TaskPriority.LOW.value
            assert items[2][1].name == "Low Priority"
    
    @pytest.mark.asyncio
    async def test_task_retry_mechanism(self):
        """Test task retry mechanism"""
        with patch('app.core.async_tasks.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            manager = AsyncTaskManager()
            manager._redis_client = mock_client
            
            call_count = 0
            
            async def failing_task():
                nonlocal call_count
                call_count += 1
                if call_count < 3:  # Fail first 2 times
                    raise ValueError("Temporary failure")
                return "success after retries"
            
            task = AsyncTask(
                id="retry-task",
                name="Retry Task",
                func=failing_task,
                priority=TaskPriority.NORMAL,
                max_retries=3
            )
            
            await manager._execute_task(task)
            
            # Should succeed after retries
            assert task.status == TaskStatus.COMPLETED
            assert task.result == "success after retries"
            assert task.retry_count == 2  # Failed 2 times, succeeded on 3rd
            assert call_count == 3


@pytest.mark.asyncio
async def test_task_cleanup():
    """Test cleanup of old tasks"""
    with patch('app.core.async_tasks.redis.from_url') as mock_redis:
        mock_client = AsyncMock()
        mock_redis.return_value = mock_client
        
        manager = AsyncTaskManager()
        manager._redis_client = mock_client
        
        # Mock old tasks
        old_timestamp = (time.time() - 25 * 3600) * 1000  # 25 hours ago in ms
        
        mock_tasks = [
            {
                "id": "old-task-1",
                "status": TaskStatus.COMPLETED.value,
                "timestamp": old_timestamp
            },
            {
                "id": "old-task-2",
                "status": TaskStatus.FAILED.value,
                "timestamp": old_timestamp
            }
        ]
        
        mock_client.keys.return_value = ["task:old-task-1", "task:old-task-2"]
        mock_client.get.side_effect = [json.dumps(task) for task in mock_tasks]
        mock_client.delete.return_value = 1
        
        deleted_count = await manager._cleanup_worker()
        
        # Should delete old tasks
        assert deleted_count == 2
        assert mock_client.delete.call_count == 2
