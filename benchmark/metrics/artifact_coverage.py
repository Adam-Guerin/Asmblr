"""
Artifact Coverage metric - percentage of required artifacts produced.
"""

from typing import Any

from .base import BaseMetric, MetricResult


class ArtifactCoverage(BaseMetric):
    """Measures percentage of required artifacts produced by the system."""
    
    requires_ground_truth = False
    output_type = "score"
    
    def __init__(self, config: Any):
        super().__init__(config)
        
        # Required artifacts with weights
        self.required_artifacts = {
            "pains_structured": {"weight": 0.15, "essential": True},
            "pains_validated": {"weight": 0.10, "essential": False},
            "opportunities": {"weight": 0.15, "essential": True},
            "opportunities_structured": {"weight": 0.10, "essential": False},
            "competitor_analysis": {"weight": 0.15, "essential": True},
            "decision": {"weight": 0.15, "essential": True},
            "confidence": {"weight": 0.10, "essential": False},
            "prd": {"weight": 0.10, "essential": False},
            "tech_spec": {"weight": 0.10, "essential": False},
            "landing_page": {"weight": 0.05, "essential": False},
            "mvp_repo": {"weight": 0.15, "essential": False}
        }
    
    def compute(self, run_result: dict[str, Any], dataset: list[dict]) -> MetricResult:
        """Compute artifact coverage score."""
        artifacts = run_result.get("artifacts", {})
        missing_artifacts = run_result.get("missing_artifacts", [])
        
        # Calculate coverage metrics
        total_artifacts = len(self.required_artifacts)
        present_artifacts = 0
        essential_present = 0
        total_essential = 0
        
        artifact_scores = {}
        weighted_score = 0.0
        total_weight = 0.0
        
        for artifact_name, config in self.required_artifacts.items():
            is_present = artifact_name not in missing_artifacts and artifacts.get(artifact_name, {}).get("exists", False)
            is_essential = config["essential"]
            weight = config["weight"]
            
            if is_present:
                present_artifacts += 1
                artifact_score = 1.0
                
                if is_essential:
                    essential_present += 1
                
                # Check if artifact has content
                artifact_data = artifacts.get(artifact_name, {})
                if artifact_data.get("content") or (artifact_data.get("type") == "directory" and artifact_data.get("size", 0) > 0):
                    artifact_score = 1.0
                else:
                    artifact_score = 0.5  # Present but empty
            else:
                artifact_score = 0.0
            
            artifact_scores[artifact_name] = {
                "present": is_present,
                "score": artifact_score,
                "weight": weight,
                "essential": is_essential
            }
            
            weighted_score += artifact_score * weight
            total_weight += weight
            
            if is_essential:
                total_essential += 1
        
        # Calculate coverage scores
        basic_coverage = present_artifacts / total_artifacts if total_artifacts > 0 else 0.0
        essential_coverage = essential_present / total_essential if total_essential > 0 else 0.0
        weighted_coverage = weighted_score / total_weight if total_weight > 0 else 0.0
        
        # Final score combines basic and essential coverage
        final_score = 0.6 * weighted_coverage + 0.4 * essential_coverage
        
        explanation = f"Artifact coverage: {final_score:.3f} (present: {present_artifacts}/{total_artifacts}, essential: {essential_present}/{total_essential})"
        
        evidence = {
            "total_artifacts": total_artifacts,
            "present_artifacts": present_artifacts,
            "essential_artifacts": total_essential,
            "essential_present": essential_present,
            "basic_coverage": basic_coverage,
            "essential_coverage": essential_coverage,
            "weighted_coverage": weighted_coverage,
            "missing_artifacts": missing_artifacts
        }
        
        return MetricResult(
            score=final_score,
            explanation=explanation,
            evidence=evidence,
            details={
                "artifact_scores": artifact_scores,
                "missing_essential": [name for name, config in self.required_artifacts.items() 
                                     if config["essential"] and name in missing_artifacts]
            }
        )
    
    def get_required_artifacts(self) -> list[str]:
        """Get required artifacts for this metric."""
        return list(self.required_artifacts.keys())
    
    def get_required_ground_truth(self) -> list[str]:
        """Get required ground truth fields."""
        return []
