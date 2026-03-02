import asyncio
import json
from pathlib import Path

from app.bench_edi import (
    PHASE1_OPTIMIZED_ARCHITECTURES,
    PHASE1_TOKEN_PROFILES,
    ArchitectureRunner,
    phase1_average_token_reduction_ratio,
)


def _count_packages(path: Path) -> int:
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        count += 1
    return count


def test_phase1_architecture_set_is_a7_to_a11():
    assert PHASE1_OPTIMIZED_ARCHITECTURES == [
        "a7_optimized",
        "a8_optimized",
        "a9_optimized",
        "a10_optimized",
        "a11_optimized",
    ]


def test_phase1_token_reduction_target_is_at_least_40_percent():
    assert phase1_average_token_reduction_ratio() >= 0.40


def test_phase1_dependency_cleanup_is_at_least_30_percent():
    full_count = _count_packages(Path("requirements.txt"))
    phase1_count = _count_packages(Path("requirements-phase1.txt"))
    reduction = 1.0 - (phase1_count / full_count)
    assert reduction >= 0.30


def test_a11_profile_run_respects_token_budget(tmp_path: Path):
    contexts_dir = tmp_path / "contexts"
    contexts_dir.mkdir(parents=True, exist_ok=True)
    context_payload = {
        "id": "ctx-1",
        "raw_text": "SaaS onboarding friction and poor handoffs across teams.",
        "timestamp": "2026-03-02T00:00:00",
        "source_url": "https://example.com",
        "industry_tag": "SaaS",
        "extracted_pains": ["onboarding friction", "handoff delays"],
        "extracted_competitors": ["CompA", "CompB"],
        "estimated_stage": "MVP",
        "geographic_cluster": "EU",
        "metadata": {"platform": "test"},
    }
    (contexts_dir / "context_0001.json").write_text(json.dumps(context_payload), encoding="utf-8")

    runner = ArchitectureRunner(str(contexts_dir), str(tmp_path / "runs"))
    result = asyncio.run(runner.run_architecture("a11_optimized", runner.contexts[0], 42))

    profile = PHASE1_TOKEN_PROFILES["a11_optimized"]
    assert result["architecture"] == "a11_optimized"
    assert profile["token_min"] <= result["tokens_used"] <= profile["token_max"]
