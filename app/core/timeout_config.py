"""
Centralized timeout configuration for Asmblr
Provides consistent timeout management across all components
"""

import os
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class TimeoutConfig:
    """Centralized timeout configuration with validation"""
    
    # Network timeouts
    request_timeout: int = 30
    connection_timeout: int = 30
    read_timeout: int = 60
    write_timeout: int = 60
    
    # MVP timeouts
    mvp_install_timeout: int = 600
    mvp_build_timeout: int = 300
    mvp_test_timeout: int = 300
    mvp_dev_startup_timeout: int = 35
    
    # Worker timeouts
    rq_default_timeout: int = 7200
    worker_timeout: int = 300
    
    # Cache timeouts
    cache_ttl: int = 3600
    cache_cleanup_timeout: int = 300
    
    # API timeouts
    social_metrics_timeout: int = 5
    veo3_timeout: int = 120
    publish_timeout: int = 30
    
    # Retry timeouts
    retry_min_wait: int = 1
    retry_max_wait: int = 6
    
    @classmethod
    def from_environment(cls) -> 'TimeoutConfig':
        """Create timeout config from environment variables with validation"""
        return cls(
            # Network timeouts
            request_timeout=cls._safe_int_timeout("REQUEST_TIMEOUT", 30, 5, 300),
            connection_timeout=cls._safe_int_timeout("CONNECTION_TIMEOUT", 30, 5, 120),
            read_timeout=cls._safe_int_timeout("READ_TIMEOUT", 60, 10, 600),
            write_timeout=cls._safe_int_timeout("WRITE_TIMEOUT", 60, 10, 600),
            
            # MVP timeouts
            mvp_install_timeout=cls._safe_int_timeout("MVP_INSTALL_TIMEOUT", 600, 60, 3600),
            mvp_build_timeout=cls._safe_int_timeout("MVP_BUILD_TIMEOUT", 300, 60, 1800),
            mvp_test_timeout=cls._safe_int_timeout("MVP_TEST_TIMEOUT", 300, 60, 1800),
            mvp_dev_startup_timeout=cls._safe_int_timeout("MVP_DEV_STARTUP_TIMEOUT", 35, 10, 300),
            
            # Worker timeouts
            rq_default_timeout=cls._safe_int_timeout("RQ_DEFAULT_TIMEOUT", 7200, 300, 14400),
            worker_timeout=cls._safe_int_timeout("WORKER_TIMEOUT", 300, 60, 3600),
            
            # Cache timeouts
            cache_ttl=cls._safe_int_timeout("CACHE_TTL", 3600, 60, 86400),
            cache_cleanup_timeout=cls._safe_int_timeout("CACHE_CLEANUP_TIMEOUT", 300, 60, 1800),
            
            # API timeouts
            social_metrics_timeout=cls._safe_int_timeout("SOCIAL_METRICS_TIMEOUT_S", 5, 1, 60),
            veo3_timeout=cls._safe_int_timeout("VEO3_TIMEOUT_S", 120, 30, 600),
            publish_timeout=cls._safe_int_timeout("PUBLISH_TIMEOUT_S", 30, 10, 300),
            
            # Retry timeouts
            retry_min_wait=cls._safe_int_timeout("RETRY_MIN_WAIT", 1, 1, 60),
            retry_max_wait=cls._safe_int_timeout("RETRY_MAX_WAIT", 6, 1, 300),
        )
    
    @staticmethod
    def _safe_int_timeout(env_var: str, default: int, min_val: int, max_val: int) -> int:
        """Safely convert environment variable to timeout with validation"""
        try:
            value = int(os.getenv(env_var, str(default)))
            if value < min_val:
                print(f"⚠️ {env_var} timeout {value}s below minimum {min_val}s, using {min_val}s")
                return min_val
            if value > max_val:
                print(f"⚠️ {env_var} timeout {value}s above maximum {max_val}s, using {max_val}s")
                return max_val
            return value
        except (ValueError, TypeError):
            print(f"⚠️ Invalid {env_var} timeout, using default: {default}s")
            return default
    
    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary for easy access"""
        return {
            'request_timeout': self.request_timeout,
            'connection_timeout': self.connection_timeout,
            'read_timeout': self.read_timeout,
            'write_timeout': self.write_timeout,
            'mvp_install_timeout': self.mvp_install_timeout,
            'mvp_build_timeout': self.mvp_build_timeout,
            'mvp_test_timeout': self.mvp_test_timeout,
            'mvp_dev_startup_timeout': self.mvp_dev_startup_timeout,
            'rq_default_timeout': self.rq_default_timeout,
            'worker_timeout': self.worker_timeout,
            'cache_ttl': self.cache_ttl,
            'cache_cleanup_timeout': self.cache_cleanup_timeout,
            'social_metrics_timeout': self.social_metrics_timeout,
            'veo3_timeout': self.veo3_timeout,
            'publish_timeout': self.publish_timeout,
            'retry_min_wait': self.retry_min_wait,
            'retry_max_wait': self.retry_max_wait,
        }
    
    def get_timeout(self, timeout_name: str) -> int:
        """Get a specific timeout by name"""
        return getattr(self, timeout_name, self.request_timeout)
    
    def validate_timeouts(self) -> Dict[str, str]:
        """Validate all timeouts and return any issues"""
        issues = []
        
        # Check for unreasonable timeout combinations
        if self.read_timeout < self.connection_timeout:
            issues.append("READ_TIMEOUT should be >= CONNECTION_TIMEOUT")
        
        if self.write_timeout < self.connection_timeout:
            issues.append("WRITE_TIMEOUT should be >= CONNECTION_TIMEOUT")
        
        if self.retry_max_wait < self.retry_min_wait:
            issues.append("RETRY_MAX_WAIT should be >= RETRY_MIN_WAIT")
        
        if self.mvp_build_timeout > self.mvp_install_timeout:
            issues.append("MVP_BUILD_TIMEOUT should not exceed MVP_INSTALL_TIMEOUT")
        
        if self.cache_ttl < 300:  # Less than 5 minutes
            issues.append("CACHE_TTL should be at least 300s (5 minutes) for effectiveness")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }


# Global timeout configuration instance
_timeout_config: TimeoutConfig | None = None


def get_timeout_config() -> TimeoutConfig:
    """Get the global timeout configuration instance"""
    global _timeout_config
    if _timeout_config is None:
        _timeout_config = TimeoutConfig.from_environment()
        
        # Validate and report issues
        validation = _timeout_config.validate_timeouts()
        if not validation['valid']:
            print("⚠️ Timeout configuration issues detected:")
            for issue in validation['issues']:
                print(f"  - {issue}")
    
    return _timeout_config


def reload_timeout_config() -> TimeoutConfig:
    """Reload timeout configuration from environment"""
    global _timeout_config
    _timeout_config = TimeoutConfig.from_environment()
    return _timeout_config


# Convenience functions for common timeouts
def get_request_timeout() -> int:
    """Get HTTP request timeout"""
    return get_timeout_config().request_timeout


def get_mvp_timeout(operation: str) -> int:
    """Get MVP operation timeout"""
    config = get_timeout_config()
    timeout_map = {
        'install': config.mvp_install_timeout,
        'build': config.mvp_build_timeout,
        'test': config.mvp_test_timeout,
        'startup': config.mvp_dev_startup_timeout,
    }
    return timeout_map.get(operation, config.mvp_build_timeout)


def get_worker_timeout() -> int:
    """Get worker operation timeout"""
    return get_timeout_config().worker_timeout


def get_cache_timeout() -> int:
    """Get cache TTL"""
    return get_timeout_config().cache_ttl
