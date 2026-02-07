import json
from pathlib import Path

from app.core.config import Settings
from app.core.pipeline import VenturePipeline


def _settings(tmp_path: Path) -> Settings:
    settings = Settings()
    settings.runs_dir = tmp_path / "runs"
    settings.data_dir = tmp_path / "data"
    settings.config_dir = Path(__file__).resolve().parents[1] / "configs"
    settings.knowledge_dir = Path(__file__).resolve().parents[1] / "knowledge"
    return settings


def test_resolve_execution_profile_defaults(tmp_path: Path) -> None:
    pipeline = VenturePipeline(_settings(tmp_path))
    standard = pipeline._resolve_execution_profile(None, fast_mode=False)
    quick = pipeline._resolve_execution_profile(None, fast_mode=True)
    deep = pipeline._resolve_execution_profile("deep", fast_mode=False)

    assert standard["name"] == "standard"
    assert quick["name"] == "quick"
    assert deep["name"] == "deep"
    assert deep["token_budget_est"] > standard["token_budget_est"] > quick["token_budget_est"]


def test_run_writes_budget_file_for_profile(tmp_path: Path) -> None:
    pipeline = VenturePipeline(_settings(tmp_path))
    result = pipeline.run("x", n_ideas=20, execution_profile="deep")
    run_dir = pipeline.settings.runs_dir / result.run_id
    budget = json.loads((run_dir / "run_budget.json").read_text(encoding="utf-8"))

    assert budget["profile"] == "deep"
    assert budget["budget"]["time_budget_min"] == 75
    assert budget["budget"]["token_budget_est"] == 140000
    assert budget["applied_overrides"]["max_n_ideas"] == 20
