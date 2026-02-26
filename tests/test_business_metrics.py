"""
Tests for Business Intelligence Metrics
Validates metrics collection, aggregation, and reporting
"""

import pytest
import asyncio
import time
import json
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

from app.monitoring.business_metrics import (
    BusinessMetricsCollector, BusinessMetric, MetricType,
    metrics_collector, track_mvp_generation
)


class TestBusinessMetric:
    """Test suite for BusinessMetric dataclass"""
    
    def test_business_metric_creation(self):
        """Test BusinessMetric creation"""
        metric = BusinessMetric(
            name="test_metric",
            description="Test metric for unit testing",
            metric_type=MetricType.COUNTER,
            labels=["label1", "label2"],
            unit="count"
        )
        
        assert metric.name == "test_metric"
        assert metric.description == "Test metric for unit testing"
        assert metric.metric_type == MetricType.COUNTER
        assert metric.labels == ["label1", "label2"]
        assert metric.unit == "count"
    
    def test_business_metric_defaults(self):
        """Test BusinessMetric with default values"""
        metric = BusinessMetric(
            name="default_metric",
            description="Default test metric",
            metric_type=MetricType.GAUGE
        )
        
        assert metric.labels == []
        assert metric.unit == ""


class TestBusinessMetricsCollector:
    """Test suite for BusinessMetricsCollector"""
    
    @pytest.fixture
    async def metrics_collector_instance(self):
        """Create metrics collector for testing"""
        with patch('app.monitoring.business_metrics.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            collector = BusinessMetricsCollector()
            collector._redis_client = mock_client
            return collector
    
    @pytest.mark.asyncio
    async def test_record_mvp_generation(self, metrics_collector_instance):
        """Test MVP generation metrics recording"""
        status = "completed"
        model_type = "nextjs"
        execution_profile = "standard"
        duration = 1800.5  # 30 minutes
        quality_scores = {
            "code_quality": 85.0,
            "ui_ux": 90.0,
            "performance": 78.5
        }
        
        await metrics_collector_instance.record_mvp_generation(
            status=status,
            model_type=model_type,
            execution_profile=execution_profile,
            duration=duration,
            quality_scores=quality_scores
        )
        
        # Verify Prometheus metrics were called
        metrics_collector_instance._prometheus_metrics["mvp_generated_total"].labels.assert_called()
        metrics_collector_instance._prometheus_metrics["mvp_generation_duration"].labels.assert_called()
        
        # Verify Redis storage
        metrics_collector_instance._redis_client.lpush.assert_called()
        metrics_collector_instance._redis_client.ltrim.assert_called()
    
    @pytest.mark.asyncio
    async def test_record_user_session(self, metrics_collector_instance):
        """Test user session metrics recording"""
        user_type = "premium"
        session_duration = 1800.0  # 30 minutes
        features_used = ["mvp_generation", "idea_scoring", "market_analysis"]
        
        await metrics_collector_instance.record_user_session(
            user_type=user_type,
            session_duration=session_duration,
            features_used=features_used
        )
        
        # Verify Prometheus metrics
        metrics_collector_instance._prometheus_metrics["user_sessions_total"].labels.assert_called()
        metrics_collector_instance._prometheus_metrics["session_duration"].labels.assert_called()
        
        # Verify feature usage tracking
        expected_calls = len(features_used)
        actual_calls = metrics_collector_instance._prometheus_metrics["feature_usage"].labels.call_count
        assert actual_calls >= expected_calls
    
    @pytest.mark.asyncio
    async def test_record_idea_generation(self, metrics_collector_instance):
        """Test idea generation metrics recording"""
        source = "market_research"
        icp_aligned = True
        actionability_score = 75.5
        total_ideas = 15
        
        await metrics_collector_instance.record_idea_generation(
            source=source,
            icp_aligned=icp_aligned,
            actionability_score=actionability_score,
            total_ideas=total_ideas
        )
        
        # Verify Prometheus metrics
        metrics_collector_instance._prometheus_metrics["ideas_generated_total"].labels.assert_called_with(
            source=source,
            icp_aligned="true"
        )
        metrics_collector_instance._prometheus_metrics["idea_actionability_score"].labels.assert_called()
    
    @pytest.mark.asyncio
    async def test_record_llm_call(self, metrics_collector_instance):
        """Test LLM call metrics recording"""
        model = "llama3.1:8b"
        endpoint = "/generate"
        status = "success"
        duration = 5.2
        
        await metrics_collector_instance.record_llm_call(
            model=model,
            endpoint=endpoint,
            status=status,
            duration=duration
        )
        
        # Verify API call counter
        metrics_collector_instance._prometheus_metrics["llm_api_calls_total"].labels.assert_called_with(
            model=model,
            endpoint=endpoint,
            status=status
        )
        
        # Verify response duration (only for successful calls)
        metrics_collector_instance._prometheus_metrics["llm_response_duration"].labels.assert_called_with(
            model=model,
            endpoint=endpoint
        )
    
    @pytest.mark.asyncio
    async def test_update_cache_hit_rate(self, metrics_collector_instance):
        """Test cache hit rate update"""
        cache_type = "llm_cache"
        hit_rate = 85.5
        
        await metrics_collector_instance.update_cache_hit_rate(cache_type, hit_rate)
        
        metrics_collector_instance._prometheus_metrics["cache_hit_rate"].labels.assert_called_with(
            cache_type=cache_type
        )
        metrics_collector_instance._prometheus_metrics["cache_hit_rate"].labels.return_value.set.assert_called_with(
            hit_rate
        )
    
    @pytest.mark.asyncio
    async def test_get_mvp_analytics(self, metrics_collector_instance):
        """Test MVP analytics retrieval"""
        # Mock Redis data
        mock_events = [
            {
                "timestamp": "2024-01-01T10:00:00",
                "event_type": "mvp_generation",
                "status": "completed",
                "model_type": "nextjs",
                "execution_profile": "standard",
                "duration": 1800.0,
                "quality_scores": {"code_quality": 85.0, "ui_ux": 90.0}
            },
            {
                "timestamp": "2024-01-01T11:00:00",
                "event_type": "mvp_generation",
                "status": "completed",
                "model_type": "react",
                "execution_profile": "quick",
                "duration": 900.0,
                "quality_scores": {"code_quality": 80.0, "ui_ux": 85.0}
            },
            {
                "timestamp": "2024-01-01T12:00:00",
                "event_type": "mvp_generation",
                "status": "failed",
                "model_type": "vue",
                "execution_profile": "standard",
                "duration": 2400.0,
                "quality_scores": {"code_quality": 70.0, "ui_ux": 75.0}
            }
        ]
        
        metrics_collector_instance._redis_client.lrange.return_value = [
            json.dumps(event) for event in mock_events
        ]
        
        analytics = await metrics_collector_instance.get_mvp_analytics("24h")
        
        assert analytics["time_period"] == "24h"
        assert analytics["total_mvps"] == 3
        assert analytics["successful_mvps"] == 2
        assert analytics["success_rate"] == 66.67  # 2/3 * 100
        assert analytics["average_duration_seconds"] == 1700.0  # (1800 + 900 + 2400) / 3
        assert "quality_scores" in analytics
    
    @pytest.mark.asyncio
    async def test_get_user_analytics(self, metrics_collector_instance):
        """Test user analytics retrieval"""
        # Mock Redis data
        mock_events = [
            {
                "timestamp": "2024-01-01T10:00:00",
                "event_type": "user_session",
                "user_type": "premium",
                "session_duration": 3600.0,
                "features_used": ["mvp_generation", "idea_scoring"]
            },
            {
                "timestamp": "2024-01-01T11:00:00",
                "event_type": "user_session",
                "user_type": "free",
                "session_duration": 1800.0,
                "features_used": ["idea_scoring"]
            },
            {
                "timestamp": "2024-01-01T12:00:00",
                "event_type": "user_session",
                "user_type": "premium",
                "session_duration": 2400.0,
                "features_used": ["mvp_generation", "market_analysis", "idea_scoring"]
            }
        ]
        
        metrics_collector_instance._redis_client.lrange.return_value = [
            json.dumps(event) for event in mock_events
        ]
        
        analytics = await metrics_collector_instance.get_user_analytics("24h")
        
        assert analytics["time_period"] == "24h"
        assert analytics["total_sessions"] == 3
        assert analytics["average_session_duration_seconds"] == 2600.0  # (3600 + 1800 + 2400) / 3
        assert analytics["user_type_distribution"]["premium"] == 2
        assert analytics["user_type_distribution"]["free"] == 1
        assert "mvp_generation" in analytics["feature_usage"]
        assert "idea_scoring" in analytics["feature_usage"]
    
    @pytest.mark.asyncio
    async def test_get_performance_summary(self, metrics_collector_instance):
        """Test performance summary retrieval"""
        summary = await metrics_collector_instance.get_performance_summary()
        
        assert "cache_hit_rates" in summary
        assert "system_load" in summary
        assert "error_rates" in summary
        assert "active_users" in summary
        
        # Verify structure
        assert isinstance(summary["cache_hit_rates"], dict)
        assert isinstance(summary["system_load"], dict)
        assert isinstance(summary["error_rates"], dict)
        assert isinstance(summary["active_users"], dict)


class TestTrackMVPGenerationDecorator:
    """Test suite for MVP generation tracking decorator"""
    
    @pytest.mark.asyncio
    async def test_track_mvp_generation_decorator(self):
        """Test MVP generation tracking decorator"""
        with patch('app.monitoring.business_metrics.metrics_collector') as mock_collector:
            mock_collector.record_mvp_generation = AsyncMock()
            
            @track_mvp_generation(execution_profile="quick")
            async def mock_mvp_function():
                await asyncio.sleep(0.1)
                return {
                    "model_type": "nextjs",
                    "quality_scores": {"code_quality": 85.0}
                }
            
            result = await mock_mvp_function()
            
            # Verify function result is returned
            assert result["model_type"] == "nextjs"
            assert result["quality_scores"]["code_quality"] == 85.0
            
            # Verify metrics were recorded
            mock_collector.record_mvp_generation.assert_called_once()
            call_args = mock_collector.record_mvp_generation.call_args[1]
            
            assert call_args["execution_profile"] == "quick"
            assert call_args["status"] == "completed"
            assert call_args["model_type"] == "nextjs"
            assert call_args["quality_scores"]["code_quality"] == 85.0
            assert call_args["duration"] > 0
    
    @pytest.mark.asyncio
    async def test_track_mvp_generation_decorator_failure(self):
        """Test MVP generation tracking decorator with failure"""
        with patch('app.monitoring.business_metrics.metrics_collector') as mock_collector:
            mock_collector.record_mvp_generation = AsyncMock()
            
            @track_mvp_generation(execution_profile="standard")
            async def failing_mvp_function():
                await asyncio.sleep(0.1)
                raise ValueError("Test failure")
            
            with pytest.raises(ValueError):
                await failing_mvp_function()
            
            # Verify metrics were recorded with failure status
            mock_collector.record_mvp_generation.assert_called_once()
            call_args = mock_collector.record_mvp_generation.call_args[1]
            
            assert call_args["execution_profile"] == "standard"
            assert call_args["status"] == "failed"
            assert call_args["model_type"] == "unknown"
            assert call_args["quality_scores"] == {}


class TestMetricsIntegration:
    """Integration tests for business metrics"""
    
    @pytest.mark.asyncio
    async def test_metrics_end_to_end_flow(self):
        """Test complete metrics flow from generation to analytics"""
        with patch('app.monitoring.business_metrics.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            collector = BusinessMetricsCollector()
            collector._redis_client = mock_client
            
            # Simulate MVP generation
            await collector.record_mvp_generation(
                status="completed",
                model_type="nextjs",
                execution_profile="standard",
                duration=1800.0,
                quality_scores={"code_quality": 85.0, "ui_ux": 90.0}
            )
            
            # Simulate user session
            await collector.record_user_session(
                user_type="premium",
                session_duration=3600.0,
                features_used=["mvp_generation", "idea_scoring"]
            )
            
            # Simulate LLM calls
            await collector.record_llm_call(
                model="llama3.1:8b",
                endpoint="/generate",
                status="success",
                duration=5.2
            )
            
            # Verify Redis operations
            assert mock_client.lpush.call_count >= 3  # One for each event type
            assert mock_client.ltrim.call_count >= 3
    
    @pytest.mark.asyncio
    async def test_metrics_error_handling(self):
        """Test metrics collection error handling"""
        with patch('app.monitoring.business_metrics.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            # Simulate Redis error
            mock_client.lpush.side_effect = Exception("Redis connection failed")
            
            collector = BusinessMetricsCollector()
            collector._redis_client = mock_client
            
            # Should not raise exception
            await collector.record_mvp_generation(
                status="completed",
                model_type="nextjs",
                execution_profile="standard",
                duration=1800.0,
                quality_scores={}
            )
            
            # Prometheus metrics should still be called
            collector._prometheus_metrics["mvp_generated_total"].labels.assert_called()
    
    @pytest.mark.asyncio
    async def test_metrics_performance(self):
        """Test metrics collection performance"""
        with patch('app.monitoring.business_metrics.redis.from_url') as mock_redis:
            mock_client = AsyncMock()
            mock_redis.return_value = mock_client
            
            collector = BusinessMetricsCollector()
            collector._redis_client = mock_client
            
            # Measure performance of multiple metric recordings
            start_time = time.time()
            
            tasks = []
            for i in range(100):
                task = collector.record_mvp_generation(
                    status="completed",
                    model_type=f"model_{i}",
                    execution_profile="standard",
                    duration=1800.0 + i,
                    quality_scores={"code_quality": 80.0 + i}
                )
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Should complete within reasonable time (under 5 seconds for 100 recordings)
            assert duration < 5.0
            
            # Verify all operations were called
            assert mock_client.lpush.call_count == 100
            assert mock_client.ltrim.call_count == 100


@pytest.mark.asyncio
async def test_global_metrics_collector():
    """Test global metrics collector instance"""
    # Verify global instance exists
    assert metrics_collector is not None
    assert isinstance(metrics_collector, BusinessMetricsCollector)
    
    # Test that it has the expected metrics
    assert hasattr(metrics_collector, '_prometheus_metrics')
    assert 'mvp_generated_total' in metrics_collector._prometheus_metrics
    assert 'user_sessions_total' in metrics_collector._prometheus_metrics
    assert 'ideas_generated_total' in metrics_collector._prometheus_metrics
