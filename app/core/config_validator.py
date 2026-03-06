"""
Comprehensive configuration validation for Asmblr
Validates all configuration values and provides detailed feedback
"""

import os
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
import ipaddress

from app.core.error_formatter import format_config_error, ErrorSeverity
from app.core.logging_system import get_logger


@dataclass
class ValidationResult:
    """Result of a configuration validation"""
    is_valid: bool
    field_name: str
    current_value: Any
    message: str
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    suggested_value: Optional[Any] = None
    validation_rule: Optional[str] = None


@dataclass
class ConfigValidationReport:
    """Complete configuration validation report"""
    overall_valid: bool
    validations: List[ValidationResult]
    critical_issues: List[ValidationResult]
    warnings: List[ValidationResult]
    info_messages: List[ValidationResult]
    
    def get_summary(self) -> str:
        """Get a summary of the validation results"""
        total = len(self.validations)
        passed = sum(1 for v in self.validations if v.is_valid)
        failed = total - passed
        
        summary = f"🔍 Configuration Validation Summary:\n"
        summary += f"   Total checks: {total}\n"
        summary += f"   ✅ Passed: {passed}\n"
        summary += f"   ❌ Failed: {failed}\n"
        summary += f"   🚨 Critical: {len(self.critical_issues)}\n"
        summary += f"   ⚠️ Warnings: {len(self.warnings)}\n"
        
        return summary


class ConfigValidator:
    """Comprehensive configuration validation system"""
    
    def __init__(self):
        self.logger = get_logger()
        self.validations: List[ValidationResult] = []
        
        # Validation rules
        self.validation_rules = self._setup_validation_rules()
    
    def _setup_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Setup validation rules for configuration fields"""
        return {
            # Ollama Configuration
            "OLLAMA_BASE_URL": {
                "type": "url",
                "required": True,
                "default": "http://localhost:11434",
                "description": "Ollama API base URL"
            },
            "GENERAL_MODEL": {
                "type": "string",
                "required": True,
                "pattern": r"^[a-zA-Z0-9_\-:]+$",
                "default": "llama3.1:8b",
                "description": "General purpose model name"
            },
            "CODE_MODEL": {
                "type": "string",
                "required": True,
                "pattern": r"^[a-zA-Z0-9_\-:]+$",
                "default": "qwen2.5-coder:7b",
                "description": "Code generation model name"
            },
            
            # API Configuration
            "API_HOST": {
                "type": "ip_or_hostname",
                "required": True,
                "default": "127.0.0.1",
                "description": "API server host"
            },
            "API_PORT": {
                "type": "port",
                "required": True,
                "min": 1024,
                "max": 65535,
                "default": "8000",
                "description": "API server port"
            },
            "UI_HOST": {
                "type": "ip_or_hostname",
                "required": True,
                "default": "127.0.0.1",
                "description": "UI server host"
            },
            "UI_PORT": {
                "type": "port",
                "required": True,
                "min": 1024,
                "max": 65535,
                "default": "8501",
                "description": "UI server port"
            },
            
            # Performance Configuration
            "REQUEST_TIMEOUT": {
                "type": "integer",
                "required": True,
                "min": 5,
                "max": 300,
                "default": "20",
                "description": "Request timeout in seconds"
            },
            "MAX_SOURCES": {
                "type": "integer",
                "required": True,
                "min": 1,
                "max": 50,
                "default": "8",
                "description": "Maximum number of sources to analyze"
            },
            "RETRY_MAX_ATTEMPTS": {
                "type": "integer",
                "required": True,
                "min": 1,
                "max": 10,
                "default": "3",
                "description": "Maximum retry attempts"
            },
            
            # Threshold Configuration
            "MARKET_SIGNAL_THRESHOLD": {
                "type": "integer",
                "required": True,
                "min": 10,
                "max": 100,
                "default": "40",
                "description": "Market signal threshold"
            },
            "SIGNAL_QUALITY_THRESHOLD": {
                "type": "integer",
                "required": True,
                "min": 10,
                "max": 100,
                "default": "45",
                "description": "Signal quality threshold"
            },
            "IDEA_ACTIONABILITY_MIN_SCORE": {
                "type": "integer",
                "required": True,
                "min": 0,
                "max": 100,
                "default": "55",
                "description": "Minimum actionability score for ideas"
            },
            
            # Learning Configuration
            "LEARNING_EXPLORATION_RATE": {
                "type": "float",
                "required": True,
                "min": 0.0,
                "max": 1.0,
                "default": "0.18",
                "description": "Learning exploration rate"
            },
            "LEARNING_HISTORY_MAX_RUNS": {
                "type": "integer",
                "required": True,
                "min": 10,
                "max": 1000,
                "default": "200",
                "description": "Maximum learning history runs"
            },
            
            # Feature Flags
            "ENABLE_CACHE": {
                "type": "boolean",
                "required": True,
                "default": "false",
                "description": "Enable caching"
            },
            "ENABLE_LOGO_DIFFUSION": {
                "type": "boolean",
                "required": True,
                "default": "false",
                "description": "Enable logo generation"
            },
            "ENABLE_VIDEO_GENERATION": {
                "type": "boolean",
                "required": True,
                "default": "true",
                "description": "Enable video generation"
            },
            
            # File Paths
            "RUNS_DIR": {
                "type": "path",
                "required": True,
                "default": "runs",
                "description": "Runs directory path"
            },
            "DATA_DIR": {
                "type": "path",
                "required": True,
                "default": "data",
                "description": "Data directory path"
            },
            "CONFIG_DIR": {
                "type": "path",
                "required": True,
                "default": "configs",
                "description": "Configuration directory path"
            }
        }
    
    def validate_all(self) -> ConfigValidationReport:
        """Validate all configuration values"""
        self.logger.info("Starting comprehensive configuration validation...")
        
        self.validations.clear()
        
        # Validate each configuration field
        for field_name, rule in self.validation_rules.items():
            self._validate_field(field_name, rule)
        
        # Validate cross-field dependencies
        self._validate_dependencies()
        
        # Validate security settings
        self._validate_security()
        
        # Generate report
        return self._generate_report()
    
    def _validate_field(self, field_name: str, rule: Dict[str, Any]) -> None:
        """Validate a single configuration field"""
        current_value = os.getenv(field_name)
        
        # Check if required field is missing
        if rule.get("required", False) and not current_value:
            self.validations.append(ValidationResult(
                is_valid=False,
                field_name=field_name,
                current_value=current_value,
                message=f"Required field {field_name} is missing",
                severity=ErrorSeverity.CRITICAL,
                suggested_value=rule.get("default"),
                validation_rule="required"
            ))
            return
        
        # Use default if value is missing
        if not current_value:
            current_value = rule.get("default")
        
        # Validate based on type
        field_type = rule.get("type", "string")
        validation_method = getattr(self, f"_validate_{field_type}", self._validate_string)
        result = validation_method(field_name, current_value, rule)
        
        if result:
            self.validations.append(result)
    
    def _validate_string(self, field_name: str, value: str, rule: Dict[str, Any]) -> Optional[ValidationResult]:
        """Validate string field"""
        if not isinstance(value, str):
            return ValidationResult(
                is_valid=False,
                field_name=field_name,
                current_value=value,
                message=f"{field_name} must be a string",
                severity=ErrorSeverity.MEDIUM,
                suggested_value=str(rule.get("default", "")),
                validation_rule="type"
            )
        
        # Check pattern if specified
        pattern = rule.get("pattern")
        if pattern and not re.match(pattern, value):
            return ValidationResult(
                is_valid=False,
                field_name=field_name,
                current_value=value,
                message=f"{field_name} does not match required pattern: {pattern}",
                severity=ErrorSeverity.MEDIUM,
                suggested_value=rule.get("default"),
                validation_rule="pattern"
            )
        
        return ValidationResult(
            is_valid=True,
            field_name=field_name,
            current_value=value,
            message=f"{field_name} is valid",
            severity=ErrorSeverity.LOW
        )
    
    def _validate_url(self, field_name: str, value: str, rule: Dict[str, Any]) -> Optional[ValidationResult]:
        """Validate URL field"""
        try:
            parsed = urlparse(value)
            if not parsed.scheme or not parsed.netloc:
                return ValidationResult(
                    is_valid=False,
                    field_name=field_name,
                    current_value=value,
                    message=f"{field_name} is not a valid URL",
                    severity=ErrorSeverity.MEDIUM,
                    suggested_value=rule.get("default"),
                    validation_rule="url_format"
                )
            
            # Check if URL is reachable (optional)
            if rule.get("check_reachable", False):
                # Could add HTTP request here to check reachability
                pass
            
        except Exception:
            return ValidationResult(
                is_valid=False,
                field_name=field_name,
                current_value=value,
                message=f"{field_name} URL parsing failed",
                severity=ErrorSeverity.MEDIUM,
                suggested_value=rule.get("default"),
                validation_rule="url_parse"
            )
        
        return ValidationResult(
            is_valid=True,
            field_name=field_name,
            current_value=value,
            message=f"{field_name} URL is valid",
            severity=ErrorSeverity.LOW
        )
    
    def _validate_ip_or_hostname(self, field_name: str, value: str, rule: Dict[str, Any]) -> Optional[ValidationResult]:
        """Validate IP address or hostname"""
        try:
            # Try to parse as IP address
            ipaddress.ip_address(value)
        except ValueError:
            # Not an IP, check if it's a valid hostname
            if not re.match(r"^[a-zA-Z0-9\-\.]+$", value):
                return ValidationResult(
                    is_valid=False,
                    field_name=field_name,
                    current_value=value,
                    message=f"{field_name} is not a valid IP address or hostname",
                    severity=ErrorSeverity.MEDIUM,
                    suggested_value=rule.get("default"),
                    validation_rule="ip_or_hostname"
                )
        
        return ValidationResult(
            is_valid=True,
            field_name=field_name,
            current_value=value,
            message=f"{field_name} is valid",
            severity=ErrorSeverity.LOW
        )
    
    def _validate_port(self, field_name: str, value: str, rule: Dict[str, Any]) -> Optional[ValidationResult]:
        """Validate port number"""
        try:
            port = int(value)
            min_port = rule.get("min", 1)
            max_port = rule.get("max", 65535)
            
            if not (min_port <= port <= max_port):
                return ValidationResult(
                    is_valid=False,
                    field_name=field_name,
                    current_value=value,
                    message=f"{field_name} must be between {min_port} and {max_port}",
                    severity=ErrorSeverity.MEDIUM,
                    suggested_value=str(rule.get("default")),
                    validation_rule="port_range"
                )
            
        except ValueError:
            return ValidationResult(
                is_valid=False,
                field_name=field_name,
                current_value=value,
                message=f"{field_name} must be a valid port number",
                severity=ErrorSeverity.MEDIUM,
                suggested_value=str(rule.get("default")),
                validation_rule="port_type"
            )
        
        return ValidationResult(
            is_valid=True,
            field_name=field_name,
            current_value=value,
            message=f"{field_name} port is valid",
            severity=ErrorSeverity.LOW
        )
    
    def _validate_integer(self, field_name: str, value: str, rule: Dict[str, Any]) -> Optional[ValidationResult]:
        """Validate integer field"""
        try:
            int_value = int(value)
            min_val = rule.get("min")
            max_val = rule.get("max")
            
            if min_val is not None and int_value < min_val:
                return ValidationResult(
                    is_valid=False,
                    field_name=field_name,
                    current_value=value,
                    message=f"{field_name} must be at least {min_val}",
                    severity=ErrorSeverity.MEDIUM,
                    suggested_value=str(rule.get("default")),
                    validation_rule="integer_min"
                )
            
            if max_val is not None and int_value > max_val:
                return ValidationResult(
                    is_valid=False,
                    field_name=field_name,
                    current_value=value,
                    message=f"{field_name} must be at most {max_val}",
                    severity=ErrorSeverity.MEDIUM,
                    suggested_value=str(rule.get("default")),
                    validation_rule="integer_max"
                )
            
        except ValueError:
            return ValidationResult(
                is_valid=False,
                field_name=field_name,
                current_value=value,
                message=f"{field_name} must be a valid integer",
                severity=ErrorSeverity.MEDIUM,
                suggested_value=str(rule.get("default")),
                validation_rule="integer_type"
            )
        
        return ValidationResult(
            is_valid=True,
            field_name=field_name,
            current_value=value,
            message=f"{field_name} integer is valid",
            severity=ErrorSeverity.LOW
        )
    
    def _validate_float(self, field_name: str, value: str, rule: Dict[str, Any]) -> Optional[ValidationResult]:
        """Validate float field"""
        try:
            float_value = float(value)
            min_val = rule.get("min")
            max_val = rule.get("max")
            
            if min_val is not None and float_value < min_val:
                return ValidationResult(
                    is_valid=False,
                    field_name=field_name,
                    current_value=value,
                    message=f"{field_name} must be at least {min_val}",
                    severity=ErrorSeverity.MEDIUM,
                    suggested_value=str(rule.get("default")),
                    validation_rule="float_min"
                )
            
            if max_val is not None and float_value > max_val:
                return ValidationResult(
                    is_valid=False,
                    field_name=field_name,
                    current_value=value,
                    message=f"{field_name} must be at most {max_val}",
                    severity=ErrorSeverity.MEDIUM,
                    suggested_value=str(rule.get("default")),
                    validation_rule="float_max"
                )
            
        except ValueError:
            return ValidationResult(
                is_valid=False,
                field_name=field_name,
                current_value=value,
                message=f"{field_name} must be a valid float",
                severity=ErrorSeverity.MEDIUM,
                suggested_value=str(rule.get("default")),
                validation_rule="float_type"
            )
        
        return ValidationResult(
            is_valid=True,
            field_name=field_name,
            current_value=value,
            message=f"{field_name} float is valid",
            severity=ErrorSeverity.LOW
        )
    
    def _validate_boolean(self, field_name: str, value: str, rule: Dict[str, Any]) -> Optional[ValidationResult]:
        """Validate boolean field"""
        valid_values = ["true", "false", "1", "0", "yes", "no", "on", "off"]
        
        if value.lower() not in valid_values:
            return ValidationResult(
                is_valid=False,
                field_name=field_name,
                current_value=value,
                message=f"{field_name} must be one of: {', '.join(valid_values)}",
                severity=ErrorSeverity.MEDIUM,
                suggested_value=str(rule.get("default")),
                validation_rule="boolean_values"
            )
        
        return ValidationResult(
            is_valid=True,
            field_name=field_name,
            current_value=value,
            message=f"{field_name} boolean is valid",
            severity=ErrorSeverity.LOW
        )
    
    def _validate_path(self, field_name: str, value: str, rule: Dict[str, Any]) -> Optional[ValidationResult]:
        """Validate path field"""
        try:
            path = Path(value)
            
            # Check for invalid characters
            invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
            for char in invalid_chars:
                if char in str(path):
                    return ValidationResult(
                        is_valid=False,
                        field_name=field_name,
                        current_value=value,
                        message=f"{field_name} contains invalid character: {char}",
                        severity=ErrorSeverity.MEDIUM,
                        suggested_value=rule.get("default"),
                        validation_rule="path_chars"
                    )
            
            # Check if path is absolute (optional requirement)
            if rule.get("require_absolute", False) and not path.is_absolute():
                return ValidationResult(
                    is_valid=False,
                    field_name=field_name,
                    current_value=value,
                    message=f"{field_name} must be an absolute path",
                    severity=ErrorSeverity.MEDIUM,
                    suggested_value=str(Path.cwd() / rule.get("default")),
                    validation_rule="absolute_path"
                )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                field_name=field_name,
                current_value=value,
                message=f"{field_name} path validation failed: {e}",
                severity=ErrorSeverity.MEDIUM,
                suggested_value=rule.get("default"),
                validation_rule="path_error"
            )
        
        return ValidationResult(
            is_valid=True,
            field_name=field_name,
            current_value=value,
            message=f"{field_name} path is valid",
            severity=ErrorSeverity.LOW
        )
    
    def _validate_dependencies(self) -> None:
        """Validate cross-field dependencies"""
        # Check port conflicts
        api_port = os.getenv("API_PORT", "8000")
        ui_port = os.getenv("UI_PORT", "8501")
        
        if api_port == ui_port:
            self.validations.append(ValidationResult(
                is_valid=False,
                field_name="API_PORT/UI_PORT",
                current_value=f"API:{api_port}, UI:{ui_port}",
                message="API and UI ports cannot be the same",
                severity=ErrorSeverity.CRITICAL,
                suggested_value="API:8000, UI:8501",
                validation_rule="port_conflict"
            ))
        
        # Check timeout relationships
        request_timeout = int(os.getenv("REQUEST_TIMEOUT", "20"))
        retry_max_wait = int(os.getenv("RETRY_MAX_WAIT", "6"))
        
        if retry_max_wait > request_timeout:
            self.validations.append(ValidationResult(
                is_valid=False,
                field_name="RETRY_MAX_WAIT/REQUEST_TIMEOUT",
                current_value=f"Retry:{retry_max_wait}, Request:{request_timeout}",
                message="Retry max wait should not exceed request timeout",
                severity=ErrorSeverity.MEDIUM,
                suggested_value="Set retry_max_wait <= request_timeout",
                validation_rule="timeout_relationship"
            ))
    
    def _validate_security(self) -> None:
        """Validate security-related settings"""
        # Check for sensitive data in environment
        sensitive_patterns = [
            ("password", r".*password.*"),
            ("secret", r".*secret.*"),
            ("key", r".*key.*"),
            ("token", r".*token.*")
        ]
        
        for pattern_name, pattern in sensitive_patterns:
            for env_var, value in os.environ.items():
                if re.match(pattern, env_var.lower()) and value:
                    self.validations.append(ValidationResult(
                        is_valid=True,  # This is informational, not an error
                        field_name=env_var,
                        current_value="***",
                        message=f"Sensitive field {env_var} detected",
                        severity=ErrorSeverity.LOW,
                        validation_rule="sensitive_field"
                    ))
    
    def _generate_report(self) -> ConfigValidationReport:
        """Generate the final validation report"""
        critical_issues = [v for v in self.validations if v.severity == ErrorSeverity.CRITICAL and not v.is_valid]
        warnings = [v for v in self.validations if v.severity == ErrorSeverity.MEDIUM and not v.is_valid]
        info_messages = [v for v in self.validations if v.severity == ErrorSeverity.LOW]
        
        overall_valid = len(critical_issues) == 0
        
        return ConfigValidationReport(
            overall_valid=overall_valid,
            validations=self.validations,
            critical_issues=critical_issues,
            warnings=warnings,
            info_messages=info_messages
        )
    
    def get_field_suggestions(self, field_name: str) -> List[str]:
        """Get suggestions for fixing a specific field"""
        suggestions = []
        
        if field_name in self.validation_rules:
            rule = self.validation_rules[field_name]
            suggestions.append(f"Default value: {rule.get('default')}")
            suggestions.append(f"Description: {rule.get('description')}")
            suggestions.append(f"Type: {rule.get('type')}")
            
            if rule.get("min") is not None:
                suggestions.append(f"Minimum value: {rule['min']}")
            if rule.get("max") is not None:
                suggestions.append(f"Maximum value: {rule['max']}")
            if rule.get("pattern"):
                suggestions.append(f"Pattern: {rule['pattern']}")
        
        return suggestions


def validate_configuration() -> ConfigValidationReport:
    """Validate all configuration and return report"""
    validator = ConfigValidator()
    report = validator.validate_all()
    
    # Log results
    logger = get_logger()
    logger.info(report.get_summary())
    
    if not report.overall_valid:
        logger.error("🚨 Critical configuration issues detected")
        for issue in report.critical_issues:
            logger.error(format_config_error(issue.message, issue.severity))
    elif report.warnings:
        logger.warning("⚠️ Configuration warnings detected")
        for warning in report.warnings:
            logger.warning(format_config_error(warning.message, warning.severity))
    else:
        logger.info("✅ All configuration validations passed")
    
    return report
