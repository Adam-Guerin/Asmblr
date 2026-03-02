"""
Base class for all benchmark metrics.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class MetricResult:
    """Result of metric computation."""
    score: float
    explanation: str
    evidence: Dict[str, Any]
    details: Optional[Dict[str, Any]] = None
    confidence: Optional[float] = None


class BaseMetric(ABC):
    """Base class for all benchmark metrics."""
    
    def __init__(self, config: Any):
        self.config = config
        self.name = self.__class__.__name__.lower().replace('metric', '').replace('_', '')
    
    @abstractmethod
    def compute(self, run_result: Dict[str, Any], dataset: List[Dict]) -> MetricResult:
        """Compute the metric for a given run result and dataset."""
        pass
    
    def validate_inputs(self, run_result: Dict[str, Any], dataset: List[Dict]) -> bool:
        """Validate that required inputs are present."""
        return True
    
    def get_required_artifacts(self) -> List[str]:
        """Get list of required artifacts for this metric."""
        return []
    
    def get_required_ground_truth(self) -> List[str]:
        """Get list of required ground truth fields."""
        return []
    
    def _extract_artifact(self, run_result: Dict[str, Any], artifact_name: str) -> Optional[Any]:
        """Extract artifact from run result."""
        artifacts = run_result.get("artifacts", {})
        artifact = artifacts.get(artifact_name)
        
        if artifact is None or not artifact.get("exists", False):
            return None
        
        return artifact.get("content")
    
    def _extract_ground_truth(self, dataset_item: Dict, field_path: str) -> Any:
        """Extract ground truth field from dataset item."""
        ground_truth = dataset_item.get("ground_truth", {})
        
        # Navigate nested field path
        fields = field_path.split(".")
        value = ground_truth
        
        for field in fields:
            if isinstance(value, dict) and field in value:
                value = value[field]
            else:
                return None
        
        return value
    
    def _safe_divide(self, numerator: float, denominator: float, default: float = 0.0) -> float:
        """Safe division with default value."""
        if denominator == 0:
            return default
        return numerator / denominator
    
    def _normalize_score(self, score: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """Normalize score to [0, 1] range."""
        if max_val <= min_val:
            return 0.0
        
        normalized = (score - min_val) / (max_val - min_val)
        return max(0.0, min(1.0, normalized))
