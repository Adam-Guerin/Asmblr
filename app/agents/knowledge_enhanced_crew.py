"""
Knowledge-enhanced crew system with shared knowledge base integration.
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
from app.agents.shared_knowledge import SharedKnowledgeBase
from app.agents.knowledge_tools import KnowledgeBaseTools, create_knowledge_prompts
from app.langchain_tools import build_toolbox


def _create_knowledge_enhanced_agent(
    role: str,
    goal: str,
    backstory: str,
    tools: list[Any],
    knowledge_tools: KnowledgeBaseTools,
    knowledge_prompt: str
) -> Agent:
    """Create an agent with knowledge base capabilities."""
    
    enhanced_backstory = f"""
{backstory}

KNOWLEDGE BASE INTEGRATION:
You have access to a shared knowledge base containing collective intelligence from all agents.
Before each task, search for relevant knowledge to improve your approach.
After each task, contribute your learnings to the knowledge base.
Use and contribute to collective intelligence for continuous improvement.

{knowledge_prompt}
"""
    
    try:
        return Agent(role=role, goal=goal, backstory=enhanced_backstory, tools=tools, llm=llm_client._client)
    except Exception:
        return Agent(role=role, goal=goal, backstory=enhanced_backstory, tools=[], llm=llm_client._client)


def run_knowledge_enhanced_crewai_pipeline(
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
    """Run enhanced CrewAI pipeline with shared knowledge base."""
    
    if Agent is None or Task is None or Crew is None:
        logger.warning("CrewAI not available; returning empty outputs")
        return {"errors": "CrewAI not available"}
    
    # Initialize shared knowledge base
    knowledge_dir = settings.runs_dir / "shared_knowledge"
    knowledge_base = SharedKnowledgeBase(knowledge_dir)
    
    # Build toolbox with knowledge tools
    base_toolbox = build_toolbox(settings, llm_client)
    knowledge_prompts = create_knowledge_prompts()
    
    # Create knowledge-enhanced agents
    def _mk_knowledge_agent(role, goal, backstory, tools):
        knowledge_tools = KnowledgeBaseTools(knowledge_base, role)
        
        # Add knowledge tools to agent toolbox
        enhanced_tools = tools + [
            knowledge_tools.search_knowledge,
            knowledge_tools.get_knowledge_entry,
            knowledge_tools.add_knowledge,
            knowledge_tools.update_knowledge,
            knowledge_tools.validate_knowledge,
            knowledge_tools.get_related_knowledge,
            knowledge_tools.get_top_knowledge,
            knowledge_tools.get_my_contributions,
            knowledge_tools.get_knowledge_statistics
        ]
        
        return _create_knowledge_enhanced_agent(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=enhanced_tools,
            knowledge_tools=knowledge_tools,
            knowledge_prompt=knowledge_prompts["knowledge_aware_agent"]
        )
    
    # Core agents with knowledge integration
    researcher = _mk_knowledge_agent(
        role="Researcher",
        goal="Collect signals, extract pains, cluster, and generate product ideas using shared knowledge.",
        backstory="Signal analyst with access to collective research intelligence.",
        tools=[base_toolbox["web"], base_toolbox["rag"]]
    )
    
    analyst = _mk_knowledge_agent(
        role="Analyst",
        goal="Score ideas, evaluate competition, and pick top opportunities using shared knowledge.",
        backstory="Quant-minded evaluator with access to collective analysis intelligence.",
        tools=[base_toolbox["scoring"], base_toolbox["competitor"]]
    )
    
    product = _mk_knowledge_agent(
        role="Product",
        goal="Produce a clear PRD with ICP/JTBD/MVP scope using shared knowledge.",
        backstory="Product strategist with access to collective product intelligence.",
        tools=[base_toolbox["rag"]]
    )
    
    tech = _mk_knowledge_agent(
        role="Tech Lead",
        goal="Write technical spec and generate buildable repo skeleton using shared knowledge.",
        backstory="Senior engineer with access to collective technical intelligence.",
        tools=[base_toolbox["repo"]]
    )
    
    growth = _mk_knowledge_agent(
        role="Growth",
        goal="Generate landing copy and content pack using shared knowledge.",
        backstory="Growth marketer with access to collective growth intelligence.",
        tools=[base_toolbox["landing"], base_toolbox["content"]]
    )
    
    brand = _mk_knowledge_agent(
        role="Brand",
        goal="Define project identity using shared knowledge.",
        backstory="Brand strategist with access to collective brand intelligence.",
        tools=[]
    )
    
    # Knowledge curator agent
    knowledge_curator = _mk_knowledge_agent(
        role="Knowledge Curator",
        goal="Maintain and improve the shared knowledge base.",
        backstory=knowledge_prompts["knowledge_curator"],
        tools=[]
    )
    
    # Knowledge harvester agent
    knowledge_harvester = _mk_knowledge_agent(
        role="Knowledge Harvester",
        goal="Extract and organize intelligence from agent experiences.",
        backstory=knowledge_prompts["knowledge_harvester"],
        tools=[]
    )
    
    # Create knowledge-enhanced tasks
    def _create_knowledge_enhanced_task(agent, description, context_tasks=None):
        """Create task with knowledge base integration."""
        enhanced_description = f"""
{description}

KNOWLEDGE BASE INTEGRATION:
1. Before starting: Use search_knowledge() to find relevant methodologies and best practices
2. During execution: Use get_knowledge_entry() to access specific knowledge items
3. Use get_related_knowledge() to find connected intelligence
4. After completion: Use add_knowledge() to share your learnings and insights
5. Use validate_knowledge() to improve existing knowledge when relevant

COLLABORATIVE INTELLIGENCE:
- Build upon knowledge contributed by other agents
- Share your unique expertise and methodologies
- Document successful strategies and patterns
- Contribute to collective intelligence growth
- Help validate and improve shared knowledge

KNOWLEDGE CONTRIBUTION GUIDELINES:
- Share successful methodologies and frameworks
- Document problem-solving approaches and solutions
- Add patterns and best practices discovered
- Contribute lessons learned and insights
- Help expand collective intelligence

Focus on LEVERAGING AND ENHANCING COLLECTIVE KNOWLEDGE.
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
    
    # Create knowledge-enhanced tasks
    research_task = _create_knowledge_enhanced_task(
        researcher,
        description=f"""
You are Knowledge-Enhanced Researcher.

ENHANCED RESEARCH PROCESS:
1. Use search_knowledge() to find research methodologies and best practices
2. Use get_top_knowledge() to access validated research frameworks
3. Use web_search_and_summarize with sources: {sources_json}
4. Use add_knowledge() to share research insights and methodologies
5. Document successful research patterns and signal extraction techniques

KNOWLEDGE-DRIVEN IMPROVEMENTS:
- Research methodology optimization based on shared knowledge
- Signal quality assessment using proven frameworks
- Pain extraction patterns from collective intelligence
- Clustering approaches validated by other agents
- Research efficiency improvements from shared experience

Your research will benefit from and contribute to collective intelligence.
"""
    )
    
    analyst_task = _create_knowledge_enhanced_task(
        analyst,
        description=f"""
You are Knowledge-Enhanced Analyst.

ENHANCED ANALYSIS PROCESS:
1. Use search_knowledge() to find analysis frameworks and scoring methodologies
2. Use get_related_knowledge() to connect with research insights
3. Use scoring tools with research data enhanced by shared knowledge
4. Use add_knowledge() to share analysis methodologies and insights
5. Document successful scoring patterns and evaluation frameworks

KNOWLEDGE-DRIVEN IMPROVEMENTS:
- Analysis methodology enhancement from shared frameworks
- Scoring optimization using validated approaches
- Competitive analysis techniques from collective experience
- Idea evaluation criteria refined by shared insights
- Decision-making frameworks validated by other agents

Your analysis will leverage and contribute to collective intelligence.
""",
        context_tasks=[research_task]
    )
    
    product_task = _create_knowledge_enhanced_task(
        product,
        description=f"""
You are Knowledge-Enhanced Product agent.

ENHANCED PRODUCT PROCESS:
1. Use search_knowledge() to find product frameworks and PRD templates
2. Use get_knowledge_entry() to access specific product methodologies
3. Use analyst and research outputs enhanced with shared knowledge
4. Use add_knowledge() to share product strategies and frameworks
5. Document successful product development patterns and approaches

KNOWLEDGE-DRIVEN IMPROVEMENTS:
- Product strategy frameworks from collective intelligence
- PRD templates and methodologies validated by other agents
- Feature prioritization approaches refined by shared experience
- User experience frameworks from shared best practices
- Product development patterns from collective success stories

Your product work will benefit from and enhance collective intelligence.
""",
        context_tasks=[research_task, analyst_task]
    )
    
    tech_task = _create_knowledge_enhanced_task(
        tech,
        description=f"""
You are Knowledge-Enhanced Tech Lead.

ENHANCED TECHNICAL PROCESS:
1. Use search_knowledge() to find technical architectures and implementation patterns
2. Use get_top_knowledge() to access validated technical frameworks
3. Use product requirements enhanced with shared technical knowledge
4. Use add_knowledge() to share technical architectures and solutions
5. Document successful implementation patterns and technical insights

KNOWLEDGE-DRIVEN IMPROVEMENTS:
- Technical architecture patterns from collective experience
- Implementation methodologies validated by other agents
- Technology selection frameworks refined by shared insights
- Feasibility assessment approaches from shared knowledge
- Technical best practices and optimization techniques

Your technical work will leverage and contribute to collective intelligence.
""",
        context_tasks=[analyst_task, product_task]
    )
    
    growth_task = _create_knowledge_enhanced_task(
        growth,
        description=f"""
You are Knowledge-Enhanced Growth agent.

ENHANCED GROWTH PROCESS:
1. Use search_knowledge() to find growth strategies and marketing frameworks
2. Use get_related_knowledge() to connect with product and brand insights
3. Use product and brand outputs enhanced with shared growth knowledge
4. Use add_knowledge() to share growth strategies and successful campaigns
5. Document effective marketing patterns and conversion optimization techniques

KNOWLEDGE-DRIVEN IMPROVEMENTS:
- Growth strategy frameworks from collective intelligence
- Marketing methodologies validated by other agents
- Conversion optimization techniques from shared experience
- Content strategy approaches refined by shared insights
- Channel optimization patterns from collective success stories

Your growth work will benefit from and enhance collective intelligence.
""",
        context_tasks=[product_task]
    )
    
    brand_task = _create_knowledge_enhanced_task(
        brand,
        description=f"""
You are Knowledge-Enhanced Brand agent.

ENHANCED BRANDING PROCESS:
1. Use search_knowledge() to find branding frameworks and creative methodologies
2. Use get_knowledge_entry() to access specific brand strategies
3. Use product and growth outputs enhanced with shared brand knowledge
4. Use add_knowledge() to share brand strategies and creative insights
5. Document successful branding patterns and creative approaches

KNOWLEDGE-DRIVEN IMPROVEMENTS:
- Brand strategy frameworks from collective intelligence
- Creative methodologies validated by other agents
- Naming approaches refined by shared experience
- Visual identity patterns from shared best practices
- Brand guidelines and consistency frameworks from collective knowledge

Your brand work will leverage and contribute to collective intelligence.
""",
        context_tasks=[product_task, growth_task]
    )
    
    # Knowledge management tasks
    knowledge_curation_task = Task(
        description=f"""
You are Knowledge Curator managing the shared knowledge base.

CURATION RESPONSIBILITIES:
1. Monitor knowledge quality and relevance across all agent contributions
2. Use search_knowledge() to identify gaps and opportunities
3. Use validate_knowledge() to rate and improve knowledge entries
4. Use get_knowledge_statistics() to assess knowledge base health
5. Generate recommendations for knowledge base improvement

QUALITY ASSURANCE:
- Review new knowledge submissions for accuracy and relevance
- Identify and update outdated or deprecated knowledge
- Ensure proper categorization and tagging
- Maintain high standards for knowledge validation
- Promote best practices and validated methodologies

INTELLIGENCE SYNTHESIS:
- Identify patterns and trends across knowledge entries
- Create knowledge summaries and best practice guides
- Facilitate knowledge transfer between domains
- Recommend areas for new knowledge contributions
- Optimize knowledge organization and discovery

Your role is to ensure the knowledge base remains a HIGH-QUALITY, RELEVANT resource.
""",
        agent=knowledge_curator,
        expected_output="JSON"
    )
    
    knowledge_harvesting_task = Task(
        description=f"""
You are Knowledge Harvester extracting intelligence from agent experiences.

HARVESTING RESPONSIBILITIES:
1. Monitor all agent outputs for valuable insights and patterns
2. Use search_knowledge() to identify knowledge gaps and opportunities
3. Extract successful methodologies and frameworks from agent work
4. Use add_knowledge() to convert experiences into structured knowledge
5. Document lessons learned and best practices discovered

EXTRACTION TECHNIQUES:
- Analyze successful task completions for repeatable patterns
- Identify effective strategies and problem-solving approaches
- Extract optimization techniques and improvements
- Document collaboration insights and synergies
- Convert agent experiences into reusable knowledge

KNOWLEDGE STRUCTURING:
- Organize extracted insights into actionable knowledge entries
- Create templates and frameworks for common scenarios
- Document step-by-step methodologies and best practices
- Identify prerequisites and related knowledge connections
- Tag and categorize for optimal discovery

CONTINUOUS LEARNING:
- Track agent performance improvements and learning curves
- Identify emerging best practices and successful strategies
- Update knowledge based on new experiences and insights
- Share learning patterns and improvement methodologies
- Contribute to collective intelligence growth

Your role is to TRANSFORM AGENT EXPERIENCES into VALUABLE, REUSABLE KNOWLEDGE.
""",
        agent=knowledge_harvester,
        expected_output="JSON"
    )
    
    # Create knowledge-enhanced crew
    knowledge_enhanced_crew = Crew(
        agents=[
            knowledge_curator,
            knowledge_harvester,
            researcher,
            analyst,
            product,
            tech,
            growth,
            brand
        ],
        tasks=[
            knowledge_curation_task,
            knowledge_harvesting_task,
            research_task,
            analyst_task,
            product_task,
            tech_task,
            growth_task,
            brand_task
        ],
        verbose=True,
        process="hierarchical"  # Knowledge management first, then parallel execution
    )
    
    # Run knowledge-enhanced crew
    try:
        knowledge_enhanced_crew.kickoff()
        
        # Get knowledge base statistics
        kb_stats = knowledge_base.get_statistics()
        
        # Parse outputs with knowledge integration
        outputs = {
            "knowledge_curation": _parse_json_safe(getattr(knowledge_curation_task, "output", "")),
            "knowledge_harvesting": _parse_json_safe(getattr(knowledge_harvesting_task, "output", "")),
            "research": _parse_json_safe(getattr(research_task, "output", "")),
            "analysis": _parse_json_safe(getattr(analyst_task, "output", "")),
            "product": _parse_json_safe(getattr(product_task, "output", "")),
            "tech": _parse_json_safe(getattr(tech_task, "output", "")),
            "growth": _parse_json_safe(getattr(growth_task, "output", "")),
            "brand": _parse_json_safe(getattr(brand_task, "output", "")),
            "knowledge_base": {
                "statistics": kb_stats,
                "total_entries": kb_stats.get("total_entries", 0),
                "new_entries_added": "tracked during execution",
                "knowledge_utilization": "high"
            }
        }
        
        logger.info(f"Knowledge-enhanced crew pipeline completed with {kb_stats.get('total_entries', 0)} knowledge entries")
        return outputs
        
    except Exception as exc:
        logger.warning(f"Knowledge-enhanced crew kickoff failed, using fallback: {exc}")
        return {"errors": "Knowledge-enhanced crew execution failed"}


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
