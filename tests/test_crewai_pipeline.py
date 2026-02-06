import json
from pathlib import Path
from app.core.config import Settings
from app.core.llm import LLMClient
from app.agents.crew import run_crewai_pipeline


def test_crewai_pipeline_smoke(tmp_path: Path, monkeypatch):
    settings = Settings()
    settings.runs_dir = tmp_path / "runs"
    settings.data_dir = tmp_path / "data"
    settings.config_dir = Path(__file__).resolve().parents[1] / "configs"
    settings.knowledge_dir = Path(__file__).resolve().parents[1] / "knowledge"

    llm = LLMClient("http://localhost:11434", "llama3.1:8b")
    monkeypatch.setattr(llm, "available", lambda: False)

    def fake_kickoff(self):
        for task in self.tasks:
            role = task.agent.role
            if role == "Researcher":
                task.output = json.dumps({
                    "pain_statements": ["Teams struggle"],
                    "clusters": {"0": ["Teams struggle"]},
                    "ideas": [{"name": "Idea 1", "one_liner": "Test", "target_user": "Teams", "problem": "Slow", "solution": "Score", "key_features": ["scoring"]}],
                    "sources": [],
                    "pages": [],
                })
            elif role == "Analyst":
                task.output = json.dumps({
                    "ideas": [{"name": "Idea 1"}],
                    "scores": [{"name": "Idea 1", "score": 70, "rationale": "ok", "risks": []}],
                    "top_idea": {"name": "Idea 1", "score": 70, "rationale": "ok"},
                    "competitors": [],
                })
            elif role == "Product":
                task.output = json.dumps({"prd_markdown": "# PRD"})
            elif role == "Tech Lead":
                task.output = json.dumps({"tech_spec_markdown": "# Tech Spec"})
            elif role == "Growth":
                task.output = json.dumps({"landing_dir": "", "content_dir": ""})
        return "ok"

    monkeypatch.setattr("crewai.Crew.kickoff", fake_kickoff)

    run_id = "test_run"
    outputs = run_crewai_pipeline("test", settings, llm, run_id, n_ideas=3, fast_mode=True)
    assert outputs.get("research")
    assert (settings.runs_dir / run_id / "repo_skeleton" / "app" / "main.py").exists()
    assert (settings.runs_dir / run_id / "landing_page" / "index.html").exists()
    assert (settings.runs_dir / run_id / "content_pack" / "posts.md").exists()


def test_crewai_pipeline_real_kickoff_with_mock_llm_and_tools(tmp_path: Path, monkeypatch):
    settings = Settings()
    settings.runs_dir = tmp_path / "runs"
    settings.data_dir = tmp_path / "data"
    settings.config_dir = Path(__file__).resolve().parents[1] / "configs"
    settings.knowledge_dir = Path(__file__).resolve().parents[1] / "knowledge"

    llm = LLMClient("http://localhost:11434", "llama3.1:8b")
    monkeypatch.setattr(llm, "available", lambda: False)

    calls = {"web": 0, "competitor": 0}

    def fake_web_run(self, *args, **kwargs):
        calls["web"] += 1
        return "[{\"name\":\"x\",\"url\":\"https://example.com\",\"text\":\"Problem\",\"summary\":\"Problem\"}]"

    def fake_comp_run(self, *args, **kwargs):
        calls["competitor"] += 1
        return "[{\"product_name\":\"Comp\",\"pricing\":\"unknown\"}]"

    monkeypatch.setattr("app.langchain_tools.WebSearchAndSummarizeTool._run", fake_web_run)
    monkeypatch.setattr("app.langchain_tools.CompetitorExtractorTool._run", fake_comp_run)

    outputs = run_crewai_pipeline("test", settings, llm, "run1", n_ideas=3, fast_mode=True)
    assert calls["web"] >= 1
    assert calls["competitor"] >= 1
    assert (settings.runs_dir / "run1" / "repo_skeleton" / "app" / "main.py").exists()
    assert (settings.runs_dir / "run1" / "landing_page" / "index.html").exists()
    assert (settings.runs_dir / "run1" / "content_pack" / "posts.md").exists()
