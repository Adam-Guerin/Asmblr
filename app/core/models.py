from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class Idea:
    name: str
    one_liner: str
    target_user: str
    problem: str
    solution: str
    key_features: List[str] = field(default_factory=list)
    source_cluster: int | None = None
    pain_ids: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    hypotheses: List[str] = field(default_factory=list)


@dataclass
class IdeaScore:
    name: str
    score: int
    rationale: str
    risks: List[str]
    signals: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RunResult:
    run_id: str
    ideas: List[Idea]
    scores: List[IdeaScore]
    top_idea: IdeaScore
    artifacts: Dict[str, str]


@dataclass
class SeedInputs:
    icp: str | None = None
    pains: List[str] = field(default_factory=list)
    competitors: List[str] = field(default_factory=list)
    context: str | None = None
    theme: str | None = None

    def has_any(self) -> bool:
        return bool(self.icp or self.context or self.theme or self.pains or self.competitors)
