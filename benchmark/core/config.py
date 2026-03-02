"""
Configuration management for benchmark experiments.
"""

import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class ExperimentConfig:
    """Configuration for benchmark experiments."""
    
    # Dataset configuration
    dataset_name: str = "toy_pains_v1"
    dataset_path: Optional[str] = None
    train_split: float = 0.7
    val_split: float = 0.15
    test_split: float = 0.15
    
    # Run configuration
    seed: int = 42
    output_dir: str = "benchmark_outputs"
    experiment_id: Optional[str] = None
    
    # Asmblr run directories (for evaluation)
    asmblr_run_dirs: List[str] = field(default_factory=list)
    
    # Baselines to run
    baselines: List[str] = field(default_factory=lambda: ["random", "rule_based", "single_agent"])
    
    # Metrics to compute
    metrics: List[str] = field(default_factory=lambda: [
        "pain_extraction_quality",
        "pain_specificity_score", 
        "clustering_quality",
        "idea_novelty",
        "feasibility_score",
        "competitor_coverage",
        "decision_quality",
        "confidence_calibration",
        "prd_completeness",
        "tech_spec_actionability",
        "artifact_coverage"
    ])
    
    # Metric thresholds and weights
    metric_weights: Dict[str, float] = field(default_factory=dict)
    thresholds: Dict[str, float] = field(default_factory=dict)
    
    # Bootstrap configuration
    bootstrap_samples: int = 1000
    confidence_level: float = 0.95
    
    # Reporting configuration
    generate_plots: bool = True
    generate_markdown: bool = True
    include_detailed_errors: bool = False
    
    # Reproducibility
    deterministic: bool = True
    save_intermediate: bool = True
    
    def __post_init__(self):
        """Post-initialization validation and setup."""
        if self.experiment_id is None:
            from datetime import datetime
            self.experiment_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Validate splits sum to 1.0
        total_split = self.train_split + self.val_split + self.test_split
        if abs(total_split - 1.0) > 0.001:
            raise ValueError(f"Data splits must sum to 1.0, got {total_split}")
        
        # Set default metric weights
        default_weights = {
            "pain_extraction_quality": 0.15,
            "pain_specificity_score": 0.10,
            "clustering_quality": 0.10,
            "idea_novelty": 0.15,
            "feasibility_score": 0.10,
            "competitor_coverage": 0.10,
            "decision_quality": 0.15,
            "confidence_calibration": 0.10,
            "prd_completeness": 0.05,
            "tech_spec_actionability": 0.05,
            "artifact_coverage": 0.05
        }
        
        for metric, weight in default_weights.items():
            if metric not in self.metric_weights:
                self.metric_weights[metric] = weight
        
        # Set default thresholds
        default_thresholds = {
            "pain_extraction_quality": 0.7,
            "pain_specificity_score": 0.6,
            "clustering_quality": 0.6,
            "idea_novelty": 0.5,
            "feasibility_score": 0.6,
            "competitor_coverage": 0.7,
            "decision_quality": 0.8,
            "confidence_calibration": 0.8,  # ECE threshold
            "prd_completeness": 0.7,
            "tech_spec_actionability": 0.7,
            "artifact_coverage": 0.8
        }
        
        for metric, threshold in default_thresholds.items():
            if metric not in self.thresholds:
                self.thresholds[metric] = threshold
    
    @classmethod
    def from_yaml(cls, config_path: str) -> "ExperimentConfig":
        """Load configuration from YAML file."""
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        
        logger.info(f"Loaded config from {config_path}")
        return cls(**config_dict)
    
    def to_yaml(self, output_path: str):
        """Save configuration to YAML file."""
        config_dict = {
            "dataset_name": self.dataset_name,
            "dataset_path": self.dataset_path,
            "train_split": self.train_split,
            "val_split": self.val_split,
            "test_split": self.test_split,
            "seed": self.seed,
            "output_dir": self.output_dir,
            "experiment_id": self.experiment_id,
            "asmblr_run_dirs": self.asmblr_run_dirs,
            "baselines": self.baselines,
            "metrics": self.metrics,
            "metric_weights": self.metric_weights,
            "thresholds": self.thresholds,
            "bootstrap_samples": self.bootstrap_samples,
            "confidence_level": self.confidence_level,
            "generate_plots": self.generate_plots,
            "generate_markdown": self.generate_markdown,
            "include_detailed_errors": self.include_detailed_errors,
            "deterministic": self.deterministic,
            "save_intermediate": self.save_intermediate
        }
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        
        logger.info(f"Saved config to {output_path}")
    
    def get_output_path(self, *path_parts) -> Path:
        """Get full path for output files."""
        base_path = Path(self.output_dir) / self.experiment_id
        if path_parts:
            return base_path / Path(*path_parts)
        return base_path
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Validate dataset
        if not self.dataset_name:
            issues.append("dataset_name is required")
        
        # Validate metrics
        valid_metrics = [
            "pain_extraction_quality",
            "pain_specificity_score", 
            "clustering_quality",
            "idea_novelty",
            "feasibility_score",
            "competitor_coverage",
            "decision_quality",
            "confidence_calibration",
            "prd_completeness",
            "tech_spec_actionability",
            "artifact_coverage"
        ]
        
        for metric in self.metrics:
            if metric not in valid_metrics:
                issues.append(f"Unknown metric: {metric}")
        
        # Validate baselines
        valid_baselines = ["random", "rule_based", "single_agent"]
        for baseline in self.baselines:
            if baseline not in valid_baselines:
                issues.append(f"Unknown baseline: {baseline}")
        
        # Validate weights sum
        weight_sum = sum(self.metric_weights.get(m, 0) for m in self.metrics)
        if abs(weight_sum - 1.0) > 0.01:
            issues.append(f"Metric weights sum to {weight_sum:.3f}, should be 1.0")
        
        return issues
