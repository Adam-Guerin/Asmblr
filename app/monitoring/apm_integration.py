"""
APM Integration for Asmblr
Supports New Relic and DataDog APM solutions
"""

import os
import time
import json
import logging
from typing import Any
from functools import wraps
from contextlib import contextmanager
import psutil

logger = logging.getLogger(__name__)

class APMProvider:
    """Base class for APM providers"""
    
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.enabled = config.get('enabled', False)
        
    def record_metric(self, name: str, value: float, tags: dict[str, str] = None):
        """Record a custom metric"""
        raise NotImplementedError
        
    def record_event(self, event_name: str, attributes: dict[str, Any] = None):
        """Record a custom event"""
        raise NotImplementedError
        
    def start_transaction(self, name: str, transaction_type: str = "custom"):
        """Start a transaction"""
        raise NotImplementedError
        
    def end_transaction(self, status: str = "success"):
        """End a transaction"""
        raise NotImplementedError
        
    def notice_error(self, error: Exception, attributes: dict[str, Any] = None):
        """Record an error"""
        raise NotImplementedError

class NewRelicProvider(APMProvider):
    """New Relic APM integration"""
    
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        if self.enabled:
            try:
                import newrelic.agent
                self.nr = newrelic.agent
                self.nr.initialize(config.get('license_key'), config.get('app_name', 'asmblr'))
                logger.info("New Relic APM initialized")
            except ImportError:
                logger.error("New Relic package not installed. Install with: pip install newrelic")
                self.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize New Relic: {e}")
                self.enabled = False
    
    def record_metric(self, name: str, value: float, tags: dict[str, str] = None):
        if not self.enabled:
            return
            
        try:
            self.nr.record_custom_metric(name, value)
            if tags:
                self.nr.add_custom_parameter(tags)
        except Exception as e:
            logger.error(f"Failed to record New Relic metric: {e}")
    
    def record_event(self, event_name: str, attributes: dict[str, Any] = None):
        if not self.enabled:
            return
            
        try:
            self.nr.record_custom_event(event_name, attributes or {})
        except Exception as e:
            logger.error(f"Failed to record New Relic event: {e}")
    
    def start_transaction(self, name: str, transaction_type: str = "custom"):
        if not self.enabled:
            return None
            
        try:
            return self.nr.background_task().name(name)
        except Exception as e:
            logger.error(f"Failed to start New Relic transaction: {e}")
            return None
    
    def end_transaction(self, status: str = "success"):
        if not self.enabled:
            return
            
        try:
            # New Relic handles transaction ending automatically
            pass
        except Exception as e:
            logger.error(f"Failed to end New Relic transaction: {e}")
    
    def notice_error(self, error: Exception, attributes: dict[str, Any] = None):
        if not self.enabled:
            return
            
        try:
            self.nr.notice_error(error)
            if attributes:
                self.nr.add_custom_parameter(attributes)
        except Exception as e:
            logger.error(f"Failed to record New Relic error: {e}")

class DataDogProvider(APMProvider):
    """DataDog APM integration"""
    
    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        if self.enabled:
            try:
                from ddtrace import tracer, patch_all
                from datadog import initialize, statsd
                
                # Initialize Datadog
                initialize(
                    api_key=config.get('api_key'),
                    app_key=config.get('app_key'),
                    statsd_host=config.get('statsd_host', 'localhost'),
                    statsd_port=config.get('statsd_port', 8125)
                )
                
                # Patch all libraries
                patch_all()
                
                self.tracer = tracer
                self.statsd = statsd
                logger.info("DataDog APM initialized")
            except ImportError:
                logger.error("DataDog packages not installed. Install with: pip install ddtrace datadog")
                self.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize DataDog: {e}")
                self.enabled = False
    
    def record_metric(self, name: str, value: float, tags: dict[str, str] = None):
        if not self.enabled:
            return
            
        try:
            self.statsd.gauge(name, value, tags=tags)
        except Exception as e:
            logger.error(f"Failed to record DataDog metric: {e}")
    
    def record_event(self, event_name: str, attributes: dict[str, Any] = None):
        if not self.enabled:
            return
            
        try:
            self.statsd.event(event_name, json.dumps(attributes or {}))
        except Exception as e:
            logger.error(f"Failed to record DataDog event: {e}")
    
    def start_transaction(self, name: str, transaction_type: str = "custom"):
        if not self.enabled:
            return None
            
        try:
            span = self.tracer.start_span(name)
            span.set_tag('component', 'asmblr')
            span.set_tag('span.type', transaction_type)
            return span
        except Exception as e:
            logger.error(f"Failed to start DataDog span: {e}")
            return None
    
    def end_transaction(self, status: str = "success"):
        if not self.enabled:
            return
            
        try:
            current_span = self.tracer.current_span()
            if current_span:
                current_span.set_tag('status', status)
                current_span.finish()
        except Exception as e:
            logger.error(f"Failed to end DataDog span: {e}")
    
    def notice_error(self, error: Exception, attributes: dict[str, Any] = None):
        if not self.enabled:
            return
            
        try:
            current_span = self.tracer.current_span()
            if current_span:
                current_span.set_tag('error', True)
                current_span.set_tag('error.msg', str(error))
                current_span.set_tag('error.type', type(error).__name__)
                if attributes:
                    for key, value in attributes.items():
                        current_span.set_tag(f'error.{key}', value)
        except Exception as e:
            logger.error(f"Failed to record DataDog error: {e}")

class APMManager:
    """Manages APM integrations and provides unified interface"""
    
    def __init__(self):
        self.providers: list[APMProvider] = []
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all configured APM providers"""
        
        # New Relic
        if os.getenv('NEW_RELIC_LICENSE_KEY'):
            new_relic_config = {
                'enabled': True,
                'license_key': os.getenv('NEW_RELIC_LICENSE_KEY'),
                'app_name': os.getenv('NEW_RELIC_APP_NAME', 'asmblr'),
                'log_level': os.getenv('NEW_RELIC_LOG_LEVEL', 'info')
            }
            self.providers.append(NewRelicProvider(new_relic_config))
        
        # DataDog
        if os.getenv('DD_API_KEY'):
            datadog_config = {
                'enabled': True,
                'api_key': os.getenv('DD_API_KEY'),
                'app_key': os.getenv('DD_APP_KEY', ''),
                'statsd_host': os.getenv('DD_STATSD_HOST', 'localhost'),
                'statsd_port': int(os.getenv('DD_STATSD_PORT', 8125)),
                'env': os.getenv('DD_ENV', 'production'),
                'version': os.getenv('DD_VERSION', '2.0.0')
            }
            self.providers.append(DataDogProvider(datadog_config))
    
    def record_metric(self, name: str, value: float, tags: dict[str, str] = None):
        """Record metric across all providers"""
        for provider in self.providers:
            provider.record_metric(name, value, tags)
    
    def record_event(self, event_name: str, attributes: dict[str, Any] = None):
        """Record event across all providers"""
        for provider in self.providers:
            provider.record_event(event_name, attributes)
    
    def start_transaction(self, name: str, transaction_type: str = "custom"):
        """Start transaction across all providers"""
        transactions = []
        for provider in self.providers:
            tx = provider.start_transaction(name, transaction_type)
            transactions.append(tx)
        return transactions
    
    def end_transaction(self, transactions: list, status: str = "success"):
        """End transactions across all providers"""
        for i, provider in enumerate(self.providers):
            if i < len(transactions) and transactions[i]:
                provider.end_transaction(status)
    
    def notice_error(self, error: Exception, attributes: dict[str, Any] = None):
        """Record error across all providers"""
        for provider in self.providers:
            provider.notice_error(error, attributes)
    
    def is_enabled(self) -> bool:
        """Check if any APM provider is enabled"""
        return any(provider.enabled for provider in self.providers)

# Global APM manager instance
apm_manager = APMManager()

# Decorators for easy integration
def apm_transaction(name: str, transaction_type: str = "custom"):
    """Decorator to wrap functions with APM transaction"""
    def decorator(func):
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            transactions = apm_manager.start_transaction(name, transaction_type)
            try:
                result = func(*args, **kwargs)
                apm_manager.end_transaction(transactions, "success")
                return result
            except Exception as e:
                apm_manager.notice_error(e, {'function': name, 'args': str(args)[:100]})
                apm_manager.end_transaction(transactions, "error")
                raise
        return sync_wrapper
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            transactions = apm_manager.start_transaction(name, transaction_type)
            try:
                result = await func(*args, **kwargs)
                apm_manager.end_transaction(transactions, "success")
                return result
            except Exception as e:
                apm_manager.notice_error(e, {'function': name, 'args': str(args)[:100]})
                apm_manager.end_transaction(transactions, "error")
                raise
        return async_wrapper
    
    return decorator

@contextmanager
def apm_span(name: str, span_type: str = "custom"):
    """Context manager for APM spans"""
    transactions = apm_manager.start_transaction(name, span_type)
    try:
        yield
        apm_manager.end_transaction(transactions, "success")
    except Exception as e:
        apm_manager.notice_error(e, {'span': name})
        apm_manager.end_transaction(transactions, "error")
        raise

# System metrics collection
def collect_system_metrics():
    """Collect and record system metrics"""
    if not apm_manager.is_enabled():
        return
    
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        apm_manager.record_metric('system.cpu.percent', cpu_percent)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        apm_manager.record_metric('system.memory.percent', memory.percent)
        apm_manager.record_metric('system.memory.available', memory.available)
        apm_manager.record_metric('system.memory.used', memory.used)
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        apm_manager.record_metric('system.disk.percent', disk.percent)
        apm_manager.record_metric('system.disk.free', disk.free)
        apm_manager.record_metric('system.disk.used', disk.used)
        
        # Network metrics
        network = psutil.net_io_counters()
        apm_manager.record_metric('system.network.bytes_sent', network.bytes_sent)
        apm_manager.record_metric('system.network.bytes_recv', network.bytes_recv)
        
    except Exception as e:
        logger.error(f"Failed to collect system metrics: {e}")

# Business metrics
def record_business_event(event_type: str, run_id: str = None, **attributes):
    """Record business events"""
    event_data = {
        'event_type': event_type,
        'timestamp': time.time(),
        **attributes
    }
    
    if run_id:
        event_data['run_id'] = run_id
    
    apm_manager.record_event(f'asmblr.business.{event_type}', event_data)

def record_pipeline_metrics(run_id: str, stage: str, duration: float, status: str):
    """Record pipeline execution metrics"""
    apm_manager.record_metric(f'asmblr.pipeline.{stage}.duration', duration, {
        'run_id': run_id,
        'status': status
    })
    
    record_business_event('pipeline_stage_completed', run_id=run_id, 
                         stage=stage, duration=duration, status=status)

def record_llm_metrics(model: str, tokens: int, duration: float, success: bool):
    """Record LLM performance metrics"""
    apm_manager.record_metric('asmblr.llm.tokens', tokens, {
        'model': model,
        'success': str(success)
    })
    
    apm_manager.record_metric('asmblr.llm.duration', duration, {
        'model': model,
        'success': str(success)
    })
    
    if success:
        apm_manager.record_metric('asmblr.llm.tokens_per_second', tokens / duration, {
            'model': model
        })

# Start background metrics collection
def start_metrics_collection(interval: int = 60):
    """Start background system metrics collection"""
    def collect_metrics():
        while True:
            collect_system_metrics()
            time.sleep(interval)
    
    import threading
    thread = threading.Thread(target=collect_metrics, daemon=True)
    thread.start()
    logger.info(f"Started metrics collection with {interval}s interval")

# Initialize metrics collection if APM is enabled
if apm_manager.is_enabled():
    start_metrics_collection()
