from dataclasses import dataclass, field
from typing import Any


@dataclass
class Idea:
    name: str
    one_liner: str
    target_user: str
    problem: str
    solution: str
    key_features: list[str] = field(default_factory=list)
    source_cluster: int | None = None
    pain_ids: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    hypotheses: list[str] = field(default_factory=list)


@dataclass
class IdeaScore:
    name: str
    score: int
    rationale: str
    risks: list[str]
    signals: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunResult:
    run_id: str
    ideas: list[Idea]
    scores: list[IdeaScore]
    top_idea: IdeaScore
    artifacts: dict[str, str]


@dataclass
class SeedInputs:
    icp: str | None = None
    pains: list[str] = field(default_factory=list)
    competitors: list[str] = field(default_factory=list)
    context: str | None = None
    theme: str | None = None

    def has_any(self) -> bool:
        return bool(self.icp or self.context or self.theme or self.pains or self.competitors)
