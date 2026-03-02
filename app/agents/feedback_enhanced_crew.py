"""
Enhanced crew system with integrated feedback loops for continuous improvement.
"""

import json
import re
from typing import Any

from loguru import logger

try:
    from crewai import Agent, Task, Crew
except Exception:  # pragma: no cover
    Agent = None
    Task = None
    Crew = None

from app.core.config import Settings
from app.core.llm import LLMClient
from app.agents.facilitators import SharedContext, FacilitatorTools
from app.agents.feedback_loops import (
    FeedbackLoopManager, 
    FeedbackTools, 
    create_feedback_prompts
)
from app.langchain_tools import build_toolbox


def _create_feedback_enhanced_agent(
    role: str,
    goal: str, 
    backstory: str,
    tools: list[Any],
    feedback_tools: FeedbackTools,
    feedback_prompt: str
) -> Agent:
    """Create an agent with feedback loop capabilities."""
    
    enhanced_backstory = f"""
{backstory}

FEEDBACK LOOP CAPABILITIES:
You have access to continuous feedback mechanisms to improve your performance.
Before each task, check for pending feedback about your work.
After each task, submit self-reflection on your performance.
Use feedback to adapt and optimize your approach over time.

{feedback_prompt}
"""
    
    try:
        return Agent(role=role, goal=goal, backstory=enhanced_backstory, tools=tools, llm=llm_client._client)
    except Exception:
        return Agent(role=role, goal=goal, backstory=enhanced_backstory, tools=[], llm=llm_client._client)


def run_feedback_enhanced_crewai_pipeline(
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
    """Run enhanced CrewAI pipeline with feedback loops and facilitator agents."""
    
    if Agent is None or Task is None or Crew is None:
        logger.warning("CrewAI not available; returning empty outputs")
        return {"errors": "CrewAI not available"}
    
    # Initialize systems
    shared_context = SharedContext(
        insights=[],
        conflicts=[],
        decisions=[],
        learnings=[],
        validation_results=[]
    )
    
    facilitator_tools = FacilitatorTools(shared_context, run_id)
    feedback_manager = FeedbackLoopManager(settings.runs_dir)
    
    # Create feedback loop for this pipeline
    feedback_loop = feedback_manager.create_feedback_loop(run_id)
    feedback_prompts = create_feedback_prompts()
    
    # Build toolbox with feedback tools
    base_toolbox = build_toolbox(settings, llm_client)
    
    # Add feedback-specific tools
    feedback_toolbox = base_toolbox.copy()
    feedback_toolbox.update({
        "submit_feedback": {
            "description": "Submit feedback about another agent",
            "function": feedback_tools.submit_feedback
        },
        "submit_self_feedback": {
            "description": "Submit self-reflection feedback",
            "function": feedback_tools.submit_self_feedback
        },
        "get_my_feedback": {
            "description": "Get feedback addressed to you",
            "function": feedback_tools.get_my_feedback
        },
        "get_pending_actions": {
            "description": "Get pending action items",
            "function": feedback_tools.get_pending_actions
        },
        "resolve_feedback": {
            "description": "Mark feedback as resolved",
            "function": feedback_tools.resolve_feedback
        },
        "sync_context": facilitator_tools.sync_context,
        "add_insight": facilitator_tools.add_insight,
        "save_context": facilitator_tools.save_context
    })
    
    # Enhanced agents with feedback capabilities
    def _mk_feedback_agent(role, goal, backstory, tools):
        return _create_feedback_enhanced_agent(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools,
            feedback_tools=feedback_tools,
            feedback_prompt=feedback_prompts["feedback_aware_agent"]
        )
    
    # Core agents with feedback awareness
    researcher = _mk_feedback_agent(
        role="Researcher",
        goal="Collect signals, extract pains, cluster, and generate product ideas with continuous improvement.",
        backstory="Signal analyst focused on market pains with feedback-driven optimization.",
        tools=[feedback_toolbox["web"], feedback_toolbox["rag"], feedback_toolbox["submit_feedback"], feedback_toolbox["get_my_feedback"], feedback_toolbox["submit_self_feedback"]]
    )
    
    analyst = _mk_feedback_agent(
        role="Analyst", 
        goal="Score ideas, evaluate competition, and pick top opportunities with quality feedback integration.",
        backstory="Quant-minded evaluator with collaborative feedback awareness.",
        tools=[feedback_toolbox["scoring"], feedback_toolbox["competitor"], feedback_toolbox["submit_feedback"], feedback_toolbox["get_my_feedback"], feedback_toolbox["submit_self_feedback"]]
    )
    
    product = _mk_feedback_agent(
        role="Product",
        goal="Produce a clear PRD with ICP/JTBD/MVP scope using feedback loops.",
        backstory="Product strategist with continuous learning from feedback.",
        tools=[feedback_toolbox["rag"], feedback_toolbox["submit_feedback"], feedback_toolbox["get_my_feedback"], feedback_toolbox["submit_self_feedback"]]
    )
    
    tech = _mk_feedback_agent(
        role="Tech Lead",
        goal="Write technical spec and generate buildable repo skeleton with feedback-driven improvements.",
        backstory="Senior engineer with adaptive learning from feedback.",
        tools=[feedback_toolbox["repo"], feedback_toolbox["submit_feedback"], feedback_toolbox["get_my_feedback"], feedback_toolbox["submit_self_feedback"]]
    )
    
    growth = _mk_feedback_agent(
        role="Growth",
        goal="Generate landing copy and content pack with feedback optimization.",
        backstory="Growth marketer with continuous improvement from feedback.",
        tools=[feedback_toolbox["landing"], feedback_toolbox["content"], feedback_toolbox["submit_feedback"], feedback_toolbox["get_my_feedback"], feedback_toolbox["submit_self_feedback"]]
    )
    
    brand = _mk_feedback_agent(
        role="Brand",
        goal="Define project identity with feedback-driven creative decisions.",
        backstory="Brand strategist with adaptive learning from feedback.",
        tools=[feedback_toolbox["submit_feedback"], feedback_toolbox["get_my_feedback"], feedback_toolbox["submit_self_feedback"]]
    )
    
    # Feedback coordinator agent
    feedback_coordinator = _mk_feedback_agent(
        role="Feedback Coordinator",
        goal="Manage feedback loops and drive continuous improvement across all agents.",
        backstory=feedback_prompts["feedback_coordinator"],
        tools=[feedback_toolbox["submit_feedback"], feedback_toolbox["sync_context"], feedback_toolbox["save_context"]]
    )
    
    # Self-improving agents
    def _mk_self_improving_agent(role, goal, backstory, tools):
        return _create_feedback_enhanced_agent(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=tools,
            feedback_tools=feedback_tools,
            feedback_prompt=feedback_prompts["self_improving_agent"]
        )
    
    # Enhanced tasks with feedback integration
    def _create_feedback_enhanced_task(agent, description, context_tasks=None):
        """Create task with feedback loop integration."""
        enhanced_description = f"""
{description}

FEEDBACK LOOP INTEGRATION:
1. Before starting: Use `get_my_feedback` to check for pending feedback
2. Address any critical or high-priority feedback first
3. Use `get_pending_actions` to get specific improvement tasks
4. During execution: Submit feedback on other agents when relevant
5. After completion: Use `submit_self_feedback` for self-reflection
6. Use `resolve_feedback` when you've addressed feedback items

CONTINUOUS IMPROVEMENT:
- Adapt your approach based on received feedback
- Share successful strategies with other agents
- Document lessons learned and best practices
- Optimize your tool usage and workflows
- Measure and track your improvement over time

Focus on EVOLVING YOUR CAPABILITIES through iterative feedback.
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
    
    # Create enhanced tasks with feedback loops
    research_task = _create_feedback_enhanced_task(
        researcher,
        description=f"""
You are the Feedback-Enhanced Researcher.

ENHANCED RESEARCH PROCESS:
1. Use `get_my_feedback` to check for research improvement feedback
2. Use `web_search_and_summarize` with sources: {sources_json}
3. Use `submit_feedback` to share methodology insights with other agents
4. Use `submit_self_feedback` to reflect on research quality and completeness
5. Address any feedback about signal quality or pain extraction

FEEDBACK-DRIVEN IMPROVEMENTS:
- Research methodology refinement based on feedback
- Signal quality assessment improvements
- Pain extraction pattern optimization
- Clustering approach enhancements
- Data gap identification and resolution

Your research will feed into enhanced analysis and product development.
"""
    )
    
    analyst_task = _create_feedback_enhanced_task(
        analyst,
        description=f"""
You are the Feedback-Enhanced Analyst.

ENHANCED ANALYSIS PROCESS:
1. Use `get_my_feedback` to check for analysis improvement feedback
2. Use scoring tools with research data
3. Use `submit_feedback` to share scoring methodology and rationale
4. Use `submit_self_feedback` to reflect on analysis quality and accuracy
5. Address feedback about scoring fairness or idea evaluation

FEEDBACK-DRIVEN IMPROVEMENTS:
- Scoring methodology refinement based on feedback
- Competitive analysis framework improvements
- Idea evaluation criteria optimization
- Risk assessment enhancements
- Decision rationale transparency improvements

Your analysis will guide product development and technical specifications.
""",
        context_tasks=[research_task]
    )
    
    product_task = _create_feedback_enhanced_task(
        product,
        description=f"""
You are the Feedback-Enhanced Product agent.

ENHANCED PRODUCT PROCESS:
1. Use `get_my_feedback` to check for product development feedback
2. Use analyst and research outputs with feedback integration
3. Use `submit_feedback` to share product strategy insights
4. Use `submit_self_feedback` to reflect on PRD quality and completeness
5. Address feedback about scope, features, or user experience

FEEDBACK-DRIVEN IMPROVEMENTS:
- Product strategy refinement based on feedback
- Feature prioritization framework improvements
- PRD quality and clarity enhancements
- User experience approach optimization
- Technical feasibility assessment improvements

Your PRD will guide technical specifications and growth strategies.
""",
        context_tasks=[research_task, analyst_task]
    )
    
    tech_task = _create_feedback_enhanced_task(
        tech,
        description=f"""
You are the Feedback-Enhanced Tech Lead.

ENHANCED TECHNICAL PROCESS:
1. Use `get_my_feedback` to check for technical development feedback
2. Use product requirements with feedback integration
3. Use `submit_feedback` to share technical architecture decisions
4. Use `submit_self_feedback` to reflect on spec quality and feasibility
5. Address feedback about implementation approach or technology choices

FEEDBACK-DRIVEN IMPROVEMENTS:
- Technical architecture refinement based on feedback
- Implementation strategy optimization
- Technology selection criteria improvements
- Feasibility assessment enhancements
- Documentation and best practices improvements

Your technical spec will enable MVP generation with continuous improvement.
""",
        context_tasks=[analyst_task, product_task]
    )
    
    growth_task = _create_feedback_enhanced_task(
        growth,
        description=f"""
You are the Feedback-Enhanced Growth agent.

ENHANCED GROWTH PROCESS:
1. Use `get_my_feedback` to check for growth strategy feedback
2. Use product and brand outputs with feedback integration
3. Use `submit_feedback` to share growth insights and messaging rationale
4. Use `submit_self_feedback` to reflect on content quality and effectiveness
5. Address feedback about messaging, conversion, or channel strategy

FEEDBACK-DRIVEN IMPROVEMENTS:
- Growth strategy refinement based on feedback
- Conversion optimization approach improvements
- Content quality and relevance enhancements
- Channel strategy optimization
- Brand alignment and messaging consistency improvements

Your growth outputs will drive go-to-market strategy with continuous improvement.
""",
        context_tasks=[product_task]
    )
    
    brand_task = _create_feedback_enhanced_task(
        brand,
        description=f"""
You are the Feedback-Enhanced Brand agent.

ENHANCED BRANDING PROCESS:
1. Use `get_my_feedback` to check for brand development feedback
2. Use product and growth outputs with feedback integration
3. Use `submit_feedback` to share brand strategy and creative rationale
4. Use `submit_self_feedback` to reflect on brand quality and consistency
5. Address feedback about naming, visual identity, or messaging

FEEDBACK-DRIVEN IMPROVEMENTS:
- Brand strategy refinement based on feedback
- Creative approach optimization
- Naming methodology improvements
- Visual identity direction enhancements
- Brand guidelines and consistency improvements

Your brand work will ensure consistent messaging across all touchpoints with continuous improvement.
""",
        context_tasks=[product_task, growth_task]
    )
    
    # Feedback coordination task
    feedback_coordination_task = Task(
        description=f"""
You are the Feedback Coordinator managing the feedback loop ecosystem.

COORDINATION RESPONSIBILITIES:
1. Monitor all feedback submissions across agents using feedback tools
2. Use `sync_context` to maintain shared knowledge base
3. Use `save_context` to persist feedback and learning data
4. Analyze feedback patterns and identify systemic improvements
5. Generate insights for process optimization

FEEDBACK ANALYSIS AND ROUTING:
- Categorize and prioritize feedback from all agents
- Identify recurring issues and patterns across the pipeline
- Route feedback to appropriate agents for resolution
- Track resolution rates and improvement trends
- Generate feedback quality reports and recommendations

PROCESS OPTIMIZATION:
- Streamline feedback submission and resolution workflows
- Identify opportunities for automation and efficiency gains
- Share best practices and successful strategies across agents
- Generate regular feedback loop performance reports

Your role is to ensure FEEDBACK DRIVES CONTINUOUS IMPROVEMENT across the entire system.
""",
        agent=feedback_coordinator,
        expected_output="JSON"
    )
    
    # Create enhanced crew with all agents
    feedback_enhanced_crew = Crew(
        agents=[
            feedback_coordinator,
            researcher,
            analyst,
            product,
            tech,
            growth,
            brand
        ],
        tasks=[
            feedback_coordination_task,
            research_task,
            analyst_task,
            product_task,
            tech_task,
            growth_task,
            brand_task
        ],
        verbose=True,
        process="hierarchical"  # Coordinator first, then parallel execution
    )
    
    # Run the feedback-enhanced crew
    try:
        feedback_enhanced_crew.kickoff()
        
        # Close feedback loop
        feedback_manager.close_feedback_loop(feedback_loop.id, "completed")
        
        # Parse outputs with feedback integration
        outputs = {
            "feedback_coordination": _parse_json_safe(getattr(feedback_coordination_task, "output", "")),
            "research": _parse_json_safe(getattr(research_task, "output", "")),
            "analysis": _parse_json_safe(getattr(analyst_task, "output", "")),
            "product": _parse_json_safe(getattr(product_task, "output", "")),
            "tech": _parse_json_safe(getattr(tech_task, "output", "")),
            "growth": _parse_json_safe(getattr(growth_task, "output", "")),
            "brand": _parse_json_safe(getattr(brand_task, "output", "")),
            "feedback_loop": {
                "id": feedback_loop.id,
                "summary": feedback_loop.summary,
                "next_actions": feedback_loop.next_actions
            }
        }
        
        logger.info(f"Feedback-enhanced crew pipeline completed with {len(feedback_loop.feedback_items)} feedback items processed")
        return outputs
        
    except Exception as exc:
        logger.warning(f"Feedback-enhanced crew kickoff failed, using fallback: {exc}")
        return {"errors": "Feedback-enhanced crew execution failed"}


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
