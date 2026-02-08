
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
