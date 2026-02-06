import json
from pathlib import Path

from app.core.config import Settings
from app.core.pipeline import VenturePipeline


def _prepare_settings(tmp_path: Path) -> Settings:
    settings = Settings()
    settings.runs_dir = tmp_path / "runs"
    settings.data_dir = tmp_path / "data"
    settings.config_dir = Path(__file__).resolve().parents[1] / "configs"
    settings.knowledge_dir = Path(__file__).resolve().parents[1] / "knowledge"
    settings.enable_self_healing = True
    settings.stage_retry_attempts = 2
    settings.stage_retry_backoff_sec = 0.0
    return settings


def test_stage_retries_and_records_failure(tmp_path: Path) -> None:
    settings = _prepare_settings(tmp_path)
    pipeline = VenturePipeline(settings)
    run_id = pipeline.manager.create_run("retry run")
    calls = {"count": 0}

    def action():
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("temporary stage error")
        return {"ok": True}

    payload = pipeline._run_stage_with_retries(run_id, "unit_stage", action)
    assert payload == {"ok": True}
    assert calls["count"] == 2
    report_path = settings.runs_dir / run_id / "failure_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["stage_failures"]
    assert report["stage_failures"][-1]["stage"] == "unit_stage"


def test_llm_fallback_model_selection(tmp_path: Path, monkeypatch) -> None:
    settings = _prepare_settings(tmp_path)
    settings.general_model = "primary-general"
    settings.code_model = "primary-code"
    settings.general_model_fallbacks = "fallback-general"
    settings.code_model_fallbacks = "fallback-code"

    pipeline = VenturePipeline(settings)
    run_id = pipeline.manager.create_run("fallback run")

    def fake_check(base_url, models):
        if models == ["fallback-general", "fallback-code"]:
            return {"models": [{"name": "fallback-general"}, {"name": "fallback-code"}]}
        raise RuntimeError("model pair unavailable")

    monkeypatch.setattr("app.core.pipeline.check_ollama", fake_check)
    pipeline._ensure_llm_ready(run_id)

    assert pipeline.active_general_model == "fallback-general"
    assert pipeline.active_code_model == "fallback-code"
    selection = json.loads((settings.runs_dir / run_id / "llm_model_selection.json").read_text(encoding="utf-8"))
    assert selection["fallback_used"] is True
