
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
