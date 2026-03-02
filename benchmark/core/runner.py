"""
Main benchmark runner that orchestrates experiments.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

from .config import ExperimentConfig
from .utils import set_seed, save_json, save_jsonl, create_directory_structure
from ..datasets import DatasetRegistry, load_dataset
from ..baselines import BaselineRegistry, run_baseline
from ..metrics import MetricRegistry, compute_all_metrics
from ..reporting import ReportGenerator

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """Main benchmark orchestrator."""
    
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.dataset_registry = DatasetRegistry()
        self.baseline_registry = BaselineRegistry()
        self.metric_registry = MetricRegistry()
        self.report_generator = ReportGenerator()
        
        # Setup output directories
        self.output_dir = config.get_output_path()
        self.runs_dir = self.output_dir / "runs"
        self.tables_dir = self.output_dir / "tables"
        self.plots_dir = self.output_dir / "plots"
        
        create_directory_structure(self.output_dir, ["runs", "tables", "plots"])
        
        # Save config
        config.to_yaml(self.output_dir / "config.yaml")
        
        logger.info(f"Initialized benchmark runner for experiment {config.experiment_id}")
    
    def run_experiment(self) -> Dict[str, Any]:
        """Run complete benchmark experiment."""
        logger.info("Starting benchmark experiment")
        start_time = time.time()
        
        # Set seed for reproducibility
        if self.config.deterministic:
            set_seed(self.config.seed)
        
        try:
            # Load dataset
            dataset = load_dataset(self.config.dataset_name, self.config.dataset_path)
            if dataset is None:
                raise ValueError(f"Failed to load dataset: {self.config.dataset_name}")
            
            logger.info(f"Loaded dataset: {len(dataset)} items")
            
            # Run baselines
            baseline_results = {}
            for baseline_name in self.config.baselines:
                logger.info(f"Running baseline: {baseline_name}")
                baseline_result = run_baseline(
                    baseline_name, 
                    dataset, 
                    self.config,
                    self.runs_dir
                )
                baseline_results[baseline_name] = baseline_result
            
            # Evaluate Asmblr runs (if provided)
            asmblr_results = {}
            for run_dir in self.config.asmblr_run_dirs:
                run_name = Path(run_dir).name
                logger.info(f"Evaluating Asmblr run: {run_name}")
                asmblr_result = self._evaluate_asmblr_run(run_dir, dataset)
                asmblr_results[run_name] = asmblr_result
            
            # Compute metrics for all runs
            all_results = {**baseline_results, **asmblr_results}
            metrics_results = {}
            
            for run_name, run_result in all_results.items():
                logger.info(f"Computing metrics for {run_name}")
                metrics = compute_all_metrics(
                    run_result, 
                    dataset, 
                    self.config.metrics,
                    self.config
                )
                metrics_results[run_name] = metrics
            
            # Aggregate results and compute statistics
            aggregated_results = self._aggregate_results(metrics_results)
            
            # Generate reports
            self._generate_reports(
                dataset, 
                metrics_results, 
                aggregated_results
            )
            
            experiment_time = time.time() - start_time
            
            # Create final summary
            summary = {
                "experiment_id": self.config.experiment_id,
                "dataset": self.config.dataset_name,
                "dataset_size": len(dataset),
                "config": self.config.__dict__,
                "results": metrics_results,
                "aggregated": aggregated_results,
                "runtime_seconds": experiment_time,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Save summary
            save_json(summary, self.output_dir / "summary.json")
            
            logger.info(f"Experiment completed in {experiment_time:.2f} seconds")
            return summary
            
        except Exception as e:
            logger.error(f"Experiment failed: {e}")
            raise
    
    def evaluate_single_run(self, run_dir: str) -> Dict[str, Any]:
        """Evaluate a single Asmblr run."""
        logger.info(f"Evaluating single run: {run_dir}")
        
        # Load dataset
        dataset = load_dataset(self.config.dataset_name, self.config.dataset_path)
        if dataset is None:
            raise ValueError(f"Failed to load dataset: {self.config.dataset_name}")
        
        # Evaluate run
        result = self._evaluate_asmblr_run(run_dir, dataset)
        
        # Compute metrics
        metrics = compute_all_metrics(
            result, 
            dataset, 
            self.config.metrics,
            self.config
        )
        
        # Save results
        run_name = Path(run_dir).name
        output_path = self.output_dir / f"{run_name}_evaluation.json"
        save_json({
            "run_name": run_name,
            "run_dir": run_dir,
            "result": result,
            "metrics": metrics
        }, output_path)
        
        return {
            "run_name": run_name,
            "result": result,
            "metrics": metrics
        }
    
    def compare_runs(self, run_dirs: List[str]) -> Dict[str, Any]:
        """Compare multiple Asmblr runs."""
        logger.info(f"Comparing {len(run_dirs)} runs")
        
        # Load dataset
        dataset = load_dataset(self.config.dataset_name, self.config.dataset_path)
        if dataset is None:
            raise ValueError(f"Failed to load dataset: {self.config.dataset_name}")
        
        # Evaluate all runs
        results = {}
        for run_dir in run_dirs:
            run_name = Path(run_dir).name
            result = self._evaluate_asmblr_run(run_dir, dataset)
            metrics = compute_all_metrics(
                result, 
                dataset, 
                self.config.metrics,
                self.config
            )
            results[run_name] = {
                "result": result,
                "metrics": metrics
            }
        
        # Generate comparison report
        comparison = self._generate_comparison_report(results, dataset)
        
        # Save comparison
        output_path = self.output_dir / "comparison.json"
        save_json(comparison, output_path)
        
        return comparison
    
    def _evaluate_asmblr_run(self, run_dir: str, dataset: List[Dict]) -> Dict[str, Any]:
        """Evaluate a single Asmblr run against dataset."""
        run_path = Path(run_dir)
        if not run_path.exists():
            raise ValueError(f"Run directory not found: {run_dir}")
        
        result = {
            "run_dir": str(run_path),
            "artifacts": {},
            "missing_artifacts": []
        }
        
        # Load Asmblr artifacts
        artifact_files = {
            "pains_structured": "pains_structured.json",
            "pains_validated": "pains_validated.json", 
            "opportunities": "opportunities.json",
            "opportunities_structured": "opportunities_structured.json",
            "competitor_analysis": "competitor_analysis.json",
            "decision": "decision.md",
            "confidence": "confidence.json",
            "data_source": "data_source.json",
            "prd": "prd.md",
            "tech_spec": "tech_spec.md",
            "landing_page": "landing_page.html",
            "mvp_repo": "mvp_repo"  # Directory
        }
        
        for artifact_name, file_name in artifact_files.items():
            file_path = run_path / file_name
            
            if file_path.exists():
                if file_path.is_dir():
                    # For directories like mvp_repo
                    result["artifacts"][artifact_name] = {
                        "type": "directory",
                        "path": str(file_path),
                        "exists": True,
                        "size": self._get_dir_size(file_path)
                    }
                else:
                    # For files
                    content = self._load_artifact_content(file_path)
                    result["artifacts"][artifact_name] = {
                        "type": "file",
                        "path": str(file_path),
                        "exists": True,
                        "size": file_path.stat().st_size if file_path.exists() else 0,
                        "content": content
                    }
            else:
                result["missing_artifacts"].append(artifact_name)
                result["artifacts"][artifact_name] = {
                    "type": "file",
                    "path": str(file_path),
                    "exists": False
                }
        
        return result
    
    def _load_artifact_content(self, file_path: Path) -> Optional[Any]:
        """Load content from artifact file."""
        try:
            if file_path.suffix == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            elif file_path.suffix in ['.md', '.txt']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif file_path.suffix == '.html':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                # Binary file or unsupported format
                return None
        except Exception as e:
            logger.warning(f"Failed to load artifact {file_path}: {e}")
            return None
    
    def _get_dir_size(self, dir_path: Path) -> int:
        """Get total size of directory."""
        total_size = 0
        try:
            for file_path in dir_path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            logger.warning(f"Failed to calculate directory size for {dir_path}: {e}")
        return total_size
    
    def _aggregate_results(self, metrics_results: Dict[str, Dict]) -> Dict[str, Any]:
        """Aggregate results across runs and compute statistics."""
        aggregated = {
            "runs": list(metrics_results.keys()),
            "metrics_summary": {},
            "bootstrap_results": {},
            "statistical_tests": {}
        }
        
        # Collect metric values across runs
        metric_values = {}
        for run_name, run_metrics in metrics_results.items():
            for metric_name, metric_result in run_metrics.items():
                if metric_name not in metric_values:
                    metric_values[metric_name] = []
                
                if isinstance(metric_result, dict) and "score" in metric_result:
                    metric_values[metric_name].append(metric_result["score"])
                elif hasattr(metric_result, "score"):
                    metric_values[metric_name].append(metric_result.score)
                elif isinstance(metric_result, (int, float)):
                    metric_values[metric_name].append(metric_result)
        
        # Compute summary statistics for each metric
        for metric_name, values in metric_values.items():
            if values:
                import numpy as np
                
                values_array = np.array(values)
                summary = {
                    "mean": float(np.mean(values_array)),
                    "std": float(np.std(values_array)),
                    "min": float(np.min(values_array)),
                    "max": float(np.max(values_array)),
                    "median": float(np.median(values_array)),
                    "count": len(values)
                }
                
                # Bootstrap confidence intervals
                if self.config.bootstrap_samples > 0:
                    from .utils import calculate_bootstrap_confidence_interval
                    ci_lower, ci_upper = calculate_bootstrap_confidence_interval(
                        values, 
                        self.config.confidence_level,
                        self.config.bootstrap_samples
                    )
                    summary["ci_lower"] = ci_lower
                    summary["ci_upper"] = ci_upper
                
                aggregated["metrics_summary"][metric_name] = summary
        
        return aggregated
    
    def _generate_reports(self, dataset: List[Dict], 
                        metrics_results: Dict[str, Dict], 
                        aggregated_results: Dict[str, Any]):
        """Generate all reports."""
        logger.info("Generating reports")
        
        # Generate markdown report
        if self.config.generate_markdown:
            report_path = self.output_dir / "report.md"
            self.report_generator.generate_markdown_report(
                dataset,
                self.config,
                metrics_results,
                aggregated_results,
                report_path
            )
        
        # Generate tables
        self._generate_tables(metrics_results, aggregated_results)
        
        # Generate plots (if requested)
        if self.config.generate_plots:
            self._generate_plots(metrics_results, aggregated_results)
    
    def _generate_tables(self, metrics_results: Dict[str, Dict], 
                        aggregated_results: Dict[str, Any]):
        """Generate CSV tables."""
        # Main results table
        main_table = []
        for run_name, run_metrics in metrics_results.items():
            row = {"run": run_name}
            for metric_name in self.config.metrics:
                if metric_name in run_metrics:
                    metric_result = run_metrics[metric_name]
                    if isinstance(metric_result, dict) and "score" in metric_result:
                        row[metric_name] = metric_result["score"]
                    elif hasattr(metric_result, "score"):
                        row[metric_name] = metric_result.score
                    elif isinstance(metric_result, (int, float)):
                        row[metric_name] = metric_result
                    else:
                        row[metric_name] = None
                else:
                    row[metric_name] = None
            main_table.append(row)
        
        # Save main table
        if main_table:
            import pandas as pd
            df = pd.DataFrame(main_table)
            df.to_csv(self.tables_dir / "results.csv", index=False)
        
        # Summary statistics table
        summary_table = []
        for metric_name, summary in aggregated_results["metrics_summary"].items():
            row = {
                "metric": metric_name,
                "mean": summary["mean"],
                "std": summary["std"],
                "min": summary["min"],
                "max": summary["max"],
                "median": summary["median"],
                "count": summary["count"]
            }
            if "ci_lower" in summary:
                row["ci_lower"] = summary["ci_lower"]
                row["ci_upper"] = summary["ci_upper"]
            summary_table.append(row)
        
        if summary_table:
            import pandas as pd
            df = pd.DataFrame(summary_table)
            df.to_csv(self.tables_dir / "summary.csv", index=False)
    
    def _generate_plots(self, metrics_results: Dict[str, Dict], 
                       aggregated_results: Dict[str, Any]):
        """Generate plots."""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            # Set style
            plt.style.use('default')
            sns.set_palette("husl")
            
            # Metric comparison plot
            self._plot_metric_comparison(metrics_results)
            
            # Distribution plots
            self._plot_metric_distributions(aggregated_results)
            
            logger.info("Generated plots")
            
        except ImportError:
            logger.warning("Matplotlib/Seaborn not available, skipping plots")
    
    def _plot_metric_comparison(self, metrics_results: Dict[str, Dict]):
        """Plot metric comparison across runs."""
        import matplotlib.pyplot as plt
        import pandas as pd
        
        # Prepare data
        data = []
        for run_name, run_metrics in metrics_results.items():
            for metric_name, metric_result in run_metrics.items():
                if isinstance(metric_result, dict) and "score" in metric_result:
                    score = metric_result["score"]
                elif hasattr(metric_result, "score"):
                    score = metric_result.score
                elif isinstance(metric_result, (int, float)):
                    score = metric_result
                else:
                    continue
                
                data.append({
                    "run": run_name,
                    "metric": metric_name,
                    "score": score
                })
        
        if not data:
            return
        
        df = pd.DataFrame(data)
        
        # Create plot
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Group by metric and plot
        for metric in df["metric"].unique():
            metric_data = df[df["metric"] == metric]
            ax.bar(metric_data["run"], metric_data["score"], label=metric, alpha=0.7)
        
        ax.set_xlabel("Run")
        ax.set_ylabel("Score")
        ax.set_title("Metric Comparison Across Runs")
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(self.plots_dir / "metric_comparison.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_metric_distributions(self, aggregated_results: Dict[str, Any]):
        """Plot metric distributions."""
        import matplotlib.pyplot as plt
        import pandas as pd
        
        # Prepare data
        data = []
        for metric_name, summary in aggregated_results["metrics_summary"].items():
            data.append({
                "metric": metric_name,
                "mean": summary["mean"],
                "std": summary["std"],
                "ci_lower": summary.get("ci_lower", summary["mean"]),
                "ci_upper": summary.get("ci_upper", summary["mean"])
            })
        
        if not data:
            return
        
        df = pd.DataFrame(data)
        
        # Create plot
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Plot means with error bars
        x_pos = range(len(df))
        ax.bar(x_pos, df["mean"], yerr=df["std"], capsize=5, alpha=0.7)
        ax.set_xlabel("Metric")
        ax.set_ylabel("Score")
        ax.set_title("Metric Distributions")
        ax.set_xticks(x_pos)
        ax.set_xticklabels(df["metric"], rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(self.plots_dir / "metric_distributions.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _generate_comparison_report(self, results: Dict[str, Dict], 
                                dataset: List[Dict]) -> Dict[str, Any]:
        """Generate comparison report for multiple runs."""
        comparison = {
            "experiment_id": self.config.experiment_id,
            "dataset": self.config.dataset_name,
            "runs": list(results.keys()),
            "comparison_results": {},
            "ranking": {}
        }
        
        # Compare metrics across runs
        metric_values = {}
        for run_name, run_data in results.items():
            metrics = run_data["metrics"]
            for metric_name, metric_result in metrics.items():
                if metric_name not in metric_values:
                    metric_values[metric_name] = {}
                
                if isinstance(metric_result, dict) and "score" in metric_result:
                    metric_values[metric_name][run_name] = metric_result["score"]
                elif hasattr(metric_result, "score"):
                    metric_values[metric_name][run_name] = metric_result.score
                elif isinstance(metric_result, (int, float)):
                    metric_values[metric_name][run_name] = metric_result
        
        # Find best run for each metric
        for metric_name, values in metric_values.items():
            if values:
                best_run = max(values.keys(), key=lambda k: values[k])
                comparison["ranking"][metric_name] = {
                    "best_run": best_run,
                    "best_score": values[best_run],
                    "all_scores": values
                }
        
        return comparison
