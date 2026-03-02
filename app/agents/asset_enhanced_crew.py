"""
Asset-Enhanced crew system with collaborative resource management.
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
from app.agents.shared_assets import SharedAssetManager
from app.agents.asset_tools import AssetManagementTools, create_asset_management_prompts
from app.langchain_tools import build_toolbox


def _create_asset_enhanced_agent(
    role: str,
    goal: str,
    backstory: str,
    tools: list[Any],
    asset_tools: AssetManagementTools,
    asset_prompt: str
) -> Agent:
    """Create an agent with asset management capabilities."""
    
    enhanced_backstory = f"""
{backstory}

ASSET MANAGEMENT INTEGRATION:
You have access to a shared asset system for collaborative resource creation and reuse.
Before creating new resources, search for existing assets to reuse.
When creating assets, make them discoverable and valuable for other agents.
Use shared assets consistently and record their usage for analytics.

{asset_prompt}
"""
    
    try:
        return Agent(role=role, goal=goal, backstory=enhanced_backstory, tools=tools, llm=llm_client._client)
    except Exception:
        return Agent(role=role, goal=goal, backstory=enhanced_backstory, tools=[], llm=llm_client._client)


def run_asset_enhanced_crewai_pipeline(
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
    """Run enhanced CrewAI pipeline with shared asset management."""
    
    if Agent is None or Task is None or Crew is None:
        logger.warning("CrewAI not available; returning empty outputs")
        return {"errors": "CrewAI not available"}
    
    # Initialize shared asset system
    assets_dir = settings.runs_dir / run_id / "shared_assets"
    asset_manager = SharedAssetManager(assets_dir)
    
    # Build toolbox with asset tools
    base_toolbox = build_toolbox(settings, llm_client)
    asset_prompts = create_asset_management_prompts()
    
    # Create asset-enhanced agents
    def _mk_asset_agent(role, goal, backstory, tools):
        asset_tools = AssetManagementTools(asset_manager, role)
        
        # Add asset management tools to agent toolbox
        enhanced_tools = tools + [
            asset_tools.create_logo,
            asset_tools.create_hosting_info,
            asset_tools.create_cta_template,
            asset_tools.search_assets,
            asset_tools.get_asset_details,
            asset_tools.use_asset,
            asset_tools.get_logos_for_brand,
            asset_tools.get_hosting_options,
            asset_tools.get_cta_templates,
            asset_tools.get_asset_statistics,
            asset_tools.approve_asset,
            asset_tools.publish_asset
        ]
        
        return _create_asset_enhanced_agent(
            role=role,
            goal=goal,
            backstory=backstory,
            tools=enhanced_tools,
            asset_tools=asset_tools,
            asset_prompt=asset_prompts["asset_aware_agent"]
        )
    
    # Core agents with asset management integration
    researcher = _mk_asset_agent(
        role="Researcher",
        goal="Collect signals, extract pains, cluster, and generate product ideas with asset sharing.",
        backstory="Signal analyst with collaborative resource management.",
        tools=[base_toolbox["web"], base_toolbox["rag"]]
    )
    
    analyst = _mk_asset_agent(
        role="Analyst",
        goal="Score ideas, evaluate competition, and pick top opportunities with asset reuse.",
        backstory="Quant-minded evaluator with asset management capabilities.",
        tools=[base_toolbox["scoring"], base_toolbox["competitor"]]
    )
    
    product = _mk_asset_agent(
        role="Product",
        goal="Produce a clear PRD with ICP/JTBD/MVP scope using shared assets.",
        backstory="Product strategist with collaborative resource management.",
        tools=[base_toolbox["rag"]]
    )
    
    tech = _mk_asset_agent(
        role="Tech Lead",
        goal="Write technical spec and generate buildable repo skeleton using shared assets.",
        backstory="Senior engineer with collaborative resource management.",
        tools=[base_toolbox["repo"]]
    )
    
    growth = _mk_asset_agent(
        role="Growth",
        goal="Generate landing copy and content pack using shared assets and CTA templates.",
        backstory="Growth marketer with collaborative resource management.",
        tools=[base_toolbox["landing"], base_toolbox["content"]]
    )
    
    brand = _mk_asset_agent(
        role="Brand",
        goal="Define project identity, create logos, and establish brand guidelines using shared assets.",
        backstory="Brand strategist with collaborative resource management.",
        tools=[]
    )
    
    # Asset curator agent
    asset_curator = _mk_asset_agent(
        role="Asset Curator",
        goal="Manage shared asset ecosystem and ensure quality standards.",
        backstory=asset_prompts["asset_curator"],
        tools=[]
    )
    
    # Brand asset manager agent
    brand_asset_manager = _mk_asset_agent(
        role="Brand Asset Manager",
        goal="Create comprehensive brand assets including logos, guidelines, and templates.",
        backstory=asset_prompts["brand_asset_manager"],
        tools=[]
    )
    
    # Create asset-enhanced tasks
    def _create_asset_enhanced_task(agent, description, context_tasks=None):
        """Create task with asset management integration."""
        enhanced_description = f"""
{description}

ASSET MANAGEMENT INTEGRATION:
1. Before creating resources: Use search_assets() to find reusable assets
2. When creating brand assets: Use create_logo() with proper brand specifications
3. When setting up deployment: Use create_hosting_info() for reproducible hosting
4. When creating marketing: Use create_cta_template() for conversion optimization
5. Use assets consistently: Record usage with use_asset() for tracking

COLLABORATIVE RESOURCE CREATION:
- Create reusable assets that benefit multiple agents and projects
- Use get_logos_for_brand() to maintain brand consistency
- Use get_hosting_options() to find optimal deployment solutions
- Use get_cta_templates() to access conversion-optimized templates
- Share assets that solve common problems across the ecosystem

ASSET SHARING STRATEGY:
- Make assets discoverable through proper categorization and tagging
- Include comprehensive metadata for easy search and reuse
- Create variations (logos, CTAs) for different use cases and platforms
- Provide hosting information for reproducible deployments
- Track asset usage and popularity to identify high-value resources

QUALITY STANDARDS:
- Ensure all assets meet technical and quality requirements
- Provide assets in multiple formats for maximum compatibility
- Include usage guidelines and best practices for asset application
- Maintain brand consistency across all created assets
- Create assets that are scalable and future-proof

Focus on CREATING AND SHARING HIGH-VALUE ASSETS that accelerate development for all agents.
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
    
    # Create asset-enhanced tasks
    research_task = _create_asset_enhanced_task(
        researcher,
        description=f"""
You are Asset-Enhanced Researcher.

ENHANCED RESEARCH PROCESS:
1. Use search_assets() to find existing research templates and methodologies
2. Use web_search_and_summarize with sources: {sources_json}
3. Create reusable research assets when appropriate
4. Use asset management to share research methodologies
5. Record usage of research assets for tracking and improvement

ASSET-DRIVEN RESEARCH:
- Research methodology templates for consistent approach
- Signal processing frameworks that can be reused
- Pain extraction patterns documented as shareable assets
- Clustering methodologies optimized for different scenarios
- Research quality standards and best practices

COLLABORATIVE RESEARCH ASSETS:
- Create research frameworks that benefit other agents
- Share successful research methodologies and approaches
- Document research patterns and insights as reusable assets
- Provide research templates for different market scenarios
- Maintain research asset library for continuous improvement

Your research will benefit from and contribute to the shared asset ecosystem.
"""
    )
    
    analyst_task = _create_asset_enhanced_task(
        analyst,
        description=f"""
You are Asset-Enhanced Analyst.

ENHANCED ANALYSIS PROCESS:
1. Use search_assets() to find analysis frameworks and scoring models
2. Use scoring tools with research data enhanced by shared assets
3. Create reusable analysis assets when appropriate
4. Use get_hosting_options() to reference deployment considerations
5. Share analysis methodologies through asset management

ASSET-DRIVEN ANALYSIS:
- Analysis framework templates for consistent evaluation
- Scoring models that can be reused and customized
- Competitive analysis approaches documented as assets
- Idea evaluation criteria optimized for different domains
- Analysis quality standards and validation frameworks

COLLABORATIVE ANALYSIS ASSETS:
- Create analysis frameworks that benefit other agents
- Share scoring methodologies and evaluation criteria
- Document analysis patterns and insights as reusable assets
- Provide analysis templates for different market and product types
- Maintain analysis asset library for continuous improvement

Your analysis will leverage and contribute to the shared asset ecosystem.
""",
        context_tasks=[research_task]
    )
    
    product_task = _create_asset_enhanced_task(
        product,
        description=f"""
You are Asset-Enhanced Product agent.

ENHANCED PRODUCT PROCESS:
1. Use search_assets() to find PRD templates and product frameworks
2. Use analyst and research outputs enhanced by shared assets
3. Create reusable product assets when appropriate
4. Use get_logos_for_brand() to maintain brand consistency
5. Share product methodologies through asset management

ASSET-DRIVEN PRODUCT DEVELOPMENT:
- PRD templates that ensure consistency and completeness
- Product framework assets for different types and domains
- Feature prioritization models that can be reused
- User experience patterns documented as shareable assets
- Product quality standards and validation frameworks

COLLABORATIVE PRODUCT ASSETS:
- Create product frameworks that benefit other agents
- Share PRD templates and best practices
- Document product development patterns as reusable assets
- Provide product assets for different industries and models
- Maintain product asset library for continuous improvement

Your product work will leverage and contribute to the shared asset ecosystem.
""",
        context_tasks=[research_task, analyst_task]
    )
    
    tech_task = _create_asset_enhanced_task(
        tech,
        description=f"""
You are Asset-Enhanced Tech Lead.

ENHANCED TECHNICAL PROCESS:
1. Use search_assets() to find technical architectures and implementation patterns
2. Use product requirements enhanced by shared technical assets
3. Create reusable technical assets when appropriate
4. Use create_hosting_info() for deployment and infrastructure
5. Share technical solutions through asset management

ASSET-DRIVEN TECHNICAL DEVELOPMENT:
- Technical architecture templates for consistent design
- Implementation patterns that can be reused and customized
- Code quality standards and best practices documented as assets
- Deployment configurations optimized for different environments
- Technical specification templates for different technology stacks

COLLABORATIVE TECHNICAL ASSETS:
- Create technical frameworks that benefit other agents
- Share architecture patterns and implementation solutions
- Document technical approaches and optimizations as reusable assets
- Provide technical assets for different platforms and requirements
- Maintain technical asset library for continuous improvement

Your technical work will leverage and contribute to the shared asset ecosystem.
""",
        context_tasks=[analyst_task, product_task]
    )
    
    growth_task = _create_asset_enhanced_task(
        growth,
        description=f"""
You are Asset-Enhanced Growth agent.

ENHANCED GROWTH PROCESS:
1. Use search_assets() to find marketing templates and CTA patterns
2. Use create_cta_template() for conversion-optimized call-to-actions
3. Use product and brand outputs enhanced by shared assets
4. Use get_logos_for_brand() to maintain brand consistency in marketing
5. Share marketing assets through asset management

ASSET-DRIVEN GROWTH MARKETING:
- CTA templates optimized for different platforms and audiences
- Landing page templates that ensure consistency and conversion
- Content frameworks that can be reused and customized
- Marketing automation templates for different campaigns
- Growth strategy assets for different market scenarios

COLLABORATIVE GROWTH ASSETS:
- Create marketing frameworks that benefit other agents
- Share CTA templates and conversion optimization strategies
- Document growth patterns and successful campaigns as assets
- Provide marketing assets for different industries and platforms
- Maintain growth asset library for continuous improvement

Your growth work will leverage and contribute to the shared asset ecosystem.
""",
        context_tasks=[product_task]
    )
    
    brand_task = _create_asset_enhanced_task(
        brand,
        description=f"""
You are Asset-Enhanced Brand agent.

ENHANCED BRANDING PROCESS:
1. Use search_assets() to find brand guidelines and identity frameworks
2. Use create_logo() to create comprehensive brand logo suites
3. Use product and growth outputs enhanced by shared brand assets
4. Create brand guidelines and asset packages for consistency
5. Share brand assets through asset management

ASSET-DRIVEN BRAND DEVELOPMENT:
- Logo suites with multiple variations for different use cases
- Brand guideline templates for consistent application
- Color palette and typography assets for brand consistency
- Brand application examples and usage guidelines
- Identity frameworks that can be customized for different brands

COLLABORATIVE BRAND ASSETS:
- Create brand frameworks that benefit other agents
- Share logo variations and brand identity elements
- Document branding patterns and successful strategies as assets
- Provide brand assets for different industries and company types
- Maintain brand asset library for continuous improvement

Your brand work will leverage and contribute to the shared asset ecosystem.
""",
        context_tasks=[product_task, growth_task]
    )
    
    # Asset management tasks
    asset_curation_task = Task(
        description=f"""
You are Asset Curator managing the shared asset ecosystem.

CURATION RESPONSIBILITIES:
1. Review and approve asset submissions for quality and relevance
2. Organize assets into logical categories and tagging systems
3. Monitor asset usage and popularity to identify high-value resources
4. Maintain asset library health and remove outdated assets
5. Generate insights on asset effectiveness and adoption

QUALITY ASSURANCE:
- Ensure all assets meet minimum quality standards
- Validate technical specifications and compatibility
- Check for proper licensing and usage rights
- Review asset metadata for completeness and accuracy
- Test assets for functionality and performance

ORGANIZATION OPTIMIZATION:
- Maintain consistent categorization and tagging systems
- Identify and fill gaps in the asset library
- Create collections and featured asset sets
- Optimize search and discovery mechanisms
- Generate usage analytics and popularity metrics

RESOURCE GOVERNANCE:
- Establish asset creation guidelines and standards
- Monitor asset lifecycle and manage deprecation
- Facilitate asset versioning and update processes
- Ensure assets support diverse use cases and platforms
- Generate insights on asset effectiveness and adoption

Your role is to ensure the SHARED ASSET SYSTEM delivers maximum value through quality, organization, and accessibility.
""",
        agent=asset_curator,
        expected_output="JSON"
    )
    
    brand_asset_management_task = Task(
        description=f"""
You are Brand Asset Manager creating comprehensive brand resources.

BRAND ASSET CREATION:
1. Use create_logo() to create complete logo suites for brands
2. Develop brand guidelines and asset usage standards
3. Ensure brand consistency across all created assets
4. Provide brand assets in multiple formats for different use cases
5. Create brand-specific hosting and CTA templates

BRAND CONSISTENCY:
- Maintain consistent color palettes, typography, and design language
- Ensure all brand assets work together harmoniously
- Create scalable assets that work across different sizes and contexts
- Provide clear usage guidelines and brand standards
- Consider brand application across different platforms and media

ASSET DELIVERABLES:
- Logo variations (primary, secondary, icon, monogram, favicon)
- Color palette definitions and usage guidelines
- Typography specifications and pairing rules
- Brand application examples and templates
- Platform-specific adaptations and requirements
- Brand guidelines documentation and usage standards

COLLABORATIVE BRAND DEVELOPMENT:
- Share brand assets with other agents for consistent application
- Provide brand guidelines for proper asset usage
- Create brand-specific templates for common use cases
- Ensure brand assets support diverse marketing needs
- Maintain brand versioning and update processes

Your role is to CREATE COMPREHENSIVE BRAND ASSETS that ensure consistent, professional brand representation.
""",
        agent=brand_asset_manager,
        expected_output="JSON"
    )
    
    # Import MLP agents if enabled
    mlp_agents = []
    mlp_tasks = []
    
    if settings.get('MLP_ENABLED', False):
        try:
            from ..agents.loveability_engineer import LoveabilityEngineerAgent
            from ..agents.ux_specialist import UXSpecialistAgent
            from ..agents.emotional_designer import EmotionalDesignerAgent
            
            # Create MLP agents
            loveability_engineer = LoveabilityEngineerAgent(llm_client)
            ux_specialist = UXSpecialistAgent(llm_client)
            emotional_designer = EmotionalDesignerAgent(llm_client)
            
            mlp_agents = [
                loveability_engineer.agent,
                ux_specialist.agent,
                emotional_designer.agent
            ]
            
            # Create MLP tasks
            product_task = next((task for task in [product_task] if task), None)
            tech_task = next((task for task in [tech_task] if task), None)
            
            if product_task:
                loveability_task = loveability_engineer.create_loveability_strategy_task({
                    'product_type': 'mlp',
                    'emotional_theme': settings.get('PRIMARY_EMOTIONAL_THEME', 'joy')
                })
                loveability_task.context_tasks = [product_task]
                mlp_tasks.append(loveability_task)
                
                ux_task = ux_specialist.create_seamless_userflow_task(
                    product_task.output if hasattr(product_task, 'output') else {},
                    tech_task.output if hasattr(tech_task, 'output') else {}
                )
                ux_task.context_tasks = [product_task]
                mlp_tasks.append(ux_task)
                
                emotional_task = emotional_designer.create_emotional_onboarding_task({
                    'emotional_theme': settings.get('PRIMARY_EMOTIONAL_THEME', 'joy')
                })
                emotional_task.context_tasks = [product_task]
                mlp_tasks.append(emotional_task)
            
            logger.info(f"MLP agents integrated: {len(mlp_agents)} agents, {len(mlp_tasks)} tasks")
            
        except ImportError as e:
            logger.warning(f"Failed to import MLP agents: {e}")
    
    # Create asset-enhanced crew with MLP integration
    asset_enhanced_crew = Crew(
        agents=[
            asset_curator,
            brand_asset_manager,
            researcher,
            analyst,
            product,
            tech,
            growth,
            brand,
            *mlp_agents  # Add MLP agents if enabled
        ],
        tasks=[
            asset_curation_task,
            brand_asset_management_task,
            research_task,
            analyst_task,
            product_task,
            tech_task,
            growth_task,
            brand_task,
            *mlp_tasks  # Add MLP tasks if enabled
        ],
        verbose=True,
        process="hierarchical"  # Asset management first, then parallel execution
    )
    
    # Run asset-enhanced crew
    try:
        asset_enhanced_crew.kickoff()
        
        # Get asset statistics
        asset_stats = asset_manager.get_asset_statistics()
        
        # Parse outputs with asset integration
        outputs = {
            "asset_curation": _parse_json_safe(getattr(asset_curation_task, "output", "")),
            "brand_asset_management": _parse_json_safe(getattr(brand_asset_management_task, "output", "")),
            "research": _parse_json_safe(getattr(research_task, "output", "")),
            "analysis": _parse_json_safe(getattr(analyst_task, "output", "")),
            "product": _parse_json_safe(getattr(product_task, "output", "")),
            "tech": _parse_json_safe(getattr(tech_task, "output", "")),
            "growth": _parse_json_safe(getattr(growth_task, "output", "")),
            "brand": _parse_json_safe(getattr(brand_task, "output", "")),
            "shared_assets": {
                "statistics": asset_stats,
                "total_assets": asset_stats.get("total_assets", 0),
                "by_type": asset_stats.get("by_type", {}),
                "total_usage": asset_stats.get("total_usage", 0),
                "asset_library_health": "tracked through curation"
            }
        }
        
        logger.info(f"Asset-enhanced crew pipeline completed with {asset_stats.get('total_assets', 0)} assets created/shared")
        return outputs
        
    except Exception as exc:
        logger.warning(f"Asset-enhanced crew kickoff failed, using fallback: {exc}")
        return {"errors": "Asset-enhanced crew execution failed"}


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
