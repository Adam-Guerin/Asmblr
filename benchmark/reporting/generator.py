"""
Report generator for creating markdown and JSON reports.
"""

from datetime import datetime
from pathlib import Path
from typing import Any
import json
import logging

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates comprehensive benchmark reports."""
    
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def generate_markdown_report(self, dataset: list[dict], 
                            config: Any,
                            metrics_results: dict[str, dict],
                            aggregated_results: dict[str, Any],
                            output_path: Path):
        """Generate comprehensive markdown report."""
        report_content = self._build_markdown_content(dataset, config, metrics_results, aggregated_results)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Generated markdown report: {output_path}")
    
    def generate_json_summary(self, dataset: list[dict],
                          config: Any,
                          metrics_results: dict[str, dict],
                          aggregated_results: dict[str, Any],
                          output_path: Path):
        """Generate JSON summary report."""
        summary = {
            "metadata": {
                "generated_at": self.timestamp,
                "benchmark_version": "1.0.0",
                "config": config.__dict__ if hasattr(config, '__dict__') else str(config)
            },
            "dataset": {
                "name": config.dataset_name,
                "size": len(dataset),
                "description": self._get_dataset_description(config.dataset_name)
            },
            "results": {
                "runs": list(metrics_results.keys()),
                "metrics_summary": aggregated_results.get("metrics_summary", {}),
                "statistical_tests": aggregated_results.get("statistical_tests", {}),
                "bootstrap_results": aggregated_results.get("bootstrap_results", {})
            },
            "analysis": self._generate_analysis(metrics_results, aggregated_results),
            "recommendations": self._generate_recommendations(metrics_results, aggregated_results)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Generated JSON summary: {output_path}")
    
    def _build_markdown_content(self, dataset: list[dict], 
                             config: Any,
                             metrics_results: dict[str, dict],
                             aggregated_results: dict[str, Any]) -> str:
        """Build the complete markdown report content."""
        content = []
        
        # Header
        content.append("# Asmblr Benchmark Report")
        content.append(f"**Generated:** {self.timestamp}")
        content.append(f"**Dataset:** {config.dataset_name} ({len(dataset)} items)")
        content.append("")
        
        # Research Questions
        content.append("## Research Questions")
        content.append("")
        research_questions = [
            "RQ1: Can autonomous multi-agent systems identify viable market opportunities with accuracy comparable to human entrepreneurs?",
            "RQ2: Does specialized agent architecture outperform monolithic LLM approaches in entrepreneurial tasks?",
            "RQ3: How well do confidence scores correlate with actual market success indicators?",
            "RQ4: What is the optimal balance between exploration (novelty) and exploitation (feasibility) in automated entrepreneurship?"
        ]
        
        for i, rq in enumerate(research_questions, 1):
            content.append(f"{i}. {rq}")
        content.append("")
        
        # Dataset Description
        content.append("## Dataset Description")
        content.append("")
        content.append(f"**Name:** {config.dataset_name}")
        content.append(f"**Size:** {len(dataset)} items")
        content.append(f"**Description:** {self._get_dataset_description(config.dataset_name)}")
        content.append("")
        
        # Metric Definitions
        content.append("## Metric Definitions")
        content.append("")
        metric_definitions = {
            "Pain Extraction Quality": "Precision, recall, and F1 score for pain point extraction vs ground truth",
            "Pain Specificity Score": "Rule-based scoring penalizing generic pains and rewarding specific, actionable descriptions",
            "Clustering Quality": "Adjusted Rand Index comparing system clusters to ground truth groupings",
            "Idea Novelty": "TF-IDF cosine distance measuring novelty vs known ideas corpus",
            "Feasibility Score": "Heuristic rubric assessing technical and economic feasibility",
            "Competitor Coverage": "Precision/recall for competitor identification vs ground truth",
            "Decision Quality": "Accuracy of ABORT/KILL/PASS decisions with weighted error costs",
            "Confidence Calibration": "Expected Calibration Error (ECE) and Brier score for confidence vs correctness",
            "PRD Completeness": "Checklist score for required PRD sections (ICP, JTBD, user stories, etc.)",
            "Tech Spec Actionability": "Checklist score for technical specification completeness",
            "Artifact Coverage": "Percentage of required artifacts produced by the system"
        }
        
        for metric, definition in metric_definitions.items():
            if metric in config.metrics:
                content.append(f"### {metric}")
                content.append(f"{definition}")
                content.append("")
        
        # Results Table
        content.append("## Results")
        content.append("")
        content.append("| Run | " + " | ".join(config.metrics) + " |")
        content.append("|------|" + "|------" * len(config.metrics) + "|")
        
        for run_name, run_metrics in metrics_results.items():
            row = [run_name]
            for metric in config.metrics:
                if metric in run_metrics:
                    metric_result = run_metrics[metric]
                    if isinstance(metric_result, dict) and "score" in metric_result:
                        score = f"{metric_result['score']:.3f}"
                    elif hasattr(metric_result, "score"):
                        score = f"{metric_result.score:.3f}"
                    elif isinstance(metric_result, (int, float)):
                        score = f"{metric_result:.3f}"
                    else:
                        score = "N/A"
                else:
                    score = "N/A"
                row.append(score)
            else:
                row.append("N/A")
            
            content.append("| " + " | ".join(row) + " |")
        
        content.append("")
        
        # Statistical Summary
        if "metrics_summary" in aggregated_results:
            content.append("## Statistical Summary")
            content.append("")
            
            for metric, summary in aggregated_results["metrics_summary"].items():
                if metric in config.metrics:
                    content.append(f"### {metric}")
                    content.append(f"- **Mean:** {summary.get('mean', 0):.3f}")
                    content.append(f"- **Std:** {summary.get('std', 0):.3f}")
                    content.append(f"- **Min:** {summary.get('min', 0):.3f}")
                    content.append(f"- **Max:** {summary.get('max', 0):.3f}")
                    if "ci_lower" in summary and "ci_upper" in summary:
                        content.append(f"- **95% CI:** [{summary['ci_lower']:.3f}, {summary['ci_upper']:.3f}]")
                    content.append("")
        
        # Analysis and Findings
        content.append("## Analysis and Findings")
        content.append("")
        analysis = self._generate_analysis(metrics_results, aggregated_results)
        content.extend(analysis)
        content.append("")
        
        # Recommendations
        content.append("## Recommendations")
        content.append("")
        recommendations = self._generate_recommendations(metrics_results, aggregated_results)
        content.extend(recommendations)
        content.append("")
        
        # Failure Mode Analysis
        content.append("## Failure Mode Analysis")
        content.append("")
        failure_analysis = self._analyze_failure_modes(metrics_results, config)
        content.extend(failure_analysis)
        content.append("")
        
        # Conclusion
        content.append("## Conclusion")
        content.append("")
        conclusion = self._generate_conclusion(aggregated_results)
        content.extend(conclusion)
        
        return "\n".join(content)
    
    def _get_dataset_description(self, dataset_name: str) -> str:
        """Get description for dataset."""
        descriptions = {
            "toy_pains_v1": "Small hand-labeled dataset with clear ground truth for testing and development",
            "synthetic_market_v1": "Programmatically generated dataset with controllable noise levels",
            "realistic_corpus_v1": "Curated realistic text samples with expert annotations"
        }
        return descriptions.get(dataset_name, "Custom dataset")
    
    def _generate_analysis(self, metrics_results: dict[str, dict], 
                        aggregated_results: dict[str, Any]) -> list[str]:
        """Generate analysis of results."""
        analysis = []
        
        # Overall performance analysis
        if "metrics_summary" in aggregated_results:
            high_performing_metrics = []
            low_performing_metrics = []
            
            for metric, summary in aggregated_results["metrics_summary"].items():
                mean_score = summary.get("mean", 0)
                if mean_score > 0.7:
                    high_performing_metrics.append(metric)
                elif mean_score < 0.4:
                    low_performing_metrics.append(metric)
            
            if high_performing_metrics:
                analysis.append(f"**Strong Performance:** {', '.join(high_performing_metrics)}")
            
            if low_performing_metrics:
                analysis.append(f"**Areas for Improvement:** {', '.join(low_performing_metrics)}")
        
        # Comparative analysis
        if len(metrics_results) > 1:
            best_run = max(metrics_results.keys(), 
                        key=lambda x: self._get_overall_score(metrics_results[x]))
            analysis.append(f"**Best Performing Run:** {best_run}")
        
        return analysis
    
    def _generate_recommendations(self, metrics_results: dict[str, dict], 
                              aggregated_results: dict[str, Any]) -> list[str]:
        """Generate recommendations based on results."""
        recommendations = []
        
        if "metrics_summary" not in aggregated_results:
            return recommendations
        
        # Metric-specific recommendations
        for metric, summary in aggregated_results["metrics_summary"].items():
            mean_score = summary.get("mean", 0)
            
            if metric == "pain_extraction_quality" and mean_score < 0.6:
                recommendations.append("Improve pain point extraction through better NLP techniques and domain-specific training")
            
            elif metric == "idea_novelty" and mean_score < 0.5:
                recommendations.append("Enhance idea generation to avoid common patterns and increase novelty")
            
            elif metric == "decision_quality" and mean_score < 0.7:
                recommendations.append("Refine decision-making logic and improve confidence calibration")
            
            elif metric == "confidence_calibration" and mean_score < 0.6:
                recommendations.append("Implement better confidence estimation and calibration techniques")
            
            elif metric == "artifact_coverage" and mean_score < 0.8:
                recommendations.append("Ensure all required artifacts are generated and contain meaningful content")
        
        # General recommendations
        recommendations.extend([
            "Continue monitoring and evaluation on diverse datasets",
            "Implement automated testing and validation pipelines",
            "Consider human-in-the-loop validation for critical decisions"
        ])
        
        return recommendations[:10]  # Top 10 recommendations
    
    def _analyze_failure_modes(self, metrics_results: dict[str, dict], config: Any) -> list[str]:
        """Analyze failure modes from metrics."""
        failure_modes = []
        
        for run_name, run_metrics in metrics_results.items():
            issues = []
            
            for metric, result in run_metrics.items():
                if isinstance(result, dict) and "score" in result:
                    score = result["score"]
                    
                    if metric == "pain_extraction_quality" and score < 0.3:
                        issues.append("Poor pain extraction")
                    elif metric == "idea_novelty" and score < 0.3:
                        issues.append("Low idea novelty")
                    elif metric == "decision_quality" and score < 0.3:
                        issues.append("Poor decision accuracy")
                    elif metric == "confidence_calibration" and score < 0.3:
                        issues.append("Poor confidence calibration")
                    elif metric == "artifact_coverage" and score < 0.5:
                        issues.append("Missing artifacts")
            
            if issues:
                failure_modes.append(f"**{run_name}:** {', '.join(issues)}")
        
        return failure_modes
    
    def _generate_conclusion(self, aggregated_results: dict[str, Any]) -> list[str]:
        """Generate conclusion from results."""
        conclusions = []
        
        if "metrics_summary" in aggregated_results:
            # Calculate overall performance
            all_means = [summary.get("mean", 0) for summary in aggregated_results["metrics_summary"].values()]
            overall_mean = sum(all_means) / len(all_means) if all_means else 0
            
            if overall_mean > 0.7:
                conclusions.append("System demonstrates strong performance across most metrics")
            elif overall_mean > 0.5:
                conclusions.append("System shows moderate performance with room for improvement")
            else:
                conclusions.append("System requires significant improvements to meet benchmark standards")
        
        conclusions.extend([
            "Benchmark provides comprehensive evaluation of entrepreneurial AI capabilities",
            "Results indicate specific areas for system enhancement and optimization"
        ])
        
        return conclusions
    
    def _get_overall_score(self, run_metrics: dict[str, dict]) -> float:
        """Calculate overall score for a run."""
        scores = []
        for metric, result in run_metrics.items():
            if isinstance(result, dict) and "score" in result:
                scores.append(result["score"])
            elif hasattr(result, "score"):
                scores.append(result.score)
            elif isinstance(result, (int, float)):
                scores.append(result)
        
        return sum(scores) / len(scores) if scores else 0.0
