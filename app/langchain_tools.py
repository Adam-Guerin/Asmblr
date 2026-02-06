"""Toolbox wiring for LangChain tool adapters."""
from __future__ import annotations

from typing import Dict

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


def build_toolbox(settings, llm: LLMClient, judge_prompt: str) -> Dict[str, BaseTool]:
    """Construct the LangChain tool registry for agent execution."""
    return {
        "web": WebSearchAndSummarizeTool(),
        "competitor": CompetitorExtractorTool(),
        "rag": RAGPlaybookQATool(settings.knowledge_dir),
        "scoring": ScoringEngineTool(llm, judge_prompt=judge_prompt),
        "repo": RepoGeneratorTool(),
        "landing": LandingGeneratorTool(llm),
        "content": ContentGeneratorTool(llm),
    }
