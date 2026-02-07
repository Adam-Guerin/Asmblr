"""
Base de données partagée pour les micro-services Asmblr
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean, JSON
from datetime import datetime
from typing import Optional

from app.core.config import get_settings


# Créer le moteur de base de données
engine = create_engine(get_settings().database_url)

# Session locale
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base déclarative pour tous les modèles
Base = declarative_base()


def get_db():
    """
    Dependency injection pour la session de base de données
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Pipeline(Base):
    """Modèle Pipeline pour la persistance"""
    __tablename__ = "pipelines"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    topic = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, index=True)
    config = Column(JSON, nullable=True)
    results = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Pipeline(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Pipeline(id={self.id}, topic={self.topic}, status={self.status})>"


class Topic(Base):
    """Modèle Topic pour les sujets d'analyse"""
    __tablename__ = "topics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    keywords = Column(JSON, nullable=True)
    validation_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Topic(id={self.id}, name={self.name})>"


class PipelineExecution(Base):
    """Modèle pour l'exécution des pipelines"""
    __tablename__ = "pipeline_executions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    pipeline_id = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, index=True)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    metrics = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<PipelineExecution(id={self.id}, pipeline_id={self.pipeline_id}, status={self.status})>"


class ServiceMetrics(Base):
    """Modèle pour les métriques des services"""
    __tablename__ = "service_metrics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    service_name = Column(String, nullable=False, index=True)
    metric_name = Column(String, nullable=False, index=True)
    metric_value = Column(Integer, nullable=False)
    metric_unit = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<ServiceMetrics(service={self.service_name}, metric={self.metric_name}, value={self.metric_value})>"


# Créer les tables
def init_db():
    """Initialise la base de données"""
    Base.metadata.create_all(bind=engine)
