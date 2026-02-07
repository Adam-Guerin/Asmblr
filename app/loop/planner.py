from __future__ import annotations

from typing import Any

from loguru import logger

from app.core.llm import LLMClient
from app.loop.errors import LoopException
from app.loop.schemas import LoopPlan

PLAN_PROMPT = '''You are a cautious engineer inside the Asmblr loop.
Goal: {goal}
Iteration: {iteration}
Provide JSON with:
- steps: 1-{max_steps} focused actions.
- rationale: why you picked them.
- files_hint: optional files touched.
Return ONLY valid JSON, no markdown or commentary.'''


class LoopPlanner:
    def __init__(self, llm: LLMClient, max_steps: int = 5, prompt_template: str = PLAN_PROMPT) -> None:
        self.llm = llm
        self.max_steps = max_steps
        self.prompt_template = prompt_template

    def plan(self, goal: str, iteration: int) -> LoopPlan:
        prompt = self.prompt_template.format(goal=goal, iteration=iteration, max_steps=self.max_steps)
        response = self._generate(prompt)
        steps = response.get("steps")
        if not isinstance(steps, list) or not steps or len(steps) > self.max_steps:
            raise LoopException(f"Plan must contain 1-{self.max_steps} steps.")
        files_hint = response.get("files_hint")
        if files_hint is None or not isinstance(files_hint, list):
            files_hint = []
        rationale = response.get("rationale", "")
        return LoopPlan(
            steps=[str(step) for step in steps],
            rationale=str(rationale),
            files_hint=[str(f) for f in files_hint],
        )

    def _generate(self, prompt: str) -> dict[str, Any]:
        for attempt in range(2):
            candidate = self.llm.generate_json(prompt)
            if self._valid(candidate):
                return candidate
            logger.warning("Plan JSON invalid on attempt %d.", attempt + 1)
        raise LoopException("Unable to parse loop plan JSON after retries.")

    def _valid(self, payload: Any) -> bool:
        return isinstance(payload, dict) and isinstance(payload.get("steps"), list)
