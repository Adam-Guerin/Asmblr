import json
from pathlib import Path
from app.core.llm import LLMClient
from app.langchain_tools import build_toolbox


def test_langchain_tools_run_smoke(tmp_path: Path, monkeypatch):
    llm = LLMClient("http://localhost:11434", "llama3.1:8b")
    monkeypatch.setattr(llm, "available", lambda: False)

    class DummySettings:
        knowledge_dir = Path(__file__).resolve().parents[1] / "knowledge"
        data_dir = tmp_path
        max_sources = 3
        request_timeout = 5
        rate_limit_per_domain = 1

    tools = build_toolbox(DummySettings(), llm, judge_prompt="")

    def fake_run(self, max_sources=8):
        return [{"name": "source", "url": "https://example.com", "text": "Problem: teams struggle."}]

    monkeypatch.setattr("app.tools.web.WebSearchAndSummarize.run", fake_run)

    sources = [{"name": "Example", "url": "https://example.com"}]
    web_json = tools["web"].run(
        {
            "sources": sources,
            "max_sources": 1,
            "cache_dir": str(tmp_path),
            "timeout": 5,
            "rate_limit_per_domain": 1,
        }
    )
    pages = json.loads(web_json)
    assert pages

    score_json = tools["scoring"].run(
        {
            "pain_statements": ["Teams struggle"],
            "ideas": [{"name": "Idea 1"}],
            "use_llm_judge": False,
        }
    )
    scores = json.loads(score_json)
    assert scores[0]["score"] >= 0
