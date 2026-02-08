#!/usr/bin/env python
"""
Script d'intégration des améliorations dans l'application Asmblr existante
Option B: Utiliser immédiatement les améliorations
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime

def log(message, level='INFO'):
    """Logger simple avec timestamps"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {level}: {message}")

def backup_original_files():
    """Crée des backups des fichiers originaux"""
    log("Création des backups des fichiers originaux...")
    
    files_to_backup = [
        'app/worker.py',
        'app/ui.py',
        'app/core/pipeline.py',
        'app/core/cache.py'
    ]
    
    backup_dir = Path('backups')
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    for file_path in files_to_backup:
        if Path(file_path).exists():
            backup_name = f"{Path(file_path).stem}_{timestamp}{Path(file_path).suffix}"
            backup_path = backup_dir / backup_name
            shutil.copy2(file_path, backup_path)
            log(f"Backup créé: {backup_path}")
    
    log(f"Backups créés dans: {backup_dir}")

def integrate_error_handler():
    """Intègre ErrorHandlerV2 dans les fichiers existants"""
    log("Intégration de ErrorHandlerV2...")
    
    # Script d'intégration pour le worker
    worker_integration = '''
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
'''
    
    # Écrire le script d'intégration
    with open('integrate_worker.py', 'w') as f:
        f.write(worker_integration)
    
    log("Script d'intégration worker créé: integrate_worker.py")

def integrate_smart_config():
    """Intègre SmartConfig dans l'application principale"""
    log("Intégration de SmartConfig...")
    
    # Script d'intégration pour la configuration dynamique
    config_integration = '''
# Ajouter dans le fichier principal (ui.py ou main.py)
try:
    from app.core.smart_config import SmartConfig, get_smart_config
    from app.core.agent_config import DynamicConfigManager
    SMART_CONFIG = SmartConfig()
    DYNAMIC_CONFIG = DynamicConfigManager()
except ImportError as e:
    print(f"Erreur import configuration dynamique: {e}")
    SMART_CONFIG = None
    DYNAMIC_CONFIG = None

# Fonction de configuration dynamique
def configure_dynamically(topic, user_profile=None, performance_data=None):
    """Configure dynamiquement un sujet"""
    if SMART_CONFIG:
        return SMART_CONFIG.configure_for_topic(topic, user_profile, performance_data)
    else:
        return {"error": "SmartConfig non disponible"}

# Exemple d'utilisation dans votre code
def example_dynamic_config():
    """Exemple d'utilisation de la configuration dynamique"""
    topic = "AI compliance for SMBs"
    user_profile = {"industry": "tech", "size": "startup"}
    
    config = configure_dynamically(topic, user_profile)
    print(f"Configuration dynamique: {config}")
'''
    
    # Écrire le script d'intégration
    with open('integrate_config.py', 'w') as f:
        f.write(config_integration)
    
    log("Script d'intégration configuration créé: integrate_config.py")

def integrate_retry_manager():
    """Intègre RetryManager pour les appels réseau"""
    log("Intégration de RetryManager...")
    
    # Script d'intégration pour les retries
    retry_integration = '''
# Ajouter dans les fichiers qui font des appels réseau
try:
    from app.core.retry_manager import get_retry_manager, retry_web_request, retry_llm_call
    RETRY_MANAGER = get_retry_manager()
except ImportError as e:
    print(f"Erreur import retry manager: {e}")
    RETRY_MANAGER = None

# Exemple d'utilisation pour les appels web
def make_web_request(url, method="GET", data=None, headers=None):
    """Appel web avec retry automatique"""
    if RETRY_MANAGER:
        return RETRY_MANAGER.retry_web_request(url, method, data, headers)
    else:
        import requests
        return requests.request(method, url, data=data, headers=headers)

# Exemple d'utilisation pour les appels LLM
def make_llm_call(prompt, model=None):
    """Appel LLM avec retry automatique"""
    if RETRY_MANAGER:
        return RETRY_MANAGER.retry_llm_call(prompt, model)
    else:
        # Fallback vers l'implémentation existante
        from app.llm import LLMClient
        client = LLMClient()
        return client.generate(prompt, model=model)
'''
    
    # Écrire le script d'intégration
    with open('integrate_retry.py', 'w') as f:
        f.write(retry_integration)
    
    log("Script d'intégration retry créé: integrate_retry.py")

def create_improved_worker():
    """Crée une version améliorée du worker"""
    log("Création du worker amélioré...")
    
    improved_worker = '''#!/usr/bin/env python
"""
Worker d'Asmblr - Version améliorée avec ErrorHandlerV2 et SmartLogger
"""

import os
import sys
import time
from datetime import datetime

try:
    from app.core.error_handler_v2 import get_error_handler, handle_errors
    from app.core.smart_logger import get_smart_logger, LogCategory, LogLevel
    from app.core.retry_manager import get_retry_manager
    from app.core.config import get_settings
    from app.llm import check_ollama
    from fastapi import HTTPException
    from redis import Redis
    from rq import Worker, Connection
    
    # Initialiser les systèmes améliorés
    ERROR_HANDLER = get_error_handler()
    SMART_LOGGER = get_smart_logger()
    RETRY_MANAGER = get_retry_manager()
    SETTINGS = get_settings()
    
except ImportError as e:
    print(f"Erreur import systèmes améliorés: {e}")
    sys.exit(1)

class ImprovedWorker:
    def __init__(self):
        self.smart_logger = get_smart_logger()
        self.error_handler = get_error_handler()
        self.retry_manager = get_retry_manager()
        
        self.smart_logger.system(
            LogLevel.LOW,
            "worker_init",
            "Worker amélioré initialisé"
        )
    
    @handle_errors("health_check", reraise=False)
    def healthz(self):
        """Health check amélioré"""
        try:
            # Redis avec retry
            redis_conn = self.retry_manager.retry_redis_connection()
            redis_conn.ping()
            
            # Ollama avec retry
            self.retry_manager.retry_ollama_check()
            
            self.smart_logger.info(LogCategory.SYSTEM, "health", "Health check OK")
            return {"status": "ok"}
            
        except Exception as e:
            context = self.error_handler.handle_exception(e, "health_check")
            raise HTTPException(status_code=503, detail=context.to_dict())
    
    @handle_errors("ready_check", reraise=False)
    def readyz(self):
        """Readiness check amélioré"""
        try:
            # Vérifications détaillées
            redis_ok = self.retry_manager.retry_redis_connection().ping()
            ollama_ok = self.retry_manager.retry_ollama_check()
            
            status = "ready" if redis_ok and ollama_ok else "not_ready"
            
            self.smart_logger.info(
                LogCategory.SYSTEM, 
                "readiness", 
                f"Readiness check: {status}"
            )
            
            return {"status": status}
            
        except Exception as e:
            context = self.error_handler.handle_exception(e, "ready_check")
            raise HTTPException(status_code=503, detail=context.to_dict())
    
    def run(self):
        """Exécution du worker amélioré"""
        self.smart_logger.business(
            LogLevel.MEDIUM,
            "worker_start",
            "Démarrage du worker amélioré"
        )
        
        try:
            redis_conn = self.retry_manager.retry_redis_connection()
            with Connection(redis_conn):
                worker = Worker([SETTINGS.rq_queue_name])
                worker.work(with_scheduler=False)
        except Exception as e:
            self.error_handler.handle_exception(e, "worker_run")
            raise

def main():
    """Point d'entrée"""
    worker = ImprovedWorker()
    
    try:
        worker.run()
    except KeyboardInterrupt:
        SMART_LOGGER.business(
            LogLevel.MEDIUM,
            "worker_shutdown",
            "Worker arrêté proprement"
        )
    except Exception as e:
        ERROR_HANDLER.handle_exception(e, "main")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    # Écrire le worker amélioré
    with open('worker_improved.py', 'w') as f:
        f.write(improved_worker)
    
    log("Worker amélioré créé: worker_improved.py")

def create_usage_examples():
    """Crée des exemples d'utilisation des améliorations"""
    log("Création des exemples d'utilisation...")
    
    examples = '''
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
'''
    
    # Écrire les exemples
    with open('usage_examples.py', 'w') as f:
        f.write(examples)
    
    log("Exemples d'utilisation créés: usage_examples.py")

def main():
    """Point d'entrée principal"""
    log("🚀 Intégration des améliorations Asmblr - Option B")
    print("=" * 60)
    
    try:
        # Étape 1: Backup des fichiers originaux
        backup_original_files()
        
        # Étape 2: Créer les scripts d'intégration
        integrate_error_handler()
        integrate_smart_config()
        integrate_retry_manager()
        
        # Étape 3: Créer le worker amélioré
        create_improved_worker()
        
        # Étape 4: Créer les exemples d'utilisation
        create_usage_examples()
        
        print("\n✅ Intégration terminée avec succès !")
        print("\n📁 Fichiers créés:")
        print("  - backups/ (backups des fichiers originaux)")
        print("  - integrate_worker.py (intégration ErrorHandlerV2)")
        print("  - integrate_config.py (intégration SmartConfig)")
        print("  - integrate_retry.py (intégration RetryManager)")
        print("  - worker_improved.py (worker amélioré)")
        print("  - usage_examples.py (exemples d'utilisation)")
        
        print("\n🎯 Prochaines étapes:")
        print("1. Testez le worker amélioré:")
        print("   python worker_improved.py")
        print("2. Intégrez les améliorations dans vos fichiers existants:")
        print("   - Copiez les imports des scripts d'intégration")
        print("   - Remplacez les appels de logging par SMART_LOGGER")
        print("   - Ajoutez les décorateurs @handle_errors")
        print("3. Utilisez les exemples d'utilisation comme référence")
        
        print("\n📊 Améliorations activées:")
        print("  ✅ ErrorHandlerV2: Gestion unifiée des erreurs")
        print("  ✅ SmartLogger: Logging intelligent filtré")
        print("  ✅ RetryManager: Retry automatique intelligent")
        print("  ✅ SmartConfig: Configuration dynamique optimisée")
        
        return True
        
    except Exception as e:
        log(f"Erreur lors de l'intégration: {e}", 'ERROR')
        print(f"\n❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
