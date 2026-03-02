"""Performance monitoring utilities for pipeline optimization."""

import time
import logging
from typing import Any
from dataclasses import dataclass, field
from contextlib import contextmanager
import threading

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a pipeline stage."""
    stage_name: str
    start_time: float
    end_time: float | None = None
    duration: float | None = None
    memory_usage: int | None = None
    success: bool = True
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """Thread-safe performance monitoring for pipeline stages."""
    
    def __init__(self):
        self._metrics: dict[str, PerformanceMetrics] = {}
        self._lock = threading.RLock()
        self._current_stage: str | None = None
    
    @contextmanager
    def stage(self, stage_name: str):
        """Context manager for monitoring a pipeline stage."""
        with self._lock:
            self._current_stage = stage_name
            metrics = PerformanceMetrics(
                stage_name=stage_name,
                start_time=time.time()
            )
            self._metrics[stage_name] = metrics
        
        try:
            logger.info(f"Starting stage: {stage_name}")
            yield metrics
            
        except Exception as e:
            with self._lock:
                metrics.success = False
                metrics.error_message = str(e)
            logger.error(f"Stage {stage_name} failed: {e}")
            raise
            
        finally:
            with self._lock:
                metrics.end_time = time.time()
                metrics.duration = metrics.end_time - metrics.start_time
                self._current_stage = None
            
            logger.info(f"Stage {stage_name} completed in {metrics.duration:.2f}s")
    
    def get_metrics(self, stage_name: str | None = None) -> dict[str, PerformanceMetrics]:
        """Get performance metrics for all stages or a specific stage."""
        with self._lock:
            if stage_name:
                return {stage_name: self._metrics.get(stage_name)}
            return self._metrics.copy()
    
    def get_summary(self) -> dict[str, Any]:
        """Get a summary of all performance metrics."""
        with self._lock:
            if not self._metrics:
                return {"total_stages": 0, "total_duration": 0, "success_rate": 0}
            
            total_duration = sum(m.duration or 0 for m in self._metrics.values())
            successful_stages = sum(1 for m in self._metrics.values() if m.success)
            
            return {
                "total_stages": len(self._metrics),
                "total_duration": total_duration,
                "success_rate": successful_stages / len(self._metrics),
                "average_stage_duration": total_duration / len(self._metrics),
                "stages": {
                    name: {
                        "duration": m.duration,
                        "success": m.success,
                        "error": m.error_message
                    }
                    for name, m in self._metrics.items()
                }
            }
    
    def reset(self):
        """Reset all metrics."""
        with self._lock:
            self._metrics.clear()
            self._current_stage = None


# Global performance monitor instance
performance_monitor = PerformanceMonitor()
