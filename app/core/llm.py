import json
from collections import OrderedDict
from copy import deepcopy
import time
import random
import httpx
from typing import Any
from loguru import logger

from app.core.metrics import METRICS
from app.core.metrics_prom import PROM_METRICS
from app.core.constants import (
    LLM_RETRY_ATTEMPTS,
    LLM_RETRY_BASE_DELAY_S,
    LLM_RETRY_JITTER_MAX_S,
)
try:
    from langchain_ollama import ChatOllama
    from langchain_core.messages import HumanMessage
except Exception:  # pragma: no cover - optional dependency path
    ChatOllama = None
    HumanMessage = None


class LLMClient:
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url
        self.model = model
        self._client = None
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._cache_max = 256
        self._usage: dict[str, int] = {
            "requests": 0,
            "cache_hits": 0,
            "prompt_chars": 0,
            "output_chars": 0,
        }
        if ChatOllama is not None:
            try:
                self._client = ChatOllama(base_url=base_url, model=model, temperature=0.3)
            except Exception as exc:
                logger.warning("Ollama init failed: {err}", err=exc)
                self._client = None

    def available(self) -> bool:
        return self._client is not None

    def generate(self, prompt: str) -> str:
        if not self._client:
            raise RuntimeError("LLM not available")
        cache_key = self._cache_key("text", prompt)
        cached = self._cache_get(cache_key)
        if cached is not None:
            logger.debug("llm_cache_hit model={model} flavor=text", model=self.model)
            self._usage["cache_hits"] += 1
            return cached
        self._usage["prompt_chars"] += len(prompt or "")
        content = self._with_retry(lambda: self._client([HumanMessage(content=prompt)]).content)
        self._usage["requests"] += 1
        self._usage["output_chars"] += len(str(content or ""))
        self._cache_set(cache_key, content)
        return content

    def generate_json(self, prompt: str) -> dict[str, Any]:
        cache_key = self._cache_key("json", prompt)
        cached = self._cache_get(cache_key)
        if cached is not None:
            logger.debug("llm_cache_hit model={model} flavor=json", model=self.model)
            return deepcopy(cached)
        raw = self._with_retry(lambda: self.generate(prompt))
        try:
            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw, re.DOTALL)
            if json_match:
                raw = json_match.group(1)
            # Also try to find JSON in the text without markdown
            elif '{' in raw and '}' in raw:
                # Extract the first JSON-like structure
                start = raw.find('{')
                end = raw.rfind('}') + 1
                raw = raw[start:end]
            parsed = json.loads(raw)
            self._cache_set(cache_key, parsed)
            return deepcopy(parsed)
        except (json.JSONDecodeError, Exception) as exc:
            logger.warning(f"Failed to parse JSON from LLM: {exc}. Raw response: {raw[:200]}")
            return {}

    def _cache_key(self, flavor: str, prompt: str) -> str:
        return f"{self.model}:{flavor}:{prompt}"

    def _cache_get(self, key: str) -> Any | None:
        if key not in self._cache:
            return None
        self._cache.move_to_end(key)
        return self._cache[key]

    def _cache_set(self, key: str, value: Any) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        if len(self._cache) > self._cache_max:
            self._cache.popitem(last=False)

    def _with_retry(self, fn):
        attempts = LLM_RETRY_ATTEMPTS
        base_delay = LLM_RETRY_BASE_DELAY_S
        for attempt in range(1, attempts + 1):
            start = time.time()
            try:
                result = fn()
                duration_ms = (time.time() - start) * 1000
                METRICS.record_llm(self.model, duration_ms, ok=True)
                PROM_METRICS.record_llm(self.model, duration_ms, ok=True)
                return result
            except Exception as exc:
                duration_ms = (time.time() - start) * 1000
                METRICS.record_llm(self.model, duration_ms, ok=False)
                PROM_METRICS.record_llm(self.model, duration_ms, ok=False)
                if attempt == attempts:
                    raise
                delay = base_delay * (2 ** (attempt - 1))
                delay += random.uniform(0.0, LLM_RETRY_JITTER_MAX_S)
                logger.warning("LLM retry {attempt}/{total} after error: {err}", attempt=attempt, total=attempts, err=exc)
                time.sleep(delay)

    def reset_usage(self) -> None:
        self._usage = {
            "requests": 0,
            "cache_hits": 0,
            "prompt_chars": 0,
            "output_chars": 0,
        }

    def usage_snapshot(self) -> dict[str, int]:
        snapshot = dict(self._usage)
        prompt_tokens_est = max(0, int(round(snapshot["prompt_chars"] / 4)))
        output_tokens_est = max(0, int(round(snapshot["output_chars"] / 4)))
        snapshot["prompt_tokens_est"] = prompt_tokens_est
        snapshot["output_tokens_est"] = output_tokens_est
        snapshot["tokens_est"] = prompt_tokens_est + output_tokens_est
        return snapshot


def check_ollama(base_url: str, models: list[str]) -> dict[str, Any]:
    """Verify Ollama is reachable and required models are available."""
    try:
        resp = httpx.get(f"{base_url}/api/tags", timeout=5.0)
        resp.raise_for_status()
    except Exception as exc:
        raise RuntimeError(
            "Ollama is not reachable. Install Ollama and ensure the service is running."
        ) from exc

    data = resp.json()
    available = {m.get("name") for m in data.get("models", []) if isinstance(m, dict)}
    missing = [m for m in models if m and m not in available]
    if missing:
        raise RuntimeError(
            f"Ollama is running but missing models: {', '.join(missing)}. "
            "Pull them with `ollama pull <model>`."
        )

    return data
