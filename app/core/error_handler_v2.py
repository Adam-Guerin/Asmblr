"""
Gestionnaire d'erreurs unifié et intelligent
Remplace la gestion hétérogène des erreurs dans tout Asmblr
"""

import sys
import traceback
import functools
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from loguru import logger

T = TypeVar('T')


class ErrorSeverity(Enum):
    """Sévérité des erreurs"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Catégories d'erreurs"""
    NETWORK = "network"
    LLM = "llm"
    FILE_IO = "file_io"
    DATABASE = "database"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    EXTERNAL_API = "external_api"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"


@dataclass
class ErrorContext:
    """Contexte d'erreur enrichi"""
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    operation: str
    user_message: str
    technical_message: str
    retry_recommended: bool
    suggestions: List[str]
    metadata: Dict[str, Any]
    timestamp: str
    stack_trace: Optional[str] = None


class AsmblrException(Exception):
    """
    Exception de base pour toute l'application Asmblr
    Remplace les exceptions génériques par des exceptions structurées
    """
    
    def __init__(self, 
                 message: str,
                 category: ErrorCategory = ErrorCategory.SYSTEM,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 operation: str = "unknown",
                 retry_recommended: bool = False,
                 suggestions: Optional[List[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.category = category
        self.severity = severity
        self.operation = operation
        self.retry_recommended = retry_recommended
        self.suggestions = suggestions or []
        self.metadata = metadata or {}
        self.error_id = self._generate_error_id()
    
    def _generate_error_id(self) -> str:
        """Génère un ID unique pour l'erreur"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def to_context(self) -> ErrorContext:
        """Convertit l'exception en contexte d'erreur"""
        return ErrorContext(
            error_id=self.error_id,
            category=self.category,
            severity=self.severity,
            operation=self.operation,
            user_message=str(self),
            technical_message=self.__class__.__name__ + ": " + str(self),
            retry_recommended=self.retry_recommended,
            suggestions=self.suggestions,
            metadata=self.metadata,
            timestamp=self._get_timestamp(),
            stack_trace=traceback.format_exc()
        )
    
    def _get_timestamp(self) -> str:
        """Génère un timestamp ISO"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()


# Exceptions spécialisées par catégorie
class NetworkException(AsmblrException):
    """Exception pour les erreurs réseau"""
    
    def __init__(self, message: str, operation: str = "network_operation", **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            operation=operation,
            retry_recommended=True,
            suggestions=[
                "Vérifiez votre connexion internet",
                "Vérifiez que le service distant est accessible",
                "Essayez de nouveau dans quelques instants"
            ],
            **kwargs
        )


class LLMException(AsmblrException):
    """Exception pour les erreurs LLM"""
    
    def __init__(self, message: str, operation: str = "llm_operation", **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.LLM,
            severity=ErrorSeverity.HIGH,
            operation=operation,
            retry_recommended=True,
            suggestions=[
                "Vérifiez qu'Ollama est en cours d'exécution",
                "Vérifiez que les modèles sont téléchargés",
                "Essayez avec un modèle plus petit"
            ],
            **kwargs
        )


class FileIOException(AsmblrException):
    """Exception pour les erreurs d'E/S fichier"""
    
    def __init__(self, message: str, operation: str = "file_operation", **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.FILE_IO,
            severity=ErrorSeverity.MEDIUM,
            operation=operation,
            retry_recommended=False,
            suggestions=[
                "Vérifiez les permissions du fichier",
                "Vérifiez que l'espace disque est suffisant",
                "Vérifiez que le chemin du fichier est correct"
            ],
            **kwargs
        )


class ValidationException(AsmblrException):
    """Exception pour les erreurs de validation"""
    
    def __init__(self, message: str, operation: str = "validation", **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            operation=operation,
            retry_recommended=False,
            suggestions=[
                "Vérifiez les données fournies",
                "Consultez la documentation pour le format attendu",
                "Contactez le support si le problème persiste"
            ],
            **kwargs
        )


class ConfigurationException(AsmblrException):
    """Exception pour les erreurs de configuration"""
    
    def __init__(self, message: str, operation: str = "configuration", **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            operation=operation,
            retry_recommended=False,
            suggestions=[
                "Vérifiez votre fichier .env",
                "Consultez le guide de configuration",
                "Utilisez la configuration intelligente"
            ],
            **kwargs
        )


class BusinessLogicException(AsmblrException):
    """Exception pour les erreurs de logique métier"""
    
    def __init__(self, message: str, operation: str = "business_logic", **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.BUSINESS_LOGIC,
            severity=ErrorSeverity.MEDIUM,
            operation=operation,
            retry_recommended=False,
            suggestions=[
                "Vérifiez les prérequis pour cette opération",
                "Consultez la documentation du workflow",
                "Essayez avec des paramètres différents"
            ],
            **kwargs
        )


class ErrorHandlerV2:
    """
    Gestionnaire d'erreurs unifié et intelligent
    Centralise la gestion des erreurs et fournit des recommandations
    """
    
    def __init__(self, enable_smart_logging: bool = True):
        self.enable_smart_logging = enable_smart_logging
        self.error_history: List[ErrorContext] = []
        self.error_patterns = self._load_error_patterns()
        self.recovery_strategies = self._load_recovery_strategies()
    
    def handle_exception(self, 
                        exception: Exception, 
                        operation: str = "unknown",
                        context: Optional[Dict[str, Any]] = None) -> ErrorContext:
        """
        Gère une exception de manière unifiée
        
        Args:
            exception: L'exception à gérer
            operation: Nom de l'opération
            context: Contexte additionnel
            
        Returns:
            Contexte d'erreur structuré
        """
        # Convertir en AsmblrException si nécessaire
        if not isinstance(exception, AsmblrException):
            asmblr_exception = self._convert_to_asmblr_exception(exception, operation)
        else:
            asmblr_exception = exception
        
        # Créer le contexte
        error_context = asmblr_exception.to_context()
        
        # Ajouter le contexte additionnel
        if context:
            error_context.metadata.update(context)
        
        # Logger intelligemment
        if self.enable_smart_logging:
            self._log_error(error_context)
        
        # Stocker dans l'historique
        self._store_error(error_context)
        
        # Tenter une récupération automatique
        if error_context.retry_recommended:
            self._attempt_recovery(error_context)
        
        return error_context
    
    def _convert_to_asmblr_exception(self, exception: Exception, operation: str) -> AsmblrException:
        """Convertit une exception générique en AsmblrException"""
        exception_type = type(exception).__name__
        message = str(exception)
        
        # Mapping des exceptions communes
        if "ConnectionError" in exception_type or "timeout" in message.lower():
            return NetworkException(message, operation)
        elif "FileNotFoundError" in exception_type or "PermissionError" in exception_type:
            return FileIOException(message, operation)
        elif "ValueError" in exception_type or "ValidationError" in exception_type:
            return ValidationException(message, operation)
        elif "KeyError" in exception_type or "IndexError" in exception_type:
            return BusinessLogicException(message, operation)
        else:
            return AsmblrException(
                message=message,
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                operation=operation,
                retry_recommended=True
            )
    
    def _log_error(self, error_context: ErrorContext) -> None:
        """Logger intelligemment selon la sévérité"""
        log_data = {
            "error_id": error_context.error_id,
            "category": error_context.category.value,
            "severity": error_context.severity.value,
            "operation": error_context.operation,
            "message": error_context.user_message,
            "retry_recommended": error_context.retry_recommended
        }
        
        # Logger selon la sévérité
        if error_context.severity == ErrorSeverity.CRITICAL:
            logger.critical("Critical error: {log_data}", log_data=log_data)
        elif error_context.severity == ErrorSeverity.HIGH:
            logger.error("High severity error: {log_data}", log_data=log_data)
        elif error_context.severity == ErrorSeverity.MEDIUM:
            logger.warning("Medium severity error: {log_data}", log_data=log_data)
        else:
            logger.info("Low severity error: {log_data}", log_data=log_data)
        
        # Logger le stack trace seulement en mode debug
        if logger.level <= 10:  # DEBUG level
            logger.debug("Stack trace for {error_id}: {stack_trace}", 
                        error_id=error_context.error_id, 
                        stack_trace=error_context.stack_trace)
    
    def _store_error(self, error_context: ErrorContext) -> None:
        """Stocke l'erreur dans l'historique"""
        self.error_history.append(error_context)
        
        # Garder seulement les 1000 dernières erreurs
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]
    
    def _attempt_recovery(self, error_context: ErrorContext) -> None:
        """Tente une récupération automatique"""
        strategy = self.recovery_strategies.get(error_context.category)
        if strategy:
            try:
                strategy(error_context)
                logger.info(f"Auto-recovery attempted for {error_context.error_id}")
            except Exception as e:
                logger.warning(f"Auto-recovery failed for {error_context.error_id}: {e}")
    
    def _load_error_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Charge les patterns d'erreurs connus"""
        return {
            "connection_refused": {
                "category": ErrorCategory.NETWORK,
                "severity": ErrorSeverity.HIGH,
                "suggestions": ["Vérifiez que le service est démarré", "Vérifiez le firewall"]
            },
            "model_not_found": {
                "category": ErrorCategory.LLM,
                "severity": ErrorSeverity.HIGH,
                "suggestions": ["Téléchargez le modèle avec ollama pull", "Vérifiez le nom du modèle"]
            },
            "permission_denied": {
                "category": ErrorCategory.FILE_IO,
                "severity": ErrorSeverity.MEDIUM,
                "suggestions": ["Vérifiez les permissions du fichier", "Exécutez avec les droits appropriés"]
            }
        }
    
    def _load_recovery_strategies(self) -> Dict[ErrorCategory, Callable]:
        """Charge les stratégies de récupération"""
        return {
            ErrorCategory.NETWORK: self._recover_network,
            ErrorCategory.LLM: self._recover_llm,
            ErrorCategory.FILE_IO: self._recover_file_io,
            ErrorCategory.CONFIGURATION: self._recover_configuration
        }
    
    def _recover_network(self, error_context: ErrorContext) -> None:
        """Stratégie de récupération réseau"""
        logger.info("Attempting network recovery...")
        # Implémenter la logique de récupération réseau
        pass
    
    def _recover_llm(self, error_context: ErrorContext) -> None:
        """Stratégie de récupération LLM"""
        logger.info("Attempting LLM recovery...")
        # Implémenter la logique de récupération LLM
        pass
    
    def _recover_file_io(self, error_context: ErrorContext) -> None:
        """Stratégie de récupération fichier"""
        logger.info("Attempting file I/O recovery...")
        # Implémenter la logique de récupération fichier
        pass
    
    def _recover_configuration(self, error_context: ErrorContext) -> None:
        """Stratégie de récupération configuration"""
        logger.info("Attempting configuration recovery...")
        # Implémenter la logique de récupération configuration
        pass
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Retourne un résumé des erreurs récentes"""
        from datetime import datetime, timezone, timedelta
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_errors = [
            e for e in self.error_history 
            if datetime.fromisoformat(e.timestamp) > cutoff_time
        ]
        
        # Compter par catégorie et sévérité
        by_category = {}
        by_severity = {}
        
        for error in recent_errors:
            by_category[error.category.value] = by_category.get(error.category.value, 0) + 1
            by_severity[error.severity.value] = by_severity.get(error.severity.value, 0) + 1
        
        # Top erreurs par opération
        by_operation = {}
        for error in recent_errors:
            by_operation[error.operation] = by_operation.get(error.operation, 0) + 1
        
        return {
            "total_errors": len(recent_errors),
            "timeframe_hours": hours,
            "by_category": by_category,
            "by_severity": by_severity,
            "by_operation": dict(sorted(by_operation.items(), key=lambda x: x[1], reverse=True)[:10]),
            "most_common_suggestions": self._get_common_suggestions(recent_errors)
        }
    
    def _get_common_suggestions(self, errors: List[ErrorContext]) -> List[str]:
        """Retourne les suggestions les plus communes"""
        suggestion_counts = {}
        for error in errors:
            for suggestion in error.suggestions:
                suggestion_counts[suggestion] = suggestion_counts.get(suggestion, 0) + 1
        
        return sorted(
            [(suggestion, count) for suggestion, count in suggestion_counts.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]
    
    def export_errors(self, format_type: str = "json", hours: int = 24) -> str:
        """Exporte les erreurs récentes"""
        from datetime import datetime, timezone, timedelta
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_errors = [
            e for e in self.error_history 
            if datetime.fromisoformat(e.timestamp) > cutoff_time
        ]
        
        if format_type == "json":
            import json
            return json.dumps([asdict(e) for e in recent_errors], indent=2)
        
        elif format_type == "csv":
            import csv
            import io
            
            output = io.StringIO()
            if recent_errors:
                writer = csv.DictWriter(output, fieldnames=asdict(recent_errors[0]).keys())
                writer.writeheader()
                for error in recent_errors:
                    writer.writerow(asdict(error))
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Format non supporté: {format_type}")


# Instance globale du gestionnaire d'erreurs
_error_handler_v2: Optional[ErrorHandlerV2] = None


def get_error_handler() -> ErrorHandlerV2:
    """Récupère l'instance globale du gestionnaire d'erreurs"""
    global _error_handler_v2
    if _error_handler_v2 is None:
        _error_handler_v2 = ErrorHandlerV2()
    return _error_handler_v2


def handle_errors(operation: str = "unknown", 
                reraise: bool = True,
                return_on_error: Any = None):
    """
    Décorateur pour gérer les erreurs de manière unifiée
    
    Args:
        operation: Nom de l'opération
        reraise: Si True, relance l'exception après traitement
        return_on_error: Valeur à retourner si reraise=False
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Union[T, Any]]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Union[T, Any]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler = get_error_handler()
                error_context = error_handler.handle_exception(e, operation)
                
                if reraise:
                    raise e
                else:
                    return return_on_error
        
        return wrapper
    return decorator


def safe_execute(func: Callable[..., T], 
               operation: str = "unknown",
               default: Any = None) -> T:
    """
    Exécute une fonction en toute sécurité avec gestion d'erreurs
    
    Args:
        func: Fonction à exécuter
        operation: Nom de l'opération
        default: Valeur par défaut en cas d'erreur
        
    Returns:
        Résultat de la fonction ou valeur par défaut
    """
    try:
        return func()
    except Exception as e:
        error_handler = get_error_handler()
        error_handler.handle_exception(e, operation)
        return default


# Exceptions pratiques pour les cas courants
def raise_network_error(message: str, operation: str = "network", **kwargs):
    """Lève une erreur réseau standardisée"""
    raise NetworkException(message, operation, **kwargs)


def raise_llm_error(message: str, operation: str = "llm", **kwargs):
    """Lève une erreur LLM standardisée"""
    raise LLMException(message, operation, **kwargs)


def raise_file_error(message: str, operation: str = "file", **kwargs):
    """Lève une erreur fichier standardisée"""
    raise FileIOException(message, operation, **kwargs)


def raise_validation_error(message: str, operation: str = "validation", **kwargs):
    """Lève une erreur validation standardisée"""
    raise ValidationException(message, operation, **kwargs)


def raise_config_error(message: str, operation: str = "config", **kwargs):
    """Lève une erreur configuration standardisée"""
    raise ConfigurationException(message, operation, **kwargs)
