"""
Tech Spec Actionability metric - checklist score for technical specification completeness.
"""

from typing import Any
import re

from .base import BaseMetric, MetricResult


class TechSpecActionability(BaseMetric):
    """Measures tech spec actionability using checklist scoring."""
    
    requires_ground_truth = False
    output_type = "score"
    
    def __init__(self, config: Any):
        super().__init__(config)
        
        # Required tech spec sections
        self.required_sections = {
            "architecture": {
                "keywords": ["architecture", "system design", "components", "modules", "layers"],
                "weight": 0.2
            },
            "data_model": {
                "keywords": ["data model", "database schema", "entities", "relationships", "tables"],
                "weight": 0.2
            },
            "endpoints": {
                "keywords": ["api", "endpoints", "routes", "interfaces", "methods"],
                "weight": 0.15
            },
            "deployment": {
                "keywords": ["deployment", "infrastructure", "environment", "hosting", "scaling"],
                "weight": 0.15
            },
            "risks": {
                "keywords": ["risks", "risk", "challenges", "limitations", "dependencies"],
                "weight": 0.15
            },
            "testing": {
                "keywords": ["testing", "tests", "unit tests", "integration", "quality assurance"],
                "weight": 0.15
            }
        }
    
    def compute(self, run_result: dict[str, Any], dataset: list[dict]) -> MetricResult:
        """Compute tech spec actionability score."""
        # Extract tech spec content
        tech_spec_content = self._extract_tech_spec_content(run_result)
        
        if not tech_spec_content:
            return MetricResult(
                score=0.0,
                explanation="No tech spec content found",
                evidence={"tech_spec_exists": False}
            )
        
        # Calculate section scores
        section_scores = {}
        total_score = 0.0
        total_weight = 0.0
        
        for section_name, section_config in self.required_sections.items():
            score, evidence = self._calculate_section_score(tech_spec_content, section_config)
            section_scores[section_name] = {
                "score": score,
                "evidence": evidence,
                "weight": section_config["weight"]
            }
            
            total_score += score * section_config["weight"]
            total_weight += section_config["weight"]
        
        # Normalize score
        actionability_score = total_score / total_weight if total_weight > 0 else 0.0
        
        explanation = f"Tech spec actionability: {actionability_score:.3f} (sections found: {sum(1 for s in section_scores.values() if s['score'] > 0.5)}/{len(section_scores)})"
        
        evidence = {
            "tech_spec_exists": True,
            "actionability_score": actionability_score,
            "section_scores": section_scores,
            "sections_present": sum(1 for s in section_scores.values() if s['score'] > 0.5),
            "total_sections": len(section_scores)
        }
        
        return MetricResult(
            score=actionability_score,
            explanation=explanation,
            evidence=evidence,
            details={
                "section_analysis": section_scores,
                "missing_sections": [name for name, score in section_scores.items() if score["score"] < 0.3]
            }
        )
    
    def _extract_tech_spec_content(self, run_result: dict[str, Any]) -> str:
        """Extract tech spec content from system output."""
        # Try tech_spec.md
        tech_spec_md = self._extract_artifact(run_result, "tech_spec")
        if tech_spec_md and isinstance(tech_spec_md, str):
            return tech_spec_md
        
        return ""
    
    def _calculate_section_score(self, content: str, section_config: dict) -> tuple[float, list[str]]:
        """Calculate score for a specific section."""
        content_lower = content.lower()
        keywords = section_config["keywords"]
        
        # Look for section indicators
        found_keywords = []
        keyword_scores = []
        
        for keyword in keywords:
            if keyword in content_lower:
                # Check if it's a substantial mention
                keyword_score = self._assess_keyword_substance(content_lower, keyword)
                keyword_scores.append(keyword_score)
                found_keywords.append(keyword)
        
        # Calculate section score based on keyword presence and substance
        if not keyword_scores:
            return 0.0, []
        
        # Average keyword scores
        avg_keyword_score = sum(keyword_scores) / len(keyword_scores)
        
        # Boost score if multiple keywords found
        keyword_diversity = len(set(found_keywords)) / len(keywords)
        final_score = avg_keyword_score * (0.7 + 0.3 * keyword_diversity)
        
        return final_score, found_keywords
    
    def _assess_keyword_substance(self, content: str, keyword: str) -> float:
        """Assess how substantially a keyword is discussed."""
        # Find all occurrences of keyword
        keyword_pattern = re.compile(rf'\b{re.escape(keyword)}\b', re.IGNORECASE)
        matches = list(keyword_pattern.finditer(content))
        
        if not matches:
            return 0.0
        
        # Score based on context around each match
        context_scores = []
        context_window = 150  # Characters before and after each match
        
        for match in matches:
            start = max(0, match.start() - context_window)
            end = min(len(content), match.end() + context_window)
            context = content[start:end]
            
            # Check for substantive discussion indicators
            substance_indicators = [
                "definition", "description", "example", "specifically",
                "including", "such as", "features", "requirements",
                "implementation", "architecture", "design", "components"
            ]
            
            context_score = 0.3  # Base score for finding keyword
            
            for indicator in substance_indicators:
                if indicator in context.lower():
                    context_score += 0.2
            
            # Length of discussion (longer is better)
            discussion_length = len(context.split())
            if discussion_length > 15:
                context_score += 0.1
            if discussion_length > 30:
                context_score += 0.1
            
            context_scores.append(min(1.0, context_score))
        
        # Return average context score
        return sum(context_scores) / len(context_scores) if context_scores else 0.0
    
    def get_required_artifacts(self) -> list[str]:
        """Get required artifacts for this metric."""
        return ["tech_spec"]
    
    def get_required_ground_truth(self) -> list[str]:
        """Get required ground truth fields."""
        return []
