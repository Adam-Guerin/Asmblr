"""
Asmblr Scientific Benchmark Suite

A comprehensive evaluation framework for autonomous entrepreneurial multi-agent systems.
"""

__version__ = "1.0.0"
__author__ = "Research Engineering Team"

from .core import BenchmarkRunner, ExperimentConfig
from .datasets import DatasetRegistry, load_dataset
from .metrics import MetricRegistry, compute_all_metrics
from .baselines import BaselineRegistry, run_baseline
from .reporting import ReportGenerator

__all__ = [
    "BenchmarkRunner",
    "ExperimentConfig", 
    "DatasetRegistry",
    "load_dataset",
    "MetricRegistry",
    "compute_all_metrics",
    "BaselineRegistry",
    "run_baseline",
    "ReportGenerator"
]
