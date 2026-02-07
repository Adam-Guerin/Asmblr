"""
Service métier pour la gestion des pipelines
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.core.database import Pipeline, PipelineStatus, get_db
from app.core.models import (
    PipelineCreate, PipelineResponse, PipelineUpdate, 
    PipelineExecutionRequest, Topic, TopicValidation, PipelineMetrics
)
from app.core.error_handler import handle_errors, ValidationException
from app.core.smart_logger import get_smart_logger, LogCategory, LogLevel
from app.core.config import get_settings


class PipelineService:
    """Service métier pour la gestion des pipelines"""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = get_smart_logger()
    
    @handle_errors("list_pipelines", reraise=True)
    def list_pipelines(self, 
                      skip: int = 0, 
                      limit: int = 50, 
                      filters: Optional[Dict[str, Any]] = None) -> List[PipelineResponse]:
        """
        Lister les pipelines avec pagination et filtres
        """
        try:
            query = self.db.query(Pipeline)
            
            # Appliquer les filtres
            if filters:
                if "status" in filters:
                    query = query.filter(Pipeline.status == filters["status"])
                if "topic" in filters:
                    query = query.filter(Pipeline.topic.contains(filters["topic"]))
            
            # Pagination
            pipelines = query.offset(skip).limit(limit).all()
            
            # Convertir en modèles de réponse
            return [
                PipelineResponse(
                    id=pipeline.id,
                    topic=pipeline.topic,
                    status=PipelineStatus(pipeline.status),
                    config=pipeline.config,
                    results=pipeline.results,
                    created_at=pipeline.created_at,
                    updated_at=pipeline.updated_at,
                    execution_history=pipeline.execution_history or []
                )
                for pipeline in pipelines
            ]
            
        except Exception as e:
            self.logger.error("list_pipelines", f"Erreur listing pipelines: {str(e)}")
            raise
    
    @handle_errors("get_pipeline", reraise=True)
    def get_pipeline(self, pipeline_id: str) -> Optional[PipelineResponse]:
        """
        Récupérer un pipeline spécifique
        """
        try:
            pipeline = self.db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
            
            if not pipeline:
                return None
            
            return PipelineResponse(
                id=pipeline.id,
                topic=pipeline.topic,
                status=PipelineStatus(pipeline.status),
                config=pipeline.config,
                results=pipeline.results,
                created_at=pipeline.created_at,
                updated_at=pipeline.updated_at,
                execution_history=pipeline.execution_history or []
            )
            
        except Exception as e:
            self.logger.error("get_pipeline", f"Erreur getting pipeline {pipeline_id}: {str(e)}")
            return None
    
    @handle_errors("create_pipeline", reraise=True)
    def create_pipeline(self, pipeline_data: PipelineCreate) -> PipelineResponse:
        """
        Créer un nouveau pipeline
        """
        try:
            # Validation des données
            if not pipeline_data.topic or len(pipeline_data.topic.strip()) < 3:
                raise ValidationException(
                    "Le sujet doit contenir au moins 3 caractères",
                    operation="create_pipeline"
                )
            
            # Créer le pipeline
            pipeline = Pipeline(
                topic=pipeline_data.topic.strip(),
                status=PipelineStatus.DRAFT,
                config=pipeline_data.config or {},
                results={},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(pipeline)
            self.db.commit()
            
            # Récupérer avec l'ID généré
            created_pipeline = self.get_pipeline(pipeline.id)
            
            self.logger.business(
                LogLevel.MEDIUM,
                "pipeline_created",
                f"Pipeline créé: {created_pipeline.id}",
                metadata={
                    "pipeline_id": created_pipeline.id,
                    "topic": created_pipeline.topic,
                    "status": created_pipeline.status
                }
            )
            
            return created_pipeline
            
        except Exception as e:
            self.logger.error("create_pipeline", f"Erreur création pipeline: {str(e)}")
            raise
    
    @handle_errors("update_pipeline", reraise=True)
    def update_pipeline(self, 
                      pipeline_id: str, 
                      update_data: PipelineUpdate) -> Optional[PipelineResponse]:
        """
        Mettre à jour un pipeline existant
        """
        try:
            pipeline = self.db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
            
            if not pipeline:
                return None
            
            # Mettre à jour les champs
            if update_data.topic is not None:
                pipeline.topic = update_data.topic.strip()
            if update_data.status is not None:
                pipeline.status = PipelineStatus(update_data.status)
            if update_data.config is not None:
                pipeline.config.update(update_data.config)
            
            pipeline.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            self.logger.business(
                LogLevel.MEDIUM,
                "pipeline_updated",
                f"Pipeline mis à jour: {pipeline.id}",
                metadata={
                    "pipeline_id": pipeline.id,
                    "topic": pipeline.topic,
                    "status": pipeline.status
                }
            )
            
            return self.get_pipeline(pipeline.id)
            
        except Exception as e:
            self.logger.error("update_pipeline", f"Erreur mise à jour pipeline {pipeline_id}: {str(e)}")
            return None
    
    @handle_errors("delete_pipeline", reraise=True)
    def delete_pipeline(self, pipeline_id: str) -> bool:
        """
        Supprimer un pipeline
        """
        try:
            pipeline = self.db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
            
            if not pipeline:
                return False
            
            self.db.delete(pipeline)
            self.db.commit()
            
            self.logger.business(
                LogLevel.MEDIUM,
                "pipeline_deleted",
                f"Pipeline supprimé: {pipeline_id}",
                metadata={"pipeline_id": pipeline_id}
            )
            
            return True
            
        except Exception as e:
            self.logger.error("delete_pipeline", f"Erreur suppression pipeline {pipeline_id}: {str(e)}")
            return False
    
    @handle_errors("update_pipeline_status", reraise=False)
    def update_pipeline_status(self, pipeline_id: str, status: PipelineStatus) -> bool:
        """
        Mettre à jour le statut d'un pipeline
        """
        try:
            pipeline = self.db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
            
            if not pipeline:
                return False
            
            pipeline.status = status
            pipeline.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            self.logger.info(
                "pipeline_status_updated",
                f"Statut mis à jour: {pipeline_id} -> {status}",
                metadata={"pipeline_id": pipeline_id, "status": status}
            )
            
            return True
            
        except Exception as e:
            self.logger.error("update_pipeline_status", f"Erreur mise à jour statut {pipeline_id}: {str(e)}")
            return False
    
    @handle_errors("run_pipeline", reraise=True)
    async def run_pipeline(self, 
                        pipeline_id: str, 
                        execution_request: Optional[PipelineExecutionRequest] = None) -> Dict[str, Any]:
        """
        Exécuter un pipeline
        """
        try:
            pipeline = self.db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
            
            if not pipeline:
                raise ValidationException("Pipeline not found", "run_pipeline")
            
            # Vérifier le statut
            if pipeline.status != PipelineStatus.READY:
                raise ValidationException(
                    f"Pipeline not ready for execution. Current status: {pipeline.status}",
                    "run_pipeline"
                )
            
            # Mettre à jour le statut en cours
            self.update_pipeline_status(pipeline_id, PipelineStatus.RUNNING)
            
            # Créer l'enregistrement d'exécution
            from app.core.database import PipelineExecution
            
            execution = PipelineExecution(
                pipeline_id=pipeline_id,
                status=PipelineStatus.RUNNING,
                started_at=datetime.utcnow(),
                duration_seconds=None,
                error_message=None,
                metrics={},
                created_at=datetime.utcnow()
            )
            
            self.db.add(execution)
            self.db.commit()
            
            # Simuler l'exécution (à remplacer par la vraie logique)
            import asyncio
            
            config = execution_request.config_overrides if execution_request else pipeline.config
            duration = config.get("expected_duration", 60)
            
            # Simuler le traitement
            await asyncio.sleep(duration)
            
            # Mettre à jour l'exécution
            execution.status = PipelineStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            execution.duration_seconds = duration
            execution.metrics = {
                "steps_completed": 5,
                "items_processed": 100,
                "success_rate": 0.95
            }
            
            self.db.commit()
            
            # Mettre à jour le statut du pipeline
            self.update_pipeline_status(pipeline_id, PipelineStatus.COMPLETED)
            
            # Mettre à jour les résultats du pipeline
            pipeline.results = {
                "execution_id": execution.id,
                "status": "completed",
                "duration": duration,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if pipeline.execution_history:
                pipeline.execution_history.append(pipeline.results)
            
            pipeline.updated_at = datetime.utcnow()
            self.db.commit()
            
            self.logger.business(
                LogLevel.HIGH,
                "pipeline_executed",
                f"Pipeline exécuté: {pipeline_id}",
                metadata={
                    "pipeline_id": pipeline_id,
                    "topic": pipeline.topic,
                    "execution_time": duration,
                    "status": execution.status
                }
            )
            
            return {
                "pipeline_id": pipeline_id,
                "status": execution.status,
                "execution_id": execution.id,
                "duration_seconds": duration,
                "metrics": execution.metrics
            }
            
        except Exception as e:
            # Mettre à jour le statut en erreur
            self.update_pipeline_status(pipeline_id, PipelineStatus.FAILED)
            
            # Créer un enregistrement d'erreur
            from app.core.database import PipelineExecution
            
            error_execution = PipelineExecution(
                pipeline_id=pipeline_id,
                status=PipelineStatus.FAILED,
                started_at=datetime.utcnow(),
                duration_seconds=None,
                error_message=str(e),
                metrics={},
                created_at=datetime.utcnow()
            )
            
            self.db.add(error_execution)
            self.db.commit()
            
            self.logger.error(
                "pipeline_execution_failed",
                f"Échec exécution pipeline {pipeline_id}: {str(e)}"
            )
            
            raise
    
    def get_available_topics(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Récupérer les sujets disponibles pour l'analyse
        """
        try:
            # Simuler des sujets disponibles
            topics = [
                {
                    "id": "ai-compliance",
                    "name": "AI Compliance for SMBs",
                    "description": "Automated compliance checking for small businesses",
                    "keywords": ["ai", "compliance", "smb", "regulation", "risk", "audit"]
                },
                {
                    "id": "customer-support-automation",
                    "name": "Customer Support Automation",
                    "description": "AI-powered customer support systems",
                    "keywords": ["customer", "support", "automation", "chatbot", "helpdesk"]
                },
                {
                    "id": "b2b-fundraising",
                    "name": "B2B Fundraising Platform",
                    "description": "AI-driven fundraising and investor outreach",
                    "keywords": ["fundraising", "investors", "pitch", "startup", "vc"]
                },
                {
                    "id": "supply-chain-optimization",
                    "name": "Supply Chain Optimization",
                    "description": "AI-powered supply chain analysis and optimization",
                    "keywords": ["supply chain", "logistics", "inventory", "optimization"]
                }
            ]
            
            return topics[:limit]
            
        except Exception as e:
            self.logger.error("get_available_topics", f"Erreur récupération sujets: {str(e)}")
            return []
    
    def get_topic_details(self, topic_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupérer les détails d'un sujet
        """
        try:
            # Simuler les détails du sujet
            topics = {
                "ai-compliance": {
                    "id": "ai-compliance",
                    "name": "AI Compliance for SMBs",
                    "description": "Automated compliance checking for small businesses",
                    "keywords": ["ai", "compliance", "smb", "regulation", "risk", "audit"],
                    "market_size": "70B",
                    "growth_rate": "15%"
                },
                "customer-support-automation": {
                    "id": "customer-support-automation",
                    "name": "Customer Support Automation",
                    "description": "AI-powered customer support systems",
                    "keywords": ["customer", "support", "automation", "chatbot", "helpdesk"],
                    "market_size": "100B",
                    "growth_rate": "25%"
                }
            }
            
            return topics.get(topic_id)
            
        except Exception as e:
            self.logger.error("get_topic_details", f"Erreur détails sujet {topic_id}: {str(e)}")
            return None
    
    def validate_topic(self, topic_id: str) -> TopicValidation:
        """
        Valider un sujet pour l'analyse
        """
        try:
            topic_details = self.get_topic_details(topic_id)
            
            if not topic_details:
                return TopicValidation(
                    topic_id=topic_id,
                    is_valid=False,
                    score=0.0,
                    issues=["Topic not found"],
                    suggestions=["Vérifiez l'ID du topic"],
                    market_signals={}
                )
            
            # Simulation de validation
            score = 75.0
            issues = []
            suggestions = []
            market_signals = {
                "search_volume": "high",
                "competition_level": "medium",
                "data_availability": "good"
            }
            
            # Validation basée sur les mots-clés
            if topic_details:
                keywords = topic_details.get("keywords", [])
                if len(keywords) >= 3:
                    score += 10
                if any(keyword in ["ai", "automation", "optimization"] for keyword in keywords):
                    score += 5
                
                if len(topic_details.get("description", "")) >= 50:
                    score += 10
                
                if score > 90:
                    issues.append("Sujet trop général")
                    suggestions.append("Soyez plus spécifique")
            
            return TopicValidation(
                topic_id=topic_id,
                is_valid=score >= 50,
                score=score,
                issues=issues,
                suggestions=suggestions,
                market_signals=market_signals
            )
            
        except Exception as e:
            self.logger.error("validate_topic", f"Erreur validation sujet {topic_id}: {str(e)}")
            return TopicValidation(
                topic_id=topic_id,
                is_valid=False,
                score=0.0,
                issues=["Erreur de validation"],
                suggestions=["Réessayez plus tard"],
                market_signals={}
            )
    
    def get_metrics(self) -> PipelineMetrics:
        """
        Récupérer les métriques du service
        """
        try:
            # Compter les pipelines
            total_pipelines = self.db.query(Pipeline).count()
            active_pipelines = self.db.query(Pipeline).filter(
                Pipeline.status.in_([PipelineStatus.READY, PipelineStatus.RUNNING])
            ).count()
            
            # Compter les exécutions
            from app.core.database import PipelineExecution
            total_executions = self.db.query(PipelineExecution).count()
            successful_executions = self.db.query(PipelineExecution).filter(
                PipelineExecution.status == PipelineStatus.COMPLETED
            ).count()
            
            # Calculer les métriques
            success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
            
            # Durée moyenne d'exécution
            avg_duration = self.db.query(
                self.db.query(PipelineExecution)
                .filter(PipelineExecution.duration_seconds.isnot(None))
                .with_entities(Pipeline)
            ).with_entities(Pipeline)
            ).all()
            
            avg_duration = sum(d.duration_seconds for d in avg_duration) / len(avg_duration) if avg_duration else 0
            
            return PipelineMetrics(
                service_name="asmblr-core",
                total_pipelines=total_pipelines,
                active_pipelines=active_pipelines,
                total_executions=total_executions,
                successful_executions=successful_executions,
                average_duration=avg_duration,
                success_rate=success_rate,
                uptime_seconds=3600.0,  # À implémenter
                memory_usage_mb=0.0,  # À implémenter
                cpu_usage_percent=0.0  # À implémenter
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error("get_metrics", f"Erreur métriques: {str(e)}")
            return PipelineMetrics(
                service_name="asmblr-core",
                total_pipelines=0,
                active_pipelines=0,
                total_executions=0,
                successful_executions=0,
                average_duration=0.0,
                success_rate=0.0,
                uptime_seconds=0.0,
                memory_usage_mb=0.0,
                cpu_usage_percent=0.0,
                timestamp=datetime.utcnow()
            )
