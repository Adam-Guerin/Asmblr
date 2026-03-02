"""
Asmblr Agents Service - AI Agents Microservice
Gestion des agents CrewAI et communication avec les LLM
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.agents.crew_service import CrewService
from app.agents.llm_service import LLMService
from app.agents.models import (
    CrewRequest, CrewResponse, LLMRequest, LLMResponse
)
from app.agents.error_handler import handle_agents_errors, AgentException
from app.agents.smart_logger import get_agents_logger, LogLevel
from app.agents.config import get_agents_settings


app = FastAPI(
    title="Asmblr Agents API",
    description="AI Agents Microservice for Asmblr",
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
logger = get_agents_logger()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "asmblr-agents",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/api/v1/agents/status")
@handle_agents_errors("get_agents_status", reraise=False)
async def get_agents_status():
    """
    Récupérer le statut des agents
    """
    logger.start_operation("get_agents_status")
    
    try:
        crew_service = CrewService()
        status = crew_service.get_all_agents_status()
        
        logger.end_operation("get_agents_status", success=True)
        return {
            "agents": status,
            "total_agents": len(status),
            "active_agents": len([s for s in status if s["status"] == "active"]),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.end_operation("get_agents_status", success=False)
        raise


@app.get("/api/v1/agents/models")
@handle_agents_errors("get_available_models", reraise=False)
async def get_available_models():
    """
    Récupérer les modèles LLM disponibles
    """
    logger.start_operation("get_available_models")
    
    try:
        llm_service = LLMService()
        models = llm_service.get_available_models()
        
        logger.end_operation("get_available_models", success=True)
        return {
            "models": models,
            "total_models": len(models),
            "default_model": llm_service.get_default_model(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.end_operation("get_available_models", success=False)
        raise


@app.post("/api/v1/agents/crew", response_model=CrewResponse)
@handle_agents_errors("execute_crew", reraise=True)
async def execute_crew(crew_request: CrewRequest):
    """
    Exécuter un CrewAI
    """
    logger.start_operation("execute_crew", metadata={"crew_type": crew_request.crew_type})
    
    try:
        crew_service = CrewService()
        
        # Validation de la requête
        if not crew_request.topic or len(crew_request.topic.strip()) < 3:
            raise AgentException(
                "Le sujet doit contenir au moins 3 caractères",
                operation="execute_crew"
            )
        
        # Exécuter le crew
        result = await crew_service.execute_crew(crew_request)
        
        logger.business(
            LogLevel.HIGH,
            "crew_executed",
            f"CrewAI exécuté: {crew_request.crew_type} - {crew_request.topic}",
            metadata={
                "crew_type": crew_request.crew_type,
                "topic": crew_request.topic,
                "execution_id": result.execution_id,
                "duration": result.duration_seconds
            }
        )
        
        logger.end_operation("execute_crew", success=True)
        return result
        
    except Exception as e:
        logger.end_operation("execute_crew", success=False)
        raise


@app.post("/api/v1/agents/llm", response_model=LLMResponse)
@handle_agents_errors("llm_call", reraise=True)
async def llm_call(llm_request: LLMRequest):
    """
    Appel direct à un LLM
    """
    logger.start_operation("llm_call", metadata={"model": llm_request.model})
    
    try:
        llm_service = LLMService()
        
        # Validation de la requête
        if not llm_request.prompt:
            raise AgentException(
                "Le prompt ne peut pas être vide",
                operation="llm_call"
            )
        
        # Appeler le LLM
        result = await llm_service.generate_text(llm_request)
        
        logger.info(
            "llm_call_completed",
            f"Appel LLM complété: {llm_request.model}",
            metadata={
                "model": llm_request.model,
                "prompt_length": len(llm_request.prompt),
                "response_length": len(result.text),
                "duration": result.duration_seconds
            }
        )
        
        logger.end_operation("llm_call", success=True)
        return result
        
    except Exception as e:
        logger.end_operation("llm_call", success=False)
        raise


@app.post("/api/v1/agents/idea-generate")
@handle_agents_errors("generate_ideas", reraise=True)
async def generate_ideas(
    topic: str,
    max_ideas: int = 10,
    model: str | None = None
):
    """
    Générer des idées pour un sujet
    """
    logger.start_operation("generate_ideas", metadata={"topic": topic, "max_ideas": max_ideas})
    
    try:
        crew_service = CrewService()
        
        # Validation
        if not topic or len(topic.strip()) < 3:
            raise AgentException(
                "Le sujet doit contenir au moins 3 caractères",
                operation="generate_ideas"
            )
        
        if max_ideas < 1 or max_ideas > 50:
            raise AgentException(
                "Le nombre d'idées doit être entre 1 et 50",
                operation="generate_ideas"
            )
        
        # Créer la requête de crew
        crew_request = CrewRequest(
            crew_type="idea_generation",
            topic=topic.strip(),
            config={
                "max_ideas": max_ideas,
                "model": model or "llama3.1:8b",
                "temperature": 0.7,
                "max_tokens": 2000
            }
        )
        
        # Exécuter le crew
        result = await crew_service.execute_crew(crew_request)
        
        logger.business(
            LogLevel.HIGH,
            "ideas_generated",
            f"Idées générées pour: {topic}",
            metadata={
                "topic": topic,
                "max_ideas": max_ideas,
                "ideas_count": len(result.results.get("ideas", [])),
                "execution_id": result.execution_id
            }
        )
        
        logger.end_operation("generate_ideas", success=True)
        return result
        
    except Exception as e:
        logger.end_operation("generate_ideas", success=False)
        raise


@app.post("/api/v1/agents/market-analyze")
@handle_agents_errors("analyze_market", reraise=True)
async def analyze_market(
    topic: str,
    max_sources: int = 8,
    model: str | None = None
):
    """
    Analyser le marché pour un sujet
    """
    logger.start_operation("analyze_market", metadata={"topic": topic, "max_sources": max_sources})
    
    try:
        crew_service = CrewService()
        
        # Validation
        if not topic or len(topic.strip()) < 3:
            raise AgentException(
                "Le sujet doit contenir au moins 3 caractères",
                operation="analyze_market"
            )
        
        if max_sources < 1 or max_sources > 20:
            raise AgentException(
                "Le nombre de sources doit être entre 1 et 20",
                operation="analyze_market"
            )
        
        # Créer la requête de crew
        crew_request = CrewRequest(
            crew_type="market_analysis",
            topic=topic.strip(),
            config={
                "max_sources": max_sources,
                "model": model or "llama3.1:8b",
                "temperature": 0.5,
                "max_tokens": 3000
            }
        )
        
        # Exécuter le crew
        result = await crew_service.execute_crew(crew_request)
        
        logger.business(
            LogLevel.HIGH,
            "market_analyzed",
            f"Analyse marché complétée pour: {topic}",
            metadata={
                "topic": topic,
                "max_sources": max_sources,
                "sources_analyzed": len(result.results.get("sources", [])),
                "execution_id": result.execution_id
            }
        )
        
        logger.end_operation("analyze_market", success=True)
        return result
        
    except Exception as e:
        logger.end_operation("analyze_market", success=False)
        raise


@app.post("/api/v1/agents/competitor-analyze")
@handle_agents_errors("analyze_competitors", reraise=True)
async def analyze_competitors(
    topic: str,
    max_competitors: int = 5,
    model: str | None = None
):
    """
    Analyser les concurrents pour un sujet
    """
    logger.start_operation("analyze_competitors", metadata={"topic": topic, "max_competitors": max_competitors})
    
    try:
        crew_service = CrewService()
        
        # Validation
        if not topic or len(topic.strip()) < 3:
            raise AgentException(
                "Le sujet doit contenir au moins 3 caractères",
                operation="analyze_competitors"
            )
        
        if max_competitors < 1 or max_competitors > 10:
            raise AgentException(
                "Le nombre de concurrents doit être entre 1 et 10",
                operation="analyze_competitors"
            )
        
        # Créer la requête de crew
        crew_request = CrewRequest(
            crew_type="competitor_analysis",
            topic=topic.strip(),
            config={
                "max_competitors": max_competitors,
                "model": model or "llama3.1:8b",
                "temperature": 0.6,
                "max_tokens": 2500
            }
        )
        
        # Exécuter le crew
        result = await crew_service.execute_crew(crew_request)
        
        logger.business(
            LogLevel.HIGH,
            "competitors_analyzed",
            f"Analyse concurrents complétée pour: {topic}",
            metadata={
                "topic": topic,
                "max_competitors": max_competitors,
                "competitors_analyzed": len(result.results.get("competitors", [])),
                "execution_id": result.execution_id
            }
        )
        
        logger.end_operation("analyze_competitors", success=True)
        return result
        
    except Exception as e:
        logger.end_operation("analyze_competitors", success=False)
        raise


@app.post("/api/v1/agents/content-generate")
@handle_agents_errors("generate_content", reraise=True)
async def generate_content(
    topic: str,
    content_type: str = "landing_page",
    tone: str = "professional",
    model: str | None = None
):
    """
    Générer du contenu pour un sujet
    """
    logger.start_operation("generate_content", metadata={"topic": topic, "content_type": content_type})
    
    try:
        crew_service = CrewService()
        
        # Validation
        if not topic or len(topic.strip()) < 3:
            raise AgentException(
                "Le sujet doit contenir au moins 3 caractères",
                operation="generate_content"
            )
        
        if content_type not in ["landing_page", "social_post", "email_campaign", "blog_post"]:
            raise AgentException(
                "Type de contenu non valide",
                operation="generate_content"
            )
        
        # Créer la requête de crew
        crew_request = CrewRequest(
            crew_type="content_generation",
            topic=topic.strip(),
            config={
                "content_type": content_type,
                "tone": tone,
                "model": model or "llama3.1:8b",
                "temperature": 0.8,
                "max_tokens": 2000
            }
        )
        
        # Exécuter le crew
        result = await crew_service.execute_crew(crew_request)
        
        logger.business(
            LogLevel.HIGH,
            "content_generated",
            f"Contenu généré pour: {topic}",
            metadata={
                "topic": topic,
                "content_type": content_type,
                "tone": tone,
                "execution_id": result.execution_id
            }
        )
        
        logger.end_operation("generate_content", success=True)
        return result
        
    except Exception as e:
        logger.end_operation("generate_content", success=False)
        raise


@app.get("/api/v1/agents/metrics")
@handle_agents_errors("get_agents_metrics", reraise=False)
async def get_agents_metrics():
    """
    Métriques du service agents
    """
    try:
        crew_service = CrewService()
        llm_service = LLMService()
        
        # Récupérer les métriques
        crew_metrics = crew_service.get_metrics()
        llm_metrics = llm_service.get_metrics()
        
        return {
            "service": "asmblr-agents",
            "crew_metrics": crew_metrics,
            "llm_metrics": llm_metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("get_agents_metrics", f"Erreur métriques agents: {str(e)}")
        return {
            "service": "asmblr-agents",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


if __name__ == "__main__":
    import uvicorn
    
    settings = get_agents_settings()
    logger.system(
        LogLevel.LOW,
        "agents_service_start",
        f"Démarrage du service agents sur {settings.api_host}:{settings.api_port}"
    )
    
    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level="info"
    )
