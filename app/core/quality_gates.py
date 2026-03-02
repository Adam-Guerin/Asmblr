"""Quality gates for ensuring MVP generation standards."""

import logging
from typing import Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class GateResult(Enum):
    """Result of a quality gate check."""
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass
class QualityGate:
    """Individual quality gate definition."""
    name: str
    threshold: float
    actual_value: float
    result: GateResult
    message: str
    suggestions: list[str] = None


class QualityGateChecker:
    """Checks various quality gates for MVP generation."""
    
    def __init__(self):
        self.gates: list[QualityGate] = []
    
    def check_idea_quality(self, ideas: list[dict[str, Any]]) -> QualityGate:
        """Check if generated ideas meet quality standards."""
        if not ideas:
            return QualityGate(
                name="idea_quality",
                threshold=3.0,
                actual_value=0.0,
                result=GateResult.FAIL,
                message="No ideas generated",
                suggestions=["Check market research sources", "Verify LLM availability", "Review topic specificity"]
            )
        
        avg_score = sum(idea.get('score', 0) for idea in ideas) / len(ideas)
        result = GateResult.PASS if avg_score >= 70 else (GateResult.WARN if avg_score >= 50 else GateResult.FAIL)
        
        suggestions = []
        if result == GateResult.FAIL:
            suggestions = [
                "Increase market research sources",
                "Refine topic specificity",
                "Check competitor analysis quality"
            ]
        elif result == GateResult.WARN:
            suggestions = [
                "Consider additional research sources",
                "Review idea scoring criteria"
            ]
        
        return QualityGate(
            name="idea_quality",
            threshold=70.0,
            actual_value=avg_score,
            result=result,
            message=f"Average idea score: {avg_score:.1f}",
            suggestions=suggestions
        )
    
    def check_market_signal_quality(self, signal_data: dict[str, Any]) -> QualityGate:
        """Check market signal quality and diversity."""
        signal_score = signal_data.get('score', 0)
        sources_count = signal_data.get('sources_count', 0)
        domains_count = signal_data.get('unique_domains', 0)
        
        # Combined quality assessment
        quality_score = (signal_score * 0.6 + min(sources_count * 10, 40) * 0.4)
        result = GateResult.PASS if quality_score >= 60 else (GateResult.WARN if quality_score >= 40 else GateResult.FAIL)
        
        suggestions = []
        if sources_count < 4:
            suggestions.append("Increase number of research sources")
        if domains_count < 3:
            suggestions.append("Ensure diverse domain sources")
        if signal_score < 50:
            suggestions.append("Improve market signal relevance")
        
        return QualityGate(
            name="market_signal_quality",
            threshold=60.0,
            actual_value=quality_score,
            result=result,
            message=f"Market signal quality: {quality_score:.1f} (sources: {sources_count}, domains: {domains_count})",
            suggestions=suggestions
        )
    
    def check_tech_spec_completeness(self, tech_spec: dict[str, Any]) -> QualityGate:
        """Check technical specification completeness."""
        required_sections = ['architecture', 'tech_stack', 'api_design', 'database_schema']
        present_sections = sum(1 for section in required_sections if tech_spec.get(section))
        completeness = (present_sections / len(required_sections)) * 100
        
        result = GateResult.PASS if completeness >= 75 else (GateResult.WARN if completeness >= 50 else GateResult.FAIL)
        
        suggestions = []
        missing_sections = [section for section in required_sections if not tech_spec.get(section)]
        if missing_sections:
            suggestions = [f"Add missing section: {section}" for section in missing_sections]
        
        return QualityGate(
            name="tech_spec_completeness",
            threshold=75.0,
            actual_value=completeness,
            result=result,
            message=f"Tech spec completeness: {completeness:.0f}%",
            suggestions=suggestions
        )
    
    def check_prd_quality(self, prd_data: dict[str, Any]) -> QualityGate:
        """Check PRD quality and completeness."""
        required_elements = ['problem_statement', 'target_audience', 'key_features', 'success_metrics']
        present_elements = sum(1 for element in required_elements if prd_data.get(element))
        completeness = (present_elements / len(required_elements)) * 100
        
        # Check content quality
        problem_length = len(prd_data.get('problem_statement', ''))
        feature_count = len(prd_data.get('key_features', []))
        
        quality_score = completeness * 0.7 + min(problem_length / 500, 1) * 15 + min(feature_count / 5, 1) * 15
        result = GateResult.PASS if quality_score >= 70 else (GateResult.WARN if quality_score >= 50 else GateResult.FAIL)
        
        suggestions = []
        if problem_length < 100:
            suggestions.append("Expand problem statement with more detail")
        if feature_count < 3:
            suggestions.append("Add more key features")
        if completeness < 75:
            suggestions.append("Complete missing PRD sections")
        
        return QualityGate(
            name="prd_quality",
            threshold=70.0,
            actual_value=quality_score,
            result=result,
            message=f"PRD quality score: {quality_score:.1f}",
            suggestions=suggestions
        )
    
    def run_all_checks(self, pipeline_results: dict[str, Any]) -> list[QualityGate]:
        """Run all quality gate checks on pipeline results."""
        self.gates = []
        
        # Check idea quality
        research_data = pipeline_results.get('research', {})
        if 'ideas' in research_data:
            self.gates.append(self.check_idea_quality(research_data['ideas']))
        
        # Check market signal quality
        if 'market_signal' in pipeline_results:
            self.gates.append(self.check_market_signal_quality(pipeline_results['market_signal']))
        
        # Check tech spec completeness
        if 'tech' in pipeline_results:
            self.gates.append(self.check_tech_spec_completeness(pipeline_results['tech']))
        
        # Check PRD quality
        if 'product' in pipeline_results:
            self.gates.append(self.check_prd_quality(pipeline_results['product']))
        
        return self.gates
    
    def get_overall_result(self) -> GateResult:
        """Get overall quality gate result."""
        if not self.gates:
            return GateResult.WARN
        
        failed_count = sum(1 for gate in self.gates if gate.result == GateResult.FAIL)
        warn_count = sum(1 for gate in self.gates if gate.result == GateResult.WARN)
        
        if failed_count > 0:
            return GateResult.FAIL
        elif warn_count > 0:
            return GateResult.WARN
        else:
            return GateResult.PASS
    
    def get_summary(self) -> dict[str, Any]:
        """Get summary of quality gate results."""
        if not self.gates:
            return {"overall": GateResult.WARN, "gates": []}
        
        return {
            "overall": self.get_overall_result(),
            "total_gates": len(self.gates),
            "passed": sum(1 for gate in self.gates if gate.result == GateResult.PASS),
            "warnings": sum(1 for gate in self.gates if gate.result == GateResult.WARN),
            "failed": sum(1 for gate in self.gates if gate.result == GateResult.FAIL),
            "gates": [
                {
                    "name": gate.name,
                    "result": gate.result.value,
                    "threshold": gate.threshold,
                    "actual": gate.actual_value,
                    "message": gate.message,
                    "suggestions": gate.suggestions or []
                }
                for gate in self.gates
            ]
        }
