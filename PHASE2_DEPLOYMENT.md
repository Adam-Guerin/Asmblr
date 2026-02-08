# 🚀 Phase 2: Déploiement Micro-services

## 🎯 Objectif

Déployer l'architecture micro-services d'Asmblr pour une meilleure scalabilité et maintenabilité.

## 📋 Phase 2.1: Préparation de l'Infrastructure

### **1. Vérification des Prérequis**
```bash
# Vérifier Docker
docker --version
docker-compose --version

# Ports requis
netstat -an | grep -E ":(8000|8001|8002|8003|3000|5432|6379|11434)" || echo "Ports disponibles"

# Espace disque
df -h . | grep -E "(Filesystem|/dev/)"
```

### **2. Configuration de l'Environnement**
```bash
# Créer le fichier d'environnement
cat > .env.microservices << 'EOF'
# API Gateway
API_GATEWAY_HOST=0.0.0.0
API_GATEWAY_PORT=8000

# Services
CORE_SERVICE_URL=http://asmblr-core:8001
AGENTS_SERVICE_URL=http://asmblr-agents:8002
MEDIA_SERVICE_URL=http://asmblr-media:8003
UI_SERVICE_URL=http://asmblr-ui:3000

# Base de données
DATABASE_URL=postgresql://asmblr:asmblr_password@postgres:5432/asmblr
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

# UI
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
```

## 🏗️ Phase 2.2: Déploiement de l'Infrastructure

### **Étape 1: Démarrer les Services de Base**
```bash
# Créer les réseaux et volumes
docker network create asmblr-network 2>/dev/null || true
docker volume create postgres_data 2>/dev/null || true
docker volume create redis_data 2>/dev/null || true
docker volume create ollama_data 2>/dev/null || true

# Démarrer PostgreSQL
docker run -d \
  --name asmblr-postgres \
  --network asmblr-network \
  -e POSTGRES_DB=asmblr \
  -e POSTGRES_USER=asmblr \
  -e POSTGRES_PASSWORD=asmblr_secure_password \
  -v postgres_data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:15-alpine

# Démarrer Redis
docker run -d \
  --name asmblr-redis \
  --network asmblr-network \
  -v redis_data:/data \
  -p 6379:6379 \
  redis:7-alpine

# Démarrer Ollama
docker run -d \
  --name asmblr-ollama \
  --network asmblr-network \
  -v ollama_data:/root/.ollama \
  -p 11434:11434 \
  ollama/ollama
```

### **Étape 2: Vérification de l'Infrastructure**
```bash
# Attendre le démarrage des services
sleep 10

# Vérifier PostgreSQL
docker exec asmblr-postgres pg_isready -U asmblr

# Vérifier Redis
docker exec asmblr-redis redis-cli ping

# Vérifier Ollama
curl http://localhost:11434/api/tags

# Télécharger les modèles requis
docker exec asmblr-ollama ollama pull llama3.1:8b
docker exec asmblr-ollama ollama pull qwen2.5-coder:7b
```

## 🔧 Phase 2.3: Déploiement des Services

### **Étape 3: Service Core**
```bash
# Construire l'image du service core
cd asmblr-core
docker build -t asmblr-core:latest .

# Démarrer le service core
docker run -d \
  --name asmblr-core \
  --network asmblr-network \
  -e DATABASE_URL=postgresql://asmblr:asmblr_secure_password@postgres:5432/asmblr \
  -e REDIS_URL=redis://redis:6379/0 \
  -e API_HOST=0.0.0.0 \
  -e API_PORT=8001 \
  -p 8001:8001 \
  asmblr-core:latest

# Vérifier le service core
curl http://localhost:8001/api/v1/health
```

### **Étape 4: Service Agents**
```bash
# Construire l'image du service agents
cd ../asmblr-agents
docker build -t asmblr-agents:latest .

# Démarrer le service agents
docker run -d \
  --name asmblr-agents \
  --network asmblr-network \
  -e REDIS_URL=redis://redis:6379/0 \
  -e OLLAMA_BASE_URL=http://ollama:11434 \
  -e DEFAULT_MODEL=llama3.1:8b \
  -e API_HOST=0.0.0.0 \
  -e API_PORT=8002 \
  -p 8002:8002 \
  asmblr-agents:latest

# Vérifier le service agents
curl http://localhost:8002/api/v1/health
```

### **Étape 5: Service Media**
```bash
# Construire l'image du service media
cd ../asmblr-media
docker build -t asmblr-media:latest .

# Démarrer le service media
docker run -d \
  --name asmblr-media \
  --network asmblr-network \
  -e REDIS_URL=redis://redis:6379/0 \
  -e STORAGE_TYPE=local \
  -e STORAGE_PATH=/app/media \
  -e API_HOST=0.0.0.0 \
  -e API_PORT=8003 \
  -p 8003:8003 \
  asmblr-media:latest

# Vérifier le service media
curl http://localhost:8003/api/v1/health
```

### **Étape 6: API Gateway**
```bash
# Construire l'image de l'API Gateway
cd ../orchestrator
docker build -t asmblr-gateway:latest .

# Démarrer l'API Gateway
docker run -d \
  --name asmblr-gateway \
  --network asmblr-network \
  -e REDIS_URL=redis://redis:6379/0 \
  -e CORE_SERVICE_URL=http://asmblr-core:8001 \
  -e AGENTS_SERVICE_URL=http://asmblr-agents:8002 \
  -e MEDIA_SERVICE_URL=http://asmblr-media:8003 \
  -e API_HOST=0.0.0.0 \
  -e API_PORT=8000 \
  -p 8000:8000 \
  asmblr-gateway:latest

# Vérifier l'API Gateway
curl http://localhost:8000/api/v1/health
```

### **Étape 7: Service UI**
```bash
# Construire l'image du service UI
cd ../asmblr-ui
docker build -t asmblr-ui:latest .

# Démarrer le service UI
docker run -d \
  --name asmblr-ui \
  --network asmblr-network \
  -e NEXT_PUBLIC_API_URL=http://localhost:8000 \
  -p 3000:3000 \
  asmblr-ui:latest

# Vérifier le service UI
curl http://localhost:3000
```

## 🧪 Phase 2.4: Tests d'Intégration

### **Test 1: Health Checks**
```bash
#!/bin/bash
# Script de test des services
services=(
    "API Gateway:http://localhost:8000/api/v1/health"
    "Core Service:http://localhost:8001/api/v1/health"
    "Agents Service:http://localhost:8002/api/v1/health"
    "Media Service:http://localhost:8003/api/v1/health"
    "UI Service:http://localhost:3000"
)

echo "🧪 Tests d'intégration des services..."
echo "=" * 50

for service in "${services[@]}"; do
    name=$(echo $service | cut -d: -f1)
    url=$(echo $service | cut -d: -f2-)
    
    if curl -f -s "$url" > /dev/null; then
        echo "✅ $name - OK"
    else
        echo "❌ $name - FAILED"
    fi
done
```

### **Test 2: Communication Inter-Services**
```bash
# Test de création de pipeline via API Gateway
curl -X POST http://localhost:8000/api/v1/core/pipelines \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AI compliance for SMBs",
    "config": {"mode": "standard"}
  }'

# Test d'exécution d'agent via API Gateway
curl -X POST http://localhost:8000/api/v1/agents/crew \
  -H "Content-Type: application/json" \
  -d '{
    "crew_type": "idea_generation",
    "topic": "AI compliance for SMBs",
    "config": {"max_ideas": 5}
  }'
```

### **Test 3: Performance**
```bash
# Test de charge simple
for i in {1..10}; do
    curl -X POST http://localhost:8000/api/v1/core/pipelines \
      -H "Content-Type: application/json" \
      -d "{\"topic\": \"Test topic $i\", \"config\": {}}" \
      -o /dev/null -s -w "Request $i: %{time_total}s\n"
done
```

## 📊 Phase 2.5: Monitoring

### **Déploiement de Prometheus**
```bash
# Démarrer Prometheus
docker run -d \
  --name asmblr-prometheus \
  --network asmblr-network \
  -v $(pwd)/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml \
  -p 9090:9090 \
  prom/prometheus
```

### **Déploiement de Grafana**
```bash
# Démarrer Grafana
docker run -d \
  --name asmblr-grafana \
  --network asmblr-network \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  -p 3001:3000 \
  grafana/grafana
```

### **Accès au Monitoring**
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)

## 📈 Phase 2.6: Validation Finale

### **Checklist de Déploiement**
- [ ] Infrastructure démarrée (PostgreSQL, Redis, Ollama)
- [ ] Services core déployés (Core, Agents, Media, Gateway, UI)
- [ ] Health checks passants
- [ ] Communication inter-services fonctionnelle
- [ ] Monitoring actif
- [ ] Documentation accessible

### **Métriques de Succès**
- **Uptime**: > 99%
- **Response time**: < 2 secondes
- **Error rate**: < 1%
- **Services actifs**: 5/5

## 🚨 Gestion des Problèmes

### **Services ne démarrent pas**
```bash
# Vérifier les logs
docker logs asmblr-core
docker logs asmblr-agents
docker logs asmblr-gateway

# Redémarrer un service
docker restart asmblr-core

# Recréer un service
docker rm -f asmblr-core
docker run -d ... # commande de départ
```

### **Problèmes de réseau**
```bash
# Vérifier le réseau
docker network ls
docker network inspect asmblr-network

# Recréer le réseau
docker network rm asmblr-network
docker network create asmblr-network
```

### **Problèmes de base de données**
```bash
# Se connecter à PostgreSQL
docker exec -it asmblr-postgres psql -U asmblr -d asmblr

# Vérifier les tables
\dt

# Vider et recréer
docker exec asmblr-postgres psql -U asmblr -d asmblr -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
```

---

## 🎯 Prochaine Étape

Une fois la Phase 2 terminée avec succès :

1. **Phase 3: Optimisation** - Activer le monitoring avancé et l'auto-optimisation
2. **Migration des données** - Transférer les données du monolithe vers les micro-services
3. **Tests de charge** - Valider la performance sous charge
4. **Documentation** - Finaliser la documentation d'exploitation

---

*Ce guide couvre le déploiement complet de l'architecture micro-services d'Asmblr.*
