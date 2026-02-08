"""
Corrections critiques pour pipeline.py
Résout les TODO et problèmes de gestion d'erreurs identifiés
"""

from typing import Any, Dict, List
from loguru import logger

# Importer les systèmes améliorés
from app.core.error_handler_v2 import get_error_handler, handle_errors, ValidationException
from app.core.smart_logger import get_smart_logger, LogCategory, LogLevel


def fix_text_missing_or_unknown_check():
    """
    Corrige la fonction _text_missing_or_unknown du pipeline
    Version améliorée qui gère les cas limites
    """
    def _text_missing_or_unknown_fixed(value: Any) -> bool:
        """
        Vérifie si le texte est manquant ou inconnu
        Version corrigée du TODO avec validation améliorée
        """
        if value is None:
            return True
        
        if not isinstance(value, str):
            value = str(value)
        
        text = value.strip().lower()
        
        # Liste étendue de valeurs invalides
        invalid_values = {
            "", "unknown", "n/a", "none", "null", "tbd", "todo",
            "undefined", "missing", "not applicable", "na",
            "n.d.", "nd", "null", "nil", "void"
        }
        
        return text in invalid_values
    
    return _text_missing_or_unknown_fixed


def fix_actionability_logging():
    """
    Corrige le logging de l'analyse d'actionabilité
    Version améliorée qui utilise le logging intelligent
    """
    smart_logger = get_smart_logger()
    
    def log_actionability_assessment(assessments: Dict[str, Any], 
                                  threshold: float,
                                  eligible: List[str],
                                  blocked: List[str]) -> None:
        """
        Log intelligent de l'évaluation d'actionabilité
        Remplace le TODO par un logging structuré
        """
        if len(assessments) > 0:
            avg_actionability = sum(a.get("score", 0) for a in assessments.values()) / len(assessments)
            
            # Log principal avec métadonnées structurées
            smart_logger.business(
                LogLevel.MEDIUM,
                "actionability_assessment",
                f"Analyse d'actionabilité terminée: {len(eligible)}/{len(assessments)} idées éligibles",
                metadata={
                    "threshold": threshold,
                    "avg_score": avg_actionability,
                    "eligible_count": len(eligible),
                    "blocked_count": len(blocked),
                    "total_assessed": len(assessments)
                }
            )
            
            # Log détaillé des idées bloquées (si nécessaire)
            if blocked and len(blocked) > 0:
                blocked_details = [
                    f"{name}({assessments.get(name, {}).get('score', 0)})"
                    for name in blocked
                    if name in assessments
                ]
                
                smart_logger.business(
                    LogLevel.LOW,
                    "blocked_ideas",
                    f"Idées bloquées par le seuil d'actionabilité",
                    metadata={
                        "blocked_ideas": blocked_details,
                        "threshold": threshold,
                        "blocked_count": len(blocked)
                    }
                )
    
    return log_actionability_assessment


def fix_pipeline_error_handling():
    """
    Corrige la gestion d'erreurs dans le pipeline
    Version unifiée avec le système d'erreurs
    """
    error_handler = get_error_handler()
    smart_logger = get_smart_logger()
    
    @handle_errors("pipeline_stage", reraise=True)
    def execute_pipeline_stage(stage_name: str, stage_func, *args, **kwargs):
        """
        Exécute une étape du pipeline avec gestion d'erreurs unifiée
        """
        try:
            smart_logger.start_operation(f"pipeline_{stage_name}")
            result = stage_func(*args, **kwargs)
            smart_logger.end_operation(f"pipeline_{stage_name}", success=True)
            return result
            
        except ValidationException as e:
            smart_logger.end_operation(f"pipeline_{stage_name}", success=False)
            # Relancer avec le contexte enrichi
            raise
        
        except Exception as e:
            smart_logger.end_operation(f"pipeline_{stage_name}", success=False)
            # Gérer avec le gestionnaire d'erreurs
            context = error_handler.handle_exception(e, f"pipeline_{stage_name}")
            raise
    
    return execute_pipeline_stage


def fix_generic_phrase_detection():
    """
    Corrige la détection de phrases génériques
    Version améliorée avec plus de patterns et validation
    """
    def _detect_generic_phrases_fixed(text: str) -> List[str]:
        """
        Détecte les phrases génériques dans un texte
        Version améliorée avec plus de patterns
        """
        if not text or not isinstance(text, str):
            return []
        
        text_lower = text.lower()
        
        # Patterns étendus de phrases génériques
        generic_patterns = [
            "save time", "improve efficiency", "increase productivity",
            "streamline workflow", "all-in-one", "for everyone",
            "any business", "one-click", "revolutionary", "game-changing",
            "disruptive", "innovative", "breakthrough", "next-generation",
            "state-of-the-art", "cutting-edge", "industry-leading",
            "world-class", "best-in-class", "unparalleled", "ultimate",
            "comprehensive", "complete solution", "end-to-end",
            "turnkey", "out-of-the-box", "plug-and-play", "seamless",
            "integrated", "unified", "centralized", "automated",
            "smart", "intelligent", "AI-powered", "machine learning",
            "artificial intelligence", "blockchain", "cloud-based",
            "future-proof", "scalable", "enterprise-grade"
        ]
        
        detected_phrases = []
        for pattern in generic_patterns:
            if pattern in text_lower:
                detected_phrases.append(pattern)
        
        return detected_phrases
    
    return _detect_generic_phrases_fixed


def create_pipeline_improvements():
    """
    Crée un dictionnaire des améliorations du pipeline
    """
    return {
        "text_validation": fix_text_missing_or_unknown_check(),
        "actionability_logging": fix_actionability_logging(),
        "error_handling": fix_pipeline_error_handling(),
        "generic_phrase_detection": fix_generic_phrase_detection(),
        
        "recommendations": [
            "Remplacer les TODO par des issues dans le suivi de projet",
            "Utiliser le logging intelligent pour réduire le bruit",
            "Appliquer la gestion d'erreurs unifiée",
            "Valider les entrées avec des fonctions dédiées",
            "Documenter les décisions métier",
            "Ajouter des tests pour les cas limites"
        ],
        
        "migration_steps": [
            "1. Analyser les TODO existants dans pipeline.py",
            "2. Créer des issues GitHub pour chaque TODO",
            "3. Remplacer les logs debug par le smart_logger",
            "4. Appliquer les décorateurs handle_errors",
            "5. Ajouter la validation des entrées",
            "6. Écrire des tests pour les nouvelles fonctions"
        ]
    }


# Fonction utilitaire pour appliquer les corrections
def apply_pipeline_fixes():
    """
    Applique les corrections critiques au pipeline
    """
    improvements = create_pipeline_improvements()
    
    logger.info("🔧 Corrections critiques du pipeline prêtes")
    logger.info(f"📋 {len(improvements['recommendations'])} recommandations")
    
    return improvements


if __name__ == "__main__":
    # Démonstration des corrections
    improvements = apply_pipeline_fixes()
    
    logger.info("=== Corrections critiques du pipeline ===")
    logger.info("\n📋 Recommandations:")
    for i, rec in enumerate(improvements['recommendations'], 1):
        logger.info(f"{i}. {rec}")
    
    logger.info("\n🔄 Étapes de migration:")
    for i, step in enumerate(improvements['migration_steps'], 1):
        logger.info(f"{i}. {step}")
