from pathlib import Path

import pytest

from app.tools.langchain_web import WebSearchArgs, is_valid_url


def test_is_valid_url_accepts_http_https() -> None:
    assert is_valid_url("https://example.com")
    assert is_valid_url("http://example.com/path")


def test_is_valid_url_rejects_invalid() -> None:
    assert not is_valid_url("")
    assert not is_valid_url("ftp://example.com")
    assert not is_valid_url("example.com")


def test_web_search_args_validation() -> None:
    args = WebSearchArgs(
        sources=[{"name": "Example", "url": "https://example.com"}],
        cache_dir=str(Path("data/cache")),
    )
    assert args.max_sources == 8


def test_web_search_args_invalid_sources() -> None:
    with pytest.raises(ValueError):
        WebSearchArgs(sources=[], cache_dir="data/cache")
