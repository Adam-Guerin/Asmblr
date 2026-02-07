import json
from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.critique import run_devils_advocate
from app.core.run_manager import RunManager


class StubLLM:
    def __init__(self, *args, **kwargs):
        pass

    def available(self):
        return True

    def generate(self, prompt: str) -> str:
        payload = {
            "verdict": "KILL",
            "top_risks": [
                {
                    "type": "data",
                    "severity": "high",
                    "evidence": "market_report.md",
                    "how_to_test_fast": "Validate pain statements via interviews",
                }
            ],
            "contradictions": ["market_report.md contradicts prd.md"],
            "missing_data": [],
            "one killer experiment": {
                "hypothesis": "Improving onboarding clarity will reduce churn",
                "method": "AB test new flow",
                "success_metric": "activation+10%",
                "stop_metric": "activation-5%",
            },
        }
        markdown = "## Markdown summary\n- Evidence: market_report.md\n"
        return f"JSON:{json.dumps(payload)}\n---\n{markdown}"


def _write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _prepare_run(tmp_path: Path, settings: Settings, status: str, confidence_score: int = 100) -> str:
    run_manager = RunManager(settings.runs_dir, settings.data_dir)
    run_id = run_manager.create_run("critique-test")
    run_manager.update_status(run_id, status)
    run_dir = settings.runs_dir / run_id
    _write_text(run_dir / "market_report.md", "# Market Report\n\nSignals.")
    _write_text(run_dir / "prd.md", "# PRD\n\nVision.")
    _write_text(run_dir / "tech_spec.md", "# Tech Spec\n\nArchitecture.")
    _write_text(run_dir / "decision.md", "# Decision\n\n- Status: PASS\n- Reason: test")
    _write_text(
        run_dir / "competitor_analysis.json",
        json.dumps({"competitors": [{"product_name": "Example", "pricing": "$0"}]}),
    )
    _write_text(
        run_dir / "confidence.json",
        json.dumps({"score": confidence_score, "breakdown": {}, "reasons": [], "caps": []}),
    )
    return run_id


def test_critique_requires_ollama(tmp_path: Path, monkeypatch):
    settings = Settings()
    settings.runs_dir = tmp_path / "runs"
    settings.data_dir = tmp_path / "data"
    run_id = _prepare_run(tmp_path, settings, status="completed")
    monkeypatch.setattr("app.core.critique.check_ollama", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("Ollama missing")))
    with pytest.raises(RuntimeError):
        run_devils_advocate(settings, run_id)


def test_critique_outputs_files(tmp_path: Path, monkeypatch):
    settings = Settings()
    settings.runs_dir = tmp_path / "runs"
    settings.data_dir = tmp_path / "data"
    run_id = _prepare_run(tmp_path, settings, status="completed")
    monkeypatch.setattr("app.core.critique.check_ollama", lambda *args, **kwargs: {})
    monkeypatch.setattr("app.core.critique.LLMClient", StubLLM)
    result = run_devils_advocate(settings, run_id, mode="standard")
    assert result.json_path.exists()
    assert result.markdown_path.exists()
    assert result.verdict == "KILL"
    assert "market_report.md" in result.summary


def test_critique_forces_non_go_when_low_confidence(tmp_path: Path, monkeypatch):
    settings = Settings()
    settings.runs_dir = tmp_path / "runs"
    settings.data_dir = tmp_path / "data"
    run_id = _prepare_run(tmp_path, settings, status="completed", confidence_score=30)
    class GoLLM(StubLLM):
        def generate(self, prompt: str) -> str:
            payload = {
                "verdict": "GO",
                "top_risks": [],
                "contradictions": [],
                "missing_data": [],
                "one killer experiment": {
                    "hypothesis": "Test clarity",
                    "method": "Prototype",
                    "success_metric": "positive feedback",
                    "stop_metric": "negative feedback",
                },
            }
            return f"JSON:{json.dumps(payload)}\n---\n## Markdown"
    monkeypatch.setattr("app.core.critique.check_ollama", lambda *args, **kwargs: {})
    monkeypatch.setattr("app.core.critique.LLMClient", GoLLM)
    result = run_devils_advocate(settings, run_id, mode="strict")
    assert result.payload["payload"]["verdict"] != "GO"
