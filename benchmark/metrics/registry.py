"""
Metric registry and computation utilities.
"""

from typing import Any
import logging

from .pain_extraction import PainExtractionQuality
from .pain_specificity import PainSpecificityScore
from .clustering import ClusteringQuality
from .idea_novelty import IdeaNovelty
from .feasibility import FeasibilityScore
from .competitor_coverage import CompetitorCoverage
from .decision_quality import DecisionQuality
from .confidence_calibration import ConfidenceCalibration
from .prd_completeness import PRDCompleteness
from .tech_spec_actionability import TechSpecActionability
from .artifact_coverage import ArtifactCoverage

logger = logging.getLogger(__name__)


class MetricRegistry:
    """Registry for benchmark metrics."""
    
    _metrics: dict[str, type] = {
        "pain_extraction_quality": PainExtractionQuality,
        "pain_specificity_score": PainSpecificityScore,
        "clustering_quality": ClusteringQuality,
        "idea_novelty": IdeaNovelty,
        "feasibility_score": FeasibilityScore,
        "competitor_coverage": CompetitorCoverage,
        "decision_quality": DecisionQuality,
        "confidence_calibration": ConfidenceCalibration,
        "prd_completeness": PRDCompleteness,
        "tech_spec_actionability": TechSpecActionability,
        "artifact_coverage": ArtifactCoverage
    }
    
    @classmethod
    def register(cls, name: str, metric_class: type):
        """Register a new metric."""
        cls._metrics[name] = metric_class
        logger.info(f"Registered metric: {name}")
    
    @classmethod
    def get_metric_class(cls, name: str) -> type | None:
        """Get metric class by name."""
        return cls._metrics.get(name)
    
    @classmethod
    def list_metrics(cls) -> list[str]:
        """List all registered metrics."""
        return list(cls._metrics.keys())
    
    @classmethod
    def metric_info(cls, name: str) -> dict | None:
        """Get information about a metric."""
        metric_class = cls.get_metric_class(name)
        if metric_class is None:
            return None
        
        return {
            "name": name,
            "class": metric_class.__name__,
            "description": getattr(metric_class, "__doc__", ""),
            "requires_ground_truth": hasattr(metric_class, "requires_ground_truth"),
            "output_type": getattr(metric_class, "output_type", "score")
        }


def compute_all_metrics(run_result: dict[str, Any], 
                      dataset: list[dict], 
                      metric_names: list[str],
                      config: Any) -> dict[str, Any]:
    """Compute all specified metrics for a run."""
    results = {}
    
    for metric_name in metric_names:
        try:
            metric_class = MetricRegistry.get_metric_class(metric_name)
            if metric_class is None:
                logger.warning(f"Unknown metric: {metric_name}")
                continue
            
            # Initialize metric
            metric = metric_class(config)
            
            # Compute metric
            result = metric.compute(run_result, dataset)
            results[metric_name] = result
            
            logger.debug(f"Computed {metric_name}: {result}")
            
        except Exception as e:
            logger.error(f"Failed to compute metric {metric_name}: {e}")
            results[metric_name] = {
                "score": 0.0,
                "error": str(e),
                "explanation": f"Metric computation failed: {e}"
            }
    
    return results


def compute_single_metric(metric_name: str, 
                       run_result: dict[str, Any], 
                       dataset: list[dict],
                       config: Any) -> dict[str, Any]:
    """Compute a single metric."""
    metric_class = MetricRegistry.get_metric_class(metric_name)
    if metric_class is None:
        raise ValueError(f"Unknown metric: {metric_name}")
    
    metric = metric_class(config)
    return metric.compute(run_result, dataset)
