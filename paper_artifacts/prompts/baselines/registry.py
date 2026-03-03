"""
Baseline registry and execution utilities.
"""

from pathlib import Path
from typing import Any
import logging

from .random_baseline import RandomBaseline
from .rule_based import RuleBasedBaseline
from .single_agent import SingleAgentBaseline

logger = logging.getLogger(__name__)


class BaselineRegistry:
    """Registry for baseline systems."""
    
    _baselines: dict[str, type] = {
        "random": RandomBaseline,
        "rule_based": RuleBasedBaseline,
        "single_agent": SingleAgentBaseline
    }
    
    @classmethod
    def register(cls, name: str, baseline_class: type):
        """Register a new baseline."""
        cls._baselines[name] = baseline_class
        logger.info(f"Registered baseline: {name}")
    
    @classmethod
    def get_baseline_class(cls, name: str) -> type | None:
        """Get baseline class by name."""
        return cls._baselines.get(name)
    
    @classmethod
    def list_baselines(cls) -> list[str]:
        """List all registered baselines."""
        return list(cls._baselines.keys())
    
    @classmethod
    def baseline_info(cls, name: str) -> dict | None:
        """Get information about a baseline."""
        baseline_class = cls.get_baseline_class(name)
        if baseline_class is None:
            return None
        
        return {
            "name": name,
            "class": baseline_class.__name__,
            "description": getattr(baseline_class, "__doc__", ""),
            "deterministic": hasattr(baseline_class, "deterministic")
        }


def run_baseline(baseline_name: str, dataset: list[dict], config: Any, output_dir: Path) -> dict[str, Any]:
    """Run a baseline system on the dataset."""
    baseline_class = BaselineRegistry.get_baseline_class(baseline_name)
    if baseline_class is None:
        raise ValueError(f"Unknown baseline: {baseline_name}")
    
    try:
        # Initialize baseline
        baseline = baseline_class(config)
        
        # Run baseline on dataset
        results = []
        for item in dataset:
            result = baseline.process_item(item)
            results.append(result)
        
        # Create output directory for this baseline
        baseline_output_dir = output_dir / f"baseline_{baseline_name}"
        baseline_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save results
        baseline.save_results(results, baseline_output_dir)
        
        # Return summary
        summary = {
            "baseline_name": baseline_name,
            "output_dir": str(baseline_output_dir),
            "results": results,
            "summary": {
                "total_items": len(dataset),
                "processed_items": len(results),
                "success_rate": sum(1 for r in results if r.get("success", False)) / len(results) if results else 0.0
            }
        }
        
        logger.info(f"Completed baseline {baseline_name}: {len(results)} items processed")
        return summary
        
    except Exception as e:
        logger.error(f"Failed to run baseline {baseline_name}: {e}")
        return {
            "baseline_name": baseline_name,
            "error": str(e),
            "results": [],
            "summary": {"total_items": len(dataset), "processed_items": 0, "success_rate": 0.0}
        }
