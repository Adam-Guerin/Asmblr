"""LangChain scoring tool for idea evaluation."""
from __future__ import annotations

import json
from typing import Any

from langchain.tools import BaseTool
from pydantic import BaseModel

from app.core.llm import LLMClient
from app.core.scoring import derive_signals, heuristic_score


class ScoringArgs(BaseModel):
    """Arguments for scoring_engine tool."""

    pain_statements: list[str]
    ideas: list[dict[str, Any]]
    use_llm_judge: bool = True
    topic: str = ""
    market_profile: str | None = None
    use_calibration: bool = True


class ScoringEngineTool(BaseTool):
    """Score ideas (0-100) using heuristics and optional LLM judge."""

    name: str = "scoring_engine"
    description: str = "Score ideas (0-100) using heuristics and optional LLM judge. Returns JSON list of scores."
    args_schema: type[BaseModel] = ScoringArgs

    def __init__(
        self,
        llm: LLMClient,
        judge_prompt: str,
        *,
        primary_icp: str = "",
        primary_icp_keywords: str = "",
        icp_alignment_bonus_max: int = 0,
    ) -> None:
        super().__init__()
        self._llm = llm
        self._judge_prompt = judge_prompt
        self._primary_icp = primary_icp
        self._primary_icp_keywords = primary_icp_keywords
        self._icp_alignment_bonus_max = max(0, int(icp_alignment_bonus_max))

    def _run(
        self,
        pain_statements: list[str],
        ideas: list[dict[str, Any]],
        use_llm_judge: bool = True,
        topic: str = "",
        market_profile: str | None = None,
        use_calibration: bool = True,
    ) -> str:
        """Execute scoring and return JSON payload."""
        scores: list[dict[str, Any]] = []
        for idea in ideas:
            signals = derive_signals(pain_statements)
            heuristic = heuristic_score(
                signals,
                topic=topic,
                pain_statements=pain_statements,
                idea=idea,
                market_profile=market_profile,
                use_calibration=use_calibration,
                icp_focus=self._primary_icp,
                icp_keywords=self._primary_icp_keywords,
                icp_alignment_bonus_max=self._icp_alignment_bonus_max,
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
                        "icp_alignment": meta.get("icp_alignment"),
                    },
                }
            )
        return json.dumps(scores, indent=2)
