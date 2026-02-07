# Architecture Micro-services d'Asmblr

## 🎯 Objectif

Refactoriser Asmblr en micro-services pour :
- **Séparer les responsabilités** (core, agents, media, ui)
- **Améliorer la maintenabilité** et l'évolutivité
- **Permettre le déploiement indépendant** de chaque service
- **Faciliter les tests** et le debugging

## 🏗️ Architecture Globale

```
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway / Orchestrator                │
├─────────────────────────────────────────────────────────────────┤
│  asmblr-core    │  asmblr-agents  │  asmblr-media  │  asmblr-ui   │
│  (Business)     │  (AI Agents)    │  (Generation) │  (Interface) │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │                 │
         └────────────────┴─────────────────┴─────────────────┘
                    Shared Infrastructure
            (Redis, PostgreSQL, Message Queue)
```

## 📦 Services Détaillés

### 1. **asmblr-core** (Business Logic)
**Responsabilités**:
- Logique métier principale
- Gestion des pipelines
- Validation des données
- Calcul des scores
- Persistance des résultats

**Technologies**:
- FastAPI
- SQLAlchemy + PostgreSQL
- Redis pour le cache
- Pydantic pour la validation

**API Endpoints**:
```
POST   /api/v1/pipelines          # Créer un pipeline
GET    /api/v1/pipelines/{id}      # Récupérer un pipeline
PUT    /api/v1/pipelines/{id}      # Mettre à jour
DELETE /api/v1/pipelines/{id}      # Supprimer
POST   /api/v1/pipelines/{id}/run  # Exécuter un pipeline

GET    /api/v1/topics              # Sujets analysés
GET    /api/v1/topics/{id}         # Détails d'un sujet
POST   /api/v1/topics/{id}/validate # Valider un sujet

GET    /api/v1/metrics             # Métriques globales
GET    /api/v1/health              # Health check
```

### 2. **asmblr-agents** (AI Agents)
**Responsabilités**:
- Gestion des agents CrewAI
- Communication avec les LLM
- Orchestration des agents
- Génération de contenu

**Technologies**:
- FastAPI
- CrewAI
- LangChain
- Ollama client
- Redis pour la communication

**API Endpoints**:
```
POST   /api/v1/agents/crew         # Exécuter CrewAI
GET    /api/v1/agents/status       # Statut des agents
POST   /api/v1/agents/llm          # Appel LLM direct
GET    /api/v1/agents/models        # Modèles disponibles

POST   /api/v1/agents/idea-generate
POST   /api/v1/agents/market-analyze
POST   /api/v1/agents/competitor-analyze
POST   /api/v1/agents/content-generate
```

### 3. **asmblr-media** (Generation)
**Responsabilités**:
- Génération d'images (logos, bannières)
- Génération de vidéos
- Génération de contenu social
- Traitement des médias

**Technologies**:
- FastAPI
- Diffusers (images)
- ImageIO (vidéos)
- Pillow (traitement)
- Stockage S3/Local

**API Endpoints**:
```
POST   /api/v1/media/generate/logo
POST   /api/v1/media/generate/image
POST   /api/v1/media/generate/video
POST   /api/v1/media/generate/social-post
GET    /api/v1/media/jobs/{id}    # Statut génération
GET    /api/v1/media/jobs/{id}/download # Télécharger média

POST   /api/v1/media/process/image
POST   /api/v1/media/vectorize
```

### 4. **asmblr-ui** (Interface)
**Responsabilités**:
- Interface utilisateur principale
- Dashboard de monitoring
- Configuration des pipelines
- Visualisation des résultats

**Technologies**:
- Next.js 14+ (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui
- React Query pour les données

**Pages/Composants**:
- Dashboard principal
- Création/édition de pipelines
- Visualisation des résultats
- Monitoring des services
- Configuration utilisateur

## 🔗 Communication Inter-Services

### 1. **API Gateway / Orchestrator**
```python
# orchestrator/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Asmblr API Gateway")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://asmblr.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router les services
app.include_router(core_router, prefix="/api/v1/core")
app.include_router(agents_router, prefix="/api/v1/agents")
app.include_router(media_router, prefix="/api/v1/media")
app.include_router(ui_router, prefix="/api/v1/ui")
```

### 2. **Message Queue (Redis/RQ)**
```python
# shared/queue.py
import redis
from rq import Queue, Worker
from app.core.config import get_settings

# Configuration Redis
redis_conn = redis.from_url(get_settings().redis_url)
core_queue = Queue("core-tasks", connection=redis_conn)
agents_queue = Queue("agents-tasks", connection=redis_conn)
media_queue = Queue("media-tasks", connection=redis_conn)

# Workers
core_worker = Worker([core_queue], connection=redis_conn)
agents_worker = Worker([agents_queue], connection=redis_conn)
media_worker = Worker([media_queue], connection=redis_conn)
```

### 3. **Shared Database**
```python
# shared/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import get_settings

# Configuration
engine = create_engine(get_settings().database_url)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Tables partagées
class Pipeline(Base):
    __tablename__ = "pipelines"
    id = Column(String, primary_key=True)
    topic = Column(String, nullable=False)
    status = Column(String, nullable=False)
    config = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
```

## 🚀 Déploiement

### 1. **Docker Compose**
```yaml
# docker-compose.microservices.yml
version: '3.8'

services:
  # API Gateway
  api-gateway:
    build: ./orchestrator
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://postgres:5432/asmblr
    depends_on:
      - redis
      - postgres
    networks:
      - asmblr-network

  # Core Service
  asmblr-core:
    build: ./asmblr-core
    environment:
      - DATABASE_URL=postgresql://postgres:5432/asmblr
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
      - postgres
    networks:
      - asmblr-network

  # Agents Service
  asmblr-agents:
    build: ./asmblr-agents
    environment:
      - REDIS_URL=redis://redis:6379/0
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - redis
      - ollama
    networks:
      - asmblr-network

  # Media Service
  asmblr-media:
    build: ./asmblr-media
    environment:
      - REDIS_URL=redis://redis:6379/0
      - STORAGE_TYPE=local  # ou s3
    depends_on:
      - redis
    networks:
      - asmblr-network

  # UI Service
  asmblr-ui:
    build: ./asmblr-ui
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - api-gateway
    networks:
      - asmblr-network

  # Infrastructure
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - asmblr-network

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=asmblr
      - POSTGRES_USER=asmblr
      - POSTGRES_PASSWORD=asmblr_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - asmblr-network

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - asmblr-network

networks:
  asmblr-network:
    driver: bridge

volumes:
  redis_data:
  postgres_data:
  ollama_data:
```

### 2. **Kubernetes**
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: asmblr

---
# k8s/deployments.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: asmblr-core
  namespace: asmblr
spec:
  replicas: 3
  selector:
    matchLabels:
      app: asmblr-core
  template:
    metadata:
      labels:
        app: asmblr-core
    spec:
      containers:
      - name: asmblr-core
        image: asmblr/core:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: asmblr-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: asmblr-config
              key: redis-url
```

## 🔧 Configuration

### 1. **Environment Variables**
```bash
# .env.microservices
# API Gateway
API_GATEWAY_HOST=0.0.0.0
API_GATEWAY_PORT=8000

# Core Service
CORE_SERVICE_URL=http://asmblr-core:8001
DATABASE_URL=postgresql://postgres:5432/asmblr
REDIS_URL=redis://redis:6379/0

# Agents Service
AGENTS_SERVICE_URL=http://asmblr-agents:8002
OLLAMA_BASE_URL=http://ollama:11434
DEFAULT_MODEL=llama3.1:8b
CODE_MODEL=qwen2.5-coder:7b

# Media Service
MEDIA_SERVICE_URL=http://asmblr-media:8003
STORAGE_TYPE=local
STORAGE_PATH=/app/media

# UI Service
UI_SERVICE_URL=http://asmblr-ui:3000
NEXT_PUBLIC_API_URL=http://localhost:8000

# Shared
REDIS_URL=redis://redis:6379/0
DATABASE_URL=postgresql://postgres:5432/asmblr
```

### 2. **Service Discovery**
```python
# shared/discovery.py
import os
from typing import Dict, Any

class ServiceDiscovery:
    """Découverte de services via variables d'environnement"""
    
    @staticmethod
    def get_service_url(service_name: str) -> str:
        """Récupère l'URL d'un service"""
        env_var = f"{service_name.upper()}_SERVICE_URL"
        return os.getenv(env_var, f"http://localhost:800{service_name[-1]}")
    
    @staticmethod
    def get_all_services() -> Dict[str, str]:
        """Récupère toutes les URLs de services"""
        return {
            "core": ServiceDiscovery.get_service_url("asmblr-core"),
            "agents": ServiceDiscovery.get_service_url("asmblr-agents"),
            "media": ServiceDiscovery.get_service_url("asmblr-media"),
            "ui": ServiceDiscovery.get_service_url("asmblr-ui"),
        }
```

## 🧪 Tests

### 1. **Tests d'Intégration**
```python
# tests/integration/test_microservices.py
import pytest
from fastapi.testclient import TestClient
from app.orchestrator.main import app

class TestMicroservicesIntegration:
    def test_api_gateway_health(self):
        """Test que l'API Gateway répond"""
        client = TestClient(app)
        response = client.get("/api/v1/health")
        assert response.status_code == 200
    
    def test_service_communication(self):
        """Test la communication entre services"""
        # Test core -> agents
        # Test agents -> media
        # Test media -> ui
        pass
    
    def test_pipeline_execution(self):
        """Test l'exécution complète d'un pipeline"""
        pipeline_data = {
            "topic": "AI compliance for SMBs",
            "config": {"mode": "standard"}
        }
        
        response = client.post("/api/v1/core/pipelines", json=pipeline_data)
        assert response.status_code == 201
        
        pipeline_id = response.json()["id"]
        
        # Exécuter le pipeline
        response = client.post(f"/api/v1/core/pipelines/{pipeline_id}/run")
        assert response.status_code == 200
```

### 2. **Tests de Charge**
```python
# tests/load/test_performance.py
import asyncio
import aiohttp
import time

async def test_pipeline_throughput():
    """Test le débit du service core"""
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        
        tasks = []
        for i in range(100):
            task = session.post(
                "http://localhost:8001/api/v1/pipelines",
                json={"topic": f"Test topic {i}", "config": {"mode": "fast"}}
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        duration = end_time - start_time
        throughput = len(results) / duration
        
        print(f"Throughput: {throughput:.2f} pipelines/second")
        assert all(r.status == 201 for r in results)
```

## 📈 Monitoring

### 1. **Metrics Collection**
```python
# shared/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Métriques
pipeline_requests_total = Counter('asmblr_pipeline_requests_total')
pipeline_duration_seconds = Histogram('asmblr_pipeline_duration_seconds')
active_pipelines = Gauge('asmblr_active_pipelines')

class MetricsCollector:
    @staticmethod
    def record_pipeline_start():
        pipeline_requests_total.inc()
    
    @staticmethod
    def record_pipeline_completion(duration: float):
        pipeline_duration_seconds.observe(duration)
        active_pipelines.dec()
    
    @staticmethod
    def increment_active_pipelines():
        active_pipelines.inc()
```

### 2. **Health Checks**
```python
# shared/health.py
from fastapi import FastAPI
from sqlalchemy import text
from app.shared.database import SessionLocal, engine

async def check_database_health():
    """Vérifie la connexion à la base de données"""
    try:
        with SessionLocal() as session:
            result = session.execute(text("SELECT 1"))
            return {"status": "healthy", "response": result.scalar()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

async def check_redis_health():
    """Vérifie la connexion à Redis"""
    try:
        import redis
        r = redis.from_url(os.getenv("REDIS_URL"))
        r.ping()
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

## 🚀 Migration Plan

### **Phase 1: Préparation (1 semaine)**
- [ ] Analyser le codebase existant
- [ ] Identifier les dépendances entre modules
- [ ] Créer la structure des micro-services
- [ ] Définir les interfaces

### **Phase 2: Infrastructure (1 semaine)**
- [ ] Configurer Docker Compose
- [ ] Mettre en place Redis et PostgreSQL
- [ ] Configurer les réseaux
- [ ] Tester l'infrastructure

### **Phase 3: Core Service (2 semaines)**
- [ ] Extraire la logique métier
- [ ] Créer l'API FastAPI
- [ ] Implémenter la persistance
- [ ] Ajouter les tests
- [ ] Déployer

### **Phase 4: Agents Service (2 semaines)**
- [ ] Isoler la logique CrewAI
- [ ] Créer l'API des agents
- [ ] Implémenter la communication avec Ollama
- [ ] Ajouter les tests
- [ ] Déployer

### **Phase 5: Media Service (1 semaine)**
- [ ] Isoler la logique de génération
- [ ] Créer l'API média
- [ ] Configurer le stockage
- [ ] Ajouter les tests
- [ ] Déployer

### **Phase 6: UI Service (1 semaine)**
- [ ] Créer l'interface Next.js
- [ ] Connecter à l'API Gateway
- ] Implémenter les pages principales
- [ ] Ajouter les tests
- [ ] Déployer

### **Phase 7: Intégration (1 semaine)**
- [ ] Configurer l'API Gateway
- [ ] Tester les communications
- [ ] Mettre en place le monitoring
- [ ] Documentation
- [ ] Tests E2E

## 📚 Documentation

### **API Documentation**
- OpenAPI/Swagger pour chaque service
- Postman collections
- Exemples d'utilisation
- Guides de déploiement

### **Architecture Documentation**
- Diagrammes d'architecture
- Patterns de communication
- Guidelines de développement
- Processus de release

---

*Cette architecture micro-services transforme Asmblr en une plateforme scalable, maintenable et évolutive.*
