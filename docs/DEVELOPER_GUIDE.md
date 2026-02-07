# 📚 Asmblr - Guide Développeur

## Table des Matières

1. [Architecture](#architecture)
2. [Setup de Développement](#setup-de-développement)
3. [Structure du Code](#structure-du-code)
4. [Tests](#tests)
5. [Monitoring](#monitoring)
6. [Déploiement](#déploiement)
7. [Contribution](#contribution)

---

## 🏗️ Architecture

### Vue d'Ensemble

Asmblr est une application Python basée sur une architecture multi-agents utilisant CrewAI et LangChain.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit    │    │   FastAPI       │    │   CLI Tool      │
│     UI         │    │     API         │    │   Interface     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Core Layer    │
                    │                 │
                    │ - Pipeline      │
                    │ - Progress      │
                    │ - Error Handler │
                    │ - Monitoring    │
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Agents       │    │     UI          │    │   Monitoring    │
│                 │    │                 │    │                 │
│ - CrewAI       │    │ - Themes        │    │ - Metrics       │
│ - LLM Tools    │    │ - Charts        │    │ - Alerts        │
│ - Scrapers     │    │ - Exports       │    │ - Notifications │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Infrastructure │
                    │                 │
                    │ - Ollama LLM    │
                    │ - SQLite        │
                    │ - File System   │
                    │ - Redis (opt)   │
                    └─────────────────┘
```

### Composants Principaux

#### Core Layer (`app/core/`)

- **Pipeline** : Orchestration des étapes de traitement
- **Progress** : Suivi en temps réel de l'exécution
- **Error Handler** : Gestion centralisée des erreurs
- **Config** : Configuration et variables d'environnement
- **LLM** : Interface avec les modèles de langage
- **Models** : Structures de données partagées

#### Agents (`app/agents/`)

- **CrewAI** : Orchestrateur multi-agents
- **Tools** : Outils LangChain pour les agents
- **Scrapers** : Collecte de données web
- **Generators** : Génération de contenu

#### UI (`app/ui/`)

- **Theme Manager** : Gestion des thèmes et styles
- **Charts** : Visualisations interactives
- **Export Manager** : Export multi-formats
- **Components** : Composants réutilisables

#### Monitoring (`app/monitoring/`)

- **Metrics** : Collecte de métriques système et applicatives
- **Alerts** : Système d'alertes multi-canaux
- **Dashboard** : Interface de monitoring

---

## 🛠️ Setup de Développement

### Prérequis

- Python 3.11+
- Git
- Docker (optionnel)
- Ollama

### Installation

```bash
# Cloner le repository
git clone https://github.com/votre-org/asmblr.git
cd asmblr

# Environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\\Scripts\\activate  # Windows

# Dépendances de développement
pip install -r requirements_updated.txt
pip install -r requirements-dev.txt

# Configuration développement
cp .env.example .env.dev
# Éditer .env.dev avec vos configurations

# Base de données développement
python -m app init-db --dev

# Démarrer Ollama
ollama serve
ollama pull llama3.1:8b
ollama pull qwen2.5-coder:7b
```

### IDE Configuration

#### VS Code

```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./.venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true
    }
}
```

#### PyCharm

- Interpreter : `.venv/bin/python`
- Test runner : pytest
- Code style : Black, Ruff

---

## 📁 Structure du Code

```
asmblr/
├── app/                          # Application principale
│   ├── agents/                   # Agents IA
│   │   ├── crew.py              # Orchestrateur CrewAI
│   │   └── tools/               # Outils des agents
│   ├── core/                     # Cœur métier
│   │   ├── config.py            # Configuration
│   │   ├── pipeline.py          # Pipeline principal
│   │   ├── progress.py          # Suivi de progression
│   │   ├── error_handler.py     # Gestion d'erreurs
│   │   ├── llm.py              # Interface LLM
│   │   └── models.py           # Modèles de données
│   ├── ui/                       # Interface utilisateur
│   │   ├── theme_manager.py     # Gestion des thèmes
│   │   ├── charts.py            # Graphiques
│   │   ├── export_manager.py    # Exports
│   │   └── components.py        # Composants UI
│   ├── monitoring/               # Monitoring
│   │   ├── metrics.py           # Métriques
│   │   └── alerts.py            # Alertes
│   ├── tools/                    # Outils utilitaires
│   ├── mvp/                      # Génération MVP
│   └── __main__.py              # Point d'entrée CLI
├── tests/                        # Tests
│   ├── unit/                    # Tests unitaires
│   ├── integration/             # Tests d'intégration
│   └── e2e/                     # Tests end-to-end
├── docs/                         # Documentation
├── configs/                      # Fichiers de configuration
├── scripts/                      # Scripts utilitaires
├── data/                         # Données applicatives
└── runs/                         # Résultats d'exécution
```

### Conventions de Codage

#### Style Guide

- **Formatter** : Black
- **Linter** : Ruff
- **Type Hints** : Obligatoires pour les nouvelles fonctions
- **Docstrings** : Format Google Style

```python
def process_ideas(ideas: List[Idea], config: Config) -> ProcessedResult:
    """Process a list of ideas and return results.
    
    Args:
        ideas: List of ideas to process
        config: Processing configuration
        
    Returns:
        ProcessedResult containing scored ideas and metadata
        
    Raises:
        ProcessingError: If processing fails
    """
    pass
```

#### Patterns

**Singleton Pattern** (pour les managers globaux) :

```python
class GlobalManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

def get_global_manager() -> GlobalManager:
    return GlobalManager()
```

**Factory Pattern** (pour les créations d'objets) :

```python
class AgentFactory:
    @staticmethod
    def create_agent(agent_type: str, config: Dict) -> Agent:
        if agent_type == "researcher":
            return ResearcherAgent(config)
        elif agent_type == "analyst":
            return AnalystAgent(config)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
```

---

## 🧪 Tests

### Structure des Tests

```
tests/
├── unit/                         # Tests unitaires
│   ├── test_progress.py          # Progress tracking
│   ├── test_error_handler.py    # Error handling
│   └── test_config.py           # Configuration
├── integration/                  # Tests d'intégration
│   ├── test_progress_tracking.py # Progress system
│   ├── test_error_handling.py    # Error system
│   └── test_ui_components.py    # UI components
├── e2e/                         # Tests end-to-end
│   ├── test_pipeline.py         # Pipeline complet
│   └── test_ui.py              # Interface utilisateur
├── fixtures/                     # Données de test
└── conftest.py                   # Configuration pytest
```

### Exécution des Tests

```bash
# Tous les tests
pytest

# Tests unitaires seulement
pytest tests/unit/

# Tests d'intégration seulement
pytest tests/integration/

# Couverture
pytest --cov=app --cov-report=html

# Tests rapides (skip lents)
pytest -m "not slow"

# Tests spécifiques
pytest tests/unit/test_progress.py::test_progress_updates
```

### Écriture de Tests

#### Tests Unitaires

```python
import pytest
from unittest.mock import Mock, patch
from app.core.progress import ProgressTracker, PipelineStage

class TestProgressTracker:
    def setup_method(self):
        self.tracker = ProgressTracker()
    
    def test_initial_state(self):
        """Test initial tracker state."""
        state = self.tracker.get_current_state()
        assert state["stage"] == PipelineStage.INITIALIZING.value
        assert state["progress"] == 0.0
    
    def test_stage_updates(self):
        """Test stage progression."""
        self.tracker.update_stage(PipelineStage.SCRAPING, "Scraping...")
        state = self.tracker.get_current_state()
        assert state["stage"] == PipelineStage.SCRAPING.value
```

#### Tests d'Intégration

```python
import pytest
from app.core.progress import get_progress_tracker
from app.core.error_handler import handle_error

class TestProgressIntegration:
    def test_progress_with_error_handling(self):
        """Test progress tracking with error scenarios."""
        tracker = get_progress_tracker()
        
        # Simulate error during progress
        error = ConnectionError("Connection failed")
        error_info = handle_error(error)
        
        assert error_info.category == ErrorCategory.NETWORK
        assert error_info.user_message is not None
```

#### Tests avec Fixtures

```python
# conftest.py
@pytest.fixture
def sample_ideas():
    return [
        {"name": "Idea 1", "score": 85.0},
        {"name": "Idea 2", "score": 72.5}
    ]

@pytest.fixture
def mock_ollama():
    with patch('app.core.llm.OllamaClient') as mock:
        mock.return_value.generate.return_value = "Test response"
        yield mock
```

### Couverture de Tests

Objectif : **> 90%** de couverture

```bash
# Rapport de couverture
pytest --cov=app --cov-report=term-missing

# Rapport HTML détaillé
pytest --cov=app --cov-report=html

# Vérifier le seuil
pytest --cov=app --cov-fail-under=90
```

---

## 📊 Monitoring

### Métriques

#### Types de Métriques

```python
from app.monitoring.metrics import get_monitoring_system

monitoring = get_monitoring_system()

# Counter (incrémentation)
monitoring.metrics_collector.increment_counter("pipelines_started")

# Gauge (valeur instantanée)
monitoring.metrics_collector.set_gauge("active_pipelines", 3)

# Histogram (distribution)
monitoring.metrics_collector.record_histogram("idea_scores", 85.5)

# Timer (durée)
with monitoring.metrics_collector.time_operation("pipeline_execution"):
    # ... code à mesurer
    pass
```

#### Métriques Système

Automatiquement collectées :
- CPU, mémoire, disque
- Métriques processus
- Métriques réseau

#### Métriques Applicatives

À implémenter manuellement :
- Pipeline metrics
- User interactions
- Business metrics

### Alertes

#### Configuration

```python
from app.monitoring.alerts import get_notification_manager, NotificationConfig, NotificationChannel

notification_manager = get_notification_manager()

# Ajouter canal email
email_config = NotificationConfig(
    channel=NotificationChannel.EMAIL,
    enabled=True,
    config={
        "smtp_server": "smtp.gmail.com",
        "username": "alerts@company.com",
        "password": "app_password",
        "to_emails": ["dev@company.com"]
    }
)
notification_manager.add_notification_channel(email_config)
```

#### Alertes Personnalisées

```python
from app.monitoring.metrics import Alert, AlertSeverity

custom_alert = Alert(
    name="high_error_rate",
    severity=AlertSeverity.WARNING,
    condition="error_rate > threshold",
    threshold=5.0,
    message="Error rate is above 5%"
)

monitoring.alert_manager.add_alert(custom_alert)
```

### Dashboard

#### Accès

- **UI** : Onglet "📊 Dashboard" dans Streamlit
- **API** : `GET /metrics` et `GET /dashboard`
- **CLI** : `python -m app dashboard`

#### Personnalisation

```python
# Ajouter des métriques custom
def custom_metric_collector():
    monitoring = get_monitoring_system()
    
    # Vos métriques personnalisées
    custom_value = calculate_custom_metric()
    monitoring.metrics_collector.set_gauge("custom_metric", custom_value)
```

---

## 🚀 Déploiement

### Docker

#### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements_updated.txt .
RUN pip install --no-cache-dir -r requirements_updated.txt

# Copy application
COPY app/ ./app/
COPY configs/ ./configs/
COPY scripts/ ./scripts/

# Create data directories
RUN mkdir -p /app/data /app/runs

# Expose ports
EXPOSE 8501 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Start command
CMD ["streamlit", "run", "app/ui.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### Docker Compose

```yaml
version: '3.8'

services:
  asmblr:
    build: .
    ports:
      - "8501:8501"
      - "8000:8000"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - DATABASE_URL=sqlite:///data/app.db
    volumes:
      - ./data:/app/data
      - ./runs:/app/runs
    depends_on:
      - ollama
      - redis

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  ollama_data:
  redis_data:
```

### Production

#### Configuration

```bash
# .env.production
NODE_ENV=production
LOG_JSON=true
PROD_MODE=true

# Sécurité
SECRET_KEY=votre-secret-key-ici
ALLOWED_HOSTS=localhost,votre-domaine.com

# Performance
RUN_MAX_CONCURRENT=2
CACHE_TTL=3600

# Monitoring
ALERT_EMAIL_ENABLED=true
ALERT_SLACK_ENABLED=true
```

#### Déploiement avec Systemd

```ini
# /etc/systemd/system/asmblr.service
[Unit]
Description=Asmblr MVP Generator
After=network.target

[Service]
Type=simple
User=asmblr
WorkingDirectory=/opt/asmblr
Environment=PATH=/opt/asmblr/.venv/bin
ExecStart=/opt/asmblr/.venv/bin/streamlit run app/ui.py --server.port=8501
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name votre-domaine.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 🤝 Contribution

### Workflow

1. **Fork** le repository
2. **Branch** : `git checkout -b feature/nouvelle-fonctionnalite`
3. **Commit** : `git commit -m "Add: nouvelle fonctionnalité"`
4. **Push** : `git push origin feature/nouvelle-fonctionnalite`
5. **Pull Request** : Avec description et tests

### Standards de Code

- **Tests** : > 90% couverture
- **Documentation** : Docstrings pour toutes les fonctions publiques
- **Type Hints** : Obligatoires
- **Style** : Black + Ruff

### Review Process

1. **Automated** : Tests, lint, sécurité
2. **Code Review** : Architecture et qualité
3. **Integration** : Tests d'intégration
4. **Documentation** : Mise à jour si nécessaire

### Types de Contributions

#### 🐛 Bug Fixes

- Template de branche : `fix/description-du-bug`
- Tests requis pour reproduction
- Documentation des impacts

#### ✨ Nouvelles Fonctionnalités

- Template de branche : `feature/nom-fonctionnalite`
- Spécification claire
- Tests complets
- Documentation utilisateur

#### 📚 Documentation

- Template de branche : `docs/mise-a-jour`
- Exemples pratiques
- Screenshots si applicable

#### 🔧 Maintenance

- Template de branche : `chore/description`
- Refactoring
- Mises à jour de dépendances
- Optimisations

---

## 📚 Ressources Additionnelles

### Documentation Interne

- **Architecture** : `docs/ARCHITECTURE.md`
- **API** : `docs/API.md`
- **Database** : `docs/DATABASE.md`
- **Security** : `docs/SECURITY.md`

### Outils

- **Monitoring** : Grafana + Prometheus (optionnel)
- **Logging** : ELK Stack (optionnel)
- **CI/CD** : GitHub Actions
- **Container** : Docker + Docker Compose

### Communauté

- **Discord** : Lien vers le serveur
- **GitHub** : Issues et discussions
- **Blog** : Articles techniques

---

*Ce guide est maintenu par l'équipe Asmblr. Dernière mise à jour : Février 2024*
