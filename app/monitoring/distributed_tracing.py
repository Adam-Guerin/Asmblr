"""
Système de tracing distribué pour Asmblr avec OpenTelemetry et Jaeger
"""

import asyncio
import time
import uuid
from typing import Dict, Any, Optional, List, Callable
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from enum import Enum
import json
from functools import wraps
import logging

try:
    from opentelemetry import trace, baggage, context
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.semantic_conventions.resource import ResourceAttributes
    from opentelemetry.propagate import inject, extract
    from opentelemetry.trace import SpanKind, Status, StatusCode
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    trace = None
    baggage = None

from app.core.config import Settings
from app.monitoring.structured_logger import StructuredLogger


class SpanKind(Enum):
    """Types de spans pour Asmblr"""
    HTTP = "http"
    DATABASE = "database"
    CACHE = "cache"
    LLM = "llm"
    PIPELINE = "pipeline"
    BUSINESS = "business"
    SYSTEM = "system"


@dataclass
class SpanContext:
    """Contexte de span pour Asmblr"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    baggage: Dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    status: str = "ok"
    error: Optional[str] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)


class DistributedTracer:
    """Gestionnaire de tracing distribué pour Asmblr"""
    
    def __init__(self, settings: Settings, logger: StructuredLogger):
        self.settings = settings
        self.logger = logger
        self.enabled = OPENTELEMETRY_AVAILABLE and settings.enable_distributed_tracing
        self.tracer = None
        self.span_processor = None
        self.exporter = None
        
        if self.enabled:
            self._setup_opentelemetry()
        else:
            logger.system("Distributed tracing disabled (OpenTelemetry not available)")
    
    def _setup_opentelemetry(self):
        """Configurer OpenTelemetry"""
        try:
            # Configurer le resource
            resource = Resource.create({
                ResourceAttributes.SERVICE_NAME: "asmblr",
                ResourceAttributes.SERVICE_VERSION: "1.0.0",
                ResourceAttributes.DEPLOYMENT_ENVIRONMENT: "development"
            })
            
            # Configurer le TracerProvider
            trace.set_tracer_provider(TracerProvider(resource=resource))
            self.tracer = trace.get_tracer(__name__)
            
            # Configurer Jaeger exporter
            jaeger_endpoint = getattr(self.settings, 'jaeger_endpoint', 'http://localhost:14268/api/traces')
            self.exporter = JaegerExporter(
                endpoint=jaeger_endpoint,
                collector_endpoint=jaeger_endpoint
            )
            
            # Configurer le span processor
            self.span_processor = BatchSpanProcessor(self.exporter)
            trace.get_tracer_provider().add_span_processor(self.span_processor)
            
            self.logger.system("Distributed tracing initialized with Jaeger")
            
        except Exception as e:
            self.logger.error(f"Failed to setup OpenTelemetry: {e}")
            self.enabled = False
    
    async def start(self):
        """Démarrer le tracing"""
        if self.enabled:
            self.logger.system("Distributed tracing started")
    
    async def shutdown(self):
        """Arrêter proprement le tracing"""
        if self.span_processor:
            self.span_processor.shutdown()
        if self.exporter:
            self.exporter.shutdown()
        self.logger.system("Distributed tracing shutdown")
    
    @contextmanager
    def trace_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.BUSINESS,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Contexte pour tracer une opération"""
        if not self.enabled:
            yield MockSpan()
            return
        
        span = self.tracer.start_span(
            name=name,
            kind=trace.SpanKind.HTTP if kind == SpanKind.HTTP else trace.SpanKind.INTERNAL
        )
        
        # Ajouter les attributs
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
        
        # Ajouter les tags standards
        span.set_attribute("asmblr.span.kind", kind.value)
        span.set_attribute("asmblr.service", "asmblr-api")
        
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise
        finally:
            span.end()
    
    @asynccontextmanager
    async def trace_async_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.BUSINESS,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """Contexte async pour tracer une opération"""
        if not self.enabled:
            yield MockSpan()
            return
        
        span = self.tracer.start_span(
            name=name,
            kind=trace.SpanKind.HTTP if kind == SpanKind.HTTP else trace.SpanKind.INTERNAL
        )
        
        # Ajouter les attributs
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
        
        span.set_attribute("asmblr.span.kind", kind.value)
        span.set_attribute("asmblr.service", "asmblr-api")
        
        try:
            yield span
            span.set_status(Status(StatusCode.OK))
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise
        finally:
            span.end()
    
    def inject_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Injecter le contexte de tracing dans les headers HTTP"""
        if not self.enabled:
            return headers
        
        inject(headers)
        return headers
    
    def extract_headers(self, headers: Dict[str, str]) -> Optional[SpanContext]:
        """Extraire le contexte de tracing des headers HTTP"""
        if not self.enabled:
            return None
        
        ctx = extract(headers)
        if ctx:
            span = trace.get_current_span(ctx)
            return SpanContext(
                trace_id=format(span.get_trace_id(), '032x'),
                span_id=format(span.get_span_id(), '016x')
            )
        return None
    
    def get_current_span(self):
        """Obtenir le span actuel"""
        if not self.enabled:
            return MockSpan()
        return trace.get_current_span()
    
    def add_baggage(self, key: str, value: str):
        """Ajouter du baggage au contexte actuel"""
        if self.enabled and baggage:
            baggage.set_baggage(key, value)
    
    def get_baggage(self, key: str) -> Optional[str]:
        """Obtenir une valeur du baggage"""
        if self.enabled and baggage:
            return baggage.get_baggage(key)
        return None


class MockSpan:
    """Mock span pour quand le tracing est désactivé"""
    
    def set_attribute(self, key: str, value: str):
        pass
    
    def set_status(self, status):
        pass
    
    def record_exception(self, exception):
        pass
    
    def end(self):
        pass
    
    def get_span_context(self):
        return type('Context', (), {'trace_id': '0', 'span_id': '0'})()
    
    def add_event(self, name: str, attributes: Dict[str, Any] = None):
        pass


# Décorateurs pour le tracing
def trace_function(
    name: Optional[str] = None,
    kind: SpanKind = SpanKind.BUSINESS,
    attributes: Optional[Dict[str, Any]] = None
):
    """Décorateur pour tracer une fonction"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = get_global_tracer()
            span_name = name or f"{func.__module__}.{func.__name__}"
            
            with tracer.trace_span(span_name, kind, attributes):
                return func(*args, **kwargs)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = get_global_tracer()
            span_name = name or f"{func.__module__}.{func.__name__}"
            
            async with tracer.trace_async_span(span_name, kind, attributes):
                return await func(*args, **kwargs)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def trace_http_request(method: str, path: str):
    """Décorateur pour tracer les requêtes HTTP"""
    return trace_function(
        name=f"http.{method.lower()}.{path}",
        kind=SpanKind.HTTP,
        attributes={
            "http.method": method,
            "http.url": path,
            "http.target": path
        }
    )


def trace_llm_request(model: str, operation: str):
    """Décorateur pour tracer les requêtes LLM"""
    return trace_function(
        name=f"llm.{operation}",
        kind=SpanKind.LLM,
        attributes={
            "llm.model": model,
            "llm.operation": operation
        }
    )


def trace_pipeline_operation(pipeline_type: str, operation: str):
    """Décorateur pour tracer les opérations de pipeline"""
    return trace_function(
        name=f"pipeline.{pipeline_type}.{operation}",
        kind=SpanKind.PIPELINE,
        attributes={
            "pipeline.type": pipeline_type,
            "pipeline.operation": operation
        }
    )


def trace_cache_operation(cache_type: str, operation: str):
    """Décorateur pour tracer les opérations de cache"""
    return trace_function(
        name=f"cache.{cache_type}.{operation}",
        kind=SpanKind.CACHE,
        attributes={
            "cache.type": cache_type,
            "cache.operation": operation
        }
    )


# Instance globale du tracer
_global_tracer: Optional[DistributedTracer] = None


def initialize_tracing(settings: Settings, logger: StructuredLogger) -> DistributedTracer:
    """Initialiser le tracing distribué globalement"""
    global _global_tracer
    _global_tracer = DistributedTracer(settings, logger)
    return _global_tracer


def get_global_tracer() -> Optional[DistributedTracer]:
    """Obtenir l'instance globale du tracer"""
    return _global_tracer


# Middleware FastAPI pour le tracing
class TracingMiddleware:
    """Middleware FastAPI pour le tracing distribué"""
    
    def __init__(self, app, tracer: DistributedTracer):
        self.app = app
        self.tracer = tracer
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Extraire les headers
        headers = dict(scope.get("headers", []))
        string_headers = {k.decode(): v.decode() for k, v in headers.items()}
        
        # Extraire le contexte de tracing
        trace_context = self.tracer.extract_headers(string_headers)
        
        # Créer un span pour la requête
        method = scope.get("method", "unknown")
        path = scope.get("path", "unknown")
        
        with self.tracer.trace_span(
            name=f"http.{method.lower()}.{path}",
            kind=SpanKind.HTTP,
            attributes={
                "http.method": method,
                "http.url": path,
                "http.target": path,
                "http.scheme": scope.get("scheme", "http"),
                "http.host": scope.get("server", ("unknown", ""))[0],
                "http.user_agent": string_headers.get("user-agent", ""),
                "http.remote_addr": scope.get("client", ("unknown", ""))[0]
            }
        ):
            await self.app(scope, receive, send)


# Fonctions utilitaires pour le tracing
def add_trace_attribute(key: str, value: Any):
    """Ajouter un attribut au span actuel"""
    tracer = get_global_tracer()
    span = tracer.get_current_span()
    span.set_attribute(key, str(value))


def add_trace_event(name: str, attributes: Dict[str, Any] = None):
    """Ajouter un événement au span actuel"""
    tracer = get_global_tracer()
    span = tracer.get_current_span()
    span.add_event(name, attributes or {})


def set_trace_error(error: Exception):
    """Marquer le span actuel comme erreur"""
    tracer = get_global_tracer()
    span = tracer.get_current_span()
    span.set_status(Status(StatusCode.ERROR, str(error)))
    span.record_exception(error)


def get_trace_id() -> Optional[str]:
    """Obtenir le trace ID actuel"""
    tracer = get_global_tracer()
    span = tracer.get_current_span()
    ctx = span.get_span_context()
    return format(ctx.trace_id, '032x') if ctx else None


def get_span_id() -> Optional[str]:
    """Obtenir le span ID actuel"""
    tracer = get_global_tracer()
    span = tracer.get_current_span()
    ctx = span.get_span_context()
    return format(ctx.span_id, '016x') if ctx else None


# Intégration avec le logger structuré
class TraceLoggerAdapter:
    """Adaptateur pour intégrer le tracing avec le logger structuré"""
    
    def __init__(self, tracer: DistributedTracer, logger: StructuredLogger):
        self.tracer = tracer
        self.logger = logger
    
    def log_with_trace(
        self,
        level: str,
        message: str,
        extra_data: Optional[Dict[str, Any]] = None
    ):
        """Logger avec les informations de tracing"""
        trace_id = get_trace_id()
        span_id = get_span_id()
        
        # Ajouter les informations de tracing aux données du logger
        trace_data = {}
        if trace_id:
            trace_data["trace_id"] = trace_id
        if span_id:
            trace_data["span_id"] = span_id
        
        # Combiner avec les données supplémentaires
        if extra_data:
            trace_data.update(extra_data)
        
        # Logger avec les données de tracing
        log_method = getattr(self.logger, level)
        log_method(message, **trace_data)


# Configuration pour le développement
def configure_tracing_for_development(settings: Settings) -> Settings:
    """Configurer les paramètres de tracing pour le développement"""
    if not hasattr(settings, 'jaeger_endpoint'):
        settings.jaeger_endpoint = 'http://localhost:14268/api/traces'
    if not hasattr(settings, 'enable_distributed_tracing'):
        settings.enable_distributed_tracing = True
    return settings


# Export des fonctions principales
__all__ = [
    'DistributedTracer',
    'SpanKind',
    'SpanContext',
    'initialize_tracing',
    'get_global_tracer',
    'trace_function',
    'trace_http_request',
    'trace_llm_request',
    'trace_pipeline_operation',
    'trace_cache_operation',
    'TracingMiddleware',
    'add_trace_attribute',
    'add_trace_event',
    'set_trace_error',
    'get_trace_id',
    'get_span_id',
    'TraceLoggerAdapter',
    'configure_tracing_for_development'
]
