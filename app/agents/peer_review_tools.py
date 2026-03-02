"""
Peer Review Tools for agents to conduct and participate in reviews.
"""

from typing import Any
from loguru import logger

from app.agents.peer_review import (
    PeerReviewManager,
    ReviewType,
    ReviewPriority
)


class PeerReviewTools:
    """Tools for agents to participate in peer review system."""
    
    def __init__(self, review_manager: PeerReviewManager, agent_name: str):
        self.review_manager = review_manager
        self.agent_name = agent_name
    
    def get_my_review_assignments(self, status: str = None) -> list[dict[str, Any]]:
        """Get review assignments for this agent."""
        try:
            assignments = [a for a in self.review_manager.assignments.values() 
                         if a.assigned_agent == self.agent_name]
            
            if status:
                assignments = [a for a in assignments if a.status == status]
            
            return [
                {
                    "id": assignment.id,
                    "review_id": assignment.review_id,
                    "assigned_by": assignment.assigned_by,
                    "assigned_at": assignment.assigned_at,
                    "due_at": assignment.due_at,
                    "accepted_at": assignment.accepted_at,
                    "status": assignment.status,
                    "priority": assignment.priority.value,
                    "context": assignment.context
                }
                for assignment in assignments
            ]
            
        except Exception as e:
            logger.error(f"Failed to get review assignments for {self.agent_name}: {e}")
            return []
    
    def get_review_details(self, review_id: str) -> dict[str, Any] | None:
        """Get detailed information about a specific review."""
        try:
            review = self.review_manager.get_review(review_id)
            if not review:
                return None
            
            return {
                "id": review.id,
                "review_type": review.review_type.value,
                "reviewer_agent": review.reviewer_agent,
                "reviewee_agent": review.reviewee_agent,
                "task_id": review.task_id,
                "artifact_id": review.artifact_id,
                "artifact_type": review.artifact_type,
                "title": review.title,
                "description": review.description,
                "criteria": [
                    {
                        "id": c.id,
                        "name": c.name,
                        "description": c.description,
                        "weight": c.weight,
                        "score_type": c.score_type,
                        "required": c.required,
                        "min_score": c.min_score
                    }
                    for c in review.criteria
                ],
                "overall_score": review.overall_score,
                "status": review.status.value,
                "priority": review.priority.value,
                "created_at": review.created_at,
                "updated_at": review.updated_at,
                "completed_at": review.completed_at,
                "review_duration": review.review_duration,
                "comments": review.comments,
                "recommendations": review.recommendations,
                "approval_conditions": review.approval_conditions,
                "revision_requests": review.revision_requests,
                "metadata": review.metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to get review details {review_id}: {e}")
            return None
    
    def accept_review_assignment(self, assignment_id: str) -> bool:
        """Accept a peer review assignment."""
        try:
            return self.review_manager.accept_review_assignment(assignment_id)
        except Exception as e:
            logger.error(f"Failed to accept review assignment {assignment_id}: {e}")
            return False
    
    def submit_review(self, review_id: str, scores: list[dict[str, Any]], 
                   comments: str = "", recommendations: list[str] = None,
                   approval_conditions: list[str] = None, 
                   revision_requests: list[str] = None) -> bool:
        """Submit a completed peer review."""
        try:
            return self.review_manager.submit_review(
                review_id=review_id,
                scores=scores,
                comments=comments,
                recommendations=recommendations,
                approval_conditions=approval_conditions,
                revision_requests=revision_requests
            )
        except Exception as e:
            logger.error(f"Failed to submit review {review_id}: {e}")
            return False
    
    def request_review(self, review_type: str, reviewee_agent: str, artifact_id: str,
                    artifact_type: str, title: str, description: str,
                    criteria_template: str = None, priority: str = "medium",
                    task_id: str = None) -> str | None:
        """Request a peer review for an artifact."""
        try:
            # Get criteria template
            if criteria_template:
                criteria = self.review_manager.get_criteria_template(criteria_template)
            else:
                # Use default criteria based on review type
                criteria = self.review_manager.get_criteria_template(
                    f"{review_type}_review"
                )
            
            review_id = self.review_manager.create_review(
                review_type=ReviewType(review_type),
                reviewer_agent=None,  # Will be assigned by system
                reviewee_agent=reviewee_agent,
                artifact_id=artifact_id,
                artifact_type=artifact_type,
                title=title,
                description=description,
                criteria=criteria,
                priority=ReviewPriority(priority),
                task_id=task_id
            )
            
            logger.info(f"Requested review {review_id} for {artifact_id}")
            return review_id
            
        except Exception as e:
            logger.error(f"Failed to request review: {e}")
            return None
    
    def get_my_reviews(self, as_reviewer: bool = True, status: str = None) -> list[dict[str, Any]]:
        """Get reviews involving this agent."""
        try:
            reviews = self.review_manager.get_reviews_for_agent(self.agent_name, as_reviewer)
            
            if status:
                reviews = [r for r in reviews if r.status.value == status]
            
            return [
                {
                    "id": review.id,
                    "review_type": review.review_type.value,
                    "other_agent": review.reviewee_agent if as_reviewer else review.reviewer_agent,
                    "task_id": review.task_id,
                    "artifact_id": review.artifact_id,
                    "artifact_type": review.artifact_type,
                    "title": review.title,
                    "description": review.description,
                    "overall_score": review.overall_score,
                    "status": review.status.value,
                    "priority": review.priority.value,
                    "created_at": review.created_at,
                    "completed_at": review.completed_at,
                    "review_duration": review.review_duration,
                    "comments": review.comments,
                    "recommendations": review.recommendations,
                    "approval_conditions": review.approval_conditions,
                    "revision_requests": review.revision_requests
                }
                for review in reviews
            ]
            
        except Exception as e:
            logger.error(f"Failed to get reviews for {self.agent_name}: {e}")
            return []
    
    def get_review_statistics(self) -> dict[str, Any]:
        """Get peer review statistics for this agent."""
        try:
            return self.review_manager.get_review_statistics(self.agent_name)
        except Exception as e:
            logger.error(f"Failed to get review statistics for {self.agent_name}: {e}")
            return {}
    
    def get_pending_reviews_for_my_artifacts(self) -> list[dict[str, Any]]:
        """Get pending reviews for artifacts created by this agent."""
        try:
            pending_reviews = self.review_manager.get_pending_reviews(self.agent_name)
            
            return [
                {
                    "id": review.id,
                    "review_type": review.review_type.value,
                    "reviewer_agent": review.reviewer_agent,
                    "title": review.title,
                    "description": review.description,
                    "artifact_id": review.artifact_id,
                    "artifact_type": review.artifact_type,
                    "priority": review.priority.value,
                    "created_at": review.created_at,
                    "criteria_count": len(review.criteria)
                }
                for review in pending_reviews
                if review.reviewee_agent == self.agent_name
            ]
            
        except Exception as e:
            logger.error(f"Failed to get pending reviews for {self.agent_name}: {e}")
            return []
    
    def get_criteria_templates(self) -> dict[str, list[dict[str, Any]]]:
        """Get available review criteria templates."""
        try:
            templates = {}
            for template_name, criteria in self.review_manager.review_criteria_templates.items():
                templates[template_name] = [
                    {
                        "id": c.id,
                        "name": c.name,
                        "description": c.description,
                        "weight": c.weight,
                        "score_type": c.score_type,
                        "required": c.required,
                        "min_score": c.min_score
                    }
                    for c in criteria
                ]
            return templates
            
        except Exception as e:
            logger.error(f"Failed to get criteria templates: {e}")
            return {}


def create_peer_review_prompts() -> dict[str, str]:
    """Create specialized prompts for peer review-aware agents."""
    
    return {
        "peer_review_aware_agent": """
You are working in a PEER REVIEW-ENHANCED ENVIRONMENT with quality assurance through collaborative review.

PEER REVIEW RESPONSIBILITIES:
1. Before submitting work: Request peer review for quality assurance
2. During review assignments: Conduct thorough, constructive reviews
3. After receiving reviews: Address feedback and improve your work
4. Participate actively in the peer review community
5. Help maintain high quality standards across all agent outputs

REVIEW CONDUCT GUIDELINES:
- Be objective, fair, and constructive in all reviews
- Use the provided criteria consistently and transparently
- Provide specific, actionable feedback with evidence
- Balance criticism with recognition of good work
- Focus on improving the work, not criticizing the agent
- Suggest concrete improvements and best practices

REVIEW PARTICIPATION:
- Accept review assignments that match your expertise
- Complete reviews thoroughly and on time
- Provide detailed scoring with clear rationale
- Share your expertise to help other agents improve
- Contribute to the collective quality improvement

QUALITY ASSURANCE:
- Request reviews for important or complex work
- Use peer feedback to improve your methodologies
- Learn from reviews conducted on other agents' work
- Share successful techniques and approaches discovered through reviews
- Help maintain high standards across the entire system

Your goal is to CONTRIBUTE TO COLLECTIVE QUALITY through peer review participation.
""",
        
        "review_coordinator": """
You are the PEER REVIEW COORDINATOR responsible for managing the review ecosystem.

COORDINATION RESPONSIBILITIES:
1. Assign appropriate reviewers based on expertise and availability
2. Monitor review progress and ensure timely completion
3. Balance review workload across all agents
4. Identify and address review quality issues
5. Maintain review criteria templates and standards

REVIEW ASSIGNMENT STRATEGY:
- Match reviewers with appropriate expertise domains
- Consider agent workload and availability
- Balance review assignments to prevent bottlenecks
- Prioritize critical or high-impact reviews
- Ensure diverse perspectives in review assignments

QUALITY MONITORING:
- Monitor review quality and consistency
- Identify and address bias or unfair reviews
- Track review completion rates and timeliness
- Ensure criteria are applied consistently
- Maintain high standards for review conduct

PROCESS OPTIMIZATION:
- Streamline review assignment and completion workflows
- Identify opportunities for automation and efficiency
- Optimize criteria templates for different review types
- Generate insights on review effectiveness and impact
- Facilitate knowledge sharing through reviews

SYSTEM HEALTH:
- Monitor overall review system performance
- Identify agents needing additional training or support
- Track quality improvements from review participation
- Generate recommendations for system enhancements
- Maintain balance between quality assurance and efficiency

Your role is to ensure the PEER REVIEW SYSTEM delivers maximum quality improvement value.
""",
        
        "quality_focused_agent": """
You are a QUALITY-FOCUSED AGENT with commitment to excellence through peer review.

QUALITY-FIRST APPROACH:
1. Seek peer review proactively for all important work
2. Treat all feedback as opportunities for improvement
3. Implement review recommendations systematically
4. Share quality improvements with the community
5. Strive for continuous quality enhancement

REVIEW INTEGRATION:
- Request reviews early in the development process
- Provide clear context and requirements for reviewers
- Be receptive to constructive criticism and suggestions
- Implement review feedback thoroughly and thoughtfully
- Share lessons learned from review experiences

QUALITY METRICS:
- Track your quality improvement over time
- Monitor review scores and feedback patterns
- Identify areas needing consistent improvement
- Celebrate quality achievements and milestones
- Contribute to collective quality standards

COLLABORATIVE EXCELLENCE:
- Help other agents improve through constructive reviews
- Share quality best practices and techniques
- Participate in quality improvement initiatives
- Contribute to criteria and standards development
- Mentor other agents in quality achievement

CONTINUOUS IMPROVEMENT:
- Use review feedback to refine your methodologies
- Develop personal quality standards and checklists
- Learn from both positive and negative review experiences
- Share successful quality improvement strategies
- Contribute to the collective quality culture

Your goal is to ACHIEVE AND MAINTAIN EXCELLENCE through peer review integration.
"""
    }
