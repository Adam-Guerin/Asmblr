import os
import time
import json
import html
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import get_settings, previous_secret_allowed
from app.core.llm import check_ollama
from app.core.models import SeedInputs
from app.core.run_manager import RunManager
from app.ui_quality import render_quality_dashboard
from app.core.rate_limit import RateLimiter
from app.core.audit import write_audit_event
from app.onboarding_templates import get_onboarding_templates, get_onboarding_template

settings = get_settings()
if settings.ui_host:
    os.environ.setdefault("STREAMLIT_SERVER_ADDRESS", settings.ui_host)
if settings.ui_port:
    os.environ.setdefault("STREAMLIT_SERVER_PORT", str(settings.ui_port))

import streamlit as st
manager = RunManager(settings.runs_dir, settings.data_dir)
ui_run_limiter = RateLimiter(settings.run_rate_limit_per_min, settings.run_rate_limit_burst)

st.set_page_config(page_title="AI Venture Factory", layout="wide")

st.title("AI Venture Factory")
st.markdown(
    """
<style>
.agent-thinking {
  color: #9ca3af;
  font-size: 0.92rem;
  line-height: 1.45;
  padding: 0.35rem 0.5rem;
  margin: 0.15rem 0;
  border-left: 2px solid rgba(148, 163, 184, 0.45);
  background: linear-gradient(
    110deg,
    rgba(148, 163, 184, 0.08) 8%,
    rgba(255, 255, 255, 0.2) 18%,
    rgba(148, 163, 184, 0.08) 33%
  );
  background-size: 220% 100%;
  animation: thinking-shimmer 2.8s linear infinite;
}
@keyframes thinking-shimmer {
  to {
    background-position: -220% 0;
  }
}
</style>
""",
    unsafe_allow_html=True,
)


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        ts = datetime.fromisoformat(value)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts
    except Exception:
        return None


def _format_delta(seconds: float | None) -> str:
    if seconds is None:
        return "n/a"
    seconds = max(0, int(seconds))
    mins, sec = divmod(seconds, 60)
    hrs, mins = divmod(mins, 60)
    if hrs:
        return f"{hrs}h {mins}m"
    if mins:
        return f"{mins}m {sec}s"
    return f"{sec}s"


def _compute_stats(runs: list[dict]) -> dict:
    now = datetime.now(timezone.utc)
    running = [r for r in runs if r.get("status") == "running"]
    completed = [r for r in runs if r.get("status") in {"completed", "killed", "aborted", "failed"}]
    durations = []
    for run in completed:
        created = _parse_ts(run.get("created_at"))
        updated = _parse_ts(run.get("updated_at"))
        if created and updated:
            durations.append((updated - created).total_seconds())
    avg_duration = sum(durations) / len(durations) if durations else None
    recent_24h = 0
    for run in completed:
        updated = _parse_ts(run.get("updated_at"))
        if updated and (now - updated).total_seconds() <= 86400:
            recent_24h += 1
    return {
        "running": running,
        "completed": completed,
        "avg_duration": avg_duration,
        "recent_24h": recent_24h,
    }


def _job_status(run_id: str) -> dict:
    try:
        from app.core.jobs import get_job_status

        return get_job_status(run_id)
    except Exception:
        return {"status": "unknown", "job_id": None}


def _load_steering_messages(output_dir: Path, limit: int = 10) -> list[dict]:
    path = output_dir / "mvp_steering.jsonl"
    if not path.exists():
        return []
    messages: list[dict] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        raw = line.strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except Exception:
            payload = {"message": raw}
        message = str(
            payload.get("message") or payload.get("prompt") or payload.get("text") or ""
        ).strip()
        if not message:
            continue
        messages.append(
            {
                "timestamp": payload.get("timestamp") or "",
                "author": payload.get("author") or "user",
                "message": message,
            }
        )
    return messages[-limit:]


def _append_steering_message(output_dir: Path, message: str, author: str = "ui") -> None:
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "author": author,
        "message": message.strip(),
    }
    path = output_dir / "mvp_steering.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _collect_agent_trace(output_dir: Path, limit: int = 28) -> list[str]:
    lines: list[str] = []
    progress_log = output_dir / "progress.log"
    if progress_log.exists():
        raw = progress_log.read_text(encoding="utf-8", errors="ignore").splitlines()
        lines.extend(raw[-80:])
    automation_log = output_dir / "mvp_automation.log"
    if automation_log.exists():
        raw = automation_log.read_text(encoding="utf-8", errors="ignore").splitlines()
        lines.extend(raw[-40:])
    if not lines:
        return []
    compact = [line.strip() for line in lines if line.strip()]
    return compact[-limit:]


def _parse_seed_items(value: str) -> list[str]:
    if not value:
        return []
    items: list[str] = []
    for chunk in value.replace(";", ",").replace("\n", ",").split(","):
        cleaned = chunk.strip()
        if cleaned:
            items.append(cleaned)
    return items[:12]


def _init_onboarding_state() -> None:
    st.session_state.setdefault("new_run_topic", "")
    st.session_state.setdefault("new_run_theme", "")
    st.session_state.setdefault("new_run_seed_icp", "")
    st.session_state.setdefault("new_run_seed_pains", "")
    st.session_state.setdefault("new_run_seed_competitors", "")
    st.session_state.setdefault("new_run_seed_context", "")
    st.session_state.setdefault("new_run_n_ideas", settings.default_n_ideas)
    st.session_state.setdefault("new_run_fast_mode", settings.fast_mode)
    st.session_state.setdefault("new_run_execution_profile", "quick" if settings.fast_mode else "standard")

if settings.ui_password:
    if "ui_authenticated" not in st.session_state:
        st.session_state.ui_authenticated = False
    if not st.session_state.ui_authenticated:
        st.subheader("Authentication")
        with st.form("ui_login"):
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in")
        if submitted:
            if password == settings.ui_password:
                st.session_state.ui_authenticated = True
                st.success("Authenticated.")
                st.rerun()
            elif settings.ui_password_prev and password == settings.ui_password_prev:
                prev_allowed, _reason = previous_secret_allowed(
                    previous_value=settings.ui_password_prev,
                    current_value=settings.ui_password,
                    expires_at=settings.ui_password_prev_expires_at,
                    enforce_rotation=settings.enforce_key_rotation,
                )
                if prev_allowed:
                    st.session_state.ui_authenticated = True
                    st.success("Authenticated.")
                    st.rerun()
                else:
                    st.error("Previous password is expired or invalid. Use the current UI password.")
            else:
                st.error("Invalid password.")
        st.stop()

if settings.ui_password:
    with st.sidebar:
        if st.button("Sign out"):
            st.session_state.ui_authenticated = False
            st.rerun()

ollama_error = None
try:
    check_ollama(settings.ollama_base_url, [settings.general_model, settings.code_model])
except Exception as exc:
    ollama_error = exc

if ollama_error:
    st.warning(f"Ollama not ready: {ollama_error}")
    st.markdown("Run the doctor to diagnose environment issues.")
    if st.button("Show doctor command"):
        st.code("python -m app doctor")

runs = manager.list_runs()
stats = _compute_stats(runs)
running_runs = stats["running"]
avg_duration = stats["avg_duration"]

st.subheader("Run status")
col_a, col_b, col_c = st.columns(3)
with col_a:
    st.metric("Active runs", len(running_runs))
with col_b:
    st.metric("Completed (24h)", stats["recent_24h"])
with col_c:
    st.metric("Avg duration", _format_delta(avg_duration))

if running_runs:
    st.caption("Active runs (ETA based on average duration)")
    for run in running_runs[:6]:
        created = _parse_ts(run.get("created_at"))
        elapsed = (datetime.now(timezone.utc) - created).total_seconds() if created else None
        eta = None
        if avg_duration is not None and elapsed is not None:
            eta = max(0, avg_duration - elapsed)
        st.write(
            f"- {run.get('id')} | {run.get('topic')} | elapsed {_format_delta(elapsed)} | ETA {_format_delta(eta)}"
        )
else:
    st.info("No active runs.")

queued_runs = [r for r in runs if r.get("status") == "queued"]
if queued_runs:
    st.caption("Queued runs (position + ETA based on average duration)")
    for run in queued_runs[:6]:
        job = _job_status(run.get("id"))
        position = job.get("position")
        queue_total = job.get("queue_total")
        eta = None
        if avg_duration is not None and position is not None:
            eta = avg_duration * max(0, position)
        st.write(
            f"- {run.get('id')} | {run.get('topic')} | pos {position if position is not None else 'n/a'}/{queue_total or 'n/a'} | ETA {_format_delta(eta)}"
        )
view_mode = st.sidebar.radio("View selector", ["Run archive", "Quality dashboard"])

if "active_run_id" not in st.session_state:
    st.session_state.active_run_id = None

with st.expander("New run (guided)", expanded=False):
    _init_onboarding_state()
    templates = get_onboarding_templates()
    template_options = list(templates.keys())
    selected_template_id = st.radio(
        "Parcours onboarding",
        template_options,
        format_func=lambda key: templates[key]["label"],
        horizontal=True,
        key="new_run_template_id",
    )
    selected_template = templates[selected_template_id]
    st.caption(selected_template.get("description", ""))
    if st.button("Appliquer ce parcours"):
        applied = get_onboarding_template(selected_template_id)
        st.session_state.new_run_topic = applied.get("topic", "")
        st.session_state.new_run_theme = applied.get("theme", "")
        st.session_state.new_run_seed_icp = applied.get("seed_icp", "")
        st.session_state.new_run_seed_pains = "\n".join(applied.get("seed_pains", []))
        st.session_state.new_run_seed_competitors = "\n".join(applied.get("seed_competitors", []))
        st.session_state.new_run_seed_context = applied.get("seed_context", "")
        st.session_state.new_run_n_ideas = int(applied.get("n_ideas", settings.default_n_ideas))
        st.session_state.new_run_fast_mode = bool(applied.get("fast_mode", settings.fast_mode))
        st.success("Parcours applique. Lance le run pour obtenir un premier MVP pertinent rapidement.")
        st.rerun()

    topic = st.text_input("Topic", key="new_run_topic")
    theme = st.text_input("Theme de l'idee (avant scraping, optionnel)", key="new_run_theme")
    seed_icp = st.text_input("Seed ICP (optional)", key="new_run_seed_icp")
    seed_pains = st.text_area(
        "Seed pains (1 par ligne, ou virgules)",
        key="new_run_seed_pains",
        height=96,
    )
    seed_competitors = st.text_area(
        "Seed competitors (1 par ligne, ou virgules)",
        key="new_run_seed_competitors",
        height=96,
    )
    seed_context = st.text_area("Seed context (optional)", key="new_run_seed_context", height=80)
    n_ideas = st.number_input("Number of ideas", min_value=1, max_value=20, key="new_run_n_ideas")
    fast_mode = st.checkbox("Fast mode", key="new_run_fast_mode")
    execution_profile = st.selectbox(
        "Execution profile",
        ["quick", "standard", "deep"],
        key="new_run_execution_profile",
        help="Defines explicit run budgets (time/token) and run depth.",
    )
    start_run = st.button("Start run")

    if start_run:
        if not topic.strip():
            st.error("Topic is required.")
        elif not ui_run_limiter.allow("ui"):
            st.error("Rate limit exceeded. Please wait before starting another run.")
        else:
            run_id = manager.create_run(topic.strip())
            seeds = SeedInputs(
                icp=seed_icp.strip() or None,
                pains=_parse_seed_items(seed_pains),
                competitors=_parse_seed_items(seed_competitors),
                context=seed_context.strip() or None,
                theme=theme.strip() or None,
            )

            from app.core.jobs import enqueue_run

            enqueue_run(
                run_id=run_id,
                topic=topic.strip(),
                n_ideas=int(n_ideas),
                fast=fast_mode,
                seeds=seeds,
                webhook_url=None,
                execution_profile=execution_profile,
            )
            manager.update_status(run_id, "queued")
            job = _job_status(run_id)
            st.session_state.active_run_id = run_id
            write_audit_event(
                Path(settings.audit_log_file),
                {
                    "event": "run_start",
                    "run_id": run_id,
                    "topic": topic.strip(),
                    "n_ideas": int(n_ideas),
                    "fast": fast_mode,
                    "theme": theme.strip() or None,
                    "seed_icp": seed_icp.strip() or None,
                    "seed_pains": _parse_seed_items(seed_pains),
                    "seed_competitors": _parse_seed_items(seed_competitors),
                    "seed_context": seed_context.strip() or None,
                    "onboarding_path": selected_template_id,
                    "execution_profile": execution_profile,
                    "actor": "ui",
                    "job_id": job.get("job_id"),
                },
            )
            write_audit_event(
                Path(settings.audit_log_file),
                {
                    "event": "run_queued",
                    "run_id": run_id,
                    "job_id": job.get("job_id"),
                    "execution_profile": execution_profile,
                    "actor": "ui",
                },
            )
            st.success(f"Run started: {run_id}")


if view_mode == "Quality dashboard":
    render_quality_dashboard(settings, manager, runs)
else:
    if not runs:
        st.info("No runs yet. Use the CLI or API to start one.")
    else:
        run_ids = [r["id"] for r in runs]
        selected = st.selectbox("Select run", run_ids)
        run = manager.get_run(selected)
        st.write(run)

        output_dir = Path(run["output_dir"])
        with st.expander("Live steering chat", expanded=run.get("status") in {"queued", "running"}):
            st.caption(
                "Ajoute un prompt de réorientation. Il sera pris en compte au prochain cycle MVP."
            )
            show_trace = st.checkbox(
                "Afficher le mode thinking (trace agent)",
                value=True,
                key=f"show_thinking_{selected}",
            )
            if show_trace:
                st.caption("Trace de travail en direct (synthèse d'exécution, pas de raisonnement interne brut).")
                trace_lines = _collect_agent_trace(output_dir, limit=24)
                if trace_lines:
                    for line in trace_lines:
                        st.markdown(
                            f"<div class='agent-thinking'>{html.escape(line)}</div>",
                            unsafe_allow_html=True,
                        )
                else:
                    st.info("Pas encore de trace agent pour ce run.")
            steering_messages = _load_steering_messages(output_dir, limit=12)
            if steering_messages:
                for msg in steering_messages:
                    stamp = msg.get("timestamp") or "unknown-time"
                    st.markdown(f"**{msg.get('author', 'user')}** ({stamp})")
                    st.markdown(msg.get("message", ""))
            else:
                st.info("Aucun message de réorientation pour ce run.")
            with st.form(f"steering_form_{selected}"):
                steering_prompt = st.text_area(
                    "Prompt de réorientation",
                    value="",
                    height=100,
                    placeholder="Ex: pivote vers une cible freelance et simplifie le flow onboarding.",
                )
                send_steering = st.form_submit_button("Envoyer")
            if send_steering:
                if not steering_prompt.strip():
                    st.error("Le prompt est vide.")
                else:
                    cleaned = steering_prompt.strip()[:2000]
                    _append_steering_message(output_dir, cleaned, author="founder")
                    write_audit_event(
                        Path(settings.audit_log_file),
                        {
                            "event": "run_steering_message",
                            "run_id": selected,
                            "status": run.get("status"),
                            "message_len": len(cleaned),
                            "actor": "ui",
                        },
                    )
                    st.success("Prompt enregistré. Il sera consommé par le cycle en cours/prochain.")
                    st.rerun()

        st.subheader("Artifacts")
        status = run.get("status", "")
        if status in ("aborted", "killed"):
            reason_file = output_dir / ("abort_reason.md" if status == "aborted" else "kill_reason.md")
            if reason_file.exists():
                st.markdown(f"### {status.upper()} reason")
                st.markdown(reason_file.read_text(encoding="utf-8"))
        for artifact in [
            "top_idea.md",
            "market_report.md",
            "prd.md",
            "tech_spec.md",
            "launch_checklist.md",
        ]:
            path = output_dir / artifact
            if path.exists():
                st.markdown(f"### {artifact}")
                st.markdown(path.read_text(encoding="utf-8"))

        landing_dir = output_dir / "landing_page"
        if (landing_dir / "index.html").exists():
            st.subheader("Landing Page")
            st.code((landing_dir / "index.html").read_text(encoding="utf-8")[:2000])

        content_dir = output_dir / "content_pack"
        if content_dir.exists():
            st.subheader("Content Pack")
            posts = content_dir / "posts.md"
            if posts.exists():
                st.markdown(posts.read_text(encoding="utf-8"))
        golden_root = settings.runs_dir / "_golden"
        if golden_root.exists():
            gems = sorted(
                [entry for entry in golden_root.iterdir() if entry.is_dir()],
                key=lambda p: p.name,
                reverse=True,
            )
            if gems:
                st.subheader("Golden runs")
                for golden in gems:
                    uri = golden.resolve().as_uri()
                    st.markdown(f"- [{golden.name}]({uri})")

    if st.session_state.active_run_id:
        st.subheader("Live progress")
        run = manager.get_run(st.session_state.active_run_id)
        if run:
            log_path = Path(run["output_dir"]) / "progress.log"
            if log_path.exists():
                content = log_path.read_text(encoding="utf-8", errors="ignore")
                lines = content.splitlines()
                tail = "\n".join(lines[-200:])
                st.text_area("Progress log (tail)", value=tail, height=220)
            else:
                st.info("Progress log not available yet.")
            if st.button("Refresh progress"):
                time.sleep(0.1)
