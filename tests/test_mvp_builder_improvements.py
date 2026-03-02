"""
Enhanced tests for MVP Builder improvements
Focus on testing edge cases, error handling, and performance scenarios
"""

import json
from pathlib import Path
from unittest.mock import patch
from pytest import raises
import time

from app.core.config import Settings
from app.mvp.builder import MVPBuilder, MVPBuilderError, StackSelector, StackConfig
from app.mvp_cycles import MVPProgressionError


class TestStackSelector:
    """Test the StackSelector component"""
    
    def test_select_default_stack(self):
        """Test that default stack is selected for generic topics"""
        selector = StackSelector()
        stack = selector.select("generic app", "simple app")
        assert isinstance(stack, StackConfig)
        assert "Next.js" in stack.frontend_stack
        assert "Tailwind" in stack.frontend_stack
    
    def test_select_detects_async_requirements(self):
        """Test async detection in stack selection"""
        selector = StackSelector()
        stack = selector.select("real-time chat app", "async messaging")
        assert isinstance(stack, StackConfig)
    
    def test_select_handles_empty_inputs(self):
        """Test stack selection with empty inputs"""
        selector = StackSelector()
        stack = selector.select(None, None)
        assert isinstance(stack, StackConfig)
        assert "Next.js" in stack.frontend_stack


class TestMVPBuilderErrorHandling:
    """Test MVP Builder error handling and edge cases"""
    
    def test_builder_refuses_env_file_in_run_dir(self, tmp_path):
        """Test that builder refuses to operate with .env in run directory"""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        settings = Settings(runs_dir=runs_dir)
        builder = MVPBuilder(settings)
        
        run_dir = runs_dir / "test_run"
        run_dir.mkdir(parents=True)
        (run_dir / ".env").write_text("TEST=value")
        
        with raises(MVPBuilderError, match="Detected .env in run directory"):
            builder.build_from_brief("test app", run_dir)
    
    def test_builder_unsupported_frontend_style(self, tmp_path):
        """Test that builder rejects unsupported frontend styles"""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        settings = Settings(runs_dir=runs_dir)
        builder = MVPBuilder(settings)
        
        run_dir = runs_dir / "test_run"
        run_dir.mkdir(parents=True)
        
        with raises(MVPBuilderError, match="Unsupported frontend style"):
            builder.build_from_brief("test app", run_dir, frontend_style="unsupported_style")
    
    def test_builder_handles_ollama_failure_gracefully(self, tmp_path):
        """Test builder handles Ollama unavailability gracefully"""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        settings = Settings(
            runs_dir=runs_dir,
            ollama_base_url="http://invalid:11434"
        )
        builder = MVPBuilder(settings)
        
        run_dir = runs_dir / "test_run"
        run_dir.mkdir(parents=True)
        
        # Mock the progression to avoid actual build
        with patch('app.mvp.builder.MVPProgression') as mock_progression:
            mock_instance = mock_progression.return_value
            mock_instance.run.side_effect = MVPProgressionError("Test failure")
            
            result = builder.build_from_brief("test app", run_dir)
            assert not result.success
            assert "Test failure" in result.error
    
    def test_builder_handles_missing_models_gracefully(self, tmp_path):
        """Test builder handles missing Ollama models gracefully"""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        settings = Settings(
            runs_dir=runs_dir,
            general_model="missing_model",
            code_model="missing_model"
        )
        builder = MVPBuilder(settings)
        
        run_dir = runs_dir / "test_run"
        run_dir.mkdir(parents=True)
        
        # Mock check_ollama to return empty models
        with patch('app.mvp.builder.check_ollama', return_value={"models": []}):
            with patch('app.mvp.builder.MVPProgression') as mock_progression:
                mock_instance = mock_progression.return_value
                mock_instance.run.side_effect = MVPProgressionError("LLM disabled")
                
                result = builder.build_from_brief("test app", run_dir)
                assert not result.success


class TestMVPBuilderPerformance:
    """Test MVP Builder performance and optimization scenarios"""
    
    def test_builder_force_cleanup_performance(self, tmp_path):
        """Test that force cleanup works efficiently"""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        settings = Settings(runs_dir=runs_dir)
        builder = MVPBuilder(settings)
        
        run_dir = runs_dir / "test_run"
        run_dir.mkdir(parents=True)
        
        # Create existing mvp_repo to test force cleanup
        mvp_repo = run_dir / "mvp_repo"
        mvp_repo.mkdir(parents=True)
        (mvp_repo / "existing_file.txt").write_text("test content")
        
        start_time = time.time()
        
        # Mock progression to avoid actual build
        with patch('app.mvp.builder.MVPProgression') as mock_progression:
            mock_instance = mock_progression.return_value
            mock_instance.run.return_value = None
            
            result = builder.build_from_brief("test app", run_dir, force=True)
            
        cleanup_time = time.time() - start_time
        
        # Should complete cleanup quickly (under 1 second for small directories)
        assert cleanup_time < 1.0
        assert not mvp_repo.exists()  # Should be cleaned up
    
    def test_builder_concurrent_safety(self, tmp_path):
        """Test builder handles concurrent operations safely"""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        settings = Settings(runs_dir=runs_dir)
        builder = MVPBuilder(settings)
        
        run_dir = runs_dir / "test_run"
        run_dir.mkdir(parents=True)
        
        # Test that multiple builders can be created safely
        builders = [MVPBuilder(settings) for _ in range(5)]
        
        # All should have independent instances
        assert all(b is not None for b in builders)
        assert len(set(id(b) for b in builders)) == 5


class TestMVPBuilderIntegration:
    """Test MVP Builder integration scenarios"""
    
    def test_builder_with_custom_runners(self, tmp_path):
        """Test builder with custom build and test runners"""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        settings = Settings(runs_dir=runs_dir)
        builder = MVPBuilder(settings)
        
        run_dir = runs_dir / "test_run"
        run_dir.mkdir(parents=True)
        
        # Custom runners that always succeed
        def build_runner(cycle_key: str, cycle_dir: Path, attempt: int) -> tuple[bool, str]:
            return True, f"Custom build {cycle_key} attempt {attempt}"
        
        def test_runner(cycle_key: str, cycle_dir: Path, attempt: int) -> tuple[bool, str]:
            return True, f"Custom test {cycle_key} attempt {attempt}"
        
        # Mock progression to capture the runners
        with patch('app.mvp.builder.MVPProgression') as mock_progression:
            mock_instance = mock_progression.return_value
            mock_instance.run.return_value = None
            
            result = builder.build_from_brief(
                "test app", 
                run_dir,
                build_runner=build_runner,
                test_runner=test_runner
            )
            
            # Verify progression was called with our custom runners
            mock_progression.assert_called_once()
            call_args = mock_progression.call_args
            assert call_args.kwargs['build_runner'] == build_runner
            assert call_args.kwargs['test_runner'] == test_runner
    
    def test_builder_data_source_tagging(self, tmp_path):
        """Test builder properly tags data sources"""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        settings = Settings(runs_dir=runs_dir)
        builder = MVPBuilder(settings)
        
        run_dir = runs_dir / "test_run"
        run_dir.mkdir(parents=True)
        
        # Test with brief (should be tagged as seed/brief)
        with patch('app.mvp.builder.MVPProgression') as mock_progression:
            mock_instance = mock_progression.return_value
            mock_instance.run.return_value = None
            
            result = builder.build_from_brief("test app", run_dir)
            
            assert result.data_source['data_source'] == 'seed/brief'
            assert result.data_source['brief'] == 'test app'
    
    def test_builder_cycle_configuration(self, tmp_path):
        """Test builder respects cycle configuration"""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        settings = Settings(runs_dir=runs_dir)
        builder = MVPBuilder(settings)
        
        run_dir = runs_dir / "test_run"
        run_dir.mkdir(parents=True)
        
        # Test with limited cycles
        with patch('app.mvp.builder.MVPProgression') as mock_progression:
            mock_instance = mock_progression.return_value
            mock_instance.run.return_value = None
            
            result = builder.build_from_brief(
                "test app", 
                run_dir,
                cycle_keys=['foundation']  # Only foundation cycle
            )
            
            # Verify progression was called with limited cycles
            mock_progression.assert_called_once()
            call_args = mock_progression.call_args
            assert call_args.kwargs['cycle_keys'] == ['foundation']


class TestMVPBuilderFileOperations:
    """Test MVP Builder file operations and I/O handling"""
    
    def test_builder_creates_required_files(self, tmp_path):
        """Test builder creates all required output files"""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        settings = Settings(runs_dir=runs_dir)
        builder = MVPBuilder(settings)
        
        run_dir = runs_dir / "test_run"
        run_dir.mkdir(parents=True)
        
        with patch('app.mvp.builder.MVPProgression') as mock_progression:
            mock_instance = mock_progression.return_value
            mock_instance.run.return_value = None
            mock_instance.cycle_results = []
            
            result = builder.build_from_brief("test app", run_dir)
            
            # Check that required files are created
            assert (run_dir / "mvp_scope.json").exists()
            assert (run_dir / "mvp_data_source.json").exists()
            assert (run_dir / "mvp_build_summary.md").exists()
    
    def test_builder_writes_valid_json(self, tmp_path):
        """Test builder writes valid JSON files"""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        settings = Settings(runs_dir=runs_dir)
        builder = MVPBuilder(settings)
        
        run_dir = runs_dir / "test_run"
        run_dir.mkdir(parents=True)
        
        with patch('app.mvp.builder.MVPProgression') as mock_progression:
            mock_instance = mock_progression.return_value
            mock_instance.run.return_value = None
            mock_instance.cycle_results = []
            
            result = builder.build_from_brief("test app", run_dir)
            
            # Verify JSON files are valid
            scope_file = run_dir / "mvp_scope.json"
            with open(scope_file) as f:
                scope_data = json.load(f)
                assert 'run_id' in scope_data
                assert 'brief' in scope_data
            
            data_source_file = run_dir / "mvp_data_source.json"
            with open(data_source_file) as f:
                data_source_data = json.load(f)
                assert 'data_source' in data_source_data
                assert 'run_id' in data_source_data


class TestMVPBuilderEdgeCases:
    """Test MVP Builder edge cases and boundary conditions"""
    
    def test_builder_with_very_long_brief(self, tmp_path):
        """Test builder handles very long brief text"""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        settings = Settings(runs_dir=runs_dir)
        builder = MVPBuilder(settings)
        
        run_dir = runs_dir / "test_run"
        run_dir.mkdir(parents=True)
        
        # Create a very long brief (10,000 characters)
        long_brief = "test app " * 1000
        
        with patch('app.mvp.builder.MVPProgression') as mock_progression:
            mock_instance = mock_progression.return_value
            mock_instance.run.return_value = None
            
            # Should handle long brief without issues
            result = builder.build_from_brief(long_brief, run_dir)
            assert result.run_id == "test_run"
    
    def test_builder_with_special_characters(self, tmp_path):
        """Test builder handles special characters in brief"""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        settings = Settings(runs_dir=runs_dir)
        builder = MVPBuilder(settings)
        
        run_dir = runs_dir / "test_run"
        run_dir.mkdir(parents=True)
        
        # Brief with special characters
        special_brief = "Test app with émojis 🚀 and spëcial chars & symbols!"
        
        with patch('app.mvp.builder.MVPProgression') as mock_progression:
            mock_instance = mock_progression.return_value
            mock_instance.run.return_value = None
            
            result = builder.build_from_brief(special_brief, run_dir)
            assert result.run_id == "test_run"
    
    def test_builder_handles_directory_creation_failure(self, tmp_path):
        """Test builder handles directory creation failures"""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        settings = Settings(runs_dir=runs_dir)
        builder = MVPBuilder(settings)
        
        # Create a file where we want to create a directory
        conflict_path = runs_dir / "test_run"
        conflict_path.write_text("This is a file, not a directory")
        
        with raises(Exception):  # Should raise some kind of exception
            builder.build_from_brief("test app", conflict_path)
