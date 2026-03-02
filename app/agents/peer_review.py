"""
Peer Review System for agent collaboration and quality assurance.
"""

from typing import Any
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
from datetime import datetime, UTC
from loguru import logger


class ReviewType(Enum):
    """Types of peer reviews."""
    CODE_REVIEW = "code_review"
    OUTPUT_REVIEW = "output_review"
    METHODOLOGY_REVIEW = "methodology_review"
    QUALITY_REVIEW = "quality_review"
    COLLABORATION_REVIEW = "collaboration_review"
    PERFORMANCE_REVIEW = "performance_review"
    VALIDATION_REVIEW = "validation_review"


class ReviewStatus(Enum):
    """Status of peer reviews."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUIRED = "revision_required"


class ReviewPriority(Enum):
    """Priority levels for reviews."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ReviewCriterion:
    """Individual criterion for peer review."""
    id: str
    name: str
    description: str
    weight: float = 1.0
    score_type: str = "scale_1_5"  # scale_1_5, binary, percentage
    required: bool = True
    min_score: float = 0.0


@dataclass
class ReviewScore:
    """Score for a specific review criterion."""
    criterion_id: str
    score: float
    comments: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


@dataclass
class PeerReview:
    """Complete peer review session."""
    id: str
    review_type: ReviewType
    reviewer_agent: str
    reviewee_agent: str
    task_id: str | None
    artifact_id: str | None
    artifact_type: str
    title: str
    description: str
    criteria: list[ReviewCriterion]
    scores: list[ReviewScore] = field(default_factory=list)
    overall_score: float = 0.0
    status: ReviewStatus = ReviewStatus.PENDING
    priority: ReviewPriority = ReviewPriority.MEDIUM
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    completed_at: str | None = None
    review_duration: int | None = None  # in seconds
    comments: str = ""
    recommendations: list[str] = field(default_factory=list)
    approval_conditions: list[str] = field(default_factory=list)
    revision_requests: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def calculate_overall_score(self) -> float:
        """Calculate overall score based on criteria weights."""
        if not self.scores:
            return 0.0
        
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for score in self.scores:
            # Find corresponding criterion
            criterion = next((c for c in self.criteria if c.id == score.criterion_id), None)
            if criterion:
                total_weighted_score += score.score * criterion.weight
                total_weight += criterion.weight
        
        return total_weighted_score / total_weight if total_weight > 0 else 0.0
    
    def add_score(self, criterion_id: str, score: float, comments: str = "", 
                 evidence: dict[str, Any] = None, confidence: float = 1.0) -> None:
        """Add a score for a specific criterion."""
        review_score = ReviewScore(
            criterion_id=criterion_id,
            score=score,
            comments=comments,
            evidence=evidence or {},
            confidence=confidence
        )
        self.scores.append(review_score)
        self.overall_score = self.calculate_overall_score()
        self.updated_at = datetime.now(UTC).isoformat()
    
    def get_score_for_criterion(self, criterion_id: str) -> ReviewScore | None:
        """Get score for a specific criterion."""
        return next((s for s in self.scores if s.criterion_id == criterion_id), None)
    
    def get_passed_criteria(self) -> list[ReviewCriterion]:
        """Get criteria that passed minimum score."""
        passed = []
        for score in self.scores:
            criterion = next((c for c in self.criteria if c.id == score.criterion_id), None)
            if criterion and score.score >= criterion.min_score:
                passed.append(criterion)
        return passed
    
    def get_failed_criteria(self) -> list[ReviewCriterion]:
        """Get criteria that failed minimum score."""
        failed = []
        for score in self.scores:
            criterion = next((c for c in self.criteria if c.id == score.criterion_id), None)
            if criterion and score.score < criterion.min_score:
                failed.append(criterion)
        return failed


@dataclass
class ReviewAssignment:
    """Assignment of peer review to an agent."""
    id: str
    review_id: str
    assigned_agent: str
    assigned_by: str
    assigned_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    due_at: str | None = None
    accepted_at: str | None = None
    status: str = "assigned"  # assigned, accepted, declined, completed
    priority: ReviewPriority = ReviewPriority.MEDIUM
    context: dict[str, Any] = field(default_factory=dict)


class PeerReviewManager:
    """Manages peer review system for agents."""
    
    def __init__(self, reviews_dir: Path):
        self.reviews_dir = reviews_dir
        self.reviews_dir.mkdir(parents=True, exist_ok=True)
        self.reviews: dict[str, PeerReview] = {}
        self.assignments: dict[str, ReviewAssignment] = {}
        self.review_criteria_templates: dict[str, list[ReviewCriterion]] = {}
        self._load_reviews()
        self._load_criteria_templates()
    
    def create_review(self, review_type: ReviewType, reviewer_agent: str, reviewee_agent: str,
                    artifact_id: str, artifact_type: str, title: str, description: str,
                    criteria: list[ReviewCriterion], priority: ReviewPriority = ReviewPriority.MEDIUM,
                    task_id: str = None) -> str:
        """Create a new peer review."""
        review_id = f"review_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{len(self.reviews)}"
        
        review = PeerReview(
            id=review_id,
            review_type=review_type,
            reviewer_agent=reviewer_agent,
            reviewee_agent=reviewee_agent,
            task_id=task_id,
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            title=title,
            description=description,
            criteria=criteria,
            priority=priority
        )
        
        self.reviews[review_id] = review
        self._save_review(review)
        
        logger.info(f"Created peer review {review_id}: {title} ({reviewer_agent} -> {reviewee_agent})")
        return review_id
    
    def assign_review(self, review_id: str, assigned_agent: str, assigned_by: str,
                   due_at: str = None, priority: ReviewPriority = ReviewPriority.MEDIUM) -> str:
        """Assign a peer review to an agent."""
        assignment_id = f"assign_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{len(self.assignments)}"
        
        assignment = ReviewAssignment(
            id=assignment_id,
            review_id=review_id,
            assigned_agent=assigned_agent,
            assigned_by=assigned_by,
            due_at=due_at,
            priority=priority
        )
        
        self.assignments[assignment_id] = assignment
        self._save_assignment(assignment)
        
        logger.info(f"Assigned review {review_id} to {assigned_agent}")
        return assignment_id
    
    def accept_review_assignment(self, assignment_id: str) -> bool:
        """Accept a peer review assignment."""
        if assignment_id not in self.assignments:
            return False
        
        assignment = self.assignments[assignment_id]
        assignment.status = "accepted"
        assignment.accepted_at = datetime.now(UTC).isoformat()
        
        self._save_assignment(assignment)
        logger.info(f"Agent {assignment.assigned_agent} accepted review assignment {assignment_id}")
        return True
    
    def submit_review(self, review_id: str, scores: list[dict[str, Any]], comments: str = "",
                   recommendations: list[str] = None, approval_conditions: list[str] = None,
                   revision_requests: list[str] = None) -> bool:
        """Submit a completed peer review."""
        if review_id not in self.reviews:
            return False
        
        review = self.reviews[review_id]
        
        # Add scores
        for score_data in scores:
            review.add_score(
                criterion_id=score_data["criterion_id"],
                score=score_data["score"],
                comments=score_data.get("comments", ""),
                evidence=score_data.get("evidence", {}),
                confidence=score_data.get("confidence", 1.0)
            )
        
        # Update review metadata
        review.comments = comments
        review.recommendations = recommendations or []
        review.approval_conditions = approval_conditions or []
        review.revision_requests = revision_requests or []
        review.status = ReviewStatus.COMPLETED
        review.completed_at = datetime.now(UTC).isoformat()
        
        # Calculate duration
        if review.accepted_at:
            start_time = datetime.fromisoformat(review.accepted_at.replace('Z', '+00:00'))
            end_time = datetime.now(UTC)
            review.review_duration = int((end_time - start_time).total_seconds())
        
        # Determine approval status
        failed_criteria = review.get_failed_criteria()
        if not failed_criteria:
            review.status = ReviewStatus.APPROVED
        elif len(failed_criteria) <= len(review.criteria) * 0.2:  # Less than 20% failed
            review.status = ReviewStatus.REVISION_REQUIRED
        else:
            review.status = ReviewStatus.REJECTED
        
        self._save_review(review)
        
        logger.info(f"Submitted review {review_id} with status {review.status.value}")
        return True
    
    def get_review(self, review_id: str) -> PeerReview | None:
        """Get a specific peer review."""
        return self.reviews.get(review_id)
    
    def get_reviews_for_agent(self, agent_name: str, as_reviewer: bool = True) -> list[PeerReview]:
        """Get all reviews for a specific agent."""
        reviews = list(self.reviews.values())
        
        if as_reviewer:
            return [r for r in reviews if r.reviewer_agent == agent_name]
        else:
            return [r for r in reviews if r.reviewee_agent == agent_name]
    
    def get_pending_reviews(self, agent_name: str = None) -> list[PeerReview]:
        """Get pending peer reviews."""
        reviews = list(self.reviews.values())
        
        if agent_name:
            return [r for r in reviews 
                    if r.status == ReviewStatus.PENDING and 
                    (r.reviewer_agent == agent_name or r.reviewee_agent == agent_name)]
        else:
            return [r for r in reviews if r.status == ReviewStatus.PENDING]
    
    def get_review_statistics(self, agent_name: str = None) -> dict[str, Any]:
        """Get peer review statistics."""
        reviews = list(self.reviews.values())
        
        if agent_name:
            reviews = [r for r in reviews 
                       if r.reviewer_agent == agent_name or r.reviewee_agent == agent_name]
        
        stats = {
            "total_reviews": len(reviews),
            "by_status": {},
            "by_type": {},
            "by_priority": {},
            "average_score": 0.0,
            "average_duration": 0,
            "completion_rate": 0.0,
            "approval_rate": 0.0,
            "top_reviewers": {},
            "top_reviewees": {}
        }
        
        if not reviews:
            return stats
        
        # Calculate statistics
        completed_reviews = [r for r in reviews if r.status in [ReviewStatus.COMPLETED, ReviewStatus.APPROVED, ReviewStatus.REJECTED, ReviewStatus.REVISION_REQUIRED]]
        approved_reviews = [r for r in reviews if r.status == ReviewStatus.APPROVED]
        
        stats["completion_rate"] = len(completed_reviews) / len(reviews)
        stats["approval_rate"] = len(approved_reviews) / len(completed_reviews) if completed_reviews else 0
        
        # By status
        for review in reviews:
            status = review.status.value
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
        
        # By type
        for review in reviews:
            rtype = review.review_type.value
            stats["by_type"][rtype] = stats["by_type"].get(rtype, 0) + 1
        
        # By priority
        for review in reviews:
            priority = review.priority.value
            stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1
        
        # Average scores and duration
        if completed_reviews:
            stats["average_score"] = sum(r.overall_score for r in completed_reviews) / len(completed_reviews)
            durations = [r.review_duration for r in completed_reviews if r.review_duration]
            stats["average_duration"] = sum(durations) / len(durations) if durations else 0
        
        # Top reviewers and reviewees
        for review in reviews:
            reviewer = review.reviewer_agent
            reviewee = review.reviewee_agent
            stats["top_reviewers"][reviewer] = stats["top_reviewers"].get(reviewer, 0) + 1
            stats["top_reviewees"][reviewee] = stats["top_reviewees"].get(reviewee, 0) + 1
        
        return stats
    
    def get_criteria_template(self, template_name: str) -> list[ReviewCriterion]:
        """Get a criteria template by name."""
        return self.review_criteria_templates.get(template_name, [])
    
    def _save_review(self, review: PeerReview) -> None:
        """Save a peer review to file."""
        try:
            review_file = self.reviews_dir / f"{review.id}.json"
            
            # Convert to serializable format
            review_data = {
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
                "scores": [
                    {
                        "criterion_id": s.criterion_id,
                        "score": s.score,
                        "comments": s.comments,
                        "evidence": s.evidence,
                        "confidence": s.confidence
                    }
                    for s in review.scores
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
            
            review_file.write_text(json.dumps(review_data, indent=2), encoding="utf-8")
            
        except Exception as e:
            logger.error(f"Failed to save review {review.id}: {e}")
    
    def _save_assignment(self, assignment: ReviewAssignment) -> None:
        """Save a review assignment to file."""
        try:
            assignment_file = self.reviews_dir / f"assignment_{assignment.id}.json"
            
            assignment_data = {
                "id": assignment.id,
                "review_id": assignment.review_id,
                "assigned_agent": assignment.assigned_agent,
                "assigned_by": assignment.assigned_by,
                "assigned_at": assignment.assigned_at,
                "due_at": assignment.due_at,
                "accepted_at": assignment.accepted_at,
                "status": assignment.status,
                "priority": assignment.priority.value,
                "context": assignment.context
            }
            
            assignment_file.write_text(json.dumps(assignment_data, indent=2), encoding="utf-8")
            
        except Exception as e:
            logger.error(f"Failed to save assignment {assignment.id}: {e}")
    
    def _load_reviews(self) -> None:
        """Load all peer reviews from files."""
        try:
            for review_file in self.reviews_dir.glob("review_*.json"):
                try:
                    review_data = json.loads(review_file.read_text(encoding="utf-8"))
                    
                    # Convert back to PeerReview
                    criteria = [
                        ReviewCriterion(
                            id=c["id"],
                            name=c["name"],
                            description=c["description"],
                            weight=c.get("weight", 1.0),
                            score_type=c.get("score_type", "scale_1_5"),
                            required=c.get("required", True),
                            min_score=c.get("min_score", 0.0)
                        )
                        for c in review_data.get("criteria", [])
                    ]
                    
                    scores = [
                        ReviewScore(
                            criterion_id=s["criterion_id"],
                            score=s["score"],
                            comments=s.get("comments", ""),
                            evidence=s.get("evidence", {}),
                            confidence=s.get("confidence", 1.0)
                        )
                        for s in review_data.get("scores", [])
                    ]
                    
                    review = PeerReview(
                        id=review_data["id"],
                        review_type=ReviewType(review_data["review_type"]),
                        reviewer_agent=review_data["reviewer_agent"],
                        reviewee_agent=review_data["reviewee_agent"],
                        task_id=review_data.get("task_id"),
                        artifact_id=review_data["artifact_id"],
                        artifact_type=review_data["artifact_type"],
                        title=review_data["title"],
                        description=review_data["description"],
                        criteria=criteria,
                        scores=scores,
                        overall_score=review_data.get("overall_score", 0.0),
                        status=ReviewStatus(review_data.get("status", "pending")),
                        priority=ReviewPriority(review_data.get("priority", "medium")),
                        created_at=review_data.get("created_at"),
                        updated_at=review_data.get("updated_at"),
                        completed_at=review_data.get("completed_at"),
                        review_duration=review_data.get("review_duration"),
                        comments=review_data.get("comments", ""),
                        recommendations=review_data.get("recommendations", []),
                        approval_conditions=review_data.get("approval_conditions", []),
                        revision_requests=review_data.get("revision_requests", []),
                        metadata=review_data.get("metadata", {})
                    )
                    
                    self.reviews[review.id] = review
                    
                except Exception as e:
                    logger.error(f"Failed to load review {review_file}: {e}")
            
            logger.info(f"Loaded {len(self.reviews)} peer reviews")
            
        except Exception as e:
            logger.error(f"Failed to load reviews: {e}")
    
    def _load_criteria_templates(self) -> None:
        """Load review criteria templates."""
        # Define standard criteria templates
        self.review_criteria_templates = {
            "code_review": [
                ReviewCriterion(
                    id="code_quality",
                    name="Code Quality",
                    description="Overall quality, readability, and maintainability of code",
                    weight=0.3,
                    min_score=3.0
                ),
                ReviewCriterion(
                    id="functionality",
                    name="Functionality",
                    description="Code meets functional requirements and works as expected",
                    weight=0.4,
                    min_score=3.0
                ),
                ReviewCriterion(
                    id="best_practices",
                    name="Best Practices",
                    description="Follows industry best practices and coding standards",
                    weight=0.2,
                    min_score=3.0
                ),
                ReviewCriterion(
                    id="documentation",
                    name="Documentation",
                    description="Code is properly documented and self-explanatory",
                    weight=0.1,
                    min_score=2.0
                )
            ],
            "output_review": [
                ReviewCriterion(
                    id="accuracy",
                    name="Accuracy",
                    description="Output is factually correct and reliable",
                    weight=0.4,
                    min_score=3.0
                ),
                ReviewCriterion(
                    id="completeness",
                    name="Completeness",
                    description="Output addresses all requirements comprehensively",
                    weight=0.3,
                    min_score=3.0
                ),
                ReviewCriterion(
                    id="clarity",
                    name="Clarity",
                    description="Output is clear, well-structured, and easy to understand",
                    weight=0.2,
                    min_score=3.0
                ),
                ReviewCriterion(
                    id="relevance",
                    name="Relevance",
                    description="Output is relevant to the task and context",
                    weight=0.1,
                    min_score=3.0
                )
            ],
            "methodology_review": [
                ReviewCriterion(
                    id="soundness",
                    name="Methodology Soundness",
                    description="Approach is logically sound and well-reasoned",
                    weight=0.4,
                    min_score=3.0
                ),
                ReviewCriterion(
                    id="efficiency",
                    name="Efficiency",
                    description="Methodology is efficient and optimized",
                    weight=0.3,
                    min_score=3.0
                ),
                ReviewCriterion(
                    id="scalability",
                    name="Scalability",
                    description="Approach can scale to larger contexts",
                    weight=0.2,
                    min_score=2.0
                ),
                ReviewCriterion(
                    id="innovation",
                    name="Innovation",
                    description="Methodology shows creative or innovative thinking",
                    weight=0.1,
                    min_score=2.0
                )
            ]
        }
