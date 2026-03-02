"""
Feasibility Score metric - heuristic rubric for technical and economic feasibility.
"""

from typing import Any

from .base import BaseMetric, MetricResult


class FeasibilityScore(BaseMetric):
    """Measures feasibility of generated ideas using heuristic rubric."""
    
    requires_ground_truth = False
    output_type = "score"
    
    def __init__(self, config: Any):
        super().__init__(config)
        
        # Feasibility criteria weights
        self.weights = {
            "technical_complexity": 0.3,
            "resource_requirements": 0.25,
            "market_readiness": 0.2,
            "regulatory_barriers": 0.15,
            "timeline_realism": 0.1
        }
    
    def compute(self, run_result: dict[str, Any], dataset: list[dict]) -> MetricResult:
        """Compute feasibility score."""
        # Extract system ideas
        system_ideas = self._extract_system_ideas(run_result)
        if not system_ideas:
            return MetricResult(
                score=0.0,
                explanation="No ideas extracted from system",
                evidence={"system_ideas_count": 0}
            )
        
        # Calculate feasibility for each idea
        idea_scores = []
        detailed_scores = []
        
        for idea in system_ideas:
            score, details = self._calculate_idea_feasibility(idea)
            idea_scores.append(score)
            detailed_scores.append(details)
        
        # Overall feasibility
        avg_feasibility = sum(idea_scores) / len(idea_scores) if idea_scores else 0.0
        max_feasibility = max(idea_scores) if idea_scores else 0.0
        
        explanation = f"Feasibility: {avg_feasibility:.3f} (max: {max_feasibility:.3f})"
        
        evidence = {
            "system_ideas_count": len(system_ideas),
            "avg_feasibility": avg_feasibility,
            "max_feasibility": max_feasibility,
            "individual_scores": idea_scores
        }
        
        return MetricResult(
            score=avg_feasibility,
            explanation=explanation,
            evidence=evidence,
            details={
                "idea_feasibility_scores": list(zip(range(len(system_ideas)), idea_scores)),
                "detailed_scores": detailed_scores[:3]  # First 3 for brevity
            }
        )
    
    def _extract_system_ideas(self, run_result: dict[str, Any]) -> list[dict]:
        """Extract ideas from system output."""
        ideas = []
        
        # Try opportunities_structured.json
        opportunities = self._extract_artifact(run_result, "opportunities_structured")
        if opportunities and isinstance(opportunities, dict):
            if "opportunities" in opportunities:
                ideas.extend(opportunities["opportunities"])
            elif "ideas" in opportunities:
                ideas.extend(opportunities["ideas"])
        
        # Try opportunities.json
        simple_opportunities = self._extract_artifact(run_result, "opportunities")
        if simple_opportunities and isinstance(simple_opportunities, list):
            ideas.extend(simple_opportunities)
        
        return ideas
    
    def _calculate_idea_feasibility(self, idea: dict) -> tuple[float, dict]:
        """Calculate feasibility score for a single idea."""
        # Extract text fields
        title = idea.get("title", "")
        description = idea.get("description", "")
        solution = idea.get("solution", "")
        features = idea.get("features", [])
        
        combined_text = f"{title} {description} {solution} {' '.join(features)}".lower()
        
        # Calculate individual feasibility components
        technical_score = self._assess_technical_complexity(combined_text)
        resource_score = self._assess_resource_requirements(combined_text)
        market_score = self._assess_market_readiness(combined_text)
        regulatory_score = self._assess_regulatory_barriers(combined_text)
        timeline_score = self._assess_timeline_realism(combined_text)
        
        # Weighted combination
        overall_score = (
            self.weights["technical_complexity"] * technical_score +
            self.weights["resource_requirements"] * resource_score +
            self.weights["market_readiness"] * market_score +
            self.weights["regulatory_barriers"] * regulatory_score +
            self.weights["timeline_realism"] * timeline_score
        )
        
        details = {
            "technical_complexity": technical_score,
            "resource_requirements": resource_score,
            "market_readiness": market_score,
            "regulatory_barriers": regulatory_score,
            "timeline_realism": timeline_score,
            "overall_score": overall_score
        }
        
        return overall_score, details
    
    def _assess_technical_complexity(self, text: str) -> float:
        """Assess technical complexity (higher complexity = lower feasibility)."""
        complexity_indicators = [
            "artificial intelligence", "machine learning", "deep learning", "neural network",
            "blockchain", "distributed ledger", "quantum computing",
            "computer vision", "natural language processing", "advanced analytics",
            "predictive modeling", "recommendation engine", "autonomous"
        ]
        
        # Count complexity indicators
        complexity_count = sum(1 for indicator in complexity_indicators if indicator in text)
        
        # Base score with penalty for high complexity
        base_score = 0.7
        complexity_penalty = min(0.5, complexity_count * 0.1)
        
        return max(0.0, base_score - complexity_penalty)
    
    def _assess_resource_requirements(self, text: str) -> float:
        """Assess resource requirements (higher requirements = lower feasibility)."""
        high_resource_indicators = [
            "massive infrastructure", "huge team", "significant investment",
            "enterprise scale", "global deployment", "extensive computing",
            "large data centers", "thousands of servers", "billion dollar"
        ]
        
        # Count high resource indicators
        resource_count = sum(1 for indicator in high_resource_indicators if indicator in text)
        
        # Base score with penalty for high resource needs
        base_score = 0.8
        resource_penalty = min(0.4, resource_count * 0.15)
        
        return max(0.0, base_score - resource_penalty)
    
    def _assess_market_readiness(self, text: str) -> float:
        """Assess market readiness (higher readiness = higher feasibility)."""
        ready_indicators = [
            "proven technology", "existing market", "clear demand",
            "customer base", "revenue model", "business case",
            "market validation", "early adopters", "pilot program"
        ]
        
        not_ready_indicators = [
            "experimental", "research phase", "prototype", "concept stage",
            "future technology", "emerging market", "uncertain demand"
        ]
        
        ready_count = sum(1 for indicator in ready_indicators if indicator in text)
        not_ready_count = sum(1 for indicator in not_ready_indicators if indicator in text)
        
        # Calculate readiness score
        if ready_count > not_ready_count:
            return 0.8
        elif ready_count == not_ready_count:
            return 0.5
        else:
            return 0.3
    
    def _assess_regulatory_barriers(self, text: str) -> float:
        """Assess regulatory barriers (higher barriers = lower feasibility)."""
        high_barrier_indicators = [
            "fda approval", "medical device", "pharmaceutical", "financial services",
            "banking", "insurance", "healthcare data", "patient information",
            "financial advice", "investment advice", "regulated industry"
        ]
        
        low_barrier_indicators = [
            "unregulated", "low barrier", "minimal compliance",
            "standard industry", "non-sensitive data", "b2b software"
        ]
        
        high_barrier_count = sum(1 for indicator in high_barrier_indicators if indicator in text)
        low_barrier_count = sum(1 for indicator in low_barrier_indicators if indicator in text)
        
        # Calculate barrier score
        if high_barrier_count > low_barrier_count:
            return 0.4
        elif high_barrier_count == low_barrier_count:
            return 0.6
        else:
            return 0.8
    
    def _assess_timeline_realism(self, text: str) -> float:
        """Assess timeline realism (more realistic = higher feasibility)."""
        unrealistic_indicators = [
            "overnight success", "immediate profit", "instant market",
            "quick domination", "rapid scaling", "explosive growth",
            "million users in months", "billion dollar valuation quickly"
        ]
        
        realistic_indicators = [
            "phased approach", "iterative development", "mvp first",
            "gradual scaling", "customer validation", "market testing",
            "realistic timeline", "measured growth"
        ]
        
        unrealistic_count = sum(1 for indicator in unrealistic_indicators if indicator in text)
        realistic_count = sum(1 for indicator in realistic_indicators if indicator in text)
        
        # Calculate timeline score
        if unrealistic_count > realistic_count:
            return 0.3
        elif unrealistic_count == realistic_count:
            return 0.6
        else:
            return 0.8
    
    def get_required_artifacts(self) -> list[str]:
        """Get required artifacts for this metric."""
        return ["opportunities_structured", "opportunities"]
    
    def get_required_ground_truth(self) -> list[str]:
        """Get required ground truth fields."""
        return []
