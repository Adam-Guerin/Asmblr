"""
Configuration dynamique pilotée par agents
Les agents ajustent automatiquement les paramètres selon le contexte
"""

import json
from dataclasses import dataclass, asdict
from typing import Any
from pathlib import Path
from loguru import logger

from app.core.llm import LLMClient


@dataclass
class AgentConfig:
    """Configuration dynamique gérée par les agents"""
    
    # Configuration de base (non-modifiable par agents)
    ollama_base_url: str = "http://localhost:11434"
    general_model: str = "llama3.1:8b"
    code_model: str = "qwen2.5-coder:7b"
    
    # Pipeline dynamique
    n_ideas: int = 10
    max_sources: int = 12
    request_timeout: int = 45
    retry_max_attempts: int = 5
    
    # Seuils de signal dynamiques
    market_signal_threshold: int = 45
    signal_quality_threshold: int = 50
    signal_sources_target: int = 6
    signal_pains_target: int = 8
    
    # Configuration MVP dynamique
    mvp_force_autofix: bool = True
    mvp_disable_llm: bool = False
    
    # Mode d'exécution
    execution_mode: str = "standard"  # validation_sprint, standard, deep
    fast_mode: bool = False


class ConfigurationAgent:
    """
    Agent spécialisé dans la configuration dynamique d'Asmblr
    Analyse le contexte et ajuste les paramètres pour optimiser les résultats
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.config_history: list[dict[str, Any]] = []
        
    def analyze_context(self, topic: str, user_profile: dict | None = None) -> dict[str, Any]:
        """
        Analyse le contexte pour déterminer la configuration optimale
        
        Args:
            topic: Le sujet de l'analyse
            user_profile: Profil utilisateur (expérience, domaine, etc.)
            
        Returns:
            Dictionnaire de configuration optimisée
        """
        context_prompt = f"""
        En tant qu'expert en configuration d'Asmblr, analyse ce contexte et propose une configuration optimale.

        SUJET: {topic}
        PROFIL UTILISATEUR: {user_profile or 'Non spécifié'}

        Directives:
        1. Pour les sujets techniques/B2B: plus de sources, seuils plus élevés
        2. Pour les sujets grand public: moins de sources, validation rapide
        3. Pour les premiers utilisateurs: mode validation sprint
        4. Pour les utilisateurs expérimentés: configuration complète

        Retourne un JSON avec:
        {{
            "execution_mode": "validation_sprint|standard|deep",
            "n_ideas": nombre_idees,
            "max_sources": nombre_sources,
            "market_signal_threshold": seuil_signal,
            "signal_quality_threshold": seuil_qualite,
            "fast_mode": true/false,
            "reasoning": "explication des choix"
        }}
        """
        
        try:
            response = self.llm.generate_json(context_prompt)
            config = response.get("configuration", {})
            
            # Validation et normalisation
            normalized_config = self._normalize_config(config)
            
            # Sauvegarde dans l'historique
            self.config_history.append({
                "topic": topic,
                "config": normalized_config,
                "reasoning": config.get("reasoning", ""),
                "timestamp": self._get_timestamp()
            })
            
            logger.info(f"Configuration générée pour '{topic}': {normalized_config}")
            return normalized_config
            
        except Exception as e:
            logger.error(f"Erreur génération configuration: {e}")
            return self._get_default_config()
    
    def _normalize_config(self, config: dict[str, Any]) -> dict[str, Any]:
        """Normalise et valide la configuration"""
        normalized = {}
        
        # Execution mode
        mode = config.get("execution_mode", "standard")
        if mode not in ["validation_sprint", "standard", "deep"]:
            mode = "standard"
        normalized["execution_mode"] = mode
        
        # N idées selon mode
        if mode == "validation_sprint":
            normalized["n_ideas"] = 1
        elif mode == "deep":
            normalized["n_ideas"] = min(config.get("n_ideas", 20), 30)
        else:
            normalized["n_ideas"] = min(config.get("n_ideas", 10), 15)
        
        # Sources selon complexité
        normalized["max_sources"] = min(config.get("max_sources", 8), 20)
        
        # Seuils de signal
        normalized["market_signal_threshold"] = max(30, min(config.get("market_signal_threshold", 45), 70))
        normalized["signal_quality_threshold"] = max(40, min(config.get("signal_quality_threshold", 50), 80))
        
        # Fast mode
        normalized["fast_mode"] = config.get("fast_mode", mode == "validation_sprint")
        
        return normalized
    
    def _get_default_config(self) -> dict[str, Any]:
        """Configuration par défaut sécurisée"""
        return {
            "execution_mode": "standard",
            "n_ideas": 10,
            "max_sources": 8,
            "market_signal_threshold": 45,
            "signal_quality_threshold": 50,
            "fast_mode": False,
            "reasoning": "Configuration par défaut suite à erreur"
        }
    
    def _get_timestamp(self) -> str:
        """Génère un timestamp pour l'historique"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def optimize_for_performance(self, current_config: dict[str, Any], 
                               performance_metrics: dict[str, float]) -> dict[str, Any]:
        """
        Ajuste la configuration en fonction des métriques de performance
        
        Args:
            current_config: Configuration actuelle
            performance_metrics: Métriques (temps_exécution, taux_erreur, etc.)
            
        Returns:
            Configuration optimisée
        """
        optimization_prompt = f"""
        En tant qu'expert en optimisation d'Asmblr, analyse ces performances et propose des ajustements.

        CONFIGURATION ACTUELLE: {current_config}
        MÉTRIQUES DE PERFORMANCE: {performance_metrics}

        Métriques disponibles:
        - execution_time_seconds: temps d'exécution total
        - error_rate: taux d'erreur (0-1)
        - success_rate: taux de succès (0-1)
        - resource_usage: utilisation ressources (0-1)

        Retourne un JSON avec:
        {{
            "adjustments": {{
                "max_sources": nouvelle_valeur,
                "request_timeout": nouvelle_valeur,
                "retry_max_attempts": nouvelle_valeur,
                "market_signal_threshold": nouvelle_valeur
            }},
            "reasoning": "explication des ajustements",
            "expected_impact": "impact attendu sur les performances"
        }}
        """
        
        try:
            response = self.llm.generate_json(optimization_prompt)
            adjustments = response.get("adjustments", {})
            
            # Appliquer les ajustements avec validation
            optimized_config = current_config.copy()
            for key, value in adjustments.items():
                if key in optimized_config and self._validate_adjustment(key, value):
                    optimized_config[key] = value
            
            logger.info(f"Configuration optimisée: {adjustments}")
            return optimized_config
            
        except Exception as e:
            logger.error(f"Erreur optimisation configuration: {e}")
            return current_config
    
    def _validate_adjustment(self, key: str, value: Any) -> bool:
        """Valide qu'un ajustement est cohérent"""
        validations = {
            "max_sources": lambda v: isinstance(v, int) and 1 <= v <= 50,
            "request_timeout": lambda v: isinstance(v, int) and 10 <= v <= 300,
            "retry_max_attempts": lambda v: isinstance(v, int) and 1 <= v <= 10,
            "market_signal_threshold": lambda v: isinstance(v, int) and 20 <= v <= 80,
            "signal_quality_threshold": lambda v: isinstance(v, int) and 30 <= v <= 90
        }
        
        return validations.get(key, lambda v: False)(value)
    
    def save_config_history(self, file_path: Path) -> None:
        """Sauvegarde l'historique des configurations"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config_history, f, indent=2, ensure_ascii=False)
            logger.info(f"Historique configuration sauvegardé: {file_path}")
        except Exception as e:
            logger.error(f"Erreur sauvegarde historique: {e}")


class DynamicConfigManager:
    """
    Gestionnaire principal de configuration dynamique
    Interface entre les agents et le reste de l'application
    """
    
    def __init__(self, llm_client: LLMClient, config_dir: Path = None):
        self.agent = ConfigurationAgent(llm_client)
        self.config_dir = config_dir or Path("configs")
        self.config_dir.mkdir(exist_ok=True)
        self.current_config = AgentConfig()
        
    def get_config_for_topic(self, topic: str, user_profile: dict | None = None) -> AgentConfig:
        """
        Génère et retourne la configuration optimale pour un sujet donné
        
        Args:
            topic: Sujet à analyser
            user_profile: Profil utilisateur optionnel
            
        Returns:
            Configuration optimisée
        """
        # Analyse du contexte par l'agent
        dynamic_config = self.agent.analyze_context(topic, user_profile)
        
        # Mise à jour de la configuration
        config_dict = asdict(self.current_config)
        config_dict.update(dynamic_config)
        
        # Création de la nouvelle configuration
        self.current_config = AgentConfig(**config_dict)
        
        # Sauvegarde pour audit
        self._save_current_config(topic)
        
        return self.current_config
    
    def optimize_performance(self, performance_metrics: dict[str, float]) -> AgentConfig:
        """Optimise la configuration basée sur les performances"""
        current_dict = asdict(self.current_config)
        optimized_dict = self.agent.optimize_for_performance(current_dict, performance_metrics)
        
        self.current_config = AgentConfig(**optimized_dict)
        return self.current_config
    
    def _save_current_config(self, topic: str) -> None:
        """Sauvegarde la configuration actuelle avec le contexte"""
        config_file = self.config_dir / f"config_{topic.replace(' ', '_')[:20]}.json"
        
        try:
            config_data = {
                "topic": topic,
                "config": asdict(self.current_config),
                "timestamp": self.agent._get_timestamp()
            }
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Erreur sauvegarde configuration: {e}")
    
    def get_env_vars(self) -> dict[str, str]:
        """
        Génère les variables d'environnement à partir de la configuration actuelle
        Compatible avec le système existant
        """
        return {
            "OLLAMA_BASE_URL": self.current_config.ollama_base_url,
            "GENERAL_MODEL": self.current_config.general_model,
            "CODE_MODEL": self.current_config.code_model,
            "DEFAULT_N_IDEAS": str(self.current_config.n_ideas),
            "MAX_SOURCES": str(self.current_config.max_sources),
            "REQUEST_TIMEOUT": str(self.current_config.request_timeout),
            "RETRY_MAX_ATTEMPTS": str(self.current_config.retry_max_attempts),
            "MARKET_SIGNAL_THRESHOLD": str(self.current_config.market_signal_threshold),
            "SIGNAL_QUALITY_THRESHOLD": str(self.current_config.signal_quality_threshold),
            "FAST_MODE": str(self.current_config.fast_mode).lower(),
            "MVP_FORCE_AUTOFIX": str(self.current_config.mvp_force_autofix).lower(),
            "MVP_DISABLE_LLM": str(self.current_config.mvp_disable_llm).lower(),
        }
