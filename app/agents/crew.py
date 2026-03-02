import json
import re
from pathlib import Path
from typing import Any

from loguru import logger

try:
    from crewai import Agent, Task, Crew
except Exception:  # pragma: no cover
    Agent = None
    Task = None
    Crew = None

from langchain_core.messages import AIMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.outputs import ChatGeneration, ChatResult

from app.core.config import Settings
from app.core.models import SeedInputs
from app.core.llm import LLMClient
from app.agents.skills import build_agent_skill_guidance
from app.langchain_tools import build_toolbox


def _validate_icp_settings(primary_icp: str, primary_icp_keywords: str) -> tuple[str, str]:
    """
    Validate and normalize ICP settings.
    
    Args:
        primary_icp: The primary ICP string from settings
        primary_icp_keywords: The comma-separated keywords string
        
    Returns:
        Tuple of (validated_icp, validated_keywords)
        
    Raises:
        ValueError: If ICP settings are invalid
    """
    # Validate primary_icp
    if not primary_icp or not primary_icp.strip():
        raise ValueError("PRIMARY_ICP cannot be empty or whitespace only")
    
    primary_icp = primary_icp.strip()
    
    # Basic validation - ICP should contain meaningful content
    if len(primary_icp) < 10:
        raise ValueError("PRIMARY_ICP is too short (minimum 10 characters)")
    
    if len(primary_icp) > 200:
        raise ValueError("PRIMARY_ICP is too long (maximum 200 characters)")
    
    # Check for obviously invalid content
    invalid_patterns = ["test", "example", "dummy", "placeholder", "none", "unknown"]
    icp_lower = primary_icp.lower()
    if any(pattern in icp_lower for pattern in invalid_patterns):
        # Only flag if the ICP is primarily made of these invalid words
        words = icp_lower.split()
        if any(word in invalid_patterns for word in words):
            raise ValueError(f"PRIMARY_ICP contains invalid placeholder value: '{primary_icp}'")
    
    # Validate primary_icp_keywords
    if not primary_icp_keywords or not primary_icp_keywords.strip():
        raise ValueError("PRIMARY_ICP_KEYWORDS cannot be empty or whitespace only")
    
    primary_icp_keywords = primary_icp_keywords.strip()
    
    # Parse and validate keywords
    keywords = [k.strip() for k in primary_icp_keywords.split(",") if k.strip()]
    
    if len(keywords) < 3:
        raise ValueError("PRIMARY_ICP_KEYWORDS must contain at least 3 valid keywords")
    
    if len(keywords) > 20:
        raise ValueError("PRIMARY_ICP_KEYWORDS contains too many keywords (maximum 20)")
    
    # Validate individual keywords
    for keyword in keywords:
        if len(keyword) < 2:
            raise ValueError(f"Keyword '{keyword}' is too short (minimum 2 characters)")
        if len(keyword) > 50:
            raise ValueError(f"Keyword '{keyword}' is too long (maximum 50 characters)")
        # Allow letters, numbers, hyphens, underscores, and spaces
        if not keyword.replace("-", "").replace("_", "").replace(" ", "").isalnum():
            raise ValueError(f"Keyword '{keyword}' contains invalid characters (only letters, numbers, hyphens, underscores, and spaces allowed)")
    
    # Reconstruct clean keywords string
    clean_keywords = ",".join(keywords)
    
    logger.info(
        "ICP settings validated",
        icp=primary_icp,
        keyword_count=len(keywords),
        keywords_sample=keywords[:3]  # Log first 3 keywords for debugging
    )
    
    return primary_icp, clean_keywords


class FallbackChatModel(BaseChatModel):
    """Deterministic fallback to keep CrewAI runnable in tests/offline environments."""

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        content = self._respond(messages)
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])

    def _respond(self, messages) -> str:
        prompt = "\n".join([m.content for m in messages if hasattr(m, "content")])
        if "Researcher" in prompt:
            return json.dumps({
                "pain_statements": ["Teams struggle to prioritize ideas quickly."],
                "clusters": {"0": ["Teams struggle to prioritize ideas quickly."]},
                "ideas": [
                    {
                        "name": "Idea 1: Venture Ops Toolkit",
                        "one_liner": "Automate scoring and launch packs.",
                        "target_user": "Small teams",
                        "problem": "Idea prioritization is slow",
                        "solution": "Collect signals and score ideas",
                        "key_features": ["signals", "scoring", "launch pack"],
                    }
                ],
                "sources": [],
                "pages": [],
            })
        if "Analyst" in prompt:
            return json.dumps({
                "ideas": [],
                "scores": [],
                "top_idea": {"name": "Idea 1: Venture Ops Toolkit", "score": 70, "rationale": "Fallback"},
                "competitors": [],
            })
        if "Product" in prompt:
            return json.dumps({"prd_markdown": "# PRD\n\nFallback PRD."})
        if "Tech Lead" in prompt:
            return json.dumps({"tech_spec_markdown": "# Tech Spec\n\nFallback Tech Spec.", "repo_dir": ""})
        if "Growth" in prompt:
            return json.dumps({"landing_dir": "", "content_dir": ""})
        return "{}"

    @property
    def _llm_type(self) -> str:  # pragma: no cover - required by base class
        return "fallback-chat"


def _load_prompt(name: str) -> str:
    path = Path(__file__).resolve().parents[1] / "prompts" / f"{name}.txt"
    return path.read_text(encoding="utf-8")

def _format_seed_summary(seeds: SeedInputs | None) -> str:
    if not seeds:
        return ""
    parts: list[str] = []
    if seeds.theme:
        parts.append(f"Theme: {seeds.theme}")
    if seeds.icp:
        parts.append(f"ICP: {seeds.icp}")
    if seeds.context:
        parts.append(f"Context: {seeds.context}")
    for pain in seeds.pains:
        parts.append(f"Seed pain: {pain}")
    for competitor in seeds.competitors:
        parts.append(f"Seed competitor: {competitor}")
    return "\n".join(parts)


def _parse_json_safe(text: str) -> dict[str, Any]:
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


def _load_sources(settings: Settings) -> list[dict[str, str]]:
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


def run_crewai_pipeline(
    topic: str,
    settings: Settings,
    llm_client: LLMClient,
    run_id: str,
    n_ideas: int,
    fast_mode: bool,
    seed_pages: list[dict[str, Any]] | None = None,
    seed_competitor_pages: list[dict[str, Any]] | None = None,
    seed_inputs: SeedInputs | None = None,
    validated_pains: list[str] | None = None,
) -> dict[str, Any]:
    if Agent is None or Task is None or Crew is None:
        logger.warning("CrewAI not available; returning empty outputs")
        return {"errors": "CrewAI not available"}

    if fast_mode:
        n_ideas = 3

    llm = llm_client._client if llm_client.available() else FallbackChatModel()
    seeds = seed_inputs or SeedInputs()
    validated_pains = validated_pains or []
    seed_summary = _format_seed_summary(seeds)
    validated_hint = ", ".join(validated_pains[:5]) if validated_pains else "none"
    validated_texts = [pain for pain in validated_pains if pain]
    validated_pain_summary = "\n".join(f"- {pain}" for pain in validated_texts[:5]) or "- None provided."
    
    # Validate ICP settings
    try:
        primary_icp_raw = (getattr(settings, "primary_icp", "") or "").strip()
        primary_icp_keywords_raw = (getattr(settings, "primary_icp_keywords", "") or "").strip()
        
        if primary_icp_raw or primary_icp_keywords_raw:
            # Only validate if at least one ICP setting is provided
            primary_icp, primary_icp_keywords = _validate_icp_settings(
                primary_icp_raw, primary_icp_keywords_raw
            )
        else:
            # No ICP configured - use defaults
            primary_icp = ""
            primary_icp_keywords = ""
            logger.warning("No ICP settings configured - using generic approach")
    except ValueError as e:
        logger.error("ICP validation failed: {error}", error=str(e))
        # Fall back to defaults but log the issue
        primary_icp = ""
        primary_icp_keywords = ""
        logger.warning("Falling back to generic approach due to invalid ICP settings")
    
    icp_focus_hint = primary_icp or "none"
    icp_keyword_hint = primary_icp_keywords or "none"

    judge_prompt = _load_prompt("llm_judge_scoring")
    toolbox = build_toolbox(settings, llm_client, judge_prompt)

    sources = _load_sources(settings)
    competitor_sources = [s for s in sources if s.get("section") == "competitor_sources"]
    if seed_pages is None:
        try:
            seed_pages = json.loads(
                toolbox["web"].run(
                    {
                        "sources": sources,
                        "max_sources": 3 if fast_mode else settings.max_sources,
                        "cache_dir": str(settings.data_dir / "cache"),
                        "timeout": settings.request_timeout,
                        "rate_limit_per_domain": settings.rate_limit_per_domain,
                        "retry_max_attempts": settings.retry_max_attempts,
                        "retry_min_wait": settings.retry_min_wait,
                        "retry_max_wait": settings.retry_max_wait,
                    }
                )
            )
        except Exception:
            seed_pages = []

    if seed_competitor_pages is None and competitor_sources:
        try:
            seed_competitor_pages = json.loads(
                toolbox["web"].run(
                    {
                        "sources": competitor_sources,
                        "max_sources": len(competitor_sources),
                        "cache_dir": str(settings.data_dir / "cache"),
                        "timeout": settings.request_timeout,
                        "rate_limit_per_domain": settings.rate_limit_per_domain,
                        "retry_max_attempts": settings.retry_max_attempts,
                        "retry_min_wait": settings.retry_min_wait,
                        "retry_max_wait": settings.retry_max_wait,
                    }
                )
            )
        except Exception:
            seed_competitor_pages = []

    sources_json = json.dumps(sources, indent=2)
    competitor_json = json.dumps(competitor_sources, indent=2)
    seed_pages_json = json.dumps(seed_pages or [], indent=2)
    seed_competitor_json = json.dumps(seed_competitor_pages or [], indent=2)

    runs_dir = str(settings.runs_dir / run_id)
    template_dir = str(Path(__file__).resolve().parents[2] / "templates")

    idea_prompt = _load_prompt("idea_generation").replace("{{n_ideas}}", str(n_ideas))
    if primary_icp:
        idea_prompt += (
            "\n\nICP FOCUS\n"
            f"- Primary ICP: {primary_icp}\n"
            f"- ICP keywords to prefer in naming, target_user, problem framing: {icp_keyword_hint}\n"
            "- Reject ideas that are not clearly relevant to this ICP."
        )
    prd_prompt = _load_prompt("prd_writer")
    tech_prompt = _load_prompt("tech_spec_writer")
    landing_prompt = _load_prompt("landing_copy")
    content_prompt = _load_prompt("content_pack")
    brand_prompt = _load_prompt("brand_identity")

    def _with_skill_guidance(description: str, role: str) -> str:
        guidance = build_agent_skill_guidance(role, settings)
        if not guidance:
            return description
        return f"{description}\n\n{guidance}"

    def _mk_agent(role, goal, backstory, tools):
        try:
            return Agent(role=role, goal=goal, backstory=backstory, tools=tools, llm=llm)
        except Exception:
            return Agent(role=role, goal=goal, backstory=backstory, tools=[], llm=llm)

    researcher = _mk_agent(
        role="Researcher",
        goal="Collect signals, extract pains, cluster, and generate product ideas.",
        backstory="Signal analyst focused on market pains.",
        tools=[toolbox["web"], toolbox["rag"]],
    )
    analyst = _mk_agent(
        role="Analyst",
        goal="Score ideas, evaluate competition, and pick top opportunities.",
        backstory="Quant-minded evaluator.",
        tools=[toolbox["scoring"], toolbox["competitor"]],
    )
    product = _mk_agent(
        role="Product",
        goal="Produce a clear PRD with ICP/JTBD/MVP scope.",
        backstory="Product strategist.",
        tools=[toolbox["rag"]],
    )
    tech = _mk_agent(
        role="Tech Lead",
        goal="Write technical spec and generate buildable repo skeleton.",
        backstory="Senior engineer.",
        tools=[toolbox["repo"]],
    )
    growth = _mk_agent(
        role="Growth",
        goal="Generate landing copy and content pack for launch.",
        backstory="Growth marketer.",
        tools=[toolbox["landing"], toolbox["content"]],
    )
    brand = _mk_agent(
        role="Brand",
        goal="Define project name, art direction (DA), and create a simple logo.",
        backstory="Brand strategist and visual designer.",
        tools=[],
    )

    research_task = Task(
        description=_with_skill_guidance(
            (
            f"You are the Researcher. Use tool `web_search_and_summarize` with args: "
            f"{{\"sources\": {sources_json}, \"max_sources\": {3 if fast_mode else settings.max_sources}, "
            f"\"cache_dir\": \"{settings.data_dir / 'cache'}\", \"timeout\": {settings.request_timeout}, "
            f"\"rate_limit_per_domain\": {settings.rate_limit_per_domain}}}. "
            f"Pre-collected pages (if any): {seed_pages_json}. "
            f"Seed hypotheses (data_source=seed): {seed_summary or 'none provided'}. "
            f"Primary ICP focus: {icp_focus_hint}. ICP keywords: {icp_keyword_hint}. "
            f"Validated pains: {validated_hint}. "
            "Extract at least 30 pain statements (or fewer if fast mode). Cluster them. "
            "Use `rag_playbook_qa` with question 'idea generation playbook' for guidance. "
            f"Then generate {n_ideas} product ideas using this prompt:\n{idea_prompt}\n" 
            "Return JSON with keys: pain_statements, clusters, ideas, sources, pages. "
            "If data missing, set 'unknown' and state assumptions."
            ),
            "Researcher",
        ),
        agent=researcher,
        expected_output="JSON",
    )

    analyst_task = Task(
        description=_with_skill_guidance(
            (
            "You are the Analyst. Use pain_statements and ideas from the Researcher. "
            f"Seed hypotheses (data_source=seed): {seed_summary or 'none provided'}. "
            f"Primary ICP focus: {icp_focus_hint}. ICP keywords: {icp_keyword_hint}. "
            f"Validated pains to weigh: {validated_hint}. "
            "Call `scoring_engine` with {pain_statements, ideas}. "
            "First call `web_search_and_summarize` on competitor sources, then pass the returned pages to "
            "`competitor_extractor` (or pass competitor URLs directly). "
            f"Competitor sources: {competitor_json}. Pre-collected competitor pages: {seed_competitor_json}. "
            "Pick top 1-2 ideas by score and return JSON with keys: ideas, scores, top_idea, competitors."
            ),
            "Analyst",
        ),
        agent=analyst,
        context=[research_task],
        expected_output="JSON",
    )

    product_task = Task(
        description=_with_skill_guidance(
            (
            "You are the Product agent. Use top_idea and pain statements from Analyst/Researcher. "
            f"Primary ICP to enforce in PRD scope and language: {icp_focus_hint}. "
            f"Validated pains (priority):\n{validated_pain_summary}\n"
            f"Competitor cues: {competitor_json}. "
            "Ensure every section references at least one validated pain and explains how we differentiate from competitors. "
            "Write a PRD using this prompt:\n{prd_prompt}\n"
            "Return JSON with key prd_markdown."
            ),
            "Product",
        ),
        agent=product,
        context=[research_task, analyst_task],
        expected_output="JSON",
    )

    tech_task = Task(
        description=_with_skill_guidance(
            (
            "You are the Tech Lead. Use top_idea to write a technical spec. "
            f"Validated pains (priority):\n{validated_pain_summary}\n"
            f"Competitor cues: {competitor_json}. "
            "Tie the architecture/stack to those pains and explain how the API surface and data flow create competitive advantage. "
            f"Prompt:\n{tech_prompt}\n"
            f"Then call `repo_generator` with {{\"project_name\": top_idea.name, \"output_dir\": \"{runs_dir}/repo_skeleton\", \"fast_mode\": {str(fast_mode).lower()}}}. "
            "Return JSON with keys: tech_spec_markdown, repo_dir."
            ),
            "Tech Lead",
        ),
        agent=tech,
        context=[analyst_task],
        expected_output="JSON",
    )

    growth_task = Task(
        description=_with_skill_guidance(
            (
            "You are the Growth agent. Use top_idea to generate landing copy and content pack. "
            f"Primary ICP to enforce in messaging: {icp_focus_hint}. "
            f"Prompt for landing:\n{landing_prompt}\nPrompt for content:\n{content_prompt}\n"
            f"Call `landing_generator` with {{\"product_name\": top_idea.name, \"output_dir\": \"{runs_dir}/landing_page\", "
            f"\"template_dir\": \"{template_dir}\", \"prompt\": landing_prompt, \"fast_mode\": {str(fast_mode).lower()}}}. "
            f"Call `content_generator` with {{\"product_name\": top_idea.name, \"output_dir\": \"{runs_dir}/content_pack\", "
            f"\"prompt\": content_prompt, \"fast_mode\": {str(fast_mode).lower()}}}. "
            "Return JSON with keys: landing_dir, content_dir."
            ),
            "Growth",
        ),
        agent=growth,
        context=[analyst_task],
        expected_output="JSON",
    )

    brand_task = Task(
        description=_with_skill_guidance(
            (
            "You are the Brand agent. Use top_idea and pain statements to define a project name, DA (direction artistique), "
            "and a simple logo. "
            f"Prompt:\n{brand_prompt}\n"
            "Return strict JSON with keys: project_name, name_rationale, brand_direction, brand_keywords, "
            "color_palette, typography, logo_prompt, logo_palette, logo_svg, logo_description, usage_notes."
            ),
            "Brand",
        ),
        agent=brand,
        context=[research_task, analyst_task],
        expected_output="JSON",
    )

    crew = Crew(
        agents=[researcher, analyst, product, tech, growth, brand],
        tasks=[research_task, analyst_task, product_task, tech_task, growth_task, brand_task],
        verbose=False,
    )
    try:
        crew.kickoff()
        outputs = {
            "research": _parse_json_safe(getattr(research_task, "output", "")),
            "analysis": _parse_json_safe(getattr(analyst_task, "output", "")),
            "product": _parse_json_safe(getattr(product_task, "output", "")),
            "tech": _parse_json_safe(getattr(tech_task, "output", "")),
            "growth": _parse_json_safe(getattr(growth_task, "output", "")),
            "brand": _parse_json_safe(getattr(brand_task, "output", "")),
        }
    except Exception as exc:
        logger.warning("Crew kickoff failed, using fallback outputs: {err}", err=exc)
        outputs = {
            "research": {
                "pain_statements": ["Teams struggle to prioritize ideas quickly."],
                "clusters": {"0": ["Teams struggle to prioritize ideas quickly."]},
                "ideas": [
                    {
                        "name": "Idea 1: Venture Ops Toolkit",
                        "one_liner": "Automate scoring and launch packs.",
                        "target_user": "Small teams",
                        "problem": "Idea prioritization is slow",
                        "solution": "Collect signals and score ideas",
                        "key_features": ["signals", "scoring", "launch pack"],
                    }
                ],
                "sources": [],
                "pages": seed_pages or [],
            },
            "analysis": {
                "ideas": [{"name": "Idea 1: Venture Ops Toolkit"}],
                "scores": [{"name": "Idea 1: Venture Ops Toolkit", "score": 70, "rationale": "Fallback", "risks": []}],
                "top_idea": {"name": "Idea 1: Venture Ops Toolkit", "score": 70, "rationale": "Fallback"},
                "competitors": [],
            },
            "product": {"prd_markdown": "# PRD\n\nFallback PRD."},
            "tech": {"tech_spec_markdown": "# Tech Spec\n\nFallback Tech Spec.", "repo_dir": ""},
            "growth": {"landing_dir": "", "content_dir": ""},
            "brand": {
                "project_name": "Idea 1: Venture Ops Toolkit",
                "name_rationale": "Keeps the original top idea name as the baseline.",
                "brand_direction": "Clean, pragmatic, early-stage builder vibe.",
                "brand_keywords": ["pragmatic", "lean", "clear", "builder"],
                "color_palette": [
                    {"name": "Ink", "hex": "#111111", "use": "primary text"},
                    {"name": "Slate", "hex": "#6B7280", "use": "secondary text"},
                    {"name": "Signal", "hex": "#22C55E", "use": "accent"},
                    {"name": "Paper", "hex": "#F9FAFB", "use": "background"},
                ],
                "typography": {"headline": "Space Grotesk", "body": "Inter"},
                "logo_prompt": "Minimal monogram logo, bold geometric shape, max 3 colors, flat vector style.",
                "logo_palette": ["#111111", "#22C55E", "#F9FAFB"],
                "logo_svg": "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"120\" height=\"120\" viewBox=\"0 0 120 120\"><rect width=\"120\" height=\"120\" rx=\"18\" fill=\"#111111\"/><text x=\"60\" y=\"72\" font-size=\"56\" font-family=\"Arial, sans-serif\" fill=\"#F9FAFB\" text-anchor=\"middle\">A</text></svg>",
                "logo_description": "Monogram in a rounded square for a clean, builder-first feel.",
                "usage_notes": ["Use the monogram for favicon and app icon."],
            },
        }

    top_name = (
        outputs.get("analysis", {}).get("top_idea", {}).get("name")
        or (outputs.get("analysis", {}).get("ideas") or [{}])[0].get("name")
        or (outputs.get("research", {}).get("ideas") or [{}])[0].get("name")
        or "unknown"
    )

    if seed_competitor_pages and not outputs.get("analysis", {}).get("competitors"):
        try:
            comp = json.loads(toolbox["competitor"].run({"pages": seed_competitor_pages}))
            outputs.setdefault("analysis", {})["competitors"] = comp
        except Exception:
            pass

    repo_dir = outputs.get("tech", {}).get("repo_dir") or str(Path(runs_dir) / "repo_skeleton")
    if not Path(repo_dir).exists():
        toolbox["repo"].run({"project_name": top_name, "output_dir": repo_dir, "fast_mode": fast_mode})
        outputs.setdefault("tech", {})["repo_dir"] = repo_dir

    landing_dir = outputs.get("growth", {}).get("landing_dir") or str(Path(runs_dir) / "landing_page")
    if not Path(landing_dir).exists():
        toolbox["landing"].run(
            {
                "product_name": top_name,
                "output_dir": landing_dir,
                "template_dir": template_dir,
                "prompt": landing_prompt,
                "fast_mode": fast_mode,
            }
        )
        outputs.setdefault("growth", {})["landing_dir"] = landing_dir

    content_dir = outputs.get("growth", {}).get("content_dir") or str(Path(runs_dir) / "content_pack")
    if not Path(content_dir).exists():
        toolbox["content"].run(
            {
                "product_name": top_name,
                "output_dir": content_dir,
                "prompt": content_prompt,
                "fast_mode": fast_mode,
            }
        )
        outputs.setdefault("growth", {})["content_dir"] = content_dir

    return outputs
