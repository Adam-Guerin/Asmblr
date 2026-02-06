from __future__ import annotations

from pathlib import Path
from typing import List

from app.core.llm import LLMClient
from app.loop.errors import LoopException
from app.loop.schemas import LoopPlan, PatchMetadata, PatchOutcome

PATCH_PROMPT = '''You are a controlled patch generator inside the Asmblr loop.
Goal: {goal}
Iteration: {iteration}
Plan steps:\n{steps}
Produce a precise git diff and nothing else. Keep each change minimal, avoid TODO comments, and never touch .env or binary files.''' 


class LoopPatcher:
    def __init__(self, llm: LLMClient, repo_root: Path) -> None:
        self.llm = llm
        self.repo_root = repo_root.resolve()

    def create_patch(self, goal: str, plan: LoopPlan, iteration: int) -> PatchOutcome:
        prompt = PATCH_PROMPT.format(goal=goal, iteration=iteration, steps='\n'.join(plan.steps))
        raw = self.llm.generate(prompt)
        return self._analyze(raw)

    def _analyze(self, patch_text: str) -> PatchOutcome:
        normalized = patch_text.strip()
        if not normalized:
            raise LoopException('LLM patch output was empty.')
        if 'Binary files' in patch_text or 'GIT binary patch' in patch_text:
            raise LoopException('Binary patch detected, refusing to apply.')
        touched: List[str] = []
        lines = patch_text.splitlines()
        line_count = 0
        for raw in lines:
            if raw.startswith('+++ ') or raw.startswith('--- '):
                label = raw.split(' ', 1)[1] if ' ' in raw else raw
                file_path = self._normalize_path(label)
                if file_path and file_path not in touched:
                    touched.append(file_path)
                continue
            if raw.startswith('+') and not raw.startswith('+++'):
                line_count += 1
            elif raw.startswith('-') and not raw.startswith('---'):
                line_count += 1
        if not touched:
            raise LoopException('Patch did not touch any repository files.')
        return PatchOutcome(text=patch_text, metadata=PatchMetadata(touched_files=touched, line_count=line_count))

    def _normalize_path(self, token: str) -> str | None:
        if token in ('/dev/null', '\\dev\\null'):
            return None
        cleaned = token
        if token.startswith('a/') or token.startswith('b/'):
            cleaned = token[2:]
        candidate = (self.repo_root / cleaned).resolve()
        repo_text = str(self.repo_root)
        candidate_text = str(candidate)
        if not candidate_text.startswith(repo_text):
            raise LoopException(f'Patch touches file outside repo: {cleaned}')
        name = Path(cleaned).name
        if name == '.env':
            raise LoopException('Modifying .env is forbidden.')
        if '..' in Path(cleaned).parts:
            raise LoopException('Path traversal detected in patch.')
        return cleaned
