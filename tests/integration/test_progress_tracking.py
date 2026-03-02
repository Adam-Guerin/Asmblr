"""Integration tests for progress tracking system."""

import time
import threading
from unittest.mock import Mock, patch
from datetime import datetime

from app.core.progress import ProgressTracker, PipelineStage, ProgressUpdate, get_progress_tracker


class TestProgressTracking:
    """Test suite for progress tracking functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.tracker = ProgressTracker()
        self.updates_received = []
        
        def callback(update: ProgressUpdate):
            self.updates_received.append(update)
        
        self.tracker.add_callback(callback)
    
    def test_initial_state(self):
        """Test initial tracker state."""
        state = self.tracker.get_current_state()
        
        assert state["stage"] == PipelineStage.INITIALIZING.value
        assert state["progress"] == 0.0
        assert state["message"] == "Starting pipeline..."
        assert state["error"] is None
        assert "elapsed_time" in state
        assert "stage_elapsed_time" in state
    
    def test_stage_updates(self):
        """Test stage progression updates."""
        # Update to scraping stage
        self.tracker.update_stage(
            PipelineStage.SCRAPING, 
            "Scraping market signals...",
            {"sources_count": 5}
        )
        
        state = self.tracker.get_current_state()
        assert state["stage"] == PipelineStage.SCRAPING.value
        assert state["message"] == "Scraping market signals..."
        assert state["details"]["sources_count"] == 5
        
        # Check callback was called
        assert len(self.updates_received) == 1
        assert self.updates_received[0].stage == PipelineStage.SCRAPING
    
    def test_progress_within_stage(self):
        """Test progress updates within a stage."""
        self.tracker.update_stage(PipelineStage.ANALYZING, "Analyzing data...")
        
        # Update progress within the stage
        self.tracker.update_progress(0.5, "Halfway through analysis...", {"processed_items": 50})
        
        state = self.tracker.get_current_state()
        assert state["progress"] > 0.0
        assert state["message"] == "Halfway through analysis..."
        assert state["details"]["processed_items"] == 50
        
        # Check callback was called
        assert len(self.updates_received) == 2  # Stage update + progress update
    
    def test_error_handling(self):
        """Test error state handling."""
        error_message = "Connection failed"
        error_details = {"url": "http://example.com", "timeout": 30}
        
        self.tracker.set_error(error_message, error_details)
        
        state = self.tracker.get_current_state()
        assert state["stage"] == PipelineStage.FAILED.value
        assert state["error"] == error_message
        assert state["details"]["url"] == "http://example.com"
        
        # Check callback was called with error
        assert len(self.updates_received) == 1
        assert self.updates_received[0].stage == PipelineStage.FAILED
        assert self.updates_received[0].error == error_message
    
    def test_completion(self):
        """Test successful completion."""
        completion_details = {"run_id": "test_run_123", "total_time": 120.5}
        
        self.tracker.complete("Pipeline completed!", completion_details)
        
        state = self.tracker.get_current_state()
        assert state["stage"] == PipelineStage.COMPLETED.value
        assert state["progress"] == 1.0
        assert state["message"] == "Pipeline completed!"
        assert state["details"]["run_id"] == "test_run_123"
        assert state["error"] is None
    
    def test_callback_management(self):
        """Test callback addition and removal."""
        callback1 = Mock()
        callback2 = Mock()
        
        # Add callbacks
        self.tracker.add_callback(callback1)
        self.tracker.add_callback(callback2)
        
        # Trigger update
        self.tracker.update_stage(PipelineStage.IDEA_GENERATION, "Generating ideas...")
        
        # Both callbacks should be called
        callback1.assert_called_once()
        callback2.assert_called_once()
        
        # Remove one callback
        self.tracker.remove_callback(callback1)
        
        # Trigger another update
        self.tracker.update_progress(0.5, "Progressing...")
        
        # Only callback2 should be called again
        assert callback1.call_count == 1
        assert callback2.call_count == 2
    
    def test_thread_safety(self):
        """Test thread safety of progress updates."""
        results = []
        
        def update_progress(thread_id: int):
            for i in range(10):
                self.tracker.update_progress(i / 10, f"Thread {thread_id} progress {i}")
                time.sleep(0.01)
            results.append(thread_id)
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=update_progress, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all threads completed
        assert len(results) == 5
        assert set(results) == {0, 1, 2, 3, 4}
    
    def test_progress_calculation(self):
        """Test overall progress calculation."""
        # Progress through stages
        stages = [
            PipelineStage.INITIALIZING,
            PipelineStage.SCRAPING,
            PipelineStage.ANALYZING,
            PipelineStage.IDEA_GENERATION
        ]
        
        for stage in stages:
            self.tracker.update_stage(stage, f"Entering {stage.value}")
        
        # Should have progressed through multiple stages
        state = self.tracker.get_current_state()
        assert state["progress"] > 0.0
        assert state["progress"] < 1.0
    
    def test_reset_functionality(self):
        """Test tracker reset functionality."""
        # Set some state
        self.tracker.update_stage(PipelineStage.MVP_BUILDING, "Building MVP...")
        self.tracker.update_progress(0.7, "Almost done...")
        
        # Reset tracker
        self.tracker.reset()
        
        # Check initial state is restored
        state = self.tracker.get_current_state()
        assert state["stage"] == PipelineStage.INITIALIZING.value
        assert state["progress"] == 0.0
        assert state["message"] == "Starting pipeline..."
        assert state["error"] is None
    
    def test_global_tracker_singleton(self):
        """Test global tracker instance."""
        tracker1 = get_progress_tracker()
        tracker2 = get_progress_tracker()
        
        # Should be the same instance
        assert tracker1 is tracker2
    
    @patch('app.core.progress.datetime')
    def test_timestamp_tracking(self, mock_datetime):
        """Test timestamp tracking in updates."""
        fixed_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = fixed_time
        
        update = ProgressUpdate(
            stage=PipelineStage.SCRAPING,
            progress=0.5,
            message="Test message"
        )
        
        assert update.timestamp == fixed_time


class TestProgressIntegration:
    """Integration tests for progress tracking with other components."""
    
    @patch('app.core.progress.logger')
    def test_logging_integration(self, mock_logger):
        """Test integration with logging system."""
        tracker = ProgressTracker()
        
        # Trigger various updates
        tracker.update_stage(PipelineStage.SCRAPING, "Starting scrape...")
        tracker.set_error("Test error", {"context": "test"})
        tracker.complete("Done!", {"result": "success"})
        
        # Verify logging calls
        assert mock_logger.info.called
        assert mock_logger.error.called
    
    def test_error_callback_handling(self):
        """Test handling of errors in callbacks."""
        tracker = ProgressTracker()
        
        def failing_callback(update: ProgressUpdate):
            raise Exception("Callback failed")
        
        def working_callback(update: ProgressUpdate):
            working_callback.called = True
        
        working_callback.called = False
        
        tracker.add_callback(failing_callback)
        tracker.add_callback(working_callback)
        
        # Should not raise exception despite failing callback
        tracker.update_stage(PipelineStage.ANALYZING, "Analyzing...")
        
        # Working callback should still be called
        assert working_callback.called
    
    def test_progress_update_serialization(self):
        """Test ProgressUpdate serialization for JSON compatibility."""
        update = ProgressUpdate(
            stage=PipelineStage.SCRAPING,
            progress=0.5,
            message="Test message",
            details={"key": "value"},
            error=None
        )
        
        # Should be JSON serializable
        import json
        update_dict = {
            "stage": update.stage.value,
            "progress": update.progress,
            "message": update.message,
            "details": update.details,
            "timestamp": update.timestamp.isoformat() if update.timestamp else None,
            "error": update.error
        }
        
        json_str = json.dumps(update_dict)
        assert json_str is not None
        
        # Should be deserializable
        loaded = json.loads(json_str)
        assert loaded["stage"] == PipelineStage.SCRAPING.value
        assert loaded["progress"] == 0.5
