"""
Enhanced Pipeline Manager with Advanced Features
Improved performance, monitoring, and user experience
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Any
from dataclasses import dataclass
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class PipelineStatus(Enum):
    """Pipeline execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelinePriority(Enum):
    """Pipeline execution priority"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class PipelineMetrics:
    """Pipeline execution metrics"""
    pipeline_id: str
    start_time: datetime
    end_time: datetime | None = None
    duration: float = 0.0
    stages_completed: int = 0
    stages_total: int = 0
    llm_calls: int = 0
    tokens_processed: int = 0
    errors: list[str] = None
    performance_score: float = 0.0
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'pipeline_id': self.pipeline_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'stages_completed': self.stages_completed,
            'stages_total': self.stages_total,
            'llm_calls': self.llm_calls,
            'tokens_processed': self.tokens_processed,
            'errors': self.errors,
            'performance_score': self.performance_score
        }


@dataclass
class PipelineConfig:
    """Enhanced pipeline configuration"""
    max_concurrent_stages: int = 3
    enable_caching: bool = True
    enable_monitoring: bool = True
    enable_auto_retry: bool = True
    max_retries: int = 3
    retry_delay: float = 5.0
    timeout_per_stage: float = 300.0
    priority: PipelinePriority = PipelinePriority.NORMAL
    enable_parallel_execution: bool = True
    resource_limits: dict[str, Any] = None
    
    def __post_init__(self):
        if self.resource_limits is None:
            self.resource_limits = {
                'max_memory_mb': 4096,
                'max_cpu_percent': 80,
                'max_llm_calls_per_minute': 60
            }


class EnhancedPipelineManager:
    """Enhanced pipeline manager with advanced features"""
    
    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()
        self.running_pipelines: dict[str, dict[str, Any]] = {}
        self.pipeline_metrics: dict[str, PipelineMetrics] = {}
        self.stage_queue = asyncio.Queue()
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_stages)
        self.metrics_history: list[PipelineMetrics] = []
        self.performance_cache: dict[str, Any] = {}
        
    async def start_pipeline(self, pipeline_id: str, stages: list[dict[str, Any]], 
                           inputs: dict[str, Any] = None) -> str:
        """Start an enhanced pipeline with advanced features"""
        
        # Initialize pipeline state
        pipeline_state = {
            'id': pipeline_id,
            'status': PipelineStatus.RUNNING,
            'stages': stages,
            'current_stage': 0,
            'inputs': inputs or {},
            'outputs': {},
            'start_time': datetime.utcnow(),
            'config': self.config,
            'retry_count': 0
        }
        
        self.running_pipelines[pipeline_id] = pipeline_state
        
        # Initialize metrics
        metrics = PipelineMetrics(
            pipeline_id=pipeline_id,
            start_time=datetime.utcnow(),
            stages_total=len(stages)
        )
        self.pipeline_metrics[pipeline_id] = metrics
        
        logger.info(f"Starting enhanced pipeline {pipeline_id} with {len(stages)} stages")
        
        try:
            # Execute pipeline with enhanced features
            if self.config.enable_parallel_execution and self._can_run_parallel(stages):
                await self._execute_parallel_stages(pipeline_id, stages, inputs)
            else:
                await self._execute_sequential_stages(pipeline_id, stages, inputs)
            
            # Mark as completed
            pipeline_state['status'] = PipelineStatus.COMPLETED
            pipeline_state['end_time'] = datetime.utcnow()
            metrics.end_time = datetime.utcnow()
            metrics.duration = (metrics.end_time - metrics.start_time).total_seconds()
            
            # Calculate performance score
            metrics.performance_score = self._calculate_performance_score(metrics)
            
            logger.info(f"Pipeline {pipeline_id} completed successfully in {metrics.duration:.2f}s")
            
            return pipeline_id
            
        except Exception as e:
            # Handle failure with retry logic
            if self.config.enable_auto_retry and pipeline_state['retry_count'] < self.config.max_retries:
                logger.warning(f"Pipeline {pipeline_id} failed, retrying... ({pipeline_state['retry_count'] + 1}/{self.config.max_retries})")
                
                pipeline_state['retry_count'] += 1
                pipeline_state['status'] = PipelineStatus.PENDING
                
                # Wait before retry
                await asyncio.sleep(self.config.retry_delay)
                
                # Retry pipeline
                return await self.start_pipeline(pipeline_id, stages, inputs)
            else:
                # Mark as failed
                pipeline_state['status'] = PipelineStatus.FAILED
                pipeline_state['end_time'] = datetime.utcnow()
                metrics.end_time = datetime.utcnow()
                metrics.duration = (metrics.end_time - metrics.start_time).total_seconds()
                metrics.errors.append(str(e))
                
                logger.error(f"Pipeline {pipeline_id} failed after {pipeline_state['retry_count']} retries: {e}")
                raise
    
    async def _execute_sequential_stages(self, pipeline_id: str, stages: list[dict[str, Any]], 
                                       inputs: dict[str, Any]) -> None:
        """Execute stages sequentially with enhanced features"""
        
        pipeline_state = self.running_pipelines[pipeline_id]
        metrics = self.pipeline_metrics[pipeline_id]
        
        for i, stage in enumerate(stages):
            # Check if pipeline is cancelled
            if pipeline_state['status'] == PipelineStatus.CANCELLED:
                break
            
            # Update current stage
            pipeline_state['current_stage'] = i
            
            # Execute stage with timeout and monitoring
            stage_start = time.time()
            
            try:
                # Check cache first if enabled
                stage_key = self._get_stage_cache_key(stage, inputs)
                if self.config.enable_caching and stage_key in self.performance_cache:
                    logger.info(f"Using cached result for stage {i}: {stage.get('name', 'unnamed')}")
                    stage_result = self.performance_cache[stage_key]
                else:
                    # Execute stage with timeout
                    stage_result = await asyncio.wait_for(
                        self._execute_stage(stage, inputs, pipeline_state['outputs']),
                        timeout=self.config.timeout_per_stage
                    )
                    
                    # Cache result if enabled
                    if self.config.enable_caching:
                        self.performance_cache[stage_key] = stage_result
                
                # Update metrics
                stage_duration = time.time() - stage_start
                metrics.stages_completed += 1
                
                if 'llm_calls' in stage_result:
                    metrics.llm_calls += stage_result['llm_calls']
                if 'tokens_processed' in stage_result:
                    metrics.tokens_processed += stage_result['tokens_processed']
                
                # Update outputs
                pipeline_state['outputs'][stage.get('name', f'stage_{i}')] = stage_result
                
                # Log progress
                logger.info(f"Stage {i+1}/{len(stages)} completed in {stage_duration:.2f}s: {stage.get('name', 'unnamed')}")
                
                # Update inputs for next stage
                inputs.update(stage_result.get('outputs', {}))
                
            except TimeoutError:
                error_msg = f"Stage {i} timed out after {self.config.timeout_per_stage}s"
                metrics.errors.append(error_msg)
                raise TimeoutError(error_msg)
            
            except Exception as e:
                error_msg = f"Stage {i} failed: {str(e)}"
                metrics.errors.append(error_msg)
                raise
    
    async def _execute_parallel_stages(self, pipeline_id: str, stages: list[dict[str, Any]], 
                                     inputs: dict[str, Any]) -> None:
        """Execute stages in parallel where possible"""
        
        pipeline_state = self.running_pipelines[pipeline_id]
        metrics = self.pipeline_metrics[pipeline_id]
        
        # Group stages by dependencies
        stage_groups = self._group_stages_by_dependencies(stages)
        
        for group in stage_groups:
            # Execute all stages in this group in parallel
            tasks = []
            
            for stage in group:
                task = asyncio.create_task(
                    self._execute_stage_with_monitoring(pipeline_id, stage, inputs)
                )
                tasks.append(task)
            
            # Wait for all stages in group to complete
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        error_msg = f"Parallel stage failed: {str(result)}"
                        metrics.errors.append(error_msg)
                        raise result
                    else:
                        stage_name = group[i].get('name', f'stage_{i}')
                        pipeline_state['outputs'][stage_name] = result
                        inputs.update(result.get('outputs', {}))
                        metrics.stages_completed += 1
                
            except Exception as e:
                logger.error(f"Parallel stage group failed: {e}")
                raise
    
    async def _execute_stage_with_monitoring(self, pipeline_id: str, stage: dict[str, Any], 
                                           inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute a stage with monitoring and resource limits"""
        
        stage_start = time.time()
        stage_name = stage.get('name', 'unnamed')
        
        # Check resource limits
        if self.config.resource_limits:
            await self._check_resource_limits()
        
        try:
            # Execute stage
            result = await asyncio.wait_for(
                self._execute_stage(stage, inputs, {}),
                timeout=self.config.timeout_per_stage
            )
            
            # Log performance
            stage_duration = time.time() - stage_start
            logger.info(f"Stage {stage_name} completed in {stage_duration:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Stage {stage_name} failed: {e}")
            raise
    
    async def _execute_stage(self, stage: dict[str, Any], inputs: dict[str, Any], 
                           context: dict[str, Any]) -> dict[str, Any]:
        """Execute a single stage"""
        
        stage_type = stage.get('type', 'default')
        stage_name = stage.get('name', 'unnamed')
        
        # Route to appropriate stage handler
        if stage_type == 'llm_call':
            return await self._execute_llm_stage(stage, inputs)
        elif stage_type == 'data_processing':
            return await self._execute_data_stage(stage, inputs)
        elif stage_type == 'api_call':
            return await self._execute_api_stage(stage, inputs)
        elif stage_type == 'file_operation':
            return await self._execute_file_stage(stage, inputs)
        else:
            return await self._execute_default_stage(stage, inputs)
    
    async def _execute_llm_stage(self, stage: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute LLM stage with monitoring"""
        
        from app.core.llm import LLMClient
        
        llm_client = LLMClient()
        prompt = stage.get('prompt', '')
        model = stage.get('model', 'llama3.1:8b')
        
        # Format prompt with inputs
        try:
            formatted_prompt = prompt.format(**inputs)
        except KeyError as e:
            raise ValueError(f"Missing input for prompt: {e}")
        
        # Make LLM call
        start_time = time.time()
        response = await llm_client.generate_async(formatted_prompt, model=model)
        duration = time.time() - start_time
        
        return {
            'outputs': {
                'response': response,
                'prompt': formatted_prompt
            },
            'llm_calls': 1,
            'tokens_processed': len(formatted_prompt.split()) + len(response.split()),
            'duration': duration
        }
    
    async def _execute_data_stage(self, stage: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute data processing stage"""
        
        operation = stage.get('operation', 'transform')
        data = inputs.get('data', {})
        
        if operation == 'transform':
            # Apply transformation
            transform_func = stage.get('transform_function')
            if transform_func:
                # This would be a registered transformation function
                result = data  # Placeholder
            else:
                result = data
            
            return {
                'outputs': {
                    'transformed_data': result
                }
            }
        
        return {'outputs': {}}
    
    async def _execute_api_stage(self, stage: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute API call stage"""
        
        import aiohttp
        
        url = stage.get('url', '')
        method = stage.get('method', 'GET')
        headers = stage.get('headers', {})
        
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=headers) as response:
                data = await response.json()
                
                return {
                    'outputs': {
                        'api_response': data,
                        'status_code': response.status
                    }
                }
    
    async def _execute_file_stage(self, stage: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute file operation stage"""
        
        operation = stage.get('operation', 'read')
        file_path = stage.get('path', '')
        
        if operation == 'read':
            with open(file_path) as f:
                content = f.read()
            
            return {
                'outputs': {
                    'file_content': content
                }
            }
        elif operation == 'write':
            content = inputs.get('content', '')
            with open(file_path, 'w') as f:
                f.write(content)
            
            return {
                'outputs': {
                    'file_written': file_path
                }
            }
        
        return {'outputs': {}}
    
    async def _execute_default_stage(self, stage: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute default stage"""
        
        # Default implementation - just pass through inputs
        return {
            'outputs': inputs
        }
    
    def _can_run_parallel(self, stages: list[dict[str, Any]]) -> bool:
        """Check if stages can run in parallel"""
        
        # Check if any stage has dependencies
        for stage in stages:
            if stage.get('dependencies'):
                return False
        
        return True
    
    def _group_stages_by_dependencies(self, stages: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
        """Group stages by dependencies"""
        
        # Simple implementation - all stages in one group if no dependencies
        if all(not stage.get('dependencies') for stage in stages):
            return [stages]
        
        # More complex dependency resolution would go here
        return [[stage] for stage in stages]
    
    def _get_stage_cache_key(self, stage: dict[str, Any], inputs: dict[str, Any]) -> str:
        """Generate cache key for stage"""
        
        import hashlib
        
        # Create a hash of stage and inputs
        cache_data = {
            'stage': stage,
            'inputs': inputs
        }
        
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _calculate_performance_score(self, metrics: PipelineMetrics) -> float:
        """Calculate performance score based on metrics"""
        
        # Base score
        score = 100.0
        
        # Deduct points for errors
        score -= len(metrics.errors) * 10
        
        # Deduct points for long duration
        if metrics.duration > 300:  # 5 minutes
            score -= (metrics.duration - 300) / 60  # 1 point per minute over 5
        
        # Add points for efficiency
        if metrics.llm_calls > 0:
            efficiency = metrics.tokens_processed / metrics.llm_calls
            if efficiency > 1000:  # Good token efficiency
                score += 10
        
        # Ensure score is between 0 and 100
        return max(0, min(100, score))
    
    async def _check_resource_limits(self) -> None:
        """Check if resource limits are exceeded"""
        
        import psutil
        
        # Check memory usage
        memory_percent = psutil.virtual_memory().percent
        if memory_percent > self.config.resource_limits['max_memory_mb'] / 1024 * 100:
            logger.warning(f"High memory usage: {memory_percent}%")
        
        # Check CPU usage
        cpu_percent = psutil.cpu_percent()
        if cpu_percent > self.config.resource_limits['max_cpu_percent']:
            logger.warning(f"High CPU usage: {cpu_percent}%")
    
    def get_pipeline_status(self, pipeline_id: str) -> dict[str, Any] | None:
        """Get pipeline status"""
        
        if pipeline_id not in self.running_pipelines:
            return None
        
        pipeline_state = self.running_pipelines[pipeline_id]
        metrics = self.pipeline_metrics.get(pipeline_id)
        
        return {
            'pipeline_id': pipeline_id,
            'status': pipeline_state['status'].value,
            'current_stage': pipeline_state['current_stage'],
            'stages_total': len(pipeline_state['stages']),
            'start_time': pipeline_state['start_time'].isoformat(),
            'end_time': pipeline_state.get('end_time', '').isoformat() if pipeline_state.get('end_time') else None,
            'retry_count': pipeline_state['retry_count'],
            'metrics': metrics.to_dict() if metrics else None
        }
    
    def cancel_pipeline(self, pipeline_id: str) -> bool:
        """Cancel a running pipeline"""
        
        if pipeline_id not in self.running_pipelines:
            return False
        
        pipeline_state = self.running_pipelines[pipeline_id]
        
        if pipeline_state['status'] in [PipelineStatus.RUNNING, PipelineStatus.PENDING]:
            pipeline_state['status'] = PipelineStatus.CANCELLED
            logger.info(f"Pipeline {pipeline_id} cancelled")
            return True
        
        return False
    
    def get_performance_metrics(self) -> dict[str, Any]:
        """Get overall performance metrics"""
        
        if not self.metrics_history:
            return {}
        
        recent_metrics = self.metrics_history[-10:]  # Last 10 pipelines
        
        avg_duration = sum(m.duration for m in recent_metrics) / len(recent_metrics)
        avg_score = sum(m.performance_score for m in recent_metrics) / len(recent_metrics)
        total_errors = sum(len(m.errors) for m in recent_metrics)
        
        return {
            'total_pipelines': len(self.metrics_history),
            'avg_duration': avg_duration,
            'avg_performance_score': avg_score,
            'total_errors': total_errors,
            'cache_size': len(self.performance_cache),
            'running_pipelines': len(self.running_pipelines)
        }
    
    def cleanup_completed_pipelines(self, max_age_hours: int = 24) -> int:
        """Clean up old completed pipelines"""
        
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        cleaned_count = 0
        
        # Remove old pipelines
        to_remove = []
        for pipeline_id, pipeline_state in self.running_pipelines.items():
            if (pipeline_state['status'] in [PipelineStatus.COMPLETED, PipelineStatus.FAILED, PipelineStatus.CANCELLED] and
                pipeline_state.get('end_time', datetime.utcnow()) < cutoff_time):
                to_remove.append(pipeline_id)
        
        for pipeline_id in to_remove:
            del self.running_pipelines[pipeline_id]
            if pipeline_id in self.pipeline_metrics:
                self.metrics_history.append(self.pipeline_metrics[pipeline_id])
                del self.pipeline_metrics[pipeline_id]
            cleaned_count += 1
        
        logger.info(f"Cleaned up {cleaned_count} old pipelines")
        return cleaned_count


# Example usage
async def example_usage():
    """Example of enhanced pipeline usage"""
    
    # Create enhanced pipeline manager
    config = PipelineConfig(
        max_concurrent_stages=3,
        enable_caching=True,
        enable_monitoring=True,
        enable_auto_retry=True,
        enable_parallel_execution=True
    )
    
    manager = EnhancedPipelineManager(config)
    
    # Define pipeline stages
    stages = [
        {
            'name': 'idea_generation',
            'type': 'llm_call',
            'prompt': 'Generate 3 startup ideas for {topic}',
            'model': 'llama3.1:8b'
        },
        {
            'name': 'idea_evaluation',
            'type': 'llm_call',
            'prompt': 'Evaluate this idea: {idea}',
            'model': 'llama3.1:8b'
        },
        {
            'name': 'save_results',
            'type': 'file_operation',
            'operation': 'write',
            'path': 'results.json'
        }
    ]
    
    # Start pipeline
    pipeline_id = await manager.start_pipeline(
        'test_pipeline',
        stages,
        {'topic': 'AI in healthcare'}
    )
    
    # Monitor progress
    while True:
        status = manager.get_pipeline_status(pipeline_id)
        if status['status'] in ['completed', 'failed', 'cancelled']:
            break
        
        print(f"Pipeline status: {status['status']}, Stage: {status['current_stage']}/{status['stages_total']}")
        await asyncio.sleep(1)
    
    # Get final metrics
    final_status = manager.get_pipeline_status(pipeline_id)
    performance = manager.get_performance_metrics()
    
    print(f"Pipeline completed with score: {final_status['metrics']['performance_score']}")
    print(f"Performance metrics: {performance}")


if __name__ == "__main__":
    asyncio.run(example_usage())
