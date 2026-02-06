from app.tools.web import WebSearchAndSummarize, WebSource
from pathlib import Path


def test_extract_text():
    tool = WebSearchAndSummarize([WebSource(name="x", url="https://example.com")], cache_dir=Path("./.cache"))
    html = "<html><body><h1>Hello</h1><p>Problem in workflow.</p></body></html>"
    text = tool.extract_text(html)
    assert "Hello" in text
    assert "Problem" in text


def test_extract_published_at_from_relative_time():
    tool = WebSearchAndSummarize([WebSource(name="x", url="https://example.com")], cache_dir=Path("./.cache"))
    html = "<html><body><relative-time datetime='2026-02-01T10:00:00Z'></relative-time></body></html>"
    published_at = tool.extract_published_at(html)
    assert published_at is not None
    assert published_at.startswith("2026-02-01T10:00:00")
