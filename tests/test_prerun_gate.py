from pathlib import Path
from app.core.config import Settings
from app.core.pipeline import VenturePipeline


def test_prerun_gate_blocks_on_insufficient_data(tmp_path: Path, monkeypatch):
    settings = Settings()
    settings.runs_dir = tmp_path / "runs"
    settings.data_dir = tmp_path / "data"
    settings.config_dir = Path(__file__).resolve().parents[1] / "configs"
    settings.knowledge_dir = Path(__file__).resolve().parents[1] / "knowledge"

    pipeline = VenturePipeline(settings)

    def fake_check(*args, **kwargs):
        return None

    def fake_web_run(self, *args, **kwargs):
        return "[]"

    def fake_crewai(*args, **kwargs):
        return {
            "research": {"pain_statements": [], "pages": []},
            "analysis": {"ideas": [], "scores": [], "top_idea": {"name": "unknown", "score": 0}, "competitors": []},
            "product": {},
            "tech": {},
            "growth": {},
        }

    monkeypatch.setattr("app.core.pipeline.check_ollama", fake_check)
    monkeypatch.setattr("app.langchain_tools.WebSearchAndSummarizeTool._run", fake_web_run)
    monkeypatch.setattr("app.agents.crew.run_crewai_pipeline", fake_crewai)

    result = pipeline.run("test", n_ideas=3, fast_mode=True)
    run_dir = settings.runs_dir / result.run_id
    assert (run_dir / "abort_reason.md").exists()
    assert not (run_dir / "prd.md").exists()
    assert not (run_dir / "tech_spec.md").exists()
    assert not (run_dir / "landing_page" / "index.html").exists()
    assert not (run_dir / "content_pack" / "posts.md").exists()
