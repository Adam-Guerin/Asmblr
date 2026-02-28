"""
Advanced Distributed Tracing for Asmblr
OpenTelemetry integration with Jaeger and comprehensive observability
"""

import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from contextlib import asynccontextmanager
from opentelemetry import trace, baggage, context
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.semconv.trace import SpanAttributes
import jaeger_client

logger = logging.getLogger(__name__)

@dataclass
class TraceSpan:
    """Trace span data structure"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: datetime
    end_time: datetime
    duration_ms: float
    status: str
    tags: Dict[str, Any]
    logs: List[Dict[str, Any]]
    service_name: str
    component: str

@dataclass
class TraceMetrics:
    """Tracing metrics"""
    total_spans: int
    error_spans: int
    average_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    services: Dict[str, int]
    operations: Dict[str, int]
    error_rate: float

class AdvancedTracer:
    """Advanced distributed tracing with OpenTelemetry"""
    
    def __init__(self, service_name: str = "asmblr", jaeger_endpoint: str = "http://localhost:14268/api/traces"):
        self.service_name = service_name
        self.jaeger_endpoint = jaeger_endpoint
        self.tracer_provider = None
        self.span_storage: List[TraceSpan] = []
        self._initialize_tracing()
    
    def _initialize_tracing(self):
        """Initialize OpenTelemetry tracing"""
        # Create resource
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: self.service_name,
            ResourceAttributes.SERVICE_VERSION: "2.0.0",
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: "production"
        })
        
        # Create tracer provider
        self.tracer_provider = TracerProvider(resource=resource)
        
        # Create Jaeger exporter
        jaeger_exporter = JaegerExporter(
            endpoint=self.jaeger_endpoint,
            collector_endpoint=self.jaeger_endpoint,
        )
        
        # Add span processor
        span_processor = BatchSpanProcessor(jaeger_exporter)
        self.tracer_provider.add_span_processor(span_processor)
        
        # Set global tracer provider
        trace.set_tracer_provider(self.tracer_provider)
        
        # Set global propagator
        set_global_textmap(B3MultiFormat())
        
        # Instrument libraries
        self._instrument_libraries()
        
        logger.info(f"Advanced tracing initialized for {self.service_name}")
    
    def _instrument_libraries(self):
        """Instrument common libraries"""
        try:
            # HTTP client instrumentation
            HTTPXClientInstrumentor().instrument()
            
            # Database instrumentation
            SQLAlchemyInstrumentor().instrument()
            
            # Redis instrumentation
            RedisInstrumentor().instrument()
            
            logger.info("Library instrumentation completed")
            
        except Exception as e:
            logger.error(f"Error instrumenting libraries: {e}")
    
    def get_tracer(self, name: str) -> trace.Tracer:
        """Get tracer for specific component"""
        return trace.get_tracer(name)
    
    @asynccontextmanager
    async def trace_async(self, operation_name: str, **attributes):
        """Async tracing context manager"""
        tracer = self.get_tracer(self.service_name)
        
        with tracer.start_as_current_span(operation_name) as span:
            # Add attributes
            for key, value in attributes.items():
                span.set_attribute(key, value)
            
            # Add service info
            span.set_attribute(SpanAttributes.SERVICE_NAME, self.service_name)
            span.set_attribute("component.name", self.service_name)
            
            start_time = time.time()
            
            try:
                yield span
                span.set_status(trace.Status(trace.StatusCode.OK))
            except Exception as e:
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
            finally:
                end_time = time.time()
                duration_ms = (end_time - start_time) * 1000
                
                # Store span data
                span_data = TraceSpan(
                    trace_id=format(span.get_trace_id(), 'x'),
                    span_id=format(span.get_span_id(), 'x'),
                    parent_span_id=format(span.parent.span_id) if span.parent else None,
                    operation_name=operation_name,
                    start_time=datetime.fromtimestamp(start_time),
                    end_time=datetime.fromtimestamp(end_time),
                    duration_ms=duration_ms,
                    status="OK" if span.status.status_code == trace.StatusCode.OK else "ERROR",
                    tags=dict(span.attributes),
                    logs=[],
                    service_name=self.service_name,
                    component=self.service_name
                )
                self.span_storage.append(span_data)
    
    def trace_function(self, operation_name: str = None):
        """Decorator for function tracing"""
        def decorator(func):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            
            if asyncio.iscoroutinefunction(func):
                async def async_wrapper(*args, **kwargs):
                    tracer = self.get_tracer(self.service_name)
                    
                    with tracer.start_as_current_span(name) as span:
                        # Add function attributes
                        span.set_attribute("function.name", func.__name__)
                        span.set_attribute("function.module", func.__module__)
                        
                        try:
                            result = await func(*args, **kwargs)
                            span.set_status(trace.Status(trace.StatusCode.OK))
                            return result
                        except Exception as e:
                            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                            span.record_exception(e)
                            raise
                
                return async_wrapper
            else:
                def sync_wrapper(*args, **kwargs):
                    tracer = self.get_tracer(self.service_name)
                    
                    with tracer.start_as_current_span(name) as span:
                        # Add function attributes
                        span.set_attribute("function.name", func.__name__)
                        span.set_attribute("function.module", func.__module__)
                        
                        try:
                            result = func(*args, **kwargs)
                            span.set_status(trace.Status(trace.StatusCode.OK))
                            return result
                        except Exception as e:
                            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                            span.record_exception(e)
                            raise
                
                return sync_wrapper
        
        return decorator
    
    def add_span_event(self, name: str, **attributes):
        """Add event to current span"""
        span = trace.get_current_span()
        if span:
            span.add_event(name, attributes=attributes)
    
    def set_span_attribute(self, key: str, value: Any):
        """Set attribute on current span"""
        span = trace.get_current_span()
        if span:
            span.set_attribute(key, value)
    
    def get_trace_metrics(self, time_range: timedelta = timedelta(hours=1)) -> TraceMetrics:
        """Get tracing metrics"""
        cutoff_time = datetime.now() - time_range
        recent_spans = [s for s in self.span_storage if s.start_time >= cutoff_time]
        
        if not recent_spans:
            return TraceMetrics(
                total_spans=0,
                error_spans=0,
                average_duration_ms=0.0,
                p95_duration_ms=0.0,
                p99_duration_ms=0.0,
                services={},
                operations={},
                error_rate=0.0
            )
        
        total_spans = len(recent_spans)
        error_spans = len([s for s in recent_spans if s.status == "ERROR"])
        durations = [s.duration_ms for s in recent_spans]
        
        # Calculate percentiles
        sorted_durations = sorted(durations)
        p95_duration = sorted_durations[int(len(sorted_durations) * 0.95)] if sorted_durations else 0
        p99_duration = sorted_durations[int(len(sorted_durations) * 0.99)] if sorted_durations else 0
        
        # Count services and operations
        services = {}
        operations = {}
        for span in recent_spans:
            services[span.service_name] = services.get(span.service_name, 0) + 1
            operations[span.operation_name] = operations.get(span.operation_name, 0) + 1
        
        return TraceMetrics(
            total_spans=total_spans,
            error_spans=error_spans,
            average_duration_ms=sum(durations) / len(durations) if durations else 0,
            p95_duration_ms=p95_duration,
            p99_duration_ms=p99_duration,
            services=services,
            operations=operations,
            error_rate=error_spans / total_spans if total_spans > 0 else 0
        )

class TraceAnalyzer:
    """Advanced trace analysis and insights"""
    
    def __init__(self, tracer: AdvancedTracer):
        self.tracer = tracer
        self.jaeger_query = "http://localhost:16686"
    
    def analyze_service_dependencies(self) -> Dict[str, List[str]]:
        """Analyze service dependencies from traces"""
        dependencies = {}
        
        for span in self.tracer.span_storage:
            service = span.service_name
            
            # Extract service calls from span tags
            if "http.url" in span.tags:
                url = span.tags["http.url"]
                # Extract service from URL (simplified)
                called_service = self._extract_service_from_url(url)
                if called_service and called_service != service:
                    if service not in dependencies:
                        dependencies[service] = []
                    dependencies[service].append(called_service)
        
        return dependencies
    
    def _extract_service_from_url(self, url: str) -> Optional[str]:
        """Extract service name from URL"""
        # Simplified service extraction
        if "api.openai.com" in url:
            return "openai-api"
        elif "huggingface.co" in url:
            return "huggingface-api"
        elif "redis" in url:
            return "redis"
        elif "postgres" in url or "postgresql" in url:
            return "postgres"
        return None
    
    def find_performance_bottlenecks(self, threshold_ms: float = 1000.0) -> List[Dict[str, Any]]:
        """Find performance bottlenecks"""
        bottlenecks = []
        
        for span in self.tracer.span_storage:
            if span.duration_ms > threshold_ms:
                bottlenecks.append({
                    "operation": span.operation_name,
                    "service": span.service_name,
                    "duration_ms": span.duration_ms,
                    "trace_id": span.trace_id,
                    "timestamp": span.start_time,
                    "tags": span.tags
                })
        
        return sorted(bottlenecks, key=lambda x: x["duration_ms"], reverse=True)
    
    def analyze_error_patterns(self) -> Dict[str, Any]:
        """Analyze error patterns"""
        error_spans = [s for s in self.tracer.span_storage if s.status == "ERROR"]
        
        if not error_spans:
            return {"total_errors": 0, "error_types": {}, "services_with_errors": {}}
        
        # Group errors by type
        error_types = {}
        services_with_errors = {}
        
        for span in error_spans:
            service = span.service_name
            operation = span.operation_name
            
            services_with_errors[service] = services_with_errors.get(service, 0) + 1
            
            # Extract error type from operation name
            error_type = operation.split(".")[-1] if "." in operation else operation
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total_errors": len(error_spans),
            "error_rate": len(error_spans) / len(self.tracer.span_storage),
            "error_types": error_types,
            "services_with_errors": services_with_errors,
            "most_common_error": max(error_types.items(), key=lambda x: x[1])[0] if error_types else None
        }
    
    def generate_trace_report(self) -> Dict[str, Any]:
        """Generate comprehensive trace report"""
        metrics = self.tracer.get_trace_metrics()
        dependencies = self.analyze_service_dependencies()
        bottlenecks = self.find_performance_bottlenecks()
        error_patterns = self.analyze_error_patterns()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": asdict(metrics),
            "dependencies": dependencies,
            "bottlenecks": bottlenecks[:10],  # Top 10
            "error_patterns": error_patterns,
            "recommendations": self._generate_recommendations(metrics, bottlenecks, error_patterns)
        }
    
    def _generate_recommendations(self, metrics: TraceMetrics, 
                               bottlenecks: List[Dict[str, Any]], 
                               error_patterns: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        # Performance recommendations
        if metrics.average_duration_ms > 500:
            recommendations.append("Consider optimizing slow operations (avg duration > 500ms)")
        
        if metrics.p95_duration_ms > 2000:
            recommendations.append("P95 response time is high (>2s), investigate outliers")
        
        if metrics.error_rate > 0.05:  # 5%
            recommendations.append(f"Error rate is high ({metrics.error_rate:.1%}), investigate root causes")
        
        # Bottleneck recommendations
        if bottlenecks:
            top_bottleneck = bottlenecks[0]
            recommendations.append(f"Address top bottleneck: {top_bottleneck['operation']} ({top_bottleneck['duration_ms']:.1f}ms)")
        
        # Error pattern recommendations
        if error_patterns.get("most_common_error"):
            recommendations.append(f"Fix most common error: {error_patterns['most_common_error']}")
        
        # Service dependency recommendations
        dependencies = self.analyze_service_dependencies()
        if len(dependencies) > 5:
            recommendations.append("Consider reducing service dependencies for better resilience")
        
        return recommendations

class TraceDashboard:
    """Trace dashboard data provider"""
    
    def __init__(self, tracer: AdvancedTracer, analyzer: TraceAnalyzer):
        self.tracer = tracer
        self.analyzer = analyzer
    
    def get_dashboard_data(self, time_range: timedelta = timedelta(hours=1)) -> Dict[str, Any]:
        """Get dashboard data"""
        metrics = self.tracer.get_trace_metrics(time_range)
        report = self.analyzer.generate_trace_report()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": asdict(metrics),
            "top_operations": self._get_top_operations(),
            "service_health": self._get_service_health(),
            "recent_traces": self._get_recent_traces(),
            "performance_trends": self._get_performance_trends(),
            "error_trends": self._get_error_trends()
        }
    
    def _get_top_operations(self) -> List[Dict[str, Any]]:
        """Get top operations by duration"""
        operations = {}
        
        for span in self.tracer.span_storage:
            op = span.operation_name
            if op not in operations:
                operations[op] = {
                    "count": 0,
                    "total_duration": 0,
                    "errors": 0
                }
            
            operations[op]["count"] += 1
            operations[op]["total_duration"] += span.duration_ms
            if span.status == "ERROR":
                operations[op]["errors"] += 1
        
        # Calculate averages and sort
        for op in operations:
            operations[op]["average_duration"] = operations[op]["total_duration"] / operations[op]["count"]
            operations[op]["error_rate"] = operations[op]["errors"] / operations[op]["count"]
        
        # Sort by average duration
        sorted_ops = sorted(operations.items(), key=lambda x: x[1]["average_duration"], reverse=True)
        
        return [
            {
                "operation": op,
                "count": data["count"],
                "average_duration": data["average_duration"],
                "error_rate": data["error_rate"]
            }
            for op, data in sorted_ops[:10]
        ]
    
    def _get_service_health(self) -> Dict[str, Any]:
        """Get service health metrics"""
        services = {}
        
        for span in self.tracer.span_storage:
            service = span.service_name
            if service not in services:
                services[service] = {
                    "total_spans": 0,
                    "error_spans": 0,
                    "total_duration": 0
                }
            
            services[service]["total_spans"] += 1
            services[service]["total_duration"] += span.duration_ms
            if span.status == "ERROR":
                services[service]["error_spans"] += 1
        
        # Calculate health metrics
        health = {}
        for service, data in services.items():
            health[service] = {
                "total_spans": data["total_spans"],
                "error_rate": data["error_spans"] / data["total_spans"],
                "average_duration": data["total_duration"] / data["total_spans"],
                "health_score": max(0, 100 - (data["error_spans"] / data["total_spans"] * 100))
            }
        
        return health
    
    def _get_recent_traces(self) -> List[Dict[str, Any]]:
        """Get recent traces"""
        recent_spans = sorted(self.tracer.span_storage, key=lambda x: x.start_time, reverse=True)[:50]
        
        return [
            {
                "trace_id": span.trace_id,
                "operation": span.operation_name,
                "service": span.service_name,
                "duration_ms": span.duration_ms,
                "status": span.status,
                "timestamp": span.start_time.isoformat()
            }
            for span in recent_spans
        ]
    
    def _get_performance_trends(self) -> Dict[str, List[float]]:
        """Get performance trends over time"""
        # Group spans by hour
        hourly_data = {}
        
        for span in self.tracer.span_storage:
            hour = span.start_time.replace(minute=0, second=0, microsecond=0)
            if hour not in hourly_data:
                hourly_data[hour] = []
            hourly_data[hour].append(span.duration_ms)
        
        # Calculate hourly averages
        trends = {}
        for hour, durations in sorted(hourly_data.items()):
            trends[hour.isoformat()] = sum(durations) / len(durations)
        
        return trends
    
    def _get_error_trends(self) -> Dict[str, List[float]]:
        """Get error trends over time"""
        # Group errors by hour
        hourly_errors = {}
        
        for span in self.tracer.span_storage:
            if span.status == "ERROR":
                hour = span.start_time.replace(minute=0, second=0, microsecond=0)
                if hour not in hourly_errors:
                    hourly_errors[hour] = 0
                hourly_errors[hour] += 1
        
        trends = {}
        for hour, count in sorted(hourly_errors.items()):
            trends[hour.isoformat()] = count
        
        return trends

# Global instances
advanced_tracer = AdvancedTracer()
trace_analyzer = TraceAnalyzer(advanced_tracer)
trace_dashboard = TraceDashboard(advanced_tracer, trace_analyzer)

# API endpoints
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/tracing", tags=["tracing"])

@router.get("/metrics")
async def get_trace_metrics():
    """Get tracing metrics"""
    try:
        metrics = advanced_tracer.get_trace_metrics()
        return asdict(metrics)
    except Exception as e:
        logger.error(f"Error getting trace metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard")
async def get_trace_dashboard():
    """Get trace dashboard data"""
    try:
        return trace_dashboard.get_dashboard_data()
    except Exception as e:
        logger.error(f"Error getting trace dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/report")
async def get_trace_report():
    """Get comprehensive trace report"""
    try:
        return trace_analyzer.generate_trace_report()
    except Exception as e:
        logger.error(f"Error generating trace report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dependencies")
async def get_service_dependencies():
    """Get service dependencies"""
    try:
        return trace_analyzer.analyze_service_dependencies()
    except Exception as e:
        logger.error(f"Error analyzing dependencies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bottlenecks")
async def get_performance_bottlenecks(threshold_ms: float = 1000.0):
    """Get performance bottlenecks"""
    try:
        return trace_analyzer.find_performance_bottlenecks(threshold_ms)
    except Exception as e:
        logger.error(f"Error finding bottlenecks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/errors")
async def get_error_patterns():
    """Get error patterns"""
    try:
        return trace_analyzer.analyze_error_patterns()
    except Exception as e:
        logger.error(f"Error analyzing errors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Integration with existing monitoring
from app.monitoring.apm_integration import record_business_event

def trace_pipeline_stage(stage_name: str, run_id: str):
    """Trace pipeline stage execution"""
    return advanced_tracer.trace_async(
        f"pipeline.{stage_name}",
        run_id=run_id,
        stage=stage_name,
        component="pipeline"
    )

def trace_llm_request(model: str, prompt_length: int, response_length: int):
    """Trace LLM request"""
    return advanced_tracer.trace_async(
        "llm.request",
        model=model,
        prompt_length=prompt_length,
        response_length=response_length,
        component="llm"
    )

def trace_database_operation(operation: str, table: str, query_time: float):
    """Trace database operation"""
    return advanced_tracer.trace_async(
        f"database.{operation}",
        table=table,
        query_time=query_time,
        component="database"
    )

def trace_api_call(method: str, endpoint: str, status_code: int, response_time: float):
    """Trace API call"""
    return advanced_tracer.trace_async(
        "api.call",
        method=method,
        endpoint=endpoint,
        status_code=status_code,
        response_time=response_time,
        component="api"
    )
