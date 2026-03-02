# 🚀 Asmblr - AI-Powered MVP Generator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20AI-green.svg)](https://ollama.ai/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Web%20UI-red.svg)](https://streamlit.io/)

> **Transform your ideas into launch-ready MVPs with AI-powered automation**

Asmblr is a comprehensive AI-powered tool that generates complete Minimum Viable Products from just a topic or idea. Built on CrewAI + LangChain with local Ollama models, it produces market reports, PRDs, tech specs, repo skeletons, landing pages, and content packs - all without requiring paid APIs.

## ✨ Key Features

### 🤖 AI-Powered Pipeline
- **Multi-Agent System**: Researcher → Analyst → Product → Tech Lead → Growth agents
- **Local AI Models**: Runs entirely on your machine with Ollama (no API costs)
- **Smart Signal Processing**: Multi-pass web scraping and market analysis
- **Automated Decision Making**: Intelligent go/no-go decisions with confidence scoring

### 📊 Comprehensive Output
- **Market Research**: Detailed market reports with competitive analysis
- **Product Requirements**: Complete PRDs with feature specifications
- **Technical Architecture**: Tech specs and implementation guidance
- **Code Generation**: Repository skeletons with modern tech stacks
- **Marketing Assets**: Landing pages and content packs for launch

### 🎯 Production-Ready Features
- **Modern Tech Stack**: Next.js + FastAPI + PostgreSQL/SQLite
- **Progressive MVP Cycles**: Foundation → UX → Polish iterations
- **Quality Gates**: Automated testing and validation
- **Security First**: Input validation, rate limiting, data protection
- **Performance Optimized**: Connection pooling, request batching, caching

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- Ollama installed and running
- 8GB+ RAM recommended (for AI models)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/asmblr.git
   cd asmblr
   ```

2. **Run the automated setup**
   ```bash
   python setup.py
   ```
   This will:
   - Install all Python dependencies
   - Install and configure Ollama
   - Download required AI models
   - Create necessary directories
   - Verify everything is working

3. **Start the application**
   ```bash
   streamlit run app/ui.py
   ```

4. **Open your browser**
   Navigate to http://localhost:8501 and generate your first MVP!

### Manual Installation

If you prefer manual setup:

1. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or
   .venv\Scripts\activate     # Windows
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup Ollama**
   ```bash
   # Install Ollama (if not already installed)
   curl -fsSL https://ollama.ai/install.sh | sh  # Linux/Mac
   # or download from https://ollama.ai/download for Windows
   
   # Start Ollama
   ollama serve
   
   # Pull required models
   ollama pull llama3.1:8b
   ollama pull qwen2.5-coder:7b
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your preferences
   ```

## 🎮 Demo Mode

Want to try Asmblr without setup? Enable demo mode:

```bash
# Copy demo configuration
cp .env.example .env
# Add these lines to .env:
DEMO_MODE=true
DEMO_TOPIC="AI-powered task management for remote teams"
```

Demo mode includes:
- Pre-configured examples and templates
- Optimized settings for quick demos
- Sample data and mock responses
- Reduced resource requirements

## 📖 Usage Guide

### Web Interface
1. **Launch the UI**: `streamlit run app/ui.py`
2. **Choose your approach**:
   - **Idea Exploration**: Start with a vague concept
   - **Validated Idea**: Use your researched idea
   - **Competitor Analysis**: Analyze existing solutions
3. **Configure settings**: Adjust ICP, sources, and thresholds
4. **Generate MVP**: Watch the AI agents work in real-time
5. **Review results**: Explore generated artifacts and insights

### Command Line Interface
```bash
# Quick generation
python -m app run --topic "AI compliance for SMBs" --fast

# Full analysis
python -m app run --topic "FinOps insights" --n_ideas 15

# Custom ICP focus
python -m app run --topic "B2B procurement" --seed-icp "Enterprise procurement managers"

# Resume interrupted run
python -m app resume --run-id <run_id>
```

### API Usage
```python
import httpx

# Start a new run
response = httpx.post("http://localhost:8000/run", json={
    "topic": "AI-powered customer support",
    "n_ideas": 10,
    "fast": False
})
run_id = response.json()["run_id"]

# Check status
status = httpx.get(f"http://localhost:8000/run/{run_id}")

# Get results
results = httpx.get(f"http://localhost:8000/run/{run_id}/artifact/market_report")
```

## 🏗️ Architecture

### Core Components
- **CrewAI Orchestrator**: Multi-agent coordination and workflow
- **LangChain Tools**: Web scraping, RAG, and content generation
- **Signal Engine**: Market signal processing and analysis
- **MVP Builder**: Progressive frontend and backend generation
- **Quality Gates**: Automated testing and validation

### Technology Stack
- **Backend**: FastAPI, Python 3.9+, Redis, PostgreSQL/SQLite
- **Frontend**: Next.js, TypeScript, Tailwind CSS, shadcn/ui
- **AI Models**: Ollama (llama3.1:8b, qwen2.5-coder:7b)
- **Infrastructure**: Docker, Docker Compose, Prometheus

### Data Flow
```
User Input → Signal Engine → CrewAI Agents → Quality Gates → MVP Generation → Output Artifacts
```

## 🔧 Configuration

### Environment Variables
Key configuration options (see `.env.example` for complete list):

```bash
# AI Models
OLLAMA_BASE_URL=http://localhost:11434
GENERAL_MODEL=llama3.1:8b
CODE_MODEL=qwen2.5-coder:7b

# Pipeline Settings
DEFAULT_N_IDEAS=10
FAST_MODE=false
MAX_SOURCES=8

# Quality Thresholds
MARKET_SIGNAL_THRESHOLD=40
SIGNAL_QUALITY_THRESHOLD=45

# Performance
ENABLE_CONNECTION_POOLING=true
ENABLE_REQUEST_BATCHING=true
MAX_HTTP_CONNECTIONS=50
```

### Custom ICP Focus
Target specific customer segments:
```bash
PRIMARY_ICP="Founders B2B SaaS pre-seed"
PRIMARY_ICP_KEYWORDS="founder,founders,b2b,saas,pre-seed,startup"
ICP_ALIGNMENT_BONUS_MAX=8
```

## 📊 Generated Artifacts

Each run produces a complete MVP package:

### 📈 Business Artifacts
- `market_report.md` - Comprehensive market analysis
- `prd.md` - Product requirements document
- `competitor_analysis.json` - Competitive landscape
- `decision.md` - Go/no-go decision with rationale

### 🛠️ Technical Artifacts
- `tech_spec.md` - Technical architecture and specifications
- `repo_skeleton/` - Complete project structure
- `project_build/` - Implementation-ready codebase

### 🎨 Frontend Artifacts
- `landing_page/` - Production-ready landing page
- `content_pack/` - Marketing content and copy
- `mvp_repo/` - Functional MVP application

### 📊 Quality & Analytics
- `confidence.json` - Reliability assessment
- `devils_advocate.md` - Critical analysis
- `run_state.json` - Execution metadata

## 🚢 Deployment

### Docker Deployment
```bash
# Build and start all services
docker compose up --build

# Services available:
# - API: http://localhost:8000
# - UI: http://localhost:8501
# - Ollama: http://localhost:11434
# - Redis: localhost:6379
```

### Production Deployment
```bash
# Production configuration
export PROD_MODE=true
export API_KEY=your-secure-api-key
export ENABLE_MONITORING=true

# Start production services
docker compose -f docker-compose.production.yml up -d
```

### Microservices Architecture
For larger deployments:
```bash
# Deploy microservices
docker compose -f docker-compose.microservices.yml up -d

# Services:
# - API Gateway: http://localhost:8000
# - Core Service: http://localhost:8001
# - Agents Service: http://localhost:8002
# - Media Service: http://localhost:8003
```

## 🧪 Testing

### Run Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=app

# Specific test suites
pytest tests/test_security.py
pytest tests/test_performance.py
pytest tests/test_integration.py
```

### Test Coverage
- Security tests: Input validation, rate limiting, data protection
- Performance tests: Connection pooling, request batching
- Integration tests: API endpoints, pipeline execution
- End-to-end tests: Complete MVP generation workflow

## 🔒 Security

### Built-in Security Features
- **Input Validation**: Prevents injection attacks and malicious input
- **Rate Limiting**: Protects against abuse and resource exhaustion
- **Data Redaction**: Automatically redacts sensitive information in logs
- **API Authentication**: Secure API access with key management
- **Content Security**: XSS and CSRF protection

### Security Best Practices
- No hardcoded secrets or credentials
- Environment-based configuration
- Regular security updates and dependency scanning
- Comprehensive audit logging
- Secure default configurations

## 📈 Performance

### Optimization Features
- **Connection Pooling**: Reuses HTTP and Redis connections
- **Request Batching**: Groups similar requests for efficiency
- **Caching**: Multi-layer caching for frequently accessed data
- **Async Processing**: Non-blocking operations throughout
- **Resource Management**: Automatic cleanup and resource limits

### Performance Metrics
- Average pipeline time: 10-35 minutes (depending on mode)
- Memory usage: 2-8GB (depending on model size)
- Concurrent runs: Up to 3 (configurable)
- API response time: <200ms for health checks

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Ways to Contribute
- 🐛 Report bugs and issues
- 💡 Suggest features and improvements
- 🔧 Submit pull requests
- 📚 Improve documentation
- 🧪 Write tests and fix bugs
- 🌟 Star the project!

### Development Setup
```bash
# Fork and clone the repository
git clone https://github.com/your-username/asmblr.git
cd asmblr

# Setup development environment
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest

# Start development server
streamlit run app/ui.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **CrewAI** - Multi-agent AI orchestration
- **LangChain** - LLM application framework
- **Ollama** - Local AI model serving
- **Streamlit** - Web application framework
- **FastAPI** - Modern Python web framework

## 📞 Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/your-username/asmblr/issues)
- 💬 [Discussions](https://github.com/your-username/asmblr/discussions)
- 📧 [Email Support](mailto:support@asmblr.ai)

## 🗺️ Roadmap

### v1.1 (Planned)
- [ ] Additional AI model support
- [ ] Enhanced collaboration features
- [ ] Advanced analytics dashboard
- [ ] Mobile-responsive UI improvements

### v1.2 (Planned)
- [ ] Multi-language support
- [ ] Cloud deployment options
- [ ] Advanced customization
- [ ] Integration marketplace

### v2.0 (Future)
- [ ] Real-time collaboration
- [ ] Advanced AI agents
- [ ] Enterprise features
- [ ] API marketplace

---

**Built with ❤️ by the Asmblr community**

Transform your ideas into reality, one MVP at a time! 🚀
