"""
Asmblr Lightweight Mode - Service unifié optimisé pour les ressources limitées
Combine Core, Agents et Media en un seul service léger
"""

import os
import asyncio
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from loguru import logger
from prometheus_client import Counter, Histogram, generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST

# Configuration lightweight
MODE = os.getenv("MODE", "lightweight")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/asmblr.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "2"))
CACHE_SIZE = int(os.getenv("CACHE_SIZE", "100"))
ENABLE_MONITORING = os.getenv("ENABLE_MONITORING", "false").lower() == "true"
ENABLE_MEDIA_GENERATION = os.getenv("ENABLE_MEDIA_GENERATION", "false").lower() == "true"

# Configuration du logger
logger.remove()
logger.add(
    "logs/asmblr.log",
    rotation="10 MB",
    retention="1 day",
    level=LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)
logger.add(lambda msg: print(msg, end=""), level=LOG_LEVEL)

# Métriques (si monitoring activé)
registry = CollectorRegistry()
REQUEST_COUNT = Counter('asmblr_requests_total', 'Total requests', ['method', 'endpoint'], registry=registry)
REQUEST_DURATION = Histogram('asmblr_request_duration_seconds', 'Request duration', registry=registry)

# Clients
redis_client = None
db_connection = None


# Models Pydantic
class PipelineCreate(BaseModel):
    topic: str = Field(..., description="Topic for the pipeline")
    mode: str = Field(default="quick", description="Execution mode")
    config: Optional[Dict[str, Any]] = Field(default={}, description="Pipeline configuration")


class PipelineResponse(BaseModel):
    id: str
    topic: str
    mode: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    config: Dict[str, Any]


class TaskRequest(BaseModel):
    task_type: str = Field(..., description="Type of task")
    input_data: Dict[str, Any] = Field(..., description="Input data")
    config: Optional[Dict[str, Any]] = Field(default={}, description="Task configuration")


class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float


class LightweightCache:
    """Cache mémoire simple pour le mode lightweight"""
    
    def __init__(self, max_size: int = CACHE_SIZE):
        self.cache = {}
        self.max_size = max_size
        self.access_times = {}
    
    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            self.access_times[key] = datetime.utcnow()
            return self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        if len(self.cache) >= self.max_size:
            # Supprimer l'entrée la moins récemment utilisée
            oldest_key = min(self.access_times, key=self.access_times.get)
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
        
        self.cache[key] = value
        self.access_times[key] = datetime.utcnow()
        
        # TTL simple (en production, utiliser un vrai système)
        asyncio.create_task(self._expire_key(key, ttl))
    
    async def _expire_key(self, key: str, ttl: int) -> None:
        await asyncio.sleep(ttl)
        if key in self.cache:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]


# Cache global
cache = LightweightCache()


class LightweightDatabase:
    """Base de données SQLite simple pour le mode lightweight"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self) -> None:
        """Initialise la base de données"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pipelines (
                    id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    mode TEXT DEFAULT 'quick',
                    status TEXT DEFAULT 'created',
                    config TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    task_type TEXT NOT NULL,
                    input_data TEXT NOT NULL,
                    result TEXT,
                    error TEXT,
                    status TEXT DEFAULT 'pending',
                    execution_time REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_pipelines_status ON pipelines(status)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)
            """)
    
    def create_pipeline(self, pipeline_data: PipelineCreate) -> str:
        """Crée un pipeline"""
        pipeline_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO pipelines (id, topic, mode, status, config)
                VALUES (?, ?, ?, 'created', ?)
            """, (pipeline_id, pipeline_data.topic, pipeline_data.mode, json.dumps(pipeline_data.config)))
        
        return pipeline_id
    
    def get_pipeline(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """Récupère un pipeline"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM pipelines WHERE id = ?
            """, (pipeline_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    "id": row["id"],
                    "topic": row["topic"],
                    "mode": row["mode"],
                    "status": row["status"],
                    "config": json.loads(row["config"]),
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                }
        return None
    
    def list_pipelines(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Liste les pipelines"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM pipelines 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            return [
                {
                    "id": row["id"],
                    "topic": row["topic"],
                    "mode": row["mode"],
                    "status": row["status"],
                    "config": json.loads(row["config"]),
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"]
                }
                for row in cursor.fetchall()
            ]
    
    def create_task(self, task_data: TaskRequest) -> str:
        """Crée une tâche"""
        task_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO tasks (id, task_type, input_data, status)
                VALUES (?, ?, ?, 'pending')
            """, (task_id, task_data.task_type, json.dumps(task_data.input_data)))
        
        return task_id
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Met à jour une tâche"""
        set_clauses = []
        params = []
        
        for key, value in updates.items():
            set_clauses.append(f"{key} = ?")
            if key in ["result", "error"]:
                params.append(json.dumps(value) if isinstance(value, (dict, list)) else str(value))
            else:
                params.append(value)
        
        params.append(task_id)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"""
                UPDATE tasks 
                SET {', '.join(set_clauses)}, completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, params)
        
        return True


# Base de données globale
db = LightweightDatabase(DATABASE_URL.replace("sqlite:///", ""))


class LightweightLLMService:
    """Service LLM simplifié pour le mode lightweight"""
    
    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.default_model = "llama3.1:8b"
        self.cache = cache
    
    async def generate_text(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Génère du texte avec cache"""
        model = model or self.default_model
        cache_key = f"llm:{model}:{hash(prompt)}"
        
        # Vérifier le cache
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"LLM cache hit for model {model}")
            return cached_result
        
        # Simuler l'appel LLM (en production, faire un vrai appel HTTP)
        await asyncio.sleep(1.0)  # Simulation
        
        result = {
            "text": f"Simulated response for: {prompt[:100]}...",
            "model": model,
            "tokens_used": len(prompt.split()) + 50,
            "generation_time": 1.0
        }
        
        # Mettre en cache
        cache.set(cache_key, result, ttl=300)
        
        return result


class LightweightPipelineService:
    """Service pipeline simplifié"""
    
    def __init__(self):
        self.llm_service = LightweightLLMService()
        self.db = db
        self.cache = cache
    
    async def execute_pipeline(self, pipeline_id: str) -> Dict[str, Any]:
        """Exécute un pipeline en mode lightweight"""
        pipeline = self.db.get_pipeline(pipeline_id)
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Mettre à jour le statut
            self.db.update_task(pipeline_id, {"status": "running"})
            
            # Étapes simplifiées
            steps = [
                {"name": "research", "duration": 2.0},
                {"name": "analysis", "duration": 1.5},
                {"name": "generation", "duration": 3.0}
            ]
            
            results = {}
            
            for step in steps:
                step_start = asyncio.get_event_loop().time()
                
                # Simuler le travail
                await asyncio.sleep(step["duration"])
                
                # Générer du contenu simple
                if step["name"] == "research":
                    result = await self.llm_service.generate_text(
                        f"Research about {pipeline['topic']}"
                    )
                elif step["name"] == "analysis":
                    result = await self.llm_service.generate_text(
                        f"Analysis of {pipeline['topic']}"
                    )
                else:
                    result = await self.llm_service.generate_text(
                        f"Generate content for {pipeline['topic']}"
                    )
                
                step_duration = asyncio.get_event_loop().time() - step_start
                results[step["name"]] = {
                    "status": "completed",
                    "duration": step_duration,
                    "output": result["text"]
                }
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            # Mettre à jour le statut final
            self.db.update_task(pipeline_id, {
                "status": "completed",
                "result": results,
                "execution_time": execution_time
            })
            
            return {
                "pipeline_id": pipeline_id,
                "status": "completed",
                "execution_time": execution_time,
                "steps": results,
                "output": {
                    "summary": f"Lightweight execution completed for {pipeline['topic']}",
                    "mode": "lightweight",
                    "steps_count": len(steps)
                }
            }
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            
            self.db.update_task(pipeline_id, {
                "status": "failed",
                "error": str(e),
                "execution_time": execution_time
            })
            
            logger.error(f"Pipeline execution failed: {e}")
            raise


# Services globaux
pipeline_service = LightweightPipelineService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie"""
    global redis_client
    
    logger.info(f"Starting Asmblr in {MODE} mode...")
    
    # Initialiser Redis (optionnel)
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        await redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis not available: {e}")
        redis_client = None
    
    logger.info(f"Asmblr {MODE} mode ready!")
    
    yield
    
    # Nettoyage
    logger.info("Shutting down Asmblr...")
    if redis_client:
        await redis_client.close()


app = FastAPI(
    title="Asmblr Lightweight",
    description="Optimized version for resource-constrained environments",
    version="3.0.0",
    lifespan=lifespan
)


# Middleware de monitoring léger
@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    """Middleware simplifié pour le monitoring"""
    if ENABLE_MONITORING:
        start_time = asyncio.get_event_loop().time()
        
        response = await call_next(request)
        
        duration = asyncio.get_event_loop().time() - start_time
        
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path
        ).inc()
        REQUEST_DURATION.observe(duration)
        
        response.headers["X-Response-Time"] = f"{duration:.3f}"
        response.headers["X-Mode"] = MODE
        
        return response
    else:
        return await call_next(request)


# API Endpoints
@app.get("/health")
async def health_check():
    """Health check"""
    redis_status = "ok" if redis_client else "not_connected"
    db_status = "ok" if os.path.exists(DATABASE_URL.replace("sqlite:///", "")) else "error"
    
    return {
        "status": "healthy" if db_status == "ok" else "unhealthy",
        "mode": MODE,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "3.0.0",
        "services": {
            "redis": redis_status,
            "database": db_status
        },
        "config": {
            "max_workers": MAX_WORKERS,
            "cache_size": CACHE_SIZE,
            "monitoring": ENABLE_MONITORING,
            "media_generation": ENABLE_MEDIA_GENERATION
        }
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check"""
    return {
        "status": "ready",
        "mode": MODE,
        "timestamp": datetime.utcnow().isoformat()
    }


# Pipeline endpoints
@app.post("/api/v1/pipelines", response_model=PipelineResponse)
async def create_pipeline(pipeline: PipelineCreate):
    """Crée un pipeline"""
    try:
        pipeline_id = db.create_pipeline(pipeline)
        
        # Récupérer le pipeline créé
        created_pipeline = db.get_pipeline(pipeline_id)
        
        logger.info(f"Pipeline created: {pipeline_id} - {pipeline.topic}")
        
        return JSONResponse(
            status_code=201,
            content=created_pipeline
        )
        
    except Exception as e:
        logger.error(f"Failed to create pipeline: {e}")
        raise HTTPException(status_code=500, detail="Failed to create pipeline")


@app.get("/api/v1/pipelines", response_model=List[PipelineResponse])
async def list_pipelines(limit: int = 50, offset: int = 0):
    """Liste les pipelines"""
    try:
        pipelines = db.list_pipelines(limit, offset)
        return pipelines
    except Exception as e:
        logger.error(f"Failed to list pipelines: {e}")
        raise HTTPException(status_code=500, detail="Failed to list pipelines")


@app.get("/api/v1/pipelines/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(pipeline_id: str):
    """Récupère un pipeline"""
    try:
        pipeline = db.get_pipeline(pipeline_id)
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        return pipeline
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pipeline {pipeline_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pipeline")


@app.post("/api/v1/pipelines/{pipeline_id}/run")
async def run_pipeline(pipeline_id: str, background_tasks: BackgroundTasks):
    """Exécute un pipeline"""
    try:
        pipeline = db.get_pipeline(pipeline_id)
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        # Lancer l'exécution en arrière-plan
        background_tasks.add_task(pipeline_service.execute_pipeline, pipeline_id)
        
        logger.info(f"Pipeline execution started: {pipeline_id}")
        
        return {
            "pipeline_id": pipeline_id,
            "status": "started",
            "message": "Pipeline execution started",
            "mode": MODE
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start pipeline {pipeline_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start pipeline")


# Task endpoints
@app.post("/api/v1/tasks", response_model=TaskResponse)
async def create_task(task: TaskRequest):
    """Crée une tâche"""
    try:
        task_id = db.create_task(task)
        
        return {
            "task_id": task_id,
            "status": "pending",
            "execution_time": 0.0
        }
        
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        raise HTTPException(status_code=500, detail="Failed to create task")


@app.get("/api/v1/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    """Récupère une tâche"""
    try:
        with sqlite3.connect(DATABASE_URL.replace("sqlite:///", "")) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM tasks WHERE id = ?
            """, (task_id,))
            
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Task not found")
            
            return {
                "task_id": row["id"],
                "status": row["status"],
                "result": json.loads(row["result"]) if row["result"] else None,
                "error": row["error"],
                "execution_time": row["execution_time"] or 0.0
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task")


# Monitoring endpoints (si activé)
@app.get("/metrics")
async def metrics():
    """Endpoint Prometheus pour les métriques"""
    if ENABLE_MONITORING:
        return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)
    else:
        return {"error": "Monitoring is disabled"}


@app.get("/api/v1/stats")
async def get_stats():
    """Statistiques du service"""
    try:
        with sqlite3.connect(DATABASE_URL.replace("sqlite:///", "")) as conn:
            # Compter les pipelines
            pipeline_count = conn.execute("SELECT COUNT(*) FROM pipelines").fetchone()[0]
            
            # Compter les tâches par statut
            task_stats = conn.execute("""
                SELECT status, COUNT(*) FROM tasks GROUP BY status
            """).fetchall()
            
            # Taille du cache
            cache_size = len(cache.cache)
            
            return {
                "mode": MODE,
                "stats": {
                    "pipelines": {
                        "total": pipeline_count
                    },
                    "tasks": dict(task_stats),
                    "cache": {
                        "size": cache_size,
                        "max_size": CACHE_SIZE
                    }
                },
                "config": {
                    "max_workers": MAX_WORKERS,
                    "monitoring": ENABLE_MONITORING,
                    "media_generation": ENABLE_MEDIA_GENERATION
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stats")


if __name__ == "__main__":
    import uvicorn
    from fastapi.responses import Response
    
    logger.info(f"Starting Asmblr in {MODE} mode...")
    
    uvicorn.run(
        "asmblr_lightweight:app",
        host="0.0.0.0",
        port=8000,
        workers=1,
        log_level=LOG_LEVEL.lower(),
        access_log=False  # Réduire le logging en mode lightweight
    )
