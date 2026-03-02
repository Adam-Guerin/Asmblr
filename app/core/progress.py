"""Pipeline progress tracking system for real-time UI updates."""

from __future__ import annotations
import threading
from enum import Enum
from typing import Any
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from loguru import logger


class PipelineStage(Enum):
    """Pipeline execution stages."""
    INITIALIZING = "initializing"
    SCRAPING = "scraping"
    ANALYZING = "analyzing"
    IDEA_GENERATION = "idea_generation"
    IDEA_SCORING = "idea_scoring"
    PRD_GENERATION = "prd_generation"
    TECH_SPEC_GENERATION = "tech_spec_generation"
    MVP_BUILDING = "mvp_building"
    CONTENT_GENERATION = "content_generation"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ProgressUpdate:
    """Progress update data structure."""
    stage: PipelineStage
    progress: float  # 0.0 to 1.0
    message: str
    details: dict[str, Any] | None = None
    timestamp: datetime | None = None
    error: str | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ProgressTracker:
    """Thread-safe progress tracker for pipeline execution."""
    
    def __init__(self):
        self._current_stage = PipelineStage.INITIALIZING
        self._progress = 0.0
        self._message = "Starting pipeline..."
        self._details: dict[str, Any] = {}
        self._error: str | None = None
        self._callbacks: list[Callable[[ProgressUpdate], None]] = []
        self._lock = threading.Lock()
        self._start_time = datetime.now()
        self._stage_start_time = datetime.now()
        
        # Stage weights for overall progress calculation
        self._stage_weights = {
            PipelineStage.INITIALIZING: 0.05,
            PipelineStage.SCRAPING: 0.15,
            PipelineStage.ANALYZING: 0.10,
            PipelineStage.IDEA_GENERATION: 0.15,
            PipelineStage.IDEA_SCORING: 0.10,
            PipelineStage.PRD_GENERATION: 0.10,
            PipelineStage.TECH_SPEC_GENERATION: 0.10,
            PipelineStage.MVP_BUILDING: 0.15,
            PipelineStage.CONTENT_GENERATION: 0.05,
            PipelineStage.FINALIZING: 0.05,
        }
    
    def add_callback(self, callback: Callable[[ProgressUpdate], None]) -> None:
        """Add a callback function to receive progress updates."""
        with self._lock:
            self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[ProgressUpdate], None]) -> None:
        """Remove a callback function."""
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)
    
    def _notify_callbacks(self, update: ProgressUpdate) -> None:
        """Notify all registered callbacks with progress update."""
        for callback in self._callbacks:
            try:
                callback(update)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")
    
    def update_stage(self, stage: PipelineStage, message: str = "", details: dict[str, Any] | None = None) -> None:
        """Update the current pipeline stage."""
        with self._lock:
            self._current_stage = stage
            self._message = message or stage.value.replace("_", " ").title()
            self._details = details or {}
            self._stage_start_time = datetime.now()
            
            # Calculate overall progress based on completed stages
            self._progress = self._calculate_overall_progress(stage)
            
            update = ProgressUpdate(
                stage=stage,
                progress=self._progress,
                message=self._message,
                details=self._details
            )
            
            self._notify_callbacks(update)
            logger.info(f"Pipeline stage updated: {stage.value} - {message}")
    
    def update_progress(self, stage_progress: float, message: str = "", details: dict[str, Any] | None = None) -> None:
        """Update progress within the current stage."""
        with self._lock:
            stage_weight = self._stage_weights.get(self._current_stage, 0.1)
            
            # Calculate base progress from completed stages
            base_progress = self._calculate_base_progress()
            
            # Add current stage progress
            self._progress = base_progress + (stage_progress * stage_weight)
            self._progress = min(self._progress, 1.0)
            
            if message:
                self._message = message
            if details:
                self._details.update(details)
            
            update = ProgressUpdate(
                stage=self._current_stage,
                progress=self._progress,
                message=self._message,
                details=self._details.copy()
            )
            
            self._notify_callbacks(update)
    
    def set_error(self, error: str, details: dict[str, Any] | None = None) -> None:
        """Set error state."""
        with self._lock:
            self._error = error
            self._current_stage = PipelineStage.FAILED
            self._message = f"Error: {error}"
            
            if details:
                self._details.update(details)
            
            update = ProgressUpdate(
                stage=PipelineStage.FAILED,
                progress=self._progress,
                message=self._message,
                details=self._details.copy(),
                error=error
            )
            
            self._notify_callbacks(update)
            logger.error(f"Pipeline error: {error}")
    
    def complete(self, message: str = "Pipeline completed successfully!", details: dict[str, Any] | None = None) -> None:
        """Mark pipeline as completed."""
        with self._lock:
            self._current_stage = PipelineStage.COMPLETED
            self._progress = 1.0
            self._message = message
            
            if details:
                self._details.update(details)
            
            update = ProgressUpdate(
                stage=PipelineStage.COMPLETED,
                progress=1.0,
                message=self._message,
                details=self._details.copy()
            )
            
            self._notify_callbacks(update)
            logger.info("Pipeline completed successfully")
    
    def _calculate_overall_progress(self, current_stage: PipelineStage) -> float:
        """Calculate overall progress based on current stage."""
        progress = 0.0
        for stage, weight in self._stage_weights.items():
            if stage == current_stage:
                break
            progress += weight
        return progress
    
    def _calculate_base_progress(self) -> float:
        """Calculate progress from completed stages."""
        progress = 0.0
        for stage, weight in self._stage_weights.items():
            if stage == self._current_stage:
                break
            progress += weight
        return progress
    
    def get_current_state(self) -> dict[str, Any]:
        """Get current progress state."""
        with self._lock:
            elapsed_time = (datetime.now() - self._start_time).total_seconds()
            stage_elapsed_time = (datetime.now() - self._stage_start_time).total_seconds()
            
            return {
                "stage": self._current_stage.value,
                "progress": self._progress,
                "message": self._message,
                "details": self._details.copy(),
                "error": self._error,
                "elapsed_time": elapsed_time,
                "stage_elapsed_time": stage_elapsed_time,
                "start_time": self._start_time.isoformat(),
                "stage_start_time": self._stage_start_time.isoformat()
            }
    
    def reset(self) -> None:
        """Reset the progress tracker."""
        with self._lock:
            self._current_stage = PipelineStage.INITIALIZING
            self._progress = 0.0
            self._message = "Starting pipeline..."
            self._details = {}
            self._error = None
            self._start_time = datetime.now()
            self._stage_start_time = datetime.now()


# Global progress tracker instance
_global_tracker = ProgressTracker()


def get_progress_tracker() -> ProgressTracker:
    """Get the global progress tracker instance."""
    return _global_tracker


def reset_progress_tracker() -> None:
    """Reset the global progress tracker."""
    _global_tracker.reset()
