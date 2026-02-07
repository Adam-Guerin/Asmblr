"""
Enhanced crew system with facilitator agents for improved synergy and coordination.
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
from app.agents.facilitators import (
    SharedContext, 
    FacilitatorTools, 
    create_facilitator_prompts
)
from app.langchain_tools import build_toolbox


def _create_facilitator_tools(
    shared_context: SharedContext, 
    settings: Settings, 
    llm_client: LLMClient,
    run_id: str
) -> Dict[str, Any]:
    """Create tools for facilitator agents."""
    
    facilitator_tools = build_toolbox(settings, llm_client)
    
    # Add facilitator-specific tools
    facilitator_tools.update({
        "sync_context": {
            "description": "Synchronize shared context from file",
            "function": lambda: facilitator_tools.sync_context(),
            "returns": "Context synchronization status and summary"
        },
        "add_insight": {
            "description": "Add insight to shared context",
            "function": lambda agent, insight, data: facilitator_tools.shared_context.add_insight(agent, insight, data),
            "returns": "Success status"
        },
        "resolve_conflict": {
            "description": "Resolve conflict between agents",
            "function": lambda agent1, agent2, conflict, resolution: facilitator_tools.shared_context.add_conflict(agent1, agent2, conflict, resolution),
            "returns": "Conflict resolution status"
        },
        "get_coordination_prompt": {
            "description": "Get current coordination context for agents",
            "function": lambda: facilitator_tools.get_coordination_prompt(),
            "returns": "Coordination prompt with shared context"
        },
        "save_context": {
            "description": "Save shared context to file",
            "function": lambda: facilitator_tools.save_context(),
            "returns": "Save status"
        }
    })
    
    return facilitator_tools


def run_enhanced_crewai_pipeline(
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
    """Run enhanced CrewAI pipeline with facilitator agents for improved synergy."""
    
    if Agent is None or Task is None or Crew is None:
        logger.warning("CrewAI not available; returning empty outputs")
        return {"errors": "CrewAI not available"}
    
    # Initialize shared context and facilitator tools
    shared_context = SharedContext(
        insights=[],
        conflicts=[],
        decisions=[],
        learnings=[],
        validation_results=[]
    )
    
    facilitator_tools = FacilitatorTools(shared_context, run_id)
    facilitator_toolbox = _create_facilitator_tools(shared_context, settings, llm_client, run_id)
    
    # Load existing context if available
    context_status = facilitator_tools.sync_context()
    logger.info(f"Shared context status: {context_status}")
    
    # Get facilitator prompts
    facilitator_prompts = create_facilitator_prompts()
    
    # Core agents (existing)
    def _mk_agent(role, goal, backstory, tools):
        try:
            return Agent(role=role, goal=goal, backstory=backstory, tools=tools, llm=llm_client._client)
        except Exception:
            return Agent(role=role, goal=goal, backstory=backstory, tools=[], llm=llm_client._client)
    
    # New facilitator agents
    coordination_facilitator = _mk_agent(
        role="Coordination Facilitator",
        goal="Monitor cross-agent collaboration and resolve conflicts",
        backstory=facilitator_prompts["coordination_facilitator"],
        tools=list(facilitator_toolbox.values())
    )
    
    conflict_resolver = _mk_agent(
        role="Conflict Resolver",
        goal="Mediate disagreements and find optimal solutions",
        backstory=facilitator_prompts["conflict_resolver"],
        tools=[facilitator_toolbox["add_insight"], facilitator_toolbox["resolve_conflict"], facilitator_toolbox["save_context"]]
    )
    
    knowledge_synthesizer = _mk_agent(
        role="Knowledge Synthesizer",
        goal="Extract and synthesize insights across all agents",
        backstory=facilitator_prompts["knowledge_synthesizer"],
        tools=[facilitator_toolbox["add_insight"], facilitator_toolbox["sync_context"], facilitator_toolbox["save_context"]]
    )
    
    quality_validator = _mk_agent(
        role="Quality Validator",
        goal="Ensure output coherence and quality standards",
        backstory=facilitator_prompts["quality_validator"],
        tools=[facilitator_toolbox["add_insight"], facilitator_toolbox["sync_context"], facilitator_toolbox["save_context"]]
    )
    
    # Existing core agents
    researcher = _mk_agent(
        role="Researcher",
        goal="Collect signals, extract pains, cluster, and generate product ideas.",
        backstory="Signal analyst focused on market pains.",
        tools=[facilitator_toolbox["web"], facilitator_toolbox["rag"], facilitator_toolbox["add_insight"]]
    )
    
    analyst = _mk_agent(
        role="Analyst",
        goal="Score ideas, evaluate competition, and pick top opportunities.",
        backstory="Quant-minded evaluator.",
        tools=[facilitator_toolbox["scoring"], facilitator_toolbox["competitor"], facilitator_toolbox["add_insight"]]
    )
    
    product = _mk_agent(
        role="Product",
        goal="Produce a clear PRD with ICP/JTBD/MVP scope.",
        backstory="Product strategist.",
        tools=[facilitator_toolbox["rag"], facilitator_toolbox["add_insight"]]
    )
    
    tech = _mk_agent(
        role="Tech Lead",
        goal="Write technical spec and generate buildable repo skeleton.",
        backstory="Senior engineer.",
        tools=[facilitator_toolbox["repo"], facilitator_toolbox["add_insight"]]
    )
    
    growth = _mk_agent(
        role="Growth",
        goal="Generate landing copy and content pack for launch.",
        backstory="Growth marketer.",
        tools=[facilitator_toolbox["landing"], facilitator_toolbox["content"], facilitator_toolbox["add_insight"]]
    )
    
    brand = _mk_agent(
        role="Brand",
        goal="Define project name, art direction (DA), and create a simple logo.",
        backstory="Brand strategist and visual designer.",
        tools=[facilitator_toolbox["add_insight"]]
    )
    
    # Enhanced task definitions with collaboration hooks
    def _create_enhanced_task(agent, description, context_tasks=None, collaboration_hooks=None):
        """Create task with collaboration hooks."""
        enhanced_description = description + f"""

COLLABORATION REQUIREMENTS:
1. Use `get_coordination_prompt` tool before starting to review shared context
2. Use `add_insight` tool to share your key findings with other agents
3. If you identify conflicts or dependencies, use `resolve_conflict` tool
4. Use `save_context` tool after completing your main task

SHARED CONTEXT ACCESS:
- Use `sync_context` to access insights from previous agents
- Build upon learnings and decisions already documented
- Reference conflicts that might affect your work
"""
        
        task = Task(
            description=enhanced_description,
            agent=agent,
            context=context_tasks or [],
            expected_output="JSON"
        )
        
        # Add collaboration hooks if specified
        if collaboration_hooks:
            for hook_name, hook_value in collaboration_hooks.items():
                setattr(task, hook_name, hook_value)
        
        return task
    
    # Create enhanced tasks with collaboration
    coordination_task = Task(
        description=f"""
You are the Coordination Facilitator. Your job is to ensure SYNERGY between all agents.

COORDINATION WORKFLOW:
1. Use `sync_context` to load current shared context
2. Monitor all agent tasks for collaboration opportunities
3. Use `add_insight` to share coordination insights
4. Use `resolve_conflict` when you identify agent conflicts
5. Use `save_context` to maintain shared knowledge base

SPECIFIC RESPONSIBILITIES:
- Before each major agent task: Share relevant context and insights
- During agent execution: Monitor for cross-agent dependencies
- After agent completion: Extract and share key learnings
- Between dependent agents: Ensure proper handoff and integration

Focus on creating TEAM INTELLIGENCE, not just individual outputs.
""",
        agent=coordination_facilitator,
        expected_output="JSON"
    )
    
    # Load sources and create enhanced research task
    sources = _load_sources(settings)
    sources_json = json.dumps(sources, indent=2)
    
    research_task = _create_enhanced_task(
        researcher,
        description=f"""
You are the Researcher working with enhanced collaboration.

ENHANCED RESEARCH PROCESS:
1. Use `get_coordination_prompt` to review collaboration context
2. Use `web_search_and_summarize` with sources: {sources_json}
3. Use `add_insight` to share research methodology and findings
4. Use `sync_context` to learn from previous research insights
5. Share pain extraction patterns and clustering insights

COLLABORATION INSIGHTS TO SHARE:
- Research methodology and approach
- Key pain patterns discovered
- Market signal quality assessment
- Clustering rationale and insights
- Data gaps or limitations identified

Your outputs will be used by Analyst, Product, Tech, Growth, and Brand agents.
""",
        collaboration_hooks={
            "requires_validation": True,
            "insight_sharing": True
        }
    )
    
    # Enhanced analyst task
    analyst_task = _create_enhanced_task(
        analyst,
        description=f"""
You are the Analyst working with enhanced collaboration.

ENHANCED ANALYSIS PROCESS:
1. Use `get_coordination_prompt` to review research insights and context
2. Use scoring tools with research data
3. Use `add_insight` to share scoring methodology and rationale
4. Use `resolve_conflict` if scoring conflicts with research findings
5. Share competitive analysis insights with other agents

COLLABORATION INSIGHTS TO SHARE:
- Scoring methodology and weight rationale
- Competitive analysis framework
- Idea evaluation criteria and trade-offs
- Market opportunity assessment approach
- Risk factors and mitigation strategies

Focus on transparent decision-making that other agents can understand and build upon.
""",
        context_tasks=[research_task]
    )
    
    # Enhanced product task
    product_task = _create_enhanced_task(
        product,
        description=f"""
You are the Product agent working with enhanced collaboration.

ENHANCED PRODUCT PROCESS:
1. Use `get_coordination_prompt` to review analysis and research insights
2. Use `add_insight` to share product strategy and prioritization rationale
3. Use `resolve_conflict` if technical feasibility conflicts with requirements
4. Share PRD methodology and scope decisions
5. Document trade-offs and assumptions clearly

COLLABORATION INSIGHTS TO SHARE:
- Product strategy and positioning rationale
- Feature prioritization framework
- Scope decisions and trade-off analysis
- User experience approach and principles
- Integration considerations for technical implementation

Your PRD will guide Tech, Growth, and Brand agents.
""",
        context_tasks=[research_task, analyst_task]
    )
    
    # Enhanced tech task
    tech_task = _create_enhanced_task(
        tech,
        description=f"""
You are the Tech Lead working with enhanced collaboration.

ENHANCED TECHNICAL PROCESS:
1. Use `get_coordination_prompt` to review product requirements and constraints
2. Use `add_insight` to share technical architecture decisions
3. Use `resolve_conflict` if technical approach conflicts with product needs
4. Share implementation strategy and technology choices
5. Document feasibility assessments and risks

COLLABORATION INSIGHTS TO SHARE:
- Technical architecture rationale and decisions
- Technology selection criteria and trade-offs
- Implementation strategy and phasing approach
- Feasibility assessments and risk mitigations
- Integration patterns and best practices

Your technical spec will enable MVP generation and guide implementation.
""",
        context_tasks=[analyst_task, product_task]
    )
    
    # Enhanced growth task
    growth_task = _create_enhanced_task(
        growth,
        description=f"""
You are the Growth agent working with enhanced collaboration.

ENHANCED GROWTH PROCESS:
1. Use `get_coordination_prompt` to review product, brand, and market insights
2. Use `add_insight` to share growth strategy and messaging rationale
3. Use `resolve_conflict` if messaging conflicts with brand direction
4. Share conversion optimization insights
5. Document channel strategy and launch approach

COLLABORATION INSIGHTS TO SHARE:
- Growth strategy and messaging framework
- Conversion optimization approach and insights
- Channel strategy and launch sequencing
- Content strategy rationale and effectiveness metrics
- Brand alignment and competitive positioning

Your outputs will create the go-to-market strategy.
""",
        context_tasks=[product_task]
    )
    
    # Enhanced brand task
    brand_task = _create_enhanced_task(
        brand,
        description=f"""
You are the Brand agent working with enhanced collaboration.

ENHANCED BRANDING PROCESS:
1. Use `get_coordination_prompt` to review product, growth, and market insights
2. Use `add_insight` to share brand strategy and creative rationale
3. Use `resolve_conflict` if creative direction conflicts with messaging
4. Share visual identity decisions and naming rationale
5. Document brand guidelines and usage principles

COLLABORATION INSIGHTS TO SHARE:
- Brand strategy and positioning rationale
- Naming methodology and decision criteria
- Visual identity direction and design principles
- Creative rationale and brand guidelines
- Market alignment and differentiation strategy

Your brand work will ensure consistent messaging across all touchpoints.
""",
        context_tasks=[product_task, growth_task]
    )
    
    # Create enhanced crew with facilitator agents
    enhanced_crew = Crew(
        agents=[
            coordination_facilitator,
            conflict_resolver,
            knowledge_synthesizer,
            quality_validator,
            researcher,
            analyst,
            product,
            tech,
            growth,
            brand
        ],
        tasks=[
            coordination_task,
            research_task,
            analyst_task,
            product_task,
            tech_task,
            growth_task,
            brand_task
        ],
        verbose=True,
        process="hierarchical"  # Coordination first, then parallel execution
    )
    
    # Run the enhanced crew
    try:
        enhanced_crew.kickoff()
        
        # Save final context state
        facilitator_tools.save_context()
        
        # Parse outputs (similar to original but enhanced)
        outputs = {
            "coordination": _parse_json_safe(getattr(coordination_task, "output", "")),
            "research": _parse_json_safe(getattr(research_task, "output", "")),
            "analysis": _parse_json_safe(getattr(analyst_task, "output", "")),
            "product": _parse_json_safe(getattr(product_task, "output", "")),
            "tech": _parse_json_safe(getattr(tech_task, "output", "")),
            "growth": _parse_json_safe(getattr(growth_task, "output", "")),
            "brand": _parse_json_safe(getattr(brand_task, "output", "")),
            "shared_context": shared_context.get_context_summary()
        }
        
        logger.info(f"Enhanced crew pipeline completed with {len(shared_context.insights)} insights shared")
        return outputs
        
    except Exception as exc:
        logger.warning(f"Enhanced crew kickoff failed, using fallback: {exc}")
        return {"errors": "Enhanced crew execution failed"}


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
