"""Quality metrics system for Asmblr results evaluation.

This module provides comprehensive quality metrics to evaluate
and improve the quality of generated ideas, scoring, and analysis.
"""

from dataclasses import dataclass
from typing import Any
from enum import Enum


class QualityLevel(Enum):
    POOR = "poor"
    FAIR = "fair" 
    GOOD = "good"
    EXCELLENT = "excellent"


@dataclass
class QualityMetrics:
    """Comprehensive quality metrics for Asmblr outputs."""
    
    # Idea Quality Metrics
    idea_specificity_score: float  # How specific are the ideas?
    idea_feasibility_score: float  # How technically feasible?
    idea_market_validation_score: float  # Market evidence strength
    idea_innovation_score: float  # How innovative/differentiated?
    
    # Signal Quality Metrics  
    signal_diversity_score: float  # Diversity of sources
    signal_recency_score: float   # Freshness of data
    signal_relevance_score: float  # Relevance to topic
    
    # Scoring Quality Metrics
    scoring_consistency_score: float  # Consistency across evaluations
    scoring_discrimination_score: float  # Ability to distinguish good/bad
    
    # Overall Quality
    overall_quality_score: float
    quality_level: QualityLevel
    
    # Recommendations
    improvement_areas: list[str]
    strengths: list[str]


class QualityMetricsCalculator:
    """Calculates quality metrics for Asmblr outputs."""
    
    def __init__(self):
        self.weights = {
            'idea_specificity': 0.25,
            'idea_feasibility': 0.20,
            'market_validation': 0.20,
            'innovation': 0.15,
            'signal_quality': 0.20
        }
    
    def calculate_idea_quality(
        self, 
        ideas: list[dict[str, Any]], 
        pains: list[dict[str, Any]]
    ) -> dict[str, float]:
        """Calculate quality metrics for generated ideas."""
        
        if not ideas:
            return {
                'specificity': 0.0,
                'feasibility': 0.0, 
                'market_validation': 0.0,
                'innovation': 0.0
            }
        
        specificity_scores = []
        feasibility_scores = []
        validation_scores = []
        innovation_scores = []
        
        for idea in ideas:
            # Specificity: concrete features vs vague benefits
            specificity = self._calculate_specificity(idea)
            specificity_scores.append(specificity)
            
            # Feasibility: technical complexity assessment
            feasibility = self._calculate_feasibility(idea)
            feasibility_scores.append(feasibility)
            
            # Market validation: evidence of real demand
            validation = self._calculate_market_validation(idea, pains)
            validation_scores.append(validation)
            
            # Innovation: differentiation from existing solutions
            innovation = self._calculate_innovation(idea)
            innovation_scores.append(innovation)
        
        return {
            'specificity': sum(specificity_scores) / len(specificity_scores),
            'feasibility': sum(feasibility_scores) / len(feasibility_scores),
            'market_validation': sum(validation_scores) / len(validation_scores),
            'innovation': sum(innovation_scores) / len(innovation_scores)
        }
    
    def _calculate_specificity(self, idea: dict[str, Any]) -> float:
        """Calculate how specific and concrete an idea is."""
        score = 0.0
        max_score = 100.0
        
        # HEAVY PENALTY for generic target users
        target_user = idea.get('target_user', '').lower()
        generic_terms = ['users', 'people', 'customers', 'businesses', 'companies', 'organizations']
        if any(term in target_user for term in generic_terms):
            score -= 30  # Heavy penalty
        
        # BONUS for hyper-specific target users
        specific_indicators = ['developers', 'founders', 'managers', 'students', 'freelancers', 'startup', 'smb', 'enterprise']
        if any(term in target_user for term in specific_indicators):
            score += 20
        
        # BONUS for company size/industry specificity
        if any(size in target_user for size in ['1-10', '11-50', '51-200', '200+', 'seed', 'series a', 'enterprise']):
            score += 15
        
        # PENALTY for generic problem statements
        problem = idea.get('problem', '').lower()
        generic_problem_terms = ['save time', 'improve efficiency', 'streamline', 'optimize', 'automate', 'simplify']
        generic_count = sum(1 for term in generic_problem_terms if term in problem)
        score -= generic_count * 15
        
        # BONUS for specific problem details
        if len(problem) > 100 and any(word in problem for word in ['struggle', 'difficulty', 'challenge', 'issue', 'pain point']):
            score += 20
        
        # BONUS for concrete, numbered features
        features = idea.get('key_features', [])
        if len(features) >= 5:
            score += 25
        elif len(features) >= 3:
            score += 15
        
        # BONUS for specific validation methods
        validation = idea.get('validation_method', '').lower()
        specific_validation = ['waitlist', 'landing page', 'interview', 'survey', 'prototype', 'mvp', 'pilot']
        if any(method in validation for method in specific_validation):
            score += 20
        
        return max(0, min(score, max_score))
    
    def _calculate_feasibility(self, idea: dict[str, Any]) -> float:
        """Assess technical feasibility of the idea."""
        score = 50.0  # Base score
        
        # Penalize overly complex solutions
        solution = idea.get('solution', '').lower()
        complexity_indicators = ['platform', 'ecosystem', 'suite', 'all-in-one', 'comprehensive']
        if any(indicator in solution for indicator in complexity_indicators):
            score -= 20
        
        # Bonus for focused solutions
        focus_indicators = ['api', 'tool', 'plugin', 'extension', 'automation']
        if any(indicator in solution for indicator in focus_indicators):
            score += 20
        
        # Check for realistic scope
        features = idea.get('key_features', [])
        if len(features) <= 5:  # Reasonable MVP scope
            score += 10
        elif len(features) > 10:  # Too ambitious
            score -= 15
        
        return max(0, min(100, score))
    
    def _calculate_market_validation(self, idea: dict[str, Any], pains: list[dict[str, Any]]) -> float:
        """Assess market validation evidence."""
        score = 0.0
        
        # Check if idea links to real pains
        linked_pains = idea.get('linked_pain_ids', [])
        if linked_pains and pains:
            score += 30
        
        # Check for market size indicators
        if 'market_size_estimate' in idea:
            estimate = idea.get('market_size_estimate', '').lower()
            if estimate in ['medium', 'large']:
                score += 25
            elif estimate == 'small':
                score += 15
            elif estimate == 'tiny':
                score += 5
        
        # Check for competitive awareness
        solution = idea.get('solution', '').lower()
        if any(word in solution for word in ['alternative', 'existing', 'current', 'traditional']):
            score += 20
        
        # Check for monetization hints
        if any(word in solution for word in ['subscription', 'pricing', 'revenue', 'business model']):
            score += 25
        
        return min(100, score)
    
    def _calculate_innovation(self, idea: dict[str, Any]) -> float:
        """Assess innovation and differentiation."""
        score = 50.0  # Base score
        
        solution = idea.get('solution', '').lower()
        
        # Penalize generic solutions
        generic_terms = ['save time', 'improve efficiency', 'streamline', 'optimize', 'automate']
        generic_count = sum(1 for term in generic_terms if term in solution)
        score -= generic_count * 10
        
        # Bonus for specific technical approaches
        tech_terms = ['ai', 'machine learning', 'blockchain', 'api', 'integration', 'automation']
        if any(term in solution for term in tech_terms):
            score += 15
        
        # Bonus for clear value proposition
        if any(word in solution for word in ['unique', 'proprietary', 'patented', 'first-of-its-kind']):
            score += 20
        
        # Check for competitive advantage
        features = idea.get('key_features', [])
        if any('advantage' in str(f).lower() or 'different' in str(f).lower() for f in features):
            score += 15
        
        return max(0, min(100, score))
    
    def calculate_signal_quality(self, pages: list[dict[str, Any]]) -> dict[str, float]:
        """Calculate quality metrics for signal data."""
        if not pages:
            return {
                'diversity': 0.0,
                'recency': 0.0,
                'relevance': 0.0
            }
        
        # Diversity: variety of sources
        sources = list(set(page.get('source_name', '') for page in pages))
        diversity_score = min(100, len(sources) * 20)  # 5 sources = 100
        
        # Recency: freshness of data
        recency_scores = []
        for page in pages:
            # Simple heuristic: newer pages have higher scores
            text_length = len(page.get('text', ''))
            recency_scores.append(min(100, text_length / 10))  # Rough proxy
        
        recency_score = sum(recency_scores) / len(recency_scores) if recency_scores else 0
        
        # Relevance: content quality and length
        relevance_scores = []
        for page in pages:
            text = page.get('text', '')
            if len(text) > 500:  # Substantial content
                relevance_scores.append(80)
            elif len(text) > 200:
                relevance_scores.append(60)
            else:
                relevance_scores.append(30)
        
        relevance_score = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
        
        return {
            'diversity': diversity_score,
            'recency': recency_score,
            'relevance': relevance_score
        }
    
    def calculate_overall_quality(
        self, 
        idea_metrics: dict[str, float],
        signal_metrics: dict[str, float]
    ) -> QualityMetrics:
        """Calculate overall quality score and recommendations."""
        
        # Weighted combination of all metrics
        idea_score = (
            idea_metrics['specificity'] * self.weights['idea_specificity'] +
            idea_metrics['feasibility'] * self.weights['idea_feasibility'] +
            idea_metrics['market_validation'] * self.weights['market_validation'] +
            idea_metrics['innovation'] * self.weights['innovation']
        )
        
        signal_score = (
            signal_metrics['diversity'] * 0.4 +
            signal_metrics['recency'] * 0.3 +
            signal_metrics['relevance'] * 0.3
        )
        
        overall_score = (idea_score * 0.7) + (signal_score * 0.3)
        
        # Determine quality level
        if overall_score >= 80:
            quality_level = QualityLevel.EXCELLENT
        elif overall_score >= 65:
            quality_level = QualityLevel.GOOD
        elif overall_score >= 50:
            quality_level = QualityLevel.FAIR
        else:
            quality_level = QualityLevel.POOR
        
        # Generate recommendations
        improvement_areas = []
        strengths = []
        
        if idea_metrics['specificity'] < 60:
            improvement_areas.append("Idea specificity needs improvement - add more concrete details")
        else:
            strengths.append("Strong idea specificity with concrete features")
        
        if idea_metrics['feasibility'] < 60:
            improvement_areas.append("Technical feasibility concerns - simplify scope")
        else:
            strengths.append("Realistic technical implementation")
        
        if signal_metrics['diversity'] < 50:
            improvement_areas.append("Limited source diversity - add more varied data sources")
        else:
            strengths.append("Good variety of signal sources")
        
        return QualityMetrics(
            idea_specificity_score=idea_metrics['specificity'],
            idea_feasibility_score=idea_metrics['feasibility'],
            idea_market_validation_score=idea_metrics['market_validation'],
            idea_innovation_score=idea_metrics['innovation'],
            signal_diversity_score=signal_metrics['diversity'],
            signal_recency_score=signal_metrics['recency'],
            signal_relevance_score=signal_metrics['relevance'],
            overall_quality_score=overall_score,
            quality_level=quality_level,
            improvement_areas=improvement_areas,
            strengths=strengths
        )


def evaluate_run_quality(
    ideas: list[dict[str, Any]],
    pains: list[dict[str, Any]], 
    pages: list[dict[str, Any]]
) -> QualityMetrics:
    """Evaluate the quality of an Asmblr run."""
    calculator = QualityMetricsCalculator()
    
    idea_metrics = calculator.calculate_idea_quality(ideas, pains)
    signal_metrics = calculator.calculate_signal_quality(pages)
    
    return calculator.calculate_overall_quality(idea_metrics, signal_metrics)
