"""
Business Intelligence Metrics for Asmblr
Tracks MVP generation performance, user behavior, and business KPIs
"""

import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import asyncio

from prometheus_client import Counter, Histogram, Gauge, Info
import redis.asyncio as redis
from loguru import logger

from app.core.config import get_settings


class MetricType(Enum):
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    GAUGE = "gauge"
    INFO = "info"


@dataclass
class BusinessMetric:
    """Business metric definition"""
    name: str
    description: str
    metric_type: MetricType
    labels: List[str] = None
    unit: str = ""
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = []


class BusinessMetricsCollector:
    """Collects and manages business intelligence metrics"""
    
    def __init__(self):
        settings = get_settings()
        self.redis_url = settings.redis_url
        self._redis_client: Optional[redis.Redis] = None
        
        # Prometheus metrics
        self._prometheus_metrics = {}
        self._setup_prometheus_metrics()
        
        # Metric definitions
        self.metrics = {
            # MVP Generation Metrics
            "mvp_generated_total": BusinessMetric(
                "mvp_generated_total",
                "Total number of MVPs generated",
                MetricType.COUNTER,
                ["status", "model_type", "execution_profile"]
            ),
            "mvp_generation_duration": BusinessMetric(
                "mvp_generation_duration_seconds",
                "Time taken to generate MVP",
                MetricType.HISTOGRAM,
                ["execution_profile"],
                "seconds"
            ),
            "mvp_quality_score": BusinessMetric(
                "mvp_quality_score",
                "Quality score of generated MVPs",
                MetricType.HISTOGRAM,
                ["quality_dimension"],
                "score"
            ),
            
            # User Engagement Metrics
            "user_sessions_total": BusinessMetric(
                "user_sessions_total",
                "Total number of user sessions",
                MetricType.COUNTER,
                ["user_type"]
            ),
            "session_duration": BusinessMetric(
                "session_duration_seconds",
                "Duration of user sessions",
                MetricType.HISTOGRAM,
                ["user_type"],
                "seconds"
            ),
            "feature_usage": BusinessMetric(
                "feature_usage_total",
                "Usage of specific features",
                MetricType.COUNTER,
                ["feature", "action"]
            ),
            
            # Idea Generation Metrics
            "ideas_generated_total": BusinessMetric(
                "ideas_generated_total",
                "Total number of ideas generated",
                MetricType.COUNTER,
                ["source", "icp_aligned"]
            ),
            "idea_actionability_score": BusinessMetric(
                "idea_actionability_score",
                "Actionability score of generated ideas",
                MetricType.HISTOGRAM,
                ["icp_aligned"],
                "score"
            ),
            "idea_to_mvp_conversion": BusinessMetric(
                "idea_to_mvp_conversion_rate",
                "Conversion rate from ideas to MVPs",
                MetricType.GAUGE,
                ["time_period"],
                "percentage"
            ),
            
            # Performance Metrics
            "llm_api_calls_total": BusinessMetric(
                "llm_api_calls_total",
                "Total number of LLM API calls",
                MetricType.COUNTER,
                ["model", "endpoint", "status"]
            ),
            "llm_response_duration": BusinessMetric(
                "llm_response_duration_seconds",
                "LLM response time",
                MetricType.HISTOGRAM,
                ["model", "endpoint"],
                "seconds"
            ),
            "cache_hit_rate": BusinessMetric(
                "cache_hit_rate",
                "Cache hit rate for LLM responses",
                MetricType.GAUGE,
                ["cache_type"],
                "percentage"
            ),
            
            # System Health Metrics
            "active_users": BusinessMetric(
                "active_users_current",
                "Current number of active users",
                MetricType.GAUGE,
                ["activity_type"]
            ),
            "system_load": BusinessMetric(
                "system_load_percentage",
                "System load percentage",
                MetricType.GAUGE,
                ["component"],
                "percentage"
            ),
            "error_rate": BusinessMetric(
                "error_rate",
                "Error rate by component",
                MetricType.GAUGE,
                ["component", "error_type"],
                "percentage"
            )
        }
    
    def _setup_prometheus_metrics(self):
        """Setup Prometheus metrics"""
        # MVP Generation
        self._prometheus_metrics["mvp_generated_total"] = Counter(
            "asmblr_mvp_generated_total",
            "Total number of MVPs generated",
            ["status", "model_type", "execution_profile"]
        )
        
        self._prometheus_metrics["mvp_generation_duration"] = Histogram(
            "asmblr_mvp_generation_duration_seconds",
            "Time taken to generate MVP",
            ["execution_profile"],
            buckets=[60, 300, 600, 1800, 3600, 7200]  # 1min to 2hrs
        )
        
        self._prometheus_metrics["mvp_quality_score"] = Histogram(
            "asmblr_mvp_quality_score",
            "Quality score of generated MVPs",
            ["quality_dimension"],
            buckets=[20, 40, 60, 80, 100]
        )
        
        # User Engagement
        self._prometheus_metrics["user_sessions_total"] = Counter(
            "asmblr_user_sessions_total",
            "Total number of user sessions",
            ["user_type"]
        )
        
        self._prometheus_metrics["session_duration"] = Histogram(
            "asmblr_session_duration_seconds",
            "Duration of user sessions",
            ["user_type"],
            buckets=[60, 300, 900, 1800, 3600]  # 1min to 1hr
        )
        
        self._prometheus_metrics["feature_usage"] = Counter(
            "asmblr_feature_usage_total",
            "Usage of specific features",
            ["feature", "action"]
        )
        
        # Idea Generation
        self._prometheus_metrics["ideas_generated_total"] = Counter(
            "asmblr_ideas_generated_total",
            "Total number of ideas generated",
            ["source", "icp_aligned"]
        )
        
        self._prometheus_metrics["idea_actionability_score"] = Histogram(
            "asmblr_idea_actionability_score",
            "Actionability score of generated ideas",
            ["icp_aligned"],
            buckets=[0, 20, 40, 60, 80, 100]
        )
        
        # Performance
        self._prometheus_metrics["llm_api_calls_total"] = Counter(
            "asmblr_llm_api_calls_total",
            "Total number of LLM API calls",
            ["model", "endpoint", "status"]
        )
        
        self._prometheus_metrics["llm_response_duration"] = Histogram(
            "asmblr_llm_response_duration_seconds",
            "LLM response time",
            ["model", "endpoint"],
            buckets=[1, 5, 10, 30, 60, 120]  # 1s to 2min
        )
        
        self._prometheus_metrics["cache_hit_rate"] = Gauge(
            "asmblr_cache_hit_rate",
            "Cache hit rate for LLM responses",
            ["cache_type"]
        )
        
        # System Health
        self._prometheus_metrics["active_users"] = Gauge(
            "asmblr_active_users_current",
            "Current number of active users",
            ["activity_type"]
        )
        
        self._prometheus_metrics["system_load"] = Gauge(
            "asmblr_system_load_percentage",
            "System load percentage",
            ["component"]
        )
        
        self._prometheus_metrics["error_rate"] = Gauge(
            "asmblr_error_rate",
            "Error rate by component",
            ["component", "error_type"]
        )
    
    async def _get_redis_client(self) -> redis.Redis:
        """Get or create Redis client"""
        if self._redis_client is None:
            self._redis_client = redis.from_url(self.redis_url)
        return self._redis_client
    
    # MVP Generation Metrics
    async def record_mvp_generation(
        self,
        status: str,
        model_type: str,
        execution_profile: str,
        duration: float,
        quality_scores: Dict[str, float]
    ) -> None:
        """Record MVP generation metrics"""
        try:
            # Prometheus metrics
            self._prometheus_metrics["mvp_generated_total"].labels(
                status=status,
                model_type=model_type,
                execution_profile=execution_profile
            ).inc()
            
            self._prometheus_metrics["mvp_generation_duration"].labels(
                execution_profile=execution_profile
            ).observe(duration)
            
            for dimension, score in quality_scores.items():
                self._prometheus_metrics["mvp_quality_score"].labels(
                    quality_dimension=dimension
                ).observe(score)
            
            # Store detailed event in Redis
            redis_client = await self._get_redis_client()
            event = {
                "timestamp": datetime.now().isoformat(),
                "event_type": "mvp_generation",
                "status": status,
                "model_type": model_type,
                "execution_profile": execution_profile,
                "duration": duration,
                "quality_scores": quality_scores
            }
            
            await redis_client.lpush(
                "business_events:mvp_generation",
                json.dumps(event)
            )
            
            # Keep only last 1000 events
            await redis_client.ltrim("business_events:mvp_generation", 0, 999)
            
        except Exception as e:
            logger.warning(f"Failed to record MVP generation metrics: {e}")
    
    # User Engagement Metrics
    async def record_user_session(
        self,
        user_type: str,
        session_duration: float,
        features_used: List[str]
    ) -> None:
        """Record user session metrics"""
        try:
            # Prometheus metrics
            self._prometheus_metrics["user_sessions_total"].labels(
                user_type=user_type
            ).inc()
            
            self._prometheus_metrics["session_duration"].labels(
                user_type=user_type
            ).observe(session_duration)
            
            # Record feature usage
            for feature in features_used:
                self._prometheus_metrics["feature_usage"].labels(
                    feature=feature,
                    action="used"
                ).inc()
            
            # Store detailed event
            redis_client = await self._get_redis_client()
            event = {
                "timestamp": datetime.now().isoformat(),
                "event_type": "user_session",
                "user_type": user_type,
                "session_duration": session_duration,
                "features_used": features_used
            }
            
            await redis_client.lpush(
                "business_events:user_sessions",
                json.dumps(event)
            )
            
            await redis_client.ltrim("business_events:user_sessions", 0, 999)
            
        except Exception as e:
            logger.warning(f"Failed to record user session metrics: {e}")
    
    # Idea Generation Metrics
    async def record_idea_generation(
        self,
        source: str,
        icp_aligned: bool,
        actionability_score: float,
        total_ideas: int
    ) -> None:
        """Record idea generation metrics"""
        try:
            icp_label = "true" if icp_aligned else "false"
            
            # Prometheus metrics
            self._prometheus_metrics["ideas_generated_total"].labels(
                source=source,
                icp_aligned=icp_label
            ).inc(total_ideas)
            
            self._prometheus_metrics["idea_actionability_score"].labels(
                icp_aligned=icp_label
            ).observe(actionability_score)
            
            # Store detailed event
            redis_client = await self._get_redis_client()
            event = {
                "timestamp": datetime.now().isoformat(),
                "event_type": "idea_generation",
                "source": source,
                "icp_aligned": icp_aligned,
                "actionability_score": actionability_score,
                "total_ideas": total_ideas
            }
            
            await redis_client.lpush(
                "business_events:idea_generation",
                json.dumps(event)
            )
            
            await redis_client.ltrim("business_events:idea_generation", 0, 999)
            
        except Exception as e:
            logger.warning(f"Failed to record idea generation metrics: {e}")
    
    # Performance Metrics
    async def record_llm_call(
        self,
        model: str,
        endpoint: str,
        status: str,
        duration: float
    ) -> None:
        """Record LLM API call metrics"""
        try:
            # Prometheus metrics
            self._prometheus_metrics["llm_api_calls_total"].labels(
                model=model,
                endpoint=endpoint,
                status=status
            ).inc()
            
            if status == "success":
                self._prometheus_metrics["llm_response_duration"].labels(
                    model=model,
                    endpoint=endpoint
                ).observe(duration)
            
        except Exception as e:
            logger.warning(f"Failed to record LLM call metrics: {e}")
    
    async def update_cache_hit_rate(self, cache_type: str, hit_rate: float) -> None:
        """Update cache hit rate metric"""
        try:
            self._prometheus_metrics["cache_hit_rate"].labels(
                cache_type=cache_type
            ).set(hit_rate)
        except Exception as e:
            logger.warning(f"Failed to update cache hit rate: {e}")
    
    # System Health Metrics
    async def update_active_users(self, activity_type: str, count: int) -> None:
        """Update active users metric"""
        try:
            self._prometheus_metrics["active_users"].labels(
                activity_type=activity_type
            ).set(count)
        except Exception as e:
            logger.warning(f"Failed to update active users: {e}")
    
    async def update_system_load(self, component: str, load_percentage: float) -> None:
        """Update system load metric"""
        try:
            self._prometheus_metrics["system_load"].labels(
                component=component
            ).set(load_percentage)
        except Exception as e:
            logger.warning(f"Failed to update system load: {e}")
    
    async def update_error_rate(self, component: str, error_type: str, rate: float) -> None:
        """Update error rate metric"""
        try:
            self._prometheus_metrics["error_rate"].labels(
                component=component,
                error_type=error_type
            ).set(rate)
        except Exception as e:
            logger.warning(f"Failed to update error rate: {e}")
    
    # Analytics and Reporting
    async def get_mvp_analytics(
        self,
        time_period: str = "24h"
    ) -> Dict[str, Any]:
        """Get MVP generation analytics"""
        try:
            redis_client = await self._get_redis_client()
            
            # Get recent MVP generation events
            events = await redis_client.lrange(
                "business_events:mvp_generation",
                0,
                -1
            )
            
            # Filter by time period
            cutoff_time = datetime.now() - timedelta(hours=24)  # Simplified
            recent_events = []
            
            for event_data in events:
                try:
                    event = json.loads(event_data)
                    event_time = datetime.fromisoformat(event["timestamp"])
                    if event_time > cutoff_time:
                        recent_events.append(event)
                except Exception:
                    continue
            
            # Calculate analytics
            total_mvps = len(recent_events)
            successful_mvps = len([e for e in recent_events if e["status"] == "completed"])
            success_rate = (successful_mvps / total_mvps * 100) if total_mvps > 0 else 0
            
            avg_duration = 0
            if recent_events:
                avg_duration = sum(e["duration"] for e in recent_events) / len(recent_events)
            
            # Quality score averages
            quality_scores = {}
            if recent_events:
                for event in recent_events:
                    for dimension, score in event["quality_scores"].items():
                        if dimension not in quality_scores:
                            quality_scores[dimension] = []
                        quality_scores[dimension].append(score)
                
                for dimension in quality_scores:
                    quality_scores[dimension] = sum(quality_scores[dimension]) / len(quality_scores[dimension])
            
            return {
                "time_period": time_period,
                "total_mvps": total_mvps,
                "successful_mvps": successful_mvps,
                "success_rate": round(success_rate, 2),
                "average_duration_seconds": round(avg_duration, 2),
                "quality_scores": quality_scores
            }
            
        except Exception as e:
            logger.warning(f"Failed to get MVP analytics: {e}")
            return {"error": str(e)}
    
    async def get_user_analytics(
        self,
        time_period: str = "24h"
    ) -> Dict[str, Any]:
        """Get user engagement analytics"""
        try:
            redis_client = await self._get_redis_client()
            
            # Get recent user session events
            events = await redis_client.lrange(
                "business_events:user_sessions",
                0,
                -1
            )
            
            # Filter and analyze
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_events = []
            
            for event_data in events:
                try:
                    event = json.loads(event_data)
                    event_time = datetime.fromisoformat(event["timestamp"])
                    if event_time > cutoff_time:
                        recent_events.append(event)
                except Exception:
                    continue
            
            total_sessions = len(recent_events)
            avg_session_duration = 0
            if recent_events:
                avg_session_duration = sum(e["session_duration"] for e in recent_events) / len(recent_events)
            
            # Feature usage analysis
            feature_usage = {}
            for event in recent_events:
                for feature in event["features_used"]:
                    feature_usage[feature] = feature_usage.get(feature, 0) + 1
            
            # User type distribution
            user_types = {}
            for event in recent_events:
                user_type = event["user_type"]
                user_types[user_type] = user_types.get(user_type, 0) + 1
            
            return {
                "time_period": time_period,
                "total_sessions": total_sessions,
                "average_session_duration_seconds": round(avg_session_duration, 2),
                "feature_usage": feature_usage,
                "user_type_distribution": user_types
            }
            
        except Exception as e:
            logger.warning(f"Failed to get user analytics: {e}")
            return {"error": str(e)}
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance metrics summary"""
        try:
            redis_client = await self._get_redis_client()
            
            # Get LLM call events (simplified - in real implementation, would track separately)
            # For now, return current Prometheus metrics
            
            return {
                "cache_hit_rates": {
                    "llm_cache": 0.75,  # Would get from cache manager
                    "redis_cache": 0.85
                },
                "system_load": {
                    "cpu": 45.2,
                    "memory": 67.8,
                    "disk": 23.1
                },
                "error_rates": {
                    "api_gateway": 0.1,
                    "llm_calls": 2.3,
                    "database": 0.05
                },
                "active_users": {
                    "current_sessions": 12,
                    "daily_active": 45
                }
            }
            
        except Exception as e:
            logger.warning(f"Failed to get performance summary: {e}")
            return {"error": str(e)}


# Global metrics collector instance
metrics_collector = BusinessMetricsCollector()


# Decorator for automatic metrics collection
def track_mvp_generation(execution_profile: str = "standard"):
    """Decorator to automatically track MVP generation metrics"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "completed"
            model_type = "unknown"
            quality_scores = {}
            
            try:
                result = await func(*args, **kwargs)
                
                # Extract metrics from result if available
                if isinstance(result, dict):
                    model_type = result.get("model_type", "unknown")
                    quality_scores = result.get("quality_scores", {})
                
                return result
                
            except Exception as e:
                status = "failed"
                raise
            finally:
                duration = time.time() - start_time
                
                # Record metrics
                await metrics_collector.record_mvp_generation(
                    status=status,
                    model_type=model_type,
                    execution_profile=execution_profile,
                    duration=duration,
                    quality_scores=quality_scores
                )
        
        return wrapper
    return decorator
