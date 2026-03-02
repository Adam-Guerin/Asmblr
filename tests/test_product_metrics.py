"""Test product metrics functionality."""

import tempfile
from pathlib import Path

import pytest

from app.core.product_metrics import ProductMetrics, init_product_metrics


def test_product_metrics_initialization():
    """Test that product metrics can be initialized."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        metrics = ProductMetrics(tmp_path)
        
        assert metrics.data_dir == tmp_path
        assert metrics.metrics_file == tmp_path / "product_metrics.json"
        assert metrics._runs == {}


def test_record_run_start():
    """Test recording a new run start."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        metrics = ProductMetrics(tmp_path)
        
        run_id = "test_run_001"
        metrics.record_run_start(run_id)
        
        assert run_id in metrics._runs
        assert metrics._runs[run_id]['run_id'] == run_id
        assert metrics._runs[run_id]['mvp_published'] is False
        assert metrics._runs[run_id]['has_feedback'] is False
        assert metrics._runs[run_id]['feedback_count'] == 0
        assert metrics._runs[run_id]['iterations_after_feedback'] == 0


def test_record_landing_created():
    """Test recording landing page creation."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        metrics = ProductMetrics(tmp_path)
        
        run_id = "test_run_001"
        metrics.record_run_start(run_id)
        
        # Simulate time passing (1 day for testing)
        import time
        one_day_ago = time.time() - (24 * 3600)
        metrics._runs[run_id]['created_at'] = one_day_ago
        
        metrics.record_landing_created(run_id)
        
        assert metrics._runs[run_id]['idea_to_landing_days'] is not None
        assert metrics._runs[run_id]['idea_to_landing_days'] >= 1.0


def test_record_mvp_published():
    """Test recording MVP publication."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        metrics = ProductMetrics(tmp_path)
        
        run_id = "test_run_001"
        metrics.record_run_start(run_id)
        metrics.record_mvp_published(run_id)
        
        assert metrics._runs[run_id]['mvp_published'] is True


def test_record_feedback():
    """Test recording user feedback."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        metrics = ProductMetrics(tmp_path)
        
        run_id = "test_run_001"
        metrics.record_run_start(run_id)
        metrics.record_user_feedback(run_id, feedback_count=3)
        
        assert metrics._runs[run_id]['has_feedback'] is True
        assert metrics._runs[run_id]['feedback_count'] == 3


def test_record_iteration():
    """Test recording iterations after feedback."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        metrics = ProductMetrics(tmp_path)
        
        run_id = "test_run_001"
        metrics.record_run_start(run_id)
        metrics.record_user_feedback(run_id)
        metrics.record_iteration(run_id)
        metrics.record_iteration(run_id)
        
        assert metrics._runs[run_id]['iterations_after_feedback'] == 2


def test_get_dashboard_metrics_empty():
    """Test getting dashboard metrics with no runs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        metrics = ProductMetrics(tmp_path)
        
        dashboard_metrics = metrics.get_dashboard_metrics(days=30)
        
        assert dashboard_metrics['runs_count'] == 0
        assert dashboard_metrics['mvp_published_pct'] == 0
        assert dashboard_metrics['avg_idea_to_landing_days'] == 0
        assert dashboard_metrics['runs_with_feedback_pct'] == 0
        assert dashboard_metrics['runs_with_iterations_pct'] == 0


def test_get_dashboard_metrics_with_runs():
    """Test getting dashboard metrics with runs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        metrics = ProductMetrics(tmp_path)
        
        # Create 10 runs with various states
        import time
        now = time.time()
        
        for i in range(10):
            run_id = f"test_run_{i:03d}"
            metrics.record_run_start(run_id)
            
            # Set creation time to recent
            metrics._runs[run_id]['created_at'] = now
            
            # 5 runs with MVP published
            if i < 5:
                metrics.record_mvp_published(run_id)
            
            # 6 runs with landing pages (simulate 1 day delay)
            if i < 6:
                metrics._runs[run_id]['created_at'] = now - (24 * 3600)
                metrics.record_landing_created(run_id)
            
            # 4 runs with feedback
            if i < 4:
                metrics.record_user_feedback(run_id)
            
            # 3 runs with iterations
            if i < 3:
                metrics.record_iteration(run_id)
        
        dashboard_metrics = metrics.get_dashboard_metrics(days=30)
        
        assert dashboard_metrics['runs_count'] == 10
        assert dashboard_metrics['mvp_published_pct'] == 50.0
        assert dashboard_metrics['runs_with_feedback_pct'] == 40.0
        assert dashboard_metrics['runs_with_iterations_pct'] == 30.0
        assert dashboard_metrics['avg_idea_to_landing_days'] >= 1.0


def test_metrics_persistence():
    """Test that metrics are persisted and loaded correctly."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        metrics_file = tmp_path / "product_metrics.json"
        
        # Create metrics and record some data
        metrics1 = ProductMetrics(tmp_path)
        metrics1.record_run_start("test_run_001")
        metrics1.record_mvp_published("test_run_001")
        metrics1.record_user_feedback("test_run_001")
        
        # Verify file was created
        assert metrics_file.exists()
        
        # Load metrics in a new instance
        metrics2 = ProductMetrics(tmp_path)
        
        # Verify data was loaded
        assert "test_run_001" in metrics2._runs
        assert metrics2._runs["test_run_001"]['mvp_published'] is True
        assert metrics2._runs["test_run_001"]['has_feedback'] is True


def test_global_metrics_initialization():
    """Test global metrics initialization."""
    # Reset global variable first
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Initialize global metrics
        init_product_metrics(tmp_path)
        
        # Import again to get the updated global variable
        from app.core.product_metrics import PRODUCT_METRICS
        
        assert PRODUCT_METRICS is not None
        assert isinstance(PRODUCT_METRICS, ProductMetrics)
        
        # Test recording via global instance
        PRODUCT_METRICS.record_run_start("global_test_run")
        assert "global_test_run" in PRODUCT_METRICS._runs


def test_manual_mvp_publication():
    """Test manual MVP publication recording."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        metrics = ProductMetrics(tmp_path)
        
        run_id = "test_run_001"
        metrics.record_run_start(run_id)
        metrics.record_manual_mvp_publication(run_id)
        
        assert metrics._runs[run_id]['mvp_published'] is True


def test_metrics_time_filtering():
    """Test that dashboard metrics filter by time correctly."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        metrics = ProductMetrics(tmp_path)
        
        # Create runs with different timestamps
        import time
        now = time.time()
        
        # Recent run (within 30 days)
        metrics.record_run_start("recent_run")
        metrics._runs["recent_run"]['created_at'] = now
        
        # Old run (more than 30 days ago)
        metrics.record_run_start("old_run")
        metrics._runs["old_run"]['created_at'] = now - (40 * 24 * 3600)
        
        # Get metrics for last 30 days
        dashboard_metrics = metrics.get_dashboard_metrics(days=30)
        
        # Should only count recent run
        assert dashboard_metrics['runs_count'] == 1
        assert "recent_run" in [r['run_id'] for r in metrics._runs.values() if r['created_at'] >= (now - 30 * 24 * 3600)]


if __name__ == "__main__":
    pytest.main([__file__])
