# 🚀 Asmblr Deployment Guide

Guide complet pour déployer Asmblr en production avec les nouvelles optimisations.

## 📋 Table des Matières

- [Prérequis](#prérequis)
- [Installation Rapide](#installation-rapide)
- [Déploiement Optimisé](#déploiement-optimisé)
- [Configuration Production](#configuration-production)
- [Monitoring](#monitoring)
- [Backup et Recovery](#backup-et-recovery)
- [Performance Tuning](#performance-tuning)
- [Dépannage](#dépannage)

## 🔧 Prérequis

### Système
- **CPU**: 4+ cores (8+ recommandés pour ML)
- **RAM**: 8GB+ (16GB+ recommandés pour ML)
- **Stockage**: 50GB+ SSD
- **OS**: Linux (Ubuntu 20.04+) ou macOS/Windows avec Docker

### Logiciels
- Docker 20.10+
- Docker Compose 2.0+
- Python 3.9+ (pour développement local)
- Git

## ⚡ Installation Rapide

### 1. Cloner le Repository
```bash
git clone https://github.com/votre-org/asmblr.git
cd asmblr
```

### 2. Configuration Minimale
```bash
# Copier la configuration minimale
cp .env.minimal .env

# Générer une clé secrète
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(64))")
echo "SECRET_KEY=$SECRET_KEY" >> .env
```

### 3. Démarrage Rapide
```bash
# Utiliser la composition optimisée
docker-compose -f docker-compose.optimized.yml up -d

# Ou avec monitoring
docker-compose -f docker-compose.optimized.yml --profile monitoring up -d
```

### 4. Vérifier l'Installation
```bash
# Health checks
curl http://localhost:8000/health/detailed

# Vérifier les services
docker-compose -f docker-compose.optimized.yml ps
```

## 🏗️ Déploiement Optimisé

### Option 1: Docker Compose Optimisé (Recommandé)

```bash
# Démarrer les services de base
docker-compose -f docker-compose.optimized.yml up -d

# Ajouter le monitoring
docker-compose -f docker-compose.optimized.yml --profile monitoring up -d

# Ajouter le backup automatisé
docker-compose -f docker-compose.optimized.yml --profile backup up -d
```

**Avantages:**
- ✅ Images optimisées (multi-stage)
- ✅ Gestion des ressources
- ✅ Health checks intégrés
- ✅ Monitoring intégré
- ✅ Backup automatisé

### Option 2: Kubernetes

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: asmblr

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: asmblr-config
  namespace: asmblr
data:
  OLLAMA_BASE_URL: "http://ollama:11434"
  REDIS_URL: "redis://redis:6379/0"
  LOG_JSON: "true"
  ENABLE_MONITORING: "true"
```

### Option 3: Déploiement Cloud

#### AWS ECS
```bash
# Créer le cluster
aws ecs create-cluster --cluster-name asmblr

# Déployer la task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json

# Créer le service
aws ecs create-service --cluster asmblr --service-name asmblr-api --task-definition asmblr:1
```

#### Google Cloud Run
```bash
# Builder l'image
gcloud builds submit --tag gcr.io/PROJECT_ID/asmblr

# Déployer
gcloud run deploy asmblr --image gcr.io/PROJECT_ID/asmblr --platform managed
```

## ⚙️ Configuration Production

### Variables d'Environnement Essentielles

```bash
# Base de données
DATABASE_URL=postgresql://user:pass@host:5432/asmblr

# Redis
REDIS_URL=redis://redis:6379/0

# Ollama
OLLAMA_BASE_URL=http://ollama:11434
GENERAL_MODEL=llama3.1:8b
CODE_MODEL=qwen2.5-coder:7b

# Sécurité
SECRET_KEY=votre-clé-secrète-64-caractères
PROD_MODE=true

# Performance
ENABLE_MONITORING=true
ENABLE_CACHE=true
MAX_CONCURRENT_RUNS=3

# Backup
BACKUP_DIR=/app/backups
BACKUP_RETENTION_DAYS=30
S3_BUCKET=asmblr-backups
```

### Configuration Avancée

```bash
# Activer les features ML
ENABLE_ML_FEATURES=true

# Configuration du cache
CACHE_TTL=3600
CACHE_SIZE=10000

# Limites de ressources
MAX_MEMORY_USAGE=80
MAX_CPU_USAGE=85

# Alertes
ENABLE_ALERTS=true
ALERT_EMAIL=admin@votre-domaine.com
```

## 📊 Monitoring

### Prometheus + Grafana

```bash
# Accéder à Prometheus
http://localhost:9090

# Accéder à Grafana
http://localhost:3001
# Username: admin
# Password: admin123
```

### Métriques Disponibles

#### Business Metrics
- `asmblr_mvp_generated_total` - MVP générés
- `asmblr_ideas_generated_total` - Idées générées
- `asmblr_user_sessions_total` - Sessions utilisateurs
- `asmblr_cache_hit_rate` - Taux de cache

#### Performance Metrics
- `asmblr_llm_response_duration_seconds` - Temps de réponse LLM
- `asmblr_system_load_percentage` - Charge système
- `asmblr_error_rate` - Taux d'erreurs

#### Health Checks
- `/health` - Basic health
- `/health/detailed` - Health détaillé
- `/readyz` - Readiness check

### Alertes Configurées

```yaml
# monitoring/alerts.yml
groups:
  - name: asmblr
    rules:
      - alert: HighErrorRate
        expr: asmblr_error_rate > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
      
      - alert: LowCacheHitRate
        expr: asmblr_cache_hit_rate < 70
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Cache hit rate below 70%"
```

## 💾 Backup et Recovery

### Configuration Backup Automatisé

```bash
# Activer le service de backup
docker-compose -f docker-compose.optimized.yml --profile backup up -d

# Backup manuel
docker exec asmblr-backup python /app/scripts/backup-service.py backup --type full

# Lister les backups
docker exec asmblr-backup python /app/scripts/backup-service.py list

# Restaurer un backup
docker exec asmblr-backup python /app/scripts/backup-service.py restore --name backup_name
```

### Backup vers S3

```bash
# Configuration dans .env
S3_BUCKET=asmblr-backups
AWS_ACCESS_KEY_ID=votre-access-key
AWS_SECRET_ACCESS_KEY=votre-secret-key

# Backup automatique toutes les 6 heures
docker exec asmblr-backup python /app/scripts/backup-service.py schedule
```

### Types de Backup

- **full**: Base de données + runs + configurations + logs
- **database**: Seulement la base de données
- **runs**: Seulement les runs récents (7 jours)
- **config**: Seulement les fichiers de configuration

## 🚀 Performance Tuning

### Optimisations Docker

```yaml
# docker-compose.optimized.yml
services:
  api:
    mem_limit: 1g
    cpus: "1.0"
    environment:
      - WORKERS=4
      - MAX_CONNECTIONS=1000
      - KEEP_ALIVE=2
```

### Cache Configuration

```python
# app/core/llm_cache.py
cache_manager = LLMCacheManager()
cache_manager.similarity_threshold = 0.85
cache_manager.max_cache_size = 10000
```

### Async Processing

```python
# app/core/async_tasks.py
@background_task(name="mvp_generation", priority=TaskPriority.HIGH)
async def generate_mvp_async(run_id: str):
    # Processing en arrière-plan
    pass
```

### Monitoring Performance

```bash
# Vérifier l'utilisation des ressources
docker stats

# Logs de performance
docker logs asmblr-api | grep "performance"

# Métriques en temps réel
curl http://localhost:8000/metrics
```

## 🔧 Dépannage

### Problèmes Communs

#### 1. Ollama ne démarre pas
```bash
# Vérifier les logs
docker logs asmblr-ollama

# Redémarrer le service
docker-compose -f docker-compose.optimized.yml restart ollama

# Vérifier les modèles
docker exec asmblr-ollama ollama list
```

#### 2. Mémoire insuffisante
```bash
# Augmenter la limite mémoire
docker-compose -f docker-compose.optimized.yml down
# Modifier mem_limit dans docker-compose.optimized.yml
docker-compose -f docker-compose.optimized.yml up -d
```

#### 3. Performance lente
```bash
# Vérifier le cache hit rate
curl http://localhost:8000/metrics | grep cache_hit_rate

# Activer le cache
echo "ENABLE_CACHE=true" >> .env
docker-compose -f docker-compose.optimized.yml restart api
```

#### 4. Backup échoue
```bash
# Vérifier l'espace disque
df -h

# Nettoyer les vieux backups
docker exec asmblr-backup python /app/scripts/backup-service.py cleanup
```

### Logs et Debugging

```bash
# Logs de tous les services
docker-compose -f docker-compose.optimized.yml logs -f

# Logs d'un service spécifique
docker-compose -f docker-compose.optimized.yml logs -f api

# Logs structurés JSON
docker logs asmblr-api | jq '.'

# Health check détaillé
curl -s http://localhost:8000/health/detailed | jq '.'
```

### Performance Monitoring

```bash
# Utilisation CPU/Mémoire
docker stats --no-stream

# Temps de réponse API
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health

# Cache performance
curl -s http://localhost:8000/metrics | grep cache
```

## 📈 Scaling

### Horizontal Scaling

```yaml
# docker-compose.scale.yml
services:
  api:
    deploy:
      replicas: 3
    environment:
      - REDIS_URL=redis://redis:6379/0
```

### Load Balancing

```nginx
# nginx.conf
upstream asmblr_api {
    server api1:8000;
    server api2:8000;
    server api3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://asmblr_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔒 Sécurité

### Bonnes Pratiques

1. **Utiliser des secrets Docker**
```bash
echo "SECRET_KEY=votre-clé" | docker secret create asmblr_secret -
```

2. **HTTPS en production**
```yaml
services:
  nginx:
    ports:
      - "443:443"
    volumes:
      - ./ssl:/etc/ssl
```

3. **Network isolation**
```yaml
networks:
  internal:
    driver: bridge
    internal: true
```

## 📚 Documentation Additionnelle

- [Guide Monitoring](./MONITORING_GUIDE.md)
- [Guide Développement](./docs/DEVELOPER_GUIDE.md)
- [API Documentation](http://localhost:8000/docs)
- [Configuration Complète](./.env.example)

---

## 🆘 Support

Pour obtenir de l'aide :

1. Consulter les [logs](#logs-et-debugging)
2. Vérifier les [health checks](#health-checks)
3. Consulter la [documentation](#documentation-additionnelle)
4. Ouvrir une issue sur GitHub

**Temps de déploiement estimé** : 10-15 minutes pour une configuration complète.
