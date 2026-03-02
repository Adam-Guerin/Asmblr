"""
Intégration de la configuration intelligente dans le pipeline existant
Permet une migration transparente vers la configuration pilotée par agents
"""

import os
from typing import Any
from pathlib import Path
from loguru import logger

from app.core.smart_config import get_smart_config, configure_for_topic


class SmartConfigIntegration:
    """
    Gère l'intégration de la configuration intelligente dans les systèmes existants
    """
    
    def __init__(self, enable_smart_config: bool | None = None):
        # Déterminer si la configuration intelligente est activée
        if enable_smart_config is None:
            enable_smart_config = os.getenv('AGENT_AUTO_CONFIG', 'true').lower() == 'true'
        
        self.enabled = enable_smart_config
        self.smart_config = None
        
        if self.enabled:
            try:
                self.smart_config = get_smart_config()
                logger.info("Configuration intelligente initialisée")
            except Exception as e:
                logger.error(f"Erreur initialisation configuration intelligente: {e}")
                self.enabled = False
                logger.info("Utilisation configuration standard")
    
    def get_config_for_run(self, topic: str, user_profile: dict | None = None,
                          performance_data: dict | None = None) -> dict[str, str]:
        """
        Récupère la configuration pour une exécution
        
        Args:
            topic: Sujet de l'exécution
            user_profile: Profil utilisateur
            performance_data: Données de performance
            
        Returns:
            Configuration complète
        """
        if not self.enabled:
            logger.info("Configuration intelligente désactivée, utilisation variables d'environnement")
            return dict(os.environ)
        
        logger.info(f"Génération configuration intelligente pour: {topic}")
        return self.smart_config.configure_for_topic(topic, user_profile, performance_data)
    
    def apply_config_to_environment(self, config: dict[str, str]) -> None:
        """
        Applique la configuration à l'environnement
        
        Args:
            config: Configuration à appliquer
        """
        for key, value in config.items():
            if value:  # Ne pas écraser avec des valeurs vides
                os.environ[key] = value
        
        logger.info(f"Configuration appliquée: {len(config)} variables")
    
    def get_config_summary(self) -> dict[str, Any]:
        """Retourne un résumé de la configuration actuelle"""
        if not self.enabled:
            return {"smart_config_enabled": False}
        
        return self.smart_config.get_config_summary()


def patch_config_module():
    """
    Patch le module de configuration existant pour utiliser la configuration intelligente
    """
    try:
        # Importer le module de configuration existant
        from app.core import config
        
        # Sauvegarder les fonctions originales
        original_get_setting = getattr(config, 'get_setting', None)
        original_get_env = getattr(config, 'get_env', None)
        
        def smart_get_setting(setting_name: str, default: Any = None) -> Any:
            """Version intelligente de get_setting"""
            # Essayer d'abord la configuration intelligente
            smart_config = get_smart_config()
            if smart_config:
                value = smart_config.current_config.get(setting_name.upper())
                if value is not None:
                    return value
            
            # Fallback sur l'original
            if original_get_setting:
                return original_get_setting(setting_name, default)
            
            # Fallback sur l'environnement
            return os.getenv(setting_name.upper(), default)
        
        def smart_get_env(var_name: str, default: str = '') -> str:
            """Version intelligente de get_env"""
            # Essayer d'abord la configuration intelligente
            smart_config = get_smart_config()
            if smart_config:
                value = smart_config.current_config.get(var_name)
                if value is not None:
                    return value
            
            # Fallback sur l'environnement
            return os.getenv(var_name, default)
        
        # Patch les fonctions
        config.get_setting = smart_get_setting
        config.get_env = smart_get_env
        
        logger.info("Module de configuration patché avec succès")
        
    except ImportError as e:
        logger.warning(f"Impossible de patcher le module config: {e}")
    except Exception as e:
        logger.error(f"Erreur lors du patch du module config: {e}")


def integrate_with_pipeline():
    """
    Intègre la configuration intelligente dans le pipeline principal
    """
    try:
        # Importer le pipeline
        from app.core import pipeline
        
        # Sauvegarder la méthode originale
        original_run = getattr(pipeline, 'run_pipeline', None)
        
        def smart_run_pipeline(topic: str, **kwargs) -> Any:
            """Version intelligente du pipeline"""
            # Extraire les données de profil et performance
            user_profile = kwargs.pop('user_profile', None)
            performance_data = kwargs.pop('performance_data', None)
            
            # Générer la configuration
            config = configure_for_topic(topic, user_profile, performance_data)
            
            # Appliquer la configuration
            integration = SmartConfigIntegration()
            integration.apply_config_to_environment(config)
            
            # Exécuter le pipeline original
            if original_run:
                return original_run(topic, **kwargs)
            else:
                logger.error("Pipeline original non trouvé")
                return None
        
        # Patch la méthode
        pipeline.run_pipeline = smart_run_pipeline
        
        logger.info("Pipeline intégré avec configuration intelligente")
        
    except ImportError as e:
        logger.warning(f"Impossible d'intégrer avec le pipeline: {e}")
    except Exception as e:
        logger.error(f"Erreur lors de l'intégration pipeline: {e}")


def setup_smart_config_integration():
    """
    Configure l'intégration complète de la configuration intelligente
    """
    logger.info("Initialisation intégration configuration intelligente")
    
    # Vérifier si la configuration intelligente est activée
    if os.getenv('AGENT_AUTO_CONFIG', 'true').lower() != 'true':
        logger.info("Configuration intelligente désactivée via AGENT_AUTO_CONFIG")
        return
    
    try:
        # Initialiser l'intégration
        integration = SmartConfigIntegration()
        
        # Patch les modules existants
        patch_config_module()
        integrate_with_pipeline()
        
        # Afficher le résumé
        summary = integration.get_config_summary()
        logger.info(f"Configuration intelligente active: {summary}")
        
        return integration
        
    except Exception as e:
        logger.error(f"Erreur initialisation intégration: {e}")
        return None


# Fonction utilitaire pour une migration facile
def migrate_to_smart_config():
    """
    Fonction utilitaire pour migrer facilement vers la configuration intelligente
    
    Usage:
        from app.core.integration_smart_config import migrate_to_smart_config
        migrate_to_smart_config()
    """
    logger.info("Début migration vers configuration intelligente")
    
    # 1. Créer un backup de la configuration actuelle
    env_file = Path('.env')
    if env_file.exists():
        backup_file = Path('.env.backup')
        env_file.rename(backup_file)
        logger.info(f"Configuration existante sauvegardée: {backup_file}")
    
    # 2. Copier le template simplifié
    template_file = Path('configs/env.simple.template')
    if template_file.exists():
        import shutil
        shutil.copy(template_file, env_file)
        logger.info("Template de configuration simplifiée copié")
    
    # 3. Initialiser l'intégration
    integration = setup_smart_config_integration()
    
    if integration:
        logger.info("Migration vers configuration intelligente réussie")
        logger.info("Les agents géreront désormais automatiquement la configuration")
    else:
        logger.error("Échec de la migration")
    
    return integration


# Auto-initialisation au démarrage
def auto_initialize():
    """Initialise automatiquement la configuration intelligente si activée"""
    if os.getenv('AGENT_AUTO_CONFIG', 'true').lower() == 'true':
        setup_smart_config_integration()


# L'initialisation se fera au premier import
auto_initialize()
