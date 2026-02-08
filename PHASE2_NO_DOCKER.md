# 🚀 Phase 2: Déploiement Sans Docker

## 🎯 Objectif

Déployer l'architecture micro-services d'Asmblr en utilisant l'environnement Python local au lieu de Docker.

## 📋 État Actuel

- ✅ **Phase 1 terminée** : Qualité de code 100/100
- ✅ **Systèmes créés** : ErrorHandlerV2, SmartLogger, RetryManager
- ✅ **Architecture définie** : 4 micro-services
- ❌ **Docker non disponible** : Docker Desktop inaccessible

## 🔄 Alternative: Déploiement Local

### **Architecture Locale**
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
                    Shared Infrastructure (Local)
            PostgreSQL (5432) | Redis (6379) | Ollama (11434)
```

## 🛠️ Phase 2.1: Préparation de l'Environnement Local

### **1. Installation des Dépendances**
```bash
# Installer PostgreSQL
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Installer Redis
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Installer Ollama
curl -fsSL https://ollama.ai/install.sh | sh
sudo systemctl start ollama
sudo systemctl enable ollama
```

### **2. Configuration de la Base de Données**
```bash
# Créer la base de données
sudo -u postgres createdb asmblr
sudo -u postgres createuser asmblr
sudo -u postgres psql -c "ALTER USER asmblr PASSWORD 'asmblr_secure_password';"

# Créer les tables
sudo -u postgres psql -d asmblr -c "
CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";
CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";
"
```

### **3. Configuration de Redis**
```bash
# Vérifier Redis
redis-cli ping
# Devrait retourner: PONG
```

### **4. Configuration d'Ollama**
```bash
# Télécharger les modèles
ollama pull llama3.1:8b
ollama pull qwen2.5-coder:7b

# Vérifier les modèles
ollama list
```

## 🚀 Phase 2.2: Déploiement des Services

### **Étape 1: Service Core**
```bash
# Créer l'environnement virtuel
cd asmblr-core
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements-core.txt

# Configurer les variables d'environnement
export DATABASE_URL=postgresql://asmblr:asmblr_secure_password@localhost:5432/asmblr
export REDIS_URL=redis://localhost:6379/0
export API_HOST=0.0.0.0
export API_PORT=8001

# Démarrer le service
python -m app.core.main
```

### **Étape 2: Service Agents**
```bash
# Nouveau terminal
cd asmblr-agents
python -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements-agents.txt

# Configurer les variables d'environnement
export REDIS_URL=redis://localhost:6379/0
export OLLAMA_BASE_URL=http://localhost:11434
export DEFAULT_MODEL=llama3.1:8b
export CODE_MODEL=qwen2.5-coder:7b
export API_HOST=0.0.0.0
export API_PORT=8002

# Démarrer le service
python -m app.agents.main
```

### **Étape 3: Service Media**
```bash
# Nouveau terminal
cd asmblr-media
python -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install fastapi uvicorn pillow diffusers torch

# Configurer les variables d'environnement
export REDIS_URL=redis://localhost:6379/0
export STORAGE_TYPE=local
export STORAGE_PATH=./media
export API_HOST=0.0.0.0
export API_PORT=8003

# Démarrer le service
python -m app.media.main
```

### **Étape 4: API Gateway**
```bash
# Nouveau terminal
cd orchestrator
python -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements-gateway.txt

# Configurer les variables d'environnement
export REDIS_URL=redis://localhost:6379/0
export CORE_SERVICE_URL=http://localhost:8001
export AGENTS_SERVICE_URL=http://localhost:8002
export MEDIA_SERVICE_URL=http://localhost:8003
export API_HOST=0.0.0.0
export API_PORT=8000

# Démarrer le service
python -m app.orchestrator.main
```

### **Étape 5: Service UI**
```bash
# Nouveau terminal
cd asmblr-ui
npm install
npm run build

# Configurer les variables d'environnement
export NEXT_PUBLIC_API_URL=http://localhost:8000
export NEXT_PUBLIC_CORE_URL=http://localhost:8001
export NEXT_PUBLIC_AGENTS_URL=http://localhost:8002
export NEXT_PUBLIC_MEDIA_URL=http://localhost:8003

# Démarrer le service
npm run dev
```

## 🧪 Phase 2.3: Tests d'Intégration

### **Test 1: Health Checks**
```bash
# Script de test
cat > test_services.sh << 'EOF'
#!/bin/bash
echo "🧪 Tests d'intégration des services..."
echo "=" * 50

services=(
    "API Gateway:http://localhost:8000/api/v1/health"
    "Core Service:http://localhost:8001/api/v1/health"
    "Agents Service:http://localhost:8002/api/v1/health"
    "Media Service:http://localhost:8003/api/v1/health"
)

for service in "${services[@]}"; do
    name=$(echo $service | cut -d: -f1)
    url=$(echo $service | cut -d: -f2)
    
    if curl -f -s "$url" > /dev/null; then
        echo "✅ $name - OK"
    else
        echo "❌ $name - FAILED"
    fi
done
EOF

chmod +x test_services.sh
./test_services.sh
```

### **Test 2: Communication Inter-Services**
```bash
# Test création de pipeline
curl -X POST http://localhost:8000/api/v1/core/pipelines \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "AI compliance for SMBs",
    "config": {"mode": "standard"}
  }'

# Test exécution d'agent
curl -X POST http://localhost:8000/api/v1/agents/crew \
  -H "Content-Type: application/json" \
  -d '{
    "crew_type": "idea_generation",
    "topic": "AI compliance for SMBs",
    "config": {"max_ideas": 5}
  }'
```

## 📊 Phase 2.4: Monitoring Local

### **Monitoring avec les Logs**
```bash
# Logs de chaque service
tail -f asmblr-core/logs/app.log
tail -f asmblr-agents/logs/app.log
tail -f orchestrator/logs/app.log
```

### **Monitoring des Processus**
```bash
# Vérifier les processus
ps aux | grep -E "(python|node)" | grep -E "(8000|8001|8002|8003|3000)"

# Utilisation des ressources
htop
```

## 🔧 Phase 2.5: Scripts de Déploiement Automatisés

### **Script de Démarrage Complet**
```bash
cat > start_all_services.sh << 'EOF'
#!/bin/bash
echo "🚀 Démarrage de tous les services Asmblr..."
echo "=" * 60

# Fonction pour démarrer un service en arrière-plan
start_service() {
    local service_name=$1
    local command=$2
    local log_file=$3
    
    echo "Démarrage de $service_name..."
    nohup $command > $log_file 2>&1 &
    echo "$service_name démarré (PID: $!)"
    sleep 2
}

# Démarrer les services
start_service "Core Service" "cd asmblr-core && source venv/bin/activate && python -m app.core.main" "core.log"
start_service "Agents Service" "cd asmblr-agents && source venv/bin/activate && python -m app.agents.main" "agents.log"
start_service "Media Service" "cd asmblr-media && source venv/bin/activate && python -m app.media.main" "media.log"
start_service "API Gateway" "cd orchestrator && source venv/bin/activate && python -m app.orchestrator.main" "gateway.log"
start_service "UI Service" "cd asmblr-ui && npm run dev" "ui.log"

echo "Tous les services démarrés !"
echo ""
echo "🌐 URLs d'accès:"
echo "  API Gateway: http://localhost:8000"
echo "  Core Service: http://localhost:8001"
echo "  Agents Service: http://localhost:8002"
echo "  Media Service: http://localhost:8003"
echo "  UI: http://localhost:3000"
EOF

chmod +x start_all_services.sh
```

### **Script d'Arrêt Complet**
```bash
cat > stop_all_services.sh << 'EOF'
#!/bin/bash
echo "🛑 Arrêt de tous les services Asmblr..."
echo "=" * 60

# Arrêter les processus Python et Node
pkill -f "python -m app.core.main"
pkill -f "python -m app.agents.main"
pkill -f "python -m app.media.main"
pkill -f "python -m app.orchestrator.main"
pkill -f "npm run dev"

echo "Tous les services arrêtés !"
EOF

chmod +x stop_all_services.sh
```

## 📈 Phase 2.6: Validation Finale

### **Checklist de Validation**
- [ ] PostgreSQL installé et configuré
- [ ] Redis installé et fonctionnel
- [ ] Ollama installé avec modèles
- [ ] Services Core démarrés et accessibles
- [ ] Services Agents démarrés et accessibles
- [ ] Services Media démarrés et accessibles
- [ ] API Gateway fonctionnelle
- [ ] UI accessible
- [ ] Tests d'intégration passants

### **Métriques de Succès**
- **Uptime**: > 99%
- **Response time**: < 2 secondes
- **Error rate**: < 1%
- **Services actifs**: 5/5

## 🎯 Prochaines Étapes

Une fois la Phase 2 terminée avec succès :

1. **Phase 3: Optimisation** - Activer le monitoring avancé
2. **Migration des données** - Transférer depuis le monolithe
3. **Tests de charge** - Valider la performance
4. **Documentation** - Finaliser la documentation

## 🚀 Instructions Immédiates

1. **Préparer l'environnement local**
2. **Installer PostgreSQL, Redis, Ollama**
3. **Utiliser les scripts de déploiement**
4. **Tester les services individuellement**
5. **Valider l'intégration complète**

---

*Cette approche sans Docker permet de déployer l'architecture micro-services en utilisant l'environnement Python local, contournant les problèmes de Docker Desktop.*
