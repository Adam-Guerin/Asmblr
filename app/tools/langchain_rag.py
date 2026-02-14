"""LangChain tool wrapper for local RAG playbook QA."""
from __future__ import annotations

from pathlib import Path

from langchain.tools import BaseTool
from pydantic import BaseModel, PrivateAttr

from app.tools.rag import RAGPlaybookQA


class RAGArgs(BaseModel):
    """Arguments for rag_playbook_qa tool."""

    question: str


class RAGPlaybookQATool(BaseTool):
    """Answer questions using local playbook content."""

    name: str = "rag_playbook_qa"
    description: str = "Answer questions using local playbook (TF-IDF fallback)."
    args_schema: type[BaseModel] = RAGArgs
    _rag: RAGPlaybookQA = PrivateAttr()

    def __init__(self, knowledge_dir: Path) -> None:
        super().__init__()
        object.__setattr__(self, "_rag", RAGPlaybookQA(knowledge_dir))

    def _run(self, question: str) -> str:
        """Execute the RAG lookup and return text response."""
        return self._rag.query(question)
