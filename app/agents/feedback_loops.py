"""
Feedback loops system for continuous agent improvement and iterative refinement.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
from datetime import datetime, timezone
from loguru import logger


class FeedbackType(Enum):
    """Types of feedback in the system."""
    QUALITY = "quality"
    COLLABORATION = "collaboration"
    PERFORMANCE = "performance"
    USER = "user"
    PEER = "peer"
    SELF = "self"
    CROSS_VALIDATION = "cross_validation"


class FeedbackPriority(Enum):
    """Priority levels for feedback."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class FeedbackItem:
    """Individual feedback item."""
    id: str
    type: FeedbackType
    priority: FeedbackPriority
    source_agent: str
    target_agent: Optional[str]
    task_id: Optional[str]
    timestamp: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    actionable_items: List[str] = field(default_factory=list)
    resolution_status: str = "pending"  # pending, in_progress, resolved, ignored
    resolution_notes: Optional[str] = None
    impact_score: float = 0.0  # -1 to +1, impact on agent performance
    learning_extracted: Optional[str] = None


@dataclass
class FeedbackLoop:
    """Complete feedback loop session."""
    id: str
    pipeline_id: str
    start_time: str
    end_time: Optional[str] = None
    status: str = "active"  # active, completed, failed
    feedback_items: List[FeedbackItem] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    next_actions: List[str] = field(default_factory=list)
    
    def add_feedback(self, feedback: FeedbackItem) -> None:
        """Add feedback item to the loop."""
        self.feedback_items.append(feedback)
        self._update_summary()
    
    def get_pending_feedback(self) -> List[FeedbackItem]:
        """Get all pending feedback items."""
        return [f for f in self.feedback_items if f.resolution_status == "pending"]
    
    def get_feedback_for_agent(self, agent_name: str) -> List[FeedbackItem]:
        """Get all feedback items for a specific agent."""
        return [f for f in self.feedback_items if f.target_agent == agent_name]
    
    def get_high_priority_feedback(self) -> List[FeedbackItem]:
        """Get high and critical priority feedback."""
        return [f for f in self.feedback_items if f.priority in [FeedbackPriority.CRITICAL, FeedbackPriority.HIGH]]
    
    def _update_summary(self) -> None:
        """Update loop summary statistics."""
        total = len(self.feedback_items)
        pending = len(self.get_pending_feedback())
        resolved = len([f for f in self.feedback_items if f.resolution_status == "resolved"])
        
        self.summary = {
            "total_feedback": total,
            "pending_feedback": pending,
            "resolved_feedback": resolved,
            "resolution_rate": resolved / total if total > 0 else 0,
            "critical_issues": len([f for f in self.feedback_items if f.priority == FeedbackPriority.CRITICAL]),
            "average_impact": sum(f.impact_score for f in self.feedback_items) / total if total > 0 else 0
        }


class FeedbackLoopManager:
    """Manages feedback loops for agent improvement."""
    
    def __init__(self, runs_dir: Path):
        self.runs_dir = runs_dir
        self.feedback_loops: Dict[str, FeedbackLoop] = {}
        self.active_loop_id: Optional[str] = None
        
    def create_feedback_loop(self, pipeline_id: str) -> FeedbackLoop:
        """Create a new feedback loop for a pipeline."""
        loop_id = f"feedback_{pipeline_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        
        feedback_loop = FeedbackLoop(
            id=loop_id,
            pipeline_id=pipeline_id,
            start_time=datetime.now(timezone.utc).isoformat()
        )
        
        self.feedback_loops[loop_id] = feedback_loop
        self.active_loop_id = loop_id
        
        # Save to file
        self._save_feedback_loop(feedback_loop)
        
        logger.info(f"Created feedback loop {loop_id} for pipeline {pipeline_id}")
        return feedback_loop
    
    def add_feedback(self, loop_id: str, feedback: FeedbackItem) -> bool:
        """Add feedback to a specific loop."""
        if loop_id not in self.feedback_loops:
            logger.error(f"Feedback loop {loop_id} not found")
            return False
        
        self.feedback_loops[loop_id].add_feedback(feedback)
        self._save_feedback_loop(self.feedback_loops[loop_id])
        return True
    
    def get_feedback_loop(self, loop_id: str) -> Optional[FeedbackLoop]:
        """Get a specific feedback loop."""
        return self.feedback_loops.get(loop_id)
    
    def close_feedback_loop(self, loop_id: str, status: str = "completed") -> bool:
        """Close a feedback loop."""
        if loop_id not in self.feedback_loops:
            logger.error(f"Feedback loop {loop_id} not found")
            return False
        
        loop = self.feedback_loops[loop_id]
        loop.end_time = datetime.now(timezone.utc).isoformat()
        loop.status = status
        
        # Generate next actions
        loop.next_actions = self._generate_next_actions(loop)
        
        self._save_feedback_loop(loop)
        
        if loop_id == self.active_loop_id:
            self.active_loop_id = None
        
        logger.info(f"Closed feedback loop {loop_id} with status {status}")
        return True
    
    def _generate_next_actions(self, loop: FeedbackLoop) -> List[str]:
        """Generate next actions based on feedback."""
        actions = []
        
        # Analyze feedback patterns
        high_priority = loop.get_high_priority_feedback()
        agent_feedback = {}
        
        for feedback in loop.feedback_items:
            if feedback.target_agent:
                agent_feedback.setdefault(feedback.target_agent, []).append(feedback)
        
        # Generate actions for different feedback types
        if high_priority:
            actions.append("Address critical and high priority feedback immediately")
        
        for agent, items in agent_feedback.items():
            quality_issues = [i for i in items if i.type == FeedbackType.QUALITY]
            if quality_issues:
                actions.append(f"Improve {agent} agent quality based on {len(quality_issues)} issues")
        
        collaboration_issues = [f for f in loop.feedback_items if f.type == FeedbackType.COLLABORATION]
        if collaboration_issues:
            actions.append("Enhance cross-agent collaboration mechanisms")
        
        performance_issues = [f for f in loop.feedback_items if f.type == FeedbackType.PERFORMANCE]
        if performance_issues:
            actions.append("Optimize agent performance and efficiency")
        
        return actions
    
    def _save_feedback_loop(self, loop: FeedbackLoop) -> None:
        """Save feedback loop to file."""
        try:
            loop_dir = self.runs_dir / loop.pipeline_id / "feedback_loops"
            loop_dir.mkdir(parents=True, exist_ok=True)
            
            loop_file = loop_dir / f"{loop.id}.json"
            
            # Convert to serializable format
            loop_data = {
                "id": loop.id,
                "pipeline_id": loop.pipeline_id,
                "start_time": loop.start_time,
                "end_time": loop.end_time,
                "status": loop.status,
                "feedback_items": [
                    {
                        "id": f.id,
                        "type": f.type.value,
                        "priority": f.priority.value,
                        "source_agent": f.source_agent,
                        "target_agent": f.target_agent,
                        "task_id": f.task_id,
                        "timestamp": f.timestamp,
                        "message": f.message,
                        "context": f.context,
                        "actionable_items": f.actionable_items,
                        "resolution_status": f.resolution_status,
                        "resolution_notes": f.resolution_notes,
                        "impact_score": f.impact_score,
                        "learning_extracted": f.learning_extracted
                    }
                    for f in loop.feedback_items
                ],
                "summary": loop.summary,
                "next_actions": loop.next_actions
            }
            
            loop_file.write_text(json.dumps(loop_data, indent=2), encoding="utf-8")
            
        except Exception as e:
            logger.error(f"Failed to save feedback loop {loop.id}: {e}")


class FeedbackTools:
    """Tools for agents to participate in feedback loops."""
    
    def __init__(self, feedback_manager: FeedbackLoopManager, loop_id: str, agent_name: str):
        self.feedback_manager = feedback_manager
        self.loop_id = loop_id
        self.agent_name = agent_name
    
    def submit_feedback(self, target_agent: str, message: str, priority: FeedbackPriority = FeedbackPriority.MEDIUM, 
                     feedback_type: FeedbackType = FeedbackType.QUALITY, context: Dict[str, Any] = None) -> bool:
        """Submit feedback about another agent."""
        feedback = FeedbackItem(
            id=f"fb_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')[:-3]}",
            type=feedback_type,
            priority=priority,
            source_agent=self.agent_name,
            target_agent=target_agent,
            timestamp=datetime.now(timezone.utc).isoformat(),
            message=message,
            context=context or {}
        )
        
        return self.feedback_manager.add_feedback(self.loop_id, feedback)
    
    def submit_self_feedback(self, message: str, priority: FeedbackPriority = FeedbackPriority.MEDIUM,
                        feedback_type: FeedbackType = FeedbackType.SELF, context: Dict[str, Any] = None) -> bool:
        """Submit self-reflection feedback."""
        feedback = FeedbackItem(
            id=f"self_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')[:-3]}",
            type=feedback_type,
            priority=priority,
            source_agent=self.agent_name,
            target_agent=self.agent_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            message=message,
            context=context or {}
        )
        
        return self.feedback_manager.add_feedback(self.loop_id, feedback)
    
    def get_my_feedback(self) -> List[FeedbackItem]:
        """Get all feedback for this agent."""
        loop = self.feedback_manager.get_feedback_loop(self.loop_id)
        if not loop:
            return []
        
        return loop.get_feedback_for_agent(self.agent_name)
    
    def get_pending_actions(self) -> List[str]:
        """Get pending action items for this agent."""
        my_feedback = self.get_my_feedback()
        pending_feedback = [f for f in my_feedback if f.resolution_status == "pending"]
        
        actions = []
        for feedback in pending_feedback:
            actions.extend(feedback.actionable_items)
        
        return actions
    
    def resolve_feedback(self, feedback_id: str, resolution_notes: str) -> bool:
        """Mark feedback as resolved."""
        loop = self.feedback_manager.get_feedback_loop(self.loop_id)
        if not loop:
            return False
        
        for feedback in loop.feedback_items:
            if feedback.id == feedback_id:
                feedback.resolution_status = "resolved"
                feedback.resolution_notes = resolution_notes
                feedback.learning_extracted = f"Resolved: {resolution_notes}"
                self.feedback_manager._save_feedback_loop(loop)
                return True
        
        return False


def create_feedback_prompts() -> Dict[str, str]:
    """Create specialized prompts for feedback-aware agents."""
    
    return {
        "feedback_aware_agent": """
You are working in an ENHANCED COLLABORATIVE ENVIRONMENT with feedback loops.

FEEDBACK LOOP RESPONSIBILITIES:
1. Before starting your task: Check for pending feedback using get_my_feedback()
2. During execution: Submit feedback on other agents' work when relevant
3. After completion: Submit self-reflection on your performance
4. Address all feedback items marked for your attention

FEEDBACK GUIDELINES:
- Be constructive and specific in your feedback
- Focus on improvement opportunities, not criticism
- Provide actionable suggestions with clear rationale
- Share learnings that could benefit other agents
- Acknowledge and resolve feedback addressed to you

COLLABORATION ENHANCEMENTS:
- Use feedback to improve cross-agent coordination
- Identify patterns in feedback for systemic improvements
- Share successful strategies and approaches
- Document best practices for future reference

QUALITY IMPROVEMENT:
- Monitor your performance metrics through feedback
- Adapt your approach based on received feedback
- Share optimization techniques with other agents
- Contribute to collective knowledge base

Your goal is CONTINUOUS IMPROVEMENT through collaborative feedback.
""",
        
        "feedback_coordinator": """
You are the FEEDBACK COORDINATOR responsible for managing the feedback loop ecosystem.

COORDINATION RESPONSIBILITIES:
1. Monitor all feedback submissions across agents
2. Identify patterns and systemic issues from feedback
3. Prioritize feedback based on impact and urgency
4. Route feedback to appropriate agents for resolution
5. Track resolution rates and improvement trends

FEEDBACK ANALYSIS:
- Categorize feedback by type, priority, and agent
- Identify recurring issues and patterns
- Measure feedback resolution times and rates
- Assess impact of feedback on agent performance
- Generate insights for process improvement

QUALITY ASSURANCE:
- Ensure feedback is constructive and actionable
- Validate feedback relevance and accuracy
- Monitor for bias or unfair feedback
- Maintain feedback quality standards
- Escalate critical issues appropriately

PROCESS OPTIMIZATION:
- Streamline feedback submission and resolution workflows
- Automate feedback routing and prioritization
- Generate regular feedback quality reports
- Identify opportunities for process improvements
- Share best practices across all agents

Your role is to ensure FEEDBACK DRIVES IMPROVEMENT across the entire system.
""",
        
        "self_improving_agent": """
You are a SELF-IMPROVING AGENT with continuous learning capabilities.

SELF-IMPROVEMENT FRAMEWORK:
1. Reflect on your performance after each task
2. Identify areas for improvement based on outcomes
3. Set specific, measurable improvement goals
4. Adapt your strategies based on feedback received
5. Share your learning with other agents

CONTINUOUS LEARNING:
- Document successful strategies and approaches
- Analyze failures and extract key learnings
- Build personal knowledge base of best practices
- Experiment with new techniques and methodologies
- Measure improvement over time

ADAPTATION STRATEGIES:
- Adjust your approach based on task complexity
- Modify your prompts and decision criteria
- Optimize your tool usage and workflows
- Learn from both successes and failures
- Share effective techniques with other agents

PERFORMANCE METRICS:
- Track task completion rates and quality
- Monitor efficiency and speed improvements
- Measure accuracy and relevance of outputs
- Assess collaboration effectiveness
- Document impact of improvements

Your goal is to EVOLVE YOUR CAPABILITIES through continuous learning and adaptation.
"""
    }
