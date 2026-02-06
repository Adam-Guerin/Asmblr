"""LangChain scoring tool for idea evaluation."""
from __future__ import annotations

import json
from typing import Any, Dict, List

from langchain.tools import BaseTool
from pydantic import BaseModel

from app.core.llm import LLMClient
from app.core.scoring import derive_signals, heuristic_score


class ScoringArgs(BaseModel):
    """Arguments for scoring_engine tool."""

    pain_statements: List[str]
    ideas: List[Dict[str, Any]]
    use_llm_judge: bool = True
    topic: str = ""
    market_profile: str | None = None
    use_calibration: bool = True


class ScoringEngineTool(BaseTool):
    """Score ideas (0-100) using heuristics and optional LLM judge."""

    name: str = "scoring_engine"
    description: str = "Score ideas (0-100) using heuristics and optional LLM judge. Returns JSON list of scores."
    args_schema: type[BaseModel] = ScoringArgs

    def __init__(self, llm: LLMClient, judge_prompt: str) -> None:
        super().__init__()
        self._llm = llm
        self._judge_prompt = judge_prompt

    def _run(
        self,
        pain_statements: List[str],
        ideas: List[Dict[str, Any]],
        use_llm_judge: bool = True,
        topic: str = "",
        market_profile: str | None = None,
        use_calibration: bool = True,
    ) -> str:
        """Execute scoring and return JSON payload."""
        scores: List[Dict[str, Any]] = []
        for idea in ideas:
            signals = derive_signals(pain_statements)
            heuristic = heuristic_score(
                signals,
                topic=topic,
                pain_statements=pain_statements,
                idea=idea,
                market_profile=market_profile,
                use_calibration=use_calibration,
                return_meta=True,
            )
            score, meta = heuristic if isinstance(heuristic, tuple) else (int(heuristic), {})
            rationale = "Adaptive heuristic score based on market profile, signal intensity, and buildability."
            risks = ["Market sizing is approximate", "Competition data limited"]
            if use_llm_judge and self._llm.available():
                prompt = self._judge_prompt + "\n\n" + json.dumps({"idea": idea, "signals": signals}, indent=2)
                judge = self._llm.generate_json(prompt)
                if isinstance(judge, dict) and judge.get("score") is not None:
                    score = int(judge.get("score", score))
                    rationale = judge.get("rationale", rationale)
                    risks = judge.get("risks", risks)
            scores.append(
                {
                    "name": idea.get("name", "unknown"),
                    "score": score,
                    "rationale": rationale,
                    "risks": risks,
                    "signals": {
                        **signals,
                        "market_profile": meta.get("market_profile"),
                        "adaptive_weights": meta.get("weights"),
                        "calibration": meta.get("calibration"),
                    },
                }
            )
        return json.dumps(scores, indent=2)
