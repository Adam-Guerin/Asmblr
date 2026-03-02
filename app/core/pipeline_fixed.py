"""
Pipeline principal d'Asmblr - Version corrigée
Corrections des TODO critiques et gestion d'erreurs unifiée
"""

from datetime import datetime, UTC
from typing import Any

from app.core.config import Settings, validate_secrets
from app.core.models import RunResult
from app.core.llm import check_ollama
from app.agents.crew import run_crewai_pipeline
from app.core.prerun_gate import PreRunGate
from app.eval.confidence import compute_confidence
from app.signal_engine import SignalEngine
from app.core.thresholds import (
    IDEA_ACTIONABILITY_MIN_SCORE,
    IDEA_ACTIONABILITY_ADJUSTMENT_MAX,
    TOPIC_MIN_LENGTH,
    TOPIC_MAX_LENGTH,
)

# Importer les systèmes améliorés
from app.core.error_handler_v2 import get_error_handler, handle_errors, NetworkException, LLMException
from app.core.smart_logger import get_smart_logger, LogLevel
from app.core.retry_manager import get_retry_manager, retry_web_request, retry_llm_call


class AsmblrPipelineFixed:
    """
    Pipeline principal d'Asmblr - Version avec corrections critiques
    Résout les TODO et gestion d'erreurs unifiée
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.error_handler = get_error_handler()
        self.smart_logger = get_smart_logger()
        self.retry_manager = get_retry_manager()
        
        # Validation des prérequis
        self._validate_prerequisites()
    
    def _validate_prerequisites(self) -> None:
        """Valide les prérequis pour le pipeline"""
        try:
            # Valider les secrets
            validate_secrets(self.settings)
            
            # Vérifier Ollama
            check_ollama(self.settings.ollama_base_url, [
                self.settings.general_model,
                self.settings.code_model
            ])
            
            self.smart_logger.system(
                LogLevel.LOW,
                "pipeline_init",
                "Prérequis validés avec succès"
            )
            
        except Exception as e:
            self.error_handler.handle_exception(e, "pipeline_validation")
            raise
    
    @handle_errors("pipeline_run", reraise=True)
    def run(self, topic: str, **kwargs) -> RunResult:
        """
        Exécute le pipeline principal avec gestion d'erreurs unifiée
        
        Args:
            topic: Sujet à analyser
            **kwargs: Paramètres additionnels
            
        Returns:
            Résultat de l'exécution
        """
        self.smart_logger.start_operation("pipeline_run", metadata={"topic": topic})
        
        try:
            # Validation du sujet
            self._validate_topic(topic)
            
            # Exécution des étapes
            result = self._execute_pipeline_stages(topic, **kwargs)
            
            self.smart_logger.end_operation("pipeline_run", success=True)
            return result
            
        except Exception as e:
            self.smart_logger.end_operation("pipeline_run", success=False)
            raise
    
    def _validate_topic(self, topic: str) -> None:
        """Valide le sujet d'entrée"""
        if not topic or not topic.strip():
            raise ValidationException(
                "Le sujet ne peut pas être vide",
                operation="topic_validation"
            )
        
        topic = topic.strip()
        
        if len(topic) < TOPIC_MIN_LENGTH:
            raise ValidationException(
                f"Le sujet doit contenir au moins {TOPIC_MIN_LENGTH} caractères",
                operation="topic_validation"
            )
        
        if len(topic) > TOPIC_MAX_LENGTH:
            raise ValidationException(
                f"Le sujet ne peut pas dépasser {TOPIC_MAX_LENGTH} caractères",
                operation="topic_validation"
            )
        
        # Vérifier les valeurs manquantes/invalides
        if self._text_missing_or_invalid(topic):
            raise ValidationException(
                "Le sujet contient des valeurs invalides (unknown, n/a, etc.)",
                operation="topic_validation"
            )
        
        self.smart_logger.business(
            LogLevel.MEDIUM,
            "topic_validated",
            f"Sujet validé: {topic[:50]}..."
        )
    
    def _text_missing_or_invalid(self, value: Any) -> bool:
        """
        Vérifie si le texte contient des valeurs manquantes ou invalides
        Version corrigée du TODO original
        """
        if not value:
            return True
        
        text = str(value).strip().lower()
        invalid_values = {
            "", "unknown", "n/a", "none", "null", "tbd", "todo",
            "undefined", "missing", "not applicable", "na"
        }
        
        return text in invalid_values
    
    @handle_errors("pipeline_stages", reraise=True)
    def _execute_pipeline_stages(self, topic: str, **kwargs) -> RunResult:
        """Exécute les étapes du pipeline avec retry automatique"""
        
        # Étape 1: Pré-run gate
        self.smart_logger.start_operation("prerun_gate")
        prerun_result = self._execute_prerun_gate(topic, **kwargs)
        self.smart_logger.end_operation("prerun_gate", success=True)
        
        # Étape 2: Signal processing
        self.smart_logger.start_operation("signal_processing")
        signal_result = self._execute_signal_processing(topic, prerun_result, **kwargs)
        self.smart_logger.end_operation("signal_processing", success=True)
        
        # Étape 3: Génération d'idées
        self.smart_logger.start_operation("idea_generation")
        idea_result = self._execute_idea_generation(topic, signal_result, **kwargs)
        self.smart_logger.end_operation("idea_generation", success=True)
        
        # Étape 4: Analyse d'actionabilité
        self.smart_logger.start_operation("actionability_analysis")
        actionability_result = self._execute_actionability_analysis(idea_result, **kwargs)
        self.smart_logger.end_operation("actionability_analysis", success=True)
        
        # Étape 5: Génération d'artefacts
        self.smart_logger.start_operation("artifact_generation")
        artifact_result = self._execute_artifact_generation(topic, actionability_result, **kwargs)
        self.smart_logger.end_operation("artifact_generation", success=True)
        
        # Construire le résultat final
        return RunResult(
            topic=topic,
            status="completed",
            prerun_result=prerun_result,
            signal_result=signal_result,
            idea_result=idea_result,
            actionability_result=actionability_result,
            artifact_result=artifact_result,
            confidence_score=self._compute_confidence(artifact_result),
            timestamp=datetime.now(UTC).isoformat()
        )
    
    @retry_web_request("prerun_gate")
    def _execute_prerun_gate(self, topic: str, **kwargs) -> dict:
        """Exécute la porte de pré-run avec retry automatique"""
        try:
            gate = PreRunGate(self.settings)
            return gate.validate_and_process(topic, **kwargs)
        except Exception as e:
            raise NetworkException(
                f"Erreur lors du pré-run gate: {str(e)}",
                operation="prerun_gate",
                metadata={"topic": topic[:50]}
            )
    
    @retry_web_request("signal_processing")
    def _execute_signal_processing(self, topic: str, prerun_result: dict, **kwargs) -> dict:
        """Exécute le traitement des signaux avec retry automatique"""
        try:
            engine = SignalEngine(self.settings)
            return engine.process_signals(topic, prerun_result, **kwargs)
        except Exception as e:
            raise NetworkException(
                f"Erreur lors du traitement des signaux: {str(e)}",
                operation="signal_processing",
                metadata={"topic": topic[:50]}
            )
    
    @retry_llm_call("idea_generation")
    def _execute_idea_generation(self, topic: str, signal_result: dict, **kwargs) -> dict:
        """Exécute la génération d'idées avec retry automatique"""
        try:
            # Utiliser CrewAI pour générer les idées
            return run_crewai_pipeline(
                topic=topic,
                signal_data=signal_result,
                stage="idea_generation",
                settings=self.settings,
                **kwargs
            )
        except Exception as e:
            raise LLMException(
                f"Erreur lors de la génération d'idées: {str(e)}",
                operation="idea_generation",
                metadata={"topic": topic[:50]}
            )
    
    def _execute_actionability_analysis(self, idea_result: dict, **kwargs) -> dict:
        """Analyse l'actionabilité des idées avec logging amélioré"""
        try:
            ideas = idea_result.get("ideas", [])
            threshold = kwargs.get("actionability_threshold", IDEA_ACTIONABILITY_MIN_SCORE)
            
            assessments = {}
            adjusted_scores = {}
            eligible = []
            blocked = []
            
            for idea in ideas:
                assessment = self._assess_idea_actionability(idea)
                assessments[idea.get("name", "unknown")] = assessment
                
                # Ajuster le score
                adjusted_score = self._adjust_idea_score(assessment["score"], threshold)
                adjusted_scores[idea.get("name", "unknown")] = adjusted_score
                
                if adjusted_score >= threshold:
                    eligible.append(idea.get("name", "unknown"))
                else:
                    blocked.append(idea.get("name", "unknown"))
            
            # Logging intelligent (remplace le TODO)
            if len(assessments) > 0:
                avg_actionability = sum(a.get("score", 0) for a in assessments.values()) / len(assessments)
                
                self.smart_logger.business(
                    LogLevel.MEDIUM,
                    "actionability_assessment",
                    f"Analyse d'actionabilité terminée: {len(eligible)}/{len(ideas)} idées éligibles",
                    metadata={
                        "threshold": threshold,
                        "avg_score": avg_actionability,
                        "eligible_count": len(eligible),
                        "blocked_count": len(blocked)
                    }
                )
                
                # Logging des idées bloquées (remplace le TODO)
                if blocked:
                    blocked_details = [
                        f"{name}({assessments.get(name, {}).get('score', 0)})"
                        for name in blocked
                        if name in assessments
                    ]
                    
                    self.smart_logger.business(
                        LogLevel.LOW,
                        "blocked_ideas",
                        f"Idées bloquées par le seuil d'actionabilité: {', '.join(blocked_details)}",
                        metadata={
                            "blocked_ideas": blocked_details,
                            "threshold": threshold
                        }
                    )
            
            return {
                "assessments": assessments,
                "adjusted_scores": adjusted_scores,
                "eligible": eligible,
                "blocked": blocked,
                "threshold": threshold
            }
            
        except Exception as e:
            self.error_handler.handle_exception(e, "actionability_analysis")
            raise
    
    def _assess_idea_actionability(self, idea: dict) -> dict:
        """Évalue l'actionabilité d'une idée"""
        score = 50
        signals = {"issues": [], "strengths": []}
        
        # Vérifier les phrases génériques
        generic_phrases = (
            "save time", "improve efficiency", "increase productivity",
            "streamline workflow", "all-in-one", "for everyone",
            "any business", "one-click", "revolutionary", "game-changing"
        )
        
        idea_text = f"{idea.get('name', '')} {idea.get('description', '')}".lower()
        
        for phrase in generic_phrases:
            if phrase in idea_text:
                score -= 5
                signals["issues"].append(f"Phrase générique: {phrase}")
        
        # Vérifier la spécificité
        if len(idea.get('description', '')) < 50:
            score -= 10
            signals["issues"].append("Description trop courte")
        
        # Vérifier la faisabilité technique
        if self._is_technically_feasible(idea):
            score += 10
            signals["strengths"].append("Faisable techniquement")
        
        return {
            "score": max(0, min(100, score)),
            "signals": signals,
            "assessment": "actionable" if score >= 50 else "not_actionable"
        }
    
    def _is_technically_feasible(self, idea: dict) -> bool:
        """Vérifie si une idée est techniquement réalisable"""
        # Logique simplifiée pour la faisabilité
        description = idea.get('description', '').lower()
        
        # Indicateurs de faisabilité
        feasible_indicators = [
            "api", "database", "web", "mobile", "app", "software",
            "platform", "service", "tool", "system", "automation"
        ]
        
        return any(indicator in description for indicator in feasible_indicators)
    
    def _adjust_idea_score(self, score: float, threshold: float) -> float:
        """Ajuste le score d'une idée selon le seuil"""
        if score >= threshold:
            return score
        
        # Ajustement progressif
        adjustment = min(IDEA_ACTIONABILITY_ADJUSTMENT_MAX, threshold - score)
        return score + adjustment
    
    @retry_llm_call("artifact_generation")
    def _execute_artifact_generation(self, topic: str, actionability_result: dict, **kwargs) -> dict:
        """Génère les artefacts finaux avec retry automatique"""
        try:
            # Utiliser CrewAI pour générer les artefacts
            return run_crewai_pipeline(
                topic=topic,
                actionability_data=actionability_result,
                stage="artifact_generation",
                settings=self.settings,
                **kwargs
            )
        except Exception as e:
            raise LLMException(
                f"Erreur lors de la génération d'artefacts: {str(e)}",
                operation="artifact_generation",
                metadata={"topic": topic[:50]}
            )
    
    def _compute_confidence(self, artifact_result: dict) -> float:
        """Calcule le score de confiance"""
        try:
            return compute_confidence(artifact_result)
        except Exception as e:
            self.smart_logger.error(
                "confidence_computation",
                f"Erreur calcul confiance: {str(e)}"
            )
            return 50.0  # Valeur par défaut
    
    def get_pipeline_status(self) -> dict:
        """Retourne le statut actuel du pipeline"""
        return {
            "status": "ready",
            "error_count": len(self.error_handler.error_history),
            "last_error": self.error_handler.error_history[-1].to_context() if self.error_handler.error_history else None,
            "log_summary": self.smart_logger.get_log_summary(hours=1)
        }


# Fonction utilitaire pour créer le pipeline corrigé
def create_fixed_pipeline(settings: Settings) -> AsmblrPipelineFixed:
    """
    Crée une instance du pipeline corrigé
    
    Args:
        settings: Configuration de l'application
        
    Returns:
        Instance du pipeline avec corrections appliquées
    """
    return AsmblrPipelineFixed(settings)


# Point d'entrée principal corrigé
@handle_errors("main_pipeline_entry", reraise=True)
def run_fixed_pipeline(topic: str, **kwargs) -> RunResult:
    """
    Point d'entrée principal pour le pipeline corrigé
    
    Args:
        topic: Sujet à analyser
        **kwargs: Paramètres additionnels
        
    Returns:
        Résultat de l'exécution du pipeline
    """
    settings = Settings()
    pipeline = create_fixed_pipeline(settings)
    
    return pipeline.run(topic, **kwargs)
