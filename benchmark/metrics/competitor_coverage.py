"""
Competitor Coverage metric - competitor precision/recall vs ground truth.
"""

from typing import Dict, List, Any, Set, Tuple
import re

from .base import BaseMetric, MetricResult


class CompetitorCoverage(BaseMetric):
    """Measures competitor identification quality using precision and recall."""
    
    requires_ground_truth = True
    output_type = "score"
    
    def compute(self, run_result: Dict[str, Any], dataset: List[Dict]) -> MetricResult:
        """Compute competitor coverage metrics."""
        # Extract system competitors
        system_competitors = self._extract_system_competitors(run_result)
        if not system_competitors:
            return MetricResult(
                score=0.0,
                explanation="No competitors extracted by system",
                evidence={"system_competitors_count": 0}
            )
        
        # Get ground truth competitors
        ground_truth_competitors = self._extract_ground_truth_competitors(dataset)
        
        # Compute matches
        matches = self._find_competitor_matches(system_competitors, ground_truth_competitors)
        
        # Calculate metrics
        precision = self._safe_divide(len(matches), len(system_competitors))
        recall = self._safe_divide(len(matches), len(ground_truth_competitors))
        f1 = self._safe_divide(2 * precision * recall, precision + recall)
        
        # Weighted score (emphasize recall slightly for competitor discovery)
        score = 0.4 * precision + 0.6 * recall
        
        explanation = f"Competitor coverage: Precision={precision:.3f}, Recall={recall:.3f}, F1={f1:.3f}"
        
        evidence = {
            "system_competitors_count": len(system_competitors),
            "ground_truth_competitors_count": len(ground_truth_competitors),
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
                "system_competitors": system_competitors[:5],  # First 5 for brevity
                "ground_truth_competitors": ground_truth_competitors[:5]
            }
        )
    
    def _extract_system_competitors(self, run_result: Dict[str, Any]) -> List[Dict]:
        """Extract competitors from system output."""
        competitors = []
        
        # Try competitor_analysis.json
        competitor_analysis = self._extract_artifact(run_result, "competitor_analysis")
        if competitor_analysis:
            if isinstance(competitor_analysis, list):
                competitors.extend(competitor_analysis)
            elif isinstance(competitor_analysis, dict):
                if "competitors" in competitor_analysis:
                    competitors.extend(competitor_analysis["competitors"])
                elif "analysis" in competitor_analysis:
                    analysis = competitor_analysis["analysis"]
                    if isinstance(analysis, dict) and "competitors" in analysis:
                        competitors.extend(analysis["competitors"])
        
        # Try opportunities_structured.json for competitor info
        opportunities = self._extract_artifact(run_result, "opportunities_structured")
        if opportunities and isinstance(opportunities, dict):
            if "competitor_analysis" in opportunities:
                comp_analysis = opportunities["competitor_analysis"]
                if isinstance(comp_analysis, list):
                    competitors.extend(comp_analysis)
        
        # Normalize competitor format
        normalized_competitors = []
        for competitor in competitors:
            normalized = self._normalize_competitor(competitor)
            if normalized:
                normalized_competitors.append(normalized)
        
        return normalized_competitors
    
    def _normalize_competitor(self, competitor: Any) -> Optional[Dict]:
        """Normalize competitor to standard format."""
        if isinstance(competitor, dict):
            return {
                "name": competitor.get("name", ""),
                "positioning": competitor.get("positioning", competitor.get("description", "")),
                "pricing": competitor.get("pricing", competitor.get("price_model", "")),
                "market_share": competitor.get("market_share", ""),
                "strengths": competitor.get("strengths", []),
                "weaknesses": competitor.get("weaknesses", [])
            }
        elif isinstance(competitor, str):
            return {
                "name": competitor,
                "positioning": "",
                "pricing": "",
                "market_share": "",
                "strengths": [],
                "weaknesses": []
            }
        return None
    
    def _extract_ground_truth_competitors(self, dataset: List[Dict]) -> List[Dict]:
        """Extract ground truth competitors from dataset."""
        all_competitors = []
        
        for item in dataset:
            gt_competitors = self._extract_ground_truth(item, "competitors")
            if gt_competitors and isinstance(gt_competitors, list):
                for competitor in gt_competitors:
                    competitor["dataset_id"] = item.get("id")
                    all_competitors.append(competitor)
        
        return all_competitors
    
    def _find_competitor_matches(self, system_competitors: List[Dict], 
                                 ground_truth_competitors: List[Dict],
                                 similarity_threshold: float = 0.7) -> List[Tuple[int, int, float]]:
        """Find matches between system and ground truth competitors."""
        matches = []
        
        for sys_idx, sys_comp in enumerate(system_competitors):
            best_match = None
            best_similarity = 0.0
            best_gt_idx = -1
            
            for gt_idx, gt_comp in enumerate(ground_truth_competitors):
                similarity = self._calculate_competitor_similarity(sys_comp, gt_comp)
                if similarity > best_similarity and similarity >= similarity_threshold:
                    best_similarity = similarity
                    best_match = gt_comp
                    best_gt_idx = gt_idx
            
            if best_match is not None:
                matches.append((sys_idx, best_gt_idx, best_similarity))
        
        return matches
    
    def _calculate_competitor_similarity(self, comp1: Dict, comp2: Dict) -> float:
        """Calculate similarity between two competitors."""
        # Extract text fields
        name1 = comp1.get("name", "").lower()
        name2 = comp2.get("name", "").lower()
        
        positioning1 = comp1.get("positioning", "").lower()
        positioning2 = comp2.get("positioning", "").lower()
        
        pricing1 = comp1.get("pricing", "").lower()
        pricing2 = comp2.get("pricing", "").lower()
        
        # Calculate text similarities
        name_sim = self._text_similarity(name1, name2)
        positioning_sim = self._text_similarity(positioning1, positioning2)
        pricing_sim = self._text_similarity(pricing1, pricing2)
        
        # Weighted average (name is most important)
        similarity = 0.5 * name_sim + 0.3 * positioning_sim + 0.2 * pricing_sim
        
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
    
    def get_required_artifacts(self) -> List[str]:
        """Get required artifacts for this metric."""
        return ["competitor_analysis", "opportunities_structured"]
    
    def get_required_ground_truth(self) -> List[str]:
        """Get required ground truth fields."""
        return ["competitors"]
