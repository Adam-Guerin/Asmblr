from pathlib import Path
import json
import httpx
from app.tools.web import WebSearchAndSummarize, WebSource


def test_fetch_url_retries(monkeypatch, tmp_path: Path):
    calls = {"count": 0}

    class DummyResponse:
        def __init__(self, status_code=200):
            self.status_code = status_code
            self.text = "ok"
            self.request = httpx.Request("GET", "https://example.com")

    class DummyClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url):
            calls["count"] += 1
            if calls["count"] < 2:
                raise httpx.ReadTimeout("timeout")
            return DummyResponse(200)

    monkeypatch.setattr(httpx, "Client", DummyClient)

    tool = WebSearchAndSummarize(
        sources=[WebSource(name="x", url="https://example.com")],
        cache_dir=tmp_path,
        retry_max_attempts=3,
    )
    text = tool.fetch_url("https://example.com")
    assert text == "ok"
    assert calls["count"] >= 2


def test_competitor_tool_accepts_urls(monkeypatch, tmp_path: Path):
    from app.langchain_tools import CompetitorExtractorTool

    def fake_fetch(self, url, headers=None):
        return "<html><head><title>CompA</title></head><body>Pricing</body></html>"

    monkeypatch.setattr("app.tools.web.WebSearchAndSummarize.fetch_url", fake_fetch)

    tool = CompetitorExtractorTool()
    payload = tool.run(
        {
            "urls": ["https://example.com"],
            "cache_dir": str(tmp_path),
            "timeout": 5,
            "rate_limit_per_domain": 1,
        }
    )
    data = json.loads(payload)
    assert data
    assert data[0]["product_name"]
