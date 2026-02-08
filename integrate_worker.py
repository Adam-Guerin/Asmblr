
# Ajouter en haut du fichier worker.py
try:
    from app.core.error_handler_v2 import get_error_handler, handle_errors
    from app.core.smart_logger import get_smart_logger, LogCategory, LogLevel
    ERROR_HANDLER = get_error_handler()
    SMART_LOGGER = get_smart_logger()
except ImportError as e:
    print(f"Erreur import systèmes améliorés: {e}")
    ERROR_HANDLER = None
    SMART_LOGGER = None

# Remplacer les fonctions de logging
def log_with_context(message, level="info", category="worker", metadata=None):
    """Logging avec contexte si disponible"""
    if SMART_LOGGER:
        if level == "info":
            SMART_LOGGER.info(LogCategory.WORKER, category, message, **(metadata or {}))
        elif level == "error":
            SMART_LOGGER.error(LogCategory.WORKER, category, message, **(metadata or {}))
        elif level == "debug":
            SMART_LOGGER.debug(LogCategory.WORKER, category, message, **(metadata or {}))
    else:
        print(f"[{level.upper()}] {message}")
    else:
        print(f"[{level.upper()}] {message}")

# Remplacer la gestion d'erreurs
def handle_error_with_context(error, operation="unknown"):
    """Gestion d'erreurs avec contexte si disponible"""
    if ERROR_HANDLER:
        return ERROR_HANDLER.handle_exception(error, operation)
    else:
        print(f"Error in {operation}: {str(error)}")
        return None
