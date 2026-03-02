# 🚀 Asmblr User Guide

**Version 2.0** | *Last Updated: 2026-02-27*

## 📖 Table of Contents

1. [Getting Started](#getting-started)
2. [Quick Start](#quick-start)
3. [Web Interface](#web-interface)
4. [Command Line Interface](#command-line-interface)
5. [Creating Ventures](#creating-ventures)
6. [Managing Runs](#managing-runs)
7. [Quality Dashboard](#quality-dashboard)
8. [Advanced Features](#advanced-features)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)

---

## 🚀 Getting Started

### System Requirements

- **Operating System**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **Memory**: Minimum 4GB RAM (8GB+ recommended)
- **CPU**: Minimum 2 cores (4+ recommended)
- **Storage**: Minimum 10GB free space
- **Python**: 3.8+ (3.9+ recommended)
- **Docker**: Optional, for containerized deployment

### Installation

#### Option 1: Quick Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/asmblr/asmblr.git
cd asmblr

# Install dependencies
pip install -r requirements.txt

# Start Ollama (required for AI functionality)
ollama serve

# Download required models
ollama pull llama3.1:8b
ollama pull qwen2.5-coder:7b

# Launch the web interface
streamlit run app/ui_enhanced.py
```

#### Option 2: Docker Installation

```bash
# Clone and build
git clone https://github.com/asmblr/asmblr.git
cd asmblr

# Run with Docker Compose
docker-compose up -d

# Access the web interface
open http://localhost:8501
```

### First-Time Setup

1. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your preferences
   ```

2. **Verify Installation**
   ```bash
   python -m app doctor
   ```

3. **Test Basic Functionality**
   ```bash
   python -m app run --topic "Test venture" --fast
   ```

---

## ⚡ Quick Start

### Your First Venture in 5 Minutes

1. **Launch the Web Interface**
   ```bash
   streamlit run app/ui_enhanced.py
   ```

2. **Create Your First Venture**
   - Navigate to "🚀 New Venture"
   - Enter a topic: "AI-powered task management for remote teams"
   - Select "Fast Mode" for quick results
   - Click "🚀 Launch Venture"

3. **Monitor Progress**
   - Watch real-time AI agent activity
   - View generated ideas and analysis
   - Download results when complete

### Command Line Quick Start

```bash
# Simple venture creation
python -m app run --topic "Sustainable fashion marketplace" --fast

# Advanced venture with custom parameters
python -m app run \
  --topic "AI compliance for healthcare" \
  --n_ideas 5 \
  --profile deep \
  --seed-icp "Healthcare CTOs" \
  --seed-pains "Regulatory compliance, data privacy"
```

---

## 🌐 Web Interface

### Dashboard Overview

The web interface provides an intuitive dashboard with:

- **📊 Metrics Dashboard**: Real-time statistics and activity monitoring
- **🚀 Venture Creation**: Form-based venture generation
- **📈 Quality Dashboard**: Quality metrics and analysis
- **⚙️ Settings**: Configuration and preferences

### Navigation

- **Sidebar Navigation**: Easy access to all features
- **Real-time Updates**: Live progress tracking
- **Responsive Design**: Works on desktop and mobile
- **Dark/Light Mode**: Automatic theme detection

### Key Features

#### 1. Metrics Dashboard
- Total ventures created
- Success rate tracking
- Recent activity timeline
- System status indicators

#### 2. Venture Creation Form
- **Topic Input**: Describe your venture idea
- **Configuration Options**: 
  - Number of ideas (1-10)
  - Execution profile (quick/standard/deep)
  - Fast mode toggle
- **Advanced Options**:
  - Target ICP (Ideal Customer Profile)
  - Pain points
  - Competitors
  - Market context

#### 3. Quality Dashboard
- Code quality metrics
- Performance indicators
- Security analysis
- Compliance checks

---

## 💻 Command Line Interface

### Basic Commands

#### Doctor Command
```bash
# Check system health
python -m app doctor

# Output includes:
# - Ollama connection status
# - Memory and CPU usage
# - Configuration validation
# - Dependency checks
```

#### Run Command
```bash
# Basic usage
python -m app run --topic "Your venture topic"

# With options
python -m app run \
  --topic "AI-powered education platform" \
  --n_ideas 3 \
  --fast \
  --profile standard

# Advanced options
python -m app run \
  --topic "Blockchain supply chain" \
  --n_ideas 5 \
  --profile deep \
  --seed-icp "Supply chain managers" \
  --seed-pains "Transparency, efficiency, cost" \
  --seed-competitors "IBM, Oracle, SAP" \
  --seed-context "Post-pandemic logistics"
```

#### Ship Command
```bash
# Full pipeline with deployment attempt
python -m app ship --topic "Mobile fitness coaching"
```

#### Build MVP Command
```bash
# Build MVP from existing run
python -m app build-mvp --run-id 20260227_001208_849003

# Build from brief
python -m app build-mvp \
  --brief "AI-powered customer service chatbot" \
  --output ./my-mvp \
  --cycles foundation,ux,polish
```

### Management Commands

#### List and Monitor Runs
```bash
# List all runs
python -m app list-runs

# Show run details
python -m app show-run --run-id 20260227_001208_849003

# Resume a failed run
python -m app resume --run-id 20260227_001208_849003
```

#### Cleanup and Maintenance
```bash
# Cleanup old runs
python -m app cleanup --purge-days 30

# Backup data
python -m app backup --retention-days 7
```

---

## 🎯 Creating Ventures

### Venture Topic Guidelines

#### Good Topics
- **Specific**: "AI-powered expense tracking for freelancers"
- **Problem-focused**: "Automated compliance checking for startups"
- **Market-oriented**: "B2B SaaS for inventory management"
- **Technology-specific**: "Machine learning for fraud detection"

#### Poor Topics
- **Too vague**: "Something with AI"
- **Too broad**: "E-commerce platform"
- **Too narrow**: "Calculator app with one feature"
- **No market**: "Personal hobby project"

### Execution Profiles

#### Quick Profile
- **Time**: 5-10 minutes
- **Depth**: Surface-level analysis
- **Best for**: Idea validation, rapid prototyping
- **Resources**: Minimal LLM usage

#### Standard Profile
- **Time**: 15-30 minutes
- **Depth**: Comprehensive analysis
- **Best for**: Most use cases, detailed planning
- **Resources**: Balanced LLM usage

#### Deep Profile
- **Time**: 45-60 minutes
- **Depth**: Exhaustive analysis
- **Best for**: Complex ventures, enterprise solutions
- **Resources**: Maximum LLM usage

### Seed Inputs

#### Ideal Customer Profile (ICP)
```bash
# Examples
--seed-icp "B2B SaaS founders, Series A+"
--seed-icp "Healthcare CIOs at hospitals >500 beds"
--seed-icp "E-commerce store owners doing $1M+ revenue"
```

#### Pain Points
```bash
# Examples
--seed-pains "Manual data entry, compliance reporting"
--seed-pains "Customer churn, high acquisition costs"
--seed-pains "Inventory management, supply chain visibility"
```

#### Competitors
```bash
# Examples
--seed-competitors "Salesforce, HubSpot, Pipedrive"
--seed-competitors "Shopify, BigCommerce, WooCommerce"
--seed-competitors "Jira, Asana, Monday.com"
```

---

## 📊 Managing Runs

### Run Lifecycle

1. **Created**: Initial setup and validation
2. **Running**: AI agents processing
3. **Completed**: Successfully finished
4. **Failed**: Error occurred
5. **Archived**: Old runs moved to storage

### Run Structure

Each run creates a directory structure:
```
runs/
├── 20260227_001208_849003/
│   ├── run_state.json      # Run metadata and status
│   ├── progress.log        # Detailed progress log
│   ├── llm_model_selection.json  # AI model choices
│   ├── adaptive_thresholds.json   # Dynamic thresholds
│   ├── run_budget.json     # Resource allocation
│   ├── seed_context.json   # Input parameters
│   └── repo_skeleton/      # Generated codebase
│       ├── README.md
│       ├── package.json
│       └── src/
```

### Monitoring Progress

#### Web Interface
- Real-time progress updates
- Agent activity logs
- Quality metrics
- Resource usage

#### Command Line
```bash
# Follow progress in real-time
tail -f runs/20260227_001208_849003/progress.log

# Check run status
python -m app show-run --run-id 20260227_001208_849003
```

### Troubleshooting Failed Runs

#### Common Issues
1. **Ollama Connection**: Ensure Ollama is running
2. **Memory Issues**: Check available RAM
3. **Network Issues**: Verify internet connection
4. **Model Availability**: Ensure models are downloaded

#### Recovery Steps
```bash
# Check run status
python -m app show-run --run-id RUN_ID

# Resume if possible
python -m app resume --run-id RUN_ID

# Check logs for errors
cat runs/RUN_ID/progress.log | grep ERROR
```

---

## 📈 Quality Dashboard

### Metrics Overview

The Quality Dashboard provides comprehensive insights into:

#### Code Quality
- **Code Complexity**: Cyclomatic complexity analysis
- **Code Coverage**: Test coverage percentage
- **Code Smells**: Detectable code issues
- **Technical Debt**: Estimated improvement effort

#### Performance Metrics
- **Response Time**: API and UI response times
- **Memory Usage**: Application memory consumption
- **CPU Usage**: Processor utilization
- **Database Performance**: Query execution times

#### Security Analysis
- **Vulnerability Scanning**: Security issue detection
- **Dependency Check**: Outdated or vulnerable packages
- **Secret Detection**: Hardcoded secrets identification
- **Compliance**: Industry standard compliance

#### Quality Gates
- **Automated Checks**: Pre-defined quality thresholds
- **Manual Review**: Human validation steps
- **Continuous Integration**: CI/CD pipeline integration
- **Quality Trends**: Historical quality metrics

### Using the Dashboard

1. **Access**: Click "📊 Quality" in the sidebar
2. **Filter**: Filter by date, project, or metric type
3. **Drill Down**: Click metrics for detailed analysis
4. **Export**: Download reports in PDF or CSV format

---

## 🔧 Advanced Features

### Autonomous Loop

The Asmblr Loop enables continuous improvement:

```bash
# Start autonomous loop
python -m app loop \
  --goal "Improve user onboarding experience" \
  --max-iter 5 \
  --tests "pytest -q" \
  --approve-mode auto

# Dry run to preview changes
python -m app loop \
  --goal "Fix performance bottlenecks" \
  --dry-run \
  --max-iter 3
```

### Golden Runs

Create reproducible golden runs:

```bash
# Capture golden run
python -m app golden-run --topic "E-commerce platform"

# Use golden run as template
python -m app run --topic "Custom e-commerce" --template golden-run-id
```

### Devil's Advocate

Get critical feedback on your ventures:

```bash
# Run critique
python -m app critique --run-id RUN_ID --mode strict

# Standard critique
python -m app critique --run-id RUN_ID --mode standard
```

### Custom Templates

Create reusable venture templates:

```bash
# List available templates
python -m app templates --list

# Use template
python -m app run --template saas-template --topic "Custom CRM"

# Create custom template
python -m app create-template \
  --name "fintech-template" \
  --from-run RUN_ID
```

---

## 🔧 Troubleshooting

### Common Issues

#### Ollama Connection Issues
```bash
# Check Ollama status
ollama list

# Restart Ollama
ollama serve

# Test connection
curl http://localhost:11434/api/tags
```

#### Memory Issues
```bash
# Check memory usage
python -m app doctor

# Enable lightweight mode
export LIGHTWEIGHT_MODE=true

# Clear cache
python -m app cleanup --cache
```

#### Import Errors
```bash
# Check dependencies
pip install -r requirements.txt

# Verify Python version
python --version

# Reinstall if needed
pip install --force-reinstall -r requirements.txt
```

#### Performance Issues
```bash
# Run performance optimizer
python performance_optimizer.py

# Apply performance config
cp .env.performance .env

# Monitor resources
python -m app monitor --realtime
```

### Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| E001 | Ollama not connected | Start Ollama service |
| E002 | Insufficient memory | Enable lightweight mode |
| E003 | Model not found | Download required models |
| E004 | Invalid topic format | Use 3-200 characters |
| E005 | Rate limit exceeded | Wait and retry |

### Getting Help

1. **Documentation**: Check this guide first
2. **Doctor Command**: Run `python -m app doctor`
3. **Community**: Join our Discord community
4. **Issues**: Report bugs on GitHub
5. **Support**: Contact support@asmblr.ai

---

## 💡 Best Practices

### Venture Creation

#### Topic Optimization
- **Be Specific**: "AI-powered expense tracking" vs "Finance app"
- **Identify Pain Points**: Focus on real problems
- **Consider Market**: Ensure viable target market
- **Leverage AI**: Use AI's unique capabilities

#### Parameter Selection
- **Start with Fast Mode**: Quick validation first
- **Use Standard Profile**: For most production use cases
- **Deep Profile**: Only for complex, high-value ventures
- **Seed Inputs**: Provide context for better results

### Performance Optimization

#### System Configuration
- **Use Lightweight Mode**: For systems with <4GB RAM
- **Enable Caching**: Improve response times
- **Monitor Resources**: Track CPU and memory usage
- **Regular Cleanup**: Remove old runs and cache

#### Development Workflow
- **Iterative Development**: Start simple, add complexity
- **Quality Gates**: Ensure quality at each step
- **Automated Testing**: Run tests automatically
- **Documentation**: Document decisions and architecture

### Security Best Practices

#### Environment Configuration
- **Use Environment Variables**: Never hardcode secrets
- **Secure .env Files**: Add to .gitignore
- **Regular Updates**: Keep dependencies updated
- **Access Control**: Limit access to sensitive data

#### Production Deployment
- **HTTPS Only**: Always use HTTPS in production
- **Rate Limiting**: Prevent abuse
- **Monitoring**: Track security events
- **Backups**: Regular data backups

### Team Collaboration

#### Version Control
- **Branch Strategy**: Use feature branches
- **Code Reviews**: Review all changes
- **Documentation**: Keep docs updated
- **Testing**: Comprehensive test coverage

#### Knowledge Sharing
- **Templates**: Create reusable templates
- **Golden Runs**: Share successful patterns
- **Best Practices**: Document lessons learned
- **Training**: Regular team training

---

## 📞 Support & Community

### Getting Help

- **Documentation**: This user guide
- **API Docs**: [docs.asmblr.ai](https://docs.asmblr.ai)
- **Community**: [discord.gg/asmblr](https://discord.gg/asmblr)
- **Issues**: [github.com/asmblr/asmblr/issues](https://github.com/asmblr/asmblr/issues)
- **Email**: support@asmblr.ai

### Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Updates

- **Release Notes**: Check CHANGELOG.md
- **Roadmap**: View future plans in ROADMAP_FUTURE.md
- **Blog**: Follow our blog for updates

---

## 📄 License

Asmblr is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

**Happy Venture Building! 🚀**

*Built with ❤️ by the Asmblr Team*
