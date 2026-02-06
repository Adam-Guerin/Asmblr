from __future__ import annotations

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST


class PrometheusMetrics:
    def __init__(self) -> None:
        self.api_requests = Counter(
            "asmblr_api_requests_total",
            "Total API requests",
            ["path", "status"],
        )
        self.api_latency = Histogram(
            "asmblr_api_request_duration_seconds",
            "API request latency in seconds",
            ["path"],
        )
        self.llm_requests = Counter(
            "asmblr_llm_requests_total",
            "Total LLM requests",
            ["model", "status"],
        )
        self.llm_latency = Histogram(
            "asmblr_llm_request_duration_seconds",
            "LLM request latency in seconds",
            ["model"],
        )

    @property
    def content_type(self) -> str:
        return CONTENT_TYPE_LATEST

    def record_api(self, path: str, status: str, duration_ms: float) -> None:
        safe_path = path or "/"
        self.api_requests.labels(path=safe_path, status=status).inc()
        self.api_latency.labels(path=safe_path).observe(duration_ms / 1000.0)

    def record_llm(self, model: str, duration_ms: float, ok: bool) -> None:
        status = "ok" if ok else "error"
        self.llm_requests.labels(model=model or "unknown", status=status).inc()
        self.llm_latency.labels(model=model or "unknown").observe(duration_ms / 1000.0)

    def render(self) -> bytes:
        return generate_latest()


PROM_METRICS = PrometheusMetrics()
