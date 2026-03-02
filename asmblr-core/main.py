"""
Asmblr Core Service - Business Logic Microservice
Logique métier principale d'Asmblr
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime
import asyncio

from app.core.database import get_db
from app.core.models import PipelineCreate, PipelineResponse, PipelineStatus
from app.core.pipeline_service import PipelineService
from app.core.error_handler import handle_errors, ValidationException
from app.core.smart_logger import get_smart_logger, LogLevel
from app.core.config import get_settings


app = FastAPI(
    title="Asmblr Core API",
    description="Business Logic Microservice for Asmblr",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logger = get_smart_logger()

# Security
security = HTTPBearer(auto_error=False)


# Dependency injection
def get_db_session():
    """Dependency pour la session de base de données"""
    return Depends(get_db)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "asmblr-core",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/api/v1/pipelines", response_model=list[PipelineResponse])
@handle_errors("list_pipelines", reraise=True)
async def list_pipelines(
    db: Session = get_db_session(),
    skip: int = 0,
    limit: int = 50,
    status_filter: str | None = None
):
    """
    Lister les pipelines avec pagination et filtres
    """
    logger.start_operation("list_pipelines")
    
    try:
        pipeline_service = PipelineService(db)
        
        # Construire les filtres
        filters = {}
        if status_filter:
            filters["status"] = status_filter
        
        pipelines = pipeline_service.list_pipelines(
            skip=skip,
            limit=limit,
            filters=filters
        )
        
        logger.end_operation("list_pipelines", success=True)
        return pipelines
        
    except Exception as e:
        logger.end_operation("list_pipelines", success=False)
        raise


@app.get("/api/v1/pipelines/{pipeline_id}", response_model=PipelineResponse)
@handle_errors("get_pipeline", reraise=True)
async def get_pipeline(
    pipeline_id: str,
    db: Session = get_db_session()
):
    """
    Récupérer un pipeline spécifique
    """
    logger.start_operation("get_pipeline", metadata={"pipeline_id": pipeline_id})
    
    try:
        pipeline_service = PipelineService(db)
        pipeline = pipeline_service.get_pipeline(pipeline_id)
        
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        logger.end_operation("get_pipeline", success=True)
        return pipeline
        
    except Exception as e:
        logger.end_operation("get_pipeline", success=False)
        raise


@app.post("/api/v1/pipelines", response_model=PipelineResponse)
@handle_errors("create_pipeline", reraise=True)
async def create_pipeline(
    pipeline_data: PipelineCreate,
    db: Session = get_db_session()
):
    """
    Créer un nouveau pipeline
    """
    logger.start_operation("create_pipeline", metadata={"topic": pipeline_data.topic})
    
    try:
        # Validation des données
        if not pipeline_data.topic or len(pipeline_data.topic.strip()) < 3:
            raise ValidationException(
                "Le sujet doit contenir au moins 3 caractères",
                operation="create_pipeline"
            )
        
        pipeline_service = PipelineService(db)
        pipeline = pipeline_service.create_pipeline(pipeline_data)
        
        logger.business(
            LogLevel.MEDIUM,
            "pipeline_created",
            f"Pipeline créé: {pipeline.id} - {pipeline.topic}",
            metadata={
                "pipeline_id": pipeline.id,
                "topic": pipeline.topic,
                "status": pipeline.status
            }
        )
        
        logger.end_operation("create_pipeline", success=True)
        return pipeline
        
    except Exception as e:
        logger.end_operation("create_pipeline", success=False)
        raise


@app.put("/api/v1/pipelines/{pipeline_id}", response_model=PipelineResponse)
@handle_errors("update_pipeline", reraise=True)
async def update_pipeline(
    pipeline_id: str,
    pipeline_data: PipelineCreate,
    db: Session = get_db_session()
):
    """
    Mettre à jour un pipeline existant
    """
    logger.start_operation("update_pipeline", metadata={"pipeline_id": pipeline_id})
    
    try:
        pipeline_service = PipelineService(db)
        pipeline = pipeline_service.update_pipeline(pipeline_id, pipeline_data)
        
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        logger.business(
            LogLevel.MEDIUM,
            "pipeline_updated",
            f"Pipeline mis à jour: {pipeline.id} - {pipeline.topic}",
            metadata={
                "pipeline_id": pipeline.id,
                "topic": pipeline.topic,
                "status": pipeline.status
            }
        )
        
        logger.end_operation("update_pipeline", success=True)
        return pipeline
        
    except Exception as e:
        logger.end_operation("update_pipeline", success=False)
        raise


@app.delete("/api/v1/pipelines/{pipeline_id}")
@handle_errors("delete_pipeline", reraise=True)
async def delete_pipeline(
    pipeline_id: str,
    db: Session = get_db_session()
):
    """
    Supprimer un pipeline
    """
    logger.start_operation("delete_pipeline", metadata={"pipeline_id": pipeline_id})
    
    try:
        pipeline_service = PipelineService(db)
        success = pipeline_service.delete_pipeline(pipeline_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        logger.business(
            LogLevel.MEDIUM,
            "pipeline_deleted",
            f"Pipeline supprimé: {pipeline_id}",
            metadata={"pipeline_id": pipeline_id}
        )
        
        logger.end_operation("delete_pipeline", success=True)
        return {"message": "Pipeline deleted successfully"}
        
    except Exception as e:
        logger.end_operation("delete_pipeline", success=False)
        raise


@app.post("/api/v1/pipelines/{pipeline_id}/run")
@handle_errors("run_pipeline", reraise=True)
async def run_pipeline(
    pipeline_id: str,
    db: Session = get_db_session(),
):
    """
    Exécuter un pipeline
    """
    logger.start_operation("run_pipeline", metadata={"pipeline_id": pipeline_id})
    
    try:
        pipeline_service = PipelineService(db)
        pipeline = pipeline_service.get_pipeline(pipeline_id)
        
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        # Validation du statut
        if pipeline.status != PipelineStatus.READY:
            raise HTTPException(
                status_code=400, 
                detail=f"Pipeline not ready for execution. Current status: {pipeline.status}"
            )
        
        # Mettre à jour le statut en cours
        pipeline_service.update_pipeline_status(pipeline_id, PipelineStatus.RUNNING)
        
        # Simuler l'exécution (à remplacer avec la vraie logique)
        await asyncio.sleep(2)  # Simulation
        
        # Mettre à jour le statut terminé
        pipeline_service.update_pipeline_status(pipeline_id, PipelineStatus.COMPLETED)
        
        logger.business(
            LogLevel.HIGH,
            "pipeline_executed",
            f"Pipeline exécuté: {pipeline_id} - {pipeline.topic}",
            metadata={
                "pipeline_id": pipeline_id,
                "topic": pipeline.topic,
                "execution_time": 2.0
            }
        )
        
        logger.end_operation("run_pipeline", success=True)
        return {
            "pipeline_id": pipeline_id,
            "status": "completed",
            "execution_time": 2.0
        }
        
    except Exception as e:
        logger.end_operation("run_pipeline", success=False)
        raise


@app.get("/api/v1/topics")
@handle_errors("list_topics", reraise=True)
async def list_topics(
    db: Session = get_db_session(),
    limit: int = 20
):
    """
    Lister les sujets disponibles pour l'analyse
    """
    logger.start_operation("list_topics")
    
    try:
        pipeline_service = PipelineService(db)
        topics = pipeline_service.get_available_topics(limit)
        
        logger.end_operation("list_topics", success=True)
        return {"topics": topics}
        
    except Exception as e:
        logger.end_operation("list_topics", success=False)
        raise


@app.get("/api/v1/topics/{topic_id}")
@handle_errors("get_topic", reraise=True)
async def get_topic(
    topic_id: str,
    db: Session = get_db_session()
):
    """
    Récupérer les détails d'un sujet
    """
    logger.start_operation("get_topic", metadata={"topic_id": topic_id})
    
    try:
        pipeline_service = PipelineService(db)
        topic = pipeline_service.get_topic_details(topic_id)
        
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        
        logger.end_operation("get_topic", success=True)
        return topic
        
    except Exception as e:
        logger.end_operation("get_topic", success=False)
        raise


@app.post("/api/v1/topics/{topic_id}/validate")
@handle_errors("validate_topic", reraise=True)
async def validate_topic(
    topic_id: str,
    db: Session = get_db_session()
):
    """
    Valider un sujet pour l'analyse
    """
    logger.start_operation("validate_topic", metadata={"topic_id": topic_id})
    
    try:
        pipeline_service = PipelineService(db)
        validation = pipeline_service.validate_topic(topic_id)
        
        logger.business(
            LogLevel.MEDIUM,
            "topic_validated",
            f"Sujet validé: {topic_id}",
            metadata=validation
        )
        
        logger.end_operation("validate_topic", success=True)
        return validation
        
    except Exception as e:
        logger.end_operation("validate_topic", success=False)
        raise


@app.get("/api/v1/metrics")
@handle_errors("get_metrics", reraise=False)
async def get_metrics():
    """
    Métriques du service core
    """
    try:
        pipeline_service = PipelineService(get_db())
        metrics = pipeline_service.get_metrics()
        
        return {
            "service": "asmblr-core",
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("get_metrics", f"Erreur récupération métriques: {str(e)}")
        return {
            "service": "asmblr-core",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    logger.system(
        LogLevel.LOW,
        "service_start",
        f"Démarrage du service core sur {settings.api_host}:{settings.api_port}"
    )
    
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level="info"
    )
