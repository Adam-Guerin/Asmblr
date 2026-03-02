"""
Pain Specificity Score - penalize generic pains using rule-based scoring.
"""

from typing import Dict, List, Any, Set
import re

from .base import BaseMetric, MetricResult


class PainSpecificityScore(BaseMetric):
    """Measures how specific and actionable the extracted pains are."""
    
    requires_ground_truth = False
    output_type = "score"
    
    def __init__(self, config: Any):
        super().__init__(config)
        
        # Generic pain indicators
        self.generic_verbs = {
            "is", "are", "has", "have", "need", "want", "should", "could", "would",
            "might", "may", "seems", "appears", "looks", "feels"
        }
        
        self.generic_nouns = {
            "problem", "issue", "challenge", "difficulty", "trouble", "concern",
            "thing", "stuff", "matter", "situation", "case", "scenario"
        }
        
        self.generic_contexts = {
            "general", "overall", "basically", "essentially", "typically",
            "usually", "normally", "commonly", "generally"
        }
        
        # Specificity indicators
        self.specific_verbs = {
            "cannot", "unable", "fails", "crashes", "breaks", "stops",
            "delays", "prevents", "blocks", "requires", "lacks",
            "missing", "incorrect", "inaccurate", "inefficient"
        }
        
        self.specific_nouns = {
            "database", "server", "api", "interface", "workflow", "process",
            "system", "application", "software", "hardware", "network",
            "integration", "automation", "calculation", "validation"
        }
        
        self.specific_contexts = {
            "production", "development", "testing", "deployment", "integration",
            "compliance", "security", "performance", "scalability"
        }
    
    def compute(self, run_result: Dict[str, Any], dataset: List[Dict]) -> MetricResult:
        """Compute pain specificity score."""
        # Extract system pains
        system_pains = self._extract_system_pains(run_result)
        if not system_pains:
            return MetricResult(
                score=0.0,
                explanation="No pains extracted by system",
                evidence={"system_pains_count": 0}
            )
        
        # Calculate specificity scores for each pain
        pain_scores = []
        total_penalties = 0
        total_possible_penalties = 0
        
        for pain in system_pains:
            score, penalties, possible = self._calculate_pain_specificity(pain)
            pain_scores.append(score)
            total_penalties += penalties
            total_possible_penalties += possible
        
        # Overall specificity score
        if total_possible_penalties == 0:
            overall_score = 0.0
        else:
            overall_score = 1.0 - (total_penalties / total_possible_penalties)
        
        # Average individual pain scores
        avg_pain_score = sum(pain_scores) / len(pain_scores) if pain_scores else 0.0
        
        # Final score combines both approaches
        final_score = 0.6 * overall_score + 0.4 * avg_pain_score
        
        explanation = f"Pain specificity: {final_score:.3f} (avg pain score: {avg_pain_score:.3f})"
        
        evidence = {
            "system_pains_count": len(system_pains),
            "overall_specificity": overall_score,
            "avg_pain_specificity": avg_pain_score,
            "total_penalties": total_penalties,
            "total_possible_penalties": total_possible_penalties,
            "pain_specificity_scores": pain_scores
        }
        
        return MetricResult(
            score=final_score,
            explanation=explanation,
            evidence=evidence,
            details={
                "pain_scores": list(zip(range(len(system_pains)), pain_scores)),
                "penalty_breakdown": self._analyze_penalties(system_pains)
            }
        )
    
    def _extract_system_pains(self, run_result: Dict[str, Any]) -> List[Dict]:
        """Extract pains from system output."""
        pains = []
        
        # Try pains_structured.json
        structured_pains = self._extract_artifact(run_result, "pains_structured")
        if structured_pains:
            if isinstance(structured_pains, list):
                pains.extend(structured_pains)
            elif isinstance(structured_pains, dict) and "pains" in structured_pains:
                pains.extend(structured_pains["pains"])
        
        # Try pains_validated.json
        validated_pains = self._extract_artifact(run_result, "pains_validated")
        if validated_pains:
            if isinstance(validated_pains, list):
                pains.extend(validated_pains)
            elif isinstance(validated_pains, dict) and "pains" in validated_pains:
                pains.extend(validated_pains["pains"])
        
        return pains
    
    def _calculate_pain_specificity(self, pain: Dict) -> tuple[float, int, int]:
        """Calculate specificity score for a single pain."""
        problem_text = pain.get("problem", "").lower()
        actor_text = pain.get("actor", "").lower()
        context_text = pain.get("context", "").lower()
        
        penalties = 0
        possible_penalties = 0
        
        # Check for generic verbs
        generic_verb_count = sum(1 for verb in self.generic_verbs if verb in problem_text)
        penalties += generic_verb_count * 2
        possible_penalties += 2
        
        # Check for generic nouns
        generic_noun_count = sum(1 for noun in self.generic_nouns if noun in problem_text)
        penalties += generic_noun_count * 2
        possible_penalties += 2
        
        # Check for generic contexts
        generic_context_count = sum(1 for ctx in self.generic_contexts if ctx in context_text)
        penalties += generic_context_count * 1
        possible_penalties += 1
        
        # Bonus for specific verbs
        specific_verb_count = sum(1 for verb in self.specific_verbs if verb in problem_text)
        penalties = max(0, penalties - specific_verb_count * 1)
        
        # Bonus for specific nouns
        specific_noun_count = sum(1 for noun in self.specific_nouns if noun in problem_text)
        penalties = max(0, penalties - specific_noun_count * 1)
        
        # Bonus for specific contexts
        specific_context_count = sum(1 for ctx in self.specific_contexts if ctx in context_text)
        penalties = max(0, penalties - specific_context_count * 1)
        
        # Length and detail bonuses
        length_bonus = self._calculate_length_bonus(problem_text)
        detail_bonus = self._calculate_detail_bonus(pain)
        
        # Calculate score
        if possible_penalties == 0:
            score = 0.0
        else:
            score = 1.0 - (penalties / possible_penalties)
        
        # Apply bonuses
        score = min(1.0, score + length_bonus + detail_bonus)
        
        return score, penalties, possible_penalties
    
    def _calculate_length_bonus(self, text: str) -> float:
        """Calculate bonus for longer, more detailed pain descriptions."""
        word_count = len(re.findall(r'\b\w+\b', text))
        
        if word_count < 5:
            return 0.0
        elif word_count < 10:
            return 0.05
        elif word_count < 15:
            return 0.1
        else:
            return 0.15
    
    def _calculate_detail_bonus(self, pain: Dict) -> float:
        """Calculate bonus for detailed pain information."""
        bonus = 0.0
        
        # Check for severity
        if pain.get("severity") and pain["severity"] > 1:
            bonus += 0.05
        
        # Check for specific actor
        actor = pain.get("actor", "").lower()
        if actor and len(actor.split()) > 1:  # Multi-word actor
            bonus += 0.05
        
        # Check for specific context
        context = pain.get("context", "").lower()
        if context and len(context.split()) > 2:  # Detailed context
            bonus += 0.05
        
        return min(0.15, bonus)
    
    def _analyze_penalties(self, pains: List[Dict]) -> Dict[str, Any]:
        """Analyze penalty patterns across all pains."""
        analysis = {
            "generic_verbs_usage": [],
            "generic_nouns_usage": [],
            "missing_specificity": []
        }
        
        for i, pain in enumerate(pains):
            problem_text = pain.get("problem", "").lower()
            
            # Find generic verbs
            generic_verbs_found = [verb for verb in self.generic_verbs if verb in problem_text]
            if generic_verbs_found:
                analysis["generic_verbs_usage"].append({
                    "pain_index": i,
                    "verbs": generic_verbs_found
                })
            
            # Find generic nouns
            generic_nouns_found = [noun for noun in self.generic_nouns if noun in problem_text]
            if generic_nouns_found:
                analysis["generic_nouns_usage"].append({
                    "pain_index": i,
                    "nouns": generic_nouns_found
                })
            
            # Check for missing specificity
            actor = pain.get("actor", "")
            context = pain.get("context", "")
            if not actor or not context or len(problem_text.split()) < 5:
                analysis["missing_specificity"].append({
                    "pain_index": i,
                    "issues": []
                })
                if not actor:
                    analysis["missing_specificity"][-1]["issues"].append("missing_actor")
                if not context:
                    analysis["missing_specificity"][-1]["issues"].append("missing_context")
                if len(problem_text.split()) < 5:
                    analysis["missing_specificity"][-1]["issues"].append("vague_problem")
        
        return analysis
    
    def get_required_artifacts(self) -> List[str]:
        """Get required artifacts for this metric."""
        return ["pains_structured", "pains_validated"]
    
    def get_required_ground_truth(self) -> List[str]:
        """Get required ground truth fields."""
        return []
