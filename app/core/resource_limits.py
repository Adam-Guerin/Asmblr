"""
Resource Limits Configuration
Protects system from resource exhaustion
"""

import os
import psutil
import signal
from pathlib import Path
from loguru import logger

class ResourceLimiter:
    """Enforces resource limits to protect system"""
    
    def __init__(self):
        self.max_memory_mb = int(os.getenv("MAX_MEMORY_MB", "2048"))
        self.max_cpu_percent = float(os.getenv("MAX_CPU_PERCENT", "80.0"))
        self.max_disk_percent = float(os.getenv("MAX_DISK_PERCENT", "90.0"))
        self.check_interval = 10  # seconds
        self._monitoring = False
        
    def start_monitoring(self):
        """Start resource limit monitoring"""
        self._monitoring = True
        
        def monitor_loop():
            while self._monitoring:
                try:
                    self._check_limits()
                except Exception as e:
                    logger.error(f"Resource monitoring error: {e}")
                
                import time
                time.sleep(self.check_interval)
        
        import threading
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
        logger.info(f"Resource limits monitoring started: {self.max_memory_mb}MB, {self.max_cpu_percent}% CPU")
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self._monitoring = False
    
    def _check_limits(self):
        """Check if resource limits are exceeded"""
        process = psutil.Process()
        
        # Check memory limit
        memory_mb = process.memory_info().rss / (1024 * 1024)
        if memory_mb > self.max_memory_mb:
            logger.warning(f"Memory limit exceeded: {memory_mb:.1f}MB > {self.max_memory_mb}MB")
            self._handle_limit_exceeded("memory", memory_mb)
        
        # Check CPU limit
        cpu_percent = process.cpu_percent(interval=1)
        if cpu_percent > self.max_cpu_percent:
            logger.warning(f"CPU limit exceeded: {cpu_percent:.1f}% > {self.max_cpu_percent}%")
            self._handle_limit_exceeded("cpu", cpu_percent)
        
        # Check disk limit
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        if disk_percent > self.max_disk_percent:
            logger.warning(f"Disk limit exceeded: {disk_percent:.1f}% > {self.max_disk_percent}%")
            self._handle_limit_exceeded("disk", disk_percent)
    
    def _handle_limit_exceeded(self, resource_type: str, current_value: float):
        """Handle resource limit exceeded"""
        if resource_type == "memory":
            # Trigger garbage collection
            import gc
            gc.collect()
            
            # If still over limit, reduce cache sizes
            if current_value > self.max_memory_mb * 1.1:  # 10% buffer
                self._emergency_memory_cleanup()
        
        elif resource_type == "cpu":
            # Reduce concurrent operations
            logger.warning("Reducing concurrent operations due to CPU limit")
            
        elif resource_type == "disk":
            # Clear temporary files
            self._cleanup_temp_files()
    
    def _emergency_memory_cleanup(self):
        """Emergency memory cleanup"""
        logger.critical("Performing emergency memory cleanup")
        
        # Clear caches
        try:
            from app.core.unified_cache import get_cache
            cache = get_cache()
            cache.clear()
        except Exception:
            pass
        
        # Force garbage collection
        import gc
        gc.collect()
    
    def _cleanup_temp_files(self):
        """Clean up temporary files"""
        import tempfile
        import shutil
        
        temp_dir = Path(tempfile.gettempdir())
        try:
            # Clean old temp files
            for item in temp_dir.glob("asmblr_*"):
                if item.is_file() and time.time() - item.stat().st_mtime > 3600:  # 1 hour
                    item.unlink()
        except Exception:
            pass

# Global limiter instance
_limiter: ResourceLimiter = None

def get_resource_limiter() -> ResourceLimiter:
    """Get global resource limiter"""
    global _limiter
    if _limiter is None:
        _limiter = ResourceLimiter()
    return _limiter
