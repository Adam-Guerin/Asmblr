from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.core import llm as llm_module
from app.core.llm import LLMClient, check_ollama


class _FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeChatClient:
    def __init__(self, *args, **kwargs) -> None:
        self.calls = 0
        self.last_prompt = ""
        self.response = "ok"

    def __call__(self, messages):
        self.calls += 1
        self.last_prompt = messages[0].content
        return SimpleNamespace(content=self.response)


@pytest.fixture(autouse=True)
def _patch_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm_module, "get_settings", lambda: SimpleNamespace(enable_cache=False))


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> LLMClient:
    monkeypatch.setattr(llm_module, "HumanMessage", _FakeMessage)
    fake_factory = _FakeChatClient
    monkeypatch.setattr(llm_module, "ChatOllama", fake_factory)
    return LLMClient("http://localhost:11434", "llama3.1:8b")


def test_available_false_when_client_missing() -> None:
    c = LLMClient("http://localhost:11434", "llama3.1:8b")
    c._client = None
    assert c.available() is False


def test_generate_raises_when_unavailable() -> None:
    c = LLMClient("http://localhost:11434", "llama3.1:8b")
    c._client = None
    with pytest.raises(RuntimeError, match="LLM not available"):
        c.generate("hello")


def test_generate_uses_client_and_updates_usage(client: LLMClient) -> None:
    out = client.generate("hello world")
    assert out == "ok"
    usage = client.usage_snapshot()
    assert usage["requests"] == 1
    assert usage["prompt_chars"] == len("hello world")
    assert usage["tokens_est"] > 0


def test_generate_json_parses_plain_json(client: LLMClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client, "generate", lambda _prompt: '{"x": 1, "name": "ok"}')
    parsed = client.generate_json("prompt")
    assert parsed["x"] == 1
    assert parsed["name"] == "ok"


def test_generate_json_parses_markdown_json(client: LLMClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(client, "generate", lambda _prompt: '```json\n{"status":"ok"}\n```')
    parsed = client.generate_json("prompt")
    assert parsed == {"status": "ok"}


def test_generate_json_returns_empty_dict_on_invalid_json(
    client: LLMClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(client, "generate", lambda _prompt: "not-json")
    assert client.generate_json("prompt") == {}


def test_cache_key_and_local_cache_roundtrip(client: LLMClient) -> None:
    key = client._cache_key("json", "prompt")
    client._cache_set(key, {"a": 1})
    assert client._cache_get(key) == {"a": 1}


def test_cache_eviction(client: LLMClient) -> None:
    client._cache_max = 1
    client._cache_set("a", 1)
    client._cache_set("b", 2)
    assert client._cache_get("a") is None
    assert client._cache_get("b") == 2


def test_with_retry_eventually_succeeds(client: LLMClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm_module.time, "sleep", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(llm_module.random, "uniform", lambda *_args, **_kwargs: 0.0)

    state = {"count": 0}

    def flaky():
        state["count"] += 1
        if state["count"] < 2:
            raise RuntimeError("temp")
        return "done"

    assert client._with_retry(flaky) == "done"
    assert state["count"] == 2


def test_with_retry_raises_after_max_attempts(
    client: LLMClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(llm_module.time, "sleep", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(llm_module.random, "uniform", lambda *_args, **_kwargs: 0.0)

    with pytest.raises(RuntimeError, match="hard-fail"):
        client._with_retry(lambda: (_ for _ in ()).throw(RuntimeError("hard-fail")))


def test_reset_usage(client: LLMClient) -> None:
    client._usage["requests"] = 3
    client.reset_usage()
    assert client.usage_snapshot()["requests"] == 0


def test_check_ollama_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {"models": [{"name": "llama3.1:8b"}]}

    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return payload

    monkeypatch.setattr(llm_module.httpx, "get", lambda *_args, **_kwargs: _Resp())
    result = check_ollama("http://localhost:11434", ["llama3.1:8b"])
    assert result == payload


def test_check_ollama_raises_when_missing_model(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"models": [{"name": "other"}]}

    monkeypatch.setattr(llm_module.httpx, "get", lambda *_args, **_kwargs: _Resp())
    with pytest.raises(RuntimeError, match="missing models"):
        check_ollama("http://localhost:11434", ["required-model"])


def test_check_ollama_raises_when_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(*_args, **_kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(llm_module.httpx, "get", _raise)
    with pytest.raises(RuntimeError, match="not reachable"):
        check_ollama("http://localhost:11434", ["any"])
