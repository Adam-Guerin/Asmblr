"""Integration tests for error handling system."""

from unittest.mock import patch

from app.core.error_handler import (
    ErrorHandler, ErrorInfo, ErrorSeverity, ErrorCategory,
    handle_error, format_error_for_ui
)


class TestErrorHandler:
    """Test suite for error handling functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.handler = ErrorHandler()
    
    def test_connection_error_handling(self):
        """Test handling of connection errors."""
        error = ConnectionError("Connection refused")
        context = {"url": "http://localhost:11434", "retry_count": 3}
        
        error_info = self.handler.handle_error(error, context)
        
        assert error_info.category == ErrorCategory.NETWORK
        assert error_info.severity == ErrorSeverity.HIGH
        assert "Ollama" in error_info.user_message
        assert len(error_info.solutions) > 0
        
        # Check solution content
        solution = error_info.solutions[0]
        assert "Ollama" in solution.title
        assert len(solution.steps) > 0
    
    def test_model_not_found_error(self):
        """Test handling of model not found errors."""
        error = Exception("Model 'llama3.1:8b' not found")
        context = {"model": "llama3.1:8b"}
        
        error_info = self.handler.handle_error(error, context)
        
        assert error_info.category == ErrorCategory.LLM
        assert "modèle" in error_info.user_message.lower()
        assert len(error_info.solutions) > 0
        
        # Check for model pull solution
        solution_titles = [sol.title for sol in error_info.solutions]
        assert any("Télécharger" in title for title in solution_titles)
    
    def test_permission_error_handling(self):
        """Test handling of permission errors."""
        error = PermissionError("Permission denied: '/app/data'")
        context = {"path": "/app/data", "operation": "write"}
        
        error_info = self.handler.handle_error(error, context)
        
        assert error_info.category == ErrorCategory.PERMISSION
        assert error_info.severity == ErrorSeverity.CRITICAL
        assert "permission" in error_info.user_message.lower()
    
    def test_timeout_error_handling(self):
        """Test handling of timeout errors."""
        error = TimeoutError("Request timed out after 30 seconds")
        context = {"timeout": 30, "operation": "scraping"}
        
        error_info = self.handler.handle_error(error, context)
        
        assert error_info.category == ErrorCategory.NETWORK
        assert "temps" in error_info.user_message.lower()
        assert len(error_info.solutions) > 0
    
    def test_validation_error_handling(self):
        """Test handling of validation errors."""
        error = ValueError("Invalid topic: empty string")
        context = {"field": "topic", "value": ""}
        
        error_info = self.handler.handle_error(error, context)
        
        assert error_info.category == ErrorCategory.VALIDATION
        assert error_info.severity == ErrorSeverity.MEDIUM
        assert "valides" in error_info.user_message.lower()
    
    def test_unknown_error_handling(self):
        """Test handling of unknown errors."""
        error = RuntimeError("Unexpected error occurred")
        context = {"component": "pipeline"}
        
        error_info = self.handler.handle_error(error, context)
        
        assert error_info.category == ErrorCategory.UNKNOWN
        assert error_info.severity == ErrorSeverity.LOW
        assert "inattendue" in error_info.user_message.lower()
    
    def test_error_severity_determination(self):
        """Test error severity determination logic."""
        test_cases = [
            (PermissionError("denied"), ErrorSeverity.CRITICAL),
            (ImportError("module not found"), ErrorSeverity.CRITICAL),
            (ConnectionError("refused"), ErrorSeverity.HIGH),
            (TimeoutError("timeout"), ErrorSeverity.HIGH),
            (FileNotFoundError("not found"), ErrorSeverity.MEDIUM),
            (ValueError("invalid"), ErrorSeverity.MEDIUM),
            (RuntimeError("unknown"), ErrorSeverity.LOW),
        ]
        
        for error, expected_severity in test_cases:
            error_info = self.handler.handle_error(error)
            assert error_info.severity == expected_severity
    
    def test_error_context_preservation(self):
        """Test that error context is preserved."""
        error = Exception("Test error")
        context = {
            "run_id": "test_123",
            "stage": "scraping",
            "timestamp": "2024-01-01T12:00:00Z",
            "user_input": "test topic"
        }
        
        error_info = self.handler.handle_error(error, context)
        
        assert error_info.context == context
    
    def test_error_solution_structure(self):
        """Test error solution structure and content."""
        error = ConnectionError("Connection refused")
        error_info = self.handler.handle_error(error)
        
        for solution in error_info.solutions:
            assert isinstance(solution.title, str)
            assert len(solution.title) > 0
            assert isinstance(solution.description, str)
            assert len(solution.description) > 0
            assert isinstance(solution.steps, list)
            assert len(solution.steps) > 0
            assert all(isinstance(step, str) for step in solution.steps)
            assert isinstance(solution.auto_fixable, bool)
    
    def test_ui_formatting(self):
        """Test UI formatting of error information."""
        error = ConnectionError("Connection refused")
        error_info = self.handler.handle_error(error)
        
        ui_data = self.handler.format_for_ui(error_info)
        
        assert "severity" in ui_data
        assert "category" in ui_data
        assert "user_message" in ui_data
        assert "solutions" in ui_data
        assert "context" in ui_data
        assert "show_details" in ui_data
        
        # Check solution formatting
        for solution in ui_data["solutions"]:
            assert "title" in solution
            assert "description" in solution
            assert "steps" in solution
            assert "auto_fixable" in solution
    
    def test_traceback_inclusion(self):
        """Test that traceback is included when available."""
        error = Exception("Test error")
        
        with patch('traceback.format_exc', return_value="Mock traceback"):
            error_info = self.handler.handle_error(error)
        
        assert error_info.traceback == "Mock traceback"
    
    def test_error_categorization_edge_cases(self):
        """Test error categorization edge cases."""
        test_cases = [
            ("connection failed", ErrorCategory.NETWORK),
            ("network timeout", ErrorCategory.NETWORK),
            ("ollama error", ErrorCategory.LLM),
            ("llm response failed", ErrorCategory.LLM),
            ("permission denied", ErrorCategory.PERMISSION),
            ("access denied", ErrorCategory.PERMISSION),
            ("file not found", ErrorCategory.FILESYSTEM),
            ("directory error", ErrorCategory.FILESYSTEM),
            ("validation failed", ErrorCategory.VALIDATION),
            ("invalid input", ErrorCategory.VALIDATION),
            ("module not found", ErrorCategory.DEPENDENCY),
            ("import error", ErrorCategory.DEPENDENCY),
            ("config error", ErrorCategory.CONFIGURATION),
            ("setting missing", ErrorCategory.CONFIGURATION),
        ]
        
        for message, expected_category in test_cases:
            error = Exception(message)
            error_info = self.handler.handle_error(error)
            assert error_info.category == expected_category, f"Failed for: {message}"


class TestGlobalErrorHandler:
    """Test global error handler functions."""
    
    def test_handle_error_function(self):
        """Test global handle_error function."""
        error = ConnectionError("Test connection error")
        context = {"test": "context"}
        
        error_info = handle_error(error, context)
        
        assert isinstance(error_info, ErrorInfo)
        assert error_info.context == context
    
    def test_format_error_for_ui_function(self):
        """Test global format_error_for_ui function."""
        error = ConnectionError("Test error")
        error_info = handle_error(error)
        
        ui_data = format_error_for_ui(error_info)
        
        assert isinstance(ui_data, dict)
        assert "user_message" in ui_data
        assert "solutions" in ui_data
    
    @patch('app.core.error_handler.logger')
    def test_logging_integration(self, mock_logger):
        """Test integration with logging system."""
        error = Exception("Test error")
        
        handle_error(error)
        
        # Verify logging calls
        assert mock_logger.error.called
        assert mock_logger.debug.called


class TestErrorRecovery:
    """Test error recovery and suggestion mechanisms."""
    
    def setup_method(self):
        """Setup test environment."""
        self.handler = ErrorHandler()
    
    def test_ollama_recovery_suggestions(self):
        """Test Ollama-specific recovery suggestions."""
        error = ConnectionError("Connection refused")
        error_info = self.handler.handle_error(error)
        
        # Should have multiple recovery options
        assert len(error_info.solutions) >= 2
        
        # Check for specific recovery steps
        all_steps = []
        for solution in error_info.solutions:
            all_steps.extend(solution.steps)
        
        # Should include starting Ollama
        assert any("ollama serve" in step.lower() for step in all_steps)
        
        # Should include checking installation
        assert any("install" in step.lower() for step in all_steps)
    
    def test_model_recovery_suggestions(self):
        """Test model-specific recovery suggestions."""
        error = Exception("Model 'unknown_model' not found")
        error_info = self.handler.handle_error(error)
        
        # Should include model pull commands
        all_steps = []
        for solution in error_info.solutions:
            all_steps.extend(solution.steps)
        
        assert any("ollama pull" in step.lower() for step in all_steps)
    
    def test_permission_recovery_suggestions(self):
        """Test permission-specific recovery suggestions."""
        error = PermissionError("Permission denied")
        error_info = self.handler.handle_error(error)
        
        # Should include permission-related suggestions
        all_steps = []
        for solution in error_info.solutions:
            all_steps.extend(solution.steps)
        
        assert any("permission" in step.lower() for step in all_steps)
        assert any("droits" in step.lower() for step in all_steps)
    
    def test_timeout_recovery_suggestions(self):
        """Test timeout-specific recovery suggestions."""
        error = TimeoutError("Operation timed out")
        error_info = self.handler.handle_error(error)
        
        # Should include optimization suggestions
        all_steps = []
        for solution in error_info.solutions:
            all_steps.extend(solution.steps)
        
        assert any("mode" in step.lower() for step in all_steps)
        assert any("réduisez" in step.lower() for step in all_steps)


class TestErrorHandlingIntegration:
    """Integration tests for error handling with other components."""
    
    @patch('app.core.error_handler.logger')
    def test_error_in_pipeline_context(self, mock_logger):
        """Test error handling in pipeline context."""
        error = Exception("Pipeline failed")
        context = {
            "run_id": "test_run_123",
            "stage": "scraping",
            "topic": "AI compliance",
            "n_ideas": 10,
            "execution_profile": "standard"
        }
        
        error_info = handle_error(error, context)
        
        assert error_info.context["run_id"] == "test_run_123"
        assert error_info.context["stage"] == "scraping"
        assert mock_logger.error.called
    
    def test_error_with_user_data(self):
        """Test error handling with user-provided data."""
        error = ValueError("Invalid topic")
        context = {
            "user_input": "",
            "field": "topic",
            "validation_rule": "non_empty_string"
        }
        
        error_info = handle_error(error, context)
        
        assert error_info.category == ErrorCategory.VALIDATION
        assert error_info.context["user_input"] == ""
        assert error_info.context["field"] == "topic"
    
    def test_error_recovery_workflow(self):
        """Test complete error recovery workflow."""
        # Simulate error occurrence
        error = ConnectionError("Ollama not reachable")
        error_info = handle_error(error)
        
        # Format for UI
        ui_data = format_error_for_ui(error_info)
        
        # Verify workflow components
        assert ui_data["user_message"]  # User-friendly message
        assert ui_data["solutions"]  # Recovery suggestions
        assert ui_data["show_details"]  # Technical details availability
        
        # Verify solution completeness
        for solution in ui_data["solutions"]:
            assert solution["title"]  # Descriptive title
            assert solution["description"]  # Clear description
            assert solution["steps"]  # Actionable steps
            assert len(solution["steps"]) > 0  # At least one step
