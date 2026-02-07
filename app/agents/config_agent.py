"""
Agent de configuration spécialisé pour Asmblr
Gère dynamiquement les paramètres selon le contexte et les performances
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from loguru import logger

try:
    from crewai import Agent, Task, Crew
except Exception:
    Agent = None
    Task = None
    Crew = None

from app.core.llm import LLMClient
from app.core.agent_config import DynamicConfigManager


@dataclass
class ConfigOptimization:
    """Résultat d'optimisation de configuration"""
    parameter: str
    old_value: Any
    new_value: Any
    reasoning: str
    expected_impact: str
    confidence: float  # 0-1


class ConfigAnalysisAgent:
    """
    Agent qui analyse les besoins et détermine la configuration optimale
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        if Agent:
            self.crew_agent = Agent(
                role="Expert en Configuration Asmblr",
                goal="Optimiser les paramètres d'Asmblr pour maximiser la qualité et la performance",
                backstory="""Tu es un expert expert en configuration de systèmes d'IA. 
                Tu comprends parfaitement comment Asmblr fonctionne et tu sais ajuster 
                chaque paramètre pour obtenir les meilleurs résultats selon le contexte.""",
                verbose=True,
                allow_delegation=False
            )
        else:
            self.crew_agent = None
    
    def analyze_topic_complexity(self, topic: str) -> Dict[str, Any]:
        """
        Analyse la complexité d'un sujet pour déterminer la configuration appropriée
        
        Args:
            topic: Sujet à analyser
            
        Returns:
            Analyse de complexité avec recommandations
        """
        complexity_prompt = f"""
        Analyse la complexité de ce sujet et recommande une configuration Asmblr.

        SUJET: {topic}

        Évalue sur 3 axes (1-10):
        1. Complexité technique (1=basique, 10=très technique)
        2. Spécificité marché (1=général, 10=niche très spécifique)  
        3. Disponibilité données (1=données abondantes, 10=données rares)

        Recommande ensuite:
        - execution_mode: validation_sprint/standard/deep
        - n_ideas: nombre d'idées à générer
        - max_sources: nombre de sources à analyser
        - market_signal_threshold: seuil de signal marché (30-70)
        - signal_quality_threshold: seuil de qualité (40-80)

        Retourne JSON formaté.
        """
        
        try:
            response = self.llm.generate_json(complexity_prompt)
            
            # Validation et normalisation
            analysis = self._validate_complexity_analysis(response)
            
            logger.info(f"Analyse complexité pour '{topic}': {analysis}")
            return analysis
            
        except Exception as e:
            logger.error(f"Erreur analyse complexité: {e}")
            return self._get_default_analysis()
    
    def _validate_complexity_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Valide et normalise l'analyse de complexité"""
        validated = {}
        
        # Scores de complexité
        for score in ["technical_complexity", "market_specificity", "data_availability"]:
            validated[score] = max(1, min(analysis.get(score, 5), 10))
        
        # Configuration recommandée
        config = analysis.get("recommended_config", {})
        validated["recommended_config"] = {
            "execution_mode": config.get("execution_mode", "standard"),
            "n_ideas": max(1, min(config.get("n_ideas", 10), 30)),
            "max_sources": max(3, min(config.get("max_sources", 8), 20)),
            "market_signal_threshold": max(30, min(config.get("market_signal_threshold", 45), 70)),
            "signal_quality_threshold": max(40, min(config.get("signal_quality_threshold", 50), 80))
        }
        
        validated["reasoning"] = analysis.get("reasoning", "Analyse automatique")
        
        return validated
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """Analyse par défaut en cas d'erreur"""
        return {
            "technical_complexity": 5,
            "market_specificity": 5,
            "data_availability": 5,
            "recommended_config": {
                "execution_mode": "standard",
                "n_ideas": 10,
                "max_sources": 8,
                "market_signal_threshold": 45,
                "signal_quality_threshold": 50
            },
            "reasoning": "Configuration par défaut (erreur analyse)"
        }


class PerformanceOptimizationAgent:
    """
    Agent qui optimise les paramètres basé sur les performances passées
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        if Agent:
            self.crew_agent = Agent(
                role="Expert en Optimisation de Performance",
                goal="Améliorer les performances d'Asmblr par ajustement intelligent des paramètres",
                backstory="""Tu es un spécialiste de l'optimisation de systèmes. 
                Tu analyses les métriques de performance et tu ajustes les paramètres 
                pour trouver le meilleur équilibre entre vitesse, qualité et fiabilité.""",
                verbose=True,
                allow_delegation=False
            )
        else:
            self.crew_agent = None
    
    def analyze_performance_issues(self, performance_data: Dict[str, Any]) -> List[ConfigOptimization]:
        """
        Analyse les problèmes de performance et suggère des optimisations
        
        Args:
            performance_data: Données de performance (temps, erreurs, etc.)
            
        Returns:
            Liste d'optimisations recommandées
        """
        optimization_prompt = f"""
        Analyse ces performances d'Asmblr et suggère des optimisations de configuration.

        DONNÉES PERFORMANCE: {performance_data}

        Indicateurs disponibles:
        - execution_time_seconds: temps total d'exécution
        - error_rate: taux d'erreur (0-1)  
        - success_rate: taux de succès (0-1)
        - memory_usage_mb: mémoire utilisée
        - cpu_usage_percent: utilisation CPU
        - network_requests_count: nombre de requêtes réseau

        Paramètres ajustables:
        - max_sources: nombre de sources (3-20)
        - request_timeout: timeout requêtes (10-300s)
        - retry_max_attempts: tentatives retry (1-10)
        - market_signal_threshold: seuil signal (30-70)
        - signal_quality_threshold: seuil qualité (40-80)

        Pour chaque optimisation, indique:
        - parameter: nom du paramètre
        - old_value: valeur actuelle
        - new_value: valeur recommandée
        - reasoning: pourquoi ce changement
        - expected_impact: impact attendu
        - confidence: niveau de confiance (0-1)

        Retourne une liste d'optimisations en JSON.
        """
        
        try:
            response = self.llm.generate_json(optimization_prompt)
            optimizations = []
            
            for opt_data in response.get("optimizations", []):
                optimization = ConfigOptimization(
                    parameter=opt_data.get("parameter", ""),
                    old_value=opt_data.get("old_value"),
                    new_value=opt_data.get("new_value"),
                    reasoning=opt_data.get("reasoning", ""),
                    expected_impact=opt_data.get("expected_impact", ""),
                    confidence=max(0, min(opt_data.get("confidence", 0.5), 1.0))
                )
                
                if self._validate_optimization(optimization):
                    optimizations.append(optimization)
            
            logger.info(f"Généré {len(optimizations)} optimisations de performance")
            return optimizations
            
        except Exception as e:
            logger.error(f"Erreur analyse performance: {e}")
            return []
    
    def _validate_optimization(self, optimization: ConfigOptimization) -> bool:
        """Valide qu'une optimisation est cohérente"""
        if not optimization.parameter or optimization.new_value is None:
            return False
        
        # Validation selon le paramètre
        validations = {
            "max_sources": lambda v: isinstance(v, int) and 3 <= v <= 20,
            "request_timeout": lambda v: isinstance(v, int) and 10 <= v <= 300,
            "retry_max_attempts": lambda v: isinstance(v, int) and 1 <= v <= 10,
            "market_signal_threshold": lambda v: isinstance(v, int) and 30 <= v <= 70,
            "signal_quality_threshold": lambda v: isinstance(v, int) and 40 <= v <= 80
        }
        
        validator = validations.get(optimization.parameter)
        return validator(optimization.new_value) if validator else False


class UserProfileAgent:
    """
    Agent qui adapte la configuration au profil utilisateur
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        if Agent:
            self.crew_agent = Agent(
                role="Expert en Expérience Utilisateur",
                goal="Personnaliser Asmblr selon le profil et les préférences de l'utilisateur",
                backstory="""Tu comprends parfaitement les différents types d'utilisateurs 
                d'Asmblr, des débutants aux experts. Tu sais adapter la configuration 
                pour offrir la meilleure expérience possible à chaque profil.""",
                verbose=True,
                allow_delegation=False
            )
        else:
            self.crew_agent = None
    
    def adapt_to_user_profile(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adapte la configuration selon le profil utilisateur
        
        Args:
            user_data: Informations sur l'utilisateur (expérience, domaine, etc.)
            
        Returns:
            Configuration adaptée au profil
        """
        profile_prompt = f"""
        Adapte la configuration d'Asmblr à ce profil utilisateur.

        PROFIL UTILISATEUR: {user_data}

        Champs possibles dans le profil:
        - experience_level: beginner/intermediate/expert
        - technical_background: low/medium/high
        - domain: domaine d'expertise (tech/marketing/finance/etc.)
        - preferred_mode: validation_sprint/standard/deep
        - time_constraint: low/medium/high
        - quality_requirement: low/medium/high

        Adapte ces paramètres:
        - execution_mode: mode recommandé
        - fast_mode: activer ou non
        - n_ideas: nombre d'idées approprié
        - max_sources: nombre de sources adapté
        - auto_optimization: activer l'optimisation auto
        - guidance_level: niveau de guidance (minimal/standard/detailed)

        Retourne la configuration adaptée en JSON avec explications.
        """
        
        try:
            response = self.llm.generate_json(profile_prompt)
            adapted_config = self._validate_adapted_config(response)
            
            logger.info(f"Configuration adaptée au profil: {adapted_config}")
            return adapted_config
            
        except Exception as e:
            logger.error(f"Erreur adaptation profil: {e}")
            return self._get_default_profile_config()
    
    def _validate_adapted_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Valide et normalise la configuration adaptée"""
        validated = {}
        
        validated["execution_mode"] = config.get("execution_mode", "standard")
        validated["fast_mode"] = config.get("fast_mode", False)
        validated["n_ideas"] = max(1, min(config.get("n_ideas", 10), 20))
        validated["max_sources"] = max(3, min(config.get("max_sources", 8), 15))
        validated["auto_optimization"] = config.get("auto_optimization", True)
        validated["guidance_level"] = config.get("guidance_level", "standard")
        
        validated["reasoning"] = config.get("reasoning", "Adaptation automatique")
        
        return validated
    
    def _get_default_profile_config(self) -> Dict[str, Any]:
        """Configuration par défaut pour profil"""
        return {
            "execution_mode": "standard",
            "fast_mode": False,
            "n_ideas": 10,
            "max_sources": 8,
            "auto_optimization": True,
            "guidance_level": "standard",
            "reasoning": "Configuration par défaut (erreur adaptation)"
        }


class ConfigCrewManager:
    """
    Gestionnaire qui orchestre tous les agents de configuration
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.analysis_agent = ConfigAnalysisAgent(llm_client)
        self.performance_agent = PerformanceOptimizationAgent(llm_client)
        self.profile_agent = UserProfileAgent(llm_client)
        self.config_manager = DynamicConfigManager(llm_client)
        
        # Créer l'équipage CrewAI si disponible
        if Agent and Task and Crew:
            self.crew = self._create_crew()
        else:
            self.crew = None
    
    def _create_crew(self) -> Optional[Crew]:
        """Crée l'équipage CrewAI pour la configuration"""
        try:
            tasks = [
                Task(
                    description="Analyser la complexité du sujet et recommander la configuration de base",
                    agent=self.analysis_agent.crew_agent,
                    expected_output="Configuration de base recommandée avec analyse de complexité"
                ),
                Task(
                    description="Adapter la configuration au profil utilisateur",
                    agent=self.profile_agent.crew_agent,
                    expected_output="Configuration personnalisée selon le profil"
                ),
                Task(
                    description="Optimiser la configuration pour les performances",
                    agent=self.performance_agent.crew_agent,
                    expected_output="Configuration finale optimisée"
                )
            ]
            
            crew = Crew(
                agents=[
                    self.analysis_agent.crew_agent,
                    self.profile_agent.crew_agent,
                    self.performance_agent.crew_agent
                ],
                tasks=tasks,
                verbose=True
            )
            
            return crew
            
        except Exception as e:
            logger.error(f"Erreur création crew configuration: {e}")
            return None
    
    def generate_optimal_config(self, topic: str, user_profile: Optional[Dict] = None,
                              performance_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Génère la configuration optimale en combinant tous les agents
        
        Args:
            topic: Sujet à analyser
            user_profile: Profil utilisateur optionnel
            performance_data: Données de performance optionnelles
            
        Returns:
            Configuration optimale avec méta-données
        """
        logger.info(f"Génération configuration optimale pour: {topic}")
        
        # 1. Analyse de complexité
        complexity_analysis = self.analysis_agent.analyze_topic_complexity(topic)
        
        # 2. Adaptation profil utilisateur
        user_config = {}
        if user_profile:
            user_config = self.profile_agent.adapt_to_user_profile(user_profile)
        
        # 3. Optimisation performance
        performance_optimizations = []
        if performance_data:
            performance_optimizations = self.performance_agent.analyze_performance_issues(performance_data)
        
        # 4. Fusion des configurations
        final_config = self._merge_configurations(
            complexity_analysis.get("recommended_config", {}),
            user_config,
            performance_optimizations
        )
        
        # 5. Application via le gestionnaire
        agent_config = self.config_manager.get_config_for_topic(topic, user_profile)
        
        result = {
            "topic": topic,
            "final_config": final_config,
            "complexity_analysis": complexity_analysis,
            "user_adaptation": user_config,
            "performance_optimizations": [
                {
                    "parameter": opt.parameter,
                    "change": f"{opt.old_value} → {opt.new_value}",
                    "reasoning": opt.reasoning,
                    "confidence": opt.confidence
                }
                for opt in performance_optimizations
            ],
            "agent_config": agent_config,
            "generated_at": self._get_timestamp()
        }
        
        logger.info(f"Configuration optimale générée avec {len(performance_optimizations)} optimisations")
        return result
    
    def _merge_configurations(self, base_config: Dict, user_config: Dict, 
                            optimizations: List) -> Dict[str, Any]:
        """Fusionne intelligemment les différentes configurations"""
        merged = base_config.copy()
        
        # Priorité: configuration utilisateur > base
        for key, value in user_config.items():
            if key != "reasoning":  # Éviter d'écraser avec des méta-données
                merged[key] = value
        
        # Appliquer les optimisations de performance
        for opt in optimizations:
            if hasattr(opt, 'parameter') and opt.parameter in merged:
                merged[opt.parameter] = opt.new_value
        
        return merged
    
    def _get_timestamp(self) -> str:
        """Génère un timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
