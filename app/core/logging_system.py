"""
Comprehensive logging system for Asmblr
Provides structured logging with different levels and contexts
"""

import os
import sys
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from app.core.error_formatter import ErrorSeverity


class LogLevel(Enum):
    """Log levels with corresponding severity"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(Enum):
    """Log categories for better organization"""
    SYSTEM = "system"
    API = "api"
    UI = "ui"
    DATABASE = "database"
    AUTHENTICATION = "authentication"
    EXPORT = "export"
    VALIDATION = "validation"
    PERFORMANCE = "performance"
    SECURITY = "security"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"


@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: str
    level: LogLevel
    category: LogCategory
    message: str
    component: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None


class AsmblrLogger:
    """Enhanced logging system for Asmblr"""
    
    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Log levels configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.enable_performance_logging = os.getenv("ENABLE_PERFORMANCE_LOGGING", "true").lower() == "true"
        self.enable_error_details = os.getenv("ENABLE_ERROR_DETAILS", "true").lower() == "true"
        
        # Configure file handlers
        self.setup_file_handlers()
        
        # Configure console handler
        self.setup_console_handler()
        
        # Performance tracking
        self.performance_data: Dict[str, Any] = {}
    
    def setup_file_handlers(self) -> None:
        """Setup file handlers for different log types"""
        # Main application log
        self.app_log_file = self.log_dir / "asmblr.log"
        
        # Error log
        self.error_log_file = self.log_dir / "errors.log"
        
        # Performance log
        self.performance_log_file = self.log_dir / "performance.log"
        
        # Security log
        self.security_log_file = self.log_dir / "security.log"
    
    def setup_console_handler(self) -> None:
        """Setup console logging"""
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
    
    def log(
        self,
        level: LogLevel,
        message: str,
        category: LogCategory = LogCategory.SYSTEM,
        component: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        performance_metrics: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a message with structured data"""
        
        # Create log entry
        log_entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level,
            category=category,
            message=message,
            component=component,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            error_details=error_details,
            performance_metrics=performance_metrics,
            context=context
        )
        
        # Write to appropriate files
        self._write_to_files(log_entry)
        
        # Console logging
        console_message = self._format_console_message(log_entry)
        getattr(logging, level.value.lower())(console_message)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message"""
        self.log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message"""
        self.log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message"""
        self.log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log error message with exception details"""
        error_details = None
        if error and self.enable_error_details:
            error_details = {
                "exception_type": type(error).__name__,
                "exception_message": str(error),
                "traceback": traceback.format_exc()
            }
        
        self.log(LogLevel.ERROR, message, error_details=error_details, **kwargs)
    
    def critical(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log critical error message"""
        error_details = None
        if error and self.enable_error_details:
            error_details = {
                "exception_type": type(error).__name__,
                "exception_message": str(error),
                "traceback": traceback.format_exc()
            }
        
        self.log(LogLevel.CRITICAL, message, error_details=error_details, **kwargs)
    
    def log_performance(
        self,
        operation: str,
        duration: float,
        component: Optional[str] = None,
        **kwargs
    ) -> None:
        """Log performance metrics"""
        if not self.enable_performance_logging:
            return
        
        performance_metrics = {
            "operation": operation,
            "duration_ms": duration * 1000,
            "timestamp": datetime.now().isoformat()
        }
        
        self.log(
            LogLevel.INFO,
            f"Performance: {operation} completed in {duration:.3f}s",
            category=LogCategory.PERFORMANCE,
            component=component,
            performance_metrics=performance_metrics,
            **kwargs
        )
    
    def log_security_event(
        self,
        event_type: str,
        severity: ErrorSeverity,
        details: Dict[str, Any],
        **kwargs
    ) -> None:
        """Log security events"""
        security_context = {
            "event_type": event_type,
            "severity": severity.value,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        level = LogLevel.WARNING if severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM] else LogLevel.ERROR
        
        self.log(
            level,
            f"Security Event: {event_type}",
            category=LogCategory.SECURITY,
            context=security_context,
            **kwargs
        )
    
    def log_api_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float,
        user_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """Log API request"""
        api_context = {
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "duration_ms": duration * 1000
        }
        
        level = LogLevel.INFO if status_code < 400 else LogLevel.ERROR
        
        self.log(
            level,
            f"API {method} {endpoint} - {status_code} ({duration:.3f}s)",
            category=LogCategory.API,
            component="api_server",
            user_id=user_id,
            context=api_context,
            **kwargs
        )
    
    def log_validation_error(
        self,
        field: str,
        value: Any,
        validation_rule: str,
        component: Optional[str] = None,
        **kwargs
    ) -> None:
        """Log validation errors"""
        validation_context = {
            "field": field,
            "value": str(value),
            "validation_rule": validation_rule,
            "component": component
        }
        
        self.log(
            LogLevel.WARNING,
            f"Validation failed for {field}: {validation_rule}",
            category=LogCategory.VALIDATION,
            component=component,
            context=validation_context,
            **kwargs
        )
    
    def _write_to_files(self, log_entry: LogEntry) -> None:
        """Write log entry to appropriate files"""
        try:
            # Main log file
            with open(self.app_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(log_entry), default=str) + '\n')
            
            # Error log file
            if log_entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                with open(self.error_log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(asdict(log_entry), default=str) + '\n')
            
            # Performance log file
            if log_entry.category == LogCategory.PERFORMANCE and log_entry.performance_metrics:
                with open(self.performance_log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(asdict(log_entry), default=str) + '\n')
            
            # Security log file
            if log_entry.category == LogCategory.SECURITY:
                with open(self.security_log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(asdict(log_entry), default=str) + '\n')
                    
        except Exception as e:
            # Fallback to console if file writing fails
            print(f"Failed to write log entry: {e}")
            print(f"Log entry: {log_entry}")
    
    def _format_console_message(self, log_entry: LogEntry) -> str:
        """Format log entry for console display"""
        category_icon = self._get_category_icon(log_entry.category)
        level_icon = self._get_level_icon(log_entry.level)
        
        message_parts = [
            f"{level_icon} [{log_entry.level.value}]",
            f"{category_icon} {log_entry.category.value}",
        ]
        
        if log_entry.component:
            message_parts.append(f"📦 {log_entry.component}")
        
        message_parts.append(log_entry.message)
        
        return " ".join(message_parts)
    
    def _get_category_icon(self, category: LogCategory) -> str:
        """Get icon for log category"""
        icons = {
            LogCategory.SYSTEM: "⚙️",
            LogCategory.API: "🌐",
            LogCategory.UI: "🖥️",
            LogCategory.DATABASE: "🗄️",
            LogCategory.AUTHENTICATION: "🔐",
            LogCategory.EXPORT: "📤",
            LogCategory.VALIDATION: "✅",
            LogCategory.PERFORMANCE: "⚡",
            LogCategory.SECURITY: "🛡️",
            LogCategory.NETWORK: "📡",
            LogCategory.FILE_SYSTEM: "📁"
        }
        return icons.get(category, "📝")
    
    def _get_level_icon(self, level: LogLevel) -> str:
        """Get icon for log level"""
        icons = {
            LogLevel.DEBUG: "🔍",
            LogLevel.INFO: "ℹ️",
            LogLevel.WARNING: "⚠️",
            LogLevel.ERROR: "❌",
            LogLevel.CRITICAL: "🚨"
        }
        return icons.get(level, "📝")
    
    def get_log_stats(self) -> Dict[str, Any]:
        """Get logging statistics"""
        stats = {
            "log_files": {
                "main": str(self.app_log_file),
                "errors": str(self.error_log_file),
                "performance": str(self.performance_log_file),
                "security": str(self.security_log_file)
            },
            "log_level": self.log_level,
            "performance_logging": self.enable_performance_logging,
            "error_details": self.enable_error_details
        }
        
        # Add file sizes if files exist
        for log_type, file_path in stats["log_files"].items():
            path = Path(file_path)
            if path.exists():
                stats[f"{log_type}_size_bytes"] = path.stat().st_size
                stats[f"{log_type}_size_mb"] = path.stat().st_size / (1024 * 1024)
        
        return stats
    
    def cleanup_old_logs(self, days_to_keep: int = 30) -> None:
        """Clean up old log files"""
        try:
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            
            for log_file in [self.app_log_file, self.error_log_file, self.performance_log_file, self.security_log_file]:
                if log_file.exists():
                    if log_file.stat().st_mtime < cutoff_date:
                        # Archive old log
                        archive_file = log_file.with_suffix(f".{datetime.now().strftime('%Y%m%d')}.log")
                        log_file.rename(archive_file)
                        self.info(f"Archived old log file: {log_file} -> {archive_file}")
                        
        except Exception as e:
            self.error(f"Failed to cleanup old logs: {e}")


# Global logger instance
_global_logger: Optional[AsmblrLogger] = None


def get_logger() -> AsmblrLogger:
    """Get the global logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = AsmblrLogger()
    return _global_logger


def setup_logging(log_dir: Optional[Path] = None) -> AsmblrLogger:
    """Setup logging system"""
    global _global_logger
    _global_logger = AsmblrLogger(log_dir)
    return _global_logger


# Convenience functions for common logging operations
def log_debug(message: str, **kwargs) -> None:
    """Log debug message"""
    get_logger().debug(message, **kwargs)


def log_info(message: str, **kwargs) -> None:
    """Log info message"""
    get_logger().info(message, **kwargs)


def log_warning(message: str, **kwargs) -> None:
    """Log warning message"""
    get_logger().warning(message, **kwargs)


def log_error(message: str, error: Optional[Exception] = None, **kwargs) -> None:
    """Log error message"""
    get_logger().error(message, error, **kwargs)


def log_critical(message: str, error: Optional[Exception] = None, **kwargs) -> None:
    """Log critical error message"""
    get_logger().critical(message, error, **kwargs)


def log_performance(operation: str, duration: float, **kwargs) -> None:
    """Log performance metrics"""
    get_logger().log_performance(operation, duration, **kwargs)


def log_security_event(event_type: str, severity: ErrorSeverity, details: Dict[str, Any], **kwargs) -> None:
    """Log security event"""
    get_logger().log_security_event(event_type, severity, details, **kwargs)


def log_api_request(method: str, endpoint: str, status_code: int, duration: float, **kwargs) -> None:
    """Log API request"""
    get_logger().log_api_request(method, endpoint, status_code, duration, **kwargs)
