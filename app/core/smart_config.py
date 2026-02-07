"""
Configuration intelligente d'Asmblr
Remplace les 365 variables .env par une configuration dynamique pilotée par agents
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger

from app.core.llm import LLMClient
from app.core.agent_config import DynamicConfigManager
from app.agents.config_agent import ConfigCrewManager


class SmartConfig:
    """
    Configuration intelligente qui s'adapte automatiquement
    Remplace la configuration statique par un système dynamique
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.config_manager = DynamicConfigManager(self.llm)
        self.crew_manager = ConfigCrewManager(self.llm)
        
        # Charger la configuration de base
        self.base_config = self._load_base_config()
        
        # Configuration actuelle (sera mise à jour dynamiquement)
        self.current_config = {}
        self._initialize_config()
    
    def _load_base_config(self) -> Dict[str, str]:
        """Charge la configuration de base depuis les variables d'environnement essentielles"""
        essential_vars = [
            'OLLAMA_BASE_URL',
            'GENERAL_MODEL', 
            'CODE_MODEL',
            'REDIS_URL',
            'RUNS_DIR',
            'DATA_DIR',
            'CONFIG_DIR',
            'KNOWLEDGE_DIR',
            'LOG_JSON',
            'AUDIT_LOG_FILE',
            'PROD_MODE',
            'API_KEY',
            'VEO3_API_KEY',
            'GOOGLE_ADS_CLIENT_ID',
            'GOOGLE_ADS_CLIENT_SECRET',
            'META_ADS_ACCESS_TOKEN',
            'LINKEDIN_TOKEN',
            'X_BEARER_TOKEN',
            'AGENT_AUTO_CONFIG'
        ]
        
        config = {}
        for var in essential_vars:
            config[var] = os.getenv(var, '')
        
        return config
    
    def _initialize_config(self) -> None:
        """Initialise la configuration avec les valeurs par défaut"""
        # Configuration par défaut pour les paramètres gérés par agents
        default_dynamic = {
            'DEFAULT_N_IDEAS': '10',
            'MAX_SOURCES': '8',
            'REQUEST_TIMEOUT': '45',
            'RETRY_MAX_ATTEMPTS': '5',
            'MARKET_SIGNAL_THRESHOLD': '45',
            'SIGNAL_QUALITY_THRESHOLD': '50',
            'FAST_MODE': 'false',
            'MVP_FORCE_AUTOFIX': 'true',
            'MVP_DISABLE_LLM': 'false',
            'ENABLE_FACILITATOR_AGENTS': 'false',
            'ENABLE_FEEDBACK_LOOPS': 'false',
            'ENABLE_SHARED_KNOWLEDGE': 'false',
            'ENABLE_PEER_REVIEW': 'false',
            'MLP_ENABLED': 'false',
            'LOVEABILITY_ENABLED': 'false',
            'EMOTIONAL_DESIGN_ENABLED': 'false'
        }
        
        # Fusionner avec la configuration de base
        self.current_config = {**self.base_config, **default_dynamic}
        
        # Vérifier si l'auto-configuration est activée
        if self.current_config.get('AGENT_AUTO_CONFIG', 'true').lower() == 'true':
            logger.info("Configuration intelligente activée")
        else:
            logger.info("Configuration intelligente désactivée - utilisation valeurs par défaut")
    
    def configure_for_topic(self, topic: str, user_profile: Optional[Dict] = None,
                          performance_data: Optional[Dict] = None) -> Dict[str, str]:
        """
        Configure Asmblr dynamiquement pour un sujet donné
        
        Args:
            topic: Sujet à traiter
            user_profile: Profil utilisateur optionnel
            performance_data: Données de performance optionnelles
            
        Returns:
            Configuration complète sous forme de variables d'environnement
        """
        if self.current_config.get('AGENT_AUTO_CONFIG', 'true').lower() != 'true':
            logger.info("Auto-configuration désactivée, utilisation configuration par défaut")
            return self.current_config
        
        logger.info(f"Configuration automatique pour: {topic}")
        
        try:
            # Générer la configuration optimale via les agents
            optimal_config = self.crew_manager.generate_optimal_config(
                topic=topic,
                user_profile=user_profile,
                performance_data=performance_data
            )
            
            # Convertir en variables d'environnement
            env_vars = self._config_to_env_vars(optimal_config)
            
            # Mettre à jour la configuration actuelle
            self.current_config.update(env_vars)
            
            # Sauvegarder la configuration générée
            self._save_generated_config(topic, optimal_config)
            
            logger.info(f"Configuration générée avec {len(optimal_config.get('performance_optimizations', []))} optimisations")
            return self.current_config
            
        except Exception as e:
            logger.error(f"Erreur configuration automatique: {e}")
            logger.info("Utilisation configuration par défaut")
            return self.current_config
    
    def _config_to_env_vars(self, config_data: Dict[str, Any]) -> Dict[str, str]:
        """Convertit la configuration des agents en variables d'environnement"""
        env_vars = {}
        
        # Configuration finale
        final_config = config_data.get('final_config', {})
        
        # Mapping des paramètres vers variables d'environnement
        param_mapping = {
            'execution_mode': 'EXECUTION_MODE',
            'n_ideas': 'DEFAULT_N_IDEAS',
            'max_sources': 'MAX_SOURCES',
            'market_signal_threshold': 'MARKET_SIGNAL_THRESHOLD',
            'signal_quality_threshold': 'SIGNAL_QUALITY_THRESHOLD',
            'fast_mode': 'FAST_MODE',
            'auto_optimization': 'ENABLE_AUTO_OPTIMIZATION',
            'guidance_level': 'GUIDANCE_LEVEL'
        }
        
        # Appliquer le mapping
        for param, env_var in param_mapping.items():
            if param in final_config:
                value = final_config[param]
                if isinstance(value, bool):
                    env_vars[env_var] = str(value).lower()
                else:
                    env_vars[env_var] = str(value)
        
        # Configuration de l'agent ConfigManager
        agent_config = config_data.get('agent_config')
        if agent_config:
            agent_env_vars = self.config_manager.get_env_vars()
            env_vars.update(agent_env_vars)
        
        return env_vars
    
    def _save_generated_config(self, topic: str, config_data: Dict[str, Any]) -> None:
        """Sauvegarde la configuration générée pour audit"""
        try:
            config_dir = Path(self.current_config.get('CONFIG_DIR', 'configs'))
            config_dir.mkdir(exist_ok=True)
            
            # Nom de fichier safe
            safe_topic = topic.replace(' ', '_')[:30]
            config_file = config_dir / f"generated_config_{safe_topic}.json"
            
            import json
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration sauvegardée: {config_file}")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde configuration: {e}")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Retourne un résumé de la configuration actuelle"""
        return {
            "agent_auto_config": self.current_config.get('AGENT_AUTO_CONFIG', 'false') == 'true',
            "current_ideas": self.current_config.get('DEFAULT_N_IDEAS', '10'),
            "current_sources": self.current_config.get('MAX_SOURCES', '8'),
            "signal_threshold": self.current_config.get('MARKET_SIGNAL_THRESHOLD', '45'),
            "fast_mode": self.current_config.get('FAST_MODE', 'false') == 'true',
            "execution_mode": self.current_config.get('EXECUTION_MODE', 'standard'),
            "base_config_vars": len(self.base_config),
            "dynamic_vars": len(self.current_config) - len(self.base_config)
        }
    
    def optimize_performance(self, performance_metrics: Dict[str, float]) -> Dict[str, str]:
        """
        Optimise la configuration basée sur les métriques de performance
        
        Args:
            performance_metrics: Métriques de performance
            
        Returns:
            Configuration optimisée
        """
        if self.current_config.get('AGENT_AUTO_CONFIG', 'true').lower() != 'true':
            return self.current_config
        
        try:
            # Utiliser le gestionnaire pour optimiser
            optimized_config = self.config_manager.optimize_performance(performance_metrics)
            
            # Convertir en variables d'environnement
            env_vars = self.config_manager.get_env_vars()
            
            # Mettre à jour la configuration actuelle
            self.current_config.update(env_vars)
            
            logger.info("Configuration optimisée pour les performances")
            return self.current_config
            
        except Exception as e:
            logger.error(f"Erreur optimisation performance: {e}")
            return self.current_config
    
    def reset_to_defaults(self) -> Dict[str, str]:
        """Réinitialise la configuration aux valeurs par défaut"""
        logger.info("Réinitialisation configuration aux valeurs par défaut")
        self._initialize_config()
        return self.current_config
    
    def export_config(self, format_type: str = "env") -> str:
        """
        Exporte la configuration actuelle dans différents formats
        
        Args:
            format_type: Format d'export (env, json, yaml)
            
        Returns:
            Configuration formatée
        """
        if format_type == "env":
            lines = []
            for key, value in self.current_config.items():
                if value:  # N'inclure que les valeurs non vides
                    lines.append(f"{key}={value}")
            return "\n".join(lines)
        
        elif format_type == "json":
            import json
            return json.dumps(self.current_config, indent=2)
        
        elif format_type == "yaml":
            try:
                import yaml
                return yaml.dump(self.current_config, default_flow_style=False)
            except ImportError:
                logger.warning("PyYAML non disponible, utilisation JSON")
                return self.export_config("json")
        
        else:
            raise ValueError(f"Format non supporté: {format_type}")


# Instance globale de configuration intelligente
_smart_config_instance: Optional[SmartConfig] = None


def get_smart_config(llm_client: Optional[LLMClient] = None) -> SmartConfig:
    """
    Récupère l'instance globale de configuration intelligente
    
    Args:
        llm_client: Client LLM optionnel
        
    Returns:
        Instance de SmartConfig
    """
    global _smart_config_instance
    
    if _smart_config_instance is None:
        _smart_config_instance = SmartConfig(llm_client)
    
    return _smart_config_instance


def configure_for_topic(topic: str, user_profile: Optional[Dict] = None,
                      performance_data: Optional[Dict] = None) -> Dict[str, str]:
    """
    Fonction utilitaire pour configurer Asmblr pour un sujet
    
    Args:
        topic: Sujet à traiter
        user_profile: Profil utilisateur optionnel
        performance_data: Données de performance optionnelles
        
    Returns:
        Configuration complète
    """
    smart_config = get_smart_config()
    return smart_config.configure_for_topic(topic, user_profile, performance_data)


def get_env_var(var_name: str, default: str = '') -> str:
    """
    Récupère une variable d'environnement depuis la configuration intelligente
    
    Args:
        var_name: Nom de la variable
        default: Valeur par défaut
        
    Returns:
        Valeur de la variable
    """
    smart_config = get_smart_config()
    return smart_config.current_config.get(var_name, default)
