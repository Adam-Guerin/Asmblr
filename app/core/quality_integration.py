"""Integration hook for quality metrics in the pipeline."""

from pathlib import Path
from typing import Any
import json
from loguru import logger

from app.core.quality_metrics import evaluate_run_quality


def generate_quality_metrics_report(
    run_id: str,
    output_dir: Path,
    ideas: list[dict[str, Any]],
    pains: list[dict[str, Any]], 
    pages: list[dict[str, Any]]
) -> None:
    """Generate and save quality metrics report for a run."""
    try:
        # Calculate quality metrics
        quality_metrics = evaluate_run_quality(ideas, pains, pages)
        
        # Convert to serializable format
        quality_report = {
            "run_id": run_id,
            "timestamp": Path.cwd().name,  # Use run folder as timestamp proxy
            "idea_specificity_score": quality_metrics.idea_specificity_score,
            "idea_feasibility_score": quality_metrics.idea_feasibility_score,
            "idea_market_validation_score": quality_metrics.idea_market_validation_score,
            "idea_innovation_score": quality_metrics.idea_innovation_score,
            "signal_diversity_score": quality_metrics.signal_diversity_score,
            "signal_recency_score": quality_metrics.signal_recency_score,
            "signal_relevance_score": quality_metrics.signal_relevance_score,
            "overall_quality_score": quality_metrics.overall_quality_score,
            "quality_level": quality_metrics.quality_level.value,
            "improvement_areas": quality_metrics.improvement_areas,
            "strengths": quality_metrics.strengths
        }
        
        # Save to output directory
        quality_file = output_dir / "quality_metrics.json"
        quality_file.write_text(json.dumps(quality_report, indent=2), encoding="utf-8")
        
        logger.info(f"Quality metrics report generated for run {run_id}: {quality_metrics.overall_quality_score:.1f}/100 ({quality_metrics.quality_level.value})")
        
    except Exception as e:
        logger.error(f"Failed to generate quality metrics for run {run_id}: {e}")


def should_improve_run(quality_metrics: dict[str, Any]) -> bool:
    """Determine if a run needs improvement based on quality metrics."""
    overall_score = quality_metrics.get("overall_quality_score", 0)
    specificity_score = quality_metrics.get("idea_specificity_score", 0)
    
    # Recommend improvement if overall quality is below threshold
    # OR if idea specificity is too low (critical for good results)
    return overall_score < 65 or specificity_score < 60


def get_improvement_recommendations(quality_metrics: dict[str, Any]) -> list[str]:
    """Get specific improvement recommendations based on quality metrics."""
    recommendations = []
    
    specificity = quality_metrics.get("idea_specificity_score", 0)
    feasibility = quality_metrics.get("idea_feasibility_score", 0)
    market_validation = quality_metrics.get("idea_market_validation_score", 0)
    signal_diversity = quality_metrics.get("signal_diversity_score", 0)
    
    if specificity < 60:
        recommendations.append("Increase idea specificity - add concrete target users and detailed features")
    
    if feasibility < 60:
        recommendations.append("Simplify technical scope - focus on core MVP features")
        
    if market_validation < 60:
        recommendations.append("Strengthen market validation - add more evidence of real demand")
        
    if signal_diversity < 50:
        recommendations.append("Diversify data sources - include more varied market signals")
    
    return recommendations
