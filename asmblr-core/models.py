"""
Modèles Pydantic pour le service core d'Asmblr
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class PipelineStatus(str, Enum):
    """Statuts possibles pour un pipeline"""
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineCreate(BaseModel):
    """Modèle pour la création d'un pipeline"""
    topic: str = Field(..., min_length=3, max_length=200, description="Sujet du pipeline")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Configuration du pipeline")
    mode: str = Field(default="standard", description="Mode d'exécution")


class PipelineResponse(BaseModel):
    """Modèle de réponse pour un pipeline"""
    id: str
    topic: str
    status: PipelineStatus
    config: Optional[Dict[str, Any]]
    results: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    execution_history: List[Dict[str, Any]] = Field(default_factory=list)


class PipelineUpdate(BaseModel):
    """Modèle pour la mise à jour d'un pipeline"""
    topic: Optional[str] = Field(None, min_length=3, max_length=200)
    status: Optional[PipelineStatus] = None
    config: Optional[Dict[str, Any]] = None


class PipelineExecutionRequest(BaseModel):
    """Modèle pour l'exécution d'un pipeline"""
    config_overrides: Optional[Dict[str, Any]] = Field(default=None, description="Configuration temporaire")


class Topic(BaseModel):
    """Modèle pour un sujet d'analyse"""
    id: str
    name: str
    description: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    validation_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class TopicCreate(BaseModel):
    """Modèle pour la création d'un sujet"""
    name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)


class TopicValidation(BaseModel):
    """Résultat de validation d'un sujet"""
    topic_id: str
    is_valid: bool
    score: float
    issues: List[str]
    suggestions: List[str]
    market_signals: Dict[str, Any]


class PipelineMetrics(BaseModel):
    """Métriques d'un pipeline"""
    pipeline_id: str
    total_executions: int
    successful_executions: int
    average_duration: float
    success_rate: float
    last_execution: Optional[datetime]


class ServiceMetrics(BaseModel):
    """Métriques du service core"""
    service_name: str
    total_pipelines: int
    active_pipelines: int
    total_executions: int
    successful_executions: int
    uptime_seconds: float
    memory_usage_mb: float
    cpu_usage_percent: float
    timestamp: datetime


class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: str
    timestamp: datetime
    dependencies: Dict[str, str]
