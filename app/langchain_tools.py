"""Toolbox wiring for LangChain tool adapters."""
from __future__ import annotations


from langchain.tools import BaseTool

from app.core.llm import LLMClient
from app.tools.langchain_generation import (
    RepoGeneratorTool,
    LandingGeneratorTool,
    ContentGeneratorTool,
)
from app.tools.langchain_rag import RAGPlaybookQATool
from app.tools.langchain_scoring import ScoringEngineTool
from app.tools.langchain_web import WebSearchAndSummarizeTool, CompetitorExtractorTool


def build_toolbox(settings, llm: LLMClient, judge_prompt: str) -> dict[str, BaseTool]:
    """Construct the LangChain tool registry for agent execution."""
    return {
        "web": WebSearchAndSummarizeTool(),
        "competitor": CompetitorExtractorTool(),
        "rag": RAGPlaybookQATool(settings.knowledge_dir),
        "scoring": ScoringEngineTool(
            llm,
            judge_prompt=judge_prompt,
            primary_icp=getattr(settings, "primary_icp", ""),
            primary_icp_keywords=getattr(settings, "primary_icp_keywords", ""),
            icp_alignment_bonus_max=getattr(settings, "icp_alignment_bonus_max", 0),
        ),
        "repo": RepoGeneratorTool(),
        "landing": LandingGeneratorTool(llm),
        "content": ContentGeneratorTool(llm),
    }
