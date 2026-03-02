"""
Confidence Calibration metric - ECE and Brier score for confidence vs correctness.
"""

from typing import Any
import numpy as np

from .base import BaseMetric, MetricResult


class ConfidenceCalibration(BaseMetric):
    """Measures confidence calibration using ECE and Brier score."""
    
    requires_ground_truth = True
    output_type = "score"
    
    def __init__(self, config: Any):
        super().__init__(config)
        self.n_bins = 10  # Number of bins for reliability diagram
    
    def compute(self, run_result: dict[str, Any], dataset: list[dict]) -> MetricResult:
        """Compute confidence calibration metrics."""
        # Extract system confidence and decision
        system_confidence, system_decision = self._extract_system_confidence_and_decision(run_result)
        
        if system_confidence is None:
            return MetricResult(
                score=0.0,
                explanation="No confidence extracted from system",
                evidence={"system_confidence": None}
            )
        
        # Get ground truth decisions and confidences
        ground_truth_data = self._extract_ground_truth_data(dataset)
        
        if not ground_truth_data:
            return MetricResult(
                score=0.0,
                explanation="No ground truth data available",
                evidence={"ground_truth_count": 0}
            )
        
        # Calculate calibration metrics
        brier_score = self._calculate_brier_score(
            system_confidence, system_decision, ground_truth_data
        )
        
        ece = self._calculate_expected_calibration_error(
            system_confidence, system_decision, ground_truth_data
        )
        
        # Combined calibration score (higher is better)
        # Convert to [0,1] where 1 is perfect calibration
        calibration_score = 1.0 - max(brier_score, ece)
        
        explanation = f"Calibration: Brier={brier_score:.3f}, ECE={ece:.3f}, Score={calibration_score:.3f}"
        
        evidence = {
            "system_confidence": system_confidence,
            "system_decision": system_decision,
            "brier_score": brier_score,
            "expected_calibration_error": ece,
            "calibration_score": calibration_score,
            "ground_truth_count": len(ground_truth_data)
        }
        
        return MetricResult(
            score=calibration_score,
            explanation=explanation,
            evidence=evidence,
            details={
                "brier_score": brier_score,
                "ece": ece,
                "reliability_diagram": self._create_reliability_diagram(
                    system_confidence, system_decision, ground_truth_data
                )
            }
        )
    
    def _extract_system_confidence_and_decision(self, run_result: dict[str, Any]) -> tuple[float, str]:
        """Extract confidence and decision from system output."""
        confidence = None
        decision = None
        
        # Try confidence.json
        confidence_json = self._extract_artifact(run_result, "confidence")
        if confidence_json and isinstance(confidence_json, dict):
            confidence = confidence_json.get("confidence")
            if "decision" in confidence_json:
                decision = confidence_json["decision"]
        
        # Try decision.md
        decision_md = self._extract_artifact(run_result, "decision")
        if decision_md and isinstance(decision_md, str):
            if decision is None:  # Only parse if not already found
                parsed_decision, _ = self._parse_decision_text(decision_md)
                decision = parsed_decision
        
        # Try data_source.json
        data_source = self._extract_artifact(run_result, "data_source")
        if data_source and isinstance(data_source, dict):
            if confidence is None:
                confidence = data_source.get("confidence")
            if decision is None:
                decision = data_source.get("decision")
        
        return confidence, decision
    
    def _parse_decision_text(self, text: str) -> tuple[str, float]:
        """Parse decision and confidence from markdown text."""
        text_lower = text.lower()
        
        # Extract decision
        decision = None
        if "pass" in text_lower:
            decision = "PASS"
        elif "kill" in text_lower:
            decision = "KILL"
        elif "abort" in text_lower:
            decision = "ABORT"
        
        # Default confidence if not found
        confidence = 0.5
        
        return decision, confidence
    
    def _extract_ground_truth_data(self, dataset: list[dict]) -> list[dict]:
        """Extract ground truth decisions and confidences from dataset."""
        data = []
        
        for item in dataset:
            gt_decision = self._extract_ground_truth(item, "decision")
            gt_confidence = self._extract_ground_truth(item, "confidence")
            
            if gt_decision:
                data.append({
                    "dataset_id": item.get("id"),
                    "decision": gt_decision,
                    "confidence": gt_confidence or 0.5
                })
        
        return data
    
    def _calculate_brier_score(self, system_confidence: float, system_decision: str,
                             ground_truth_data: list[dict]) -> float:
        """Calculate Brier score for probability calibration."""
        if not ground_truth_data:
            return 1.0  # Worst possible score
        
        # For single decision case, compare against all ground truth items
        # In practice, you'd have multiple decisions to evaluate
        total_brier = 0.0
        count = 0
        
        for gt_item in ground_truth_data:
            gt_decision = gt_item["decision"]
            gt_confidence = gt_item["confidence"]
            
            # Binary outcome: is system decision correct?
            is_correct = 1 if system_decision == gt_decision else 0
            
            # Use system confidence as predicted probability of correctness
            predicted_prob = system_confidence
            
            # Brier score: (predicted - actual)^2
            brier = (predicted_prob - is_correct) ** 2
            total_brier += brier
            count += 1
        
        return total_brier / count if count > 0 else 1.0
    
    def _calculate_expected_calibration_error(self, system_confidence: float, 
                                          system_decision: str,
                                          ground_truth_data: list[dict]) -> float:
        """Calculate Expected Calibration Error (ECE)."""
        if not ground_truth_data:
            return 1.0
        
        # Create bins for confidence values
        bin_edges = np.linspace(0, 1, self.n_bins + 1)
        bin_indices = np.digitize([system_confidence], bin_edges) - 1
        
        # For single decision case, create synthetic data points
        # In practice, you'd have multiple decisions with different confidences
        confidences = [system_confidence]
        accuracies = []
        
        for gt_item in ground_truth_data:
            is_correct = 1 if system_decision == gt_item["decision"] else 0
            accuracies.append(is_correct)
        
        # Calculate ECE
        ece = 0.0
        for i in range(self.n_bins):
            mask = bin_indices == i
            if np.any(mask):
                bin_confidences = np.array(confidences)[mask]
                bin_accuracies = np.array(accuracies)[mask]
                
                avg_confidence = np.mean(bin_confidences)
                avg_accuracy = np.mean(bin_accuracies)
                bin_weight = len(bin_confidences) / len(confidences)
                
                ece += bin_weight * abs(avg_confidence - avg_accuracy)
        
        return ece
    
    def _create_reliability_diagram(self, system_confidence: float,
                                   system_decision: str,
                                   ground_truth_data: list[dict]) -> list[dict]:
        """Create reliability diagram data."""
        # For single decision case, create simplified diagram
        diagram = []
        
        for gt_item in ground_truth_data:
            is_correct = 1 if system_decision == gt_item["decision"] else 0
            
            diagram.append({
                "confidence": system_confidence,
                "accuracy": is_correct,
                "bin": int(system_confidence * self.n_bins)
            })
        
        return diagram
    
    def get_required_artifacts(self) -> list[str]:
        """Get required artifacts for this metric."""
        return ["confidence", "decision", "data_source"]
    
    def get_required_ground_truth(self) -> list[str]:
        """Get required ground truth fields."""
        return ["decision", "confidence"]
