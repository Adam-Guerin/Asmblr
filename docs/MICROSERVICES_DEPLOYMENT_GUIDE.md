# Guide de Déploiement - Architecture Micro-services Asmblr

## 🎯 Objectif

Déployer Asmblr en architecture micro-services pour une meilleure scalabilité, maintenabilité et fiabilité.

## 🏗️ Architecture Déployée

```
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway (Port 8000)                │
├─────────────────────────────────────────────────────────────────┤
│  asmblr-core    │  asmblr-agents  │  asmblr-media  │  asmblr-ui   │
│  (Port 8001)    │  (Port 8002)    │  (Port 8003)    │  (Port 3000)    │
│  Business Logic  │  AI Agents       │  Generation      │  Frontend       │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │                 │
         └────────────────┴─────────────────┴─────────────────┘
                    Shared Infrastructure
            Redis (6379) | PostgreSQL (5432) | Ollama (11434)
```

## 🚀 Déploiement Rapide

### 1. **Prérequis**

```bash
# Docker et Docker Compose
docker --version
docker-compose --version

# Ports requis (vérifier disponibilité)
netstat -an | grep -E ":(8000|8001|8002|8003|3000|5432|6379|11434)"

# Espace disque minimum (10GB recommandé)
df -h .
```

### 2. **Déploiement Complet**

```bash
# Cloner le repository
git clone <repository-url>
cd Asmblr

# Copier la configuration
cp .env.example .env.microservices

# Démarrer tous les services
docker-compose -f docker-compose.microservices.yml up -d

# Vérifier le statut
docker-compose -f docker-compose.microservices.yml ps
```

### 3. **Vérification du Déploiement**

```bash
# 1. Vérifier les services sont démarrés
docker-compose -f docker-compose.microservices.yml ps

# 2. Tester l'API Gateway
curl http://localhost:8000/api/v1/health

# 3. Tester chaque service
curl http://localhost:8001/api/v1/health  # Core
curl http://localhost:8002/api/v1/health  # Agents
curl http://localhost:8003/api/v1/health  # Media
curl http://localhost:3000                   # UI

# 4. Vérifier les logs
docker-compose -f docker-compose.microservices.yml logs -f api-gateway
```

## 📋 Services Détaillés

### **1. API Gateway (Port 8000)**

**Rôle**: Point d'entrée unique et orchestration

**Endpoints principaux**:
```bash
# Health check
GET http://localhost:8000/api/v1/health

# Redirection vers services
POST http://localhost:8000/api/v1/core/pipelines
POST http://localhost:8000/api/v1/agents/crew
POST http://localhost:8000/api/v1/media/generate
```

**Logs**:
```bash
docker-compose -f docker-compose.microservices.yml logs -f api-gateway
```

### **2. Core Service (Port 8001)**

**Rôle**: Logique métier et gestion des pipelines

**Endpoints principaux**:
```bash
# Pipelines
GET http://localhost:8001/api/v1/pipelines
POST http://localhost:8001/api/v1/pipelines
POST http://localhost:8001/api/v1/pipelines/{id}/run

# Sujets
GET http://localhost:8001/api/v1/topics
POST http://localhost:8001/api/v1/topics/{id}/validate
```

**Logs**:
```bash
docker-compose -f docker-compose.microservices.yml logs -f asmblr-core
```

### **3. Agents Service (Port 8002)**

**Rôle**: Agents CrewAI et communication LLM

**Endpoints principaux**:
```bash
# Agents
GET http://localhost:8002/api/v1/agents/status
GET http://localhost:8002/api/v1/agents/models
POST http://localhost:8002/api/v1/agents/crew

# Génération
POST http://localhost:8002/api/v1/agents/idea-generate
POST http://localhost:8002/api/v1/agents/market-analyze
```

**Logs**:
```bash
docker-compose -f docker-compose.microservices.yml logs -f asmblr-agents
```

### **4. Media Service (Port 8003)**

**Rôle**: Génération de médias (images, vidéos)

**Endpoints principaux**:
```bash
# Génération
POST http://localhost:8003/api/v1/media/generate/logo
POST http://localhost:8003/api/v1/media/generate/image
POST http://localhost:8003/api/v1/media/generate/video

# Jobs
GET http://localhost:8003/api/v1/media/jobs/{id}
GET http://localhost:8003/api/v1/media/jobs/{id}/download
```

**Logs**:
```bash
docker-compose -f docker-compose.microservices.yml logs -f asmblr-media
```

### **5. UI Service (Port 3000)**

**Rôle**: Interface utilisateur principale

**Accès**:
```bash
# Navigateur
http://localhost:3000

# Ou curl pour vérification
curl http://localhost:3000
```

## 🔧 Configuration

### **Variables d'Environnement**

```bash
# .env.microservices
# API Gateway
API_GATEWAY_HOST=0.0.0.0
API_GATEWAY_PORT=8000

# Services
CORE_SERVICE_URL=http://asmblr-core:8001
AGENTS_SERVICE_URL=http://asmblr-agents:8002
MEDIA_SERVICE_URL=http://asmblr-media:8003
UI_SERVICE_URL=http://asmblr-ui:3000

# Base de données
DATABASE_URL=postgresql://postgres:5432/asmblr
POSTGRES_DB=asmblr
POSTGRES_USER=asmblr
POSTGRES_PASSWORD=asmblr_secure_password

# Cache
REDIS_URL=redis://redis:6379/0

# LLM
OLLAMA_BASE_URL=http://ollama:11434
DEFAULT_MODEL=llama3.1:8b
CODE_MODEL=qwen2.5-coder:7b

# Stockage
STORAGE_TYPE=local
STORAGE_PATH=/app/media
```

### **Configuration Ollama**

```bash
# Télécharger les modèles requis
docker exec -it ollama ollama pull llama3.1:8b
docker exec -it ollama ollama pull qwen2.5-coder:7b

# Vérifier les modèles disponibles
docker exec -it ollama ollama list
```

## 📊 Monitoring

### **1. Prometheus (Port 9090)**

**Accès**: http://localhost:9090

**Métriques disponibles**:
- `asmblr_pipeline_requests_total`
- `asmblr_agents_executions_total`
- `asmblr_media_generations_total`
- `asmblr_uptime_seconds`

### **2. Grafana (Port 3001)**

**Accès**: http://localhost:3001
**Login**: admin / admin

**Dashboards disponibles**:
- Vue d'ensemble des services
- Métriques de performance
- Alertes et erreurs
- Utilisation des ressources

## 🛠️ Gestion des Services

### **Démarrer/Arrêter**

```bash
# Démarrer tous les services
docker-compose -f docker-compose.microservices.yml up -d

# Arrêter tous les services
docker-compose -f docker-compose.microservices.yml down

# Redémarrer un service spécifique
docker-compose -f docker-compose.microservices.yml restart asmblr-core

# Mettre à jour un service
docker-compose -f docker-compose.microservices.yml up -d --build asmblr-agents
```

### **Logs et Debug**

```bash
# Logs de tous les services
docker-compose -f docker-compose.microservices.yml logs

# Logs d'un service spécifique
docker-compose -f docker-compose.microservices.yml logs -f asmblr-core

# Logs en temps réel avec filtre
docker-compose -f docker-compose.microservices.yml logs -f --tail=100 asmblr-agents

# Entrer dans un container pour debug
docker exec -it asmblr-core /bin/bash
```

### **Base de Données**

```bash
# Se connecter à PostgreSQL
docker exec -it postgres psql -U asmblr -d asmblr

# Sauvegarder la base de données
docker exec postgres pg_dump -U asmblr asmblr > backup.sql

# Restaurer la base de données
docker exec -i postgres psql -U asmblr asmblr < backup.sql
```

### **Cache Redis**

```bash
# Se connecter à Redis
docker exec -it redis redis-cli

# Vider le cache
docker exec -it redis redis-cli FLUSHALL

# Vérifier les clés
docker exec -it redis redis-cli KEYS "*"
```

## 🚨 Dépannage

### **Problèmes Communs**

#### **1. Services ne démarrent pas**

```bash
# Vérifier les ports
netstat -an | grep -E ":(8000|8001|8002|8003|3000)"

# Vérifier les logs d'erreurs
docker-compose -f docker-compose.microservices.yml logs | grep ERROR

# Recréer les containers
docker-compose -f docker-compose.microservices.yml down
docker-compose -f docker-compose.microservices.yml up -d --force-recreate
```

#### **2. Connexion base de données**

```bash
# Vérifier PostgreSQL
docker exec -it postgres pg_isready -U asmblr

# Vérifier la connexion depuis le service core
docker exec -it asmblr-core python -c "
import psycopg2
try:
    conn = psycopg2.connect('postgresql://postgres:5432/asmblr')
    print('Connexion réussie')
except Exception as e:
    print(f'Erreur: {e}')
"
```

#### **3. Ollama non disponible**

```bash
# Vérifier Ollama
curl http://localhost:11434/api/tags

# Redémarrer Ollama
docker-compose -f docker-compose.microservices.yml restart ollama

# Télécharger les modèles manuellement
docker exec -it ollama ollama pull llama3.1:8b
```

#### **4. Performance lente**

```bash
# Vérifier l'utilisation des ressources
docker stats

# Augmenter la mémoire allouée
docker-compose -f docker-compose.microservices.yml down
# Modifier docker-compose.yml pour ajouter mem_limit
docker-compose -f docker-compose.microservices.yml up -d
```

### **Health Checks Automatiques**

```bash
# Script de vérification
cat > health_check.sh << 'EOF'
#!/bin/bash
services=("api-gateway:8000" "asmblr-core:8001" "asmblr-agents:8002" "asmblr-media:8003")

for service in "${services[@]}"; do
    if curl -f -s "http://$service/api/v1/health" > /dev/null; then
        echo "✅ $service - OK"
    else
        echo "❌ $service - FAILED"
    fi
done
EOF

chmod +x health_check.sh
./health_check.sh
```

## 🔄 Mise à Jour

### **1. Mise à jour des services**

```bash
# Récupérer les dernières modifications
git pull origin main

# Mettre à jour les images
docker-compose -f docker-compose.microservices.yml pull

# Reconstruire et redémarrer
docker-compose -f docker-compose.microservices.yml down
docker-compose -f docker-compose.microservices.yml up -d --build
```

### **2. Mise à jour zero-downtime**

```bash
# Mettre à jour service par service
docker-compose -f docker-compose.microservices.yml up -d --build --no-deps asmblr-core
docker-compose -f docker-compose.microservices.yml up -d --no-deps asmblr-agents
docker-compose -f docker-compose.microservices.yml up -d --no-deps asmblr-media
docker-compose -f docker-compose.microservices.yml up -d --no-deps asmblr-ui
```

## 📈 Performance et Scalabilité

### **1. Scaling Horizontal**

```bash
# Scaler un service spécifique
docker-compose -f docker-compose.microservices.yml up -d --scale asmblr-core=3

# Scaler tous les services stateless
docker-compose -f docker-compose.microservices.yml up -d \
  --scale asmblr-agents=2 \
  --scale asmblr-media=2
```

### **2. Configuration Production**

```bash
# Variables d'environnement production
export ENVIRONMENT=production
export LOG_LEVEL=info
export WORKERS=4

# Démarrer avec configuration production
docker-compose -f docker-compose.microservices.yml -f docker-compose.prod.yml up -d
```

## 🔒 Sécurité

### **1. Configuration SSL**

```bash
# Générer certificats auto-signés
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/nginx.key \
  -out nginx/ssl/nginx.crt

# Mettre à jour nginx.conf pour SSL
# Décommenter les lignes SSL dans nginx/nginx.conf
```

### **2. Variables d'environnement sécurisées**

```bash
# Utiliser Docker secrets
echo "asmblr_secure_password" | docker secret create db_password -

# Référencer dans docker-compose.yml
environment:
  POSTGRES_PASSWORD_FILE: /run/secrets/db_password
secrets:
  db_password:
    external: true
```

## 📚 Documentation Complète

### **API Documentation**

- **API Gateway**: http://localhost:8000/docs
- **Core Service**: http://localhost:8001/docs
- **Agents Service**: http://localhost:8002/docs
- **Media Service**: http://localhost:8003/docs

### **Monitoring**

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)

### **Architecture**

- Diagramme complet: `MICROSERVICES_ARCHITECTURE.md`
- Configuration: `docker-compose.microservices.yml`
- Health checks: `/api/v1/health` sur chaque service

---

*Ce guide couvre le déploiement complet de l'architecture micro-services d'Asmblr avec monitoring, sécurité et scalabilité.*
