"""
Tests pour le gestionnaire d'erreurs unifié
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock

from app.core.error_handler import (
    ErrorHandler, ErrorCategory, ErrorSeverity, handle_error
)


class TestErrorHandler:
    """Tests pour la classe ErrorHandler"""
    
    def test_error_handler_initialization(self):
        """Test l'initialisation du gestionnaire d'erreurs"""
        handler = ErrorHandler()
        
        assert handler.error_handlers == {}
        assert handler.error_history == []
        assert len(handler.recovery_strategies) > 0
        assert len(handler.suggestion_patterns) > 0
    
    def test_handle_basic_error(self):
        """Test la gestion d'une erreur basique"""
        handler = ErrorHandler()
        
        # Créer une exception test
        exception = ValueError("Test error message")
        
        # Gérer l'erreur
        error = handler.handle_error(
            exception=exception,
            category=ErrorCategory.VALIDATION,
            message="Custom message",
            severity=ErrorSeverity.MEDIUM
        )
        
        # Vérifications
        assert isinstance(error, AsmblrError)
        assert error.category == ErrorCategory.VALIDATION
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.message == "Custom message"
        assert error.original_exception == exception
        assert error.error_id.startswith("validation_")
        assert len(handler.error_history) == 1
    
    def test_handle_error_with_context(self):
        """Test la gestion d'erreur avec contexte"""
        handler = ErrorHandler()
        exception = FileNotFoundError("File not found")
        
        context = ErrorContext(
            user_id="user123",
            component="File Manager",
            operation="read_file",
            file_path="/path/to/file.txt"
        )
        
        error = handler.handle_error(
            exception=exception,
            category=ErrorCategory.FILE_IO,
            context=context
        )
        
        assert error.context.user_id == "user123"
        assert error.context.component == "File Manager"
        assert error.context.operation == "read_file"
        assert error.context.file_path == "/path/to/file.txt"
    
    def test_error_suggestions_generation(self):
        """Test la génération de suggestions"""
        handler = ErrorHandler()
        
        # Test avec ConnectionError
        exception = ConnectionError("Connection failed")
        error = handler.handle_error(
            exception=exception,
            category=ErrorCategory.NETWORK
        )
        
        assert len(error.suggestions) > 0
        assert any("réseau" in s.lower() or "network" in s.lower() for s in error.suggestions)
    
    def test_error_recovery_actions(self):
        """Test la génération d'actions de récupération"""
        handler = ErrorHandler()
        
        exception = TimeoutError("Operation timeout")
        error = handler.handle_error(
            exception=exception,
            category=ErrorCategory.LLM
        )
        
        assert len(error.recovery_actions) > 0
        assert any("fallback" in action.lower() for action in error.recovery_actions)
    
    def test_error_statistics(self):
        """Test les statistiques d'erreurs"""
        handler = ErrorHandler()
        
        # Ajouter plusieurs erreurs
        handler.handle_error(ValueError("Error 1"), ErrorCategory.VALIDATION)
        handler.handle_error(ConnectionError("Error 2"), ErrorCategory.NETWORK)
        handler.handle_error(ValueError("Error 3"), ErrorCategory.VALIDATION, severity=ErrorSeverity.HIGH)
        
        stats = handler.get_error_statistics()
        
        assert stats["total_errors"] == 3
        assert stats["by_category"]["validation"] == 2
        assert stats["by_category"]["network"] == 1
        assert stats["by_severity"]["medium"] == 2
        assert stats["by_severity"]["high"] == 1
        assert stats["most_common_category"] == "validation"
    
    def test_error_history_limit(self):
        """Test la limitation de l'historique des erreurs"""
        handler = ErrorHandler()
        
        # Simuler beaucoup d'erreurs
        for i in range(1100):
            handler.handle_error(ValueError(f"Error {i}"), ErrorCategory.VALIDATION)
        
        # L'historique devrait être limité
        assert len(handler.error_history) <= 1000
    
    def test_custom_handler_registration(self):
        """Test l'enregistrement de handlers personnalisés"""
        handler = ErrorHandler()
        
        # Créer un handler mock
        mock_handler = Mock()
        
        # Enregistrer le handler
        handler.register_handler(ErrorCategory.NETWORK, mock_handler)
        
        # Gérer une erreur réseau
        handler.handle_error(ConnectionError("Test"), ErrorCategory.NETWORK)
        
        # Vérifier que le handler a été appelé
        mock_handler.assert_called_once()
        
        # Vérifier l'argument passé
        call_args = mock_handler.call_args[0]
        assert isinstance(call_args[0], AsmblrError)
        assert call_args[0].category == ErrorCategory.NETWORK
    
    def test_error_export_json(self):
        """Test l'export des erreurs en JSON"""
        handler = ErrorHandler()
        
        # Ajouter des erreurs
        handler.handle_error(ValueError("Test error"), ErrorCategory.VALIDATION)
        
        # Exporter
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            success = handler.export_errors(temp_path, "json")
            assert success
            assert temp_path.exists()
            
            # Vérifier le contenu
            import json
            with open(temp_path) as f:
                data = json.load(f)
            
            assert len(data) == 1
            assert data[0]["category"] == "validation"
            assert data[0]["message"] == "Test error"
        finally:
            temp_path.unlink(missing_ok=True)
    
    def test_context_extraction_from_exception(self):
        """Test l'extraction automatique du contexte"""
        handler = ErrorHandler()
        
        try:
            # Simuler une erreur avec traceback
            def nested_function():
                raise RuntimeError("Nested error")
            
            nested_function()
        except Exception as e:
            error = handler.handle_error(e, ErrorCategory.RUNTIME)
            
            # Le contexte devrait être extrait automatiquement
            assert error.context.function_name is not None
            assert error.context.file_path is not None
    
    def test_clear_history(self):
        """Test l'effacement de l'historique"""
        handler = ErrorHandler()
        
        # Ajouter des erreurs
        handler.handle_error(ValueError("Test"), ErrorCategory.VALIDATION)
        assert len(handler.error_history) == 1
        
        # Effacer
        handler.clear_history()
        assert len(handler.error_history) == 0


class TestHelperFunctions:
    """Tests pour les fonctions helper"""
    
    def test_handle_error_function(self):
        """Test la fonction handle_error"""
        exception = ValueError("Test")
        
        error = handle_error(
            exception=exception,
            category=ErrorCategory.VALIDATION,
            message="Helper test",
            test_metadata="test_value"
        )
        
        assert isinstance(error, AsmblrError)
        assert error.category == ErrorCategory.VALIDATION
        assert error.message == "Helper test"
        assert error.metadata["test_metadata"] == "test_value"
    
    def test_register_error_handler_function(self):
        """Test la fonction register_error_handler"""
        mock_handler = Mock()
        
        register_error_handler(ErrorCategory.CACHE, mock_handler)
        
        # Vérifier que le handler est enregistré globalement
        assert ErrorCategory.CACHE in ERROR_HANDLER.error_handlers
        assert mock_handler in ERROR_HANDLER.error_handlers[ErrorCategory.CACHE]
    
    def test_error_handler_decorator(self):
        """Test le décorateur error_handler"""
        
        @error_handler(category=ErrorCategory.FILE_IO, reraise=False)
        def failing_function():
            raise FileNotFoundError("Test file not found")
        
        # La fonction ne devrait pas lever d'exception
        result = failing_function()
        assert result is None
        
        # Une erreur devrait être enregistrée
        assert len(ERROR_HANDLER.error_history) > 0
        last_error = ERROR_HANDLER.error_history[-1]
        assert last_error.category == ErrorCategory.FILE_IO
        assert "file not found" in last_error.message.lower()
    
    def test_error_handler_decorator_with_reraise(self):
        """Test le décorateur avec reraise=True"""
        
        @error_handler(category=ErrorCategory.NETWORK, reraise=True)
        def failing_function():
            raise ConnectionError("Connection failed")
        
        # L'exception devrait être relancée
        with pytest.raises(ConnectionError):
            failing_function()
        
        # Mais une erreur devrait quand même être enregistrée
        assert len(ERROR_HANDLER.error_history) > 0
        last_error = ERROR_HANDLER.error_history[-1]
        assert last_error.category == ErrorCategory.NETWORK


class TestErrorCategories:
    """Tests pour les différentes catégories d'erreurs"""
    
    def test_network_error_handling(self):
        """Test la gestion des erreurs réseau"""
        handler = ErrorHandler()
        
        exception = ConnectionError("Network timeout")
        error = handler.handle_error(exception, ErrorCategory.NETWORK)
        
        assert error.category == ErrorCategory.NETWORK
        assert any("network" in s.lower() for s in error.suggestions)
        assert any("retry" in s.lower() for s in error.recovery_actions)
    
    def test_llm_error_handling(self):
        """Test la gestion des erreurs LLM"""
        handler = ErrorHandler()
        
        exception = TimeoutError("LLM request timeout")
        error = handler.handle_error(exception, ErrorCategory.LLM)
        
        assert error.category == ErrorCategory.LLM
        assert any("model" in s.lower() for s in error.suggestions)
        assert any("fallback" in s.lower() for s in error.recovery_actions)
    
    def test_file_io_error_handling(self):
        """Test la gestion des erreurs fichier"""
        handler = ErrorHandler()
        
        exception = PermissionError("Permission denied")
        error = handler.handle_error(exception, ErrorCategory.FILE_IO)
        
        assert error.category == ErrorCategory.FILE_IO
        assert any("permission" in s.lower() for s in error.suggestions)
        assert any("vérifier" in s.lower() for s in error.recovery_actions)
    
    def test_cache_error_handling(self):
        """Test la gestion des erreurs de cache"""
        handler = ErrorHandler()
        
        exception = RuntimeError("Cache overflow")
        error = handler.handle_error(exception, ErrorCategory.CACHE)
        
        assert error.category == ErrorCategory.CACHE
        assert any("cache" in s.lower() for s in error.suggestions)
        assert any("vider" in s.lower() for s in error.recovery_actions)


class TestErrorSeverity:
    """Tests pour les niveaux de sévérité"""
    
    def test_all_severity_levels(self):
        """Test tous les niveaux de sévérité"""
        handler = ErrorHandler()
        exception = ValueError("Test")
        
        for severity in ErrorSeverity:
            error = handler.handle_error(exception, ErrorCategory.VALIDATION, severity=severity)
            assert error.severity == severity
    
    def test_severity_statistics(self):
        """Test les statistiques par sévérité"""
        handler = ErrorHandler()
        
        # Ajouter des erreurs de différentes sévérités
        handler.handle_error(ValueError("Low"), ErrorCategory.VALIDATION, ErrorSeverity.LOW)
        handler.handle_error(ValueError("Medium"), ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM)
        handler.handle_error(ValueError("High"), ErrorCategory.VALIDATION, ErrorSeverity.HIGH)
        handler.handle_error(ValueError("Critical"), ErrorCategory.VALIDATION, ErrorSeverity.CRITICAL)
        
        stats = handler.get_error_statistics()
        
        assert stats["by_severity"]["low"] == 1
        assert stats["by_severity"]["medium"] == 1
        assert stats["by_severity"]["high"] == 1
        assert stats["by_severity"]["critical"] == 1


# Instance globale pour les tests
ERROR_HANDLER = ErrorHandler()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
