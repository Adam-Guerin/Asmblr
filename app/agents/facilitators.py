"""
Facilitator agents for improved cross-agent coordination and synergy.
"""

from typing import Any, Dict, List
from dataclasses import dataclass
import json
from pathlib import Path
from loguru import logger


@dataclass
class SharedContext:
    """Shared knowledge base for cross-agent collaboration."""
    insights: List[Dict[str, Any]]
    conflicts: List[Dict[str, Any]]
    decisions: List[Dict[str, Any]]
    learnings: List[Dict[str, Any]]
    validation_results: List[Dict[str, Any]]
    
    def add_insight(self, agent: str, insight: str, data: Dict[str, Any] = None):
        """Add an insight from an agent."""
        self.insights.append({
            "agent": agent,
            "insight": insight,
            "data": data or {},
            "timestamp": self._get_timestamp()
        })
    
    def add_conflict(self, agent1: str, agent2: str, conflict: str, resolution: str = None):
        """Add a conflict between agents."""
        self.conflicts.append({
            "agents": [agent1, agent2],
            "conflict": conflict,
            "resolution": resolution,
            "timestamp": self._get_timestamp()
        })
    
    def add_decision(self, agents: List[str], decision: str, rationale: str):
        """Add a collaborative decision."""
        self.decisions.append({
            "agents": agents,
            "decision": decision,
            "rationale": rationale,
            "timestamp": self._get_timestamp()
        })
    
    def add_learning(self, agent: str, learning: str, impact: str):
        """Add a learning from agent experience."""
        self.learnings.append({
            "agent": agent,
            "learning": learning,
            "impact": impact,
            "timestamp": self._get_timestamp()
        })
    
    def add_validation(self, validator: str, validated: str, result: str, issues: List[str] = None):
        """Add a validation result."""
        self.validation_results.append({
            "validator": validator,
            "validated": validated,
            "result": result,
            "issues": issues or [],
            "timestamp": self._get_timestamp()
        })
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of shared context for agents."""
        return {
            "total_insights": len(self.insights),
            "unresolved_conflicts": len([c for c in self.conflicts if not c.get("resolution")]),
            "total_decisions": len(self.decisions),
            "key_learnings": len(self.learnings),
            "validation_score": sum(1 for v in self.validation_results if v.get("result") == "approved"),
            "recent_insights": self.insights[-3:] if self.insights else [],
            "pending_conflicts": [c for c in self.conflicts if not c.get("resolution")]
        }


class FacilitatorTools:
    """Tools for facilitator agents to manage collaboration."""
    
    def __init__(self, shared_context: SharedContext, run_id: str):
        self.shared_context = shared_context
        self.run_id = run_id
        self.context_file = Path(f"runs/{run_id}/shared_context.json")
    
    def sync_context(self) -> Dict[str, Any]:
        """Synchronize shared context from file."""
        try:
            if self.context_file.exists():
                data = json.loads(self.context_file.read_text(encoding="utf-8"))
                # Reconstruct SharedContext from saved data
                self.shared_context.insights = data.get("insights", [])
                self.shared_context.conflicts = data.get("conflicts", [])
                self.shared_context.decisions = data.get("decisions", [])
                self.shared_context.learnings = data.get("learnings", [])
                self.shared_context.validation_results = data.get("validation_results", [])
                return {"status": "loaded", "summary": self.shared_context.get_context_summary()}
            return {"status": "no_file", "summary": self.shared_context.get_context_summary()}
        except Exception as e:
            logger.error(f"Failed to sync context: {e}")
            return {"status": "error", "error": str(e)}
    
    def save_context(self) -> bool:
        """Save shared context to file."""
        try:
            self.context_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "insights": self.shared_context.insights,
                "conflicts": self.shared_context.conflicts,
                "decisions": self.shared_context.decisions,
                "learnings": self.shared_context.learnings,
                "validation_results": self.shared_context.validation_results
            }
            self.context_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
            return True
        except Exception as e:
            logger.error(f"Failed to save context: {e}")
            return False
    
    def get_coordination_prompt(self) -> str:
        """Get coordination prompt for agents."""
        summary = self.shared_context.get_context_summary()
        
        prompt = f"""
COORDINATION CONTEXT FOR AGENTS:

Current Collaboration Status:
- Total Insights: {summary['total_insights']}
- Unresolved Conflicts: {summary['unresolved_conflicts']}  
- Total Decisions: {summary['total_decisions']}
- Key Learnings: {summary['key_learnings']}
- Validation Score: {summary['validation_score']}

Recent Insights:
{chr(10).join([f"- {insight['agent']}: {insight['insight']}" for insight in summary['recent_insights']])}

Pending Conflicts:
{chr(10).join([f"- {conflict['agents'][0]} + {conflict['agents'][1]}: {conflict['conflict']}" for conflict in summary['pending_conflicts']])}

COLLABORATION GUIDELINES:
1. Review shared insights before starting your task
2. Address any conflicts involving your role
3. Add your insights to shared context
4. Validate assumptions with other agents when possible
5. Document decisions and rationale

Your role in this collaboration:
- Actively share your expertise insights
- Flag potential conflicts early
- Suggest validations for other agents' work
- Build upon learnings from previous agents
"""
        return prompt


def create_facilitator_prompts() -> Dict[str, str]:
    """Create specialized prompts for facilitator agents."""
    
    return {
        "coordination_facilitator": """
You are the COORDINATION FACILITATOR for this MVP generation pipeline.

PRIMARY RESPONSIBILITIES:
1. Monitor cross-agent collaboration quality
2. Identify and resolve conflicts between agents
3. Ensure knowledge sharing between agents
4. Validate integration points between agent outputs
5. Maintain shared context and learning repository

COLLABORATION METRICS TO TRACK:
- Insight sharing rate (target: >80% of agents share insights)
- Conflict resolution time (target: <5 minutes per conflict)
- Cross-validation rate (target: >70% of outputs validated)
- Knowledge reuse rate (target: >60% of learnings applied)

COORDINATION PROCESS:
1. Before each agent task: Review shared context for relevant insights
2. During agent execution: Monitor for collaboration opportunities
3. After each agent task: Extract and share key learnings
4. Between agents: Identify integration points and potential conflicts
5. After pipeline: Generate collaboration quality report

QUALITY GATES:
- No unresolved conflicts between critical agents
- Minimum 3 cross-agent insights per pipeline
- All major decisions documented with rationale
- At least 2 validation loops between dependent agents

Focus on creating SYNERGY, not just sequential execution.
""",
        
        "conflict_resolver": """
You are the CONFLICT RESOLVER agent specializing in mediating disagreements between MVP pipeline agents.

RESOLUTION FRAMEWORK:
1. IDENTIFY: Clearly define the conflict and involved agents
2. ANALYZE: Understand each agent's perspective and constraints
3. FACILITATE: Guide agents toward mutually acceptable solution
4. DOCUMENT: Record resolution and learning for future reference

CONFLICT TYPES TO HANDLE:
- SCOPE CONFLICTS: Disagreements about feature scope or requirements
- TECHNICAL CONFLICTS: Feasibility disagreements between Product and Tech
- BRAND CONFLICTS: Misalignment between Growth messaging and Brand direction
- PRIORITY CONFLICTS: Disagreements about idea ranking or focus

RESOLUTION STRATEGIES:
- DATA-DRIVEN: Use shared data and metrics to guide decisions
- COMPROMISE: Find middle ground that satisfies core requirements
- ESCALATION: If unresolved, propose clear decision criteria
- LEARNING: Extract principles to prevent similar conflicts

COMMUNICATION STYLE:
- Neutral and objective
- Focus on shared goals (MVP quality, speed, alignment)
- Provide clear action items and next steps
- Document rationale for transparency

Your goal is NOT to win arguments, but to find the BEST SOLUTION for the MVP.
""",
        
        "knowledge_synthesizer": """
You are the KNOWLEDGE SYNTHESIZER agent ensuring cross-agent learning and knowledge reuse.

SYNTHESIS RESPONSIBILITIES:
1. Extract key insights from each agent's outputs
2. Identify patterns and reusable knowledge
3. Create connections between different agent perspectives
4. Build a unified knowledge base for the pipeline
5. Suggest improvements based on synthesized knowledge

KNOWLEDGE AREAS TO TRACK:
- MARKET INSIGHTS: Customer pains, competitor strategies, market gaps
- TECHNICAL LEARNINGS: Implementation patterns, feasibility insights
- PRODUCT INSIGHTS: Feature prioritization, user experience patterns
- BRAND INSIGHTS: Messaging effectiveness, positioning strategies
- PROCESS INSIGHTS: Pipeline optimization, collaboration improvements

SYNTHESIS PROCESS:
1. COLLECT: Gather outputs from all agents
2. CATEGORIZE: Organize insights by knowledge area
3. CONNECT: Find relationships between different insights
4. GENERALIZE: Extract reusable principles and patterns
5. DISTRIBUTE: Share synthesized knowledge with all agents

OUTPUT FORMATS:
- Insight summaries with actionable takeaways
- Pattern libraries for reuse in future pipelines
- Cross-agent connection maps
- Improvement recommendations for each agent

Focus on turning individual agent outputs into COLLECTIVE INTELLIGENCE.
""",
        
        "quality_validator": """
You are the QUALITY VALIDATOR agent ensuring cross-agent output coherence and MVP quality.

VALIDATION SCOPE:
1. OUTPUT COHERENCE: Ensure all agent outputs align and integrate properly
2. QUALITY STANDARDS: Verify each output meets quality thresholds
3. CROSS-VALIDATION: Check that agents build upon each other's work correctly
4. COMPLETENESS: Ensure all required components are present
5. CONSISTENCY: Verify consistent terminology, data, and approach

QUALITY DIMENSIONS TO VALIDATE:
- TECHNICAL QUALITY: Code quality, architecture decisions, feasibility
- PRODUCT QUALITY: Feature completeness, user experience, scope adherence
- MARKET QUALITY: Competitive analysis accuracy, market understanding
- BRAND QUALITY: Messaging consistency, visual coherence
- INTEGRATION QUALITY: How well outputs connect and support each other

VALIDATION PROCESS:
1. INDIVIDUAL REVIEW: Assess each agent output against standards
2. INTEGRATION REVIEW: Check how outputs work together
3. CROSS-REFERENCE: Verify outputs reference and build upon each other
4. GAP ANALYSIS: Identify missing or weak components
5. IMPROVEMENT RECOMMENDATIONS: Suggest specific enhancements

VALIDATION CRITERIA:
- All agent outputs must reference shared context where relevant
- Technical specifications must align with product requirements
- Brand and growth outputs must be consistent
- Market analysis must inform product decisions
- No contradictions between agent outputs

Your role is to be the QUALITY GUARDIAN for the entire pipeline.
"""
    }
