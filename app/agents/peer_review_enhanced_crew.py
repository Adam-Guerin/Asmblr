"""
Peer Review Enhanced crew system with collaborative quality assurance.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

try:
    from crewai import Agent, Task, Crew
except Exception:  # pragma: no cover
    Agent = None
    Task = None
    Crew = None

from app.core.config import Settings
from app.core.llm import LLMClient
from app.agents.peer_review import PeerReviewManager, ReviewType, ReviewPriority
from app.agents.peer_review_tools import PeerReviewTools, create_peer_review_prompts
from app.langchain_tools import build_toolbox


def _create_peer_review_enhanced_agent(
    role: str,
    goal: str,
    backstory: str,
    tools: List[Any],
    peer_review_tools: PeerReviewTools,
    peer_review_prompt: str
) -> Agent:
    """Create an agent with peer review capabilities."""
    
    enhanced_backstory = f"""
{backstory}

PEER REVIEW INTEGRATION:
You have access to a peer review system for collaborative quality assurance.
Before submitting important work, request peer review for validation.
When assigned reviews, conduct thorough, constructive evaluations.
Use peer feedback to continuously improve your work quality.
Participate actively in maintaining high standards across all agent outputs.

{peer_review_prompt}
"""
    
    try:
        return Agent(role=role, goal=goal, backstory=enhanced_backstory, tools=tools, llm=llm_client._client)
    except Exception:
        return Agent(role=role, goal=goal, backstory=enhanced_backstory, tools=[], llm=llm_client._client)


def run_peer_review_enhanced_crewai_pipeline(
    topic: str,
    settings: Settings,
    llm_client: LLMClient,
    run_id: str,
    n_ideas: int,
    fast_mode: bool,
    seed_pages: list[dict[str, Any]] | None = None,
    seed_competitor_pages: list[dict[str, Any]] | None = None,
    seed_inputs: Any = None,
    validated_pains: list[str] | None = None,
) -> dict[str, Any]:
    """Run enhanced CrewAI pipeline with peer review system."""
    
    if Agent is None or Task is None or Crew is None:
        logger.warning("CrewAI not available; returning empty outputs")
        return {"errors": "CrewAI not available"}
    
    # Initialize peer review system
    reviews_dir = settings.runs_dir / run_id / "peer_reviews"
    review_manager = PeerReviewManager(reviews_dir)
    
    # Build toolbox with peer review tools
    base_toolbox = build_toolbox(settings, llm_client)
    peer_review_prompts = create_peer_review_prompts()
    
    # Create peer review-enhanced agents
    def _mk_peer_review_agent(role, goal, backstory, tools):
        peer_review_tools = PeerReviewTools(review_manager, role)
        
        # Add peer review tools to agent toolbox
        enhanced_tools = tools + [
            peer_review_tools.get_my_review_assignments,
            peer_review_tools.get_review_details,
            peer_review_tools.accept_review_assignment,
            peer_review_tools.submit_review,
            peer_review_tools.request_review,
            peer_review_tools.get_my_reviews,
            peer_review_tools.get_review_statistics,
            peer_review_tools.get_pending_reviews_for_my_artifacts,
            peer_review_tools.get_criteria_templates
        ]
        
        return _create_peer_review_enhanced_agent(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=enhanced_tools,
            peer_review_tools=peer_review_tools,
            peer_review_prompt=peer_review_prompts["peer_review_aware_agent"]
        )
    
    # Core agents with peer review integration
    researcher = _mk_peer_review_agent(
        role="Researcher",
        goal="Collect signals, extract pains, cluster, and generate product ideas with peer review quality assurance.",
        backstory="Signal analyst committed to quality through collaborative review.",
        tools=[base_toolbox["web"], base_toolbox["rag"]]
    )
    
    analyst = _mk_peer_review_agent(
        role="Analyst",
        goal="Score ideas, evaluate competition, and pick top opportunities with peer review validation.",
        backstory="Quant-minded evaluator ensuring quality through peer review.",
        tools=[base_toolbox["scoring"], base_toolbox["competitor"]]
    )
    
    product = _mk_peer_review_agent(
        role="Product",
        goal="Produce a clear PRD with ICP/JTBD/MVP scope validated through peer review.",
        backstory="Product strategist ensuring quality through collaborative review.",
        tools=[base_toolbox["rag"]]
    )
    
    tech = _mk_peer_review_agent(
        role="Tech Lead",
        goal="Write technical spec and generate buildable repo skeleton with peer review quality assurance.",
        backstory="Senior engineer committed to quality through peer review.",
        tools=[base_toolbox["repo"]]
    )
    
    growth = _mk_peer_review_agent(
        role="Growth",
        goal="Generate landing copy and content pack validated through peer review.",
        backstory="Growth marketer ensuring quality through collaborative review.",
        tools=[base_toolbox["landing"], base_toolbox["content"]]
    )
    
    brand = _mk_peer_review_agent(
        role="Brand",
        goal="Define project identity with peer review quality validation.",
        backstory="Brand strategist committed to quality through peer review.",
        tools=[]
    )
    
    # Review coordinator agent
    review_coordinator = _mk_peer_review_agent(
        role="Review Coordinator",
        goal="Manage peer review ecosystem and ensure quality standards.",
        backstory=peer_review_prompts["review_coordinator"],
        tools=[]
    )
    
    # Quality-focused agents
    def _mk_quality_focused_agent(role, goal, backstory, tools):
        return _create_peer_review_enhanced_agent(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools,
            peer_review_tools=PeerReviewTools(review_manager, role),
            peer_review_prompt=peer_review_prompts["quality_focused_agent"]
        )
    
    # Create peer review-enhanced tasks
    def _create_peer_review_enhanced_task(agent, description, context_tasks=None):
        """Create task with peer review integration."""
        enhanced_description = f"""
{description}

PEER REVIEW INTEGRATION:
1. Before submitting important work: Use request_review() for quality validation
2. During execution: Check get_my_review_assignments() for pending reviews
3. Use get_review_details() to access review assignments and conduct thorough reviews
4. After receiving reviews: Use feedback to improve your approach and outputs
5. Use get_my_reviews() to track your review history and quality trends

QUALITY ASSURANCE PROCESS:
- Request reviews for complex or high-impact work
- Conduct reviews objectively using provided criteria templates
- Provide constructive, specific feedback with clear recommendations
- Use review feedback to systematically improve your work quality
- Share quality improvements and best practices discovered

COLLABORATIVE EXCELLENCE:
- Participate actively in the peer review community
- Help maintain high quality standards across all agent outputs
- Share your expertise to help other agents improve
- Contribute to collective quality improvement and standards
- Balance quality assurance with efficiency and collaboration

Focus on ACHIEVING EXCELLENCE through collaborative peer review.
"""
        
        return Task(
            description=enhanced_description,
            agent=agent,
            context=context_tasks or [],
            expected_output="JSON"
        )
    
    # Load sources and configuration
    sources = _load_sources(settings)
    sources_json = json.dumps(sources, indent=2)
    
    # Create peer review-enhanced tasks
    research_task = _create_peer_review_enhanced_task(
        researcher,
        description=f"""
You are Peer Review-Enhanced Researcher.

ENHANCED RESEARCH PROCESS:
1. Use request_review() to get peer validation for research methodologies
2. Use get_my_review_assignments() to check for review requests
3. Conduct thorough reviews using get_review_details() when assigned
4. Use web_search_and_summarize with sources: {sources_json}
5. Use peer feedback to improve research quality and methodologies

QUALITY-DRIVEN RESEARCH:
- Research methodology validation through peer review
- Signal quality assessment with collaborative verification
- Pain extraction patterns validated by peer feedback
- Clustering approaches improved through review insights
- Research efficiency optimization from peer recommendations

PEER REVIEW PARTICIPATION:
- Provide constructive feedback on other agents' research work
- Share research best practices and methodologies
- Help maintain high research quality standards
- Contribute to collective research excellence
- Learn from peer reviews to enhance your own work

Your research will benefit from and contribute to collaborative quality assurance.
"""
    )
    
    analyst_task = _create_peer_review_enhanced_task(
        analyst,
        description=f"""
You are Peer Review-Enhanced Analyst.

ENHANCED ANALYSIS PROCESS:
1. Use request_review() to validate scoring methodologies with peers
2. Use get_my_review_assignments() to participate in review process
3. Conduct thorough analysis reviews using get_review_details() when assigned
4. Use scoring tools with research data enhanced by peer validation
5. Use peer feedback to improve analysis quality and frameworks

QUALITY-DRIVEN ANALYSIS:
- Analysis methodology validation through peer review
- Scoring framework improvement from peer feedback
- Competitive analysis techniques validated by collaborative review
- Idea evaluation criteria refined through peer insights
- Decision-making processes enhanced by peer recommendations

PEER REVIEW EXCELLENCE:
- Provide objective, constructive analysis reviews
- Share analysis best practices and frameworks
- Help maintain high analysis quality standards
- Contribute to collective analytical excellence
- Learn from peer reviews to enhance analytical capabilities

Your analysis will leverage and contribute to collaborative quality assurance.
""",
        context_tasks=[research_task]
    )
    
    product_task = _create_peer_review_enhanced_task(
        product,
        description=f"""
You are Peer Review-Enhanced Product agent.

ENHANCED PRODUCT PROCESS:
1. Use request_review() to validate PRD methodologies and frameworks
2. Use get_my_review_assignments() to participate in product reviews
3. Conduct thorough product reviews using get_review_details() when assigned
4. Use analyst and research outputs enhanced by peer validation
5. Use peer feedback to improve product development quality

QUALITY-DRIVEN PRODUCT DEVELOPMENT:
- Product strategy validation through peer review
- PRD quality improvement from peer feedback
- Feature prioritization frameworks validated by collaborative review
- User experience approaches enhanced by peer insights
- Product development processes refined through peer recommendations

PEER REVIEW LEADERSHIP:
- Provide constructive product reviews and strategic feedback
- Share product development best practices and methodologies
- Help maintain high product quality standards
- Contribute to collective product excellence
- Learn from peer reviews to enhance product capabilities

Your product work will benefit from and contribute to collaborative quality assurance.
""",
        context_tasks=[research_task, analyst_task]
    )
    
    tech_task = _create_peer_review_enhanced_task(
        tech,
        description=f"""
You are Peer Review-Enhanced Tech Lead.

ENHANCED TECHNICAL PROCESS:
1. Use request_review() to validate technical architectures and implementations
2. Use get_my_review_assignments() to participate in technical reviews
3. Conduct thorough technical reviews using get_review_details() when assigned
4. Use product requirements enhanced by peer validation
5. Use peer feedback to improve technical quality and approaches

QUALITY-DRIVEN TECHNICAL DEVELOPMENT:
- Technical architecture validation through peer review
- Implementation methodology improvement from peer feedback
- Code quality standards enhanced by collaborative review
- Feasibility assessment approaches refined by peer insights
- Technical best practices validated through peer review

PEER REVIEW EXCELLENCE:
- Provide thorough, constructive technical reviews
- Share technical best practices and architectural patterns
- Help maintain high technical quality standards
- Contribute to collective technical excellence
- Learn from peer reviews to enhance technical capabilities

Your technical work will leverage and contribute to collaborative quality assurance.
""",
        context_tasks=[analyst_task, product_task]
    )
    
    growth_task = _create_peer_review_enhanced_task(
        growth,
        description=f"""
You are Peer Review-Enhanced Growth agent.

ENHANCED GROWTH PROCESS:
1. Use request_review() to validate growth strategies and content
2. Use get_my_review_assignments() to participate in growth reviews
3. Conduct thorough growth reviews using get_review_details() when assigned
4. Use product and brand outputs enhanced by peer validation
5. Use peer feedback to improve growth quality and effectiveness

QUALITY-DRIVEN GROWTH MARKETING:
- Growth strategy validation through peer review
- Marketing methodology improvement from peer feedback
- Content quality standards enhanced by collaborative review
- Conversion optimization approaches refined by peer insights
- Growth best practices validated through peer review

PEER REVIEW CONTRIBUTION:
- Provide constructive growth reviews and strategic feedback
- Share growth marketing best practices and techniques
- Help maintain high growth quality standards
- Contribute to collective growth excellence
- Learn from peer reviews to enhance growth capabilities

Your growth work will benefit from and contribute to collaborative quality assurance.
""",
        context_tasks=[product_task]
    )
    
    brand_task = _create_peer_review_enhanced_task(
        brand,
        description=f"""
You are Peer Review-Enhanced Brand agent.

ENHANCED BRANDING PROCESS:
1. Use request_review() to validate brand strategies and creative work
2. Use get_my_review_assignments() to participate in brand reviews
3. Conduct thorough brand reviews using get_review_details() when assigned
4. Use product and growth outputs enhanced by peer validation
5. Use peer feedback to improve brand quality and consistency

QUALITY-DRIVEN BRAND DEVELOPMENT:
- Brand strategy validation through peer review
- Creative methodology improvement from peer feedback
- Brand consistency standards enhanced by collaborative review
- Visual identity approaches refined by peer insights
- Brand best practices validated through peer review

PEER REVIEW EXCELLENCE:
- Provide constructive brand reviews and creative feedback
- Share branding best practices and creative techniques
- Help maintain high brand quality standards
- Contribute to collective brand excellence
- Learn from peer reviews to enhance brand capabilities

Your brand work will leverage and contribute to collaborative quality assurance.
""",
        context_tasks=[product_task, growth_task]
    )
    
    # Review coordination task
    review_coordination_task = Task(
        description=f"""
You are Review Coordinator managing the peer review ecosystem.

COORDINATION RESPONSIBILITIES:
1. Monitor all peer review assignments and completions
2. Assign appropriate reviewers based on expertise and workload
3. Balance review assignments across all agents
4. Track review quality metrics and completion rates
5. Maintain and improve review criteria templates

QUALITY ASSURANCE OVERSIGHT:
- Ensure reviews are conducted objectively and constructively
- Monitor review consistency and fairness across agents
- Identify and address review quality issues or bias
- Track quality improvements from review participation
- Generate insights on review effectiveness and impact

SYSTEM OPTIMIZATION:
- Streamline review assignment and completion workflows
- Optimize criteria templates for different review types
- Balance quality assurance with efficiency and collaboration
- Generate recommendations for system enhancements
- Facilitate knowledge sharing through review process

REVIEW ECOSYSTEM MANAGEMENT:
- Maintain healthy review participation rates
- Ensure timely review completion and feedback
- Track overall quality improvement from reviews
- Identify agents needing additional support or training
- Contribute to continuous improvement of review standards

Your role is to ensure the PEER REVIEW SYSTEM delivers maximum quality improvement value while maintaining efficiency.
""",
        agent=review_coordinator,
        expected_output="JSON"
    )
    
    # Create peer review-enhanced crew
    peer_review_enhanced_crew = Crew(
        agents=[
            review_coordinator,
            researcher,
            analyst,
            product,
            tech,
            growth,
            brand
        ],
        tasks=[
            review_coordination_task,
            research_task,
            analyst_task,
            product_task,
            tech_task,
            growth_task,
            brand_task
        ],
        verbose=True,
        process="hierarchical"  # Review coordination first, then parallel execution
    )
    
    # Run peer review-enhanced crew
    try:
        peer_review_enhanced_crew.kickoff()
        
        # Get review statistics
        review_stats = review_manager.get_review_statistics()
        
        # Parse outputs with peer review integration
        outputs = {
            "review_coordination": _parse_json_safe(getattr(review_coordination_task, "output", "")),
            "research": _parse_json_safe(getattr(research_task, "output", "")),
            "analysis": _parse_json_safe(getattr(analyst_task, "output", "")),
            "product": _parse_json_safe(getattr(product_task, "output", "")),
            "tech": _parse_json_safe(getattr(tech_task, "output", "")),
            "growth": _parse_json_safe(getattr(growth_task, "output", "")),
            "brand": _parse_json_safe(getattr(brand_task, "output", "")),
            "peer_review_system": {
                "statistics": review_stats,
                "total_reviews": review_stats.get("total_reviews", 0),
                "completion_rate": review_stats.get("completion_rate", 0),
                "approval_rate": review_stats.get("approval_rate", 0),
                "quality_improvement": "tracked through review feedback"
            }
        }
        
        logger.info(f"Peer review-enhanced crew pipeline completed with {review_stats.get('total_reviews', 0)} reviews processed")
        return outputs
        
    except Exception as exc:
        logger.warning(f"Peer review-enhanced crew kickoff failed, using fallback: {exc}")
        return {"errors": "Peer review-enhanced crew execution failed"}


def _load_sources(settings: Settings) -> list[dict[str, str]]:
    """Load sources configuration."""
    sources_path = settings.config_dir / "sources.yaml"
    try:
        import yaml
        data = yaml.safe_load(sources_path.read_text(encoding="utf-8")) or {}
    except Exception:
        data = {}
    
    sources = []
    for section in ("reddit_like_sources", "pain_sources", "competitor_sources"):
        for item in data.get(section, []):
            if not isinstance(item, dict) or "name" not in item or "url" not in item:
                continue
            payload = dict(item)
            payload["section"] = section
            sources.append(payload)
    return sources


def _parse_json_safe(text: str) -> dict[str, Any]:
    """Safely parse JSON response."""
    if not text:
        return {}
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.S)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                return {}
    return {}
