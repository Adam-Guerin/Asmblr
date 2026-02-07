"""Test atomic write functionality to prevent race conditions."""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.core.run_manager import RunManager


def test_write_json_atomic_basic():
    """Test basic atomic write functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        runs_dir = Path(temp_dir) / "runs"
        data_dir = Path(temp_dir) / "data"
        runs_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock the database initialization to avoid file locking issues
        with patch('sqlite3.connect'):
            manager = RunManager(runs_dir, data_dir)
        
        # Create a mock run
        run_id = "test-run-123"
        with patch.object(manager, 'get_run') as mock_get_run:
            mock_get_run.return_value = {
                "id": run_id,
                "output_dir": str(runs_dir / run_id)
            }
            
            # Test atomic write
            test_data = {"test": "data", "number": 42}
            result_path = manager.write_json_atomic(run_id, "test.json", test_data)
            
            # Verify file was created
            assert result_path.exists()
            
            # Verify content is correct
            with open(result_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            assert loaded_data == test_data


def test_write_json_atomic_overwrite():
    """Test that atomic write properly overwrites existing files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        runs_dir = Path(temp_dir) / "runs"
        data_dir = Path(temp_dir) / "data"
        runs_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock the database initialization to avoid file locking issues
        with patch('sqlite3.connect'):
            manager = RunManager(runs_dir, data_dir)
        
        # Create a mock run
        run_id = "test-run-123"
        with patch.object(manager, 'get_run') as mock_get_run:
            mock_get_run.return_value = {
                "id": run_id,
                "output_dir": str(runs_dir / run_id)
            }
            
            # Write initial data
            initial_data = {"initial": "data"}
            manager.write_json_atomic(run_id, "test.json", initial_data)
            
            # Overwrite with new data
            new_data = {"new": "data", "updated": True}
            result_path = manager.write_json_atomic(run_id, "test.json", new_data)
            
            # Verify content was updated
            with open(result_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            assert loaded_data == new_data
            assert loaded_data != initial_data


def test_write_json_atomic_concurrent():
    """Test that atomic writes work correctly under concurrent access."""
    with tempfile.TemporaryDirectory() as temp_dir:
        runs_dir = Path(temp_dir) / "runs"
        data_dir = Path(temp_dir) / "data"
        runs_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock the database initialization to avoid file locking issues
        with patch('sqlite3.connect'):
            manager = RunManager(runs_dir, data_dir)
        
        # Create a mock run
        run_id = "test-run-123"
        with patch.object(manager, 'get_run') as mock_get_run:
            mock_get_run.return_value = {
                "id": run_id,
                "output_dir": str(runs_dir / run_id)
            }
            
            def write_data(thread_id):
                """Function to write data from different threads."""
                data = {
                    "thread_id": thread_id,
                    "timestamp": time.time(),
                    "data": f"from_thread_{thread_id}"
                }
                return manager.write_json_atomic(run_id, "concurrent_test.json", data)
            
            # Run multiple threads writing to the same file
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(write_data, i) for i in range(10)]
                results = [future.result() for future in as_completed(futures)]
            
            # Verify that exactly one file exists and has valid JSON
            target_path = runs_dir / run_id / "concurrent_test.json"
            assert target_path.exists()
            
            # Verify the file contains valid JSON
            with open(target_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            # Verify it has the expected structure
            assert "thread_id" in loaded_data
            assert "timestamp" in loaded_data
            assert "data" in loaded_data
            assert isinstance(loaded_data["thread_id"], int)
            assert 0 <= loaded_data["thread_id"] < 10


def test_write_json_atomic_fallback():
    """Test fallback to non-atomic write when atomic operation fails."""
    with tempfile.TemporaryDirectory() as temp_dir:
        runs_dir = Path(temp_dir) / "runs"
        data_dir = Path(temp_dir) / "data"
        runs_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock the database initialization to avoid file locking issues
        with patch('sqlite3.connect'):
            manager = RunManager(runs_dir, data_dir)
        
        # Create a mock run
        run_id = "test-run-123"
        with patch.object(manager, 'get_run') as mock_get_run:
            mock_get_run.return_value = {
                "id": run_id,
                "output_dir": str(runs_dir / run_id)
            }
            
            test_data = {"fallback": "test"}
            
            # Mock os.rename to fail to trigger fallback
            with patch('os.rename', side_effect=OSError("Simulated failure")):
                result_path = manager.write_json_atomic(run_id, "fallback_test.json", test_data)
            
            # Verify file was still created via fallback
            assert result_path.exists()
            
            # Verify content is correct
            with open(result_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            assert loaded_data == test_data


def test_write_json_atomic_cleanup():
    """Test that temporary files are cleaned up on failure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        runs_dir = Path(temp_dir) / "runs"
        data_dir = Path(temp_dir) / "data"
        runs_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock the database initialization to avoid file locking issues
        with patch('sqlite3.connect'):
            manager = RunManager(runs_dir, data_dir)
        
        # Create a mock run
        run_id = "test-run-123"
        with patch.object(manager, 'get_run') as mock_get_run:
            mock_get_run.return_value = {
                "id": run_id,
                "output_dir": str(runs_dir / run_id)
            }
            
            test_data = {"cleanup": "test"}
            
            # Mock json.dump to fail after writing some data
            def failing_dump(*args, **kwargs):
                raise ValueError("Simulated JSON write failure")
            
            with patch('json.dump', side_effect=failing_dump):
                try:
                    manager.write_json_atomic(run_id, "cleanup_test.json", test_data)
                except Exception:
                    pass  # Expected to fail
            
            # Verify no temporary files remain
            target_dir = runs_dir / run_id
            temp_files = list(target_dir.glob("*.tmp"))
            assert len(temp_files) == 0, f"Found temporary files: {temp_files}"
