"""
Advanced Agent Performance Optimizer
Improves agent efficiency, reduces LLM calls, and enhances response quality
"""

import asyncio
import json
import time
from typing import Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
from collections import defaultdict
import hashlib
import pickle
import redis
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent execution status"""
    IDLE = "idle"
    THINKING = "thinking"
    WORKING = "working"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentMetrics:
    """Agent performance metrics"""
    agent_id: str
    agent_type: str
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    avg_task_duration: float = 0.0
    total_llm_calls: int = 0
    total_tokens: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    efficiency_score: float = 0.0
    last_activity: datetime | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'total_tasks': self.total_tasks,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'avg_task_duration': self.avg_task_duration,
            'total_llm_calls': self.total_llm_calls,
            'total_tokens': self.total_tokens,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'efficiency_score': self.efficiency_score,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None
        }
    
    def update_efficiency(self) -> None:
        """Calculate efficiency score"""
        if self.total_tasks == 0:
            self.efficiency_score = 0.0
            return
        
        # Base efficiency from completion rate
        completion_rate = self.completed_tasks / self.total_tasks
        
        # Cache efficiency
        cache_efficiency = self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
        
        # Speed efficiency (lower duration is better)
        speed_efficiency = max(0, 1 - (self.avg_task_duration / 300))  # Normalize to 5 minutes
        
        # Token efficiency
        token_efficiency = min(1, self.total_tokens / max(self.total_llm_calls, 1) / 1000)  # 1000 tokens per call is good
        
        # Weighted score
        self.efficiency_score = (
            completion_rate * 0.4 +
            cache_efficiency * 0.3 +
            speed_efficiency * 0.2 +
            token_efficiency * 0.1
        ) * 100


class SmartCache:
    """Intelligent caching system for agent responses"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", max_size: int = 10000):
        self.redis_client = redis.from_url(redis_url)
        self.max_size = max_size
        self.cache_stats = defaultdict(int)
        self.similarity_threshold = 0.85
    
    def _generate_cache_key(self, agent_type: str, task: str, context: dict[str, Any]) -> str:
        """Generate cache key for task"""
        cache_data = {
            'agent_type': agent_type,
            'task': task,
            'context': context
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using simple word overlap"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    async def get(self, agent_type: str, task: str, context: dict[str, Any]) -> Any | None:
        """Get cached response"""
        
        # Try exact match first
        exact_key = self._generate_cache_key(agent_type, task, context)
        cached_result = self.redis_client.get(exact_key)
        
        if cached_result:
            self.cache_stats['exact_hits'] += 1
            return pickle.loads(cached_result)
        
        # Try similarity search
        similarity_key = f"similarity:{agent_type}"
        cached_tasks = self.redis_client.hgetall(similarity_key)
        
        if cached_tasks:
            best_match = None
            best_similarity = 0.0
            
            for cached_key, cached_data in cached_tasks.items():
                try:
                    cached_task = json.loads(cached_key.decode())['task']
                    similarity = self._calculate_similarity(task, cached_task)
                    
                    if similarity > best_similarity and similarity >= self.similarity_threshold:
                        best_similarity = similarity
                        best_match = pickle.loads(cached_data)
                except Exception as e:
                    logger.warning(f"Error parsing cached task: {e}")
            
            if best_match:
                self.cache_stats['similarity_hits'] += 1
                return best_match
        
        self.cache_stats['misses'] += 1
        return None
    
    async def set(self, agent_type: str, task: str, context: dict[str, Any], result: Any, ttl: int = 3600) -> None:
        """Cache response"""
        
        # Exact cache
        exact_key = self._generate_cache_key(agent_type, task, context)
        self.redis_client.setex(exact_key, ttl, pickle.dumps(result))
        
        # Similarity cache
        similarity_key = f"similarity:{agent_type}"
        task_data = json.dumps({'task': task})
        self.redis_client.hset(similarity_key, task_data, pickle.dumps(result))
        self.redis_client.expire(similarity_key, ttl)
        
        # Update stats
        self.cache_stats['sets'] += 1
    
    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats['exact_hits'] + self.cache_stats['similarity_hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['exact_hits'] + self.cache_stats['similarity_hits']) / total_requests if total_requests > 0 else 0
        
        return {
            'exact_hits': self.cache_stats['exact_hits'],
            'similarity_hits': self.cache_stats['similarity_hits'],
            'misses': self.cache_stats['misses'],
            'hit_rate': hit_rate,
            'total_sets': self.cache_stats['sets']
        }


class TaskQueue:
    """Priority-based task queue for agents"""
    
    def __init__(self):
        self.queues = {
            'high': asyncio.Queue(),
            'normal': asyncio.Queue(),
            'low': asyncio.Queue()
        }
        self.task_stats = defaultdict(int)
    
    async def put(self, task: dict[str, Any], priority: str = 'normal') -> None:
        """Add task to queue"""
        if priority not in self.queues:
            priority = 'normal'
        
        await self.queues[priority].put(task)
        self.task_stats[f'added_{priority}'] += 1
    
    async def get(self) -> tuple[dict[str, Any], str]:
        """Get next task from highest priority queue"""
        
        # Check queues in priority order
        for priority in ['high', 'normal', 'low']:
            try:
                task = self.queues[priority].get_nowait()
                self.task_stats[f'got_{priority}'] += 1
                return task, priority
            except asyncio.QueueEmpty:
                continue
        
        # No tasks available
        return None, None
    
    def size(self) -> int:
        """Get total queue size"""
        return sum(queue.qsize() for queue in self.queues.values())
    
    def get_stats(self) -> dict[str, Any]:
        """Get queue statistics"""
        return {
            'queue_sizes': {priority: queue.qsize() for priority, queue in self.queues.items()},
            'total_size': self.size(),
            'task_stats': dict(self.task_stats)
        }


class AgentOptimizer:
    """Advanced agent performance optimizer"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.cache = SmartCache(redis_url)
        self.task_queue = TaskQueue()
        self.agent_metrics: dict[str, AgentMetrics] = {}
        self.performance_history: list[dict[str, Any]] = []
        self.optimization_rules = self._load_optimization_rules()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def _load_optimization_rules(self) -> dict[str, Any]:
        """Load optimization rules"""
        return {
            'cache_enabled_agents': ['researcher', 'analyst', 'product'],
            'parallel_agents': ['researcher', 'analyst'],
            'timeout_per_task': {
                'researcher': 120,
                'analyst': 90,
                'product': 60,
                'tech_lead': 180,
                'growth': 90
            },
            'max_concurrent_tasks': {
                'researcher': 3,
                'analyst': 2,
                'product': 2,
                'tech_lead': 1,
                'growth': 2
            },
            'retry_limits': {
                'researcher': 2,
                'analyst': 2,
                'product': 1,
                'tech_lead': 1,
                'growth': 2
            }
        }
    
    async def optimize_agent_task(self, agent_id: str, agent_type: str, task: str, 
                                context: dict[str, Any]) -> dict[str, Any]:
        """Optimize and execute agent task"""
        
        # Initialize metrics if needed
        if agent_id not in self.agent_metrics:
            self.agent_metrics[agent_id] = AgentMetrics(agent_id, agent_type)
        
        metrics = self.agent_metrics[agent_id]
        metrics.total_tasks += 1
        metrics.last_activity = datetime.utcnow()
        
        start_time = time.time()
        
        try:
            # Check cache first
            if agent_type in self.optimization_rules['cache_enabled_agents']:
                cached_result = await self.cache.get(agent_type, task, context)
                if cached_result:
                    metrics.cache_hits += 1
                    metrics.completed_tasks += 1
                    
                    duration = time.time() - start_time
                    metrics.avg_task_duration = (metrics.avg_task_duration * (metrics.completed_tasks - 1) + duration) / metrics.completed_tasks
                    
                    logger.info(f"Cache hit for {agent_type}: {task[:50]}...")
                    return cached_result
            
            metrics.cache_misses += 1
            
            # Execute task with optimization
            result = await self._execute_optimized_task(agent_id, agent_type, task, context)
            
            # Cache result
            if agent_type in self.optimization_rules['cache_enabled_agents']:
                await self.cache.set(agent_type, task, context, result)
            
            # Update metrics
            metrics.completed_tasks += 1
            duration = time.time() - start_time
            metrics.avg_task_duration = (metrics.avg_task_duration * (metrics.completed_tasks - 1) + duration) / metrics.completed_tasks
            
            # Update LLM metrics
            if 'llm_calls' in result:
                metrics.total_llm_calls += result['llm_calls']
            if 'tokens_processed' in result:
                metrics.total_tokens += result['tokens_processed']
            
            metrics.update_efficiency()
            
            return result
            
        except Exception as e:
            metrics.failed_tasks += 1
            metrics.update_efficiency()
            logger.error(f"Task failed for {agent_type}: {e}")
            raise
    
    async def _execute_optimized_task(self, agent_id: str, agent_type: str, task: str, 
                                    context: dict[str, Any]) -> dict[str, Any]:
        """Execute task with optimizations"""
        
        # Get timeout for this agent type
        timeout = self.optimization_rules['timeout_per_task'].get(agent_type, 120)
        
        # Get retry limit
        retry_limit = self.optimization_rules['retry_limits'].get(agent_type, 2)
        
        # Execute with timeout and retry
        for attempt in range(retry_limit + 1):
            try:
                # Execute task
                result = await asyncio.wait_for(
                    self._execute_agent_task(agent_type, task, context),
                    timeout=timeout
                )
                
                # Add optimization metadata
                result['optimization'] = {
                    'attempt': attempt + 1,
                    'cached': False,
                    'timeout': timeout,
                    'execution_time': time.time()
                }
                
                return result
                
            except TimeoutError:
                if attempt < retry_limit:
                    logger.warning(f"Task timeout for {agent_type}, retrying... ({attempt + 1}/{retry_limit + 1})")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise TimeoutError(f"Task timed out after {retry_limit + 1} attempts")
            
            except Exception as e:
                if attempt < retry_limit:
                    logger.warning(f"Task failed for {agent_type}, retrying... ({attempt + 1}/{retry_limit + 1}): {e}")
                    await asyncio.sleep(1)
                else:
                    raise
    
    async def _execute_agent_task(self, agent_type: str, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Execute actual agent task"""
        
        # This would integrate with the existing agent system
        # For now, simulate execution
        
        if agent_type == 'researcher':
            return await self._execute_researcher_task(task, context)
        elif agent_type == 'analyst':
            return await self._execute_analyst_task(task, context)
        elif agent_type == 'product':
            return await self._execute_product_task(task, context)
        elif agent_type == 'tech_lead':
            return await self._execute_tech_lead_task(task, context)
        elif agent_type == 'growth':
            return await self._execute_growth_task(task, context)
        else:
            return await self._execute_default_task(task, context)
    
    async def _execute_researcher_task(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Execute researcher task with optimizations"""
        
        # Simulate research task
        await asyncio.sleep(2)  # Simulate work
        
        return {
            'outputs': {
                'research_findings': f"Research results for: {task}",
                'sources': ['source1', 'source2', 'source3'],
                'confidence': 0.85
            },
            'llm_calls': 2,
            'tokens_processed': 1500
        }
    
    async def _execute_analyst_task(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Execute analyst task with optimizations"""
        
        await asyncio.sleep(1.5)
        
        return {
            'outputs': {
                'analysis': f"Analysis of: {task}",
                'recommendations': ['rec1', 'rec2'],
                'score': 0.78
            },
            'llm_calls': 1,
            'tokens_processed': 800
        }
    
    async def _execute_product_task(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Execute product task with optimizations"""
        
        await asyncio.sleep(1)
        
        return {
            'outputs': {
                'product_spec': f"Product specification for: {task}",
                'features': ['feature1', 'feature2'],
                'user_stories': ['story1', 'story2']
            },
            'llm_calls': 1,
            'tokens_processed': 600
        }
    
    async def _execute_tech_lead_task(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Execute tech lead task with optimizations"""
        
        await asyncio.sleep(3)
        
        return {
            'outputs': {
                'tech_spec': f"Technical specification for: {task}",
                'architecture': 'microservices',
                'technologies': ['Python', 'FastAPI', 'React']
            },
            'llm_calls': 3,
            'tokens_processed': 2000
        }
    
    async def _execute_growth_task(self, str, context: dict[str, Any]) -> dict[str, Any]:
        """Execute growth task with optimizations"""
        
        await asyncio.sleep(1.5)
        
        return {
            'outputs': {
                'growth_strategy': f"Growth strategy for: {task}",
                'channels': ['social', 'email', 'content'],
                'metrics': ['MAU', 'conversion', 'retention']
            },
            'llm_calls': 2,
            'tokens_processed': 1000
        }
    
    async def _execute_default_task(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        """Execute default task"""
        
        await asyncio.sleep(1)
        
        return {
            'outputs': {
                'result': f"Default result for: {task}"
            },
            'llm_calls': 1,
            'tokens_processed': 500
        }
    
    async def run_parallel_agents(self, agent_tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Run multiple agents in parallel where possible"""
        
        # Group tasks by agent type
        task_groups = defaultdict(list)
        for i, task in enumerate(agent_tasks):
            agent_type = task.get('agent_type', 'default')
            task_groups[agent_type].append((i, task))
        
        # Execute parallelizable agents
        results = [None] * len(agent_tasks)
        
        # Check which agents can run in parallel
        parallel_agents = self.optimization_rules['parallel_agents']
        
        # Create tasks for parallel execution
        parallel_tasks = []
        task_mapping = []
        
        for agent_type, tasks in task_groups.items():
            if agent_type in parallel_agents and len(tasks) > 1:
                # Can run in parallel
                for i, task in tasks:
                    future = asyncio.create_task(
                        self.optimize_agent_task(
                            task.get('agent_id', f"{agent_type}_{i}"),
                            agent_type,
                            task.get('task', ''),
                            task.get('context', {})
                        )
                    )
                    parallel_tasks.append(future)
                    task_mapping.append((i, future))
            else:
                # Must run sequentially
                for i, task in tasks:
                    result = await self.optimize_agent_task(
                        task.get('agent_id', f"{agent_type}_{i}"),
                        agent_type,
                        task.get('task', ''),
                        task.get('context', {})
                    )
                    results[i] = result
        
        # Wait for parallel tasks
        if parallel_tasks:
            parallel_results = await asyncio.gather(*parallel_tasks, return_exceptions=True)
            
            for i, future in task_mapping:
                try:
                    results[i] = future.result()
                except Exception as e:
                    results[i] = {'error': str(e)}
        
        return results
    
    def get_agent_metrics(self, agent_id: str = None) -> dict[str, Any]:
        """Get agent performance metrics"""
        
        if agent_id:
            if agent_id in self.agent_metrics:
                return self.agent_metrics[agent_id].to_dict()
            else:
                return {}
        
        # Return all agent metrics
        return {
            agent_id: metrics.to_dict()
            for agent_id, metrics in self.agent_metrics.items()
        }
    
    def get_performance_summary(self) -> dict[str, Any]:
        """Get overall performance summary"""
        
        if not self.agent_metrics:
            return {}
        
        # Calculate aggregate metrics
        total_tasks = sum(m.total_tasks for m in self.agent_metrics.values())
        completed_tasks = sum(m.completed_tasks for m in self.agent_metrics.values())
        failed_tasks = sum(m.failed_tasks for m in self.agent_metrics.values())
        total_llm_calls = sum(m.total_llm_calls for m in self.agent_metrics.values())
        total_tokens = sum(m.total_tokens for m in self.agent_metrics.values())
        total_cache_hits = sum(m.cache_hits for m in self.agent_metrics.values())
        total_cache_misses = sum(m.cache_misses for m in self.agent_metrics.values())
        
        avg_efficiency = sum(m.efficiency_score for m in self.agent_metrics.values()) / len(self.agent_metrics)
        
        cache_hit_rate = total_cache_hits / (total_cache_hits + total_cache_misses) if (total_cache_hits + total_cache_misses) > 0 else 0
        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
        
        return {
            'total_agents': len(self.agent_metrics),
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
            'completion_rate': completion_rate,
            'total_llm_calls': total_llm_calls,
            'total_tokens': total_tokens,
            'avg_tokens_per_call': total_tokens / total_llm_calls if total_llm_calls > 0 else 0,
            'cache_hit_rate': cache_hit_rate,
            'avg_efficiency_score': avg_efficiency,
            'cache_stats': self.cache.get_stats(),
            'queue_stats': self.task_queue.get_stats()
        }
    
    def optimize_agent_configuration(self, agent_type: str) -> dict[str, Any]:
        """Generate optimization recommendations for agent type"""
        
        if agent_type not in self.agent_metrics:
            return {}
        
        # Get metrics for this agent type
        agent_metrics = [m for m in self.agent_metrics.values() if m.agent_type == agent_type]
        
        if not agent_metrics:
            return {}
        
        # Calculate averages
        avg_efficiency = sum(m.efficiency_score for m in agent_metrics) / len(agent_metrics)
        avg_duration = sum(m.avg_task_duration for m in agent_metrics) / len(agent_metrics)
        cache_hit_rate = sum(m.cache_hits for m in agent_metrics) / sum(m.cache_hits + m.cache_misses) if sum(m.cache_hits + m.cache_misses) > 0 else 0
        
        # Generate recommendations
        recommendations = []
        
        if avg_efficiency < 70:
            recommendations.append("Consider increasing timeout or reducing task complexity")
        
        if avg_duration > self.optimization_rules['timeout_per_task'].get(agent_type, 120) * 0.8:
            recommendations.append("Tasks are taking too long, consider breaking down complex tasks")
        
        if cache_hit_rate < 0.5:
            recommendations.append("Enable caching for this agent type to improve performance")
        
        if sum(m.total_llm_calls for m in agent_metrics) > len(agent_metrics) * 5:
            recommendations.append("High LLM usage detected, consider optimizing prompts")
        
        return {
            'agent_type': agent_type,
            'avg_efficiency': avg_efficiency,
            'avg_duration': avg_duration,
            'cache_hit_rate': cache_hit_rate,
            'recommendations': recommendations,
            'current_config': self.optimization_rules.get(agent_type, {})
        }


# Example usage
async def example_usage():
    """Example of agent optimizer usage"""
    
    optimizer = AgentOptimizer()
    
    # Define agent tasks
    agent_tasks = [
        {
            'agent_id': 'researcher_1',
            'agent_type': 'researcher',
            'task': 'Research AI in healthcare market',
            'context': {'topic': 'AI healthcare', 'depth': 'deep'}
        },
        {
            'agent_id': 'analyst_1',
            'agent_type': 'analyst',
            'task': 'Analyze market opportunities',
            'context': {'market': 'healthcare', 'region': 'US'}
        },
        {
            'agent_id': 'product_1',
            'agent_type': 'product',
            'task': 'Define product requirements',
            'context': {'features': ['AI diagnosis', 'patient management']}
        }
    ]
    
    # Run agents with optimization
    results = await optimizer.run_parallel_agents(agent_tasks)
    
    # Get performance summary
    summary = optimizer.get_performance_summary()
    print(f"Performance Summary: {summary}")
    
    # Get optimization recommendations
    for agent_type in ['researcher', 'analyst', 'product']:
        recommendations = optimizer.optimize_agent_configuration(agent_type)
        print(f"{agent_type} recommendations: {recommendations}")


if __name__ == "__main__":
    asyncio.run(example_usage())
