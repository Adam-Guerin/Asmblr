# 🚀 Quick Start Guide - Asmblr

Ce guide vous permet de démarrer avec Asmblr en utilisant la configuration simplifiée et les dépendances optimisées.

## 📋 Prérequis

- Python 3.9+
- Docker (optionnel, pour Redis)
- Git

## ⚡ Installation Rapide (5 minutes)

### 1. Cloner le projet
```bash
git clone <repository-url>
cd Asmblr
```

### 2. Créer l'environnement virtuel
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 3. Installer les dépendances de base
```bash
pip install -r requirements.core.txt
```

### 4. Configurer l'environnement
```bash
cp .env.minimal .env
```

Générer une clé secrète :
```bash
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(64))"
```

Ajouter la clé générée dans `.env`.

### 5. Installer Ollama
```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Télécharger depuis https://ollama.com/download
```

### 6. Télécharger les modèles
```bash
ollama pull llama3.1:8b
ollama pull qwen2.5-coder:7b
```

### 7. Démarrer Redis (optionnel mais recommandé)
```bash
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

### 8. Lancer Asmblr
```bash
streamlit run app/ui.py
```

Ouvrez http://localhost:8501 dans votre navigateur !

## 🔧 Options Avancées

### Activer les fonctionnalités ML
```bash
pip install -r requirements.ml.txt
```

### Développement complet
```bash
pip install -r requirements.core.txt
pip install -r requirements.ml.txt  
pip install -r requirements-dev.txt
```

### Production avec Docker
```bash
docker-compose up --build
```

## 🏥 Vérifier l'Installation

### Health Checks
```bash
# Basic health
curl http://localhost:8000/health

# Detailed health
curl http://localhost:8000/health/detailed

# Readiness check
curl http://localhost:8000/readyz
```

### Tests
```bash
# Tests rapides
python -m pytest tests/ -v

# Tests avec couverture
python -m pytest --cov=app tests/
```

## 📊 Monitoring

Les endpoints de monitoring sont disponibles :
- **Métriques** : http://localhost:8000/metrics
- **Prometheus** : http://localhost:8000/metrics/prometheus

## 🚨 Dépannage

### Problèmes courants

**Ollama not found**
```bash
# Vérifier Ollama
ollama list

# Redémarrer Ollama
ollama serve
```

**Redis connection failed**
```bash
# Vérifier Redis
docker ps | grep redis

# Redémarrer Redis
docker restart redis
```

**Port déjà utilisé**
```bash
# Changer les ports dans .env
API_PORT=8001
UI_PORT=8502
```

### Logs

```bash
# Logs de l'API
tail -f logs/api.log

# Logs de l'UI
tail -f logs/ui.log

# Logs système
journalctl -u asmblr
```

## 🔄 Mise à jour

```bash
git pull origin main
pip install -r requirements.core.txt
```

## 📚 Documentation Complète

- [Guide complet](./README.md)
- [Configuration avancée](./.env.example)
- [Guide monitoring](./MONITORING_GUIDE.md)
- [Développement](./docs/DEVELOPER_GUIDE.md)

## 🆘 Support

Si vous rencontrez des problèmes :

1. Vérifiez les [logs](#logs)
2. Lancez les [health checks](#health-checks)
3. Consultez le [guide de dépannage](#dépannage)
4. Ouvrez une issue sur GitHub

---

**Temps total estimé** : 5-10 minutes pour une installation de base.
