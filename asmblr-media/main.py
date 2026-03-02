"""
Media Service - Asset Generation and Management Microservice
Gère la génération de médias, assets et contenu statique
"""

import os
import asyncio
import json
import uuid
from datetime import datetime
from typing import Any
from contextlib import asynccontextmanager
from pathlib import Path

import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from loguru import logger
from prometheus_client import Counter, Histogram, generate_latest

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/2")
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local")
STORAGE_PATH = os.getenv("STORAGE_PATH", "/app/media")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8003"))

# Métriques
MEDIA_GENERATED = Counter('media_generated_total', 'Media generated', ['media_type', 'status'])
UPLOADS_PROCESSED = Counter('uploads_processed_total', 'Uploads processed', ['file_type'])
GENERATION_DURATION = Histogram('media_generation_duration_seconds', 'Media generation duration')

# Clients
redis_client = None

# Storage setup
storage_path = Path(STORAGE_PATH)
storage_path.mkdir(parents=True, exist_ok=True)


# Models Pydantic
class MediaGenerationRequest(BaseModel):
    media_type: str = Field(..., description="Type of media to generate")
    prompt: str = Field(..., description="Prompt for generation")
    config: dict[str, Any] | None = Field(default={}, description="Generation configuration")
    metadata: dict[str, Any] | None = Field(default={}, description="Additional metadata")


class MediaResponse(BaseModel):
    media_id: str
    media_type: str
    status: str
    url: str | None = None
    file_path: str | None = None
    generation_time: float | None = None
    metadata: dict[str, Any] | None = None


class UploadResponse(BaseModel):
    upload_id: str
    filename: str
    file_type: str
    size: int
    url: str
    status: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie"""
    global redis_client
    
    logger.info("Starting Media Service...")
    
    # Initialiser Redis
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        await redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        redis_client = None
    
    # Créer les répertoires de stockage
    (storage_path / "images").mkdir(exist_ok=True)
    (storage_path / "documents").mkdir(exist_ok=True)
    (storage_path / "videos").mkdir(exist_ok=True)
    (storage_path / "audio").mkdir(exist_ok=True)
    (storage_path / "temp").mkdir(exist_ok=True)
    
    logger.info(f"Storage initialized at {storage_path}")
    
    yield
    
    # Nettoyage
    logger.info("Shutting down Media Service...")
    if redis_client:
        await redis_client.close()


app = FastAPI(
    title="Asmblr Media Service",
    description="Media generation and management microservice",
    version="2.0.0",
    lifespan=lifespan
)


async def store_media_metadata(media_id: str, metadata: dict[str, Any]):
    """Stocke les métadonnées d'un média"""
    if redis_client:
        await redis_client.hset(
            f"media:{media_id}",
            mapping=metadata
        )
        await redis_client.expire(f"media:{media_id}", 86400)  # 24h


async def get_media_metadata(media_id: str) -> dict[str, Any] | None:
    """Récupère les métadonnées d'un média"""
    if redis_client:
        metadata = await redis_client.hgetall(f"media:{media_id}")
        return metadata if metadata else None
    return None


async def generate_image(prompt: str, config: dict[str, Any]) -> dict[str, Any]:
    """Génère une image (simulation)"""
    start_time = asyncio.get_event_loop().time()
    
    try:
        # Simuler la génération d'image
        await asyncio.sleep(3.0)  # Simulation
        
        # Créer un fichier image factice
        media_id = str(uuid.uuid4())
        filename = f"{media_id}.png"
        file_path = storage_path / "images" / filename
        
        # Créer un fichier PNG factice (1x1 pixel transparent)
        import base64
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        )
        with open(file_path, "wb") as f:
            f.write(png_data)
        
        generation_time = asyncio.get_event_loop().time() - start_time
        
        # Métadonnées
        metadata = {
            "media_id": media_id,
            "media_type": "image",
            "prompt": prompt,
            "config": config,
            "filename": filename,
            "file_path": str(file_path),
            "file_size": len(png_data),
            "generation_time": generation_time,
            "status": "completed",
            "created_at": datetime.utcnow().isoformat()
        }
        
        await store_media_metadata(media_id, metadata)
        
        MEDIA_GENERATED.labels(media_type="image", status="completed").inc()
        GENERATION_DURATION.observe(generation_time)
        
        return metadata
        
    except Exception as e:
        generation_time = asyncio.get_event_loop().time() - start_time
        MEDIA_GENERATED.labels(media_type="image", status="failed").inc()
        
        logger.error(f"Image generation failed: {e}")
        
        return {
            "media_id": str(uuid.uuid4()),
            "media_type": "image",
            "status": "failed",
            "error": str(e),
            "generation_time": generation_time
        }


async def generate_document(prompt: str, config: dict[str, Any]) -> dict[str, Any]:
    """Génère un document (simulation)"""
    start_time = asyncio.get_event_loop().time()
    
    try:
        # Simuler la génération de document
        await asyncio.sleep(2.0)  # Simulation
        
        media_id = str(uuid.uuid4())
        filename = f"{media_id}.md"
        file_path = storage_path / "documents" / filename
        
        # Créer un document Markdown factice
        content = f"""# Generated Document

## Prompt
{prompt}

## Configuration
{json.dumps(config, indent=2)}

## Generated Content
This is a simulated document generated based on the prompt above.
In a real implementation, this would contain AI-generated content.

---
Generated by Asmblr Media Service
{datetime.utcnow().isoformat()}
"""
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        generation_time = asyncio.get_event_loop().time() - start_time
        
        metadata = {
            "media_id": media_id,
            "media_type": "document",
            "prompt": prompt,
            "config": config,
            "filename": filename,
            "file_path": str(file_path),
            "file_size": len(content.encode('utf-8')),
            "generation_time": generation_time,
            "status": "completed",
            "created_at": datetime.utcnow().isoformat()
        }
        
        await store_media_metadata(media_id, metadata)
        
        MEDIA_GENERATED.labels(media_type="document", status="completed").inc()
        GENERATION_DURATION.observe(generation_time)
        
        return metadata
        
    except Exception as e:
        generation_time = asyncio.get_event_loop().time() - start_time
        MEDIA_GENERATED.labels(media_type="document", status="failed").inc()
        
        logger.error(f"Document generation failed: {e}")
        
        return {
            "media_id": str(uuid.uuid4()),
            "media_type": "document",
            "status": "failed",
            "error": str(e),
            "generation_time": generation_time
        }


# API Endpoints
@app.post("/api/v1/media/generate", response_model=MediaResponse)
async def generate_media(request: MediaGenerationRequest):
    """Génère un média"""
    try:
        # Validation
        if not request.prompt or len(request.prompt.strip()) < 3:
            raise HTTPException(
                status_code=400, 
                detail="Le prompt doit contenir au moins 3 caractères"
            )
        
        if request.media_type not in ["image", "document", "video", "audio"]:
            raise HTTPException(
                status_code=400,
                detail="Type de média non supporté. Types supportés: image, document, video, audio"
            )
        
        logger.info(f"Generating {request.media_type} for prompt: {request.prompt[:100]}...")
        
        # Router vers la fonction de génération appropriée
        if request.media_type == "image":
            result = await generate_image(request.prompt, request.config)
        elif request.media_type == "document":
            result = await generate_document(request.prompt, request.config)
        else:
            # Simulation pour les autres types
            await asyncio.sleep(1.0)
            result = {
                "media_id": str(uuid.uuid4()),
                "media_type": request.media_type,
                "status": "simulated",
                "message": f"Generation of {request.media_type} not yet implemented",
                "generation_time": 1.0
            }
        
        # Construire la réponse
        response = {
            "media_id": result["media_id"],
            "media_type": result["media_type"],
            "status": result["status"],
            "generation_time": result.get("generation_time"),
            "metadata": {
                "prompt": request.prompt,
                "config": request.config,
                "created_at": result.get("created_at")
            }
        }
        
        if result.get("file_path"):
            response["file_path"] = result["file_path"]
            response["url"] = f"/api/v1/media/{result['media_id']}/download"
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Media generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate media")


@app.post("/api/v1/media/upload", response_model=UploadResponse)
async def upload_media(file: UploadFile = File(...)):
    """Upload un fichier média"""
    try:
        # Validation
        if not file.filename:
            raise HTTPException(status_code=400, detail="Aucun fichier fourni")
        
        # Déterminer le type de fichier
        file_ext = Path(file.filename).suffix.lower()
        if file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
            media_type = "image"
            target_dir = storage_path / "images"
        elif file_ext in ['.pdf', '.doc', '.docx', '.txt', '.md']:
            media_type = "document"
            target_dir = storage_path / "documents"
        elif file_ext in ['.mp4', '.avi', '.mov']:
            media_type = "video"
            target_dir = storage_path / "videos"
        elif file_ext in ['.mp3', '.wav', '.ogg']:
            media_type = "audio"
            target_dir = storage_path / "audio"
        else:
            raise HTTPException(status_code=400, detail="Type de fichier non supporté")
        
        # Générer un ID unique
        upload_id = str(uuid.uuid4())
        safe_filename = f"{upload_id}_{file.filename}"
        file_path = target_dir / safe_filename
        
        # Sauvegarder le fichier
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Métadonnées
        metadata = {
            "upload_id": upload_id,
            "original_filename": file.filename,
            "safe_filename": safe_filename,
            "file_path": str(file_path),
            "file_size": len(content),
            "media_type": media_type,
            "content_type": file.content_type,
            "status": "uploaded",
            "uploaded_at": datetime.utcnow().isoformat()
        }
        
        await store_media_metadata(upload_id, metadata)
        
        UPLOADS_PROCESSED.labels(file_type=media_type).inc()
        
        logger.info(f"File uploaded: {file.filename} ({media_type}, {len(content)} bytes)")
        
        return {
            "upload_id": upload_id,
            "filename": file.filename,
            "file_type": media_type,
            "size": len(content),
            "url": f"/api/v1/media/{upload_id}/download",
            "status": "uploaded"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload file")


@app.get("/api/v1/media/{media_id}/download")
async def download_media(media_id: str):
    """Télécharge un média"""
    try:
        metadata = await get_media_metadata(media_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Média non trouvé")
        
        file_path = Path(metadata.get("file_path", ""))
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Fichier non trouvé")
        
        return FileResponse(
            path=str(file_path),
            filename=metadata.get("original_filename", file_path.name),
            media_type=metadata.get("content_type", "application/octet-stream")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Media download failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to download media")


@app.get("/api/v1/media/{media_id}/info")
async def get_media_info(media_id: str):
    """Récupère les informations d'un média"""
    try:
        metadata = await get_media_metadata(media_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Média non trouvé")
        
        return {
            "media_id": media_id,
            "metadata": metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get media info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get media info")


@app.get("/api/v1/media/list")
async def list_media(media_type: str | None = None, limit: int = 50, offset: int = 0):
    """Liste les médias"""
    try:
        if not redis_client:
            return {"media": [], "total": 0}
        
        # Récupérer toutes les clés de médias
        keys = await redis_client.keys("media:*")
        media_list = []
        
        for key in keys[offset:offset+limit]:
            metadata = await redis_client.hgetall(key)
            if metadata and (media_type is None or metadata.get("media_type") == media_type):
                media_list.append({
                    "media_id": key.replace("media:", ""),
                    **metadata
                })
        
        return {
            "media": media_list,
            "total": len(keys),
            "limit": limit,
            "offset": offset,
            "media_type": media_type
        }
        
    except Exception as e:
        logger.error(f"Failed to list media: {e}")
        raise HTTPException(status_code=500, detail="Failed to list media")


@app.delete("/api/v1/media/{media_id}")
async def delete_media(media_id: str):
    """Supprime un média"""
    try:
        metadata = await get_media_metadata(media_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Média non trouvé")
        
        # Supprimer le fichier
        file_path = Path(metadata.get("file_path", ""))
        if file_path.exists():
            file_path.unlink()
        
        # Supprimer les métadonnées
        if redis_client:
            await redis_client.delete(f"media:{media_id}")
        
        logger.info(f"Media deleted: {media_id}")
        
        return {"message": "Média supprimé avec succès"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete media: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete media")


@app.get("/api/v1/media/stats")
async def get_media_stats():
    """Statistiques du service média"""
    try:
        if not redis_client:
            return {"error": "Redis not available"}
        
        # Compter les médias par type
        keys = await redis_client.keys("media:*")
        stats = {
            "total_media": len(keys),
            "by_type": {},
            "by_status": {},
            "storage_usage": {}
        }
        
        for key in keys:
            metadata = await redis_client.hgetall(key)
            if metadata:
                media_type = metadata.get("media_type", "unknown")
                status = metadata.get("status", "unknown")
                file_size = int(metadata.get("file_size", 0))
                
                # Compter par type
                stats["by_type"][media_type] = stats["by_type"].get(media_type, 0) + 1
                
                # Compter par statut
                stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
                
                # Usage de stockage
                stats["storage_usage"][media_type] = stats["storage_usage"].get(media_type, 0) + file_size
        
        return {
            "service": "asmblr-media",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get media stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get media stats")


# Health checks
@app.get("/health")
async def health_check():
    """Health check du service"""
    redis_status = "unknown"
    storage_status = "unknown"
    
    # Vérifier Redis
    try:
        if redis_client:
            await redis_client.ping()
            redis_status = "ok"
        else:
            redis_status = "not_connected"
    except Exception as e:
        redis_status = f"error: {str(e)}"
    
    # Vérifier le stockage
    try:
        if storage_path.exists() and storage_path.is_dir():
            storage_status = "ok"
        else:
            storage_status = "not_accessible"
    except Exception as e:
        storage_status = f"error: {str(e)}"
    
    return {
        "status": "healthy" if redis_status == "ok" and storage_status == "ok" else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "services": {
            "redis": redis_status,
            "storage": storage_status
        }
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check"""
    try:
        if redis_client:
            await redis_client.ping()
        
        if not storage_path.exists():
            return {
                "status": "not_ready",
                "error": "Storage path not accessible",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Métriques
@app.get("/metrics")
async def metrics():
    """Endpoint Prometheus pour les métriques"""
    return Response(generate_latest(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    from fastapi.responses import Response
    
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=False,
        log_level="info"
    )
