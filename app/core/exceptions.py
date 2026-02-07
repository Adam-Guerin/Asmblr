"""Standardized exception hierarchy for the Asmblr application.

This module provides a consistent approach to error handling throughout the codebase,
using custom exceptions for exceptional cases rather than returning error objects.
"""

from __future__ import annotations
from typing import Any


# ============================================================================
# BASE EXCEPTION CLASSES
# ============================================================================

class AsmblrException(Exception):
    """Base exception for all Asmblr-specific errors."""
    
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self) -> str:
        return self.message
    
    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class ConfigurationError(AsmblrException):
    """Raised when configuration is invalid or missing."""
    pass


class ValidationError(AsmblrException):
    """Raised when input validation fails."""
    pass


class ResourceNotFoundError(AsmblrException):
    """Raised when required resources (files, models, etc.) are not found."""
    pass


class ServiceUnavailableError(AsmblrException):
    """Raised when external services are unavailable."""
    pass


class ProcessingError(AsmblrException):
    """Raised when data processing fails."""
    pass


class StateError(AsmblrException):
    """Raised when system state is invalid for requested operation."""
    pass


# ============================================================================
# SPECIFIC EXCEPTION CLASSES
# ============================================================================

class LLMUnavailableError(ServiceUnavailableError):
    """Raised when LLM service is not available or unreachable."""
    
    def __init__(self, service_name: str, details: dict[str, Any] | None = None) -> None:
        message = f"{service_name} is not available or unreachable"
        super().__init__(message, details)
        self.service_name = service_name


class ModelNotFoundError(ResourceNotFoundError):
    """Raised when required AI model is not found."""
    
    def __init__(self, model_name: str, available_models: list[str] | None = None) -> None:
        message = f"Model '{model_name}' not found"
        details = {"requested_model": model_name}
        if available_models:
            details["available_models"] = available_models
        super().__init__(message, details)


class RunNotFoundError(ResourceNotFoundError):
    """Raised when a specific run ID is not found."""
    
    def __init__(self, run_id: str) -> None:
        message = f"Run '{run_id}' not found"
        details = {"run_id": run_id}
        super().__init__(message, details)


class InvalidTopicError(ValidationError):
    """Raised when topic validation fails."""
    
    def __init__(self, topic: str, reason: str) -> None:
        message = f"Invalid topic: {reason}"
        details = {"topic": topic, "validation_reason": reason}
        super().__init__(message, details)


class InvalidStateError(StateError):
    """Raised when system state prevents an operation."""
    
    def __init__(self, operation: str, current_state: str, required_state: str) -> None:
        message = f"Cannot {operation} in state '{current_state}'. Requires '{required_state}'"
        details = {
            "operation": operation,
            "current_state": current_state,
            "required_state": required_state,
        }
        super().__init__(message, details)


class PipelineStageError(ProcessingError):
    """Raised when a pipeline stage fails."""
    
    def __init__(self, stage: str, run_id: str, cause: Exception | str, retryable: bool = False) -> None:
        if isinstance(cause, Exception):
            message = f"Stage '{stage}' failed in run '{run_id}': {cause}"
            details = {
                "stage": stage,
                "run_id": run_id,
                "cause_type": cause.__class__.__name__,
                "cause_message": str(cause),
                "retryable": retryable,
            }
        else:
            message = f"Stage '{stage}' failed in run '{run_id}': {cause}"
            details = {
                "stage": stage,
                "run_id": run_id,
                "cause_type": "Error",
                "cause_message": str(cause),
                "retryable": retryable,
            }
        super().__init__(message, details)
        self.stage = stage
        self.run_id = run_id
        self.retryable = retryable


class DataProcessingError(ProcessingError):
    """Raised when data processing operations fail."""
    
    def __init__(self, operation: str, data_type: str, cause: Exception | str) -> None:
        if isinstance(cause, Exception):
            message = f"Failed to {operation} {data_type}: {cause}"
            details = {
                "operation": operation,
                "data_type": data_type,
                "cause_type": cause.__class__.__name__,
                "cause_message": str(cause),
            }
        else:
            message = f"Failed to {operation} {data_type}: {cause}"
            details = {
                "operation": operation,
                "data_type": data_type,
                "cause_type": "Error",
                "cause_message": str(cause),
            }
        super().__init__(message, details)


class FileOperationError(ProcessingError):
    """Raised when file operations fail."""
    
    def __init__(self, operation: str, file_path: str, cause: Exception | str) -> None:
        if isinstance(cause, Exception):
            message = f"Failed to {operation} file '{file_path}': {cause}"
            details = {
                "operation": operation,
                "file_path": file_path,
                "cause_type": cause.__class__.__name__,
                "cause_message": str(cause),
            }
        else:
            message = f"Failed to {operation} file '{file_path}': {cause}"
            details = {
                "operation": operation,
                "file_path": file_path,
                "cause_type": "Error",
                "cause_message": str(cause),
            }
        super().__init__(message, details)


class NetworkError(ServiceUnavailableError):
    """Raised when network operations fail."""
    
    def __init__(self, operation: str, url: str, cause: Exception | str) -> None:
        if isinstance(cause, Exception):
            message = f"Network {operation} failed for '{url}': {cause}"
            details = {
                "operation": operation,
                "url": url,
                "cause_type": cause.__class__.__name__,
                "cause_message": str(cause),
            }
        else:
            message = f"Network {operation} failed for '{url}': {cause}"
            details = {
                "operation": operation,
                "url": url,
                "cause_type": "Error",
                "cause_message": str(cause),
            }
        super().__init__(message, details)


# ============================================================================
# ERROR HANDLING UTILITIES
# ============================================================================

def handle_file_operation_error(
    operation: str,
    file_path: str,
    cause: Exception,
    fallback_action: str | None = None,
) -> None:
    """Handle file operation errors consistently.
    
    Args:
        operation: The file operation being performed
        file_path: Path to the file
        cause: The exception that occurred
        fallback_action: Optional action to take instead of raising
    """
    import logging
    logger = logging.getLogger(__name__)
    
    error = FileOperationError(operation, file_path, cause)
    logger.error(str(error), extra={"error_details": error.to_dict()})
    
    if fallback_action:
        logger.info(f"Fallback action: {fallback_action}")


def handle_validation_error(
    field: str,
    value: Any,
    reason: str,
    context: dict[str, Any] | None = None,
) -> None:
    """Handle validation errors consistently.
    
    Args:
        field: The field being validated
        value: The invalid value
        reason: Why validation failed
        context: Additional context information
    """
    import logging
    logger = logging.getLogger(__name__)
    
    error = ValidationError(f"Invalid {field}: {reason}")
    error.details["field"] = field
    error.details["value"] = str(value)
    if context:
        error.details.update(context)
    
    logger.error(str(error), extra={"error_details": error.to_dict()})


def handle_service_unavailable(
    service_name: str,
    cause: Exception,
    fallback_message: str | None = None,
) -> None:
    """Handle service unavailable errors consistently.
    
    Args:
        service_name: Name of the unavailable service
        cause: The exception that occurred
        fallback_message: Optional message about fallback behavior
    """
    import logging
    logger = logging.getLogger(__name__)
    
    error = ServiceUnavailableError(service_name, {"cause": str(cause)})
    logger.error(str(error), extra={"error_details": error.to_dict()})
    
    if fallback_message:
        logger.info(fallback_message)


def convert_to_error_response(
    exception: Exception,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Convert any exception to a standardized error response.
    
    Args:
        exception: The exception to convert
        context: Additional context information
        
    Returns:
        Standardized error response dictionary
    """
    if isinstance(exception, AsmblrException):
        response = exception.to_dict()
    else:
        response = {
            "error_type": exception.__class__.__name__,
            "message": str(exception),
            "details": {},
        }
    
    if context:
        response["context"] = context
    
    return response


# ============================================================================
# EXCEPTION MAPPING
# ============================================================================

def map_exception_to_error_type(exception: Exception) -> str:
    """Map common exceptions to standardized error types.
    
    Args:
        exception: The exception to map
        
    Returns:
        Standardized error type string
    """
    exception_type_mapping = {
        ValueError: "validation_error",
        FileNotFoundError: "resource_not_found",
        ConnectionError: "network_error",
        TimeoutError: "timeout_error",
        json.JSONDecodeError: "data_processing_error",
        PermissionError: "authorization_error",
        RuntimeError: "processing_error",
    }
    
    return exception_type_mapping.get(type(exception), "unknown_error")


def is_retryable_exception(exception: Exception) -> bool:
    """Determine if an exception is retryable.
    
    Args:
        exception: The exception to check
        
    Returns:
        True if the exception type is typically retryable
    """
    retryable_exceptions = (
        ConnectionError,
        TimeoutError,
        NetworkError,
    )
    
    return isinstance(exception, retryable_exceptions) or "timeout" in str(exception).lower()


def should_suppress_exception_details(exception: Exception) -> bool:
    """Determine if exception details should be suppressed for security.
    
    Args:
        exception: The exception to check
        
    Returns:
        True if details should be suppressed (e.g., for security reasons)
    """
    # Suppress detailed error messages for security-sensitive exceptions
    security_sensitive_patterns = [
        "authentication",
        "authorization", 
        "credential",
        "token",
        "key",
    ]
    
    exception_str = str(exception).lower()
    return any(pattern in exception_str for pattern in security_sensitive_patterns)
