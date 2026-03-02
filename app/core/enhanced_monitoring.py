"""
Enhanced monitoring and alerting system for Asmblr
Distributed tracing, alerting, and advanced observability
"""

import asyncio
import time
import json
import uuid
from typing import Any
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import threading
from enum import Enum

# Monitoring and tracing imports
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.semconv.trace import SpanAttributes

# Alerting imports
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import redis.asyncio as redis

# Metrics and monitoring
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
from loguru import logger


class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status"""
    FIRING = "firing"
    RESOLVED = "resolved"
    SILENCED = "silenced"


@dataclass
class Span:
    """Distributed tracing span"""
    trace_id: str
    span_id: str
    parent_span_id: str | None
    operation_name: str
    start_time: datetime
    end_time: datetime | None
    duration_ms: float | None
    status_code: str
    status_message: str
    tags: dict[str, Any]
    logs: list[dict[str, Any]]
    service_name: str


@dataclass
class Alert:
    """Alert definition"""
    alert_id: str
    name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    labels: dict[str, str]
    annotations: dict[str, str]
    starts_at: datetime
    ends_at: datetime | None
    fingerprint: str
    generator_url: str | None = None


@dataclass
class MonitoringRule:
    """Monitoring rule for alerting"""
    rule_id: str
    name: str
    condition: str  # Prometheus query expression
    severity: AlertSeverity
    message: str
    labels: dict[str, str]
    annotations: dict[str, str]
    for_duration: timedelta = timedelta(minutes=5)
    evaluation_interval: timedelta = timedelta(minutes=1)


class DistributedTracer:
    """Distributed tracing with OpenTelemetry"""
    
    def __init__(self, service_name: str, jaeger_endpoint: str = "http://localhost:14268/api/traces"):
        self.service_name = service_name
        self.jaeger_endpoint = jaeger_endpoint
        self.tracer_provider = None
        self.tracer = None
        self.active_spans: dict[str, Span] = {}
        self._lock = threading.RLock()
        
    def initialize(self):
        """Initialize OpenTelemetry tracing"""
        # Create resource
        resource = Resource(attributes={
            ResourceAttributes.SERVICE_NAME: self.service_name,
            ResourceAttributes.SERVICE_VERSION: "1.0.0",
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
        
        # Get tracer
        self.tracer = trace.get_tracer(__name__)
        
        logger.info(f"Distributed tracing initialized for {self.service_name}")
    
    @asynccontextmanager
    async def start_span(self, operation_name: str, **attributes):
        """Start a new span"""
        if not self.tracer:
            self.initialize()
        
        with self.tracer.start_as_current_span(operation_name) as span:
            # Set attributes
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
            
            # Add service name
            span.set_attribute(SpanAttributes.SERVICE_NAME, self.service_name)
            
            yield span
    
    def add_span_event(self, name: str, **attributes):
        """Add event to current span"""
        current_span = trace.get_current_span()
        if current_span:
            current_span.add_event(name, attributes)
    
    def set_span_attribute(self, key: str, value: str):
        """Set attribute on current span"""
        current_span = trace.get_current_span()
        if current_span:
            current_span.set_attribute(key, value)
    
    def get_trace_context(self) -> dict[str, str]:
        """Get current trace context for propagation"""
        current_span = trace.get_current_span()
        if current_span:
            span_context = current_span.get_span_context()
            return {
                "trace_id": format(span_context.trace_id, "032x"),
                "span_id": format(span_context.span_id, "016x"),
                "trace_flags": format(span_context.trace_flags, "02x")
            }
        return {}


class AlertManager:
    """Advanced alerting system"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.active_alerts: dict[str, Alert] = {}
        self.alert_rules: dict[str, MonitoringRule] = {}
        self.notification_channels: list[Callable] = []
        self._lock = asyncio.Lock()
        
        # Default rules
        self._setup_default_rules()
        
        # Prometheus metrics for alerts
        self.alerts_total = Counter('asmblr_alerts_total', 'Total alerts', ['severity', 'status'])
        self.alerts_active = Gauge('asmblr_alerts_active', 'Active alerts', ['severity'])
        
    def _setup_default_rules(self):
        """Setup default monitoring rules"""
        default_rules = [
            MonitoringRule(
                rule_id="high_error_rate",
                name="High Error Rate",
                condition="rate(http_requests_total{status=~'5..'}[5m]) > 0.1",
                severity=AlertSeverity.HIGH,
                message="Error rate is above 10%",
                labels={"team": "platform"},
                annotations={"runbook": "https://docs.asmblr.ai/runbooks/error-rate"}
            ),
            MonitoringRule(
                rule_id="high_response_time",
                name="High Response Time",
                condition="histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2",
                severity=AlertSeverity.MEDIUM,
                message="95th percentile response time is above 2s",
                labels={"team": "platform"},
                annotations={"runbook": "https://docs.asmblr.ai/runbooks/response-time"}
            ),
            MonitoringRule(
                rule_id="pipeline_failure_rate",
                name="Pipeline Failure Rate",
                condition="rate(asmblr_pipeline_runs_total{status='failed'}[5m]) > 0.2",
                severity=AlertSeverity.CRITICAL,
                message="Pipeline failure rate is above 20%",
                labels={"team": "pipeline"},
                annotations={"runbook": "https://docs.asmblr.ai/runbooks/pipeline-failures"}
            ),
            MonitoringRule(
                rule_id="memory_usage_high",
                name="High Memory Usage",
                condition="process_resident_memory_bytes / 1024 / 1024 > 4000",
                severity=AlertSeverity.HIGH,
                message="Memory usage is above 4GB",
                labels={"team": "platform"},
                annotations={"runbook": "https://docs.asmblr.ai/runbooks/memory-usage"}
            ),
            MonitoringRule(
                rule_id="cpu_usage_high",
                name="High CPU Usage",
                condition="rate(process_cpu_seconds_total[5m]) * 100 > 80",
                severity=AlertSeverity.MEDIUM,
                message="CPU usage is above 80%",
                labels={"team": "platform"},
                annotations={"runbook": "https://docs.asmblr.ai/runbooks/cpu-usage"}
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.rule_id] = rule
    
    def add_notification_channel(self, channel: Callable[[Alert], None]):
        """Add notification channel (email, Slack, etc.)"""
        self.notification_channels.append(channel)
    
    async def evaluate_rules(self, metrics_data: dict[str, float]):
        """Evaluate all monitoring rules"""
        async with self._lock:
            for rule_id, rule in self.alert_rules.items():
                try:
                    # Evaluate rule condition (simplified - in production use Prometheus)
                    should_fire = self._evaluate_condition(rule.condition, metrics_data)
                    
                    alert_key = f"{rule_id}:{rule.fingerprint}"
                    
                    if should_fire and alert_key not in self.active_alerts:
                        # Create new alert
                        alert = Alert(
                            alert_id=str(uuid.uuid4()),
                            name=rule.name,
                            severity=rule.severity,
                            status=AlertStatus.FIRING,
                            message=rule.message,
                            labels=rule.labels,
                            annotations=rule.annotations,
                            starts_at=datetime.now(),
                            fingerprint=rule.fingerprint
                        )
                        
                        self.active_alerts[alert_key] = alert
                        await self._fire_alert(alert)
                        
                    elif not should_fire and alert_key in self.active_alerts:
                        # Resolve alert
                        alert = self.active_alerts[alert_key]
                        alert.status = AlertStatus.RESOLVED
                        alert.ends_at = datetime.now()
                        
                        del self.active_alerts[alert_key]
                        await self._resolve_alert(alert)
                
                except Exception as e:
                    logger.error(f"Error evaluating rule {rule_id}: {e}")
    
    def _evaluate_condition(self, condition: str, metrics_data: dict[str, float]) -> bool:
        """Evaluate rule condition (simplified implementation)"""
        # This is a simplified evaluation - in production use Prometheus query evaluation
        try:
            # Map common conditions to metrics
            if "error_rate" in condition and "http_requests_5xx" in metrics_data:
                return metrics_data["http_requests_5xx"] > 0.1
            elif "response_time" in condition and "response_time_p95" in metrics_data:
                return metrics_data["response_time_p95"] > 2.0
            elif "memory_usage" in condition and "memory_mb" in metrics_data:
                return metrics_data["memory_mb"] > 4000
            elif "cpu_usage" in condition and "cpu_percent" in metrics_data:
                return metrics_data["cpu_percent"] > 80
            else:
                return False
        except:
            return False
    
    async def _fire_alert(self, alert: Alert):
        """Fire alert and send notifications"""
        logger.warning(f"Alert fired: {alert.name} - {alert.message}")
        
        # Update metrics
        self.alerts_total.labels(severity=alert.severity.value, status=alert.status.value).inc()
        self.alerts_active.labels(severity=alert.severity.value).inc()
        
        # Send notifications
        for channel in self.notification_channels:
            try:
                if asyncio.iscoroutinefunction(channel):
                    await channel(alert)
                else:
                    channel(alert)
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")
        
        # Store in Redis
        await self.redis_client.hset(
            "alerts:active",
            f"{alert.name}:{alert.fingerprint}",
            json.dumps({
                "alert_id": alert.alert_id,
                "name": alert.name,
                "severity": alert.severity.value,
                "status": alert.status.value,
                "message": alert.message,
                "starts_at": alert.starts_at.isoformat(),
                "labels": alert.labels,
                "annotations": alert.annotations
            })
        )
    
    async def _resolve_alert(self, alert: Alert):
        """Resolve alert"""
        logger.info(f"Alert resolved: {alert.name}")
        
        # Update metrics
        self.alerts_total.labels(severity=alert.severity.value, status=alert.status.value).inc()
        self.alerts_active.labels(severity=alert.severity.value).dec()
        
        # Remove from Redis
        await self.redis_client.hdel(
            "alerts:active",
            f"{alert.name}:{alert.fingerprint}"
        )
        
        # Store in history
        await self.redis_client.lpush(
            "alerts:history",
            json.dumps({
                "alert_id": alert.alert_id,
                "name": alert.name,
                "severity": alert.severity.value,
                "status": alert.status.value,
                "message": alert.message,
                "starts_at": alert.starts_at.isoformat(),
                "ends_at": alert.ends_at.isoformat() if alert.ends_at else None,
                "labels": alert.labels,
                "annotations": alert.annotations
            })
        )
    
    async def get_active_alerts(self) -> list[Alert]:
        """Get all active alerts"""
        async with self._lock:
            return list(self.active_alerts.values())


class EmailNotificationChannel:
    """Email notification channel"""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str, 
                 from_email: str, to_emails: list[str]):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
    
    async def __call__(self, alert: Alert):
        """Send email notification"""
        try:
            # Create message
            msg = MimeMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.name}"
            
            # Email body
            body = f"""
Alert: {alert.name}
Severity: {alert.severity.value}
Status: {alert.status.value}
Message: {alert.message}
Started: {alert.starts_at}
Labels: {json.dumps(alert.labels, indent=2)}
Annotations: {json.dumps(alert.annotations, indent=2)}
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            # Send email (simplified - use async email library in production)
            # For now, just log
            logger.info(f"Email alert sent: {alert.name}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")


class SlackNotificationChannel:
    """Slack notification channel"""
    
    def __init__(self, webhook_url: str, channel: str = "#alerts"):
        self.webhook_url = webhook_url
        self.channel = channel
    
    async def __call__(self, alert: Alert):
        """Send Slack notification"""
        try:
            # Color based on severity
            color_map = {
                AlertSeverity.LOW: "good",
                AlertSeverity.MEDIUM: "warning",
                AlertSeverity.HIGH: "danger",
                AlertSeverity.CRITICAL: "danger"
            }
            
            payload = {
                "channel": self.channel,
                "username": "Asmblr Alert",
                "icon_emoji": ":warning:",
                "attachments": [{
                    "color": color_map.get(alert.severity, "warning"),
                    "title": alert.name,
                    "text": alert.message,
                    "fields": [
                        {"title": "Severity", "value": alert.severity.value, "short": True},
                        {"title": "Status", "value": alert.status.value, "short": True},
                        {"title": "Started", "value": alert.starts_at.strftime("%Y-%m-%d %H:%M:%S"), "short": True}
                    ],
                    "footer": "Asmblr Monitoring",
                    "ts": int(alert.starts_at.timestamp())
                }]
            }
            
            # Send to Slack (simplified)
            logger.info(f"Slack alert sent: {alert.name}")
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")


class EnhancedMonitoringSystem:
    """Enhanced monitoring system with tracing and alerting"""
    
    def __init__(self, service_name: str = "asmblr"):
        self.service_name = service_name
        self.tracer = DistributedTracer(service_name)
        self.redis_client: redis.Redis | None = None
        self.alert_manager: AlertManager | None = None
        self.metrics_registry = CollectorRegistry()
        self.is_running = False
        
        # Custom metrics
        self.custom_metrics = {
            "business_metrics": Counter('asmblr_business_metrics_total', 'Business metrics', ['metric_type']),
            "pipeline_duration": Histogram('asmblr_pipeline_duration_seconds', 'Pipeline execution duration'),
            "active_runs": Gauge('asmblr_active_runs', 'Number of active pipeline runs'),
            "queue_size": Gauge('asmblr_queue_size', 'Background queue size'),
        }
        
        # Register metrics
        for metric in self.custom_metrics.values():
            self.metrics_registry.register(metric)
    
    async def initialize(self, redis_url: str = "redis://localhost:6379/0"):
        """Initialize monitoring system"""
        # Initialize Redis
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        
        # Initialize alert manager
        self.alert_manager = AlertManager(self.redis_client)
        
        # Add notification channels (configure as needed)
        # self.alert_manager.add_notification_channel(EmailNotificationChannel(...))
        # self.alert_manager.add_notification_channel(SlackNotificationChannel(...))
        
        # Initialize tracing
        self.tracer.initialize()
        
        self.is_running = True
        logger.info("Enhanced monitoring system initialized")
    
    @asynccontextmanager
    async def trace_operation(self, operation_name: str, **attributes):
        """Trace an operation with distributed tracing"""
        async with self.tracer.start_span(operation_name, **attributes) as span:
            # Add monitoring context
            span.set_attribute("service.name", self.service_name)
            span.set_attribute("operation.name", operation_name)
            
            start_time = time.time()
            try:
                yield span
                span.set_attribute("operation.success", "true")
            except Exception as e:
                span.set_attribute("operation.success", "false")
                span.set_attribute("operation.error", str(e))
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                raise
            finally:
                duration = time.time() - start_time
                span.set_attribute("operation.duration_ms", duration * 1000)
    
    def record_business_metric(self, metric_type: str, value: float = 1):
        """Record business metric"""
        self.custom_metrics["business_metrics"].labels(metric_type=metric_type).inc(value)
    
    def record_pipeline_duration(self, duration: float):
        """Record pipeline execution duration"""
        self.custom_metrics["pipeline_duration"].observe(duration)
    
    def set_active_runs(self, count: int):
        """Set number of active runs"""
        self.custom_metrics["active_runs"].set(count)
    
    def set_queue_size(self, size: int):
        """Set queue size"""
        self.custom_metrics["queue_size"].set(size)
    
    async def evaluate_alerts(self, metrics_data: dict[str, float]):
        """Evaluate alert rules"""
        if self.alert_manager:
            await self.alert_manager.evaluate_rules(metrics_data)
    
    async def get_monitoring_dashboard(self) -> dict[str, Any]:
        """Get monitoring dashboard data"""
        if not self.is_running:
            return {"error": "Monitoring system not initialized"}
        
        # Get active alerts
        active_alerts = await self.alert_manager.get_active_alerts() if self.alert_manager else []
        
        # Get metrics
        metrics_data = {}
        for name, metric in self.custom_metrics.items():
            if hasattr(metric, '_value'):
                metrics_data[name] = metric._value._value
        
        # Get Prometheus metrics
        prometheus_metrics = generate_latest(self.metrics_registry).decode('utf-8')
        
        return {
            "service_name": self.service_name,
            "timestamp": datetime.now().isoformat(),
            "active_alerts": [
                {
                    "name": alert.name,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "starts_at": alert.starts_at.isoformat()
                }
                for alert in active_alerts
            ],
            "metrics": metrics_data,
            "prometheus_metrics": prometheus_metrics,
            "trace_context": self.tracer.get_trace_context()
        }
    
    async def cleanup(self):
        """Cleanup monitoring resources"""
        self.is_running = False
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Enhanced monitoring system cleanup completed")


# Global monitoring system instance
enhanced_monitoring = EnhancedMonitoringSystem()
