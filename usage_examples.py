
# Exemples d'utilisation des améliorations Asmblr

## 1. ErrorHandlerV2
```python
from app.core.error_handler_v2 import get_error_handler, handle_errors, NetworkException

error_handler = get_error_handler()

@handle_errors("api_call", reraise=True)
def make_api_call():
    try:
        # Votre logique d'appel API
        if network_error:
            raise NetworkException(
                message="Service inaccessible",
                operation="api_call",
                metadata={"service": "external_api", "timeout": 30}
            )
        return result
    except Exception as e:
        # Géré automatiquement par le décorateur
        return None
```

## 2. SmartLogger
```python
from app.core.smart_logger import get_smart_logger, LogCategory, LogLevel

smart_logger = get_smart_logger()

# Logging intelligent (pas de bruit)
smart_logger.business(
    LogLevel.MEDIUM,
    "user_action", 
    "Utilisateur connecté",
    metadata={"user_id": 123, "ip": "192.168.1.1"}
)

# Logging de debugging (filtré automatiquement)
smart_logger.debug(
    LogCategory.SYSTEM,
    "cache_operation",
    "Opération cache terminée",
    metadata={"operation": "get", "key": "user_123"}
)
```

## 3. RetryManager
```python
from app.core.retry_manager import get_retry_manager, retry_web_request, retry_llm_call

retry_manager = get_retry_manager()

# Appel web avec retry automatique
response = retry_manager.retry_web_request(
    url="https://api.example.com/data",
    method="POST",
    data={"key": "value"},
    max_retries=3
)

# Appel LLM avec retry automatique
response = retry_manager.retry_llm_call(
    prompt="Générer une idée pour AI compliance",
    model="llama3.1:8b",
    max_retries=2
)
```

## 4. SmartConfig
```python
from app.core.smart_config import SmartConfig

smart_config = SmartConfig()

# Configuration dynamique optimisée par les agents
config = smart_config.configure_for_topic(
    topic="AI compliance for SMBs",
    user_profile={"industry": "tech", "size": "startup"},
    performance_data={"avg_response_time": 2.5}
)

print(f"Configuration optimisée: {config}")
```

## 5. Intégration dans le code existant
```python
# Dans app/worker.py
from app.core.error_handler_v2 import get_error_handler
from app.core.smart_logger import get_smart_logger

# Remplacer les imports et logger existants
ERROR_HANDLER = get_error_handler()
SMART_LOGGER = get_smart_logger()

# Utiliser les nouvelles fonctions
@handle_errors("worker_task")
def process_task(task):
    SMART_LOGGER.business(
        LogLevel.MEDIUM,
        "task_processing",
        f"Traitement de la tâche: {task.id}",
        metadata={"task_type": task.type}
    )
    # Votre logique de traitement
    return result
```
