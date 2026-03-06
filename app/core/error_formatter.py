"""
Standardized error message formatting for Asmblr
Provides consistent error messaging across all components
"""

import os
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better organization"""
    CONFIGURATION = "configuration"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    VALIDATION = "validation"
    RUNTIME = "runtime"
    SECURITY = "security"
    PERFORMANCE = "performance"
    USER_INPUT = "user_input"


@dataclass
class ErrorContext:
    """Context information for errors"""
    component: str
    operation: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


class ErrorMessageFormatter:
    """Standardized error message formatting"""
    
    # Error message templates
    TEMPLATES = {
        ErrorCategory.CONFIGURATION: {
            ErrorSeverity.LOW: "⚙️ Configuration notice: {message}",
            ErrorSeverity.MEDIUM: "⚠️ Configuration issue: {message}",
            ErrorSeverity.HIGH: "🚨 Configuration error: {message}",
            ErrorSeverity.CRITICAL: "💥 Critical configuration failure: {message}"
        },
        ErrorCategory.NETWORK: {
            ErrorSeverity.LOW: "🌐 Network notice: {message}",
            ErrorSeverity.MEDIUM: "📡 Network issue: {message}",
            ErrorSeverity.HIGH: "🚫 Network error: {message}",
            ErrorSeverity.CRITICAL: "💥 Network failure: {message}"
        },
        ErrorCategory.FILE_SYSTEM: {
            ErrorSeverity.LOW: "📁 File system notice: {message}",
            ErrorSeverity.MEDIUM: "📂 File system issue: {message}",
            ErrorSeverity.HIGH: "❌ File system error: {message}",
            ErrorSeverity.CRITICAL: "💥 File system failure: {message}"
        },
        ErrorCategory.VALIDATION: {
            ErrorSeverity.LOW: "✓ Validation notice: {message}",
            ErrorSeverity.MEDIUM: "⚠️ Validation issue: {message}",
            ErrorSeverity.HIGH: "❌ Validation error: {message}",
            ErrorSeverity.CRITICAL: "💥 Validation failure: {message}"
        },
        ErrorCategory.RUNTIME: {
            ErrorSeverity.LOW: "🔄 Runtime notice: {message}",
            ErrorSeverity.MEDIUM: "⚠️ Runtime issue: {message}",
            ErrorSeverity.HIGH: "🚫 Runtime error: {message}",
            ErrorSeverity.CRITICAL: "💥 Runtime failure: {message}"
        },
        ErrorCategory.SECURITY: {
            ErrorSeverity.LOW: "🔒 Security notice: {message}",
            ErrorSeverity.MEDIUM: "⚠️ Security issue: {message}",
            ErrorSeverity.HIGH: "🚨 Security error: {message}",
            ErrorSeverity.CRITICAL: "💥 Security breach: {message}"
        },
        ErrorCategory.PERFORMANCE: {
            ErrorSeverity.LOW: "⚡ Performance notice: {message}",
            ErrorSeverity.MEDIUM: "⚠️ Performance issue: {message}",
            ErrorSeverity.HIGH: "🐌 Performance error: {message}",
            ErrorSeverity.CRITICAL: "💥 Performance failure: {message}"
        },
        ErrorCategory.USER_INPUT: {
            ErrorSeverity.LOW: "💡 Input suggestion: {message}",
            ErrorSeverity.MEDIUM: "⚠️ Input issue: {message}",
            ErrorSeverity.HIGH: "❌ Input error: {message}",
            ErrorSeverity.CRITICAL: "💥 Invalid input: {message}"
        }
    }
    
    # Common error messages
    COMMON_MESSAGES = {
        "file_not_found": "File not found: {file_path}",
        "permission_denied": "Permission denied: {action}",
        "invalid_format": "Invalid format: {expected_format} expected",
        "timeout": "Operation timed out after {timeout}s",
        "connection_failed": "Failed to connect to {service}",
        "resource_unavailable": "Resource unavailable: {resource}",
        "validation_failed": "Validation failed: {field}",
        "configuration_missing": "Missing configuration: {config_key}",
        "dependency_missing": "Missing dependency: {dependency}",
        "quota_exceeded": "Quota exceeded: {quota_type}",
        "rate_limited": "Rate limited: please wait {retry_after}s"
    }
    
    @classmethod
    def format_error(
        cls,
        message: str,
        category: ErrorCategory = ErrorCategory.RUNTIME,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[ErrorContext] = None,
        include_suggestions: bool = True
    ) -> str:
        """Format an error message with consistent styling"""
        
        # Get the appropriate template
        template = cls.TEMPLATES.get(category, {}).get(severity, "⚠️ Error: {message}")
        
        # Format the base message
        formatted_message = template.format(message=message)
        
        # Add context information if available
        if context:
            context_info = []
            if context.component:
                context_info.append(f"Component: {context.component}")
            if context.operation:
                context_info.append(f"Operation: {context.operation}")
            if context.user_id:
                context_info.append(f"User: {context.user_id}")
            if context.session_id:
                context_info.append(f"Session: {context.session_id}")
            
            if context_info:
                formatted_message += f"\n📍 Context: {' | '.join(context_info)}"
        
        # Add suggestions for common errors
        if include_suggestions:
            suggestion = cls._get_suggestion(message, category, severity)
            if suggestion:
                formatted_message += f"\n💡 Suggestion: {suggestion}"
        
        return formatted_message
    
    @classmethod
    def format_common_error(
        cls,
        error_key: str,
        **kwargs
    ) -> str:
        """Format a common error message"""
        template = cls.COMMON_MESSAGES.get(error_key, "Unknown error: {message}")
        return template.format(**kwargs)
    
    @classmethod
    def _get_suggestion(
        cls,
        message: str,
        category: ErrorCategory,
        severity: ErrorSeverity
    ) -> Optional[str]:
        """Get suggestion for common error patterns"""
        message_lower = message.lower()
        
        # Configuration suggestions
        if category == ErrorCategory.CONFIGURATION:
            if "not found" in message_lower or "missing" in message_lower:
                return "Check your environment variables and configuration files"
            elif "invalid" in message_lower:
                return "Verify the format and values in your configuration"
            elif "permission" in message_lower:
                return "Check file permissions and user access rights"
        
        # Network suggestions
        elif category == ErrorCategory.NETWORK:
            if "connection" in message_lower:
                return "Check network connectivity and service availability"
            elif "timeout" in message_lower:
                return "Try increasing timeout values or check network latency"
            elif "rate limit" in message_lower:
                return "Wait before retrying or reduce request frequency"
        
        # File system suggestions
        elif category == ErrorCategory.FILE_SYSTEM:
            if "not found" in message_lower:
                return "Verify file paths and ensure files exist"
            elif "permission" in message_lower:
                return "Check file/directory permissions"
            elif "space" in message_lower or "disk" in message_lower:
                return "Free up disk space or change storage location"
        
        # Validation suggestions
        elif category == ErrorCategory.VALIDATION:
            if "required" in message_lower:
                return "Provide all required fields"
            elif "format" in message_lower:
                return "Check the expected format and try again"
            elif "range" in message_lower or "limit" in message_lower:
                return "Ensure values are within the allowed range"
        
        # Performance suggestions
        elif category == ErrorCategory.PERFORMANCE:
            if "memory" in message_lower:
                return "Reduce memory usage or increase available memory"
            elif "slow" in message_lower or "timeout" in message_lower:
                return "Optimize the operation or increase timeout values"
        
        # User input suggestions
        elif category == ErrorCategory.USER_INPUT:
            if "invalid" in message_lower:
                return "Check the input format and requirements"
            elif "empty" in message_lower or "missing" in message_lower:
                return "Provide the required input"
        
        return None
    
    @classmethod
    def format_exception(
        cls,
        exception: Exception,
        context: Optional[ErrorContext] = None
    ) -> str:
        """Format an exception with consistent styling"""
        exception_type = type(exception).__name__
        exception_message = str(exception)
        
        # Determine category and severity based on exception type
        category, severity = cls._classify_exception(exception)
        
        # Format the error
        base_message = f"{exception_type}: {exception_message}"
        return cls.format_error(
            message=base_message,
            category=category,
            severity=severity,
            context=context
        )
    
    @classmethod
    def _classify_exception(cls, exception: Exception) -> tuple[ErrorCategory, ErrorSeverity]:
        """Classify exception by type and determine severity"""
        exception_type = type(exception).__name__
        
        # File system errors
        if exception_type in ('FileNotFoundError', 'PermissionError', 'IsADirectoryError'):
            return ErrorCategory.FILE_SYSTEM, ErrorSeverity.MEDIUM
        elif exception_type in ('OSError', 'IOError'):
            return ErrorCategory.FILE_SYSTEM, ErrorSeverity.HIGH
        
        # Network errors
        elif exception_type in ('ConnectionError', 'TimeoutError', 'HTTPError'):
            return ErrorCategory.NETWORK, ErrorSeverity.MEDIUM
        elif exception_type in ('URLError', 'SSLError'):
            return ErrorCategory.NETWORK, ErrorSeverity.HIGH
        
        # Validation errors
        elif exception_type in ('ValueError', 'TypeError', 'ValidationError'):
            return ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM
        elif exception_type in ('AssertionError',):
            return ErrorCategory.VALIDATION, ErrorSeverity.HIGH
        
        # Configuration errors
        elif exception_type in ('KeyError', 'AttributeError'):
            return ErrorCategory.CONFIGURATION, ErrorSeverity.MEDIUM
        elif exception_type in ('ImportError', 'ModuleNotFoundError'):
            return ErrorCategory.CONFIGURATION, ErrorSeverity.HIGH
        
        # Runtime errors
        elif exception_type in ('RuntimeError', 'RuntimeWarning'):
            return ErrorCategory.RUNTIME, ErrorSeverity.MEDIUM
        elif exception_type in ('SystemError', 'MemoryError'):
            return ErrorCategory.RUNTIME, ErrorSeverity.CRITICAL
        
        # Security errors
        elif exception_type in ('PermissionError', 'AccessDenied'):
            return ErrorCategory.SECURITY, ErrorSeverity.HIGH
        elif exception_type in ('SecurityError',):
            return ErrorCategory.SECURITY, ErrorSeverity.CRITICAL
        
        # Default classification
        return ErrorCategory.RUNTIME, ErrorSeverity.MEDIUM


# Convenience functions for common error formatting
def format_config_error(message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> str:
    """Format a configuration error"""
    return ErrorMessageFormatter.format_error(
        message=message,
        category=ErrorCategory.CONFIGURATION,
        severity=severity
    )


def format_network_error(message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> str:
    """Format a network error"""
    return ErrorMessageFormatter.format_error(
        message=message,
        category=ErrorCategory.NETWORK,
        severity=severity
    )


def format_file_error(message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> str:
    """Format a file system error"""
    return ErrorMessageFormatter.format_error(
        message=message,
        category=ErrorCategory.FILE_SYSTEM,
        severity=severity
    )


def format_validation_error(message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> str:
    """Format a validation error"""
    return ErrorMessageFormatter.format_error(
        message=message,
        category=ErrorCategory.VALIDATION,
        severity=severity
    )


def format_runtime_error(message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> str:
    """Format a runtime error"""
    return ErrorMessageFormatter.format_error(
        message=message,
        category=ErrorCategory.RUNTIME,
        severity=severity
    )


def format_security_error(message: str, severity: ErrorSeverity = ErrorSeverity.HIGH) -> str:
    """Format a security error"""
    return ErrorMessageFormatter.format_error(
        message=message,
        category=ErrorCategory.SECURITY,
        severity=severity
    )


def format_performance_error(message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> str:
    """Format a performance error"""
    return ErrorMessageFormatter.format_error(
        message=message,
        category=ErrorCategory.PERFORMANCE,
        severity=severity
    )


def format_user_input_error(message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM) -> str:
    """Format a user input error"""
    return ErrorMessageFormatter.format_error(
        message=message,
        category=ErrorCategory.USER_INPUT,
        severity=severity
    )


def format_exception_with_context(
    exception: Exception,
    component: str,
    operation: str,
    **context_data
) -> str:
    """Format an exception with context"""
    context = ErrorContext(
        component=component,
        operation=operation,
        additional_data=context_data
    )
    return ErrorMessageFormatter.format_exception(exception, context)
