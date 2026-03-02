# 🚀 Asmblr - AI-Powered MVP Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20AI-green.svg)](https://ollama.ai/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Web%20UI-red.svg)](https://streamlit.io/)

> **Transform your ideas into launch-ready MVPs with AI-powered automation — no paid APIs required.**

Asmblr is a local, multi-agent venture pipeline built on CrewAI + LangChain, running on Ollama. From a single topic it produces a complete launch package: market report, PRD, tech spec, repo skeleton, landing page, and content pack.

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
  - [Web Interface](#web-interface)
  - [Command Line](#command-line)
  - [API](#api)
- [Execution Profiles](#-execution-profiles)
- [Generated Artifacts](#-generated-artifacts)
- [Architecture](#-architecture)
- [Configuration](#-configuration)
- [Deployment](#-deployment)
- [Monitoring](#-monitoring)
- [Advanced Features](#-advanced-features)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### 🤖 AI-Powered Pipeline
- **Multi-Agent System**: Researcher → Analyst → Product → Tech Lead → Growth agents
- **Local AI Models**: Runs entirely on your machine with Ollama (no API costs)
- **Smart Signal Processing**: Multi-pass web scraping with SimHash deduplication
- **Automated Decision Making**: Intelligent PASS/ABORT verdicts with confidence scoring

### 📊 Comprehensive Output
- **Market Research**: Detailed market reports with competitive analysis and pain clustering
- **Product Requirements**: Complete PRDs with feature specifications and traceability
- **Technical Architecture**: Tech specs and implementation guidance
- **Code Generation**: Repository skeletons with modern tech stacks (Next.js + FastAPI)
- **Marketing Assets**: Landing pages and content packs ready for launch

### 🎯 Production-Ready Features
- **Progressive MVP Cycles**: Foundation → UX → Polish iterations with build/test gates
- **Quality Gates**: Automated signal quality checks before committing resources
- **Frontend Kit**: Next.js App Router + TypeScript + Tailwind CSS + shadcn/ui
- **Performance Optimized**: LLM caching, async workers, connection pooling
- **Security First**: Input validation, rate limiting, audit logging

---

## 🚀 Quick Start

```bash
# 1. Run the automated setup script
python setup.py

# 2. Start the UI
streamlit run app/ui.py

# 3. Open http://localhost:8501 and generate your first MVP!
```

The setup script installs Python dependencies, Ollama, required AI models, and verifies everything is working.

---

## ⚡ Performance Optimizations (v2.0+)

### **Phase 1: Architecture Optimization**
- **43.64% token reduction** with optimized A7-A11 architectures
- **30% dependency cleanup** for faster installation
- **Smart architecture selection** based on context complexity

### **Phase 2: Dynamic Performance**
- **Dynamic Model Selection**: Fast/Balanced/Accurate profiles
- **Smart Cache Layer**: TTL-based caching with hit tracking
- **Real-time Monitoring**: Event-driven performance metrics

### **Phase 3: Enterprise Scale**
- **Multi-tenant Manager**: Isolated tenant contexts
- **Marketplace Deployment**: One-click deployment manifests
- **Advanced Analytics**: Tenant-level rollups and insights

### **Benchmark Results**
```
Architecture Performance (Token Efficiency):
- A11: 43.64% reduction vs baseline
- A10: 41.2% reduction vs baseline  
- A9: 38.7% reduction vs baseline
- A8: 35.1% reduction vs baseline
- A7: 32.4% reduction vs baseline
```

---

## 🛠️ Installation

### Prerequisites
- Python 3.9 or higher
- [Ollama](https://ollama.ai/) installed and running
- 8 GB+ RAM recommended

### Automated Setup (Recommended)

```bash
git clone https://github.com/Adam-Guerin/Asmblr.git
cd Asmblr
python setup.py
```

### Manual Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
# .venv\Scripts\activate        # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and edit the environment file
cp .env.example .env

# 4. Install Ollama and pull required models
curl -fsSL https://ollama.com/install.sh | sh   # Linux / macOS
# Download from https://ollama.com/download      # Windows

ollama pull llama3.1:8b
ollama pull qwen2.5-coder:7b
```

### Getting to Green

```bash
# Check that your environment is ready
python -m app doctor

# Run the pipeline once Ollama reports healthy
python -m app run --topic "AI compliance for SMBs" --fast
```

---

## 🎮 Usage

### Web Interface

```bash
streamlit run app/ui.py
```

Navigate to http://localhost:8501, then:

1. **Choose an onboarding path**: *Vague idea*, *Validated idea*, or *Competitor analysis*
2. **Configure settings**: Adjust ICP, sources, and quality thresholds
3. **Generate MVP**: Watch the agents work in real time
4. **Review results**: Explore artifacts in the **Quality dashboard**

### Command Line

```bash
# Standard run
python -m app run --topic "Customer support automation" --n_ideas 10

# Fast mode (3 ideas, 3 sources, minimal output)
python -m app run --topic "FinOps insights" --fast

# Execution profile
python -m app run --topic "B2B procurement intelligence" --profile deep

# Golden run (audit-ready snapshot)
python -m app golden-run --topic "Audit-ready topic"

# Resume an interrupted run
python -m app resume --run-id <run_id>

# Post-run critique
python -m app critique --run-id <run_id> --mode strict
```

### API

```bash
# Start the API server
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/run` | Start a new pipeline run |
| `GET` | `/run/{id}` | Get run status |
| `GET` | `/run/{id}/artifact/{name}` | Retrieve a generated artifact |
| `POST` | `/run/{id}/feedback-metrics` | Submit feedback metrics |

```python
import httpx

response = httpx.post("http://localhost:8000/run", json={
    "topic": "AI-powered customer support",
    "n_ideas": 10,
    "fast": False
})
run_id = response.json()["run_id"]
```

---

## ⚡ Execution Profiles

Each profile sets fixed budgets for predictable local resource use:

| Profile | Time | Est. Tokens | Ideas | Sources |
|---------|------|-------------|-------|---------|
| `quick` | ~12 min | ~18k | 3 | 3 |
| `standard` | ~35 min | ~60k | 10 | 8 |
| `deep` | ~75 min | ~140k | 20 | 12 |

Use with `--profile quick|standard|deep` (CLI), `execution_profile` (API), or the *Execution profile* dropdown (UI).

Per-run budget telemetry is written to `runs/<run_id>/run_budget.json`.

---

## 📦 Generated Artifacts

Each run writes artifacts under `runs/<run_id>/`:

| Artifact | Description |
|----------|-------------|
| `market_report.md` | Competitive market analysis with cited sources |
| `prd.md` | Product requirements document |
| `tech_spec.md` | Technical architecture and stack |
| `repo_skeleton/` | Project scaffold ready for development |
| `landing_page/` | Production-ready landing page |
| `content_pack/` | Marketing copy and social posts |
| `launch_checklist.md` | Go-to-market checklist |
| `decision.md` | Verdict (PASS / ABORT) with rationale |
| `confidence.json` | 0–100 reliability score and breakdown |
| `devils_advocate.md` | Critical risk analysis |
| `mvp_repo/` | Functional MVP application (Next.js + FastAPI) |
| `project_build/` | Implementation-ready codebase with git history |

### Verdict Taxonomy

| Verdict | Meaning |
|---------|---------|
| **PASS** | Real data + high confidence → full artifact set generated |
| **ABORT** | Insufficient or fallback data → pipeline stops early, no product artifacts |

> The system enforces **NO DATA → NO PRODUCT**. It never generates artifacts from synthetic data.

---

## 🏗️ Architecture

```
User Input → Signal Engine → CrewAI Agents → Quality Gates → MVP Generation → Output Artifacts
```

### Core Components

| Component | Role |
|-----------|------|
| **CrewAI** (`app/agents/crew.py`) | Multi-agent orchestration |
| **LangChain** (`app/langchain_tools.py`) | Web scraping, RAG, content tools |
| **Signal Engine** | Multi-pass scraping, SimHash dedup, pain clustering |
| **MVP Builder** | Progressive Foundation → UX → Polish cycles |
| **Quality Gates** | Pre-run signal checks and post-run confidence scoring |

### Technology Stack

- **Backend**: FastAPI, Python 3.9+, Redis, SQLite
- **Frontend (generated)**: Next.js, TypeScript, Tailwind CSS, shadcn/ui
- **AI Models**: Ollama — `llama3.1:8b` (general), `qwen2.5-coder:7b` (code)
- **Infrastructure**: Docker Compose, Prometheus, Grafana

---

## ⚙️ Configuration

Key variables in `.env` (see `.env.example` for the full list):

```bash
# Ollama
OLLAMA_BASE_URL=http://localhost:11434
GENERAL_MODEL=llama3.1:8b
CODE_MODEL=qwen2.5-coder:7b

# Pipeline
DEFAULT_N_IDEAS=10
FAST_MODE=false
MAX_SOURCES=8

# Quality thresholds
MARKET_SIGNAL_THRESHOLD=40
SIGNAL_QUALITY_THRESHOLD=45

# ICP focus (optional)
PRIMARY_ICP="Founders B2B SaaS pre-seed"
PRIMARY_ICP_KEYWORDS="founder,founders,b2b,saas,pre-seed,startup"

# Performance
ENABLE_CACHE=true
CACHE_TTL=3600
```

Configuration files:
- `configs/sources.yaml` — scraped sources
- `configs/thresholds.yaml` — signal and quality thresholds
- `app/prompts/` — LLM prompt templates
- `knowledge/` — RAG playbook

---

## 🚢 Deployment

### Docker (local / dev)

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| UI | http://localhost:8501 |
| Ollama | http://localhost:11434 |
| Redis | localhost:6379 |

### Production

```bash
docker compose -f docker-compose.production.yml up -d
```

### Health Checks

```bash
curl http://localhost:8000/healthz
curl http://localhost:8000/readyz
curl http://localhost:8000/metrics          # JSON snapshot
curl http://localhost:8000/metrics/prometheus
```

---

## 📊 Monitoring

```bash
# Start the full monitoring stack
docker-compose -f docker-compose.monitoring-complete.yml up -d
```

| Service | URL |
|---------|-----|
| Grafana | http://localhost:3001 (admin / admin123) |
| Prometheus | http://localhost:9090 |
| Kibana | http://localhost:5601 |
| Jaeger | http://localhost:16686 |

See [MONITORING_GUIDE.md](./MONITORING_GUIDE.md) for full setup and alert configuration.

---

## 🔬 Advanced Features

### Asmblr Loop (automated patch cycles)

Run a controlled *plan → patch → verify → checkpoint* cycle against your codebase:

```bash
python -m app loop \
  --goal "Improve dependency management" \
  --max-iter 3 \
  --tests "python -m pytest -q" \
  --approve-mode auto
```

- Use `--dry-run` to inspect plan/patch artifacts without applying them.
- Use `--approve-mode manual` to confirm each patch interactively.
- Each iteration writes artifacts under `runs/<run_id>/loop/iter_<k>/`.

**Rollback:**
```bash
python -m app loop-rollback --run-id 20260126_120000_000000 --to-iter 2
```

### Build MVP (standalone)

Regenerate or create an MVP from an existing run or a one-line brief:

```bash
# Rebuild MVP for an existing run
python -m app build-mvp --run-id <run_id> --force

# Build from a brief (creates a new run)
python -m app build-mvp --brief "SaaS invoicing for freelancers" \
  --output runs/_adhoc/

# Preview the generated UI
cd runs/<run_id>/mvp_repo && npm install && npm run dev
```

### Watch a Run

Monitor a long-running pipeline without waiting for the CLI to exit:

```bash
python scripts/watch_run.py runs/<run_id>
```

Prints `run_state.json` changes and tails `progress.log` until `status=completed`.

### Scheduler / Batch

```bash
# Linux cron (daily scan at 09:00)
0 9 * * * cd /path/to/repo && . .venv/bin/activate && python -m app run --topic "Daily trend scan" --fast
```

Windows Task Scheduler: use `scripts/run_daily.bat`.

---

## 🧪 Testing

```bash
# Quick suite (lint + smoke test)
python scripts/test_all.py --mode quick

# Full suite
python scripts/test_all.py --mode full

# Or with make
make test

# pytest directly
pytest -q
pytest --cov=app
```

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Ollama not reachable | Set `OLLAMA_BASE_URL` in `.env`; run `python -m app doctor` |
| Scraping fails | Sources may block robots.txt — try different sources in `configs/sources.yaml` |
| CPU-only machine is slow | Reduce `MAX_SOURCES` and use `--fast` or `--profile quick` |
| Run interrupted | Use `python -m app resume --run-id <run_id>` |
| Low signal quality | Lower `SIGNAL_QUALITY_THRESHOLD` in `.env` for testing (default 45) |

Logs:
- Set `LOG_JSON=true` in `.env` for structured logs
- Audit log: `data/audit.log`
- Run log: `runs/<run_id>/progress.log`

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Fork, clone, then:
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pytest
streamlit run app/ui.py
```

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ by the Asmblr community — transform your ideas into reality, one MVP at a time! 🚀**
