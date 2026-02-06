from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

from app.core.config import Settings
from app.core.run_manager import RunManager

ARTIFACT_CHECKS: List[tuple[str, str]] = [
    ("prd.md", "PRD"),
    ("tech_spec.md", "Tech spec"),
    ("market_report.md", "Market report"),
    ("competitor_analysis.json", "Competitor analysis"),
    ("landing_page/index.html", "Landing page"),
    ("content_pack/posts.md", "Content pack"),
    ("repo_skeleton", "Repo skeleton"),
]


def _safe_read_text(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return None


def _safe_load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _extract_decision_status(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    for line in text.splitlines():
        if line.strip().lower().startswith("- status:"):
            return line.split(":", 1)[1].strip().upper()
    return None


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None


def _format_datetime(value: Optional[datetime]) -> str:
    if not value:
        return "unknown"
    return value.strftime("%Y-%m-%d %H:%M UTC")


def _run_uri(run_dir: Path) -> str:
    try:
        return run_dir.resolve().as_uri()
    except Exception:
        return str(run_dir)


def load_run_metrics(run_dir: Path, run_meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    run_meta = run_meta or {}
    run_id = run_meta.get("id") or run_dir.name
    status_meta = (run_meta.get("status") or "").lower() if run_meta.get("status") else "unknown"
    topic = run_meta.get("topic") or "unknown"
    created_at = run_meta.get("created_at")
    created_dt = _parse_datetime(created_at)
    created_display = _format_datetime(created_dt) if created_dt else created_at or "unknown"

    decision_text = _safe_read_text(run_dir / "decision.md")
    decision_status = _extract_decision_status(decision_text) or run_meta.get("status", "").upper() or "UNKNOWN"

    abort_reason = _safe_read_text(run_dir / "abort_reason.md") or _safe_read_text(run_dir / "kill_reason.md")
    confidence = _safe_load_json(run_dir / "confidence.json")
    market_data = _safe_load_json(run_dir / "market_signal_score.json")
    devils = _safe_load_json(run_dir / "devils_advocate.json")
    failure_report = _safe_load_json(run_dir / "failure_report.json")

    missing_artifacts: List[str] = []
    for path_suffix, label in ARTIFACT_CHECKS:
        candidate = run_dir / path_suffix
        if not candidate.exists():
            missing_artifacts.append(label)

    return {
        "run_id": run_id,
        "status": status_meta,
        "topic": topic,
        "created_at": created_at,
        "created_display": created_display,
        "confidence_score": confidence.get("score"),
        "confidence_breakdown": confidence.get("breakdown") or {},
        "confidence_caps": confidence.get("caps") or [],
        "confidence_reasons": confidence.get("reasons") or [],
        "decision_status": decision_status,
        "decision_text": decision_text,
        "signal_score": market_data.get("score"),
        "signal_details": market_data,
        "missing_artifacts": missing_artifacts,
        "abort_reason": abort_reason,
        "devils_advocate": devils,
        "failure_report": failure_report,
        "run_uri": _run_uri(run_dir),
        "created_dt": created_dt,
    }


def aggregate_dashboard_metrics(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(metrics)
    if total == 0:
        return {
            "status_counts": {},
            "status_percent": {},
            "avg_confidence": None,
            "completed_count": 0,
            "top_abort_reasons": [],
            "top_missing_artifacts": [],
            "runs_table": [],
            "metrics_by_run": {},
        }

    status_counts = Counter(m.get("status") or "unknown" for m in metrics)
    status_percent = {
        status: round((count / total) * 100, 1) for status, count in status_counts.items()
    }
    completed_metrics = [
        m
        for m in metrics
        if m.get("status") == "completed" and isinstance(m.get("confidence_score"), (int, float))
    ]
    avg_confidence = (
        round(sum(m["confidence_score"] for m in completed_metrics) / len(completed_metrics), 1)
        if completed_metrics
        else None
    )

    abort_reasons = Counter(
        m["abort_reason"]
        for m in metrics
        if m.get("status") == "aborted" and m.get("abort_reason")
    )
    top_abort_reasons = abort_reasons.most_common(5)

    missing_counter = Counter()
    for m in metrics:
        missing_counter.update(m.get("missing_artifacts") or [])
    top_missing_artifacts = missing_counter.most_common(5)

    sorted_metrics = sorted(
        metrics,
        key=lambda entry: entry.get("created_dt") or datetime.min,
        reverse=True,
    )

    table_entries: List[Dict[str, Any]] = []
    for entry in sorted_metrics:
        table_entries.append(
            {
                "run_id": entry["run_id"],
                "date": entry["created_display"],
                "topic": entry["topic"],
                "status": entry["status"].capitalize(),
                "confidence": entry["confidence_score"] if entry["confidence_score"] is not None else "N/A",
                "decision": entry["decision_status"],
                "signal_score": entry["signal_score"] if entry["signal_score"] is not None else "N/A",
                "link": entry["run_uri"],
            }
        )

    metrics_map = {entry["run_id"]: entry for entry in metrics}
    return {
        "status_counts": dict(status_counts),
        "status_percent": status_percent,
        "avg_confidence": avg_confidence,
        "completed_count": len(completed_metrics),
        "top_abort_reasons": top_abort_reasons,
        "top_missing_artifacts": top_missing_artifacts,
        "runs_table": table_entries,
        "ordered_run_ids": [entry["run_id"] for entry in sorted_metrics],
        "metrics_by_run": metrics_map,
    }


def persist_metrics_index(runs_dir: Path, metrics: List[Dict[str, Any]]) -> None:
    index_path = runs_dir / "_metrics_index.json"
    payload: Dict[str, Any] = {
        "generated_at": datetime.utcnow().isoformat(),
        "runs": {},
    }
    for entry in metrics:
        payload["runs"][entry["run_id"]] = {
            "status": entry["status"],
            "confidence_score": entry["confidence_score"],
            "decision": entry["decision_status"],
            "signal_score": entry["signal_score"],
            "missing_artifacts": entry["missing_artifacts"],
            "abort_reason": entry["abort_reason"],
            "updated_at": entry["created_at"],
        }
    try:
        index_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception:
        pass


def render_quality_dashboard(
    settings: Settings, manager: RunManager, runs: Optional[List[Dict[str, Any]]] = None
) -> None:
    runs = runs or manager.list_runs()
    if not runs:
        st.info("No runs yet. Use the CLI or API to start one.")
        return

    metrics = []
    for run in runs:
        output_dir = Path(run["output_dir"])
        metrics.append(load_run_metrics(output_dir, run))

    aggregated = aggregate_dashboard_metrics(metrics)
    persist_metrics_index(settings.runs_dir, metrics)

    st.subheader("Quality KPIs")
    cols = st.columns(4)
    status_order = ["aborted", "killed", "completed"]
    for idx, status in enumerate(status_order):
        percent = aggregated["status_percent"].get(status, 0.0)
        count = aggregated["status_counts"].get(status, 0)
        label = status.capitalize()
        cols[idx].metric(f"% {label}", f"{percent:.1f}%", f"{count} run(s)")

    avg_conf = (
        f"{aggregated['avg_confidence']:.1f}" if aggregated["avg_confidence"] is not None else "N/A"
    )
    cols[3].metric(
        "Avg confidence (completed)",
        avg_conf,
        f"{aggregated['completed_count']} completed run(s)",
    )

    st.subheader("Top abort reasons")
    if aggregated["top_abort_reasons"]:
        st.table(
            [
                {"reason": reason, "count": count}
                for reason, count in aggregated["top_abort_reasons"]
            ]
        )
    else:
        st.caption("No aborts recorded yet.")

    st.subheader("Top missing artifacts")
    if aggregated["top_missing_artifacts"]:
        st.table(
            [
                {"missing": name, "count": count}
                for name, count in aggregated["top_missing_artifacts"]
            ]
        )
    else:
        st.caption("All critical artifacts are present across runs.")

    if aggregated["runs_table"]:
        st.subheader("Run ledger")
        headers = ["Run ID", "Date", "Topic", "Status", "Confidence", "Decision", "Signal score", "Link"]
        table_markdown = "| " + " | ".join(headers) + " |\n"
        table_markdown += "| " + " | ".join(["---"] * len(headers)) + " |\n"
        for row in aggregated["runs_table"]:
            topic_value = row["topic"] or "unknown"
            safe_topic = str(topic_value).replace("|", "\\|")
            link = f"[Open run]({row['link']})"
            table_markdown += (
                f"| {row['run_id']} | {row['date']} | {safe_topic} | "
                f"{row['status']} | {row['confidence']} | {row['decision']} | {row['signal_score']} | {link} |\n"
            )
        st.markdown(table_markdown)
    else:
        st.caption("No run records found.")

    if not aggregated["metrics_by_run"]:
        return

    st.subheader("Run drilldown")
    run_ids = aggregated.get("ordered_run_ids") or list(aggregated["metrics_by_run"].keys())
    selected = st.selectbox("Select run", run_ids)
    selected_metrics = aggregated["metrics_by_run"][selected]

    st.markdown(f"**Decision ({selected_metrics['decision_status']})**")
    if selected_metrics["decision_text"]:
        st.code(selected_metrics["decision_text"])
    else:
        st.caption("decision.md not yet available.")

    st.markdown("**Confidence breakdown**")
    breakdown = selected_metrics.get("confidence_breakdown") or {}
    if breakdown:
        breakdown_table = []
        for section, detail in breakdown.items():
            breakdown_table.append(
                {
                    "section": section.replace("_", " ").capitalize(),
                    "score": detail.get("score"),
                    "max": detail.get("max"),
                    "details": detail.get("details", ""),
                }
            )
        st.table(breakdown_table)
    else:
        st.caption("Confidence details are not available yet.")

    devils = selected_metrics.get("devils_advocate") or {}
    st.markdown("**Devil's Advocate critique**")
    if devils:
        st.markdown(f"- Verdict: **{devils.get('verdict', 'N/A')}**")
        top_risks = devils.get("top_risks") or []
        if top_risks:
            st.markdown("  - Top risks:")
            for risk in top_risks:
                st.markdown(
                    f"    - {risk.get('type', 'risk')} (severity {risk.get('severity')}): "
                    f"{risk.get('evidence')} -> {risk.get('how_to_test_fast')}"
                )
        missing_data = devils.get("missing_data") or []
        if missing_data:
            st.markdown("  - Missing data:")
            for item in missing_data:
                st.markdown(f"    - {item}")
        killer = devils.get("one killer experiment") or {}
        if killer:
            st.markdown("  - Killer experiment:")
            st.markdown(
                f"    - Hypothesis: {killer.get('hypothesis')}\n"
                f"    - Method: {killer.get('method')}\n"
                f"    - Success metric: {killer.get('success_metric')}\n"
                f"    - Stop metric: {killer.get('stop_metric')}"
            )
    else:
        st.caption("Devil's Advocate has not run for this run.")

    failure_report = selected_metrics.get("failure_report") or {}
    st.markdown("**Failure report**")
    if failure_report:
        st.markdown(
            f"- Status: **{failure_report.get('status', 'unknown')}**\n"
            f"- Last stage: **{failure_report.get('last_stage', 'unknown')}**\n"
            f"- Last reason: {failure_report.get('last_reason', 'n/a')}"
        )
        recent = list(failure_report.get("stage_failures") or [])[-5:]
        if recent:
            st.table(
                [
                    {
                        "stage": item.get("stage"),
                        "type": item.get("error_type"),
                        "attempt": f"{item.get('attempt')}/{item.get('max_attempts')}",
                        "retryable": item.get("retryable"),
                        "reason": item.get("reason"),
                    }
                    for item in recent
                ]
            )
    else:
        st.caption("No standardized failure report found for this run.")
