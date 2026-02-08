"""
API Gateway pour Asmblr - Point d'entrée unique pour les micro-services
Gère le routing, l'authentification, le rate limiting et le monitoring
"""

import os
import time
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

import fastapi
import httpx
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Request, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from loguru import logger

# Configuration
CORE_SERVICE_URL = os.getenv("CORE_SERVICE_URL", "http://asmblr-core:8000")
AGENTS_SERVICE_URL = os.getenv("AGENTS_SERVICE_URL", "http://asmblr-agents:8000")
MEDIA_SERVICE_URL = os.getenv("MEDIA_SERVICE_URL", "http://asmblr-media:8000")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/3")
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))

# Métriques Prometheus
REQUEST_COUNT = Counter('api_gateway_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('api_gateway_request_duration_seconds', 'Request duration')
ACTIVE_CONNECTIONS = Gauge('api_gateway_active_connections', 'Active connections')
RATE_LIMIT_HITS = Counter('api_gateway_rate_limit_hits_total', 'Rate limit hits')

# Client HTTP pour les services
http_client = None
redis_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application"""
    global http_client, redis_client
    
    # Démarrage
    logger.info("Starting API Gateway...")
    
    # Initialiser les clients
    http_client = httpx.AsyncClient(timeout=30.0)
    
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        await redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        redis_client = None
    
    # Vérifier les services
    await check_services_health()
    
    yield
    
    # Arrêt
    logger.info("Shutting down API Gateway...")
    if http_client:
        await http_client.aclose()
    if redis_client:
        await redis_client.close()


# Créer l'application FastAPI
app = FastAPI(
    title="Asmblr API Gateway",
    description="API Gateway for Asmblr Microservices",
    version="2.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


class RateLimiter:
    """Gestionnaire de rate limiting avec Redis"""
    
    def __init__(self):
        self.redis = redis_client
    
    async def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Vérifie si la requête est autorisée"""
        if not self.redis:
            return True  # Fallback si Redis indisponible
        
        try:
            current_time = int(time.time())
            window_start = current_time - window
            
            # Nettoyer les anciennes entrées
            await self.redis.zremrangebyscore(key, 0, window_start)
            
            # Compter les requêtes dans la fenêtre
            current_requests = await self.redis.zcard(key)
            
            if current_requests >= limit:
                return False
            
            # Ajouter la requête actuelle
            await self.redis.zadd(key, {str(current_time): current_time})
            await self.redis.expire(key, window)
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            return True  # Autoriser en cas d'erreur


rate_limiter = RateLimiter()


@app.middleware("http")
async def middleware(request: Request, call_next):
    """Middleware principal pour le logging, rate limiting et métriques"""
    start_time = time.time()
    client_ip = request.client.host
    
    # Rate limiting
    rate_limit_key = f"rate_limit:{client_ip}"
    if not await rate_limiter.is_allowed(rate_limit_key, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW):
        RATE_LIMIT_HITS.inc()
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded", "retry_after": RATE_LIMIT_WINDOW}
        )
    
    # Métriques
    ACTIVE_CONNECTIONS.inc()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Métriques Prometheus
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        REQUEST_DURATION.observe(duration)
        
        # Headers de monitoring
        response.headers["X-Response-Time"] = f"{duration:.3f}"
        response.headers["X-Gateway-Version"] = "2.0.0"
        
        return response
        
    except Exception as e:
        logger.error(f"Request error: {e}")
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=500
        ).inc()
        raise
    finally:
        ACTIVE_CONNECTIONS.dec()


async def check_services_health():
    """Vérifie la santé des services"""
    services = {
        "core": CORE_SERVICE_URL,
        "agents": AGENTS_SERVICE_URL,
        "media": MEDIA_SERVICE_URL
    }
    
    for name, url in services.items():
        try:
            response = await http_client.get(f"{url}/health", timeout=5.0)
            if response.status_code == 200:
                logger.info(f"Service {name} is healthy")
            else:
                logger.warning(f"Service {name} returned status {response.status_code}")
        except Exception as e:
            logger.error(f"Service {name} health check failed: {e}")


async def proxy_request(service_url: str, path: str, method: str, 
                     headers: Dict[str, str], body: Optional[bytes] = None,
                     query_params: Optional[Dict[str, Any]] = None) -> JSONResponse:
    """Proxy une requête vers un service"""
    try:
        url = f"{service_url}{path}"
        
        # Préparer les headers
        proxy_headers = {k: v for k, v in headers.items() 
                       if k.lower() not in ['host', 'content-length']}
        
        # Faire la requête
        response = await http_client.request(
            method=method,
            url=url,
            headers=proxy_headers,
            content=body,
            params=query_params,
            timeout=30.0
        )
        
        # Retourner la réponse
        return JSONResponse(
            status_code=response.status_code,
            content=response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
            headers=dict(response.headers)
        )
        
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Service timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Service unavailable")
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Routes de routing
@app.api_route("/api/v1/core/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_core(request: Request, path: str):
    """Proxy vers le service core"""
    return await proxy_request(
        service_url=CORE_SERVICE_URL,
        path=f"/api/v1/{path}",
        method=request.method,
        headers=dict(request.headers),
        body=await request.body(),
        query_params=dict(request.query_params)
    )


@app.api_route("/api/v1/agents/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_agents(request: Request, path: str):
    """Proxy vers le service agents"""
    return await proxy_request(
        service_url=AGENTS_SERVICE_URL,
        path=f"/api/v1/{path}",
        method=request.method,
        headers=dict(request.headers),
        body=await request.body(),
        query_params=dict(request.query_params)
    )


@app.api_route("/api/v1/media/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_media(request: Request, path: str):
    """Proxy vers le service media"""
    return await proxy_request(
        service_url=MEDIA_SERVICE_URL,
        path=f"/api/v1/{path}",
        method=request.method,
        headers=dict(request.headers),
        body=await request.body(),
        query_params=dict(request.query_params)
    )


# Routes directes pour les endpoints principaux
@app.post("/api/v1/pipelines")
async def create_pipeline(request: Request):
    """Créer un pipeline - route vers core"""
    return await proxy_request(
        service_url=CORE_SERVICE_URL,
        path="/api/v1/pipelines",
        method="POST",
        headers=dict(request.headers),
        body=await request.body()
    )


@app.get("/api/v1/pipelines")
async def list_pipelines(request: Request):
    """Lister les pipelines - route vers core"""
    return await proxy_request(
        service_url=CORE_SERVICE_URL,
        path="/api/v1/pipelines",
        method="GET",
        headers=dict(request.headers),
        query_params=dict(request.query_params)
    )


@app.get("/api/v1/pipelines/{pipeline_id}")
async def get_pipeline(pipeline_id: str, request: Request):
    """Obtenir un pipeline - route vers core"""
    return await proxy_request(
        service_url=CORE_SERVICE_URL,
        path=f"/api/v1/pipelines/{pipeline_id}",
        method="GET",
        headers=dict(request.headers)
    )


@app.post("/api/v1/pipelines/{pipeline_id}/run")
async def run_pipeline(pipeline_id: str, request: Request):
    """Exécuter un pipeline - route vers agents"""
    return await proxy_request(
        service_url=AGENTS_SERVICE_URL,
        path=f"/api/v1/pipelines/{pipeline_id}/run",
        method="POST",
        headers=dict(request.headers),
        body=await request.body()
    )


# Health checks
@app.get("/health")
async def health_check():
    """Health check du gateway"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "services": {
            "core": CORE_SERVICE_URL,
            "agents": AGENTS_SERVICE_URL,
            "media": MEDIA_SERVICE_URL
        }
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check"""
    services_status = {}
    
    services = {
        "core": CORE_SERVICE_URL,
        "agents": AGENTS_SERVICE_URL,
        "media": MEDIA_SERVICE_URL
    }
    
    for name, url in services.items():
        try:
            response = await http_client.get(f"{url}/health", timeout=2.0)
            services_status[name] = "ok" if response.status_code == 200 else "error"
        except Exception:
            services_status[name] = "error"
    
    all_ready = all(status == "ok" for status in services_status.values())
    
    return {
        "status": "ready" if all_ready else "not_ready",
        "services": services_status,
        "timestamp": datetime.utcnow().isoformat()
    }


# Métriques
@app.get("/metrics")
async def metrics():
    """Endpoint Prometheus pour les métriques"""
    return Response(generate_latest(), media_type="text/plain")


# Routes legacy pour compatibilité
@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_legacy(request: Request, path: str):
    """Proxy legacy pour compatibilité"""
    # Router vers le service approprié basé sur le path
    if path.startswith("pipelines"):
        service_url = CORE_SERVICE_URL
    elif path.startswith("agents") or path.startswith("crew"):
        service_url = AGENTS_SERVICE_URL
    elif path.startswith("media") or path.startswith("assets"):
        service_url = MEDIA_SERVICE_URL
    else:
        service_url = CORE_SERVICE_URL  # Default
    
    return await proxy_request(
        service_url=service_url,
        path=f"/api/v1/{path}",
        method=request.method,
        headers=dict(request.headers),
        body=await request.body(),
        query_params=dict(request.query_params)
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api_gateway:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
