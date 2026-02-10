import json
import os
import math
import time
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from collections.abc import Callable
from urllib.parse import urlparse
from urllib.parse import urlencode, urlsplit, urlunsplit
import re
from zipfile import ZipFile, ZIP_DEFLATED
from loguru import logger

# Import du smart logger pour logging optimisé
try:
    from app.core.smart_logger import get_smart_logger, LogLevel, LogCategory
    SMART_LOGGER_AVAILABLE = True
except ImportError:
    SMART_LOGGER_AVAILABLE = False
    smart_logger = None

from app.core.config import Settings, validate_secrets
from app.core.deploy import deploy_run
from app.core.models import Idea, IdeaScore, RunResult, SeedInputs
from app.core.llm import LLMClient, check_ollama
from app.core.run_manager import RunManager
from app.tools.generator import default_content_pack, default_landing_payload
from app.tools.rag import RAGPlaybookQA
from app.langchain_tools import build_toolbox
from app.agents.crew import run_crewai_pipeline
from app.core.prerun_gate import PreRunGate
from app.core.logging import set_log_context, clear_log_context
from app.eval.confidence import compute_confidence, compute_pre_artifact_confidence
from app.signal_engine import SignalEngine
from app.signal_insights import (
    cluster_pains,
    extract_structured_pains,
    generate_opportunities,
)
from app.signal_quality import compute_novelty_score, compute_signal_quality
from app.project_build import ProjectBuilder
from app.mvp.builder import MVPBuilder, MVPBuilderError
from app.tools.repo_generator import generate_fastapi_skeleton
from app.mvp.frontend_kit.scaffold import write_frontend_scaffold
from app.core.sanitizer import DataSanitizer
from app.core.thresholds import (
    IDEA_ACTIONABILITY_MIN_SCORE,
    IDEA_ACTIONABILITY_ADJUSTMENT_MAX,
    LEARNING_HISTORY_MAX_RUNS,
    LEARNING_EXPLORATION_RATE,
    KEYWORD_LIST_MAX_SIZE,
    TOPIC_MIN_LENGTH,
    TOPIC_MAX_LENGTH,
    PAIN_SENTENCE_MIN_LENGTH,
    PAIN_LIST_MAX_SIZE,
    PAIN_KEYWORDS,
    FAILURE_REASON_MAX_LENGTH,
    TRACEBACK_HINT_MAX_LENGTH,
    RECENT_FAILURES_COUNT,
    PROJECT_NAME_MAX_LENGTH,
    THEME_CLEAN_MAX_LENGTH,
    ICP_ALIGNMENT_BONUS_MAX,
)
from app.core.exceptions import (
    AsmblrException,
    RunNotFoundError,
    InvalidTopicError,
    InvalidStateError,
    PipelineStageError,
    LLMUnavailableError,
    ModelNotFoundError,
    FileOperationError,
    handle_file_operation_error,
    convert_to_error_response,
)
from app.core.cache import (
    get_cached_artifact_loader,
    load_cached_json,
    load_cached_text,
    invalidate_cached_artifact,
)
from app.core.streaming import (
    StreamingDataProcessor,
    create_streaming_processor,
    process_large_feedback_file,
    process_large_historical_runs,
)
from app.core.product_metrics import PRODUCT_METRICS
from app.core.cache import (
    get_cached_artifact_loader,
    load_cached_json,
    load_cached_text,
    invalidate_cached_artifact,
)


class VenturePipeline:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.manager = RunManager(settings.runs_dir, settings.data_dir)
        self.general_llm = LLMClient(settings.ollama_base_url, settings.general_model)
        self.code_llm = LLMClient(settings.ollama_base_url, settings.code_model)
        self.active_general_model = settings.general_model
        self.active_code_model = settings.code_model
        self.rag = RAGPlaybookQA(settings.knowledge_dir)
        
        # Initialize product metrics
        from app.core.product_metrics import init_product_metrics, PRODUCT_METRICS
        init_product_metrics(settings.data_dir)

    def record_ollama_failure(self, run_id: str, exc: Exception, llm_summary: str | None = None) -> str:
        reason = f"Ollama check failed: {exc}"
        self.manager.update_status(run_id, "aborted")
        self.manager.write_artifact(run_id, "abort_reason.md", reason)
        summary = llm_summary or "LLM check: failed (Ollama not ready)"
        self.manager.write_artifact(run_id, "llm_check.md", summary)
        self._safe_write_ship_summary(run_id)
        return reason

    def _load_prompt(self, name: str) -> str:
        path = Path(__file__).resolve().parents[1] / "prompts" / f"{name}.txt"
        return path.read_text(encoding="utf-8")

    def _parse_fallback_models(self, raw: str) -> list[str]:
        if not raw:
            return []
        return [item.strip() for item in raw.split(",") if item and item.strip()]

    def _model_candidates(self) -> list[tuple[str, str]]:
        general_models = [self.settings.general_model] + self._parse_fallback_models(self.settings.general_model_fallbacks)
        code_models = [self.settings.code_model] + self._parse_fallback_models(self.settings.code_model_fallbacks)
        pairs: list[tuple[str, str]] = []
        for general_model in general_models:
            for code_model in code_models:
                pair = (general_model, code_model)
                if pair not in pairs:
                    pairs.append(pair)
        return pairs

    def _activate_models(self, general_model: str, code_model: str) -> None:
        if general_model != self.active_general_model:
            self.general_llm = LLMClient(self.settings.ollama_base_url, general_model)
            self.active_general_model = general_model
        if code_model != self.active_code_model:
            self.code_llm = LLMClient(self.settings.ollama_base_url, code_model)
            self.active_code_model = code_model

    def _ensure_llm_ready(self, run_id: str) -> None:
        errors: list[str] = []
        selected: tuple[str, str] | None = None
        for general_model, code_model in self._model_candidates():
            try:
                check_ollama(self.settings.ollama_base_url, [general_model, code_model])
                selected = (general_model, code_model)
                break
            except Exception as exc:
                errors.append(f"{general_model} + {code_model}: {exc}")
        if not selected:
            raise RuntimeError(" ; ".join(errors[-3:]) if errors else "No available model pair found")
        self._activate_models(*selected)
        selection_payload = {
            "run_id": run_id,
            "general_model": self.active_general_model,
            "code_model": self.active_code_model,
            "fallback_used": (
                self.active_general_model != self.settings.general_model
                or self.active_code_model != self.settings.code_model
            ),
            "checked_at": datetime.utcnow().isoformat(),
        }
        self.manager.write_json(run_id, "llm_model_selection.json", selection_payload)
        if selection_payload["fallback_used"]:
            self._log_progress(
                run_id,
                f"Self-healing: switched model pair to {self.active_general_model} / {self.active_code_model}",
            )

    def _failure_report_path(self, run_id: str) -> Path:
        run = self.manager.get_run(run_id)
        run_dir = Path(run["output_dir"]) if run else (self.settings.runs_dir / run_id)
        return run_dir / "failure_report.json"

    def _sanitize_artifact_data(self, data: Any, artifact_type: str = "json") -> Any:
        """Sanitize data before writing to artifacts."""
        return DataSanitizer.sanitize_for_artifact(data, artifact_type)
    
    def _write_sanitized_json(self, run_id: str, filename: str, data: Any) -> None:
        """Write sanitized JSON artifact."""
        sanitized_data = self._sanitize_artifact_data(data, "json")
        self.manager.write_json_atomic(run_id, filename, sanitized_data)

    def _record_failure_report(
        self,
        run_id: str,
        *,
        status: str,
        stage: str,
        reason: str,
        error_type: str,
        retryable: bool = False,
        attempt: int | None = None,
        max_attempts: int | None = None,
        traceback_hint: str | None = None,
    ) -> None:
        path = self._failure_report_path(run_id)
        existing = self._load_json_artifact(path) or {}
        failures = list(existing.get("stage_failures") or [])
        payload = {
            "run_id": run_id,
            "status": status,
            "stage": stage,
            "reason": reason[:FAILURE_REASON_MAX_LENGTH],
            "error_type": error_type,
            "retryable": retryable,
            "attempt": attempt,
            "max_attempts": max_attempts,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if traceback_hint:
            payload["traceback_hint"] = traceback_hint[:TRACEBACK_HINT_MAX_LENGTH]
        failures.append(payload)
        report = {
            "run_id": run_id,
            "status": status,
            "last_stage": stage,
            "last_reason": reason[:FAILURE_REASON_MAX_LENGTH],
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "stage_failures": failures[-RECENT_FAILURES_COUNT:],
        }
        self.manager.write_json(run_id, "failure_report.json", report)
        lines = [
            "# Failure Report",
            "",
            f"- Status: {report['status']}",
            f"- Last stage: {report['last_stage']}",
            f"- Last reason: {report['last_reason']}",
            f"- Total stage failures: {len(report['stage_failures'])}",
            "",
            "## Recent failures",
        ]
        for item in report["stage_failures"][-RECENT_FAILURES_COUNT:]:
            lines.append(
                f"- [{item.get('timestamp')}] stage={item.get('stage')} type={item.get('error_type')} "
                f"attempt={item.get('attempt')}/{item.get('max_attempts')} retryable={item.get('retryable')} "
                f"reason={item.get('reason')}"
            )
        self.manager.write_artifact(run_id, "failure_report.md", "\n".join(lines).rstrip() + "\n")

    def _run_stage_with_retries(
        self,
        run_id: str,
        stage: str,
        action: Callable[[], Any],
    ) -> Any:
        if not self.settings.enable_self_healing:
            self.manager.begin_stage(run_id, stage)
            result = action()
            self.manager.complete_stage(run_id, stage)
            return result
        attempts = max(1, int(self.settings.stage_retry_attempts))
        backoff = max(0.0, float(self.settings.stage_retry_backoff_sec))
        last_exc: Exception | None = None
        for attempt in range(1, attempts + 1):
            self.manager.begin_stage(run_id, stage)
            try:
                result = action()
                self.manager.complete_stage(run_id, stage)
                if attempt > 1:
                    self._log_progress(run_id, f"Self-healing: recovered stage '{stage}' on attempt {attempt}/{attempts}")
                return result
            except Exception as exc:
                last_exc = exc
                retryable = attempt < attempts
                self._record_failure_report(
                    run_id,
                    status="retrying" if retryable else "failed",
                    stage=stage,
                    reason=str(exc),
                    error_type=exc.__class__.__name__,
                    retryable=retryable,
                    attempt=attempt,
                    max_attempts=attempts,
                )
                self._log_progress(
                    run_id,
                    f"Self-healing: stage '{stage}' failed ({attempt}/{attempts}) - {exc}",
                )
                if retryable and backoff > 0:
                    time.sleep(backoff * attempt)
        if last_exc is None:
            raise RuntimeError(f"Stage {stage} failed without exception detail")
        raise last_exc

    def _ensure_repo_skeleton(self, run_id: str, topic: str) -> None:
        run_dir = self.settings.runs_dir / run_id
        repo_dir = run_dir / "repo_skeleton"
        if repo_dir.exists():
            return
        try:
            project_name = (topic or "Launchpad").strip()[:PROJECT_NAME_MAX_LENGTH] or "Launchpad"
            # Use React/TypeScript scaffold instead of FastAPI
            write_frontend_scaffold(repo_dir, project_name, brief=f"{project_name} helps teams launch with clarity", audience="founders and small teams", style="startup_clean")
        except Exception as exc:
            self.manager.write_artifact(run_id, "repo_skeleton_error.md", str(exc))

    def _validate_topic(self, topic: str) -> str | None:
        cleaned = (topic or "").strip()
        if len(cleaned) < TOPIC_MIN_LENGTH or len(cleaned) > TOPIC_MAX_LENGTH:
            return "Topic must be between 3 and 200 characters."
        if any(ord(ch) < 32 for ch in cleaned):
            return "Topic contains control characters."
        return None

    def _extract_pain_statements(self, pages: list[dict[str, Any]]) -> list[str]:
        pains: list[str] = []
        for page in pages:
            text = (page.get("text") or "").split(".")
            for sentence in text:
                s = sentence.strip()
                if len(s) < PAIN_SENTENCE_MIN_LENGTH:
                    continue
                if any(token in s.lower() for token in PAIN_KEYWORDS):
                    pains.append(s)
        return pains[:PAIN_LIST_MAX_SIZE]

    def _is_generic_pain(self, pain: str) -> bool:
        generic = [
            "save time",
            "increase productivity",
            "improve efficiency",
            "automate tasks",
            "streamline workflow",
        ]
        return any(g in pain.lower() for g in generic)

    def _data_self_test(self, pages: list[dict[str, Any]], pains: list[str]) -> dict[str, Any]:
        texts = [p.get("text", "") for p in pages if p.get("text")]
        avg_len = int(sum(len(t) for t in texts) / max(1, len(texts)))
        domains = {urlparse(p.get("url", "")).netloc for p in pages if p.get("url")}
        non_generic = [p for p in pains if not self._is_generic_pain(p)]
        return {
            "pages_count": len(pages),
            "avg_text_len": avg_len,
            "unique_domains": len(domains),
            "pain_count": len(pains),
            "non_generic_pain_count": len(non_generic),
            "non_generic_pains": non_generic[:5],
        }

    def run(
        self,
        topic: str,
        n_ideas: int,
        fast_mode: bool = False,
        run_id: str | None = None,
        seed_inputs: SeedInputs | None = None,
        resume: bool = False,
        execution_profile: str | None = None,
    ) -> RunResult:
        seeds = seed_inputs or SeedInputs()
        if not seeds.icp and (self.settings.primary_icp or "").strip():
            seeds.icp = self.settings.primary_icp.strip()
        decision_signals: dict[str, Any] = {}
        decision_missing: list[str] = []
        decision_hypotheses: list[str] = []
        run_started_ts = time.time()
        budget_warning_emitted = False

        if run_id is None:
            run_id = self.manager.create_run(topic)
            # Record run start for product metrics
            if PRODUCT_METRICS:
                PRODUCT_METRICS.record_run_start(run_id)
        else:
            run_info = self.manager.get_run(run_id)
            if not run_info:
                raise RunNotFoundError(run_id)

        state = self.manager.get_state(run_id)
        if resume:
            if state and state.get("status") in ("completed", "killed", "aborted"):
                raise InvalidStateError(
                    operation="resume run",
                    current_state=state.get("status", "unknown"),
                    required_state="not finalized"
                )
            if state and state.get("params"):
                params = state["params"]
                topic = params.get("topic", topic)
                n_ideas = int(params.get("n_ideas", n_ideas))
                fast_mode = bool(params.get("fast_mode", fast_mode))
                execution_profile = params.get("execution_profile") or execution_profile
                if seed_inputs is None:
                    seeds = self._seed_from_dict(params.get("seed_inputs", {}))
        profile = self._resolve_execution_profile(execution_profile, fast_mode)
        execution_profile = profile["name"]
        if profile.get("force_fast_mode"):
            fast_mode = True
        n_ideas = min(int(n_ideas), int(profile["max_n_ideas"]))
        params_payload = {
            "topic": topic,
            "n_ideas": n_ideas,
            "fast_mode": fast_mode,
            "execution_profile": execution_profile,
            "seed_inputs": self._seed_to_dict(seeds),
        }
        state = self.manager.init_state(run_id, params=params_payload)

        decision_hypotheses = self._describe_seed_hypotheses(seeds)
        if fast_mode:
            n_ideas = 3
        adaptive_thresholds = self._compute_adaptive_thresholds(topic)
        signal_quality_threshold = int(adaptive_thresholds.get("signal_quality_threshold", self.settings.signal_quality_threshold))
        kill_threshold = int(adaptive_thresholds.get("kill_threshold", self.settings.kill_threshold))
        original_max_sources = self.settings.max_sources
        original_stage_retry_attempts = self.settings.stage_retry_attempts
        self.settings.max_sources = int(profile["max_sources"])
        self.settings.stage_retry_attempts = int(profile["stage_retry_attempts"])
        self.general_llm.reset_usage()
        self.code_llm.reset_usage()

        def _budget_snapshot(phase: str) -> dict[str, Any]:
            general_usage = self.general_llm.usage_snapshot()
            code_usage = self.code_llm.usage_snapshot()
            elapsed_sec = max(0.0, time.time() - run_started_ts)
            token_est = int(general_usage.get("tokens_est", 0)) + int(code_usage.get("tokens_est", 0))
            time_budget_sec = int(profile["time_budget_min"]) * 60
            token_budget = int(profile["token_budget_est"])
            return {
                "run_id": run_id,
                "phase": phase,
                "profile": profile["name"],
                "budget": {
                    "time_budget_min": int(profile["time_budget_min"]),
                    "time_budget_sec": time_budget_sec,
                    "token_budget_est": token_budget,
                },
                "consumed": {
                    "elapsed_sec": round(elapsed_sec, 2),
                    "token_est": token_est,
                    "llm_usage": {
                        "general": general_usage,
                        "code": code_usage,
                    },
                },
                "over_budget": {
                    "time": elapsed_sec > time_budget_sec,
                    "token": token_est > token_budget,
                },
                "applied_overrides": {
                    "max_sources": self.settings.max_sources,
                    "stage_retry_attempts": self.settings.stage_retry_attempts,
                    "max_n_ideas": int(profile["max_n_ideas"]),
                },
            }

        def _record_budget(phase: str) -> None:
            nonlocal budget_warning_emitted
            snapshot = _budget_snapshot(phase)
            
            # Use atomic write for budget file to prevent race conditions
            self.manager.write_json_atomic(run_id, "run_budget.json", snapshot)
            
            if not budget_warning_emitted and (snapshot["over_budget"]["time"] or snapshot["over_budget"]["token"]):
                budget_warning_emitted = True
                self._log_progress(
                    run_id,
                    (
                        "Budget warning: "
                        f"elapsed={snapshot['consumed']['elapsed_sec']}s/"
                        f"{snapshot['budget']['time_budget_sec']}s, "
                        f"tokens_est={snapshot['consumed']['token_est']}/"
                        f"{snapshot['budget']['token_budget_est']}"
                    ),
                )

        self.manager.update_status(run_id, "running")
        self.manager.update_state(run_id, status="running")
        set_log_context(run_id=run_id)
        self._log_progress(run_id, f"Run started (topic='{DataSanitizer.sanitize_topic(topic)}')")
        self._log_progress(
            run_id,
            (
                f"Execution profile={profile['name']} "
                f"(time_budget={profile['time_budget_min']}m, token_budget_est={profile['token_budget_est']}, "
                f"max_sources={profile['max_sources']}, max_n_ideas={profile['max_n_ideas']})"
            ),
        )
        _record_budget("start")
        self._log_progress(
            run_id,
            (
                "Adaptive thresholds: "
                f"signal_quality={signal_quality_threshold} (base {self.settings.signal_quality_threshold}), "
                f"kill={kill_threshold} (base {self.settings.kill_threshold}), "
                f"segment_records={adaptive_thresholds.get('segment_records', 0)}"
            ),
        )
        logger.info("Run {run_id} started", run_id=DataSanitizer.sanitize_run_id(run_id))
        run_dir = self.settings.runs_dir / run_id
        self.manager.write_json_atomic(run_id, "adaptive_thresholds.json", adaptive_thresholds)
        decision_signals["primary_icp"] = self.settings.primary_icp
        decision_signals["adaptive_thresholds"] = {
            "signal_quality_threshold": signal_quality_threshold,
            "kill_threshold": kill_threshold,
            "segment_records": adaptive_thresholds.get("segment_records", 0),
            "segment_weighted_learning_score": adaptive_thresholds.get("segment_weighted_learning_score"),
            "global_records": adaptive_thresholds.get("global_records", 0),
        }
        decision_signals["execution_profile"] = {
            "name": profile["name"],
            "time_budget_min": profile["time_budget_min"],
            "token_budget_est": profile["token_budget_est"],
            "max_sources": profile["max_sources"],
            "max_n_ideas": profile["max_n_ideas"],
            "stage_retry_attempts": profile["stage_retry_attempts"],
        }
        self._ensure_repo_skeleton(run_id, topic)

        topic_error = self._validate_topic(topic)
        if topic_error:
            raise InvalidTopicError(topic, topic_error)
            self._write_decision_file(
                run_id,
                "ABORT",
                topic_error,
                decision_signals,
                decision_hypotheses,
                decision_missing,
            )
            _record_budget("topic_validation_abort")
            self.settings.max_sources = original_max_sources
            self.settings.stage_retry_attempts = original_stage_retry_attempts
            clear_log_context()
            return RunResult(
                run_id=run_id,
                ideas=[],
                scores=[],
                top_idea=IdeaScore(
                    name="unknown",
                    score=0,
                    rationale=topic_error,
                    risks=[],
                    signals={},
                ),
                artifacts={},
            )

        if seeds.has_any():
            self._write_seed_context(run_id, seeds)
            self._log_progress(run_id, "Seed context recorded")

        try:
            try:
                self._ensure_llm_ready(run_id)
            except Exception as exc:
                reason = self.record_ollama_failure(run_id, exc)
                self._log_progress(run_id, "Abort: Ollama unreachable")
                decision_missing.append("Ollama unreachable")
                self.manager.update_state(run_id, status="aborted")
                self._record_failure_report(
                    run_id,
                    status="aborted",
                    stage="llm_readiness",
                    reason=reason,
                    error_type=exc.__class__.__name__,
                    retryable=False,
                )
                self._write_decision_file(
                    run_id,
                    "ABORT",
                    reason,
                    decision_signals,
                    decision_hypotheses,
                    decision_missing,
                )
                return RunResult(
                    run_id=run_id,
                    ideas=[],
                    scores=[],
                    top_idea=IdeaScore(
                        name="unknown",
                        score=0,
                        rationale=str(exc),
                        risks=[],
                        signals={},
                    ),
                    artifacts={},
                )

            llm_check_path = run_dir / "llm_check.md"
            if not self._stage_complete(run_id, "llm_check") or not llm_check_path.exists():
                llm_check: dict[str, Any] = {"text_ok": False, "json_ok": False, "errors": []}

                def _llm_check_action() -> dict[str, Any]:
                    payload: dict[str, Any] = {"text_ok": False, "json_ok": False, "errors": []}
                    try:
                        text_resp = self.general_llm.generate("Return a short sentence: ok.")
                        payload["text_ok"] = bool(text_resp and isinstance(text_resp, str))
                    except Exception as exc:
                        payload["errors"].append(f"text_prompt_failed: {exc}")
                    try:
                        json_resp = self.general_llm.generate_json("Return strict JSON: {\"ok\": true}")
                        payload["json_ok"] = isinstance(json_resp, dict) and json_resp.get("ok") is True
                    except Exception as exc:
                        payload["errors"].append(f"json_prompt_failed: {exc}")
                    self.manager.write_artifact(run_id, "llm_check.md", f"LLM check: {payload}")
                    if not (payload["text_ok"] and payload["json_ok"]):
                        raise RuntimeError("LLM self-test failed")
                    return payload

                try:
                    llm_check = self._run_stage_with_retries(run_id, "llm_check", _llm_check_action)
                except Exception:
                    # One last attempt with fallback model pair before aborting the run.
                    try:
                        self._ensure_llm_ready(run_id)
                        llm_check = self._run_stage_with_retries(run_id, "llm_check", _llm_check_action)
                    except Exception as exc:
                        reason = "LLM self-test failed"
                        self.manager.update_status(run_id, "aborted")
                        self.manager.update_state(run_id, status="aborted")
                        self.manager.write_artifact(run_id, "abort_reason.md", reason)
                        self._log_progress(run_id, "Abort: LLM self-test failed")
                        decision_missing.append("LLM self-test failed")
                        self._record_failure_report(
                            run_id,
                            status="aborted",
                            stage="llm_check",
                            reason=str(exc),
                            error_type=exc.__class__.__name__,
                            retryable=False,
                        )
                        self._write_decision_file(
                            run_id,
                            "ABORT",
                            reason,
                            decision_signals,
                            decision_hypotheses,
                            decision_missing,
                        )
                        return RunResult(
                            run_id=run_id,
                            ideas=[],
                            scores=[],
                            top_idea=IdeaScore(name="unknown", score=0, rationale=reason, risks=[], signals={}),
                            artifacts={},
                        )
            _record_budget("llm_check")

            sources_path = self.settings.config_dir / "sources.yaml"
            try:
                import yaml

                data = yaml.safe_load(sources_path.read_text(encoding="utf-8")) or {}
            except Exception:
                data = {}

            def _section(name: str) -> list[dict[str, str]]:
                items = []
                for item in data.get(name, []):
                    if not isinstance(item, dict) or "name" not in item or "url" not in item:
                        continue
                    payload = dict(item)
                    items.append(payload)
                return items

            pain_sources = _section("pain_sources")
            competitor_sources = _section("competitor_sources")

            tools = build_toolbox(self.settings, self.general_llm, judge_prompt=self._load_prompt("llm_judge_scoring"))
            cache_dir = str(self.settings.data_dir / "cache")
            signal_topic = f"{topic} {seeds.theme}".strip() if seeds.theme else topic
            if seeds.theme:
                theme_clean = " ".join(str(seeds.theme).split())[:240]
                self.manager.write_artifact(
                    run_id,
                    "theme_scope.md",
                    "# Theme scope\n\n"
                    f"- Topic: {topic}\n"
                    f"- Theme: {theme_clean}\n"
                    f"- Applied to scraping query: {signal_topic}\n",
                )
                self._log_progress(
                    run_id,
                    f"Signal engine: scraping sources with theme '{theme_clean}'",
                )
            else:
                self._log_progress(run_id, "Signal engine: scraping sources")
            signal_engine = SignalEngine(
                settings=self.settings,
                output_dir=self.settings.runs_dir / run_id,
                topic=signal_topic,
                fast_mode=fast_mode,
            )
            pre_pages: list[dict[str, Any]] = []
            raw_pages: list[dict[str, Any]] = []
            structured_pains: list[dict[str, Any]] = []
            structured_result: dict[str, Any] = {"pains": [], "rejected": []}
            clusters: list[dict[str, Any]] = []
            opportunities: list[dict[str, Any]] = []
            novelty: dict[str, Any] = {"novelty_score": 0, "breakdown": {}, "keywords": []}
            signal_quality: dict[str, Any] = {"score": 0, "breakdown": {}}
            if pain_sources:
                if self._stage_complete(run_id, "signal_engine"):
                    raw_pages, pre_pages = self._load_signal_pages(run_dir)
                if not pre_pages:
                    signal_output = self._run_stage_with_retries(
                        run_id,
                        "signal_engine",
                        lambda: signal_engine.run(pain_sources),
                    )
                    raw_pages = signal_output.raw_pages
                    pre_pages = signal_output.deduped_pages
                    self._log_progress(run_id, f"Signal engine: collected {len(pre_pages)} unique pages")
                _record_budget("signal_engine")
                if self._stage_complete(run_id, "pain_structuring"):
                    structured_result = self._load_json_artifact(run_dir / "pains_structured.json") or structured_result
                    structured_pains = structured_result.get("pains", [])
                    clusters_payload = self._load_json_artifact(run_dir / "pain_clusters.json") or {}
                    clusters = clusters_payload.get("clusters", [])
                    opportunities_payload = self._load_json_artifact(run_dir / "opportunities_structured.json") or {}
                    opportunities = opportunities_payload.get("items", [])
                    novelty = self._load_json_artifact(run_dir / "novelty_score.json") or 0
                    signal_quality = self._load_json_artifact(run_dir / "signal_quality.json") or {"score": 0}
                else:
                    def _pain_structuring_action() -> dict[str, Any]:
                        local_structured = extract_structured_pains(pre_pages)
                        local_structured_pains = local_structured["pains"]
                        self.manager.write_json(run_id, "pains_structured.json", local_structured)
                        local_clusters = cluster_pains(local_structured_pains)
                        self.manager.write_json(run_id, "pain_clusters.json", {"clusters": local_clusters})
                        local_opportunities = generate_opportunities(local_clusters, local_structured_pains)
                        self.manager.write_json(
                            run_id,
                            "opportunities_structured.json",
                            {"opportunities": local_opportunities},
                        )
                        local_novelty = compute_novelty_score(pre_pages, local_structured_pains, self.settings)
                        self.manager.write_json(run_id, "novelty_score.json", local_novelty)
                        local_signal_quality = compute_signal_quality(
                            pre_pages,
                            local_structured_pains,
                            local_clusters,
                            local_novelty["novelty_score"],
                            self.settings,
                        )
                        self.manager.write_json(run_id, "signal_quality.json", local_signal_quality)
                        return {
                            "structured_result": local_structured,
                            "structured_pains": local_structured_pains,
                            "clusters": local_clusters,
                            "opportunities": local_opportunities,
                            "novelty": local_novelty,
                            "signal_quality": local_signal_quality,
                        }

                    struct_payload = self._run_stage_with_retries(run_id, "pain_structuring", _pain_structuring_action)
                    structured_result = struct_payload["structured_result"]
                    structured_pains = struct_payload["structured_pains"]
                    clusters = struct_payload["clusters"]
                    opportunities = struct_payload["opportunities"]
                    novelty = struct_payload["novelty"]
                    signal_quality = struct_payload["signal_quality"]
                    decision_signals["cluster_count"] = len(clusters)
                    decision_signals["structured_pain_count"] = len(structured_pains)
                    decision_signals["signal_quality"] = signal_quality["score"]
                    decision_signals["novelty_score"] = novelty["novelty_score"]
                decision_signals["cluster_count"] = len(clusters)
                decision_signals["structured_pain_count"] = len(structured_pains)
                decision_signals["signal_quality"] = signal_quality["score"]
                decision_signals["novelty_score"] = novelty["novelty_score"]
            else:
                self.manager.write_json(run_id, "signal_quality.json", signal_quality)
                self.manager.write_json(run_id, "novelty_score.json", novelty)

            pre_competitor_pages: list[dict[str, Any]] = []
            competitor_pages_path = run_dir / "competitor_pages.json"
            if competitor_sources:
                if self._stage_complete(run_id, "competitor_scrape") and competitor_pages_path.exists():
                    pre_competitor_pages = self._load_json_artifact(competitor_pages_path) or []
                if not pre_competitor_pages:
                    pre_competitor_pages = self._run_stage_with_retries(
                        run_id,
                        "competitor_scrape",
                        lambda: json.loads(
                            tools["web"].run(
                                {
                                    "sources": competitor_sources,
                                    "max_sources": len(competitor_sources),
                                    "cache_dir": cache_dir,
                                    "timeout": self.settings.request_timeout,
                                    "rate_limit_per_domain": self.settings.rate_limit_per_domain,
                                    "retry_max_attempts": self.settings.retry_max_attempts,
                                    "retry_min_wait": self.settings.retry_min_wait,
                                    "retry_max_wait": self.settings.retry_max_wait,
                                }
                            )
                        ),
                    )
                    self.manager.write_json(run_id, "competitor_pages.json", pre_competitor_pages)
            competitor_analysis_path = run_dir / "competitor_analysis.json"
            if pre_competitor_pages and not competitor_analysis_path.exists():
                try:
                    competitors_payload = json.loads(tools["competitor"].run({"pages": pre_competitor_pages}))
                except Exception:
                    competitors_payload = []
                self.manager.write_json(run_id, "competitor_analysis.json", {"competitors": competitors_payload})

            if self._stage_complete(run_id, "data_validation"):
                validated_pains = self._load_json_artifact(run_dir / "pains_validated.json") or {"validated": [], "rejected": []}
                market_score = self._load_json_artifact(run_dir / "market_signal_score.json") or {"score": 0}
            else:
                self.manager.begin_stage(run_id, "data_validation")
                if structured_pains:
                    raw_pains = [pain["problem"] for pain in structured_pains]
                else:
                    raw_pains = self._extract_pain_statements(pre_pages)
                data_check = self._data_self_test(pre_pages, raw_pains)
                self.manager.write_artifact(run_id, "data_check.md", f"Data check: {data_check}")
                self._log_progress(run_id, f"Data check: pages={data_check['pages_count']} pains={data_check['pain_count']}")

                if structured_pains:
                    validated_pains = {"validated": structured_pains, "rejected": structured_result["rejected"]}
                else:
                    validated_pains = self._validate_pains(raw_pains)
                self.manager.write_json(run_id, "pains_validated.json", validated_pains)
                validated_texts = [item["text"] for item in validated_pains["validated"]]
                decision_signals["validated_pain_count"] = len(validated_texts)
                decision_signals["data_check"] = data_check

                market_score = self._compute_market_signal_score(
                    pages=pre_pages,
                    validated_pains=validated_pains["validated"],
                    settings=self.settings,
                )
                decision_signals["market_signal"] = market_score
                self.manager.write_json(run_id, "market_signal_score.json", market_score)
                self.manager.complete_stage(run_id, "data_validation")

            validated_texts = [item["text"] for item in validated_pains["validated"]]
            if "validated_pain_count" not in decision_signals:
                decision_signals["validated_pain_count"] = len(validated_texts)
            if "data_check" not in decision_signals:
                raw_pains_for_check = [pain.get("problem") for pain in structured_pains] if structured_pains else validated_texts
                decision_signals["data_check"] = self._data_self_test(pre_pages, raw_pains_for_check)
            if "market_signal" not in decision_signals:
                decision_signals["market_signal"] = market_score

            if market_score["score"] < self.settings.market_signal_threshold:
                reason = (
                    f"Market signal score {market_score['score']} below threshold {self.settings.market_signal_threshold}."
                )
                self.manager.update_status(run_id, "aborted")
                self.manager.write_artifact(run_id, "abort_reason.md", reason)
                self._log_progress(run_id, "Abort: market signal below threshold")
                decision_missing.append("Market signal score below threshold")
                self._write_decision_file(
                    run_id,
                    "ABORT",
                    reason,
                    decision_signals,
                    decision_hypotheses,
                    decision_missing,
                )
                return RunResult(
                    run_id=run_id,
                    ideas=[],
                    scores=[],
                    top_idea=IdeaScore(name="unknown", score=0, rationale=reason, risks=[], signals={}),
                    artifacts={},
                )

            competitor_candidates = self._derive_competitors_from_pages(pre_competitor_pages)
            if not competitor_candidates and pre_pages:
                try:
                    market_competitors = json.loads(tools["competitor"].run({"pages": pre_pages}))
                    if isinstance(market_competitors, list):
                        filtered = [
                            item
                            for item in market_competitors
                            if isinstance(item, dict) and str(item.get("product_name", "")).strip() not in ("", "unknown")
                        ]
                        if filtered:
                            competitor_candidates = filtered
                            self.manager.write_json(
                                run_id,
                                "competitor_analysis.json",
                                {"competitors": competitor_candidates, "source": "market_pages_fallback"},
                            )
                except Exception:
                    pass
            icp = seeds.icp or self.settings.primary_icp or self._infer_icp_from_pains(validated_pains["validated"]) or "unknown"
            data_source = {
                "pages": "real" if pre_pages else "fallback",
                "pains": "real" if validated_texts else "fallback",
                "competitors": "real" if competitor_candidates else "fallback",
                "seeds": "seed" if seeds.has_any() else "none",
            }

            # Rule: Automatically propose collection actions for unknown critical fields
            self._propose_collection_actions_for_unknown_fields(run_id, data_source, topic, decision_missing)

            gate = PreRunGate(
                min_pages=self.settings.min_pages,
                min_pains=self.settings.min_pains,
                min_competitors=self.settings.min_competitors,
                min_signal_quality=signal_quality_threshold,
            )
            gate_result = gate.evaluate(
                pre_pages,
                validated_texts,
                competitor_candidates,
                icp,
                data_source,
                signal_quality=signal_quality,
            )
            if not gate_result.ok:
                reason = "PreRunGate failed:\n- " + "\n- ".join(gate_result.reasons)
                self.manager.update_status(run_id, "aborted")
                self.manager.write_artifact(run_id, "abort_reason.md", reason)
                self._log_progress(run_id, "Abort: PreRunGate failed")
                decision_missing.extend(gate_result.reasons)
                self._write_decision_file(
                    run_id,
                    "ABORT",
                    reason,
                    decision_signals,
                    decision_hypotheses,
                    decision_missing,
                )
                return RunResult(
                    run_id=run_id,
                    ideas=[],
                    scores=[],
                    top_idea=IdeaScore(name="unknown", score=0, rationale=reason, risks=[], signals={}),
                    artifacts={},
                )

            crew_outputs: dict[str, Any] = {}
            crew_outputs_path = run_dir / "crew_outputs.json"
            if self._stage_complete(run_id, "crew_pipeline") and crew_outputs_path.exists():
                crew_outputs = self._load_json_artifact(crew_outputs_path) or {}
                self._log_progress(run_id, "CrewAI: loaded cached outputs")
            else:
                self._log_progress(run_id, "CrewAI: starting agent pipeline")
                crew_outputs = self._run_stage_with_retries(
                    run_id,
                    "crew_pipeline",
                    lambda: run_crewai_pipeline(
                        topic,
                        self.settings,
                        self.general_llm,
                        run_id,
                        n_ideas,
                        fast_mode,
                        seed_pages=pre_pages,
                        seed_competitor_pages=pre_competitor_pages,
                        seed_inputs=seeds,
                        validated_pains=validated_texts,
                    ),
                )
                self._write_sanitized_json(run_id, "crew_outputs.json", crew_outputs)
                self._log_progress(run_id, "CrewAI: pipeline finished")
            _record_budget("crew_pipeline")
            research = crew_outputs.get("research", {})
            analysis = crew_outputs.get("analysis", {})
            product = crew_outputs.get("product", {})
            tech = crew_outputs.get("tech", {})
            growth = crew_outputs.get("growth", {})
            brand = crew_outputs.get("brand", {})

            pages = research.get("pages") or pre_pages or []
            pains = validated_texts
            competitors = analysis.get("competitors") or competitor_candidates
            if not competitors and pre_competitor_pages:
                try:
                    competitors = json.loads(tools["competitor"].run({"pages": pre_competitor_pages}))
                except Exception:
                    competitors = competitors or []

            structured_opportunities = self._load_json_artifact(run_dir / "opportunities_structured.json") or []
            idea_dicts = self._select_idea_dicts(analysis, research)
            if not idea_dicts:
                idea_dicts = self._derive_ideas_from_structured_opportunities(
                    structured_opportunities,
                    validated_pains["validated"],
                    seeds,
                    limit=max(1, n_ideas),
                )
            ideas = self._build_traceable_ideas(
                idea_dicts,
                validated_pains["validated"],
                pages,
                seeds,
            )
            if not ideas:
                reason = "No traceable ideas available after extraction."
                fallback_top_name = (
                    (analysis.get("top_idea") or {}).get("name")
                    or (growth.get("landing_payload") or {}).get("product_name")
                    or "Venture Ops Toolkit"
                )
                fallback_top = IdeaScore(
                    name=str(fallback_top_name),
                    score=0,
                    rationale=reason,
                    risks=[],
                    signals={},
                )
                try:
                    fallback_brand = self._normalize_brand_payload(
                        brand if isinstance(brand, dict) else {},
                        fallback_top.name,
                    )
                    self.manager.write_json(run_id, "brand_identity.json", fallback_brand)
                    self.manager.write_artifact(
                        run_id,
                        "brand_direction.md",
                        self._build_brand_markdown(fallback_brand),
                    )
                    self._generate_logo_assets(run_id, fallback_brand, fallback_top)

                    landing_dir = Path(growth.get("landing_dir") or (self.settings.runs_dir / run_id / "landing_page"))
                    if landing_dir.exists():
                        fallback_landing_payload = growth.get("landing_payload") or default_landing_payload(
                            fallback_top.name,
                            fast_mode=fast_mode,
                        )
                        fallback_landing_payload.setdefault("logo_src", "./logo.svg")
                        fallback_landing_payload.setdefault("logo_alt", f"{fallback_top.name} logo")
                        tools["landing"].run(
                            {
                                "product_name": fallback_top.name,
                                "output_dir": str(landing_dir),
                                "template_dir": str(Path(__file__).resolve().parents[2] / "templates"),
                                "payload": fallback_landing_payload,
                                "fast_mode": fast_mode,
                            }
                        )
                except Exception:
                    pass
                self.manager.update_status(run_id, "aborted")
                self.manager.write_artifact(run_id, "abort_reason.md", reason)
                self._log_progress(run_id, "Abort: no traceable ideas")
                decision_missing.append("Idea traceability missing")
                self._write_decision_file(
                    run_id,
                    "ABORT",
                    reason,
                    decision_signals,
                    decision_hypotheses,
                    decision_missing,
                )
                return RunResult(
                    run_id=run_id,
                    ideas=[],
                    scores=[],
                    top_idea=IdeaScore(name="unknown", score=0, rationale=reason, risks=[], signals={}),
                    artifacts={},
                )

            scores: list[IdeaScore] = []
            for item in analysis.get("scores", []):
                name = str(item.get("name", "unknown"))
                scores.append(
                    IdeaScore(
                        name=name,
                        score=int(item.get("score", 0)),
                        rationale=item.get("rationale", ""),
                        risks=item.get("risks", []),
                        signals=item.get("signals", {}),
                    )
                )
            if not scores:
                scores = [
                    IdeaScore(
                        name=idea.name,
                        score=55,
                        rationale="Base score from scraper-derived idea candidate.",
                        risks=[],
                        signals={},
                    )
                    for idea in ideas
                ]
            scores = self._apply_pragmatic_potential_to_scores(
                scores=scores,
                ideas=ideas,
                validated_pains=validated_pains["validated"],
            )

            learning_profile = self._build_product_learning_profile(topic)
            decision_signals["product_learning"] = {
                "records": learning_profile.get("records", 0),
                "score": learning_profile.get("score", 50),
                "confidence": learning_profile.get("confidence", 0.0),
                "adjustment": learning_profile.get("adjustment", 0),
            }
            scores = self._apply_product_learning_to_scores(scores, ideas, learning_profile)
            
            # Build historical learning memory with error handling
            try:
                historical_learning = self._build_historical_learning_memory(topic, run_id=run_id)
                decision_signals["historical_learning"] = {
                    "feedback_records": historical_learning.get("feedback_records", 0),
                    "finalized_runs": historical_learning.get("finalized_runs", 0),
                    "success_keywords": historical_learning.get("success_keywords", [])[:8],
                    "failure_keywords": historical_learning.get("failure_keywords", [])[:8],
                    "exploration_rate": historical_learning.get("exploration_rate", 0.0),
                }
                scores = self._apply_historical_learning_to_scores(
                    scores=scores,
                    ideas=ideas,
                    topic=topic,
                    run_id=run_id,
                    memory=historical_learning,
                )
                self._write_sanitized_json(run_id, "historical_learning.json", historical_learning)
            except Exception as e:
                # Fallback behavior if historical learning fails
                logger.error("Historical learning failed: {error}", error=DataSanitizer.sanitize_error_message(e))
                self._log_progress(
                    run_id,
                    f"Historical learning failed ({DataSanitizer.sanitize_error_message(e)[:100]}...), using default learning behavior"
                )
                decision_signals["historical_learning"] = {
                    "feedback_records": 0,
                    "finalized_runs": 0,
                    "success_keywords": [],
                    "failure_keywords": [],
                    "exploration_rate": float(self.settings.learning_exploration_rate),
                    "error": DataSanitizer.sanitize_error_message(e),
                }
                # Continue with original scores without historical learning adjustments
            scores, actionability_report = self._apply_actionability_to_scores(scores, ideas)
            self.manager.write_json(run_id, "idea_actionability.json", actionability_report)
            decision_signals["actionability"] = {
                "threshold": actionability_report.get("threshold"),
                "eligible_count": len(actionability_report.get("eligible") or []),
                "blocked_count": len(actionability_report.get("blocked") or []),
            }

            if scores:
                threshold = int(actionability_report.get("threshold", self.settings.idea_actionability_min_score))
                eligible_scores = [
                    score
                    for score in scores
                    if int(((score.signals or {}).get("actionability") or {}).get("score", 100)) >= threshold
                ]
                if eligible_scores:
                    top = max(eligible_scores, key=lambda item: item.score)
                else:
                    if self.settings.idea_actionability_require_eligible_top:
                        reason = (
                            "No actionable idea passed threshold "
                            f"{threshold}. Refine inputs and rerun with tighter pains/ICP."
                        )
                        self.manager.update_status(run_id, "aborted")
                        self.manager.write_artifact(run_id, "abort_reason.md", reason)
                        self._log_progress(run_id, "Abort: no actionable idea candidate")
                        decision_missing.append("No actionable idea candidate")
                        self._write_decision_file(
                            run_id,
                            "ABORT",
                            reason,
                            decision_signals,
                            decision_hypotheses,
                            decision_missing,
                        )
                        return RunResult(
                            run_id=run_id,
                            ideas=ideas,
                            scores=scores,
                            top_idea=IdeaScore(name="unknown", score=0, rationale=reason, risks=[], signals={}),
                            artifacts={},
                        )
                    top = max(scores, key=lambda item: item.score)
                    decision_missing.append("No idea met actionability threshold; selected best available candidate.")
                    # Log warning about fallback to non-actionable idea
                    logger.warning(
                        "Actionability fallback: No ideas met threshold {threshold}, "
                        "selected highest-scoring idea '{idea_name}' with score {score}. "
                        "This may indicate issues with idea generation or actionability assessment.",
                        threshold=threshold,
                        idea_name=top.name,
                        score=top.score
                    )
                    self._log_progress(
                        run_id,
                        f"Actionability fallback: No ideas met threshold {threshold}, "
                        f"selected '{top.name}' (score: {top.score}) as best available candidate. "
                        "Consider refining inputs or checking idea generation quality."
                    )
            else:
                top_item = analysis.get("top_idea") or {"name": "unknown", "score": 0, "rationale": ""}
                top = IdeaScore(
                    name=top_item.get("name", "unknown"),
                    score=int(top_item.get("score", 0)),
                    rationale=top_item.get("rationale", ""),
                    risks=top_item.get("risks", []),
                    signals=top_item.get("signals", {}),
                )
                top = self._apply_product_learning_to_top_idea(top, ideas, learning_profile)

            data_source_summary = {
                "pages": data_source["pages"],
                "pains": data_source["pains"],
                "competitors": data_source["competitors"],
                "seeds": data_source["seeds"],
            }
            decision_source = "real" if all(
                value == "real" for key, value in data_source_summary.items() if key != "seeds"
            ) else "fallback"
            if not (run_dir / "data_source.json").exists():
                self.manager.write_json(
                    run_id,
                    "data_source.json",
                    {"critical": data_source_summary, "decision": decision_source},
                )

            gate = PreRunGate(
                min_pages=self.settings.min_pages,
                min_pains=self.settings.min_pains,
                min_competitors=self.settings.min_competitors,
                min_signal_quality=signal_quality_threshold,
            )
            gate_result = gate.evaluate(
                pages,
                pains,
                competitors,
                top.name,
                data_source_summary,
                signal_quality=signal_quality,
            )
            if not gate_result.ok:
                reason = "PreRunGate failed after idea generation:\n- " + "\n- ".join(gate_result.reasons)
                self.manager.update_status(run_id, "aborted")
                self.manager.write_artifact(run_id, "abort_reason.md", reason)
                decision_missing.extend(gate_result.reasons)
                self._write_decision_file(
                    run_id,
                    "ABORT",
                    reason,
                    decision_signals,
                    decision_hypotheses,
                    decision_missing,
                )
                return RunResult(
                    run_id=run_id,
                    ideas=ideas,
                    scores=scores,
                    top_idea=top,
                    artifacts={},
                )
            if decision_source != "real":
                reason = "Critical data source fallback detected"
                self.manager.update_status(run_id, "aborted")
                self.manager.write_artifact(run_id, "abort_reason.md", reason)
                decision_missing.append("Fallback data source")
                self._write_decision_file(
                    run_id,
                    "ABORT",
                    reason,
                    decision_signals,
                    decision_hypotheses,
                    decision_missing,
                )
                return RunResult(run_id=run_id, ideas=ideas, scores=scores, top_idea=top, artifacts={})

            artifacts_ready = (
                self._stage_complete(run_id, "artifacts")
                and (run_dir / "prd.md").exists()
                and (run_dir / "tech_spec.md").exists()
                and (run_dir / "market_report.md").exists()
                and (run_dir / "brand_identity.json").exists()
                and (run_dir / "brand_direction.md").exists()
                and (run_dir / "logo.svg").exists()
            )
            if artifacts_ready:
                prd = self._load_text_artifact(run_dir / "prd.md") or ""
                tech_spec = self._load_text_artifact(run_dir / "tech_spec.md") or ""
                market_report = self._load_text_artifact(run_dir / "market_report.md") or ""
                brand_payload = self._load_json_artifact(run_dir / "brand_identity.json") or {}
                opportunities_payload = self._load_json_artifact(run_dir / "opportunities.json") or {}
                opportunities = opportunities_payload.get("items", opportunities)
            else:
                self.manager.begin_stage(run_id, "artifacts")
                market_report = self._build_market_report(topic, pains, competitors, pages, pages)
                prd = product.get("prd_markdown") or ""
                tech_spec = tech.get("tech_spec_markdown") or ""
                if not prd or "fallback" in prd.lower():
                    decision_missing.append("PRD fallback used")
                    prd = self._generate_prd(top, ideas, topic)
                    self._log_progress(run_id, "Artifacts: PRD fallback detected, generated local PRD.")
                if not tech_spec or "fallback" in tech_spec.lower():
                    decision_missing.append("Tech spec fallback used")
                    tech_spec = self._generate_tech_spec(top, topic)
                    self._log_progress(run_id, "Artifacts: Tech fallback detected, generated local tech spec.")

                brand_payload = brand if isinstance(brand, dict) else {}
                brand_payload = self._normalize_brand_payload(brand_payload, top.name)
                brand_name = brand_payload.get("project_name") or top.name
                self.manager.write_json(run_id, "brand_identity.json", brand_payload)
                self.manager.write_artifact(run_id, "brand_direction.md", self._build_brand_markdown(brand_payload))
                self._generate_logo_assets(run_id, brand_payload, top)

                repo_dir = Path(tech.get("repo_dir") or (self.settings.runs_dir / run_id / "repo_skeleton"))
                if not repo_dir.exists():
                    tools["repo"].run({"project_name": brand_name, "output_dir": str(repo_dir), "fast_mode": fast_mode})
                landing_dir = Path(growth.get("landing_dir") or (self.settings.runs_dir / run_id / "landing_page"))
                landing_payload = growth.get("landing_payload") or default_landing_payload(brand_name, fast_mode=fast_mode)
                landing_payload.setdefault("logo_src", "./logo.svg")
                landing_payload.setdefault("logo_alt", f"{brand_name} logo")
                landing_prompt = self._load_prompt("landing_copy") + "\n\nIdea:\n" + json.dumps(top.__dict__, indent=2)
                if not landing_dir.exists():
                    tools["landing"].run(
                        {
                            "product_name": brand_name,
                            "output_dir": str(landing_dir),
                            "template_dir": str(Path(__file__).resolve().parents[2] / "templates"),
                            "prompt": landing_prompt,
                            "payload": landing_payload,
                            "fast_mode": fast_mode,
                        }
                    )
                    # Record landing page creation for product metrics
                    if PRODUCT_METRICS:
                        PRODUCT_METRICS.record_landing_created(run_id)

                content_dir = Path(growth.get("content_dir") or (self.settings.runs_dir / run_id / "content_pack"))
                content_pack = growth.get("content_pack") or default_content_pack(brand_name, fast_mode=fast_mode)
                content_prompt = self._load_prompt("content_pack") + "\n\nIdea:\n" + json.dumps(top.__dict__, indent=2)
                if not content_dir.exists():
                    tools["content"].run(
                        {
                            "product_name": brand_name,
                            "output_dir": str(content_dir),
                            "prompt": content_prompt,
                            "content_pack": content_pack,
                            "fast_mode": fast_mode,
                        }
                    )

                opportunities = []
                for idea in ideas:
                    score = next((s for s in scores if s.name == idea.name), None)
                    if score:
                        opportunities.append({"idea": idea.__dict__, "score": score.__dict__})
                self.manager.write_json(run_id, "data_source.json", {"critical": data_source_summary, "decision": decision_source})
                self.manager.write_json(run_id, "opportunities.json", {"data_source": decision_source, "items": opportunities})
                self.manager.write_artifact(
                    run_id,
                    "top_idea.md",
                    f"Data source: {decision_source}\n\n# Top Idea\n\n{top.name}\n\nScore: {top.score}\n\n{top.rationale}\n",
                )
                self.manager.write_artifact(run_id, "market_report.md", f"Data source: {data_source_summary}\n\n{market_report}")
                self.manager.complete_stage(run_id, "artifacts")
                
                # Generate Validation Sprint output if execution profile requires it
                if profile.get("output_mode") == "execution_focused":
                    self._log_progress(run_id, "Generating Validation Sprint execution-focused output...")
                    validation_output = self._generate_validation_sprint_output(
                        run_id, topic, top, validated_texts, competitor_candidates
                    )
                    self._log_progress(run_id, f"Validation Sprint output generated: hypothesis, A/B test, landing, outreach messages, KPIs")
            _record_budget("artifacts")

            run_dir = self.settings.runs_dir / run_id
            prd_path = run_dir / "prd.md"
            tech_spec_path = run_dir / "tech_spec.md"
            if not prd_path.exists():
                self.manager.write_artifact(run_id, "prd.md", f"Data source: {decision_source}\n\n{prd}")
            if not tech_spec_path.exists():
                self.manager.write_artifact(run_id, "tech_spec.md", f"Data source: {decision_source}\n\n{tech_spec}")
            mvp_scope_path = run_dir / "mvp_scope.json"
            if not mvp_scope_path.exists():
                scope_payload = {
                    "run_id": run_id,
                    "topic": topic,
                    "top_idea": top.__dict__,
                    "stack": {
                        "frontend": self._extract_stack_from_tech(tech, tech_spec),
                        "backend": self._extract_stack_from_tech(tech, tech_spec),
                        "database": "SQLite",
                    },
                    "source": "pipeline",
                    "generated_at": datetime.utcnow().isoformat(),
                }
                self.manager.write_json(run_id, "mvp_scope.json", scope_payload)
            _record_budget("post_mvp_scope")

            checklist_path = run_dir / "launch_checklist.md"
            if not checklist_path.exists():
                checklist = self._build_launch_checklist(top.name)
                self.manager.write_artifact(run_id, "launch_checklist.md", f"Data source: {decision_source}\n\n{checklist}")

            pre_confidence = compute_pre_artifact_confidence(run_dir, settings=self.settings)
            final_confidence = compute_confidence(run_dir, settings=self.settings, status="COMPLETED")
            effective_confidence = max(pre_confidence["score"], final_confidence["score"])
            if (
                decision_source == "real"
                and gate_result.ok
                and effective_confidence < kill_threshold
            ):
                reason = (
                    f"Kill: confidence {effective_confidence} below threshold {kill_threshold} despite real data."
                )
                self.manager.update_status(run_id, "killed")
                self.manager.write_artifact(run_id, "kill_reason.md", reason)
                self._log_progress(run_id, "Kill: confidence below threshold")
                decision_signals["kill_confidence"] = effective_confidence
                decision_signals["kill_confidence_pre"] = pre_confidence["score"]
                decision_signals["kill_confidence_final"] = final_confidence["score"]
                decision_missing.append("Confidence below kill threshold")
                self._write_decision_file(
                    run_id,
                    "KILL",
                    reason,
                    decision_signals,
                    decision_hypotheses,
                    decision_missing,
                )
                return RunResult(
                    run_id=run_id,
                    ideas=ideas,
                    scores=scores,
                    top_idea=top,
                    artifacts={},
                )

            project_build_done = self._stage_complete(run_id, "project_build") and (run_dir / "project_build" / "vision_roadmap.md").exists()
            if not project_build_done:
                self.manager.begin_stage(run_id, "project_build")
                project_builder = ProjectBuilder(
                    project_dir=run_dir / "project_build",
                    topic=topic,
                    idea=top,
                    vision=product.get("vision") or "",
                    roadmap=product.get("roadmap") or [],
                    stack=self._extract_stack_from_tech(tech, tech_spec),
                    tech_spec=tech_spec,
                    opportunities=opportunities,
                )
                project_builder.build()
                self.manager.complete_stage(run_id, "project_build")

            landing_dir = run_dir / "landing_page"
            content_dir = run_dir / "content_pack"

            if self.settings.enable_progressive_cycles:
                mvp_done = self._stage_complete(run_id, "mvp_cycles") and (run_dir / "mvp_cycles").exists()
                if not mvp_done:
                    self.manager.begin_stage(run_id, "mvp_cycles")
                    try:
                        builder = MVPBuilder(self.settings)
                        self._log_progress(run_id, "MVP cycles: build/test running")
                        builder.build_from_run(
                            run_id,
                            max_fix_iter=5,
                            force=False,
                            frontend_style=self.settings.frontend_style,
                        )
                        self.manager.complete_stage(run_id, "mvp_cycles")
                    except MVPBuilderError as exc:
                        logger.warning("MVP builder failed for run {run_id}: {err}", run_id=DataSanitizer.sanitize_run_id(run_id), err=DataSanitizer.sanitize_error_message(exc))
                        self.manager.write_artifact(run_id, "mvp_build_error.md", str(exc))
                        self._log_progress(run_id, "MVP cycles: failed")

            if self.settings.enable_distribution:
                distribution_done = self._stage_complete(run_id, "distribution") and (run_dir / "distribution").exists()
                if not distribution_done:
                    self.manager.begin_stage(run_id, "distribution")
                    self._generate_distribution_assets(run_id, brand_payload, top, landing_dir, content_dir)
                    self._generate_outreach_assets(run_id, brand_payload, top)
                    self.manager.complete_stage(run_id, "distribution")

            n8n_done = self._stage_complete(run_id, "n8n") and (run_dir / "n8n" / "venture_factory.json").exists()
            if not n8n_done:
                self.manager.begin_stage(run_id, "n8n")
                self._export_n8n_workflow(run_id)
                self.manager.complete_stage(run_id, "n8n")

            secrets_done = self._stage_complete(run_id, "secrets_validation") and (run_dir / "secrets_validation.json").exists()
            if not secrets_done:
                self.manager.begin_stage(run_id, "secrets_validation")
                secrets_report = validate_secrets(self.settings)
                self.manager.write_json(run_id, "secrets_validation.json", secrets_report)
                if not secrets_report.get("ok"):
                    self._log_progress(run_id, "Secrets validation: missing credentials for enabled features")
                self.manager.complete_stage(run_id, "secrets_validation")

            if self.settings.enable_video_generation:
                video_done = self._stage_complete(run_id, "video_generation") and (run_dir / "distribution" / "videos").exists()
                if not video_done:
                    self.manager.begin_stage(run_id, "video_generation")
                    self._generate_videos(run_id, brand_payload, top)
                    self.manager.complete_stage(run_id, "video_generation")

            if self.settings.enable_publishing:
                publish_done = self._stage_complete(run_id, "publishing") and (run_dir / "distribution" / "publishing.json").exists()
                if not publish_done:
                    self.manager.begin_stage(run_id, "publishing")
                    self._publish_distribution(run_id)
                    self.manager.complete_stage(run_id, "publishing")

            if self.settings.enable_ads:
                ads_done = self._stage_complete(run_id, "ads") and (run_dir / "distribution" / "ads.json").exists()
                if not ads_done:
                    self.manager.begin_stage(run_id, "ads")
                    self._generate_ads(run_id, brand_payload, top)
                    self.manager.complete_stage(run_id, "ads")

            container_assets_done = (run_dir / "hosting" / "Dockerfile").exists() and (run_dir / "hosting" / "docker-compose.yml").exists()
            if not container_assets_done:
                self._ensure_container_assets(run_id)

            if self.settings.enable_hosting:
                hosting_done = self._stage_complete(run_id, "hosting") and (run_dir / "hosting" / "deploy_plan.json").exists()
                if not hosting_done:
                    self.manager.begin_stage(run_id, "hosting")
                    self._generate_hosting_assets(run_id, brand_payload)
                    self.manager.complete_stage(run_id, "hosting")

            if self.settings.enable_deploy:
                deploy_done = self._stage_complete(run_id, "deploy") and (run_dir / "deploy_log.md").exists()
                if not deploy_done:
                    self.manager.begin_stage(run_id, "deploy")
                    try:
                        deploy_run(self.settings, run_id)
                        # Record MVP publication for product metrics
                        if PRODUCT_METRICS:
                            PRODUCT_METRICS.record_mvp_published(run_id)
                    except Exception as exc:
                        self.manager.write_artifact(run_id, "deploy_error.md", str(exc))
                    self.manager.complete_stage(run_id, "deploy")

            if self.settings.enable_app_packaging:
                packaging_done = self._stage_complete(run_id, "app_packaging") and (run_dir / "app_package.zip").exists()
                if not packaging_done:
                    self.manager.begin_stage(run_id, "app_packaging")
                    self._package_app(run_id)
                    self.manager.complete_stage(run_id, "app_packaging")

            secrets_guard_done = self._stage_complete(run_id, "secrets_guard") and (run_dir / "secrets_guard.json").exists()
            if not secrets_guard_done:
                self.manager.begin_stage(run_id, "secrets_guard")
                findings = self._scan_run_for_secrets(run_dir)
                self._write_secrets_guard(run_id, findings)
                if findings:
                    reason = "Secrets guard failed: potential secrets detected in run artifacts."
                    self.manager.update_status(run_id, "aborted")
                    self.manager.write_artifact(run_id, "abort_reason.md", reason)
                    self._log_progress(run_id, "Abort: secrets guard failed")
                    decision_missing.append("Secrets guard failed")
                    self._write_decision_file(
                        run_id,
                        "ABORT",
                        reason,
                        decision_signals,
                        decision_hypotheses,
                        decision_missing,
                    )
                    return RunResult(run_id=run_id, ideas=ideas, scores=scores, top_idea=top, artifacts={})
                self.manager.complete_stage(run_id, "secrets_guard")

            self.manager.update_status(run_id, "completed")
            logger.info("Run {run_id} completed", run_id=DataSanitizer.sanitize_run_id(run_id))
            self._log_progress(run_id, "Run completed")
            decision_hypotheses.extend(self._derive_hypotheses_from_pains(validated_pains["validated"]))
            reason = "Run completed with PASS and validated decision artifacts."
            self._write_decision_file(
                run_id,
                "PASS",
                reason,
                decision_signals,
                decision_hypotheses,
                decision_missing,
            )
            self._write_ship_summary(run_id)
            self.manager.complete_stage(run_id, "decision")
            _record_budget("decision")
            return RunResult(run_id=run_id, ideas=ideas, scores=scores, top_idea=top, artifacts={})
        except Exception as exc:
            self.manager.update_status(run_id, "failed")
            logger.exception("Run {run_id} failed: {err}", run_id=DataSanitizer.sanitize_run_id(run_id), err=DataSanitizer.sanitize_error_message(exc))
            self._log_progress(run_id, f"Run failed: {DataSanitizer.sanitize_error_message(exc)}")
            state = self.manager.get_state(run_id) or {}
            self._record_failure_report(
                run_id,
                status="failed",
                stage=str(state.get("stage") or "unknown"),
                reason=DataSanitizer.sanitize_error_message(exc),
                error_type=exc.__class__.__name__,
                retryable=False,
            )
            raise
        finally:
            try:
                final_status = (self.manager.get_run(run_id) or {}).get("status") or "unknown"
                self.manager.write_json(
                    run_id,
                    "run_budget.json",
                    {**_budget_snapshot("final"), "final_status": final_status},
                )
            except Exception:
                pass
            self.settings.max_sources = original_max_sources
            self.settings.stage_retry_attempts = original_stage_retry_attempts
            clear_log_context()

    def _log_progress(self, run_id: str, message: str) -> None:
        try:
            self.manager.append_log(run_id, message)
        except Exception:
            pass

    def _scan_run_for_secrets(self, run_dir: Path) -> list[dict]:
        ignore_dirs = {
            ".git",
            ".next",
            "node_modules",
            "dist",
            "build",
            ".cache",
            "__pycache__",
            ".venv",
            "venv",
            "archive.zip",
        }
        ignore_files = {
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
        }
        patterns = [
            ("openai_key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
            ("aws_key", re.compile(r"AKIA[0-9A-Z]{16}")),
            ("private_key", re.compile(r"-----BEGIN (?:RSA|EC|DSA|OPENSSH) PRIVATE KEY-----")),
            ("generic_api_key", re.compile(r"(?i)api[_-]?key\\s*[:=]\\s*['\\\"][^'\\\"]{8,}['\\\"]")),
            ("generic_secret", re.compile(r"(?i)secret\\s*[:=]\\s*['\\\"][^'\\\"]{8,}['\\\"]")),
            ("generic_password", re.compile(r"(?i)password\\s*[:=]\\s*['\\\"][^'\\\"]{6,}['\\\"]")),
            ("bearer_token", re.compile(r"(?i)bearer\\s+[A-Za-z0-9\\-_.]{12,}")),
        ]
        allow_markers = ("example", "placeholder", "your_", "YOUR_", "REPLACE_ME", "changeme")
        findings: list[dict] = []

        for root, dirs, files in os.walk(run_dir):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for filename in files:
                if filename in ignore_files:
                    continue
                path = Path(root) / filename
                try:
                    if path.stat().st_size > 512_000:
                        continue
                except OSError:
                    continue
                try:
                    content = path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                for line_no, line in enumerate(content.splitlines(), start=1):
                    lowered = line.lower()
                    if any(marker in lowered for marker in allow_markers):
                        continue
                    for label, pattern in patterns:
                        if pattern.search(line):
                            rel = path.relative_to(run_dir).as_posix()
                            findings.append(
                                {
                                    "file": rel,
                                    "line": line_no,
                                    "type": label,
                                }
                            )
                            break
        return findings

    def _write_secrets_guard(self, run_id: str, findings: list[dict]) -> None:
        payload = {
            "run_id": run_id,
            "checked_at": datetime.utcnow().isoformat(),
            "findings": findings,
        }
        self.manager.write_json(run_id, "secrets_guard.json", payload)
        if findings:
            lines = [
                "# Secrets Guard",
                "",
                "Status: FAILED (potential secrets detected)",
                "",
                "## Findings",
            ]
            for item in findings:
                lines.append(f"- {item.get('file')}:{item.get('line')} ({item.get('type')})")
        else:
            lines = [
                "# Secrets Guard",
                "",
                "Status: OK (no secrets detected)",
            ]
        self.manager.write_artifact(run_id, "secrets_guard.md", "\n".join(lines).rstrip() + "\n")

    def _package_app(self, run_id: str) -> None:
        run_dir = self.settings.runs_dir / run_id
        targets = [item.strip() for item in self.settings.app_package_targets.split(",") if item.strip()]
        package_path = run_dir / "app_package.zip"
        manifest_path = run_dir / "app_package_manifest.json"
        included: list[str] = []
        missing: list[str] = []
        with ZipFile(package_path, "w", compression=ZIP_DEFLATED) as zf:
            for target in targets:
                target_path = run_dir / target
                if not target_path.exists():
                    missing.append(target)
                    continue
                if target_path.is_dir():
                    for file_path in target_path.rglob("*"):
                        if file_path.is_file():
                            arcname = file_path.relative_to(run_dir).as_posix()
                            zf.write(file_path, arcname)
                            included.append(arcname)
                else:
                    arcname = target_path.relative_to(run_dir).as_posix()
                    zf.write(target_path, arcname)
                    included.append(arcname)
        manifest = {
            "run_id": run_id,
            "created_at": datetime.utcnow().isoformat(),
            "targets": targets,
            "included": sorted(set(included)),
            "missing": sorted(set(missing)),
            "package": "app_package.zip",
        }
        self.manager.write_json(run_id, "app_package_manifest.json", manifest)

    def _ensure_container_assets(self, run_id: str) -> None:
        run_dir = self.settings.runs_dir / run_id
        hosting_dir = run_dir / "hosting"
        hosting_dir.mkdir(parents=True, exist_ok=True)
        dockerfile_path = hosting_dir / "Dockerfile"
        compose_path = hosting_dir / "docker-compose.yml"
        if not dockerfile_path.exists():
            dockerfile = (
                "FROM node:20-alpine\n"
                "WORKDIR /app\n"
                "COPY mvp_repo/package.json mvp_repo/package-lock.json* ./\n"
                "RUN npm install\n"
                "COPY mvp_repo ./\n"
                "RUN npm run build\n"
                "EXPOSE 3000\n"
                "CMD [\"npm\", \"run\", \"start\", \"--\", \"-p\", \"3000\"]\n"
            )
            self.manager.write_artifact(run_id, "hosting/Dockerfile", dockerfile)
        if not compose_path.exists():
            compose = (
                "services:\n"
                "  app:\n"
                "    build:\n"
                "      context: ..\n"
                "      dockerfile: hosting/Dockerfile\n"
                "    ports:\n"
                "      - \"3000:3000\"\n"
            )
            self.manager.write_artifact(run_id, "hosting/docker-compose.yml", compose)

    def _export_n8n_workflow(self, run_id: str) -> None:
        run_dir = self.settings.runs_dir / run_id
        src = Path(__file__).resolve().parents[2] / "n8n" / "workflows" / "venture_factory.json"
        if not src.exists():
            self.manager.write_artifact(run_id, "n8n_export_error.md", "n8n workflow not found.")
            return
        dest_dir = run_dir / "n8n"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "venture_factory.json"
        try:
            payload = json.loads(src.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        api_url = f"http://{self.settings.api_host}:{self.settings.api_port}/run"
        if isinstance(payload.get("nodes"), list):
            for node in payload["nodes"]:
                if node.get("name") == "Trigger Run" and isinstance(node.get("parameters"), dict):
                    node["parameters"]["url"] = api_url
                    if self.settings.api_key:
                        node["parameters"]["headerParametersJson"] = json.dumps({"X-API-Key": self.settings.api_key})
        dest.write_text(json.dumps(payload or {}, indent=2), encoding="utf-8")
        readme = (
            "# n8n Workflow Export\n\n"
            "Import `venture_factory.json` into n8n to trigger the Asmblr API.\n"
            f"- Trigger URL prewired to: {api_url}\n"
            "- If API auth is enabled, the `X-API-Key` header is included in the HTTP Request node.\n"
        )
        self.manager.write_artifact(run_id, "n8n/README.md", readme)

    def _write_ship_summary(self, run_id: str) -> None:
        run = self.manager.get_run(run_id) or {}
        run_dir = Path(run.get("output_dir") or (self.settings.runs_dir / run_id))
        stage_artifacts = {
            "decision": ["decision.md", "data_source.json"],
            "market": [
                "raw_pages.json",
                "pages_deduped.json",
                "pains_structured.json",
                "pains_validated.json",
                "pain_clusters.json",
                "novelty_score.json",
                "signal_quality.json",
                "market_signal_score.json",
                "opportunities_structured.json",
            ],
            "idea": ["top_idea.md", "opportunities.json", "market_report.md"],
            "product": ["prd.md", "tech_spec.md", "mvp_scope.json"],
            "mvp": ["mvp_repo", "mvp_cycles", "mvp_build_summary.md", "build_info.json"],
            "distribution": ["landing_page", "content_pack", "distribution"],
            "hosting": ["hosting/deploy_plan.json"],
            "deploy": ["deploy_log.md", "deployed_url.txt"],
            "packaging": ["app_package.zip", "app_package_manifest.json"],
            "secrets": ["secrets_validation.json"],
            "secrets_guard": ["secrets_guard.json", "secrets_guard.md"],
            "failures": ["failure_report.json", "failure_report.md"],
            "n8n": ["n8n/venture_factory.json"],
        }
        lines = ["# Ship Summary", ""]
        lines.append(f"- Run ID: {run_id}")
        lines.append(f"- Status: {run.get('status', 'unknown')}")
        lines.append(f"- Topic: {run.get('topic', '')}")
        lines.append("")
        for stage, items in stage_artifacts.items():
            lines.append(f"## {stage.title()}")
            for item in items:
                target = run_dir / item
                exists = target.exists()
                label = "OK" if exists else "missing"
                lines.append(f"- {item}: {label}")
            lines.append("")
        summary = "\n".join(lines).rstrip() + "\n"
        self.manager.write_artifact(run_id, "ship_summary.md", summary)

    def _build_campaign_brief(self, run_id: str, brand: dict[str, Any], top: IdeaScore) -> dict[str, Any]:
        run_dir = self.settings.runs_dir / run_id
        idea_details: dict[str, Any] = {}
        opportunities_payload = self._load_json_artifact(run_dir / "opportunities.json") or {}
        for item in opportunities_payload.get("items", []):
            if not isinstance(item, dict):
                continue
            idea = item.get("idea") or {}
            score = item.get("score") or {}
            score_name = (score.get("name") or "").strip()
            idea_name = (idea.get("name") or "").strip()
            if top.name and (top.name == score_name or top.name == idea_name):
                idea_details = idea
                break
        if not idea_details and isinstance(opportunities_payload.get("items"), list) and len(opportunities_payload["items"]) == 1:
            candidate = opportunities_payload["items"][0]
            idea_details = candidate.get("idea") if isinstance(candidate, dict) else {}
        key_features = idea_details.get("key_features")
        if not isinstance(key_features, list):
            key_features = []
        brief = {
            "project_name": brand.get("project_name", top.name),
            "idea_name": top.name,
            "one_liner": idea_details.get("one_liner", ""),
            "target_user": idea_details.get("target_user", ""),
            "problem": idea_details.get("problem", ""),
            "solution": idea_details.get("solution", ""),
            "key_features": [str(item) for item in key_features if str(item).strip()],
            "brand_direction": brand.get("brand_direction", ""),
            "brand_keywords": brand.get("brand_keywords", []),
            "score": int(getattr(top, "score", 0) or 0),
            "rationale": getattr(top, "rationale", ""),
        }
        self.manager.write_json(run_id, "distribution/campaign_brief.json", brief)
        return brief

    def _campaign_angles(self, brief: dict[str, Any]) -> list[dict[str, str]]:
        problem = (brief.get("problem") or "manual planning").strip()
        solution = (brief.get("solution") or "a focused launch system").strip()
        target_user = (brief.get("target_user") or "lean teams").strip()
        features = [str(item).strip() for item in (brief.get("key_features") or []) if str(item).strip()]
        feature_text = ", ".join(features[:3]) if features else "scoring, scope and launch assets"
        return [
            {"title": "Pain-first", "subtitle": "Turn recurring pain into one clear next step.", "hook": f"{target_user} keep losing time because {problem}.", "cta": "Join early access"},
            {"title": "Outcome", "subtitle": "Go from signal to launch-ready output quickly.", "hook": f"We built this to solve {problem} with {solution}.", "cta": "Get the launch pack"},
            {"title": "Speed", "subtitle": "From research to assets in one workflow.", "hook": f"Ship faster with {feature_text}.", "cta": "See how it works"},
            {"title": "Clarity", "subtitle": "Focus only on what validates the idea.", "hook": f"Use {solution} to remove guesswork.", "cta": "View the MVP plan"},
            {"title": "Evidence", "subtitle": "Built from real signal analysis.", "hook": f"{target_user} can prioritize with practical signal scoring.", "cta": "Try the framework"},
            {"title": "Execution", "subtitle": "Planning and distribution stay aligned.", "hook": f"One system for scope, landing page, and campaign assets.", "cta": "Launch this week"},
        ]

    def _trim_text(self, value: str, max_chars: int) -> str:
        text = (value or "").strip()
        if len(text) <= max_chars:
            return text
        return text[: max(0, max_chars - 1)].rstrip() + "…"

    def _expand_posts_for_campaign(self, posts: dict[str, Any], brief: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.campaign_auto_expand_assets:
            return posts if isinstance(posts, dict) else {}
        product_name = brief.get("project_name") or brief.get("idea_name") or "Product"
        hashtags = [f"#{str(tag).strip().replace(' ', '')}" for tag in (brief.get("brand_keywords") or []) if str(tag).strip()]
        hashtags = hashtags[:4] or ["#startup", "#mvp", "#build"]
        target_total = max(2, int(self.settings.campaign_posts_target))
        if target_total % 2 != 0:
            target_total += 1
        target_per_platform = max(1, target_total // 2)
        normalized: dict[str, list[dict[str, Any]]] = {"x": [], "linkedin": []}
        for platform in ("x", "linkedin"):
            variants = posts.get(platform)
            if not isinstance(variants, list):
                variants = []
            cleaned = [item for item in variants if isinstance(item, dict)]
            normalized[platform] = cleaned[:target_per_platform]
        angles = self._campaign_angles(brief)
        for platform in ("x", "linkedin"):
            while len(normalized[platform]) < target_per_platform:
                idx = len(normalized[platform])
                angle = angles[idx % len(angles)]
                if platform == "x":
                    text = self._trim_text(f"{product_name}: {angle['hook']} {angle['cta']}.", 280)
                else:
                    text = self._trim_text(
                        f"{product_name} helps {brief.get('target_user') or 'operators'}: {angle['hook']} "
                        f"The goal is pragmatic validation, not vanity output. {angle['cta']}.",
                        600,
                    )
                normalized[platform].append(
                    {
                        "text": text,
                        "hashtags": hashtags,
                        "cta": angle["cta"],
                        "image_title": f"{product_name} - {angle['title']}",
                        "image_subtitle": angle["subtitle"],
                    }
                )
        return normalized

    def _expand_outreach_for_campaign(self, outreach: dict[str, Any], brief: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.campaign_auto_expand_assets:
            return outreach if isinstance(outreach, dict) else {}
        product_name = brief.get("project_name") or brief.get("idea_name") or "Product"
        target_total = max(2, int(self.settings.campaign_outreach_target))
        per_channel = max(1, target_total // 2)
        email_seq = outreach.get("email_sequence")
        dm_seq = outreach.get("dm_sequence")
        emails = [item for item in (email_seq if isinstance(email_seq, list) else []) if isinstance(item, dict)]
        dms = [item for item in (dm_seq if isinstance(dm_seq, list) else []) if isinstance(item, dict)]
        angles = self._campaign_angles(brief)
        while len(emails) < per_channel:
            angle = angles[len(emails) % len(angles)]
            emails.append(
                {
                    "subject": self._trim_text(f"{product_name}: quick validation feedback?", 110),
                    "body": self._trim_text(
                        f"Hi, we built {product_name} for {brief.get('target_user') or 'early teams'}. "
                        f"{angle['hook']} Could I get 5 minutes of direct feedback?",
                        500,
                    ),
                }
            )
        while len(dms) < per_channel:
            angle = angles[len(dms) % len(angles)]
            dms.append(
                {
                    "platform": "linkedin" if len(dms) % 2 == 0 else "x",
                    "body": self._trim_text(
                        f"Working on {product_name}. {angle['hook']} Open to a quick opinion?",
                        280,
                    ),
                }
            )
        return {"email_sequence": emails[:per_channel], "dm_sequence": dms[:per_channel]}

    def _expand_videos_for_campaign(self, videos_payload: dict[str, Any], brief: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.campaign_auto_expand_assets:
            return videos_payload if isinstance(videos_payload, dict) else {}
        product_name = brief.get("project_name") or brief.get("idea_name") or "Product"
        target_total = max(1, int(self.settings.campaign_videos_target))
        raw_videos = videos_payload.get("videos")
        videos = [item for item in (raw_videos if isinstance(raw_videos, list) else []) if isinstance(item, dict)]
        angles = self._campaign_angles(brief)
        while len(videos) < target_total:
            angle = angles[len(videos) % len(angles)]
            videos.append(
                {
                    "title": f"{product_name} - {angle['title']}",
                    "hook": angle["hook"],
                    "storyboard": ["Show the pain context.", "Reveal focused MVP and campaign assets."],
                    "on_screen_text": [angle["title"], angle["subtitle"]],
                    "voiceover": self._trim_text(f"{product_name}: {angle['hook']} {angle['cta']}.", 220),
                    "duration_s": 15,
                    "style": "clean, bold, product UI",
                    "prompt": f"Short vertical ad, {angle['subtitle']}, modern product UI, 9:16.",
                }
            )
        return {"videos": videos[:target_total]}

    def _expand_ads_for_campaign(self, ads_payload: dict[str, Any], brief: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.campaign_auto_expand_assets:
            return ads_payload if isinstance(ads_payload, dict) else {}
        product_name = brief.get("project_name") or brief.get("idea_name") or "Product"
        target_total = max(3, int(self.settings.campaign_ads_target))
        if target_total % 3 != 0:
            target_total += 3 - (target_total % 3)
        per_platform = max(1, target_total // 3)
        angles = self._campaign_angles(brief)
        google_ads = [item for item in (ads_payload.get("google_ads") or []) if isinstance(item, dict)]
        meta_ads = [item for item in (ads_payload.get("meta_ads") or []) if isinstance(item, dict)]
        tiktok_ads = [item for item in (ads_payload.get("tiktok_ads") or []) if isinstance(item, dict)]
        while len(google_ads) < per_platform:
            angle = angles[len(google_ads) % len(angles)]
            google_ads.append(
                {
                    "headline": self._trim_text(f"{product_name}: {angle['title']}", 30),
                    "description": self._trim_text(angle["hook"], 90),
                    "final_url": "",
                }
            )
        while len(meta_ads) < per_platform:
            angle = angles[len(meta_ads) % len(angles)]
            meta_ads.append(
                {
                    "primary_text": self._trim_text(f"{product_name}. {angle['hook']}", 140),
                    "headline": self._trim_text(angle["title"], 40),
                    "description": self._trim_text(angle["subtitle"], 80),
                    "call_to_action": "LEARN_MORE",
                    "landing_url": "",
                }
            )
        while len(tiktok_ads) < per_platform:
            angle = angles[len(tiktok_ads) % len(angles)]
            tiktok_ads.append(
                {
                    "caption": self._trim_text(f"{product_name}: {angle['hook']}", 150),
                    "call_to_action": "Learn More",
                    "landing_url": "",
                }
            )
        ads_payload["google_ads"] = google_ads[:per_platform]
        ads_payload["meta_ads"] = meta_ads[:per_platform]
        ads_payload["tiktok_ads"] = tiktok_ads[:per_platform]
        ads_payload.setdefault("budget_per_platform_usd", self.settings.ads_budget_usd)
        ads_payload.setdefault(
            "campaign_strategy",
            {
                "goal": "Drive early access signups",
                "funnel_stage": "Top of funnel",
                "audience_hypothesis": f"{brief.get('target_user') or 'Founders validating MVPs'}",
                "creative_angle": "Pragmatic validation and fast launch execution",
                "success_metrics": ["CTR", "landing page signups"],
            },
        )
        ads_payload.setdefault(
            "targeting",
            {
                "countries": [c.strip() for c in self.settings.ads_countries.split(",") if c.strip()],
                "language": self.settings.ads_language,
                "audience": self.settings.ads_audience,
                "interests": [i.strip() for i in self.settings.ads_interests.split(",") if i.strip()],
            },
        )
        return ads_payload

    def _write_campaign_asset_manifest(self, run_id: str) -> None:
        run_dir = self.settings.runs_dir / run_id
        dist_dir = run_dir / "distribution"
        posts_payload = self._load_json_artifact(dist_dir / "posts.json") or {}
        outreach_payload = self._load_json_artifact(dist_dir / "outreach.json") or {}
        videos_payload = self._load_json_artifact(dist_dir / "video_prompts.json") or {}
        ads_payload = self._load_json_artifact(dist_dir / "ads.json") or {}
        posts_count = sum(len(items) for items in posts_payload.values() if isinstance(items, list))
        outreach_count = len(outreach_payload.get("email_sequence") or []) + len(outreach_payload.get("dm_sequence") or [])
        videos_count = len(videos_payload.get("videos") or [])
        ads_count = len(ads_payload.get("google_ads") or []) + len(ads_payload.get("meta_ads") or []) + len(ads_payload.get("tiktok_ads") or [])
        manifest = {
            "target_assets": int(self.settings.campaign_target_assets),
            "counts": {
                "posts": posts_count,
                "outreach": outreach_count,
                "videos": videos_count,
                "ads": ads_count,
                "total": posts_count + outreach_count + videos_count + ads_count,
            },
            "targets": {
                "posts": int(self.settings.campaign_posts_target),
                "outreach": int(self.settings.campaign_outreach_target),
                "videos": int(self.settings.campaign_videos_target),
                "ads": int(self.settings.campaign_ads_target),
            },
            "artifacts": {
                "brand_identity": (run_dir / "brand_identity.json").exists(),
                "logo": (run_dir / "logo.svg").exists(),
                "landing_page": (run_dir / "landing_page" / "index.html").exists(),
                "mvp_repo": (run_dir / "mvp_repo").exists(),
                "campaign_brief": (dist_dir / "campaign_brief.json").exists(),
            },
        }
        self.manager.write_json(run_id, "distribution/asset_manifest.json", manifest)

    def _generate_distribution_assets(
        self,
        run_id: str,
        brand: dict[str, Any],
        top: IdeaScore,
        landing_dir: Path,
        content_dir: Path,
    ) -> None:
        brief = self._build_campaign_brief(run_id, brand, top)
        run_dir = self.settings.runs_dir / run_id
        dist_dir = run_dir / "distribution"
        dist_dir.mkdir(parents=True, exist_ok=True)
        prompt = self._load_prompt("social_posts")
        payload = dict(brief)

        posts = {}
        if self.general_llm.available():
            try:
                prompt_full = prompt + "\n\nContext:\n" + json.dumps(payload, indent=2)
                posts = self.general_llm.generate_json(prompt_full)
            except Exception:
                posts = {}

        if not posts:
            product_name = brand.get("project_name", top.name)
            posts = {
                "x": [
                    {
                        "text": f"New: {product_name}. We built a focused MVP workflow for fast validation. Join early access.",
                        "hashtags": ["#startup", "#mvp", "#build"],
                        "cta": "Join early access",
                        "image_title": f"{product_name} MVP",
                        "image_subtitle": "Validate faster with a clear scope.",
                    },
                    {
                        "text": f"{product_name} turns market pains into a launch-ready MVP plan. Feedback welcome.",
                        "hashtags": ["#product", "#founders"],
                        "cta": "Get the launch pack",
                        "image_title": "Launch-ready MVP",
                        "image_subtitle": "Scope, landing, content in one run.",
                    },
                ],
                "linkedin": [
                    {
                        "text": f"We're sharing {product_name}, a lean MVP launch workflow for early teams. If you're validating a new idea, we'd love feedback.",
                        "hashtags": ["#product", "#mvp", "#startup"],
                        "cta": "Request early access",
                        "image_title": f"{product_name} Launch Pack",
                        "image_subtitle": "From pains to a testable MVP.",
                    },
                    {
                        "text": f"Shipping faster starts with clarity. {product_name} distills pains into a focused MVP plan and launch assets.",
                        "hashtags": ["#founder", "#productstrategy"],
                        "cta": "See the MVP plan",
                        "image_title": "Clarity for MVPs",
                        "image_subtitle": "Scope, landing, and content.",
                    },
                ],
            }

        posts = self._expand_posts_for_campaign(posts, brief)
        images_dir = dist_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        palette = brand.get("logo_palette") or [item.get("hex") for item in brand.get("color_palette", [])]
        landing_url = self._build_public_url(brand)
        try:
            if self.settings.offline_creation and self.settings.enable_local_social_images:
                from app.tools.media import generate_diffusion_image, build_social_prompt
                import torch

                device = self.settings.logo_device
                if device.startswith("cuda") and not torch.cuda.is_available():
                    device = "cpu"
                seed = None if self.settings.social_image_seed == 0 else self.settings.social_image_seed

                for platform, variants in posts.items():
                    for idx, item in enumerate(variants, start=1):
                        title = item.get("image_title", "")
                        subtitle = item.get("image_subtitle", "")
                        prompt = build_social_prompt(title, subtitle, brand.get("brand_keywords", []))
                        filename = f"{platform}_{idx}.png"
                        generate_diffusion_image(
                            output_path=images_dir / filename,
                            prompt=prompt,
                            model_id=self.settings.social_image_model_id,
                            size=self.settings.social_image_size,
                            steps=self.settings.social_image_steps,
                            guidance=self.settings.social_image_guidance,
                            seed=seed,
                            device=device,
                        )
                        item["image_path"] = f"distribution/images/{filename}"
                        if landing_url:
                            item["final_url"] = self._with_utm(landing_url, platform, "social", f"variant{idx}")
            else:
                from app.tools.social import generate_social_image

                for platform, variants in posts.items():
                    for idx, item in enumerate(variants, start=1):
                        title = item.get("image_title", "")
                        subtitle = item.get("image_subtitle", "")
                        size = (1200, 628) if platform == "x" else (1200, 627)
                        filename = f"{platform}_{idx}.png"
                        generate_social_image(images_dir / filename, title, subtitle, palette, size)
                        item["image_path"] = f"distribution/images/{filename}"
                        if landing_url:
                            item["final_url"] = self._with_utm(landing_url, platform, "social", f"variant{idx}")
        except Exception as exc:
            self.manager.write_artifact(run_id, "distribution_error.md", str(exc))

        self.manager.write_json(run_id, "distribution/posts.json", posts)
        md_lines = ["# Distribution Posts", ""]
        for platform, variants in posts.items():
            md_lines.append(f"## {platform.upper()}")
            for idx, item in enumerate(variants, start=1):
                md_lines.append(f"- Variant {idx}: {item.get('text', '')}")
                md_lines.append(f"  - Hashtags: {', '.join(item.get('hashtags', []))}")
                md_lines.append(f"  - CTA: {item.get('cta', '')}")
                md_lines.append(f"  - Image: {item.get('image_path', 'n/a')}")
            md_lines.append("")
        self.manager.write_artifact(run_id, "distribution/posts.md", "\n".join(md_lines).rstrip() + "\n")
        txt_lines = []
        for platform, variants in posts.items():
            for item in variants:
                txt_lines.append(f"[{platform}] {item.get('text', '')}")
        if txt_lines:
            self.manager.write_artifact(run_id, "distribution/posts.txt", "\n".join(txt_lines).rstrip() + "\n")
        self._write_campaign_asset_manifest(run_id)

    def _generate_outreach_assets(self, run_id: str, brand: dict[str, Any], top: IdeaScore) -> None:
        brief = self._build_campaign_brief(run_id, brand, top)
        run_dir = self.settings.runs_dir / run_id
        dist_dir = run_dir / "distribution"
        dist_dir.mkdir(parents=True, exist_ok=True)
        prompt = self._load_prompt("outreach_sequences")
        payload = dict(brief)

        outreach = {}
        if self.general_llm.available():
            try:
                prompt_full = prompt + "\n\nContext:\n" + json.dumps(payload, indent=2)
                outreach = self.general_llm.generate_json(prompt_full)
            except Exception:
                outreach = {}

        if not outreach:
            product_name = brand.get("project_name", top.name)
            outreach = {
                "email_sequence": [
                    {
                        "subject": f"Quick feedback on {product_name}?",
                        "body": f"Hey - we built {product_name} to help teams validate MVPs faster. Would you be open to 5 minutes of feedback?",
                    }
                ],
                "dm_sequence": [
                    {
                        "platform": "linkedin",
                        "body": f"Hi! We built {product_name} to turn pains into a testable MVP plan. Would love a quick take if you're open.",
                    }
                ],
            }
        outreach = self._expand_outreach_for_campaign(outreach, brief)

        landing_url = self._build_public_url(brand)
        if landing_url:
            utm = self._with_utm(landing_url, "outreach", "dm", "seq1")
            for item in outreach.get("email_sequence", []):
                if "link" not in item:
                    item["link"] = utm
            for item in outreach.get("dm_sequence", []):
                if "link" not in item:
                    item["link"] = utm

        self.manager.write_json(run_id, "distribution/outreach.json", outreach)
        md_lines = ["# Outreach Sequences", ""]
        for item in outreach.get("email_sequence", []):
            md_lines.append(f"- Email subject: {item.get('subject', '')}")
            md_lines.append(f"  - Body: {item.get('body', '')}")
            md_lines.append(f"  - Link: {item.get('link', '')}")
        for item in outreach.get("dm_sequence", []):
            md_lines.append(f"- DM ({item.get('platform', '')}): {item.get('body', '')}")
            md_lines.append(f"  - Link: {item.get('link', '')}")
        self.manager.write_artifact(run_id, "distribution/outreach.md", "\n".join(md_lines).rstrip() + "\n")
        self._write_campaign_asset_manifest(run_id)

    def _build_public_url(self, brand: dict[str, Any]) -> str:
        if self.settings.public_base_url:
            return self.settings.public_base_url.rstrip("/")
        domain = self.settings.public_base_domain.strip()
        if not domain:
            return ""
        project_name = (brand.get("project_name") or "").strip()
        slug = self._slugify(project_name) if project_name else ""
        if not slug:
            return ""
        template = self.settings.public_url_template or "https://{slug}.{domain}"
        return template.format(slug=slug, domain=domain).rstrip("/")

    def _slugify(self, value: str) -> str:
        sanitized = re.sub(r"[^a-z0-9-]", "-", value.lower())
        sanitized = re.sub(r"-+", "-", sanitized).strip("-")
        return sanitized

    def _with_utm(self, base_url: str, source: str, medium: str, campaign: str) -> str:
        if not base_url:
            return ""
        parts = urlsplit(base_url)
        query = dict([pair.split("=", 1) for pair in parts.query.split("&") if pair]) if parts.query else {}
        query.update(
            {
                "utm_source": source,
                "utm_medium": medium,
                "utm_campaign": campaign,
            }
        )
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))

    def _generate_videos(self, run_id: str, brand: dict[str, Any], top: IdeaScore) -> None:
        brief = self._build_campaign_brief(run_id, brand, top)
        run_dir = self.settings.runs_dir / run_id
        dist_dir = run_dir / "distribution"
        videos_dir = dist_dir / "videos"
        videos_dir.mkdir(parents=True, exist_ok=True)

        payload = dict(brief)

        prompt = self._load_prompt("video_prompts")
        videos_payload = {}
        if self.general_llm.available():
            try:
                prompt_full = prompt + "\n\nContext:\n" + json.dumps(payload, indent=2)
                videos_payload = self.general_llm.generate_json(prompt_full)
            except Exception:
                videos_payload = {}

        if not videos_payload:
            product_name = brand.get("project_name", top.name)
            videos_payload = {
                "videos": [
                    {
                        "title": f"{product_name} in 15s",
                        "hook": "Stop guessing your MVP scope.",
                        "storyboard": [
                            "Show messy idea board.",
                            "Show clean MVP scope card.",
                        ],
                        "on_screen_text": [
                            "Too many ideas",
                            "One clear MVP",
                        ],
                        "voiceover": f"{product_name} turns pains into a launch-ready MVP plan.",
                        "duration_s": 15,
                        "style": "clean, bold, product UI",
                        "prompt": "Minimal UI montage, clean typography, 9:16, high contrast, product screenshots.",
                    },
                    {
                        "title": "Launch pack demo",
                        "hook": "From pains to launch assets.",
                        "storyboard": [
                            "Pain statements animating in.",
                            "Landing page + content pack reveal.",
                        ],
                        "on_screen_text": [
                            "Pain → MVP",
                            "Landing + Content",
                        ],
                        "voiceover": "Get scope, landing, and content in one run.",
                        "duration_s": 18,
                        "style": "clean, bold, product UI",
                        "prompt": "Fast cuts, motion text, mock landing pages, 9:16.",
                    },
                ]
            }

        videos_payload = self._expand_videos_for_campaign(videos_payload, brief)
        self.manager.write_json(run_id, "distribution/video_prompts.json", videos_payload)
        self._write_campaign_asset_manifest(run_id)

        if self.settings.offline_creation:
            if self.settings.enable_local_video:
                try:
                    from app.tools.media import generate_diffusion_image, generate_video_from_image
                    import torch

                    device = self.settings.logo_device
                    if device.startswith("cuda") and not torch.cuda.is_available():
                        device = "cpu"
                    seed = None if self.settings.social_image_seed == 0 else self.settings.social_image_seed

                    for idx, video in enumerate(videos_payload.get("videos", []), start=1):
                        prompt = video.get("prompt") or video.get("hook") or "Minimal product UI promo"
                        image_path = videos_dir / f"video_{idx}_base.png"
                        generate_diffusion_image(
                            output_path=image_path,
                            prompt=prompt,
                            model_id=self.settings.social_image_model_id,
                            size=self.settings.social_image_size,
                            steps=self.settings.social_image_steps,
                            guidance=self.settings.social_image_guidance,
                            seed=seed,
                            device=device,
                        )
                        video_path = videos_dir / f"video_{idx}.mp4"
                        duration_s = int(video.get("duration_s") or 0)
                        fps = self.settings.local_video_fps
                        frames = duration_s * fps if duration_s > 0 else self.settings.local_video_frames
                        generate_video_from_image(
                            image_path=image_path,
                            output_path=video_path,
                            model_id=self.settings.local_video_model_id,
                            num_frames=frames,
                            fps=fps,
                            device=device,
                        )
                        video["file"] = f"distribution/videos/{video_path.name}"
                    self.manager.write_json(run_id, "distribution/video_prompts.json", videos_payload)
                except Exception as exc:
                    self.manager.write_artifact(run_id, "distribution/video_notice.md", f"Offline local video failed: {exc}")
            else:
                self.manager.write_artifact(
                    run_id,
                    "distribution/video_notice.md",
                    "Offline creation enabled; video prompts generated but no API calls were made.",
                )
            return

        if not self.settings.veo3_api_base or not self.settings.veo3_api_key:
            self.manager.write_artifact(
                run_id,
                "distribution/video_error.md",
                "Veo3 API not configured. Set VEO3_API_BASE and VEO3_API_KEY.",
            )
            return

        try:
            from app.tools.veo3 import Veo3Config, submit_video_job, wait_for_video_job, download_video

            config = Veo3Config(
                base_url=self.settings.veo3_api_base,
                api_key=self.settings.veo3_api_key,
                timeout_s=self.settings.veo3_timeout_s,
                poll_interval_s=self.settings.veo3_poll_interval_s,
                submit_path=self.settings.veo3_submit_path,
                status_path=self.settings.veo3_status_path,
                download_path=self.settings.veo3_download_path,
            )

            for idx, video in enumerate(videos_payload.get("videos", []), start=1):
                job_payload = {
                    "prompt": video.get("prompt") or video.get("hook") or "",
                    "title": video.get("title", f"video_{idx}"),
                    "duration_s": video.get("duration_s", 15),
                    "aspect_ratio": "9:16",
                    "style": video.get("style", "clean, bold, product UI"),
                }
                job_id = submit_video_job(config, job_payload)
                status = wait_for_video_job(config, job_id)
                content = download_video(config, job_id)
                video_path = videos_dir / f"video_{idx}.mp4"
                video_path.write_bytes(content)
                video["job_id"] = job_id
                video["status"] = status
                video["file"] = f"distribution/videos/{video_path.name}"
        except Exception as exc:
            self.manager.write_artifact(run_id, "distribution/video_error.md", str(exc))

    def _publish_distribution(self, run_id: str) -> None:
        run_dir = self.settings.runs_dir / run_id
        posts_path = run_dir / "distribution" / "posts.json"
        videos_path = run_dir / "distribution" / "video_prompts.json"
        result_path = run_dir / "distribution" / "publishing.json"

        if self.settings.offline_creation:
            result_path.write_text(json.dumps({"offline": True, "status": "skipped"}, indent=2), encoding="utf-8")
            return

        if not posts_path.exists():
            self.manager.write_artifact(run_id, "distribution/publishing_error.md", "Missing distribution/posts.json")
            return

        try:
            posts_payload = json.loads(posts_path.read_text(encoding="utf-8"))
        except Exception:
            self.manager.write_artifact(run_id, "distribution/publishing_error.md", "Invalid posts.json")
            return

        videos_payload = {}
        if videos_path.exists():
            try:
                videos_payload = json.loads(videos_path.read_text(encoding="utf-8"))
            except Exception:
                videos_payload = {}

        from app.tools.publish import PublishConfig, publish_linkedin, publish_x, publish_youtube, publish_instagram

        config = PublishConfig(
            linkedin_token=self.settings.linkedin_token,
            linkedin_author=self.settings.linkedin_author,
            x_bearer_token=self.settings.x_bearer_token,
            x_user_id=self.settings.x_user_id,
            youtube_token=self.settings.youtube_token,
            youtube_channel_id=self.settings.youtube_channel_id,
            instagram_token=self.settings.instagram_token,
            instagram_account_id=self.settings.instagram_account_id,
            dry_run=self.settings.publish_dry_run,
            timeout_s=self.settings.publish_timeout_s,
        )

        results: dict[str, list[dict[str, Any]]] = {"linkedin": [], "x": [], "youtube": [], "instagram": []}

        for item in posts_payload.get("x", []):
            text = item.get("text", "")
            media_path = item.get("image_path")
            if config.x_bearer_token and config.x_user_id:
                results["x"].append(publish_x(config, text, media_path))
            else:
                results["x"].append({"skipped": True, "reason": "missing X credentials", "text": text})

        for item in posts_payload.get("linkedin", []):
            text = item.get("text", "")
            media_path = item.get("image_path")
            if config.linkedin_token and config.linkedin_author:
                results["linkedin"].append(publish_linkedin(config, text, media_path))
            else:
                results["linkedin"].append({"skipped": True, "reason": "missing LinkedIn credentials", "text": text})

        videos_dir = run_dir / "distribution" / "videos"
        if videos_dir.exists():
            for idx, video in enumerate(videos_payload.get("videos", []), start=1):
                video_file = videos_dir / f"video_{idx}.mp4"
                if video_file.exists():
                    if config.youtube_token and config.youtube_channel_id:
                        results["youtube"].append(
                            publish_youtube(
                                config,
                                title=video.get("title", f"Video {idx}"),
                                description=video.get("voiceover", ""),
                                video_path=str(video_file),
                            )
                        )
                    else:
                        results["youtube"].append({"skipped": True, "reason": "missing YouTube credentials"})
                    if config.instagram_token and config.instagram_account_id:
                        results["instagram"].append(
                            publish_instagram(
                                config,
                                caption=video.get("voiceover", ""),
                                media_path=str(video_file),
                            )
                        )
                    else:
                        results["instagram"].append({"skipped": True, "reason": "missing Instagram credentials"})

        result_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    def _generate_ads(self, run_id: str, brand: dict[str, Any], top: IdeaScore) -> None:
        brief = self._build_campaign_brief(run_id, brand, top)
        run_dir = self.settings.runs_dir / run_id
        dist_dir = run_dir / "distribution"
        dist_dir.mkdir(parents=True, exist_ok=True)

        payload = dict(brief)

        prompt = self._load_prompt("ad_assets")
        ads_payload = {}
        if self.general_llm.available():
            try:
                prompt_full = prompt + "\n\nContext:\n" + json.dumps(payload, indent=2)
                ads_payload = self.general_llm.generate_json(prompt_full)
            except Exception:
                ads_payload = {}

        if not ads_payload:
            product_name = brand.get("project_name", top.name)
            ads_payload = {
                "budget_per_platform_usd": self.settings.ads_budget_usd,
                "campaign_strategy": {
                    "goal": "Drive early access signups",
                    "funnel_stage": "Top of funnel",
                    "audience_hypothesis": "Founders and small product teams validating MVPs",
                    "creative_angle": "Clarity and speed to MVP scope",
                    "success_metrics": ["CTR", "landing page signups"],
                },
                "targeting": {
                    "countries": [c.strip() for c in self.settings.ads_countries.split(",") if c.strip()],
                    "language": self.settings.ads_language,
                    "audience": self.settings.ads_audience,
                    "interests": [i.strip() for i in self.settings.ads_interests.split(",") if i.strip()],
                },
                "google_ads": [
                    {
                        "headline": f"{product_name} MVP Launch Pack",
                        "description": "Turn pains into a testable MVP plan. Join early access.",
                        "final_url": "",
                    },
                    {
                        "headline": "Validate Faster",
                        "description": f"{product_name} creates scope, landing, and content in one run.",
                        "final_url": "",
                    },
                ],
                "meta_ads": [
                    {
                        "primary_text": f"Stop guessing. {product_name} builds a clear MVP plan from real pains.",
                        "headline": "Launch-ready MVP plan",
                        "description": "Scope, landing, content included.",
                        "call_to_action": "LEARN_MORE",
                        "landing_url": "",
                    },
                    {
                        "primary_text": "Early teams need clarity. Get a focused MVP scope fast.",
                        "headline": f"{product_name} for founders",
                        "description": "Validate with a simple launch pack.",
                        "call_to_action": "SIGN_UP",
                        "landing_url": "",
                    },
                ],
                "tiktok_ads": [
                    {
                        "caption": f"{product_name} turns pains into MVP launch packs.",
                        "call_to_action": "Learn More",
                        "landing_url": "",
                    },
                    {
                        "caption": "Build less. Validate more. MVP scope in minutes.",
                        "call_to_action": "Learn More",
                        "landing_url": "",
                    },
                ],
            }

        ads_payload = self._expand_ads_for_campaign(ads_payload, brief)
        self.manager.write_json(run_id, "distribution/ads.json", ads_payload)
        landing_url = self._build_public_url(brand)
        if landing_url:
            for idx, item in enumerate(ads_payload.get("google_ads", []), start=1):
                if not item.get("final_url"):
                    item["final_url"] = self._with_utm(landing_url, "google", "ads", f"g{idx}")
            for idx, item in enumerate(ads_payload.get("meta_ads", []), start=1):
                if not item.get("landing_url"):
                    item["landing_url"] = self._with_utm(landing_url, "meta", "ads", f"m{idx}")
            for idx, item in enumerate(ads_payload.get("tiktok_ads", []), start=1):
                if not item.get("landing_url"):
                    item["landing_url"] = self._with_utm(landing_url, "tiktok", "ads", f"t{idx}")
            self.manager.write_json(run_id, "distribution/ads.json", ads_payload)
        self._write_campaign_asset_manifest(run_id)

        from app.tools.ads import AdsConfig, create_google_ads_campaign, create_meta_ads_campaign, create_tiktok_ads_campaign

        config = AdsConfig(
            google_customer_id=self.settings.google_ads_customer_id,
            google_dev_token=self.settings.google_ads_dev_token,
            google_client_id=self.settings.google_ads_client_id,
            google_client_secret=self.settings.google_ads_client_secret,
            google_refresh_token=self.settings.google_ads_refresh_token,
            meta_access_token=self.settings.meta_ads_access_token,
            meta_ad_account_id=self.settings.meta_ads_account_id,
            tiktok_access_token=self.settings.tiktok_ads_access_token,
            tiktok_ad_account_id=self.settings.tiktok_ads_account_id,
            dry_run=self.settings.ads_dry_run,
            timeout_s=self.settings.ads_timeout_s,
        )

        if self.settings.offline_creation:
            self.manager.write_json(run_id, "distribution/ads_publish.json", {"offline": True, "status": "skipped"})
            return

        results: dict[str, list[dict[str, Any]]] = {"google": [], "meta": [], "tiktok": []}
        per_platform_budget = ads_payload.get("budget_per_platform_usd", self.settings.ads_budget_usd)
        strategy = ads_payload.get("campaign_strategy", {})
        for item in ads_payload.get("google_ads", []):
            if config.google_customer_id and config.google_dev_token:
                results["google"].append(
                    create_google_ads_campaign(
                        config,
                        {"ad": item, "budget": per_platform_budget, "strategy": strategy, "targeting": ads_payload.get("targeting", {})},
                    )
                )
            else:
                results["google"].append({"skipped": True, "reason": "missing Google Ads credentials"})
        for item in ads_payload.get("meta_ads", []):
            if config.meta_access_token and config.meta_ad_account_id:
                results["meta"].append(
                    create_meta_ads_campaign(
                        config,
                        {"ad": item, "budget": per_platform_budget, "strategy": strategy, "targeting": ads_payload.get("targeting", {})},
                    )
                )
            else:
                results["meta"].append({"skipped": True, "reason": "missing Meta Ads credentials"})
        for item in ads_payload.get("tiktok_ads", []):
            if config.tiktok_access_token and config.tiktok_ad_account_id:
                results["tiktok"].append(
                    create_tiktok_ads_campaign(
                        config,
                        {"ad": item, "budget": per_platform_budget, "strategy": strategy, "targeting": ads_payload.get("targeting", {})},
                    )
                )
            else:
                results["tiktok"].append({"skipped": True, "reason": "missing TikTok Ads credentials"})

        self.manager.write_json(run_id, "distribution/ads_publish.json", results)

    def _generate_hosting_assets(self, run_id: str, brand: dict[str, Any]) -> None:
        run_dir = self.settings.runs_dir / run_id
        hosting_dir = run_dir / "hosting"
        hosting_dir.mkdir(parents=True, exist_ok=True)

        provider = self.settings.hosting_provider
        domain = self.settings.hosting_domain.strip()
        project_name = (brand.get("project_name") or "").strip()
        slug = self._slugify(project_name) if project_name else ""
        subdomain = ""
        if domain and slug:
            template = self.settings.hosting_subdomain_template or "{slug}.{domain}"
            subdomain = template.format(slug=slug, domain=domain)

        provider = (provider or "").strip().lower()
        provider_specs = {
            "aws_apprunner": {
                "label": "AWS App Runner",
                "deploy_command": "aws apprunner create-service --service-name $APP_NAME --source-configuration file://hosting/apprunner_source.json",
                "required_env": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION", "APP_NAME", "ECR_IMAGE_URI"],
                "notes": "Uses ECR image from ECR_IMAGE_URI. Requires AWS CLI + IAM + apprunner_source.json.",
            },
            "vercel": {
                "label": "Vercel",
                "deploy_command": "vercel deploy --prod",
                "required_env": ["VERCEL_TOKEN"],
                "notes": "Requires Vercel CLI installed and project configured.",
            },
            "netlify": {
                "label": "Netlify",
                "deploy_command": "netlify deploy --prod",
                "required_env": ["NETLIFY_AUTH_TOKEN"],
                "notes": "Requires Netlify CLI and site setup.",
            },
            "fly": {
                "label": "Fly.io",
                "deploy_command": "fly deploy",
                "required_env": ["FLY_API_TOKEN", "FLY_APP_NAME"],
                "notes": "Requires flyctl and app configured (uses FLY_APP_NAME).",
            },
            "render": {
                "label": "Render",
                "deploy_command": "render deploy --service $RENDER_SERVICE_ID",
                "required_env": ["RENDER_API_KEY", "RENDER_SERVICE_ID"],
                "notes": "Requires Render CLI and service id.",
            },
        }
        spec = provider_specs.get(provider)

        plan = {
            "provider": provider,
            "provider_label": spec.get("label") if spec else "unknown",
            "supported": bool(spec),
            "domain": domain,
            "subdomain": subdomain,
            "slug": slug,
            "project_name": project_name,
            "repo_path": "mvp_repo",
            "deploy_command": spec.get("deploy_command") if spec else "",
            "required_env": spec.get("required_env") if spec else [],
            "notes": spec.get("notes") if spec else "Unknown provider. Update HOSTING_PROVIDER.",
        }
        self.manager.write_json(run_id, "hosting/deploy_plan.json", plan)

        deploy_script = (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n\n"
            "PROVIDER=\"${HOSTING_PROVIDER:-" + provider + "}\"\n"
            "case \"$PROVIDER\" in\n"
            "  aws_apprunner)\n"
            "    : \"${APP_NAME:?APP_NAME required}\"\n"
            "    : \"${ECR_IMAGE_URI:?ECR_IMAGE_URI required}\"\n"
            "    aws apprunner create-service --service-name \"$APP_NAME\" --source-configuration file://hosting/apprunner_source.json\n"
            "    ;;\n"
            "  vercel)\n"
            "    vercel deploy --prod\n"
            "    ;;\n"
            "  netlify)\n"
            "    netlify deploy --prod\n"
            "    ;;\n"
            "  fly)\n"
            "    : \"${FLY_APP_NAME:?FLY_APP_NAME required}\"\n"
            "    fly deploy\n"
            "    ;;\n"
            "  render)\n"
            "    : \"${RENDER_SERVICE_ID:?RENDER_SERVICE_ID required}\"\n"
            "    render deploy --service \"$RENDER_SERVICE_ID\"\n"
            "    ;;\n"
            "  *)\n"
            "    echo \"Unsupported provider: $PROVIDER\" >&2\n"
            "    exit 1\n"
            "    ;;\n"
            "esac\n"
        )
        self.manager.write_artifact(run_id, "hosting/deploy.sh", deploy_script)

        apprunner_source = (
            "{\n"
            "  \"ImageRepository\": {\n"
            "    \"ImageIdentifier\": \"${ECR_IMAGE_URI}\",\n"
            "    \"ImageRepositoryType\": \"ECR\",\n"
            "    \"ImageConfiguration\": {\n"
            "      \"Port\": \"3000\"\n"
            "    }\n"
            "  },\n"
            "  \"AutoDeploymentsEnabled\": false\n"
            "}\n"
        )
        self.manager.write_artifact(run_id, "hosting/apprunner_source.json", apprunner_source)

        dockerfile = (
            "FROM node:20-alpine\n"
            "WORKDIR /app\n"
            "COPY mvp_repo/package.json mvp_repo/package-lock.json* ./\n"
            "RUN npm install\n"
            "COPY mvp_repo ./\n"
            "RUN npm run build\n"
            "EXPOSE 3000\n"
            "CMD [\"npm\", \"run\", \"start\", \"--\", \"-p\", \"3000\"]\n"
        )
        self.manager.write_artifact(run_id, "hosting/Dockerfile", dockerfile)

        compose = (
            "services:\n"
            "  app:\n"
            "    build:\n"
            "      context: ..\n"
            "      dockerfile: hosting/Dockerfile\n"
            "    ports:\n"
            "      - \"3000:3000\"\n"
        )
        self.manager.write_artifact(run_id, "hosting/docker-compose.yml", compose)

        guide = (
            "# Hosting Plan\n\n"
            "## Overview\n"
            "This run includes a Dockerfile, docker-compose.yml, and a deploy plan script.\n\n"
            "## Deploy Script\n"
            "- Use `hosting/deploy.sh` with HOSTING_PROVIDER set (aws_apprunner, vercel, netlify, fly, render).\n"
            "- Required env vars are listed in `hosting/deploy_plan.json`.\n\n"
            "## AWS App Runner (if selected)\n"
            "1. Build and push the image to ECR.\n"
            "2. Set APP_NAME and ECR_IMAGE_URI, then run `hosting/deploy.sh`.\n"
            "3. Add a custom domain for the service and map the subdomain.\n\n"
            "## Expected Subdomain\n"
            f"- {subdomain or 'set HOSTING_DOMAIN + project name'}\n"
        )
        self.manager.write_artifact(run_id, "hosting/README.md", guide)

    def _stage_complete(self, run_id: str, stage: str) -> bool:
        state = self.manager.get_state(run_id) or {}
        completed = state.get("completed") or []
        return stage in completed

    def _load_json_artifact(self, path: Path) -> Any | None:
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _load_text_artifact(self, path: Path) -> str | None:
        if not path.exists():
            return None
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return None

    def _load_signal_pages(self, run_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        raw_pages: list[dict[str, Any]] = []
        deduped_pages: list[dict[str, Any]] = []
        raw_payload = self._load_json_artifact(run_dir / "raw_pages.json") or {}
        deduped_payload = self._load_json_artifact(run_dir / "pages_deduped.json") or {}
        raw_pages = list(raw_payload.get("pages") or [])
        groups = deduped_payload.get("groups") or []
        deduped_pages = [group.get("canonical") for group in groups if group.get("canonical")]
        return raw_pages, deduped_pages

    def _seed_to_dict(self, seeds: SeedInputs) -> dict[str, Any]:
        return {
            "icp": seeds.icp,
            "pains": list(seeds.pains),
            "competitors": list(seeds.competitors),
            "context": seeds.context,
            "theme": seeds.theme,
        }

    def _seed_from_dict(self, payload: dict[str, Any] | None) -> SeedInputs:
        payload = payload or {}
        return SeedInputs(
            icp=payload.get("icp"),
            pains=list(payload.get("pains") or []),
            competitors=list(payload.get("competitors") or []),
            context=payload.get("context"),
            theme=payload.get("theme"),
        )

    def _build_market_report(
        self,
        topic: str,
        pains: list[str],
        competitors: list[dict[str, Any]],
        pages: list[dict[str, Any]],
        collected_pages: list[dict[str, Any]],
    ) -> str:
        citations = "\n".join([f"- {p['url']}" for p in pages if p.get("url")])
        collected = "\n".join([f"- {p['url']}" for p in collected_pages if p.get("url")])
        competitor_lines = "\n".join(
            [
                f"- {c.get('product_name', 'Unknown')} ({c.get('pricing', 'Unknown')})"
                for c in competitors
            ]
        )
        pains_md = "\n".join([f"- {p}" for p in pains[:10]])
        return (
            f"# Market Report\n\n"
            f"## Topic\n{topic}\n\n"
            f"## Pain Statements\n{pains_md}\n\n"
            f"## Competitors\n{competitor_lines or 'Unknown'}\n\n"
            f"## Pricing Snapshot\nUnknown (requires deeper scan)\n\n"
            f"## Differentiation\nFocus on local LLM workflows and launch-ready outputs.\n\n"
            f"## Sources (collected)\n{collected or 'Unknown'}\n\n"
            f"## Sources (LLM referenced)\n{citations or 'Unknown'}\n"
        )

    def _generate_prd(self, top: IdeaScore, ideas: list[Idea], topic: str) -> str:
        rag_context = self.rag.query("PRD guidance")
        prompt = self._load_prompt("prd_writer") + "\n\nIdea:\n" + json.dumps(top.__dict__, indent=2)
        if rag_context:
            prompt += "\n\nPlaybook context:\n" + rag_context
        if self.general_llm.available():
            try:
                return self.general_llm.generate(prompt)
            except Exception:
                pass
        return (
            f"# PRD\n\n"
            f"## Vision\nLaunch-ready pipeline for {topic}.\n\n"
            f"## Problem\nTeams lack structured idea scoring and launch assets.\n\n"
            f"## ICP\nOperators, founders, small product teams.\n\n"
            f"## JTBD\nTurn raw signals into a shippable MVP plan.\n\n"
            f"## User Stories\n- As a founder, I want to score ideas quickly.\n- As a PM, I need a PRD draft fast.\n\n"
            f"## MVP Scope\nSignal ingestion, scoring, PRD/landing generation.\n\n"
            f"## Success Metrics\nTime to PRD < 2 hours, idea score accuracy feedback.\n\n"
            f"## Risks\nLimited market data, scraping failures.\n"
        )

    def _generate_tech_spec(self, top: IdeaScore, topic: str) -> str:
        rag_context = self.rag.query("tech spec guidance")
        prompt = self._load_prompt("tech_spec_writer") + "\n\nIdea:\n" + json.dumps(top.__dict__, indent=2)
        if rag_context:
            prompt += "\n\nPlaybook context:\n" + rag_context
        if self.general_llm.available():
            try:
                return self.general_llm.generate(prompt)
            except Exception:
                pass
        return (
            "# Tech Spec\n\n"
            "## Architecture\nFastAPI + SQLite + background jobs.\n\n"
            "## Stack Options\n"
            "- Option A: FastAPI + SQLite + Streamlit UI.\n"
            "- Option B: Next.js frontend + FastAPI backend.\n\n"
            "## Endpoints\n- POST /run\n- GET /run/{id}\n- GET /run/{id}/artifact/{name}\n\n"
            "## DB Schema\nRuns(id, topic, status, created_at, updated_at, output_dir)\n\n"
            "## Deployment\nDocker compose with Ollama + app.\n"
        )

    def _build_launch_checklist(self, idea_name: str) -> str:
        return (
            f"# Launch Checklist - {idea_name}\n\n"
            "- Validate top 3 pains with 5 interviews\n"
            "- Finalize MVP scope and timelines\n"
            "- Publish landing page\n"
            "- Set up analytics (Plausible or PostHog)\n"
            "- Create feedback loop and iterate\n"
        )

    def _normalize_brand_payload(self, payload: dict[str, Any], default_name: str) -> dict[str, Any]:
        brand = dict(payload or {})
        name = (brand.get("project_name") or "").strip() or default_name
        brand["project_name"] = name
        if not brand.get("name_rationale"):
            brand["name_rationale"] = f"Derived from the top idea name '{name}' to keep clarity and focus."
        if not brand.get("brand_direction"):
            brand["brand_direction"] = (
                "Clean, pragmatic, early-stage builder aesthetic. Minimal shapes, strong contrast, "
                "and generous whitespace. Avoid visual noise; emphasize clarity and momentum."
            )
        if not isinstance(brand.get("brand_keywords"), list) or not brand["brand_keywords"]:
            brand["brand_keywords"] = ["pragmatic", "lean", "clear", "builder"]
        if not isinstance(brand.get("color_palette"), list) or not brand["color_palette"]:
            brand["color_palette"] = [
                {"name": "Ink", "hex": "#111111", "use": "primary text"},
                {"name": "Slate", "hex": "#6B7280", "use": "secondary text"},
                {"name": "Signal", "hex": "#22C55E", "use": "accent"},
                {"name": "Paper", "hex": "#F9FAFB", "use": "background"},
            ]
        if not isinstance(brand.get("typography"), dict):
            brand["typography"] = {"headline": "Space Grotesk", "body": "Inter"}
        else:
            brand["typography"].setdefault("headline", "Space Grotesk")
            brand["typography"].setdefault("body", "Inter")
        if not brand.get("logo_prompt"):
            brand["logo_prompt"] = "Minimal monogram logo, bold geometric shape, max 3 colors, flat vector style."
        if not isinstance(brand.get("logo_palette"), list) or not brand["logo_palette"]:
            palette = [item.get("hex") for item in brand.get("color_palette", []) if item.get("hex")]
            brand["logo_palette"] = palette[:3] if palette else ["#111111", "#22C55E", "#F9FAFB"]
        if not brand.get("logo_svg"):
            initial = (name[:1] or "A").upper()
            brand["logo_svg"] = (
                "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"120\" height=\"120\" "
                "viewBox=\"0 0 120 120\">"
                "<rect width=\"120\" height=\"120\" rx=\"18\" fill=\"#111111\"/>"
                f"<text x=\"60\" y=\"72\" font-size=\"56\" font-family=\"Arial, sans-serif\" "
                f"fill=\"#F9FAFB\" text-anchor=\"middle\">{initial}</text>"
                "</svg>"
            )
        if not brand.get("logo_description"):
            brand["logo_description"] = "Monogram in a rounded square for a clean, builder-first feel."
        if not isinstance(brand.get("usage_notes"), list) or not brand["usage_notes"]:
            brand["usage_notes"] = [
                "Use the monogram for favicon and app icon.",
                "Keep spacing generous around the mark.",
            ]
        return brand

    def _build_brand_markdown(self, brand: dict[str, Any]) -> str:
        palette = "\n".join(
            f"- {item.get('name', 'Color')}: {item.get('hex', '')} ({item.get('use', '')})"
            for item in brand.get("color_palette", [])
        ) or "- None"
        keywords = ", ".join(brand.get("brand_keywords", [])) or "None"
        usage_notes = "\n".join(f"- {note}" for note in brand.get("usage_notes", [])) or "- None"
        typography = brand.get("typography", {})
        return (
            f"# Brand Direction - {brand.get('project_name', 'Unnamed')}\n\n"
            f"## Name Rationale\n{brand.get('name_rationale', '')}\n\n"
            f"## Direction Artistique\n{brand.get('brand_direction', '')}\n\n"
            f"## Keywords\n{keywords}\n\n"
            f"## Color Palette\n{palette}\n\n"
            "## Typography\n"
            f"- Headline: {typography.get('headline', '')}\n"
            f"- Body: {typography.get('body', '')}\n\n"
            f"## Logo\n{brand.get('logo_description', '')}\n\n"
            f"## Usage Notes\n{usage_notes}\n"
        )

    def _build_logo_prompt(self, brand: dict[str, Any], top: IdeaScore) -> str:
        palette = brand.get("logo_palette") or [item.get("hex") for item in brand.get("color_palette", [])]
        palette = [c for c in palette if c][:3]
        palette_text = ", ".join(palette) if palette else "black, white, accent"
        keywords = ", ".join(brand.get("brand_keywords", [])) or "clean, minimal"
        return (
            "Minimal logo mark, flat vector style, no gradients, "
            f"max 3 colors ({palette_text}), "
            f"keywords: {keywords}, "
            f"project: {brand.get('project_name', top.name)}."
        )

    def _generate_logo_assets(self, run_id: str, brand: dict[str, Any], top: IdeaScore) -> None:
        run_dir = self.settings.runs_dir / run_id
        logo_prompt = brand.get("logo_prompt") or self._build_logo_prompt(brand, top)
        self.manager.write_artifact(run_id, "logo_prompt.txt", logo_prompt)

        if not self.settings.enable_logo_diffusion:
            self.manager.write_artifact(run_id, "logo.svg", brand.get("logo_svg", ""))
            return

        try:
            from app.tools.logo import generate_logo_png, quantize_png_three_colors, png_to_svg_three_colors
            import torch

            logo_png = run_dir / "logo.png"
            logo_quant = run_dir / "logo_3color.png"
            logo_svg = run_dir / "logo.svg"

            seed = None if self.settings.logo_seed == 0 else self.settings.logo_seed
            device = self.settings.logo_device
            if device.startswith("cuda") and not torch.cuda.is_available():
                device = "cpu"
            generate_logo_png(
                output_path=logo_png,
                prompt=logo_prompt,
                model_id=self.settings.logo_model_id,
                size=self.settings.logo_image_size,
                steps=self.settings.logo_steps,
                guidance=self.settings.logo_guidance,
                seed=seed,
                device=device,
            )
            quantize_png_three_colors(logo_png, logo_quant)
            png_to_svg_three_colors(logo_quant, logo_svg)
        except Exception as exc:
            self.manager.write_artifact(run_id, "logo_error.md", str(exc))
            self.manager.write_artifact(run_id, "logo.svg", brand.get("logo_svg", ""))

    def _extract_stack_from_tech(self, tech: dict[str, Any], tech_spec: str) -> str:
        stack_candidate = ""
        if isinstance(tech, dict):
            stack_candidate = tech.get("stack", "")
        if stack_candidate:
            return stack_candidate
        for line in tech_spec.splitlines():
            clean = line.strip()
            if not clean:
                continue
            if "stack" in clean.lower():
                if ":" in clean:
                    candidate = clean.split(":", 1)[1].strip()
                    if candidate:
                        return candidate
                return clean
        return "Next.js frontend + FastAPI backend + SQLite"

    def _describe_seed_hypotheses(self, seeds: SeedInputs) -> list[str]:
        hypotheses: list[str] = []
        if seeds.theme:
            hypotheses.append(f"Theme seed: {seeds.theme}")
        if seeds.icp:
            hypotheses.append(f"ICP seed: {seeds.icp}")
        if seeds.context:
            hypotheses.append(f"Context seed: {seeds.context}")
        for pain in seeds.pains:
            hypotheses.append(f"Seed pain: {pain}")
        for competitor in seeds.competitors:
            hypotheses.append(f"Seed competitor: {competitor}")
        return hypotheses

    def _write_seed_context(self, run_id: str, seeds: SeedInputs) -> None:
        if not seeds.has_any():
            return
        payload = {
            "theme": seeds.theme,
            "icp": seeds.icp,
            "pains": seeds.pains,
            "competitors": seeds.competitors,
            "context": seeds.context,
            "data_source": "seed",
        }
        self.manager.write_json(run_id, "seed_context.json", payload)

    def _validate_pains(self, pains: list[str]) -> dict[str, Any]:
        actor_keywords = ["team", "teams", "users", "founders", "operators", "business", "companies", "startup"]
        context_keywords = ["when", "while", "during", "after", "before", "in", "at", "within", "on"]
        difficulty_keywords = ["struggle", "hard", "problem", "need", "pain", "friction", "bottleneck", "difficult"]
        validated: list[dict[str, str]] = []
        rejected: list[dict[str, str]] = []
        seen: set[str] = set()
        count = 0
        for raw in pains:
            text = raw.strip()
            if not text or text in seen:
                continue
            seen.add(text)
            if self._is_generic_pain(text):
                rejected.append({"text": text, "reason": "generic assumption"})
                continue
            lower = text.lower()
            actor = next((kw for kw in actor_keywords if kw in lower), "")
            context = next((kw for kw in context_keywords if kw in lower), "")
            difficulty = next((kw for kw in difficulty_keywords if kw in lower), "")
            issues = []
            if not actor:
                issues.append("missing actor")
            if not context:
                issues.append("missing context")
            if not difficulty:
                issues.append("missing difficulty")
            if issues:
                rejected.append({"text": text, "reason": ", ".join(issues)})
                continue
            count += 1
            validated.append(
                {
                    "id": f"pain_{count}",
                    "text": text,
                    "actor": actor,
                    "context": context,
                    "difficulty": difficulty,
                }
            )
        return {"validated": validated, "rejected": rejected}

    def _derive_hypotheses_from_pains(self, validated_pains: list[dict[str, Any]]) -> list[str]:
        return [
            f"{pain['id']} validated: {pain['text']}"
            for pain in validated_pains[:3]
        ]

    def _derive_competitors_from_pages(self, pages: list[dict[str, Any]]) -> list[dict[str, str]]:
        competitors: list[dict[str, str]] = []
        seen: set[str] = set()
        for page in pages:
            url = page.get("url")
            if not url:
                continue
            domain = urlparse(url).netloc or url
            if domain in seen:
                continue
            seen.add(domain)
            competitors.append({"product_name": domain, "url": url})
        return competitors

    def _infer_icp_from_pains(self, validated_pains: list[dict[str, Any]]) -> str | None:
        for pain in validated_pains:
            actor = pain.get("actor")
            if actor:
                return actor
        return None

    def _match_pain_ids(self, text: str, validated_pains: list[dict[str, Any]]) -> list[str]:
        matches: list[str] = []
        if not text:
            return matches
        text_lower = text.lower()
        for pain in validated_pains:
            pain_text = pain["text"].lower()
            if pain_text in text_lower or text_lower in pain_text:
                matches.append(pain["id"])
        return matches

    def _build_traceable_ideas(
        self,
        idea_dicts: list[dict[str, Any]],
        validated_pains: list[dict[str, Any]],
        pages: list[dict[str, Any]],
        seeds: SeedInputs,
    ) -> list[Idea]:
        ideas: list[Idea] = []
        page_urls = [page.get("url") for page in pages if page.get("url")]
        unique_sources = list(dict.fromkeys(page_urls))
        for raw in idea_dicts:
            context_text = raw.get("problem", "") or raw.get("one_liner", "")
            pain_ids = raw.get("pain_ids") or self._match_pain_ids(context_text, validated_pains)
            if not pain_ids and validated_pains and context_text:
                pain_ids = [validated_pains[0]["id"]]
            if not pain_ids:
                continue
            idea_sources = raw.get("sources") or unique_sources[:3]
            if not idea_sources:
                idea_sources = ["inferred: collected market data"]
            hypotheses = raw.get("hypotheses") or self._describe_seed_hypotheses(seeds)
            if not hypotheses and validated_pains:
                hypotheses = [f"Assumes pain {validated_pains[0]['id']} aligns with market conversations."]
            idea = Idea(
                name=raw.get("name", "unknown"),
                one_liner=raw.get("one_liner", ""),
                target_user=raw.get("target_user", "unknown"),
                problem=raw.get("problem", ""),
                solution=raw.get("solution", ""),
                key_features=raw.get("key_features", []),
                pain_ids=pain_ids,
                sources=idea_sources,
                hypotheses=hypotheses,
            )
            if idea.pain_ids and idea.sources and idea.hypotheses:
                ideas.append(idea)
        return ideas

    def _idea_has_traceability_fields(self, idea_dict: dict[str, Any]) -> bool:
        if not isinstance(idea_dict, dict):
            return False
        if idea_dict.get("pain_ids"):
            return True
        text_fields = [
            idea_dict.get("problem"),
            idea_dict.get("one_liner"),
            idea_dict.get("solution"),
        ]
        if any(str(value or "").strip() for value in text_fields):
            return True
        return bool(idea_dict.get("key_features"))

    def _select_idea_dicts(
        self,
        analysis: dict[str, Any],
        research: dict[str, Any],
    ) -> list[dict[str, Any]]:
        analysis_ideas = [item for item in (analysis.get("ideas") or []) if isinstance(item, dict)]
        research_ideas = [item for item in (research.get("ideas") or []) if isinstance(item, dict)]
        if not analysis_ideas:
            return research_ideas
        if not research_ideas:
            return analysis_ideas

        research_by_name = {
            str(item.get("name", "")).strip().lower(): item
            for item in research_ideas
            if str(item.get("name", "")).strip()
        }

        merged: list[dict[str, Any]] = []
        sparse_count = 0
        for item in analysis_ideas:
            if self._idea_has_traceability_fields(item):
                merged.append(item)
                continue
            sparse_count += 1
            name_key = str(item.get("name", "")).strip().lower()
            if name_key and name_key in research_by_name:
                enriched = dict(research_by_name[name_key])
                enriched.update({k: v for k, v in item.items() if v not in (None, "", [], {})})
                merged.append(enriched)
            else:
                merged.append(item)

        # Root-cause fix: analysis can return name-only ideas; prefer research ideas when all are sparse.
        if sparse_count == len(analysis_ideas):
            return research_ideas
        return merged

    def _derive_ideas_from_structured_opportunities(
        self,
        opportunities: list[dict[str, Any]],
        validated_pains: list[dict[str, Any]],
        seeds: SeedInputs,
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        if not opportunities:
            return []
        pain_map = {str(p.get("id")): p for p in validated_pains if p.get("id")}
        idea_dicts: list[dict[str, Any]] = []
        for opportunity in opportunities[: max(1, limit)]:
            linked_pains = [str(pid) for pid in (opportunity.get("linked_pains") or []) if str(pid)]
            primary_pain = pain_map.get(linked_pains[0]) if linked_pains else None
            problem_text = str((primary_pain or {}).get("text") or opportunity.get("jtbd") or "").strip()
            target_user = str(
                opportunity.get("target_actor")
                or seeds.icp
                or self._infer_icp_from_pains(validated_pains)
                or "Early-stage teams"
            ).strip()
            name = str(opportunity.get("name") or "Signal-derived opportunity").strip()
            if not problem_text:
                continue
            source_urls = [u for u in (opportunity.get("source_urls") or []) if isinstance(u, str) and u.strip()]
            assumptions = [a for a in (opportunity.get("assumptions") or []) if isinstance(a, str) and a.strip()]
            idea_dicts.append(
                {
                    "name": name[:120],
                    "one_liner": f"Help {target_user.lower()} solve a repeated pain with a fast validation workflow.",
                    "target_user": target_user,
                    "problem": problem_text,
                    "solution": "Provide a focused MVP test workflow with clear validation steps and measurable outcomes.",
                    "key_features": [
                        "Pain-to-hypothesis mapping",
                        "Test plan and success criteria",
                        "Launch-ready landing and outreach starter kit",
                    ],
                    "pain_ids": linked_pains,
                    "sources": source_urls,
                    "hypotheses": assumptions,
                }
            )
        return idea_dicts

    def _score_pragmatic_potential(
        self,
        idea: Idea,
        validated_pains: list[dict[str, Any]],
    ) -> dict[str, Any]:
        pain_map = {str(item.get("id")): item for item in validated_pains if item.get("id")}
        linked = [pain_map[pid] for pid in (idea.pain_ids or []) if pid in pain_map]
        linked_count = len(linked)
        avg_intensity = (
            sum(int(item.get("intensity_signal", 0)) for item in linked) / linked_count if linked_count else 0.0
        )
        avg_frequency = (
            sum(int(item.get("frequency_signal", 0)) for item in linked) / linked_count if linked_count else 0.0
        )
        source_domains: set[str] = set()
        for raw_url in (idea.sources or []):
            if not isinstance(raw_url, str):
                continue
            url = raw_url.strip()
            if not url:
                continue
            try:
                domain = urlparse(url).netloc
            except Exception:
                domain = ""
            if domain:
                source_domains.add(domain)
        source_diversity = len(source_domains)
        has_test_markers = any(
            marker in " ".join(
                [idea.one_liner, idea.solution, " ".join(idea.key_features or [])]
            ).lower()
            for marker in ("test", "validate", "landing", "waitlist", "interview", "pilot", "trial", "signup")
        )
        icp_hint = (self.settings.primary_icp or "").lower()
        icp_fit = 1 if icp_hint and icp_hint in (idea.target_user or "").lower() else 0

        score = 0.0
        score += min(30.0, linked_count * 10.0)
        score += min(20.0, avg_intensity * 0.2)
        score += min(15.0, avg_frequency * 0.3)
        score += min(15.0, source_diversity * 5.0)
        score += 12.0 if has_test_markers else 0.0
        score += 8.0 if icp_fit else 0.0
        final = int(max(0, min(100, round(score))))
        return {
            "score": final,
            "linked_pains": linked_count,
            "avg_intensity": round(avg_intensity, 1),
            "avg_frequency": round(avg_frequency, 1),
            "source_diversity": source_diversity,
            "has_test_markers": has_test_markers,
            "icp_fit": bool(icp_fit),
        }

    def _apply_pragmatic_potential_to_scores(
        self,
        scores: list[IdeaScore],
        ideas: list[Idea],
        validated_pains: list[dict[str, Any]],
    ) -> list[IdeaScore]:
        if not scores or not ideas:
            return scores
        idea_map = {idea.name: idea for idea in ideas}
        adjusted: list[IdeaScore] = []
        for score in scores:
            idea = idea_map.get(score.name)
            if not idea:
                adjusted.append(score)
                continue
            potential = self._score_pragmatic_potential(idea, validated_pains)
            combined = int(round((0.55 * score.score) + (0.45 * int(potential["score"]))))
            signals = dict(score.signals or {})
            signals["pragmatic_potential"] = potential
            rationale = (
                f"{score.rationale} "
                f"(Pragmatic potential {potential['score']}/100 from signal evidence, combined score: {combined}.)"
            ).strip()
            adjusted.append(
                IdeaScore(
                    name=score.name,
                    score=max(0, min(100, combined)),
                    rationale=rationale,
                    risks=score.risks,
                    signals=signals,
                )
            )
        return adjusted

    def _text_missing_or_unknown(self, value: Any) -> bool:
        text = str(value or "").strip().lower()
        # Liste étendue de valeurs invalides pour meilleure validation
        invalid_values = {
            "", "unknown", "n/a", "none", "null", "tbd", "todo",
            "undefined", "missing", "not applicable", "na",
            "n.d.", "nd", "nil", "void", "not available", "-"
        }
        return text in invalid_values

    def _score_idea_actionability(self, idea: Idea) -> dict[str, Any]:
        score = 50
        signals: dict[str, Any] = {"issues": [], "strengths": []}
        generic_phrases = (
            "save time",
            "improve efficiency",
            "increase productivity",
            "streamline workflow",
            "all-in-one",
            "for everyone",
            "any business",
            "one-click",
            "revolutionary",
            "game-changing",
        )
        action_verbs = (
            "test",
            "validate",
            "launch",
            "ship",
            "interview",
            "outreach",
            "onboard",
            "measure",
            "deploy",
            "automate",
        )
        testability_markers = (
            "landing",
            "waitlist",
            "demo",
            "pilot",
            "trial",
            "signup",
            "email",
            "linkedin",
            "reddit",
            "ads",
            "7 day",
            "14 day",
            "week",
        )
        if self._text_missing_or_unknown(idea.target_user):
            score -= 18
            signals["issues"].append("target_user missing/unknown")
        else:
            score += 10
            signals["strengths"].append("target_user specified")
        if self._text_missing_or_unknown(idea.problem) or len(idea.problem.strip()) < 20:
            score -= 16
            signals["issues"].append("problem too vague")
        else:
            score += 10
            signals["strengths"].append("problem is concrete")
        if self._text_missing_or_unknown(idea.solution) or len(idea.solution.strip()) < 20:
            score -= 16
            signals["issues"].append("solution too vague")
        else:
            score += 10
            signals["strengths"].append("solution is concrete")

        features = [item.strip() for item in (idea.key_features or []) if str(item).strip()]
        if 2 <= len(features) <= 6:
            score += 10
            signals["strengths"].append("feature scope is focused")
        elif len(features) == 1:
            score += 4
            signals["issues"].append("feature scope too thin")
        elif len(features) == 0:
            score -= 12
            signals["issues"].append("key_features missing")
        else:
            score -= 6
            signals["issues"].append("feature scope too broad")

        text = " ".join(
            [
                idea.name,
                idea.one_liner,
                idea.target_user,
                idea.problem,
                idea.solution,
                " ".join(features),
            ]
        ).lower()

        generic_hits = [phrase for phrase in generic_phrases if phrase in text]
        if generic_hits:
            penalty = min(24, 6 * len(generic_hits))
            score -= penalty
            signals["issues"].append(f"generic messaging ({', '.join(generic_hits[:3])})")
        else:
            score += 4
            signals["strengths"].append("messaging not generic")

        action_hits = [verb for verb in action_verbs if verb in text]
        if action_hits:
            score += 8
            signals["strengths"].append("contains execution verbs")
        else:
            score -= 8
            signals["issues"].append("missing execution verbs")

        testability_hits = [token for token in testability_markers if token in text]
        if testability_hits:
            score += 12
            signals["strengths"].append("has testable GTM markers")
        else:
            score -= 10
            signals["issues"].append("no clear test channel/format")

        if any(ch.isdigit() for ch in text):
            score += 4
            signals["strengths"].append("includes measurable/time-bound detail")
        else:
            signals["issues"].append("missing measurable/time-bound detail")

        final_score = max(0, min(100, int(round(score))))
        signals["score"] = final_score
        signals["generic_hits"] = generic_hits
        signals["action_hits"] = action_hits
        signals["testability_hits"] = testability_hits
        return signals

    def _apply_actionability_to_scores(
        self,
        scores: list[IdeaScore],
        ideas: list[Idea],
    ) -> tuple[list[IdeaScore], dict[str, Any]]:
        if not scores:
            logger.warning("Actionability assessment: No scores provided, returning empty results")
            return scores, {"assessments": [], "eligible": [], "blocked": [], "threshold": self.settings.idea_actionability_min_score}

        adjust_cap = max(0, min(IDEA_ACTIONABILITY_ADJUSTMENT_MAX, int(self.settings.idea_actionability_adjustment_max)))
        threshold = max(0, min(100, int(self.settings.idea_actionability_min_score)))
        idea_map = {idea.name: idea for idea in ideas}
        assessments: list[dict[str, Any]] = []
        assessment_by_name: dict[str, dict[str, Any]] = {}
        for idea in ideas:
            item = self._score_idea_actionability(idea)
            payload = {"name": idea.name, **item}
            assessments.append(payload)
            assessment_by_name[idea.name] = payload

        adjusted_scores: list[IdeaScore] = []
        eligible: list[str] = []
        blocked: list[str] = []
        for score in scores:
            assessment = assessment_by_name.get(score.name)
            if not assessment:
                adjusted_scores.append(score)
                continue
            actionability_score = int(assessment.get("score", 0))
            delta = int(round(((actionability_score - 50) / 50.0) * adjust_cap))
            new_score = max(0, min(100, score.score + delta))
            signals = dict(score.signals or {})
            signals["actionability"] = {
                "score": actionability_score,
                "delta": delta,
                "threshold": threshold,
                "issues": assessment.get("issues", []),
                "strengths": assessment.get("strengths", []),
                "testability_hits": assessment.get("testability_hits", []),
            }
            risks = list(score.risks or [])
            rationale = score.rationale or ""
            rationale = (
                f"{rationale} (Actionability {actionability_score}/100, adjusted {delta:+d}.)".strip()
            )
            if actionability_score >= threshold:
                eligible.append(score.name)
            else:
                blocked.append(score.name)
                risks.append("Low actionability: idea remains generic or hard to test quickly.")
            adjusted_scores.append(
                IdeaScore(
                    name=score.name,
                    score=new_score,
                    rationale=rationale,
                    risks=risks,
                    signals=signals,
                )
            )

        report = {
            "threshold": threshold,
            "adjustment_cap": adjust_cap,
            "assessments": assessments,
            "eligible": eligible,
            "blocked": blocked,
        }
        
        # Log summary of actionability assessment - optimized with smart logger
        if len(assessments) > 0:
            avg_actionability = sum(a.get("score", 0) for a in assessments) / len(assessments)
            
            # Utiliser le smart logger si disponible
            if SMART_LOGGER_AVAILABLE:
                smart_logger = get_smart_logger()
                smart_logger.business(
                    LogLevel.MEDIUM,
                    "Actionability assessment completed",
                    {
                        "eligible_count": len(eligible),
                        "total_count": len(assessments),
                        "threshold": threshold,
                        "avg_score": round(avg_actionability, 1),
                        "blocked_count": len(blocked)
                    }
                )
            else:
                # Fallback vers loguru standard
                logger.info(
                    "Actionability assessment: {eligible}/{total} ideas passed (threshold: {threshold}, avg: {avg_score:.1f})",
                    eligible=len(eligible),
                    total=len(assessments),
                    threshold=threshold,
                    avg_score=avg_actionability
                )
            
            # Log détaillé seulement quand des idées sont bloquées.
            if blocked and len(blocked) > 0:
                if SMART_LOGGER_AVAILABLE:
                    smart_logger.debug(
                        LogCategory.BUSINESS,
                        f"{len(blocked)} ideas blocked by actionability threshold",
                        {"blocked_ideas": blocked[:5]}  # Limiter à 5 exemples
                    )
                else:
                    blocked_summary = f"{len(blocked)} ideas blocked"
                    logger.debug("Actionability blocked: {blocked_summary}", blocked_summary=blocked_summary)
        
        return adjusted_scores, report

    def _compute_market_signal_score(
        self,
        pages: list[dict[str, Any]],
        validated_pains: list[dict[str, Any]],
        settings: Settings,
    ) -> dict[str, Any]:
        source_ids = {
            (page.get("url") or page.get("source") or "").strip()
            for page in pages
            if page.get("url") or page.get("source")
        }
        domain_set = {
            urlparse(page.get("url", "")).netloc
            for page in pages
            if page.get("url")
        }
        distinct_pains = len({pain["text"].strip() for pain in validated_pains if pain.get("text")})
        counts = Counter(pain["text"].strip() for pain in validated_pains if pain.get("text"))
        repeated = sum(count - 1 for count in counts.values() if count > 1)
        repeat_score = min(1.0, repeated / max(1, settings.signal_repeat_target))
        components = [
            min(len(source_ids), settings.signal_sources_target) / max(1, settings.signal_sources_target),
            min(distinct_pains, settings.signal_pains_target) / max(1, settings.signal_pains_target),
            repeat_score,
            min(len(domain_set), settings.signal_domain_target) / max(1, settings.signal_domain_target),
        ]
        score_value = int(round(sum(components) / len(components) * 100))
        return {
            "score": max(0, min(100, score_value)),
            "sources_count": len(source_ids),
            "distinct_pains": distinct_pains,
            "repeat_score": repeat_score,
            "unique_domains": len(domain_set),
            "threshold": settings.market_signal_threshold,
        }

    def record_product_feedback(
        self,
        run_id: str,
        ctr_landing: float,
        signup_rate: float,
        activation_rate: float,
        visitors: int | None = None,
        signups: int | None = None,
        activated_users: int | None = None,
        window_days: int | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        run = self.manager.get_run(run_id)
        if not run:
            raise ValueError("Run not found")

        ctr_pct = self._normalize_rate_percent(ctr_landing, "ctr_landing")
        signup_pct = self._normalize_rate_percent(signup_rate, "signup_rate")
        activation_pct = self._normalize_rate_percent(activation_rate, "activation_rate")

        if visitors is not None and visitors < 0:
            raise ValueError("visitors must be >= 0")
        if signups is not None and signups < 0:
            raise ValueError("signups must be >= 0")
        if activated_users is not None and activated_users < 0:
            raise ValueError("activated_users must be >= 0")
        if window_days is not None and (window_days < 1 or window_days > 365):
            raise ValueError("window_days must be between 1 and 365")

        learning = self._compute_feedback_learning_score(
            ctr_pct=ctr_pct,
            signup_pct=signup_pct,
            activation_pct=activation_pct,
            visitors=visitors,
            signups=signups,
            activated_users=activated_users,
        )

        payload = {
            "run_id": run_id,
            "topic": run.get("topic", ""),
            "captured_at": datetime.utcnow().isoformat(),
            "window_days": window_days,
            "notes": (notes or "").strip()[:400],
            "metrics": {
                "ctr_landing_pct": ctr_pct,
                "signup_rate_pct": signup_pct,
                "activation_rate_pct": activation_pct,
                "visitors": visitors,
                "signups": signups,
                "activated_users": activated_users,
            },
            "learning_score": learning["learning_score"],
            "raw_score": learning["raw_score"],
            "confidence": learning["confidence"],
            "benchmarks": learning["benchmarks"],
        }
        self.manager.write_json(run_id, "post_launch_metrics.json", payload)
        self._append_feedback_record(payload)
        return payload

    def _normalize_rate_percent(self, value: float, field_name: str) -> float:
        value = float(value)
        if value < 0:
            raise ValueError(f"{field_name} must be >= 0")
        if value <= 1.0:
            value *= 100.0
        if value > 100.0:
            raise ValueError(f"{field_name} must be <= 100 (or <= 1.0 ratio)")
        return round(value, 4)

    def _compute_feedback_learning_score(
        self,
        ctr_pct: float,
        signup_pct: float,
        activation_pct: float,
        visitors: int | None,
        signups: int | None,
        activated_users: int | None,
    ) -> dict[str, Any]:
        benchmarks = {
            "ctr_landing_pct": 2.0,
            "signup_rate_pct": 8.0,
            "activation_rate_pct": 25.0,
        }

        def _component(actual: float, target: float) -> float:
            return max(0.0, min(140.0, (actual / max(0.01, target)) * 100.0))

        ctr_score = _component(ctr_pct, benchmarks["ctr_landing_pct"])
        signup_score = _component(signup_pct, benchmarks["signup_rate_pct"])
        activation_score = _component(activation_pct, benchmarks["activation_rate_pct"])
        raw_score = 0.30 * ctr_score + 0.35 * signup_score + 0.35 * activation_score

        sample_factors: list[float] = []
        if visitors is not None:
            sample_factors.append(min(1.0, visitors / 400.0))
        if signups is not None:
            sample_factors.append(min(1.0, signups / 40.0))
        if activated_users is not None:
            sample_factors.append(min(1.0, activated_users / 20.0))
        if sample_factors:
            confidence = max(0.30, min(1.0, math.sqrt(sum(sample_factors) / len(sample_factors))))
        else:
            confidence = 0.35

        learning_score = int(round(raw_score * confidence + 50.0 * (1.0 - confidence)))
        learning_score = max(0, min(100, learning_score))
        return {
            "learning_score": learning_score,
            "raw_score": round(raw_score, 2),
            "confidence": round(confidence, 3),
            "benchmarks": benchmarks,
        }

    def _feedback_records_path(self) -> Path:
        return self.settings.data_dir / "product_feedback.jsonl"

    def _append_feedback_record(self, payload: dict[str, Any]) -> None:
        path = self._feedback_records_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")

    def _load_feedback_records(self) -> list[dict[str, Any]]:
        path = self._feedback_records_path()
        if not path.exists():
            return []
        records: list[dict[str, Any]] = []
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except Exception:
                continue
            if isinstance(payload, dict):
                records.append(payload)
        return records

    def _topic_tokens(self, text: str) -> set[str]:
        return {token for token in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(token) >= 3}

    def _token_similarity(self, left: set[str], right: set[str]) -> float:
        if not left or not right:
            return 0.0
        overlap = len(left & right)
        denom = max(len(left), len(right), 1)
        return overlap / denom

    def _resolve_execution_profile(self, requested_profile: str | None, fast_mode: bool) -> dict[str, Any]:
        profile_key = (requested_profile or "").strip().lower()
        if not profile_key:
            profile_key = "quick" if fast_mode else "standard"
        profiles: dict[str, dict[str, Any]] = {
            "quick": {
                "name": "quick",
                "time_budget_min": 12,
                "token_budget_est": 18000,
                "max_sources": 3,
                "max_n_ideas": 3,
                "stage_retry_attempts": 1,
                "force_fast_mode": True,
            },
            "standard": {
                "name": "standard",
                "time_budget_min": 35,
                "token_budget_est": 60000,
                "max_sources": 8,
                "max_n_ideas": 10,
                "stage_retry_attempts": 2,
                "force_fast_mode": False,
            },
            "deep": {
                "name": "deep",
                "time_budget_min": 75,
                "token_budget_est": 140000,
                "max_sources": 12,
                "max_n_ideas": 20,
                "stage_retry_attempts": 3,
                "force_fast_mode": False,
            },
            "validation_sprint": {
                "name": "validation_sprint",
                "time_budget_min": 15,
                "token_budget_est": 25000,
                "max_sources": 5,
                "max_n_ideas": 1,
                "stage_retry_attempts": 1,
                "force_fast_mode": True,
                "output_mode": "execution_focused",
            },
        }
        selected = profiles.get(profile_key, profiles["standard"]).copy()
        selected["max_sources"] = max(1, int(selected["max_sources"]))
        selected["max_n_ideas"] = max(1, int(selected["max_n_ideas"]))
        selected["stage_retry_attempts"] = max(1, int(selected["stage_retry_attempts"]))
        return selected

    def _build_historical_learning_memory(self, topic: str, run_id: str | None = None) -> dict[str, Any]:
        try:
            feedback_records = self._load_feedback_records()
        except Exception as e:
            logger.warning("Failed to load feedback records for historical learning: {error}", error=DataSanitizer.sanitize_error_message(e))
            feedback_records = []
        
        try:
            finalized_runs = [r for r in self.manager.list_runs() if r.get("status") in {"completed", "aborted", "killed", "failed"}]
        except Exception as e:
            logger.warning("Failed to load finalized runs for historical learning: {error}", error=DataSanitizer.sanitize_error_message(e))
            finalized_runs = []
        
        if run_id:
            finalized_runs = [r for r in finalized_runs if r.get("id") != run_id]
        
        try:
            max_runs = max(1, int(self.settings.learning_history_max_runs))
        except Exception:
            max_runs = 10  # Default fallback
        finalized_runs = finalized_runs[:max_runs]

        success_counter: Counter[str] = Counter()
        failure_counter: Counter[str] = Counter()
        success_topic_sets: list[set[str]] = []
        failure_topic_sets: list[set[str]] = []
        reasons: list[str] = []

        for record in feedback_records[-max_runs:]:
            try:
                learning_score = float(record.get("learning_score"))
                confidence = max(0.0, min(1.0, float(record.get("confidence", 0.0))))
            except Exception:
                continue
            try:
                tokens = self._topic_tokens(str(record.get("topic", "")))
            except Exception:
                continue
            if not tokens:
                continue
            weight = max(0.2, 0.4 + 0.6 * confidence)
            if learning_score >= 60:
                for token in tokens:
                    success_counter[token] += weight
                success_topic_sets.append(tokens)
            elif learning_score <= 45:
                for token in tokens:
                    failure_counter[token] += weight
                failure_topic_sets.append(tokens)

        for run in finalized_runs:
            try:
                run_topic_tokens = self._topic_tokens(str(run.get("topic", "")))
            except Exception:
                continue
            if not run_topic_tokens:
                continue
            status = str(run.get("status") or "")
            output_dir = Path(run.get("output_dir") or "")
            if status in {"aborted", "failed", "killed"}:
                for token in run_topic_tokens:
                    failure_counter[token] += 0.35
                failure_topic_sets.append(run_topic_tokens)
                try:
                    reason_path = output_dir / ("kill_reason.md" if status == "killed" else "abort_reason.md")
                    reason_text = self._load_text_artifact(reason_path) or ""
                    if reason_text:
                        reasons.append(reason_text[:220])
                        for token in self._topic_tokens(reason_text):
                            failure_counter[token] += 0.15
                except Exception:
                    # If we can't load reason files, continue without them
                    pass
            elif status == "completed":
                for token in run_topic_tokens:
                    success_counter[token] += 0.25
                success_topic_sets.append(run_topic_tokens)

        try:
            exploration_rate = max(0.0, min(0.6, float(self.settings.learning_exploration_rate)))
        except Exception:
            exploration_rate = 0.3  # Default fallback

        return {
            "topic": topic,
            "feedback_records": len(feedback_records),
            "finalized_runs": len(finalized_runs),
            "success_keywords": [token for token, _ in success_counter.most_common(40)],
            "failure_keywords": [token for token, _ in failure_counter.most_common(40)],
            "success_topic_sets": [sorted(list(tokens)) for tokens in success_topic_sets[:60]],
            "failure_topic_sets": [sorted(list(tokens)) for tokens in failure_topic_sets[:60]],
            "recent_failure_reasons": reasons[-10:],
            "exploration_rate": exploration_rate,
        }

    def _apply_historical_learning_to_scores(
        self,
        scores: list[IdeaScore],
        ideas: list[Idea],
        topic: str,
        run_id: str,
        memory: dict[str, Any],
    ) -> list[IdeaScore]:
        if not scores:
            return scores
        
        try:
            idea_map = {idea.name: idea for idea in ideas}
            success_keywords = set(memory.get("success_keywords") or [])
            failure_keywords = set(memory.get("failure_keywords") or [])
            success_sets = [set(item) for item in (memory.get("success_topic_sets") or []) if isinstance(item, list)]
            
            try:
                exploration_rate = max(0.0, min(0.6, float(memory.get("exploration_rate", 0.0))))
            except Exception:
                exploration_rate = 0.3  # Default fallback
            
            rng = random.Random(f"{run_id}:{topic}:historical-learning")
            
            try:
                success_bonus_cap = max(1, int(self.settings.learning_success_bonus_max))
            except Exception:
                success_bonus_cap = 5  # Default fallback
            
            try:
                failure_penalty_cap = max(1, int(self.settings.learning_failure_penalty_max))
            except Exception:
                failure_penalty_cap = 5  # Default fallback
            
            try:
                novelty_bonus_cap = max(0, int(self.settings.learning_novelty_bonus_max))
            except Exception:
                novelty_bonus_cap = 3  # Default fallback
            
            try:
                clone_penalty_start = max(0.45, min(0.95, float(self.settings.learning_clone_penalty_start)))
            except Exception:
                clone_penalty_start = 0.7  # Default fallback

            adjusted: list[IdeaScore] = []
            for score in scores:
                try:
                    idea = idea_map.get(score.name)
                    idea_text = (
                        " ".join(
                            [
                                score.name,
                                getattr(idea, "one_liner", "") if idea else "",
                                getattr(idea, "problem", "") if idea else "",
                                getattr(idea, "solution", "") if idea else "",
                                " ".join(getattr(idea, "key_features", []) if idea else []),
                            ]
                        )
                    ).strip()
                    tokens = self._topic_tokens(idea_text)
                    if not tokens:
                        adjusted.append(score)
                        continue

                    success_overlap = len(tokens & success_keywords) / max(1, min(len(tokens), max(1, len(success_keywords))))
                    failure_overlap = len(tokens & failure_keywords) / max(1, min(len(tokens), max(1, len(failure_keywords))))
                    max_success_similarity = max((self._token_similarity(tokens, ref) for ref in success_sets), default=0.0)
                    novelty = max(0.0, 1.0 - max_success_similarity)
                    clone_penalty = 0.0
                    if max_success_similarity > clone_penalty_start:
                        clone_penalty = ((max_success_similarity - clone_penalty_start) / max(0.05, 1.0 - clone_penalty_start)) * 4.0

                    exploration_jitter = rng.uniform(-1.0, 1.0) * exploration_rate * (0.5 + novelty * 0.7)
                    success_bonus = success_overlap * success_bonus_cap
                    failure_penalty = failure_overlap * failure_penalty_cap
                    novelty_bonus = novelty * novelty_bonus_cap
                    total_delta = int(round(success_bonus + novelty_bonus - failure_penalty - clone_penalty + exploration_jitter * 4.0))
                    total_delta = max(-failure_penalty_cap, min(success_bonus_cap + novelty_bonus_cap, total_delta))

                    signals = dict(score.signals or {})
                    signals.update(
                        {
                            "historical_learning_adjustment": total_delta,
                            "historical_success_overlap": round(success_overlap, 3),
                            "historical_failure_overlap": round(failure_overlap, 3),
                            "historical_novelty": round(novelty, 3),
                            "historical_clone_similarity": round(max_success_similarity, 3),
                            "historical_exploration_rate": round(exploration_rate, 3),
                        }
                    )
                    rationale = score.rationale
                    if total_delta != 0:
                        rationale = (
                            f"{score.rationale} "
                            f"(Historical learning {total_delta:+d}: avoids repeated failures while preserving exploration.)"
                        ).strip()
                    adjusted.append(
                        IdeaScore(
                            name=score.name,
                            score=max(0, min(100, score.score + total_delta)),
                            rationale=rationale,
                            risks=score.risks,
                            signals=signals,
                        )
                    )
                except Exception as e:
                    # If processing individual score fails, keep original score
                    logger.warning("Failed to apply historical learning to score {score}: {error}", score=score.name, error=DataSanitizer.sanitize_error_message(e))
                    adjusted.append(score)

            return adjusted
        except Exception as e:
            # If entire function fails, return original scores
            logger.error("Historical learning score adjustment failed: {error}", error=DataSanitizer.sanitize_error_message(e))
            return scores

    def _build_product_learning_profile(self, topic: str) -> dict[str, Any]:
        records = self._load_feedback_records()
        if not records:
            return {
                "score": 50,
                "confidence": 0.0,
                "adjustment": 0,
                "records": 0,
                "keywords": [],
            }

        topic_tokens = self._topic_tokens(topic)
        weighted_scores = 0.0
        weight_total = 0.0
        keyword_counter: Counter[str] = Counter()
        valid_records = 0
        for record in records:
            try:
                score = float(record.get("learning_score"))
                confidence = float(record.get("confidence", 0.0))
            except Exception:
                continue
            if score < 0 or score > 100:
                continue
            record_tokens = self._topic_tokens(str(record.get("topic", "")))
            overlap = len(topic_tokens & record_tokens)
            denom = max(len(topic_tokens), len(record_tokens), 1)
            similarity = overlap / denom
            weight = max(0.05, (0.25 + 0.75 * max(0.0, min(1.0, confidence))) * (0.50 + 0.50 * similarity))
            weighted_scores += score * weight
            weight_total += weight
            valid_records += 1
            if score >= 60:
                keyword_counter.update(record_tokens)

        if weight_total <= 0:
            return {
                "score": 50,
                "confidence": 0.0,
                "adjustment": 0,
                "records": valid_records,
                "keywords": [],
            }

        profile_score = int(round(weighted_scores / weight_total))
        profile_confidence = max(0.0, min(1.0, weight_total / max(1.0, valid_records)))
        adjustment = int(round((profile_score - 50) * profile_confidence * 0.25))
        adjustment = max(-12, min(12, adjustment))
        keywords = [token for token, _ in keyword_counter.most_common(12)]
        return {
            "score": profile_score,
            "confidence": round(profile_confidence, 3),
            "adjustment": adjustment,
            "records": valid_records,
            "keywords": keywords,
        }

    def _compute_adaptive_thresholds(self, topic: str) -> dict[str, Any]:
        base_signal = int(self.settings.signal_quality_threshold)
        base_kill = int(self.settings.kill_threshold)
        payload: dict[str, Any] = {
            "topic": topic,
            "signal_quality_threshold_base": base_signal,
            "kill_threshold_base": base_kill,
            "signal_quality_threshold": base_signal,
            "kill_threshold": base_kill,
            "segment_records": 0,
            "global_records": 0,
            "segment_weighted_learning_score": None,
            "segment_weighted_confidence": None,
            "segment_keywords": [],
            "notes": "No qualifying feedback segment. Using base thresholds.",
        }

        records = self._load_feedback_records()
        payload["global_records"] = len(records)
        if not records:
            return payload

        topic_tokens = self._topic_tokens(topic)
        weighted_score = 0.0
        weighted_conf = 0.0
        total_weight = 0.0
        segment_keywords: Counter[str] = Counter()
        matched_records = 0

        for record in records:
            try:
                learning_score = float(record.get("learning_score"))
                confidence = float(record.get("confidence", 0.0))
            except Exception:
                continue
            if learning_score < 0 or learning_score > 100:
                continue
            record_topic = str(record.get("topic", ""))
            record_tokens = self._topic_tokens(record_topic)
            overlap = len(topic_tokens & record_tokens)
            denom = max(len(topic_tokens), len(record_tokens), 1)
            similarity = overlap / denom
            if similarity < 0.2:
                continue
            confidence = max(0.0, min(1.0, confidence))
            weight = max(0.05, (0.25 + 0.75 * confidence) * (0.40 + 0.60 * similarity))
            weighted_score += learning_score * weight
            weighted_conf += confidence * weight
            total_weight += weight
            matched_records += 1
            segment_keywords.update(record_tokens)

        payload["segment_records"] = matched_records
        if matched_records < 2 or total_weight <= 0:
            payload["notes"] = "Insufficient segment evidence (<2 matched feedback records). Using base thresholds."
            return payload

        segment_score = weighted_score / total_weight
        segment_conf = weighted_conf / total_weight
        payload["segment_weighted_learning_score"] = round(segment_score, 2)
        payload["segment_weighted_confidence"] = round(segment_conf, 3)
        payload["segment_keywords"] = [token for token, _ in segment_keywords.most_common(8)]

        # Strong segments with high learning score relax thresholds; weak segments tighten them.
        pressure = max(-1.0, min(1.0, (segment_score - 50.0) / 50.0))
        evidence = max(0.0, min(1.0, min(1.0, matched_records / 6.0) * (0.50 + 0.50 * segment_conf)))
        delta = int(round(pressure * 10 * evidence))
        adjusted_signal = max(25, min(80, base_signal - delta))
        adjusted_kill = max(40, min(85, base_kill - delta))
        payload["signal_quality_threshold"] = int(adjusted_signal)
        payload["kill_threshold"] = int(adjusted_kill)
        payload["notes"] = "Thresholds auto-adjusted from topic-segment launch feedback."
        return payload

    def _idea_token_fit(self, idea: Idea | None, profile_keywords: list[str]) -> float:
        if not idea or not profile_keywords:
            return 1.0
        profile_set = set(profile_keywords)
        idea_text = " ".join(
            [
                idea.name,
                idea.one_liner,
                idea.problem,
                idea.solution,
                " ".join(idea.key_features),
            ]
        )
        tokens = self._topic_tokens(idea_text)
        if not tokens:
            return 1.0
        overlap = len(tokens & profile_set)
        return max(0.0, min(1.0, overlap / max(1, min(len(tokens), len(profile_set)))))

    def _apply_product_learning_to_scores(
        self,
        scores: list[IdeaScore],
        ideas: list[Idea],
        profile: dict[str, Any],
    ) -> list[IdeaScore]:
        base_adjustment = int(profile.get("adjustment", 0))
        if not scores or base_adjustment == 0:
            return scores

        idea_map = {idea.name: idea for idea in ideas}
        keywords = list(profile.get("keywords") or [])
        adjusted_scores: list[IdeaScore] = []
        for score in scores:
            idea = idea_map.get(score.name)
            fit = self._idea_token_fit(idea, keywords)
            idea_adjustment = int(round(base_adjustment * (0.70 + 0.60 * fit)))
            new_score = max(0, min(100, score.score + idea_adjustment))
            signals = dict(score.signals or {})
            signals.update(
                {
                    "product_learning_profile_score": profile.get("score"),
                    "product_learning_confidence": profile.get("confidence"),
                    "product_learning_adjustment": idea_adjustment,
                }
            )
            rationale = score.rationale
            if idea_adjustment != 0:
                rationale = (
                    f"{score.rationale} "
                    f"(Adjusted by product learning {idea_adjustment:+d} from historical launch metrics.)"
                ).strip()
            adjusted_scores.append(
                IdeaScore(
                    name=score.name,
                    score=new_score,
                    rationale=rationale,
                    risks=score.risks,
                    signals=signals,
                )
            )
        return adjusted_scores

    def _apply_product_learning_to_top_idea(
        self,
        top: IdeaScore,
        ideas: list[Idea],
        profile: dict[str, Any],
    ) -> IdeaScore:
        base_adjustment = int(profile.get("adjustment", 0))
        if base_adjustment == 0:
            return top
        idea = next((item for item in ideas if item.name == top.name), None)
        fit = self._idea_token_fit(idea, list(profile.get("keywords") or []))
        idea_adjustment = int(round(base_adjustment * (0.70 + 0.60 * fit)))
        new_score = max(0, min(100, top.score + idea_adjustment))
        signals = dict(top.signals or {})
        signals.update(
            {
                "product_learning_profile_score": profile.get("score"),
                "product_learning_confidence": profile.get("confidence"),
                "product_learning_adjustment": idea_adjustment,
            }
        )
        rationale = top.rationale
        if idea_adjustment != 0:
            rationale = (
                f"{top.rationale} "
                f"(Adjusted by product learning {idea_adjustment:+d} from historical launch metrics.)"
            ).strip()
        return IdeaScore(
            name=top.name,
            score=new_score,
            rationale=rationale,
            risks=top.risks,
            signals=signals,
        )

    def _write_decision_file(
        self,
        run_id: str,
        status: str,
        reason: str,
        signals: dict[str, Any],
        hypotheses: list[str],
        missing: list[str],
    ) -> None:
        lines = ["# Decision", "", f"- Status: {status}", f"- Reason: {reason}", ""]
        if signals:
            lines.append("## Signals")
            for key, value in signals.items():
                lines.append(f"- {key}: {self._format_signal_value(value)}")
            lines.append("")
        if hypotheses:
            lines.append("## Hypotheses")
            for hypothesis in hypotheses:
                lines.append(f"- {hypothesis}")
            lines.append("")
        if missing:
            lines.append("## Missing Signals")
            for item in missing:
                lines.append(f"- {item}")
            lines.append("")
        run_info = self.manager.get_run(run_id)
        run_dir = Path(run_info["output_dir"]) if run_info else self.settings.runs_dir / run_id
        confidence = compute_confidence(run_dir, settings=self.settings, status=status)
        lines.append("## Confidence Score")
        lines.append(f"- Score (0-100): {confidence['score']}")
        for key, detail in confidence["breakdown"].items():
            label = key.replace("_", " ").capitalize()
            lines.append(f"  - {label}: {detail['score']}/{detail['max']}")
        if confidence["caps"]:
            lines.append("")
            lines.append("## Confidence Caps")
            for cap in confidence["caps"]:
                lines.append(f"- {cap}")
        if confidence["reasons"]:
            lines.append("")
            lines.append("## Confidence Reasons")
            for reason_entry in confidence["reasons"]:
                lines.append(f"- {reason_entry}")
        content = "\n".join(line for line in lines if line is not None).rstrip() + "\n"
        self.manager.write_artifact(run_id, "decision.md", content)
        self._safe_write_ship_summary(run_id)

    def _format_signal_value(self, value: Any) -> str:
        if isinstance(value, dict):
            parts = [f"{key}={val}" for key, val in value.items()]
            return "{" + ", ".join(parts) + "}"
        return str(value)

    def _safe_write_ship_summary(self, run_id: str) -> None:
        try:
            self._write_ship_summary(run_id)
        except Exception as exc:
            self.manager.write_artifact(run_id, "ship_summary_error.md", str(exc))

    def _propose_collection_actions_for_unknown_fields(self, run_id: str, data_source: dict[str, str], topic: str, decision_missing: list[str]) -> None:
        """Rule: Automatically propose collection actions when critical fields are unknown."""
        unknown_fields = [key for key, value in data_source.items() if value == "unknown"]
        
        if not unknown_fields:
            return
        
        # Define collection actions for each critical field
        collection_actions = {
            "pages": {
                "source_missing": "No web sources configured or accessible",
                "next_step": "Configure pain_sources in configs/sources.yaml with valid URLs and APIs",
                "priority": "HIGH"
            },
            "pains": {
                "source_missing": "No pain statements extracted from sources",
                "next_step": "Add more diverse sources or improve pain extraction prompts",
                "priority": "HIGH"
            },
            "competitors": {
                "source_missing": "No competitor data found in sources",
                "next_step": "Configure competitor_sources in configs/sources.yaml or add competitor analysis tools",
                "priority": "MEDIUM"
            },
            "seeds": {
                "source_missing": "No seed inputs provided (ICP, context, pains, competitors)",
                "next_step": "Provide seed inputs via UI or API to improve analysis quality",
                "priority": "MEDIUM"
            }
        }
        
        # Generate collection action recommendations
        actions = []
        for field in unknown_fields:
            if field in collection_actions:
                action = collection_actions[field]
                actions.append({
                    "field": field,
                    "source_missing": action["source_missing"],
                    "next_step": action["next_step"],
                    "priority": action["priority"],
                    "estimated_impact": self._estimate_field_impact(field)
                })
        
        if actions:
            # Write collection actions to artifact
            self.manager.write_json(run_id, "collection_actions.json", {
                "topic": topic,
                "unknown_fields": unknown_fields,
                "actions": actions,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "rule_applied": "auto-propose-collection-for-unknown-critical-fields"
            })
            
            # Log the recommendation
            action_summary = ", ".join([f"{a['field']} ({a['priority']})" for a in actions])
            self._log_progress(
                run_id,
                f"Collection actions auto-proposed for unknown critical fields: {action_summary}"
            )
            
            # Add to decision missing for visibility
            for action in actions:
                decision_missing.append(
                    f"Unknown critical field '{action['field']}': {action['next_step']}"
                )

    def _estimate_field_impact(self, field: str) -> str:
        """Estimate the impact of missing a critical field."""
        impact_map = {
            "pages": "CRITICAL - No market signals available",
            "pains": "HIGH - Limited problem understanding",
            "competitors": "MEDIUM - No competitive analysis",
            "seeds": "LOW - Can proceed with generic analysis"
        }
        return impact_map.get(field, "UNKNOWN")

    def _generate_validation_sprint_output(
        self, 
        run_id: str, 
        topic: str, 
        top_idea: IdeaScore, 
        validated_pains: list[dict[str, Any]],
        competitors: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Generate execution-focused output for Validation Sprint mode."""
        
        # Generate hypothesis
        hypothesis = self._generate_validation_hypothesis(topic, top_idea, validated_pains)
        
        # Generate A/B test plan
        test_plan = self._generate_ab_test_plan(hypothesis, top_idea)
        
        # Generate landing page copy
        landing_content = self._generate_landing_copy(hypothesis, top_idea, topic)
        
        # Generate outreach messages
        outreach_messages = self._generate_outreach_messages(hypothesis, top_idea, competitors)
        
        # Generate target KPIs
        target_kpis = self._generate_target_kpis(hypothesis, topic)
        
        validation_output = {
            "mode": "validation_sprint",
            "duration_days": 7,
            "topic": topic,
            "hypothesis": hypothesis,
            "test_plan": test_plan,
            "landing_page": landing_content,
            "outreach_messages": outreach_messages,
            "target_kpis": target_kpis,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "next_steps": [
                "1. Set up landing page with A/B test variants",
                "2. Launch outreach campaigns to target segments",
                "3. Monitor KPIs daily for 7 days",
                "4. Analyze results and decide on pivot vs persevere"
            ]
        }
        
        # Write validation sprint output
        self.manager.write_json(run_id, "validation_sprint_output.json", validation_output)
        
        # Also write a markdown version for easy reading
        markdown_content = self._format_validation_sprint_markdown(validation_output)
        self.manager.write_artifact(run_id, "validation_sprint_plan.md", markdown_content)
        
        return validation_output

    def _generate_validation_hypothesis(
        self, 
        topic: str, 
        top_idea: IdeaScore, 
        validated_pains: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Generate a clear testable hypothesis."""
        
        # Extract key pain points
        key_pains = []
        for pain in validated_pains[:3]:  # Top 3 pains
            key_pains.append(pain.get("problem", "").strip())
        
        # Build hypothesis statement
        hypothesis_statement = ("Nous croyons que [TARGET_SEGMENT] éprouvent [KEY_PROBLEM] "
        "lorsque [CONTEXT]. Si nous leur offrons [SOLUTION], "
        "alors [EXPECTED_OUTCOME] mesuré par [SUCCESS_METRIC].")
        
        # Fill in template with idea details
        target_segment = top_idea.rationale.split("target")[0].strip() if "target" in top_idea.rationale.lower() else "Solo founders"
        key_problem = key_pains[0] if key_pains else "inefficient workflows"
        solution = top_idea.name
        expected_outcome = "ils adopteront notre solution"
        success_metric = "taux d'adoption > 15% en 7 jours"
        
        hypothesis = {
            "statement": hypothesis_statement.replace("[TARGET_SEGMENT]", target_segment)
                                      .replace("[KEY_PROBLEM]", key_problem)
                                      .replace("[CONTEXT]", "ils gèrent leur croissance quotidienne")
                                      .replace("[SOLUTION]", solution)
                                      .replace("[EXPECTED_OUTCOME]", expected_outcome)
                                      .replace("[SUCCESS_METRIC]", success_metric),
            "target_segment": target_segment,
            "key_problem": key_problem,
            "solution": solution,
            "expected_outcome": expected_outcome,
            "success_metric": success_metric,
            "risk_level": "MEDIUM",
            "confidence": 65
        }
        
        return hypothesis

    def _generate_ab_test_plan(self, hypothesis: dict[str, Any], top_idea: IdeaScore) -> dict[str, Any]:
        """Generate A/B test plan for validation."""
        
        return {
            "test_name": f"Validation Sprint - {top_idea.name}",
            "duration_days": 7,
            "variants": {
                "A": {
                    "name": "Control - MVP Features",
                    "description": "Version minimale avec fonctionnalités essentielles",
                    "key_changes": ["Interface simplifiée", "Onboarding rapide", "Prix d'essai gratuit"]
                },
                "B": {
                    "name": "Test - Enhanced Value Prop",
                    "description": "Version avec proposition de valeur améliorée",
                    "key_changes": ["Copy optimisé", "Social proof", "Garantie satisfait ou remboursé"]
                }
            },
            "success_criteria": [
                "Taux de conversion > 10%",
                "Temps sur page > 2 minutes",
                "Taux d'engagement > 30%"
            ],
            "traffic_split": "50/50",
            "sample_size": "min 100 visiteurs par variant"
        }

    def _generate_landing_copy(
        self, 
        hypothesis: dict[str, Any], 
        top_idea: IdeaScore, 
        topic: str
    ) -> dict[str, Any]:
        """Generate landing page copy for validation."""
        
        return {
            "headline": f"La solution {top_idea.name} pour {hypothesis['target_segment']}",
            "subheadline": f"Résolvez {hypothesis['key_problem']} en moins de temps",
            "key_benefits": [
                "Économisez 10h par semaine",
                "Lancez plus vite vos projets", 
                "Automatisez les tâches répétitives"
            ],
            "social_proof": [
                "Rejoint par 50+ entrepreneurs en beta",
                "4.8/5 étoiles sur les premiers tests",
                "Cas d'usage validés par 3 experts"
            ],
            "cta_primary": "Commencer l'essai gratuit - 7 jours",
            "cta_secondary": "Voir la démo en 2 minutes",
            "pricing": {
                "trial": "Gratuit 7 jours",
                "after_trial": "29€/mois - sans engagement",
                "guarantee": "Satisfait ou remboursé 30 jours"
            },
            "faq_items": [
                {
                    "q": "Est-ce vraiment gratuit les 7 premiers jours ?",
                    "a": "Oui, 100% gratuit et sans engagement. Annulez quand vous voulez."
                },
                {
                    "q": "Combien de temps pour voir des résultats ?", 
                    "a": "La plupart des utilisateurs voient des bénéfices dès les premiers jours."
                }
            ]
        }

    def _generate_outreach_messages(
        self, 
        hypothesis: dict[str, Any], 
        top_idea: IdeaScore, 
        competitors: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Generate 3 outreach messages for validation."""
        
        return [
            {
                "channel": "Email - Cold Outreach",
                "subject": f"Aide pour {hypothesis['key_problem'].lower()} ?",
                "template": (f"Bonjour [PRÉNOM],\n\n"
                f"J'ai remarqué que beaucoup de {hypothesis['target_segment'].lower()} comme vous "
                f"strugglent avec {hypothesis['key_problem'].lower()}.\n\n"
                f"J'ai développé {top_idea.name} - une solution qui vous permet de "
                f"[PRINCIPAL_BÉNÉFICE].\n\n"
                f"Seriez-vous ouvert à un échange de 15 minutes la semaine prochaine "
                f"pour en discuter ?\n\n"
                f"Bien à vous,\n"
                f"[VOTRE NOM]"),
                "personalization_vars": ["PRÉNOM", "PRINCIPAL_BÉNÉFICE"],
                "target_audience": "Cold prospects",
                "send_timing": "Jour 2-3 du sprint"
            },
            {
                "channel": "LinkedIn - Message direct",
                "subject": "Solution pour {hypothesis['key_problem'].lower()}",
                "template": (f"Salut [PRÉNOM] !\n\n"
                f"Je vois que vous êtes dans l'écosystème {hypothesis['target_segment']}. "
                f"Je partage une solution qui pourrait intéresser votre réseau : {top_idea.name}.\n\n"
                f"Elle aide spécifiquement avec {hypothesis['key_problem'].lower()}. "
                f"Plusieurs entrepreneurs déjà l'adoptent avec de bons résultats.\n\n"
                f"Ça vous dirait qu'on en discute 5 minutes ?\n\n"
                f"[VOTRE NOM]"),
                "personalization_vars": ["PRÉNOM"],
                "target_audience": "LinkedIn connections",
                "send_timing": "Jour 4-5 du sprint"
            },
            {
                "channel": "Communauté - Post engagement",
                "subject": "Retour d'expérience validation sprint",
                "template": (f"🚀 VALIDATION SPRINT - JOUR 5\n\n"
                f"Je teste actuellement {top_idea.name} pour résoudre {hypothesis['key_problem'].lower()}.\n\n"
                f"📊 Résultats intermédiaires :\n"
                f"• [RÉSULTAT_1]\n"
                f"• [RÉSULTAT_2]\n" 
                f"• [RÉSULTAT_3]\n\n"
                f"🎯 Objectif : [OBJECTIF_SPRINT]\n\n"
                f"Quelqu'un a déjà testé une solution similaire ? "
                f"Vos retours m'intéressent beaucoup !\n\n"
                f"#solo #startup #validation"),
                "personalization_vars": ["RÉSULTAT_1", "RÉSULTAT_2", "RÉSULTAT_3", "OBJECTIF_SPRINT"],
                "target_audience": "Community/Forum members",
                "send_timing": "Jour 5-7 du sprint"
            }
        ]

    def _generate_target_kpis(self, hypothesis: dict[str, Any], topic: str) -> dict[str, Any]:
        """Generate target KPIs for 7-day validation sprint."""
        
        return {
            "primary_kpis": {
                "conversion_rate": {
                    "target": "15%",
                    "current": "0%",
                    "measurement": "Sign-ups / visiteurs uniques"
                },
                "activation_rate": {
                    "target": "60%", 
                    "current": "0%",
                    "measurement": "Utilisateurs qui complètent onboarding / sign-ups"
                },
                "retention_day_7": {
                    "target": "40%",
                    "current": "0%", 
                    "measurement": "Utilisateurs actifs jour 7 / sign-ups"
                }
            },
            "secondary_kpis": {
                "engagement_time": {
                    "target": "2+ minutes",
                    "current": "0 min",
                    "measurement": "Temps moyen par session"
                },
                "feature_adoption": {
                    "target": "3+ fonctionnalités",
                    "current": "0",
                    "measurement": "Nombre de fonctionnalités utilisées par utilisateur"
                },
                "nps_score": {
                    "target": "+40",
                    "current": "N/A",
                    "measurement": "Net Promoter Score après 7 jours"
                }
            },
            "success_criteria": {
                "minimum_viable": "Conversion > 10% ET Activation > 40%",
                "target_achieved": "Conversion > 15% ET Activation > 60%",
                "exceptional": "Conversion > 25% ET Retention > 50%"
            },
            "tracking_setup": [
                "Google Analytics 4 installé",
                "Événements de conversion définis",
                "Dashboard KPI créé",
                "Alertes quotidiennes configurées"
            ]
        }

    def _format_validation_sprint_markdown(self, validation_output: dict[str, Any]) -> str:
        """Format validation sprint output as readable markdown."""
        
        md = ("# Validation Sprint 7 Jours - " + validation_output['topic'] + "\n\n" +
        "## 🎯 Hypothèse de Validation\n\n" +
        "**Segment Cible** : " + validation_output['hypothesis']['target_segment'] + "\n" +
        "**Problème Clé** : " + validation_output['hypothesis']['key_problem'] + "\n" +
        "**Solution Proposée** : " + validation_output['hypothesis']['solution'] + "\n\n" +
        "### Énoncé Complet\n" +
        validation_output['hypothesis']['statement'] + "\n\n" +
        "**Confiance** : " + str(validation_output['hypothesis']['confidence']) + "% | **Risque** : " + validation_output['hypothesis']['risk_level'] + "\n\n" +
        "---\n\n" +
        "## 🧪 Plan de Test A/B\n\n" +
        "**Durée** : " + str(validation_output['test_plan']['duration_days']) + " jours\n" +
        "**Répartition Trafic** : " + validation_output['test_plan']['traffic_split'] + "\n\n" +
        "### Variante A : " + validation_output['test_plan']['variants']['A']['name'] + "\n" +
        validation_output['test_plan']['variants']['A']['description'] + "\n\n" +
        "**Changements Clés** :\n" +
        "\n".join(f"• {change}" for change in validation_output['test_plan']['variants']['A']['key_changes']) + "\n\n" +
        "### Variante B : " + validation_output['test_plan']['variants']['B']['name'] + "\n" +
        validation_output['test_plan']['variants']['B']['description'] + "\n\n" +
        "**Changements Clés** :\n" +
        "\n".join(f"• {change}" for change in validation_output['test_plan']['variants']['B']['key_changes']) + "\n\n" +
        "### Critères de Succès\n" +
        "\n".join(f"• {criteria}" for criteria in validation_output['test_plan']['success_criteria']) + "\n\n" +
        "---\n\n" +
        "## 🌄 Contenu Landing Page\n\n" +
        "**Titre Principal** : " + validation_output['landing_page']['headline'] + "\n\n" +
        "**Sous-titre** : " + validation_output['landing_page']['subheadline'] + "\n\n" +
        "### Bénéfices Clés\n" +
        "\n".join(f"• {benefit}" for benefit in validation_output['landing_page']['key_benefits']) + "\n\n" +
        "### Preuve Sociale\n" +
        "\n".join(f"• {proof}" for proof in validation_output['landing_page']['social_proof']) + "\n\n" +
        "### Appels à l'Action\n" +
        "- **Principal** : " + validation_output['landing_page']['cta_primary'] + "\n" +
        "- **Secondaire** : " + validation_output['landing_page']['cta_secondary'] + "\n\n" +
        "### Tarification\n" +
        "- **Essai** : " + validation_output['landing_page']['pricing']['trial'] + "\n" +
        "- **Après essai** : " + validation_output['landing_page']['pricing']['after_trial'] + "\n" +
        "- **Garantie** : " + validation_output['landing_page']['pricing']['guarantee'] + "\n\n" +
        "---\n\n" +
        "## 📧 Messages Outreach\n\n" +
        "### Message 1 - Email Cold Outreach\n" +
        "**Canal** : " + validation_output['outreach_messages'][0]['channel'] + "\n" +
        "**Timing** : " + validation_output['outreach_messages'][0]['send_timing'] + "\n" +
        "**Audience** : " + validation_output['outreach_messages'][0]['target_audience'] + "\n\n" +
        "**Sujet** : " + validation_output['outreach_messages'][0]['subject'] + "\n\n" +
        "**Template** :\n" +
        "```\n" + validation_output['outreach_messages'][0]['template'] + "\n```\n\n" +
        "### Message 2 - LinkedIn Direct\n" +
        "**Canal** : " + validation_output['outreach_messages'][1]['channel'] + "\n" +
        "**Timing** : " + validation_output['outreach_messages'][1]['send_timing'] + "\n" +
        "**Audience** : " + validation_output['outreach_messages'][1]['target_audience'] + "\n\n" +
        "**Sujet** : " + validation_output['outreach_messages'][1]['subject'] + "\n\n" +
        "**Template** :\n" +
        "```\n" + validation_output['outreach_messages'][1]['template'] + "\n```\n\n" +
        "### Message 3 - Communauté Engagement\n" +
        "**Canal** : " + validation_output['outreach_messages'][2]['channel'] + "\n" +
        "**Timing** : " + validation_output['outreach_messages'][2]['send_timing'] + "\n" +
        "**Audience** : " + validation_output['outreach_messages'][2]['target_audience'] + "\n\n" +
        "**Sujet** : " + validation_output['outreach_messages'][2]['subject'] + "\n\n" +
        "**Template** :\n" +
        "```\n" + validation_output['outreach_messages'][2]['template'] + "\n```\n\n" +
        "---\n\n" +
        "## 📊 KPI Cibles\n\n" +
        "### KPIs Primaires\n" +
        "| Métrique | Cible | Actuel | Mesure |\n" +
        "|-----------|--------|---------|---------|\n" +
        "| Taux Conversion | " + validation_output['target_kpis']['primary_kpis']['conversion_rate']['target'] + " | " + validation_output['target_kpis']['primary_kpis']['conversion_rate']['current'] + " | " + validation_output['target_kpis']['primary_kpis']['conversion_rate']['measurement'] + " |\n" +
        "| Taux Activation | " + validation_output['target_kpis']['primary_kpis']['activation_rate']['target'] + " | " + validation_output['target_kpis']['primary_kpis']['activation_rate']['current'] + " | " + validation_output['target_kpis']['primary_kpis']['activation_rate']['measurement'] + " |\n" +
        "| Rétention J7 | " + validation_output['target_kpis']['primary_kpis']['retention_day_7']['target'] + " | " + validation_output['target_kpis']['primary_kpis']['retention_day_7']['current'] + " | " + validation_output['target_kpis']['primary_kpis']['retention_day_7']['measurement'] + " |\n\n" +
        "### KPIs Secondaires\n" +
        "| Métrique | Cible | Actuel | Mesure |\n" +
        "|-----------|--------|---------|---------|\n" +
        "| Temps Engagement | " + validation_output['target_kpis']['secondary_kpis']['engagement_time']['target'] + " | " + validation_output['target_kpis']['secondary_kpis']['engagement_time']['current'] + " | " + validation_output['target_kpis']['secondary_kpis']['engagement_time']['measurement'] + " |\n" +
        "| Adoption Fonctionnalités | " + validation_output['target_kpis']['secondary_kpis']['feature_adoption']['target'] + " | " + validation_output['target_kpis']['secondary_kpis']['feature_adoption']['current'] + " | " + validation_output['target_kpis']['secondary_kpis']['feature_adoption']['measurement'] + " |\n" +
        "| Score NPS | " + validation_output['target_kpis']['secondary_kpis']['nps_score']['target'] + " | " + validation_output['target_kpis']['secondary_kpis']['nps_score']['current'] + " | " + validation_output['target_kpis']['secondary_kpis']['nps_score']['measurement'] + " |\n\n" +
        "### Critères de Succès\n" +
        "- **Minimum Viable** : " + validation_output['target_kpis']['success_criteria']['minimum_viable'] + "\n" +
        "- **Cible Atteinte** : " + validation_output['target_kpis']['success_criteria']['target_achieved'] + "\n" +
        "- **Exceptionnel** : " + validation_output['target_kpis']['success_criteria']['exceptional'] + "\n\n" +
        "---\n\n" +
        "## 🚀 Prochaines Étapes\n\n" +
        "\n".join(step for step in validation_output['next_steps']) + "\n\n" +
        "---\n\n" +
        "*Généré le " + validation_output['generated_at'] + "*\n" +
        "*Mode : " + validation_output['mode'] + " (" + str(validation_output['duration_days']) + " jours)*\n")
        return md
