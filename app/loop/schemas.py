from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class LoopConfig:
    goal: str
    max_iter: int = 3
    time_minutes: float | None = None
    tests_command: str = "pytest -q"
    dry_run: bool = False
    approve_mode: str = "auto"
    max_total_diff_lines: int = 500
    max_patch_lines: int = 200


@dataclass
class LoopPlan:
    steps: List[str]
    rationale: str
    files_hint: List[str]


@dataclass
class PatchMetadata:
    touched_files: List[str]
    line_count: int


@dataclass
class PatchOutcome:
    text: str
    metadata: PatchMetadata


@dataclass
class IterationVerdict:
    status: str
    reasons: List[str]
    metrics: Dict[str, Any]
