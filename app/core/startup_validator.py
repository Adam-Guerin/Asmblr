"""
Comprehensive startup validation for Asmblr
Validates all configuration and system requirements at startup
"""

import os
import sys
import platform
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from loguru import logger

from app.core.error_formatter import (
    format_config_error,
    format_file_error,
    format_security_error,
    ErrorSeverity
)
from app.core.timeout_config import get_timeout_config


@dataclass
class ValidationResult:
    """Result of a validation check"""
    is_valid: bool
    message: str
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    suggestion: Optional[str] = None
    component: Optional[str] = None


@dataclass
class StartupValidationReport:
    """Complete startup validation report"""
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
        
        summary = f"🔍 Startup Validation Summary:\n"
        summary += f"   Total checks: {total}\n"
        summary += f"   ✅ Passed: {passed}\n"
        summary += f"   ❌ Failed: {failed}\n"
        summary += f"   🚨 Critical: {len(self.critical_issues)}\n"
        summary += f"   ⚠️ Warnings: {len(self.warnings)}\n"
        
        return summary


class StartupValidator:
    """Comprehensive startup validation system"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).resolve().parents[2]
        self.validations: List[ValidationResult] = []
    
    def validate_all(self) -> StartupValidationReport:
        """Run all startup validations"""
        logger.info("🔍 Starting comprehensive startup validation...")
        
        self.validations.clear()
        
        # Core system validations
        self._validate_python_version()
        self._validate_platform()
        self._validate_permissions()
        
        # Configuration validations
        self._validate_environment_files()
        self._validate_critical_paths()
        self._validate_timeout_configuration()
        
        # Security validations
        self._validate_file_permissions()
        self._validate_environment_security()
        
        # Resource validations
        self._validate_disk_space()
        self._validate_memory_requirements()
        
        # Dependency validations
        self._validate_core_dependencies()
        self._validate_optional_dependencies()
        
        # Generate report
        return self._generate_report()
    
    def _validate_python_version(self) -> None:
        """Validate Python version compatibility"""
        version_info = sys.version_info
        min_version = (3, 8)
        
        if version_info >= min_version:
            self.validations.append(ValidationResult(
                is_valid=True,
                message=f"Python version {version_info.major}.{version_info.minor}.{version_info.micro} is supported",
                severity=ErrorSeverity.LOW,
                component="python"
            ))
        else:
            self.validations.append(ValidationResult(
                is_valid=False,
                message=f"Python version {version_info.major}.{version_info.minor}.{version_info.micro} is not supported (minimum: 3.8)",
                severity=ErrorSeverity.CRITICAL,
                suggestion="Please upgrade to Python 3.8 or higher",
                component="python"
            ))
    
    def _validate_platform(self) -> None:
        """Validate platform compatibility"""
        system = platform.system().lower()
        architecture = platform.machine().lower()
        
        supported_platforms = ['windows', 'linux', 'darwin']
        
        if system in supported_platforms:
            self.validations.append(ValidationResult(
                is_valid=True,
                message=f"Platform {platform.platform()} is supported",
                severity=ErrorSeverity.LOW,
                component="platform"
            ))
        else:
            self.validations.append(ValidationResult(
                is_valid=False,
                message=f"Platform {system} is not officially supported",
                severity=ErrorSeverity.HIGH,
                suggestion="Consider using a supported platform: Windows, Linux, or macOS",
                component="platform"
            ))
        
        # Check for 64-bit architecture
        if '64' in architecture or 'amd64' in architecture:
            self.validations.append(ValidationResult(
                is_valid=True,
                message=f"64-bit architecture {architecture} detected",
                severity=ErrorSeverity.LOW,
                component="platform"
            ))
        else:
            self.validations.append(ValidationResult(
                is_valid=False,
                message=f"32-bit architecture {architecture} detected - may have limitations",
                severity=ErrorSeverity.MEDIUM,
                suggestion="64-bit architecture recommended for better performance",
                component="platform"
            ))
    
    def _validate_permissions(self) -> None:
        """Validate basic file permissions"""
        try:
            # Test write permissions in base directory
            test_file = self.base_dir / ".permission_test"
            test_file.write_text("test", encoding="utf-8")
            test_file.unlink()
            
            self.validations.append(ValidationResult(
                is_valid=True,
                message="Write permissions validated in base directory",
                severity=ErrorSeverity.LOW,
                component="permissions"
            ))
        except PermissionError:
            self.validations.append(ValidationResult(
                is_valid=False,
                message="Insufficient write permissions in base directory",
                severity=ErrorSeverity.CRITICAL,
                suggestion="Check directory permissions and user access rights",
                component="permissions"
            ))
        except Exception as e:
            self.validations.append(ValidationResult(
                is_valid=False,
                message=f"Permission check failed: {e}",
                severity=ErrorSeverity.HIGH,
                suggestion="Verify file system access and permissions",
                component="permissions"
            ))
    
    def _validate_environment_files(self) -> None:
        """Validate environment configuration files"""
        env_file = self.base_dir / ".env"
        env_example = self.base_dir / "config" / ".env.example"
        env_light = self.base_dir / ".env.light"
        
        # Check if at least one env file exists
        if env_file.exists() or env_light.exists():
            self.validations.append(ValidationResult(
                is_valid=True,
                message="Environment configuration file found",
                severity=ErrorSeverity.LOW,
                component="environment"
            ))
        else:
            self.validations.append(ValidationResult(
                is_valid=False,
                message="No environment configuration file found",
                severity=ErrorSeverity.HIGH,
                suggestion=f"Copy {env_example} to {env_file} and configure your settings",
                component="environment"
            ))
        
        # Validate env file format if it exists
        for env_path in [env_file, env_light]:
            if env_path.exists():
                try:
                    content = env_path.read_text(encoding="utf-8")
                    lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
                    
                    # Check for basic KEY=VALUE format
                    invalid_lines = [line for line in lines if '=' not in line or line.startswith('=')]
                    
                    if invalid_lines:
                        self.validations.append(ValidationResult(
                            is_valid=False,
                            message=f"Invalid format in {env_path.name}: {len(invalid_lines)} lines",
                            severity=ErrorSeverity.MEDIUM,
                            suggestion="Fix lines that don't follow KEY=VALUE format",
                            component="environment"
                        ))
                    else:
                        self.validations.append(ValidationResult(
                            is_valid=True,
                            message=f"Environment file {env_path.name} format is valid",
                            severity=ErrorSeverity.LOW,
                            component="environment"
                        ))
                except Exception as e:
                    self.validations.append(ValidationResult(
                        is_valid=False,
                        message=f"Failed to read {env_path.name}: {e}",
                        severity=ErrorSeverity.HIGH,
                        suggestion="Check file permissions and encoding",
                        component="environment"
                    ))
    
    def _validate_critical_paths(self) -> None:
        """Validate critical directory structure"""
        critical_dirs = [
            "app",
            "data", 
            "configs",
            "runs"
        ]
        
        for dir_name in critical_dirs:
            dir_path = self.base_dir / dir_name
            if dir_path.exists() and dir_path.is_dir():
                self.validations.append(ValidationResult(
                    is_valid=True,
                    message=f"Critical directory {dir_name}/ exists",
                    severity=ErrorSeverity.LOW,
                    component="paths"
                ))
            else:
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    self.validations.append(ValidationResult(
                        is_valid=True,
                        message=f"Created missing directory {dir_name}/",
                        severity=ErrorSeverity.LOW,
                        component="paths"
                    ))
                except Exception as e:
                    self.validations.append(ValidationResult(
                        is_valid=False,
                        message=f"Cannot create critical directory {dir_name}/: {e}",
                        severity=ErrorSeverity.HIGH,
                        suggestion="Check permissions and disk space",
                        component="paths"
                    ))
    
    def _validate_timeout_configuration(self) -> None:
        """Validate timeout configuration"""
        try:
            timeout_config = get_timeout_config()
            validation = timeout_config.validate_timeouts()
            
            if validation['valid']:
                self.validations.append(ValidationResult(
                    is_valid=True,
                    message="Timeout configuration is valid",
                    severity=ErrorSeverity.LOW,
                    component="timeouts"
                ))
            else:
                for issue in validation['issues']:
                    self.validations.append(ValidationResult(
                        is_valid=False,
                        message=f"Timeout configuration issue: {issue}",
                        severity=ErrorSeverity.MEDIUM,
                        suggestion="Review and adjust timeout values",
                        component="timeouts"
                    ))
        except Exception as e:
            self.validations.append(ValidationResult(
                is_valid=False,
                message=f"Failed to validate timeout configuration: {e}",
                severity=ErrorSeverity.HIGH,
                suggestion="Check timeout configuration files",
                component="timeouts"
            ))
    
    def _validate_file_permissions(self) -> None:
        """Validate file permissions for security"""
        sensitive_files = [
            ".env",
            ".env.light",
            "config/.env.example"
        ]
        
        for file_name in sensitive_files:
            file_path = self.base_dir / file_name
            if file_path.exists():
                try:
                    stat = file_path.stat()
                    # Check if file is readable by owner only (basic security check)
                    mode = oct(stat.st_mode)[-3:]
                    
                    if mode in ['600', '640', '644']:
                        self.validations.append(ValidationResult(
                            is_valid=True,
                            message=f"File permissions for {file_name} are appropriate ({mode})",
                            severity=ErrorSeverity.LOW,
                            component="security"
                        ))
                    else:
                        self.validations.append(ValidationResult(
                            is_valid=False,
                            message=f"File {file_name} has permissive permissions ({mode})",
                            severity=ErrorSeverity.MEDIUM,
                            suggestion=f"Consider restricting permissions: chmod 600 {file_name}",
                            component="security"
                        ))
                except Exception as e:
                    self.validations.append(ValidationResult(
                        is_valid=False,
                        message=f"Cannot check permissions for {file_name}: {e}",
                        severity=ErrorSeverity.MEDIUM,
                        component="security"
                    ))
    
    def _validate_environment_security(self) -> None:
        """Validate environment variable security"""
        sensitive_vars = [
            "API_KEY",
            "SECRET_KEY",
            "DATABASE_URL",
            "REDIS_PASSWORD"
        ]
        
        exposed_count = 0
        for var in sensitive_vars:
            if os.getenv(var):
                exposed_count += 1
        
        if exposed_count == 0:
            self.validations.append(ValidationResult(
                is_valid=True,
                message="No sensitive environment variables detected in current process",
                severity=ErrorSeverity.LOW,
                component="security"
            ))
        else:
            self.validations.append(ValidationResult(
                is_valid=False,
                message=f"{exposed_count} sensitive environment variables may be exposed",
                severity=ErrorSeverity.MEDIUM,
                suggestion="Ensure sensitive variables are properly secured and not logged",
                component="security"
            ))
    
    def _validate_disk_space(self) -> None:
        """Validate available disk space"""
        try:
            import shutil
            total, used, free = shutil.disk_usage(self.base_dir)
            free_gb = free // (1024**3)
            
            if free_gb >= 1:  # At least 1GB free
                self.validations.append(ValidationResult(
                    is_valid=True,
                    message=f"Sufficient disk space available: {free_gb}GB free",
                    severity=ErrorSeverity.LOW,
                    component="resources"
                ))
            else:
                self.validations.append(ValidationResult(
                    is_valid=False,
                    message=f"Low disk space: only {free_gb}GB free",
                    severity=ErrorSeverity.HIGH,
                    suggestion="Free up disk space or move to a different location",
                    component="resources"
                ))
        except Exception as e:
            self.validations.append(ValidationResult(
                is_valid=False,
                message=f"Cannot check disk space: {e}",
                severity=ErrorSeverity.MEDIUM,
                component="resources"
            ))
    
    def _validate_memory_requirements(self) -> None:
        """Validate memory requirements"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)
            
            if available_gb >= 2:  # At least 2GB available
                self.validations.append(ValidationResult(
                    is_valid=True,
                    message=f"Sufficient memory available: {available_gb:.1f}GB free",
                    severity=ErrorSeverity.LOW,
                    component="resources"
                ))
            elif available_gb >= 1:
                self.validations.append(ValidationResult(
                    is_valid=False,
                    message=f"Low memory available: {available_gb:.1f}GB free",
                    severity=ErrorSeverity.MEDIUM,
                    suggestion="Consider closing other applications or enabling lightweight mode",
                    component="resources"
                ))
            else:
                self.validations.append(ValidationResult(
                    is_valid=False,
                    message=f"Very low memory available: {available_gb:.1f}GB free",
                    severity=ErrorSeverity.HIGH,
                    suggestion="Enable lightweight mode or free up memory",
                    component="resources"
                ))
        except ImportError:
            self.validations.append(ValidationResult(
                is_valid=True,
                message="Memory validation skipped (psutil not available)",
                severity=ErrorSeverity.LOW,
                component="resources"
            ))
        except Exception as e:
            self.validations.append(ValidationResult(
                is_valid=False,
                message=f"Cannot check memory: {e}",
                severity=ErrorSeverity.MEDIUM,
                component="resources"
            ))
    
    def _validate_core_dependencies(self) -> None:
        """Validate core dependencies are available"""
        core_deps = [
            "streamlit",
            "fastapi", 
            "loguru",
            "pydantic",
            "crewai",
            "langchain"
        ]
        
        for dep in core_deps:
            try:
                __import__(dep)
                self.validations.append(ValidationResult(
                    is_valid=True,
                    message=f"Core dependency {dep} is available",
                    severity=ErrorSeverity.LOW,
                    component="dependencies"
                ))
            except ImportError:
                self.validations.append(ValidationResult(
                    is_valid=False,
                    message=f"Core dependency {dep} is missing",
                    severity=ErrorSeverity.CRITICAL,
                    suggestion=f"Install with: pip install {dep}",
                    component="dependencies"
                ))
    
    def _validate_optional_dependencies(self) -> None:
        """Validate optional dependencies with warnings"""
        optional_deps = [
            "torch",
            "transformers",
            "diffusers",
            "psutil"
        ]
        
        for dep in optional_deps:
            try:
                __import__(dep)
                self.validations.append(ValidationResult(
                    is_valid=True,
                    message=f"Optional dependency {dep} is available",
                    severity=ErrorSeverity.LOW,
                    component="dependencies"
                ))
            except ImportError:
                self.validations.append(ValidationResult(
                    is_valid=True,  # Not critical, but worth noting
                    message=f"Optional dependency {dep} is not available (some features may be limited)",
                    severity=ErrorSeverity.LOW,
                    suggestion=f"Install with: pip install {dep} (optional)",
                    component="dependencies"
                ))
    
    def _generate_report(self) -> StartupValidationReport:
        """Generate the final validation report"""
        critical_issues = [v for v in self.validations if v.severity == ErrorSeverity.CRITICAL and not v.is_valid]
        warnings = [v for v in self.validations if v.severity == ErrorSeverity.MEDIUM and not v.is_valid]
        info_messages = [v for v in self.validations if v.severity == ErrorSeverity.LOW]
        
        overall_valid = len(critical_issues) == 0
        
        return StartupValidationReport(
            overall_valid=overall_valid,
            validations=self.validations,
            critical_issues=critical_issues,
            warnings=warnings,
            info_messages=info_messages
        )


def run_startup_validation(base_dir: Optional[Path] = None) -> StartupValidationReport:
    """Run comprehensive startup validation"""
    validator = StartupValidator(base_dir)
    report = validator.validate_all()
    
    # Log results
    logger.info(report.get_summary())
    
    if not report.overall_valid:
        logger.error("🚨 Critical issues detected - application may not function properly")
        for issue in report.critical_issues:
            logger.error(format_config_error(issue.message, issue.severity))
    elif report.warnings:
        logger.warning("⚠️ Warnings detected - some features may be limited")
        for warning in report.warnings:
            logger.warning(format_config_error(warning.message, warning.severity))
    else:
        logger.info("✅ All validations passed - system is ready")
    
    return report


def validate_before_startup() -> bool:
    """Quick validation before application startup"""
    report = run_startup_validation()
    return report.overall_valid
