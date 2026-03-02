"""Enhanced error handling with user-friendly messages and recovery suggestions."""

from __future__ import annotations
import traceback
from typing import Any
from enum import Enum
from dataclasses import dataclass

from loguru import logger


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better handling."""
    NETWORK = "network"
    LLM = "llm"
    FILESYSTEM = "filesystem"
    VALIDATION = "validation"
    PERMISSION = "permission"
    DEPENDENCY = "dependency"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


@dataclass
class ErrorSolution:
    """Solution suggestion for an error."""
    title: str
    description: str
    steps: list[str]
    auto_fixable: bool = False
    fix_command: str | None = None


@dataclass
class ErrorInfo:
    """Enhanced error information."""
    category: ErrorCategory
    severity: ErrorSeverity
    user_message: str
    technical_message: str
    solutions: list[ErrorSolution]
    context: dict[str, Any]
    traceback: str | None = None


class ErrorHandler:
    """Enhanced error handler with user-friendly messages and recovery suggestions."""
    
    def __init__(self):
        self._error_solutions = self._initialize_error_solutions()
    
    def _initialize_error_solutions(self) -> dict[str, list[ErrorSolution]]:
        """Initialize predefined error solutions."""
        return {
            "connection_refused": [
                ErrorSolution(
                    title="Démarrer Ollama",
                    description="Ollama n'est pas en cours d'exécution",
                    steps=[
                        "Ouvrez un terminal",
                        "Exécutez: ollama serve",
                        "Attendez que le service démarre",
                        "Réessayez l'opération"
                    ],
                    auto_fixable=False
                ),
                ErrorSolution(
                    title="Vérifier l'installation",
                    description="Ollama peut ne pas être installé",
                    steps=[
                        "Téléchargez Ollama depuis https://ollama.ai/download",
                        "Installez-le selon votre OS",
                        "Redémarrez votre terminal",
                        "Vérifiez avec: ollama --version"
                    ],
                    auto_fixable=False
                )
            ],
            "model_not_found": [
                ErrorSolution(
                    title="Télécharger le modèle manquant",
                    description="Le modèle LLM requis n'est pas disponible",
                    steps=[
                        "Exécutez: ollama pull llama3.1:8b",
                        "Exécutez: ollama pull qwen2.5-coder:7b",
                        "Vérifiez avec: ollama list",
                        "Réessayez l'opération"
                    ],
                    auto_fixable=False
                )
            ],
            "permission_denied": [
                ErrorSolution(
                    title="Vérifier les permissions",
                    description="Permissions insuffisantes pour accéder aux fichiers",
                    steps=[
                        "Vérifiez que vous avez les droits d'écriture (permission)",
                        "Exécutez en tant qu'administrateur si nécessaire",
                        "Vérifiez que le dossier n'est pas en lecture seule",
                        "Réessayez l'opération"
                    ],
                    auto_fixable=False
                )
            ],
            "timeout": [
                ErrorSolution(
                    title="Optimiser le traitement",
                    description="L'opération a pris trop de temps",
                    steps=[
                        "Réduisez le nombre d'idées à générer",
                        "Utilisez le mode Fast",
                        "Vérifiez votre connexion internet",
                        "Essayez avec moins de sources"
                    ],
                    auto_fixable=False
                )
            ],
            "memory_error": [
                ErrorSolution(
                    title="Optimiser la mémoire",
                    description="Mémoire insuffisante pour le traitement",
                    steps=[
                        "Fermez d'autres applications",
                        "Utilisez le mode Fast",
                        "Réduisez le nombre de sources",
                        "Augmentez la mémoire virtuelle si possible"
                    ],
                    auto_fixable=False
                )
            ],
            "validation_error": [
                ErrorSolution(
                    title="Corriger les entrées",
                    description="Les données fournies ne sont pas valides",
                    steps=[
                        "Vérifiez que le topic n'est pas vide",
                        "Assurez-vous que le nombre d'idées est entre 1 et 20",
                        "Vérifiez que les URLs des sources sont valides",
                        "Réessayez avec des entrées valides"
                    ],
                    auto_fixable=False
                )
            ]
        }
    
    def handle_error(self, error: Exception, context: dict[str, Any] | None = None) -> ErrorInfo:
        """Handle an error and return user-friendly information."""
        context = context or {}
        error_message = str(error)
        error_type = type(error).__name__
        traceback_str = traceback.format_exc()
        
        logger.error(f"Handling error: {error_type}: {error_message}")
        logger.debug(f"Traceback: {traceback_str}")
        
        # Categorize error
        category = self._categorize_error(error, error_message)
        severity = self._determine_severity(error, category)
        
        # Generate user-friendly message and solutions
        user_message, solutions = self._generate_user_message_and_solutions(
            error_message, category, context
        )
        
        return ErrorInfo(
            category=category,
            severity=severity,
            user_message=user_message,
            technical_message=error_message,
            solutions=solutions,
            context=context,
            traceback=traceback_str
        )
    
    def _categorize_error(self, error: Exception, error_message: str) -> ErrorCategory:
        """Categorize error based on type and message."""
        error_message_lower = error_message.lower()
        error_type = type(error).__name__
        
        # First check by exception type for more accurate categorization
        if isinstance(error, (ConnectionError, ConnectionRefusedError)) or isinstance(error, TimeoutError):
            return ErrorCategory.NETWORK
        elif isinstance(error, PermissionError):
            return ErrorCategory.PERMISSION
        elif isinstance(error, (FileNotFoundError, FileExistsError, IsADirectoryError)):
            return ErrorCategory.FILESYSTEM
        elif isinstance(error, (ValueError, TypeError)):
            return ErrorCategory.VALIDATION
        elif isinstance(error, (ImportError, ModuleNotFoundError)):
            return ErrorCategory.DEPENDENCY
        
        # Fall back to message-based categorization
        if "connection" in error_message_lower or "network" in error_message_lower:
            return ErrorCategory.NETWORK
        elif "ollama" in error_message_lower or "llm" in error_message_lower or "model" in error_message_lower:
            return ErrorCategory.LLM
        elif "permission" in error_message_lower or "access denied" in error_message_lower:
            return ErrorCategory.PERMISSION
        elif "file" in error_message_lower or "directory" in error_message_lower:
            return ErrorCategory.FILESYSTEM
        elif "validation" in error_message_lower or "invalid" in error_message_lower:
            return ErrorCategory.VALIDATION
        elif "module" in error_message_lower or "import" in error_message_lower:
            return ErrorCategory.DEPENDENCY
        elif "config" in error_message_lower or "setting" in error_message_lower:
            return ErrorCategory.CONFIGURATION
        else:
            return ErrorCategory.UNKNOWN
    
    def _determine_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity."""
        if category in [ErrorCategory.PERMISSION, ErrorCategory.DEPENDENCY]:
            return ErrorSeverity.CRITICAL
        elif category in [ErrorCategory.LLM, ErrorCategory.CONFIGURATION, ErrorCategory.NETWORK]:
            return ErrorSeverity.HIGH
        elif category in [ErrorCategory.FILESYSTEM, ErrorCategory.VALIDATION]:
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    def _generate_user_message_and_solutions(
        self, error_message: str, category: ErrorCategory, context: dict[str, Any]
    ) -> tuple[str, list[ErrorSolution]]:
        """Generate user-friendly message and solutions."""
        error_message_lower = error_message.lower()
        
        # Connection issues
        if "connection refused" in error_message_lower:
            return (
                "❌ Impossible de se connecter à Ollama. Le service n'est probablement pas démarré.",
                self._error_solutions.get("connection_refused", [])
            )
        elif "ollama" in error_message_lower and ("not reachable" in error_message_lower or "unreachable" in error_message_lower):
            return (
                "❌ Ollama n'est pas accessible. Vérifiez que le service fonctionne.",
                self._error_solutions.get("connection_refused", [])
            )
        
        # Model not found
        elif "model" in error_message_lower and "not found" in error_message_lower:
            return (
                "❌ Le modèle LLM requis n'est pas disponible. Veuillez télécharger les modèles nécessaires.",
                self._error_solutions.get("model_not_found", [])
            )
        
        # Permission issues
        elif "permission" in error_message_lower or "access denied" in error_message_lower:
            return (
                "❌ Permissions insuffisantes pour accéder aux fichiers ou dossiers nécessaires.",
                self._error_solutions.get("permission_denied", [])
            )
        
        # Timeout issues
        elif "timeout" in error_message_lower or "timed out" in error_message_lower:
            return (
                "⏱️ L'opération a pris trop de temps. Essayez d'optimiser les paramètres.",
                self._error_solutions.get("timeout", [])
            )
        
        # Memory issues
        elif "memory" in error_message_lower:
            return (
                "💾 Mémoire insuffisante pour effectuer cette opération.",
                self._error_solutions.get("memory_error", [])
            )
        
        # Validation issues
        elif "validation" in error_message_lower or "invalid" in error_message_lower:
            return (
                "⚠️ Les données fournies ne sont pas valides. Veuillez vérifier vos entrées.",
                self._error_solutions.get("validation_error", [])
            )
        
        # Default messages by category
        category_messages = {
            ErrorCategory.NETWORK: "🌐 Problème de connexion réseau. Vérifiez votre connexion internet.",
            ErrorCategory.LLM: "🤖 Problème avec le service LLM. Vérifiez qu'Ollama fonctionne correctement.",
            ErrorCategory.FILESYSTEM: "📁 Problème d'accès aux fichiers. Vérifiez les permissions et l'espace disque.",
            ErrorCategory.DEPENDENCY: "📦 Dépendance manquante. Vérifiez que tous les packages sont installés.",
            ErrorCategory.CONFIGURATION: "⚙️ Problème de configuration. Vérifiez votre fichier .env.",
        }
        
        default_message = category_messages.get(category, "❌ Une erreur inattendue est survenue.")
        
        return default_message, []
    
    def format_for_ui(self, error_info: ErrorInfo) -> dict[str, Any]:
        """Format error information for UI display."""
        return {
            "severity": error_info.severity.value,
            "category": error_info.category.value,
            "user_message": error_info.user_message,
            "solutions": [
                {
                    "title": sol.title,
                    "description": sol.description,
                    "steps": sol.steps,
                    "auto_fixable": sol.auto_fixable,
                    "fix_command": sol.fix_command
                }
                for sol in error_info.solutions
            ],
            "context": error_info.context,
            "show_details": error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]
        }


# Global error handler instance
_global_error_handler = ErrorHandler()


def handle_error(error: Exception, context: dict[str, Any] | None = None) -> ErrorInfo:
    """Handle an error using the global error handler."""
    return _global_error_handler.handle_error(error, context)


def format_error_for_ui(error_info: ErrorInfo) -> dict[str, Any]:
    """Format error information for UI display."""
    return _global_error_handler.format_for_ui(error_info)
