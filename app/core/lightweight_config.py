"""
Lightweight Configuration Manager - AI-driven variable selection
Automatically configures optimal settings for resource-constrained environments
"""

import os
import json
from pathlib import Path
from typing import Any
from datetime import datetime
from loguru import logger
import psutil

class LightweightConfigManager:
    """Manages lightweight configuration with AI-driven optimization"""
    
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parents[2]
        self.settings_dir = self.base_dir / "configs"
        self.settings_dir.mkdir(exist_ok=True)
        self.cache_file = self.settings_dir / "lightweight_cache.json"
        
    def _get_safe_system_path(self) -> Path | None:
        """Get a safe system path for resource monitoring"""
        try:
            if os.name == 'nt':  # Windows
                # Use Windows root with validation
                path = Path('C:\\')
            else:  # Unix-like systems
                # Use Unix root with validation
                path = Path('/')
            
            return self._validate_path_security(path)
        except Exception:
            return None
    
    def _get_safe_current_directory(self) -> Path | None:
        """Get current working directory with security validation"""
        try:
            current_dir = Path.cwd().resolve()
            return self._validate_path_security(current_dir)
        except Exception:
            return None
    
    def _validate_path_security(self, path: Path) -> Path | None:
        """Validate path for security (prevent path traversal)"""
        try:
            # Resolve to absolute path
            resolved = path.resolve()
            
            # Define allowed root paths based on OS
            if os.name == 'nt':  # Windows
                allowed_roots = [Path('C:\\'), Path('\\\\')]
            else:  # Unix-like systems
                allowed_roots = [Path('/')]
            
            # Check if resolved path is within allowed roots
            path_str = str(resolved)
            if not any(str(resolved).startswith(str(root)) for root in allowed_roots):
                logger.warning(f"Path outside allowed roots: {path_str}")
                return None
            
            # Additional security checks
            if not resolved.exists():
                logger.warning(f"Path does not exist: {path_str}")
                return None
            
            return resolved
        except (OSError, ValueError, RuntimeError) as e:
            logger.warning(f"Path validation failed: {e}")
            return None
    
    def is_lightweight_mode(self) -> bool:
        """Check if lightweight mode is active"""
        return (
            os.getenv("LIGHTWEIGHT_MODE", "").lower() == "true" or
            os.getenv("ASMblr_LIGHTWEIGHT", "").lower() == "true"
        )
    
    def get_system_resources(self) -> dict[str, Any]:
        """Get current system resource information with cross-platform support"""
        try:
            memory = psutil.virtual_memory()
            cpu_count = psutil.cpu_count()
            
            # Cross-platform disk usage detection with security validation
            try:
                disk_path = self._get_safe_system_path()
                if disk_path is None:
                    raise Exception("Unable to determine safe system path")
                
                disk = psutil.disk_usage(str(disk_path))
            except Exception as e:
                logger.warning(f"Failed to get system disk usage: {e}")
                # Fallback to current directory with validation
                try:
                    current_dir = self._get_safe_current_directory()
                    if current_dir is None:
                        raise Exception("Unable to determine safe current directory")
                    disk = psutil.disk_usage(str(current_dir))
                except Exception as e2:
                    logger.warning(f"Failed to get current directory disk usage: {e2}")
                    # Use safe defaults
                    disk = None
            
            return {
                "available_memory_gb": memory.available / (1024**3),
                "total_memory_gb": memory.total / (1024**3),
                "cpu_count": cpu_count,
                "available_disk_gb": disk.free / (1024**3) if disk else 100.0,
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": memory.percent
            }
        except Exception as e:
            logger.warning(f"Failed to get system resources: {e}")
            # Return safe defaults
            return {
                "available_memory_gb": 8.0,
                "total_memory_gb": 16.0,
                "cpu_count": 4,
                "available_disk_gb": 100.0,
                "cpu_percent": 25.0,
                "memory_percent": 50.0
            }
    
    def load_cached_config(self) -> dict[str, Any] | None:
        """Load cached lightweight configuration with validation"""
        try:
            if not self.cache_file.exists():
                return None
                
            # Check file size (security: prevent loading huge files)
            file_size = self.cache_file.stat().st_size
            if file_size > 1024 * 1024:  # 1MB limit
                logger.warning("Cache file too large - ignoring")
                return None
                
            with open(self.cache_file) as f:
                cache_data = json.load(f)
                
            # Validate cache structure
            if not isinstance(cache_data, dict):
                logger.warning("Invalid cache structure - ignoring")
                return None
                
            if "timestamp" not in cache_data or "config" not in cache_data:
                logger.warning("Missing required cache fields - ignoring")
                return None
                
            # Validate config values first
            config = cache_data.get("config", {})
            if not isinstance(config, dict) or len(config) >= 100:  # Reasonable size limit
                logger.warning("Invalid config structure - ignoring")
                return None
            
            # Check if cache is recent (less than 24 hours)
            try:
                cache_time = datetime.fromisoformat(cache_data.get("timestamp", ""))
            except ValueError:
                logger.warning("Invalid timestamp format - ignoring")
                return None
            
            now = datetime.now()
            if (now - cache_time).total_seconds() < 86400:
                return config
            else:
                logger.info("Cache expired - will generate new config")
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in cache file: {e}")
        except Exception as e:
            logger.warning(f"Failed to load cached config: {e}")
        
        return None
    
    def save_cached_config(self, config: dict[str, Any]):
        """Save lightweight configuration to cache"""
        try:
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "config": config,
                "system_resources": self.get_system_resources()
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            logger.info("Lightweight configuration cached")
        except Exception as e:
            logger.warning(f"Failed to save cached config: {e}")
    
    def generate_ai_optimized_config(self, context: dict[str, Any]) -> dict[str, str]:
        """Generate AI-optimized configuration based on context"""
        resources = self.get_system_resources()
        
        # AI-driven optimization logic
        config = {}
        
        # Memory-based optimization
        available_memory = resources.get("available_memory_gb", 8)
        if available_memory < 2:
            # Very low memory - ultra conservative
            config.update({
                "DEFAULT_N_IDEAS": "3",
                "MAX_SOURCES": "3",
                "MIN_PAGES": "1",
                "MIN_PAINS": "1",
                "REQUEST_TIMEOUT": "10",
                "RETRY_MAX_ATTEMPTS": "1",
                "RUN_MAX_CONCURRENT": "1",
                "WORKER_CONCURRENCY": "1",
                "API_CONCURRENCY": "3",
                "ENABLE_CACHE": "true",
                "CACHE_TTL": "900"
            })
        elif available_memory < 4:
            # Low memory - conservative
            config.update({
                "DEFAULT_N_IDEAS": "5",
                "MAX_SOURCES": "5",
                "MIN_PAGES": "2",
                "MIN_PAINS": "2",
                "REQUEST_TIMEOUT": "15",
                "RETRY_MAX_ATTEMPTS": "2",
                "RUN_MAX_CONCURRENT": "2",
                "WORKER_CONCURRENCY": "2",
                "API_CONCURRENCY": "5",
                "ENABLE_CACHE": "true",
                "CACHE_TTL": "1800"
            })
        else:
            # Moderate memory - balanced
            config.update({
                "DEFAULT_N_IDEAS": "8",
                "MAX_SOURCES": "8",
                "MIN_PAGES": "3",
                "MIN_PAINS": "3",
                "REQUEST_TIMEOUT": "20",
                "RETRY_MAX_ATTEMPTS": "3",
                "RUN_MAX_CONCURRENT": "3",
                "WORKER_CONCURRENCY": "2",
                "API_CONCURRENCY": "8",
                "ENABLE_CACHE": "true",
                "CACHE_TTL": "3600"
            })
        
        # CPU-based optimization
        cpu_count = resources.get("cpu_count", 4)
        if cpu_count < 2:
            config.update({
                "RUN_MAX_CONCURRENT": "1",
                "WORKER_CONCURRENCY": "1",
                "API_CONCURRENCY": "2"
            })
        elif cpu_count < 4:
            config.update({
                "RUN_MAX_CONCURRENT": "2",
                "WORKER_CONCURRENCY": "2",
                "API_CONCURRENCY": "5"
            })
        
        # Context-based optimization
        if context.get("project_type") == "simple":
            config.update({
                "DEFAULT_N_IDEAS": "3",
                "MAX_SOURCES": "3",
                "FAST_MODE": "true"
            })
        elif context.get("project_type") == "complex":
            config.update({
                "DEFAULT_N_IDEAS": "10",
                "MAX_SOURCES": "10",
                "FAST_MODE": "false"
            })
        
        # Quality-based optimization
        if context.get("quality_priority") == "speed":
            config.update({
                "MARKET_SIGNAL_THRESHOLD": "30",
                "SIGNAL_QUALITY_THRESHOLD": "35",
                "MIN_AVG_TEXT_LEN": "100"
            })
        elif context.get("quality_priority") == "quality":
            config.update({
                "MARKET_SIGNAL_THRESHOLD": "50",
                "SIGNAL_QUALITY_THRESHOLD": "60",
                "MIN_AVG_TEXT_LEN": "300"
            })
        
        # Feature optimization based on resources
        if available_memory < 4:
            # Disable heavy features in low memory
            config.update({
                "ENABLE_LOGO_DIFFUSION": "false",
                "ENABLE_VIDEO_GENERATION": "false",
                "ENABLE_SOCIAL_MEDIA": "false",
                "ENABLE_MONITORING": "false"
            })
        
        return config
    
    def get_missing_variables(self) -> dict[str, str]:
        """Get variables that are not set but needed for lightweight mode"""
        essential_vars = {
            "MARKET_SIGNAL_THRESHOLD": "40",
            "SIGNAL_QUALITY_THRESHOLD": "45", 
            "MIN_AVG_TEXT_LEN": "200",
            "SIGNAL_SOURCES_TARGET": "4",
            "SIGNAL_PAINS_TARGET": "5",
            "SIGNAL_DOMAIN_TARGET": "2",
            "SIGNAL_REPEAT_TARGET": "1",
            "SIGNAL_RECENCY_DAYS": "180",
            "IDEA_ACTIONABILITY_MIN_SCORE": "45",
            "IDEA_ACTIONABILITY_ADJUSTMENT_MAX": "10",
            "LEARNING_HISTORY_MAX_RUNS": "50",
            "LEARNING_EXPLORATION_RATE": "0.25",
            "ENABLE_SELF_HEALING": "true",
            "STAGE_RETRY_ATTEMPTS": "1",
            "ENABLE_PROGRESSIVE_CYCLES": "true"
        }
        
        missing_vars = {}
        for var, default in essential_vars.items():
            if not os.getenv(var):
                missing_vars[var] = default
        
        return missing_vars
    
    def apply_ai_optimizations(self, context: dict[str, Any] | None = None):
        """Apply AI-driven optimizations to environment"""
        if not self.is_lightweight_mode():
            return
        
        context = context or {}
        
        # Try to load cached configuration first
        cached_config = self.load_cached_config()
        
        if cached_config:
            logger.info("Using cached lightweight configuration")
            config = cached_config
        else:
            logger.info("Generating new AI-optimized configuration")
            config = self.generate_ai_optimized_config(context)
            self.save_cached_config(config)
        
        # Apply configuration to environment (only if not already set)
        applied_vars = 0
        for key, value in config.items():
            if not os.getenv(key):
                os.environ[key] = str(value)
                applied_vars += 1
        
        # Apply missing essential variables
        missing_vars = self.get_missing_variables()
        for key, value in missing_vars.items():
            if not os.getenv(key):
                os.environ[key] = value
                applied_vars += 1
        
        logger.info(f"Applied {applied_vars} AI-optimized variables")
        
        # Log resource optimization
        resources = self.get_system_resources()
        logger.info(f"Lightweight mode optimized for {resources.get('available_memory_gb', 'N/A')}GB RAM, {resources.get('cpu_count', 'N/A')} CPU cores")

# Global instance for easy access
lightweight_config = LightweightConfigManager()
