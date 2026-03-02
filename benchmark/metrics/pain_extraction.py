"""
Pain Extraction Quality metric - precision/recall/F1 vs ground truth pains.
"""

from typing import Any
import re

from .base import BaseMetric, MetricResult


class PainExtractionQuality(BaseMetric):
    """Measures precision, recall, and F1 score for pain point extraction."""
    
    requires_ground_truth = True
    output_type = "score"
    
    def compute(self, run_result: dict[str, Any], dataset: list[dict]) -> MetricResult:
        """Compute pain extraction quality metrics."""
        # Extract system pains
        system_pains = self._extract_system_pains(run_result)
        if not system_pains:
            return MetricResult(
                score=0.0,
                explanation="No pains extracted by system",
                evidence={"system_pains_count": 0}
            )
        
        # Get ground truth pains
        ground_truth_pains = self._extract_ground_truth_pains(dataset)
        
        # Compute matches
        matches = self._find_pain_matches(system_pains, ground_truth_pains)
        
        # Calculate metrics
        precision = self._safe_divide(len(matches), len(system_pains))
        recall = self._safe_divide(len(matches), len(ground_truth_pains))
        f1 = self._safe_divide(2 * precision * recall, precision + recall)
        
        # Weighted score (emphasize recall slightly)
        score = 0.4 * precision + 0.6 * recall
        
        explanation = f"Pain extraction: Precision={precision:.3f}, Recall={recall:.3f}, F1={f1:.3f}"
        
        evidence = {
            "system_pains_count": len(system_pains),
            "ground_truth_pains_count": len(ground_truth_pains),
            "matches_count": len(matches),
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "matches": [{"system_idx": m[0], "gt_idx": m[1], "similarity": m[2]} for m in matches]
        }
        
        return MetricResult(
            score=score,
            explanation=explanation,
            evidence=evidence,
            details={
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "system_pains": system_pains[:5],  # First 5 for brevity
                "ground_truth_pains": ground_truth_pains[:5]
            }
        )
    
    def _extract_system_pains(self, run_result: dict[str, Any]) -> list[dict]:
        """Extract pains from system output."""
        pains = []
        
        # Try pains_structured.json
        structured_pains = self._extract_artifact(run_result, "pains_structured")
        if structured_pains:
            if isinstance(structured_pains, list):
                pains.extend(structured_pains)
            elif isinstance(structured_pains, dict) and "pains" in structured_pains:
                pains.extend(structured_pains["pains"])
        
        # Try pains_validated.json
        validated_pains = self._extract_artifact(run_result, "pains_validated")
        if validated_pains:
            if isinstance(validated_pains, list):
                pains.extend(validated_pains)
            elif isinstance(validated_pains, dict) and "pains" in validated_pains:
                pains.extend(validated_pains["pains"])
        
        # Normalize pain format
        normalized_pains = []
        for pain in pains:
            normalized = self._normalize_pain(pain)
            if normalized:
                normalized_pains.append(normalized)
        
        return normalized_pains
    
    def _normalize_pain(self, pain: Any) -> Optional[dict]:
        """Normalize pain to standard format."""
        if isinstance(pain, dict):
            return {
                "actor": pain.get("actor", ""),
                "context": pain.get("context", ""),
                "problem": pain.get("problem", ""),
                "severity": pain.get("severity", 1)
            }
        elif isinstance(pain, str):
            # Extract from text
            return {
                "actor": "unknown",
                "context": "unknown", 
                "problem": pain,
                "severity": 1
            }
        return None
    
    def _extract_ground_truth_pains(self, dataset: list[dict]) -> list[dict]:
        """Extract ground truth pains from dataset."""
        all_pains = []
        
        for item in dataset:
            gt_pains = self._extract_ground_truth(item, "pains")
            if gt_pains and isinstance(gt_pains, list):
                for pain in gt_pains:
                    pain["dataset_id"] = item.get("id")
                    all_pains.append(pain)
        
        return all_pains
    
    def _find_pain_matches(self, system_pains: list[dict], 
                           ground_truth_pains: list[dict],
                           similarity_threshold: float = 0.7) -> list[tuple[int, int, float]]:
        """Find matches between system and ground truth pains using fuzzy matching."""
        matches = []
        
        for sys_idx, sys_pain in enumerate(system_pains):
            best_match = None
            best_similarity = 0.0
            best_gt_idx = -1
            
            for gt_idx, gt_pain in enumerate(ground_truth_pains):
                similarity = self._calculate_pain_similarity(sys_pain, gt_pain)
                if similarity > best_similarity and similarity >= similarity_threshold:
                    best_similarity = similarity
                    best_match = gt_pain
                    best_gt_idx = gt_idx
            
            if best_match is not None:
                matches.append((sys_idx, best_gt_idx, best_similarity))
        
        return matches
    
    def _calculate_pain_similarity(self, pain1: dict, pain2: dict) -> float:
        """Calculate similarity between two pains."""
        # Extract text fields
        actor1 = pain1.get("actor", "").lower()
        actor2 = pain2.get("actor", "").lower()
        
        context1 = pain1.get("context", "").lower()
        context2 = pain2.get("context", "").lower()
        
        problem1 = pain1.get("problem", "").lower()
        problem2 = pain2.get("problem", "").lower()
        
        # Calculate text similarities
        actor_sim = self._text_similarity(actor1, actor2)
        context_sim = self._text_similarity(context1, context2)
        problem_sim = self._text_similarity(problem1, problem2)
        
        # Severity similarity
        severity1 = pain1.get("severity", 1)
        severity2 = pain2.get("severity", 1)
        severity_sim = 1.0 - abs(severity1 - severity2) / 4.0  # Normalize to [0,1]
        
        # Weighted average
        similarity = 0.3 * actor_sim + 0.3 * context_sim + 0.3 * problem_sim + 0.1 * severity_sim
        
        return similarity
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using Jaccard similarity."""
        if not text1 or not text2:
            return 0.0
        
        # Tokenize
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))
        
        # Jaccard similarity
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def get_required_artifacts(self) -> list[str]:
        """Get required artifacts for this metric."""
        return ["pains_structured", "pains_validated"]
    
    def get_required_ground_truth(self) -> list[str]:
        """Get required ground truth fields."""
        return ["pains"]
