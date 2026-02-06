from pathlib import Path
from app.core.config import Settings
from app.core.pipeline import VenturePipeline
from app.tools.generator import default_content_pack, default_landing_payload


def test_pipeline_fast_mode(tmp_path: Path, monkeypatch):
    settings = Settings()
    settings.runs_dir = tmp_path / "runs"
    settings.data_dir = tmp_path / "data"
    settings.config_dir = Path(__file__).resolve().parents[1] / "configs"
    settings.knowledge_dir = Path(__file__).resolve().parents[1] / "knowledge"

    pipeline = VenturePipeline(settings)

    def fake_check(*args, **kwargs):
        return None

    monkeypatch.setattr("app.core.pipeline.check_ollama", fake_check)

    def fake_web_run(self, *args, **kwargs):
        return "[]"

    monkeypatch.setattr("app.langchain_tools.WebSearchAndSummarizeTool._run", fake_web_run)

    def fake_crewai(topic, settings, llm, run_id, n_ideas, fast_mode, **kwargs):
        return {
            "research": {"pain_statements": ["Problem: teams struggle."], "pages": [{"url": "https://example.com"}]},
            "analysis": {
                "ideas": [
                    {
                        "name": "Idea 1",
                        "one_liner": "Test",
                        "target_user": "Teams",
                        "problem": "Slow prioritization",
                        "solution": "Score ideas",
                        "key_features": ["scoring"],
                    }
                ],
                "scores": [{"name": "Idea 1", "score": 70, "rationale": "ok", "risks": []}],
                "top_idea": {"name": "Idea 1", "score": 70, "rationale": "ok"},
                "competitors": [],
            },
            "product": {"prd_markdown": "# PRD"},
            "tech": {"tech_spec_markdown": "# Tech Spec", "repo_dir": str(settings.runs_dir / run_id / "repo_skeleton")},
            "growth": {
                "landing_payload": default_landing_payload("Idea 1", fast_mode=True),
                "content_pack": default_content_pack("Idea 1", fast_mode=True),
                "landing_dir": str(settings.runs_dir / run_id / "landing_page"),
                "content_dir": str(settings.runs_dir / run_id / "content_pack"),
            },
        }

    monkeypatch.setattr("app.agents.crew.run_crewai_pipeline", fake_crewai)
    result = pipeline.run("test", n_ideas=10, fast_mode=True)
    assert result.run_id
    assert (settings.runs_dir / result.run_id / "opportunities.json").exists()
