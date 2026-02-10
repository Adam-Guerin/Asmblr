"""LangChain tools for repo, landing page, and content generation."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from langchain.tools import BaseTool
from pydantic import BaseModel

from app.core.llm import LLMClient
from app.tools.repo_generator import generate_fastapi_skeleton
from app.tools.generator import (
    render_landing,
    generate_landing_copy,
    generate_content_pack,
    write_content_pack,
    default_landing_payload,
    default_content_pack,
)


class RepoArgs(BaseModel):
    """Arguments for repo_generator tool."""

    project_name: str
    output_dir: str
    fast_mode: bool = False


class RepoGeneratorTool(BaseTool):
    """Generate a minimal FastAPI repo skeleton."""

    name: str = "repo_generator"
    description: str = "Generate a minimal FastAPI repo skeleton. Returns output path."
    args_schema: type[BaseModel] = RepoArgs

    def _run(self, project_name: str, output_dir: str, fast_mode: bool = False) -> str:
        """Generate the repo skeleton and return the path as string."""
        target_dir = Path(output_dir)
        generate_fastapi_skeleton(target_dir, project_name, minimal=fast_mode)
        return str(target_dir)


class LandingArgs(BaseModel):
    """Arguments for landing_generator tool."""

    product_name: str
    output_dir: str
    template_dir: str
    prompt: str | None = None
    payload: dict[str, Any] | None = None
    fast_mode: bool = False


class LandingGeneratorTool(BaseTool):
    """Generate landing page HTML/CSS using templates and optional LLM copy."""

    name: str = "landing_generator"
    description: str = "Generate landing page HTML/CSS using templates and optional LLM copy. Returns output path."
    args_schema: type[BaseModel] = LandingArgs

    def __init__(self, llm: LLMClient) -> None:
        super().__init__()
        self._llm = llm

    def _run(
        self,
        product_name: str,
        output_dir: str,
        template_dir: str,
        prompt: str | None = None,
        payload: dict[str, Any] | None = None,
        fast_mode: bool = False,
    ) -> str:
        """Render landing assets and return output directory."""
        template_root = Path(template_dir)
        data = payload or default_landing_payload(product_name, fast_mode=fast_mode)
        if prompt:
            data = generate_landing_copy(self._llm, prompt, data)
        if "solution_summary" not in data and data.get("solution"):
            data["solution_summary"] = data.get("solution")
        if "solution_does" not in data and data.get("features"):
            data["solution_does"] = [
                item.get("title", "") for item in data.get("features", []) if isinstance(item, dict)
            ]
        data.setdefault("solution_summary", "")
        data.setdefault("solution_does", [])
        data.setdefault("solution_does_not", [])
        data.setdefault("why_now", "")
        data.setdefault("differentiation", [])
        data.setdefault("value_prop_5s", "")
        data.setdefault("social_proof_title", "Social proof")
        data.setdefault("social_proof_items", [])
        data.setdefault("objections", [])
        data.setdefault("cta_intent", "early_access")
        data.setdefault(
            "analytics",
            {
                "provider": "default_js",
                "events": ["page_view", "cta_click", "waitlist_submit"],
                "cta_event_name": "cta_click",
                "primary_conversion": "waitlist_submit",
            },
        )
        data.setdefault("category", "")
        data.setdefault("logo_src", "./logo.svg")
        data.setdefault("logo_alt", f"{product_name} logo")
        data.setdefault("cta_heading", data.get("cta_primary", ""))
        data.setdefault("cta_subhead", "")
        if fast_mode:
            data["solution_does"] = (data.get("solution_does") or [])[:2]
            data["solution_does_not"] = (data.get("solution_does_not") or [])[:2]
            data["social_proof_items"] = (data.get("social_proof_items") or [])[:1]
            data["objections"] = (data.get("objections") or [])[:1]
            data["faq"] = (data.get("faq") or [])[:2]
            data["why_now"] = ""
            data["differentiation"] = []
        render_landing(template_root, data, Path(output_dir))
        return str(output_dir)


class ContentArgs(BaseModel):
    """Arguments for content_generator tool."""

    product_name: str
    output_dir: str
    prompt: str | None = None
    content_pack: dict[str, Any] | None = None
    fast_mode: bool = False


class ContentGeneratorTool(BaseTool):
    """Generate content pack (posts, hooks, ads, script, calendar)."""

    name: str = "content_generator"
    description: str = "Generate content pack (posts, hooks, ads, script, calendar). Returns output path."
    args_schema: type[BaseModel] = ContentArgs

    def __init__(self, llm: LLMClient) -> None:
        super().__init__()
        self._llm = llm

    def _run(
        self,
        product_name: str,
        output_dir: str,
        prompt: str | None = None,
        content_pack: dict[str, Any] | None = None,
        fast_mode: bool = False,
    ) -> str:
        """Generate the content pack and return output directory."""
        pack = content_pack or default_content_pack(product_name, fast_mode=fast_mode)
        if prompt:
            pack = generate_content_pack(self._llm, prompt, pack)
        pack.setdefault("cta_primary", "Request early access")
        pack.setdefault("cta_intent", "early_access")
        pack.setdefault(
            "analytics_plan",
            {
                "primary_conversion": "waitlist_submit",
                "events": ["page_view", "cta_click", "waitlist_submit"],
                "utm_template": "utm_source={source}&utm_medium={medium}&utm_campaign={campaign}",
            },
        )
        if fast_mode:
            pack["posts"] = (pack.get("posts") or [])[:3]
            pack["hooks"] = (pack.get("hooks") or [])[:2]
            pack["ads"] = (pack.get("ads") or [])[:1]
        write_content_pack(Path(output_dir), pack)
        return str(output_dir)
