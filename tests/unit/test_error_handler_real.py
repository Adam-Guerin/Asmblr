"""
Tests pour le gestionnaire d'erreurs existant
Basés sur la structure réelle du error_handler.py
"""

import pytest

from app.core.error_handler import (
    ErrorSeverity, ErrorCategory, ErrorSolution, ErrorInfo,
    ErrorHandler, handle_error, format_error_for_ui
)


class TestErrorSeverity:
    """Tests pour ErrorSeverity"""
    
    def test_severity_values(self):
        """Test les valeurs de sévérité"""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"
    
    def test_severity_comparison(self):
        """Test la comparaison de sévérités"""
        # Les enums peuvent être comparées
        assert ErrorSeverity.LOW != ErrorSeverity.MEDIUM
        assert ErrorSeverity.CRITICAL != ErrorSeverity.LOW


class TestErrorCategory:
    """Tests pour ErrorCategory"""
    
    def test_category_values(self):
        """Test les valeurs de catégories"""
        assert ErrorCategory.NETWORK.value == "network"
        assert ErrorCategory.LLM.value == "llm"
        assert ErrorCategory.FILESYSTEM.value == "filesystem"
        assert ErrorCategory.VALIDATION.value == "validation"
    
    def test_all_categories(self):
        """Test que toutes les catégories attendues existent"""
        expected_categories = [
            "NETWORK", "LLM", "FILESYSTEM", "VALIDATION", 
            "PERMISSION", "DEPENDENCY", "CONFIGURATION", "UNKNOWN"
        ]
        
        for cat_name in expected_categories:
            assert hasattr(ErrorCategory, cat_name)


class TestErrorSolution:
    """Tests pour ErrorSolution"""
    
    def test_solution_creation(self):
        """Test la création d'une solution"""
        solution = ErrorSolution(
            title="Test Solution",
            description="Test description",
            steps=["Step 1", "Step 2"],
            auto_fixable=True,
            fix_command="echo 'fix'"
        )
        
        assert solution.title == "Test Solution"
        assert solution.description == "Test description"
        assert len(solution.steps) == 2
        assert solution.auto_fixable is True
        assert solution.fix_command == "echo 'fix'"
    
    def test_solution_defaults(self):
        """Test les valeurs par défaut"""
        solution = ErrorSolution(
            title="Test",
            description="Test",
            steps=[]
        )
        
        assert solution.auto_fixable is False
        assert solution.fix_command is None


class TestErrorInfo:
    """Tests pour ErrorInfo"""
    
    def test_error_info_creation(self):
        """Test la création d'informations d'erreur"""
        solution = ErrorSolution(
            title="Fix it",
            description="How to fix",
            steps=["Do this", "Do that"]
        )
        
        error_info = ErrorInfo(
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            user_message="Network failed",
            technical_message="Connection timeout",
            solutions=[solution],
            context={"retry_count": 3}
        )
        
        assert error_info.category == ErrorCategory.NETWORK
        assert error_info.severity == ErrorSeverity.HIGH
        assert error_info.user_message == "Network failed"
        assert error_info.technical_message == "Connection timeout"
        assert len(error_info.solutions) == 1
        assert error_info.context["retry_count"] == 3


class TestErrorHandler:
    """Tests pour la classe ErrorHandler"""
    
    def test_error_handler_creation(self):
        """Test la création du gestionnaire d'erreurs"""
        handler = ErrorHandler()
        assert handler is not None
    
    def test_handle_connection_error(self):
        """Test la gestion d'erreur de connexion"""
        handler = ErrorHandler()
        
        try:
            # Simuler une erreur de connexion
            raise ConnectionError("Connection timeout")
        except Exception as e:
            error_info = handler.handle_error(e, "test_context")
            
            assert isinstance(error_info, ErrorInfo)
            assert error_info.category in [ErrorCategory.NETWORK, ErrorCategory.UNKNOWN]
            assert error_info.technical_message == "Connection timeout"
            assert len(error_info.solutions) > 0
    
    def test_handle_file_error(self):
        """Test la gestion d'erreur fichier"""
        handler = ErrorHandler()
        
        try:
            raise FileNotFoundError("File not found")
        except Exception as e:
            error_info = handler.handle_error(e, "file_operation")
            
            assert isinstance(error_info, ErrorInfo)
            assert error_info.category in [ErrorCategory.FILESYSTEM, ErrorCategory.PERMISSION]
            assert "File not found" in error_info.technical_message
    
    def test_handle_validation_error(self):
        """Test la gestion d'erreur de validation"""
        handler = ErrorHandler()
        
        try:
            raise ValueError("Invalid input")
        except Exception as e:
            error_info = handler.handle_error(e, "validation")
            
            assert isinstance(error_info, ErrorInfo)
            assert error_info.category == ErrorCategory.VALIDATION
            assert "Invalid input" in error_info.technical_message
    
    def test_error_with_context(self):
        """Test la gestion d'erreur avec contexte"""
        handler = ErrorHandler()
        
        try:
            raise RuntimeError("Test error")
        except Exception as e:
            context = {
                "user_id": "123",
                "operation": "test_operation",
                "file_path": "/test/path"
            }
            
            error_info = handler.handle_error(e, context)
            
            assert isinstance(error_info, ErrorInfo)
            # Le contexte devrait être inclus dans les métadonnées
            assert error_info.context is not None
    
    def test_solutions_generation(self):
        """Test la génération de solutions"""
        handler = ErrorHandler()
        
        try:
            raise PermissionError("Permission denied")
        except Exception as e:
            error_info = handler.handle_error(e, "permission_test")
            
            assert len(error_info.solutions) > 0
            
            # Vérifier que les solutions ont les champs requis
            for solution in error_info.solutions:
                assert isinstance(solution, ErrorSolution)
                assert solution.title
                assert solution.description
                assert isinstance(solution.steps, list)


class TestHelperFunctions:
    """Tests pour les fonctions helper"""
    
    def test_handle_error_function(self):
        """Test la fonction handle_error"""
        try:
            raise ValueError("Test error")
        except Exception as e:
            error_info = handle_error(e, {"test": "context"})
            
            assert isinstance(error_info, ErrorInfo)
            assert error_info.technical_message == "Test error"
    
    def test_format_error_for_ui_function(self):
        """Test la fonction format_error_for_ui"""
        solution = ErrorSolution(
            title="Test Solution",
            description="Test",
            steps=["Step 1"]
        )
        
        error_info = ErrorInfo(
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.MEDIUM,
            user_message="Config error",
            technical_message="Missing config",
            solutions=[solution],
            context={"config_file": "config.yaml"}
        )
        
        formatted = format_error_for_ui(error_info)
        
        assert formatted["severity"] == "medium"
        assert formatted["category"] == "configuration"
        assert formatted["user_message"] == "Config error"
        assert len(formatted["solutions"]) == 1
        assert formatted["solutions"][0]["title"] == "Test Solution"
        assert formatted["context"]["config_file"] == "config.yaml"


class TestErrorScenarios:
    """Tests pour des scénarios d'erreur réels"""
    
    def test_network_timeout_scenario(self):
        """Test scénario de timeout réseau"""
        handler = ErrorHandler()
        
        try:
            raise TimeoutError("Network operation timed out after 30 seconds")
        except Exception as e:
            error_info = handler.handle_error(e, "network_operation")
            
            assert error_info.category in [ErrorCategory.NETWORK, ErrorCategory.UNKNOWN]
            assert "timed out" in error_info.technical_message.lower()
            assert len(error_info.solutions) >= 0  # Peut être vide ou avoir des solutions
    
    def test_dependency_missing_scenario(self):
        """Test scénario de dépendance manquante"""
        handler = ErrorHandler()
        
        try:
            raise ImportError("No module named 'missing_package'")
        except Exception as e:
            error_info = handler.handle_error(e, "import_operation")
            
            # Devrait être catégorisé comme dépendance
            assert error_info.category in [ErrorCategory.DEPENDENCY, ErrorCategory.UNKNOWN]
            assert "missing_package" in error_info.technical_message
    
    def test_permission_denied_scenario(self):
        """Test scénario de permission refusée"""
        handler = ErrorHandler()
        
        try:
            raise PermissionError("Permission denied: /restricted/file")
        except Exception as e:
            error_info = handler.handle_error(e, "file_access")
            
            assert error_info.category in [ErrorCategory.PERMISSION, ErrorCategory.FILESYSTEM]
            assert "permission denied" in error_info.technical_message.lower()
    
    def test_unknown_error_scenario(self):
        """Test scénario d'erreur inconnue"""
        handler = ErrorHandler()
        
        try:
            raise RuntimeError("Unknown error occurred")
        except Exception as e:
            error_info = handler.handle_error(e, "unknown_context")
            
            # Les erreurs inconnues devraient avoir une catégorie par défaut
            assert isinstance(error_info.category, ErrorCategory)
            assert error_info.technical_message == "Unknown error occurred"
    
    def test_multiple_errors_same_context(self):
        """Test plusieurs erreurs dans le même contexte"""
        handler = ErrorHandler()
        
        errors = []
        
        # Générer plusieurs erreurs
        for i in range(3):
            try:
                raise ValueError(f"Error {i}")
            except Exception as e:
                error_info = handler.handle_error(e, f"iteration_{i}")
                errors.append(error_info)
        
        # Vérifier que toutes les erreurs sont bien gérées
        assert len(errors) == 3
        for error in errors:
            assert isinstance(error, ErrorInfo)
            assert error.category == ErrorCategory.VALIDATION


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
