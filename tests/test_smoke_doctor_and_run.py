from pathlib import Path
import json
from app.core.config import Settings
from app.core.pipeline import VenturePipeline


def test_smoke_doctor_and_run(tmp_path: Path, monkeypatch):
    settings = Settings()
    settings.runs_dir = tmp_path / "runs"
    settings.data_dir = tmp_path / "data"
    settings.config_dir = Path(__file__).resolve().parents[1] / "configs"
    settings.knowledge_dir = Path(__file__).resolve().parents[1] / "knowledge"

    pipeline = VenturePipeline(settings)

    monkeypatch.setattr("app.core.pipeline.check_ollama", lambda *a, **k: None)

    monkeypatch.setattr(pipeline.general_llm, "generate", lambda prompt: "ok")
    monkeypatch.setattr(pipeline.general_llm, "generate_json", lambda prompt: {"ok": True})

    def fake_web_run(self, *args, **kwargs):
        pages = [
            {
                "name": "source",
                "url": "https://example.com/a",
                "summary": "",
                "text": ("Problem: teams struggle with handoffs. " * 20),
            },
            {
                "name": "source",
                "url": "https://example.org/b",
                "summary": "",
                "text": ("Problem: onboarding is hard when tools are scattered. " * 20),
            },
            {
                "name": "source",
                "url": "https://example.net/c",
                "summary": "",
                "text": ("Need: clear MVP scope for internal tooling decisions. " * 20),
            },
        ]
        return json.dumps(pages)

    monkeypatch.setattr("app.langchain_tools.WebSearchAndSummarizeTool._run", fake_web_run)

    def fake_comp(self, *args, **kwargs):
        return json.dumps([{"product_name": "CompA", "pricing": "unknown"}])

    monkeypatch.setattr("app.langchain_tools.CompetitorExtractorTool._run", fake_comp)

    def fake_crewai(*args, **kwargs):
        return {
            "research": {
                "pain_statements": [
                    "Teams struggle with handoffs across tools.",
                    "Onboarding breaks when workflows are unclear.",
                    "MVP scope decisions are delayed by missing evidence.",
                ],
                "pages": [],
            },
            "analysis": {
                "ideas": [{"name": "Idea 1", "target_user": "Ops teams"}],
                "scores": [{"name": "Idea 1", "score": 80, "rationale": "ok", "risks": []}],
                "top_idea": {"name": "Idea 1", "score": 80, "rationale": "ok"},
                "competitors": [{"product_name": "CompA", "pricing": "unknown"}],
            },
            "product": {"prd_markdown": "# PRD\n\nICP: Ops teams"},
            "tech": {"tech_spec_markdown": "# Tech Spec\n\nStack: FastAPI"},
            "growth": {"landing_payload": {}, "content_pack": {}},
        }

    monkeypatch.setattr("app.core.pipeline.run_crewai_pipeline", fake_crewai)

    result = pipeline.run("test", n_ideas=3, fast_mode=True)
    run_dir = settings.runs_dir / result.run_id

    data_source = json.loads((run_dir / "data_source.json").read_text(encoding="utf-8"))
    assert data_source["decision"] == "real"
    assert (run_dir / "prd.md").exists()
    assert (run_dir / "tech_spec.md").exists()
    assert (run_dir / "market_report.md").exists()
    assert (run_dir / "repo_skeleton").exists()
    assert (run_dir / "landing_page").exists()
    assert (run_dir / "content_pack").exists()


def test_doctor_ok(monkeypatch):
    from app.core.doctor import run_doctor
    settings = Settings()
    settings.prod_mode = False
    settings.require_prod_checklist = False

    def fake_get(url, timeout=5):
        class Resp:
            def raise_for_status(self):
                return None
            def json(self):
                return {"models": [{"name": settings.general_model}, {"name": settings.code_model}]}
        return Resp()

    monkeypatch.setattr("httpx.get", fake_get)
    monkeypatch.setattr("app.core.llm.LLMClient.generate", lambda self, prompt: "ok")
    monkeypatch.setattr("app.core.llm.LLMClient.generate_json", lambda self, prompt: {"ok": True})
    monkeypatch.setattr("app.core.llm.LLMClient.available", lambda self: True)
    result = run_doctor(settings)
    assert result.ok is True


def test_doctor_prod_checklist_fails_when_dry_run_enabled(monkeypatch):
    from app.core.doctor import run_doctor

    def fake_get(url, timeout=5):
        class Resp:
            def raise_for_status(self):
                return None

            def json(self):
                return {"models": [{"name": "llama3.1:8b"}, {"name": "qwen2.5-coder:7b"}]}

        return Resp()

    monkeypatch.setattr("httpx.get", fake_get)
    monkeypatch.setattr("app.core.llm.LLMClient.generate", lambda self, prompt: "ok")
    monkeypatch.setattr("app.core.llm.LLMClient.generate_json", lambda self, prompt: {"ok": True})
    monkeypatch.setattr("app.core.llm.LLMClient.available", lambda self: True)

    settings = Settings()
    settings.prod_mode = True
    settings.require_prod_checklist = True
    settings.api_key = "prod_key_123"
    settings.ui_password = "prod_pwd_123"
    settings.enable_publishing = True
    settings.publish_dry_run = True

    result = run_doctor(settings)
    assert result.ok is False
    assert "publish_dry_run_disabled" in result.report
