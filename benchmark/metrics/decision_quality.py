"""
Decision Quality metric - accuracy of ABORT/KILL/PASS vs ground truth with cost weighting.
"""

from typing import Any
import re

from .base import BaseMetric, MetricResult


class DecisionQuality(BaseMetric):
    """Measures decision quality with weighted error costs."""
    
    requires_ground_truth = True
    output_type = "score"
    
    def __init__(self, config: Any):
        super().__init__(config)
        
        # Error cost weights (false PASS is worst)
        self.error_costs = {
            "false_pass": 1.0,    # PASS when should be KILL/ABORT
            "false_kill": 0.6,    # KILL when should be PASS/ABORT  
            "false_abort": 0.4,   # ABORT when should be PASS/KILL
            "true_pass": 0.0,      # Correct PASS
            "true_kill": 0.0,      # Correct KILL
            "true_abort": 0.0      # Correct ABORT
        }
    
    def compute(self, run_result: dict[str, Any], dataset: list[dict]) -> MetricResult:
        """Compute decision quality metrics."""
        # Extract system decision and confidence
        system_decision, system_confidence = self._extract_system_decision(run_result)
        
        if system_decision is None:
            return MetricResult(
                score=0.0,
                explanation="No decision extracted from system",
                evidence={"system_decision": None}
            )
        
        # Get ground truth decisions
        ground_truth_decisions = self._extract_ground_truth_decisions(dataset)
        
        # Calculate decision accuracy
        accuracy, error_type = self._calculate_decision_accuracy(
            system_decision, ground_truth_decisions
        )
        
        # Calculate confidence calibration
        calibration_score = self._calculate_confidence_calibration(
            system_confidence, system_decision, ground_truth_decisions
        )
        
        # Weighted score combining accuracy and calibration
        base_score = accuracy
        if calibration_score is not None:
            # Penalize overconfidence
            confidence_penalty = max(0.0, system_confidence - accuracy) * 0.2
            base_score = max(0.0, accuracy - confidence_penalty)
        
        explanation = f"Decision quality: Accuracy={accuracy:.3f}, Error={error_type}, Score={base_score:.3f}"
        
        evidence = {
            "system_decision": system_decision,
            "system_confidence": system_confidence,
            "accuracy": accuracy,
            "error_type": error_type,
            "calibration_score": calibration_score
        }
        
        return MetricResult(
            score=base_score,
            explanation=explanation,
            evidence=evidence,
            details={
                "decision_accuracy": accuracy,
                "error_costs": self.error_costs,
                "confidence_calibration": calibration_score
            }
        )
    
    def _extract_system_decision(self, run_result: dict[str, Any]) -> tuple[str, float]:
        """Extract decision and confidence from system output."""
        decision = None
        confidence = 0.5  # Default
        
        # Try decision.md
        decision_md = self._extract_artifact(run_result, "decision")
        if decision_md and isinstance(decision_md, str):
            decision, confidence = self._parse_decision_text(decision_md)
        
        # Try confidence.json
        confidence_json = self._extract_artifact(run_result, "confidence")
        if confidence_json and isinstance(confidence_json, dict):
            confidence = confidence_json.get("confidence", confidence)
            if "decision" in confidence_json:
                decision = confidence_json["decision"]
        
        # Try data_source.json for decision info
        data_source = self._extract_artifact(run_result, "data_source")
        if data_source and isinstance(data_source, dict):
            if "decision" in data_source:
                decision = data_source["decision"]
            if "confidence" in data_source:
                confidence = data_source["confidence"]
        
        return decision, confidence
    
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
        
        # Extract confidence (look for percentage or decimal)
        confidence = 0.5
        confidence_patterns = [
            r'confidence[:\s]*([0-9]+\.?[0-9]*)',
            r'([0-9]+\.?[0-9]*)\s*%.*confidence',
            r'([0-9]+\.?[0-9]*)\s*percent',
            r'confident[:\s]*([0-9]+\.?[0-9]*)'
        ]
        
        for pattern in confidence_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    conf_val = float(match.group(1))
                    if conf_val <= 1.0:
                        confidence = conf_val
                    elif conf_val <= 100:
                        confidence = conf_val / 100
                except ValueError:
                    pass
                break
        
        return decision, confidence
    
    def _extract_ground_truth_decisions(self, dataset: list[dict]) -> list[dict]:
        """Extract ground truth decisions from dataset."""
        decisions = []
        
        for item in dataset:
            gt_decision = self._extract_ground_truth(item, "decision")
            gt_confidence = self._extract_ground_truth(item, "confidence")
            
            if gt_decision:
                decisions.append({
                    "dataset_id": item.get("id"),
                    "decision": gt_decision,
                    "confidence": gt_confidence or 0.5
                })
        
        return decisions
    
    def _calculate_decision_accuracy(self, system_decision: str, 
                                 ground_truth_decisions: list[dict]) -> tuple[float, str]:
        """Calculate decision accuracy and error type."""
        if not ground_truth_decisions:
            return 0.0, "no_ground_truth"
        
        # For simplicity, use the first ground truth decision
        # In a real implementation, you might aggregate multiple decisions
        gt_decision = ground_truth_decisions[0]["decision"]
        
        if system_decision == gt_decision:
            # Correct decision
            error_type = f"true_{system_decision.lower()}"
            accuracy = 1.0
        else:
            # Incorrect decision - determine error type
            if system_decision == "PASS":
                error_type = "false_pass"
            elif system_decision == "KILL":
                error_type = "false_kill"
            elif system_decision == "ABORT":
                error_type = "false_abort"
            else:
                error_type = "unknown_error"
            
            # Base accuracy is 0, but we apply cost weighting
            accuracy = 0.0
        
        return accuracy, error_type
    
    def _calculate_confidence_calibration(self, system_confidence: float,
                                    system_decision: str,
                                    ground_truth_decisions: list[dict]) -> float:
        """Calculate confidence calibration score."""
        if not ground_truth_decisions:
            return None
        
        gt_decision = ground_truth_decisions[0]["decision"]
        
        # Perfect calibration if confidence matches correctness
        is_correct = system_decision == gt_decision
        
        if is_correct:
            # High confidence for correct decision = good calibration
            return system_confidence
        else:
            # Low confidence for incorrect decision = good calibration
            return 1.0 - system_confidence
    
    def get_required_artifacts(self) -> list[str]:
        """Get required artifacts for this metric."""
        return ["decision", "confidence", "data_source"]
    
    def get_required_ground_truth(self) -> list[str]:
        """Get required ground truth fields."""
        return ["decision", "confidence"]
