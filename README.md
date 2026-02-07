# 🚀 Asmblr - AI-Powered MVP Generator

Local, multi-agent venture pipeline built on CrewAI + LangChain, running on Ollama (no paid APIs). Produces a launch-ready package: market report, PRD, tech spec, repo skeleton, landing page, and content pack.

## ✨ Quick Start (Recommended)

```bash
# 1. Run the automated setup script
python setup.py

# 2. Start the UI
streamlit run app/ui.py

# 3. Open http://localhost:8501 and generate your first MVP!
```

The setup script will:
- Install all Python dependencies
- Install and configure Ollama
- Download required AI models
- Create necessary directories
- Verify everything is working

## 🎯 Features
- **CrewAI orchestrator** (Researcher -> Analyst -> Product -> Tech Lead -> Growth)
- **LangChain tools** used by agents (web, scoring, RAG, generators)
- **Ollama local LLMs** (CPU-only supported; AMD ROCm optional)
- **Modern Streamlit UI** for easy interaction
- **Automated setup** script for zero-config installation
- **MVP generation** with progressive cycles (foundation -> ux -> polish)
- **FastAPI API** + CLI interface
- **SQLite + file artifacts** in `/runs`
- **Configurable sources, prompts, thresholds`

## ICP Focus (Niche-first)
Asmblr can enforce one primary ICP across idea generation, scoring, PRD, and growth copy.

Set in `.env`:
```bash
PRIMARY_ICP="Founders B2B SaaS pre-seed"
PRIMARY_ICP_KEYWORDS="founder,founders,b2b,saas,pre-seed,startup,startups,small team,operators"
ICP_ALIGNMENT_BONUS_MAX=8
IDEA_ACTIONABILITY_MIN_SCORE=55
IDEA_ACTIONABILITY_ADJUSTMENT_MAX=12
IDEA_ACTIONABILITY_REQUIRE_ELIGIBLE_TOP=false
```

This adds an ICP alignment bonus/malus during scoring and pushes agents to keep outputs tied to that segment.
It also computes `idea_actionability.json` and downranks generic ideas that lack a clear early validation path.

## Frontend Quality: Lovable-grade
Every MVP ships with a deterministic frontend kit and UI quality gates:
- **Stack**: Next.js App Router + TypeScript + Tailwind CSS + shadcn/ui (Radix) + lucide-react
- **Design system**: light-first palette, soft gradients, consistent spacing/radius/shadow tokens
- **Progressive UI cycles**: foundation -> ux -> polish (build + UI lint enforced every cycle)
- **UX polish**: loading, empty, error states, toasts, and form validation microcopy
- **Accessibility**: WCAG 2.1 AA contrast heuristics built into UI lint

Preview a generated MVP UI:
```bash
cd runs/<run_id>/mvp_repo
npm install
npm run dev
```

Build an MVP with the frontend kit:
```bash
python -m app build-mvp --run-id <run_id> --frontend-style startup_clean
```

## Quickstart (local)
```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

# Run a pipeline
python -m app run --topic "AI compliance for SMBs" --n_ideas 10
```

## Local prerequisites
Install Ollama and verify it runs:
```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Download from https://ollama.com/download and run installer
```

Pull required models (configurable in `.env`):
```bash
ollama pull llama3.1:8b
ollama pull qwen2.5-coder:7b
```

The pipeline will NOT run if Ollama is missing or models are not pulled.

## Getting to green
1) Create a Python environment and install dependencies
```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
2) Run the doctor (fails until Ollama is ready; it prints the exact install/start/pull commands for your OS)
```bash
python -m app doctor
```
3) Install and start Ollama

- **macOS/Linux**
  ```bash
  curl -fsSL https://ollama.com/install.sh | sh
  ollama serve --port 11434 --listen http://localhost:11434
  ```

- **Windows**
  ```powershell
  # Download from https://ollama.com/download and run the installer
  ollama serve --port 11434
  ```

4) Pull the required models and recheck Ollama with the helper scripts (they also restart Ollama if needed)
```bash
# macOS/Linux
./scripts/setup_ollama.sh

# Windows PowerShell
./scripts/setup_ollama.ps1
```
5) Re-run the doctor (should now report green)
```bash
python -m app doctor
```
6) Run the pipeline once Ollama is healthy
```bash
python -m app run --topic "Internal Audit Gate" --fast
```

## Unified Quality Gate
Use one command for lint + tests + smoke MVP generation:

```bash
python scripts/test_all.py --mode quick
```

Run full suite:

```bash
python scripts/test_all.py --mode full
```

If `make` is available:

```bash
make test
```

## Operations

### How to restart
- UI (Streamlit):
  ```bash
  streamlit run app/ui.py
  ```
- API (FastAPI):
  ```bash
  uvicorn app.main:app --host 127.0.0.1 --port 8000
  ```
- Docker Compose:
  ```bash
  docker compose up --build
  ```

### How to diagnose
- Environment check:
  ```bash
  python -m app doctor
  ```
- API health:
  ```bash
  curl http://localhost:8000/healthz
  curl http://localhost:8000/readyz
  ```
- Logs:
  - Set `LOG_JSON=true` in `.env` for structured logs.
  - Run audit log: `data/audit.log`
- Metrics:
  - JSON snapshot: `GET /metrics`
  - Prometheus: `GET /metrics/prometheus`

### Run recovery
- Resume a failed/interrupted run:
  ```bash
  python -m app resume --run-id <run_id>
  ```
- Inspect run state:
  - `runs/<run_id>/run_state.json`
  - `runs/<run_id>/progress.log`

## Docker option
```bash
docker compose up --build
```
Services:
- Ollama on http://localhost:11434 (bring your own models in the Ollama service)
- Redis on localhost:6379
- Worker on background queue
- API on http://localhost:8000
- UI on http://localhost:8501
Worker health:
- http://localhost:8001/healthz
- http://localhost:8001/readyz

Resource limits (best effort) are defined in `docker-compose.yml`. Tune:
- `mem_limit` / `cpus` per service
- App concurrency via `RUN_MAX_CONCURRENT` (default 1)

Models: `llama3.1:8b`, `qwen2.5-coder:7b` (pull before container use if you prefer local Ollama cache)

## Ollama models
Recommended (configurable in `.env`):
- General: `llama3.1:8b` or `qwen2.5:7b-instruct`
- Code: `qwen2.5-coder:7b` or `deepseek-coder:6.7b`

Pull models:
```bash
ollama pull llama3.1:8b
ollama pull qwen2.5-coder:7b
```

## CLI
```bash
python -m app run --topic "Customer support automation" --n_ideas 10
python -m app run --topic "FinOps insights" --fast
python -m app run --topic "Founder workflow automation" --profile quick
python -m app run --topic "B2B procurement intelligence" --profile deep
python -m app golden-run --topic "Audit-ready topic"
```

## Fast Mode
Fast mode reduces cost/time by:
- forcing `n_ideas=3`
- limiting sources to 3
- generating a minimal repo skeleton
- shorter landing and content pack (3 posts, 2 hooks, 1 ad)

## Execution Profiles (Predictable Local Cost)
Each run can use one explicit execution profile with fixed budgets:

- `quick`: 12 min, ~18k token est, max 3 ideas, max 3 sources
- `standard`: 35 min, ~60k token est, max 10 ideas, max 8 sources
- `deep`: 75 min, ~140k token est, max 20 ideas, max 12 sources

How to use:
- CLI: `python -m app run --topic "..." --profile quick|standard|deep`
- API: pass `execution_profile` in `POST /run`
- UI: select `Execution profile` in `New run (guided)`

Per-run budget telemetry is written to:
- `runs/<run_id>/run_budget.json`

## Onboarding (<10 min to first value)
In the Streamlit UI (`New run (guided)`), use one of the 3 onboarding paths:
- `Idee floue`
- `Idee validee`
- `Copie concurrent`

Each path pre-fills `seed_icp`, `seed_pains`, and `seed_competitors` templates to speed up first MVP relevance.

## Robustness (Retries)
HTTP fetches use exponential backoff retries for timeouts and 429/5xx responses. Configure via:
- `RETRY_MAX_ATTEMPTS`
- `RETRY_MIN_WAIT`
- `RETRY_MAX_WAIT`

## ABORT vs KILL
- **ABORT** = data insufficient (no product artifacts generated)
- **KILL** = idea evaluated and rejected despite sufficient data

The system enforces: **NO DATA -> NO PRODUCT**. If data is partial, the run is aborted before PRD/Tech/Growth.
This tool refuses to generate products without external data.
KILL is a success state for internal decision-making.

## Data source tagging
Each generated artifact is tagged with `Data source: real|fallback` and a `data_source.json` is written to the run folder.

## How Citations Are Generated
`market_report.md` always includes **Sources (collected)** from pre-run scraping, plus optional **Sources (LLM referenced)** if the CrewAI Researcher returns pages.

## API
- `POST /run` with `{ "topic": "...", "n_ideas": 10, "fast": false }`
- `GET /run/{id}`
- `GET /run/{id}/artifact/{name}`
- `POST /run/{id}/feedback-metrics` with `{ "ctr_landing": 0.03, "signup_rate": 0.1, "activation_rate": 0.25, "visitors": 500 }` (ratio `0..1` or percent `0..100`)

## Outputs
Each run produces:
- `opportunities.json`
- `top_idea.md`
- `market_report.md`
- `prd.md`
- `tech_spec.md`
- `repo_skeleton/`
- `landing_page/`
- `content_pack/`
- `launch_checklist.md`
- `seed_context.json` (seed hypotheses tagged as `data_source=seed`)
- `pains_validated.json` (quality-filtered pain statements with metadata)
- `market_signal_score.json` (0–100 signal score + rationale)
- `decision.md` (PASS/ABORT justification referencing signals and hypotheses)
- `confidence.json` (global 0–100 reliability score + rubric)
- `devils_advocate.md` + `devils_advocate.json` (Devil's Advocate critique)
- `raw_pages.json` (multi-pass scrape output with pass_type, signal_score, and canonical metadata)
- `pages_deduped.json` (SimHash-based groups + canonical page pick per cluster)
- `pains_structured.json` (structured pains with actor/context/problem/signal metrics)
- `pain_clusters.json` (job-to-be-done cluster metadata + keywords)
- `opportunities_structured.json` (cluster-derived opportunity hypotheses with linked pain IDs)
- `novelty_score.json` (novelty heuristics: keywords, multi-platform ratio, recency)
- `signal_quality.json` (0–100 signal quality breakdown that feeds the signal gate)

## Signal Engine V2

- **Multi-pass scraping**: each configured source is visited via _recent_, _top_, and keyword search passes, producing `raw_pages.json` with `{url, title, source_name, pass_type, signal_score, text}` so you capture freshness, signals, and engagement hints.
- **Deduplication & canonicalization**: a SimHash-like fingerprint groups similar pages; `pages_deduped.json` keeps the canonical century-long page and its duplicates (longer text + higher signal score wins) so downstream pain extraction sees clean, unique signals.
- **Pipeline impact**: the deduplicated set feeds `_extract_pain_statements`, while the raw JSON remains available for auditors, novelty heuristics, and future scoring layers.
- **Structured pains**: we now parse structured statements with actor, context, signal metrics, and write them to `pains_structured.json`, ensuring every candidate contains an actor and a concrete problem.
- **Job clustering & opportunities**: `pain_clusters.json` groups those pains into job-to-be-done clusters by TF-IDF + KMeans and `opportunities_structured.json` emits 2–3 hypotheses per cluster linked back to the original pain IDs, so traceability expands beyond simple text scoring.
- **Novelty heuristics & signal quality**: `novelty_score.json` captures new keywords, multi-platform modes, and recency ratios, while `signal_quality.json` consolidates volume, diversity, repetition, clustering density, and novelty into a 0–100 score that PreRunGate requires to exceed `SIGNAL_QUALITY_THRESHOLD`.
- PreRunGate now enforces this combined score via the `SIGNAL_QUALITY_THRESHOLD` setting (default 45), so you can tune the gate by editing `.env` (or set it to 0 in quick test runs).

## Verdict taxonomy
- **ABORT** -> insufficient or fallback data; pipeline stops before PRD/Tech/landing/content.
- **KILL** -> data is real but confidence (pre-artifact and traceability signals) falls below the configured `KILL_THRESHOLD` (55 by default); PRD/Tech/landing/content are never emitted, and `kill_reason.md` records why.
- **PASS** -> real data and high confidence, so the run produces PRD/Tech specs, repo scaffolding, and launch assets while documenting the rationale in `decision.md`.

## How Asmblr makes better decisions
- **Input seeding**: pass `--seed-icp`, `--seed-pains`, `--seed-competitors`, and `--seed-context` to `python -m app run` so your hypotheses are persisted in `seed_context.json` and the CrewAI Researcher sees `data_source=seed` cues without replacing the real scrape.
- **Pain quality filter**: every scraped sentence that mentions actor, context, and concrete difficulty survives into `pains_validated.json`; generic statements are recorded and dropped before scoring.
- **Market signal score**: counts of sources, distinct pains, repeat mentions, and domain diversity are consolidated into `market_signal_score.json` (0–100); pipelines abort before idea generation if the score is below `MARKET_SIGNAL_THRESHOLD` to avoid weak signals.
- **Idea traceability & decision file**: ideas must carry `pain_ids`, `sources`, and `hypotheses`. If that metadata is missing the run aborts, otherwise `decision.md` records whether the run PASSed or ABORTed, which signals were used, and what hypotheses remain unverified.
- **Abort early, no fake products**: whenever `abort_reason.md` triggers, `decision.md` makes the failure transparent and no PRD/Tech/launch assets are emitted until signal strength and traceability are solid.

## Confidence score
- Each run writes `confidence.json` with a 0–100 score derived from LLM health, data coverage, pain quality, competitor evidence, traceability, and artifact integrity. The same breakdown is mirrored in the `Confidence Score` section appended to `decision.md`.
- Aborted runs default to 0, fallback decisions are capped at 25, and any “unknown” data sources further reduce the score; reasons and caps are stored in the JSON for easy machine consumption.
- Confidence is entirely self-contained in `runs/<run_id>/confidence.json` (no network), so identical inputs always yield the same score and you can audit reliability before trusting generated artifacts.

## Critique (Devil's Advocate)
- Run `python -m app critique --run-id <run_id> [--mode strict|standard]` once a run reaches the “completed” status. Ollama must be running because the critique uses the same local models as the pipeline.
- The meta-agent reads `market_report.md`, `competitor_analysis.json`, `prd.md`, `tech_spec.md`, optional landing and content packs, `decision.md`, and `confidence.json` to inform the JSON verdict. Any missing competitor evidence, fallback artifacts, or confidence below 50 forces the verdict to ITERATE/KILL.
- Outputs `runs/<run_id>/devils_advocate.json` (machine-readable verdict, top risks, contradictions, and killer experiment) and `runs/<run_id>/devils_advocate.md` (markdown critique citing the files consumed). Treat those files as a hard post-run critique before shipping any artifacts.

## Quality Dashboard

- Launch the Streamlit UI (`streamlit run app/ui.py`) and switch to the **Quality dashboard** view in the sidebar.
- KPIs surface the percentage of ABORTED / KILLED / COMPLETED runs, the average confidence score for completed runs, the top five abort reasons pulled from `abort_reason.md`, and the top five missing artifacts tracked across the archive.
- The ledger table lists `run_id`, date, topic, status, confidence, decision, and signal score for every run, and each row includes a direct link to `runs/<run_id>` for quick inspection.
- Drill into any run to see its `decision.md`, the confidence breakdown, and the Devil’s Advocate verdict so you can understand why the system PASSed, KILLED, or ABORTed the idea.
- The dashboard tolerates partial artifacts, avoids failures when files are missing, and writes an optional cache at `runs/_metrics_index.json` so refreshes stay responsive.

## Golden runs

- Run `python -m app golden-run --topic "<topic>"` to produce an audit-ready snapshot once a run finishes with status `completed` or `killed`; golden runs are skipped on `ABORT`.
- Each snapshot copies `runs/<run_id>` into `runs/_golden/<timestamp>_<run_id>`, never overwrites previous folders, and records metadata in `runs/_golden/latest.json`.
- The Golden runs section in the Streamlit UI lists those folders so you can click through an audited artifact package just like a normal run.

## Config
- `configs/sources.yaml` (scraped sources)
- `configs/thresholds.yaml`
- `app/prompts/` (LLM prompts)
- `knowledge/` (RAG playbook)

## Scheduler / Batch
Example cron (Linux):
```
0 9 * * * cd /path/to/repo && . .venv/bin/activate && python -m app run --topic "Daily trend scan" --fast
```
Windows Task Scheduler: run `scripts/run_daily.bat`.

## AMD ROCm (optional)
If using ROCm, ensure your drivers and ROCm stack are installed. Ollama supports ROCm on compatible AMD GPUs. If ROCm is not available, the pipeline falls back to CPU-only.

## Tests
```bash
pytest -q
```

## Troubleshooting
- If Ollama is not reachable, set `OLLAMA_BASE_URL` in `.env`.
- If scraping fails, sources may block robots.txt. Use different sources.
- For CPU-only, reduce `MAX_SOURCES` and use `--fast`.

## Asmblr Loop (Ralph-like)

- **Purpose**: run a controlled “plan -> patch -> verify -> checkpoint” cycle with Ollama prompts, automated logging, and git checkpoints.
- **Safety guardrails**: loops abort if Ollama fails, a patch touches `.env`, binary diff is detected, tests fail, or the aggregate diff exceeds 500 lines (configurable via `LoopConfig`). The `NO DATA -> NO PRODUCT` principle is preserved because the loop can only adjust infrastructure/robustness and never generate fallback artifacts.

### Run the loop
```bash
python -m app loop \
  --goal "Improve dependency management" \
  --max-iter 3 \
  --tests "python -m pytest -q" \
  --approve-mode auto
```

- Use `--dry-run` to collect plan+patch artifacts without applying changes.
- Use `--approve-mode manual` to stop before applying a patch and confirm interactively (type `y` to approve).
- Each iteration writes `plan.md`, `patch.diff`, `apply.log`, `test.log`, `verdict.json`, `files_touched.json`, and `rollback_hint.md` under `runs/<run_id>/loop/iter_<k>/`.
- Loop reports “completed” only when tests pass, no infra aborts occurred, and the diff stays within budget.

### Rollback
```bash
python -m app loop-rollback --run-id 20260126_120000_000000 --to-iter 2
```
This runs `git reset --hard <commit>` to return to the checkpoint of the given iteration.

### Limitations
- Default budgets: 3 iterations, 500 total diff lines, 200 lines per iteration.
- Git is required; if the working tree is dirty, the loop creates a dedicated worktree while leaving untracked changes untouched.
- Patches are vetted for path traversal, `.env` touches, binary blobs, and “TODO” comments are discouraged by the prompt.

## Ralph Loop (anti context-rot)
- Create `prd.json` from `prd.json.example`, then update `progress.txt` each iteration.
- Run `python -m app ralph-loop --max-iter 3 --tests "pytest -q"` or use `scripts/ralph/ralph.ps1`.
- The loop picks the next `passes=false` story, runs a single iteration, appends to `progress.txt`, and marks the story as passed on success.
## Build MVP (independent)
- Use `python -m app build-mvp --run-id <run_id> [--force] [--cycles foundation,ux,polish] [--max-fix-iter 5]` to regenerate `mvp_repo/` and `mvp_cycles/` inside an existing run—even if it was `ABORT` or `KILLED`. The command marks the provenance in `mvp_data_source.json` (e.g., `data_source=seed/abort`) so auditors know this prototype is a fallback.
- Use `python -m app build-mvp --brief "<one-line idea>" --output runs/_adhoc/<timestamp>/` to create a completely new run that seeds the generator from a brief. The builder writes `mvp_scope.json` with the brief, cycle plan, and stack selection so the run is self-describing.
- Each execution creates or overwrites `mvp_repo/`, the `mvp_cycles/cycle_<n>_*/` folders, `mvp_build_summary.md`, and `mvp_data_source.json`. `mvp_cycles` always contains `plan.md`, `patch.diff`, `patch.log`, `build.log`, `test.log`, and `verdict.json` per cycle so you can inspect how foundation -> ux -> polish progressed (even when builds fail).
- The builder uses a deterministic stack selector (Next.js + Tailwind + shadcn-style UI, Prisma + SQLite or FastAPI + SQLite depending on the brief) to scaffold a working `mvp_repo/` that runs `npm install`, `npm run build`, and `npm run dev`. The summary emphasises “prototype built” rather than market validation and records the cycle outcomes in `mvp_build_summary.md`.
- `--force` removes existing `mvp_repo`/`mvp_cycles` before scaffolding, `--cycles` limits which phases run, and `--max-fix-iter` controls how many auto-fix attempts the cycle runner performs when builds/tests fail.

## Progressive MVP Cycles
- Foundation cycle (`cycle_1_foundation`) now uses `app/prompts/mvp/foundation_prompt.txt` to generate a git diff scoped to `mvp_repo/`, writes that diff to `patch.diff`, logs the prompt/plan in `patch.log`, and applies the addition so `runs/<run_id>/mvp_repo/foundation_notes.md` captures the baseline goals.
- When `ENABLE_PROGRESSIVE_CYCLES=true` (default) the PASS flow writes `runs/<run_id>/mvp_cycles/cycle_<n>_<name>` folders containing `plan.md`, `patch.diff`, `patch.log`, `build.log`, and `test.log`, so you can trace how the repo evolves through foundation -> ux -> polish without resetting the worktree.
- Set `MVP_BUILD_COMMAND` and `MVP_TEST_COMMAND` (empty by default) to run your actual build/test steps inside `runs/<run_id>/mvp_repo`; each cycle writes the command output, return code, and any stderr to `build.log`/`test.log` so the progress is auditable.

## Project build playbook
- Once the pipeline confirms a PASS, it creates `runs/<run_id>/project_build/vision_roadmap.md` that summarizes the vision, roadmap, stack, and key opportunities so the idea traceability continues into implementation.
- Inside that directory the `app/` scaffold carries `stack_config.json`, a frontend README/`index.html`, and a backend `main.py`/`requirements.txt` that follow the stack identified in the tech specification (Next.js + FastAPI + SQLite by default). Treat these files as the starting point for the MVP implementation.
- The project directory is initialized as a git repository (`.git/`) with an initial commit so every new startup workspace is versioned independently; use `runs/<run_id>/project_build` as the canonical repo for further development or automated cycles.

## Architecture (Option A)
- **CrewAI** is the orchestrator and runs the full pipeline in `app/agents/crew.py`
- **LangChain** provides tool wrappers in `app/langchain_tools.py`
- **Ollama** provides local LLM inference (no paid APIs)
