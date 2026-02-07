"""
Integration module for enhanced crew system with facilitator agents, feedback loops, shared knowledge base, peer review, and asset management.
"""

from typing import Any, Dict
from pathlib import Path

from app.core.config import Settings
from app.core.llm import LLMClient
from app.agents.enhanced_crew import run_enhanced_crewai_pipeline
from app.agents.feedback_enhanced_crew import run_feedback_enhanced_crewai_pipeline
from app.agents.knowledge_enhanced_crew import run_knowledge_enhanced_crewai_pipeline
from app.agents.peer_review_enhanced_crew import run_peer_review_enhanced_crewai_pipeline
from app.agents.asset_enhanced_crew import run_asset_enhanced_crewai_pipeline
from app.agents.crew import run_crewai_pipeline


def should_use_enhanced_crew(settings: Settings) -> bool:
    """Determine if enhanced crew should be used based on configuration."""
    # Check for enhanced collaboration setting
    return getattr(settings, 'enable_facilitator_agents', False)


def should_use_feedback_loops(settings: Settings) -> bool:
    """Determine if feedback loops should be used based on configuration."""
    # Check for feedback loops setting
    return getattr(settings, 'enable_feedback_loops', False)


def should_use_shared_knowledge(settings: Settings) -> bool:
    """Determine if shared knowledge base should be used based on configuration."""
    # Check for shared knowledge setting
    return getattr(settings, 'enable_shared_knowledge', False)


def should_use_peer_review(settings: Settings) -> bool:
    """Determine if peer review system should be used based on configuration."""
    # Check for peer review setting
    return getattr(settings, 'enable_peer_review', False)


def should_use_shared_assets(settings: Settings) -> bool:
    """Determine if shared asset management should be used based on configuration."""
    # Check for shared assets setting
    return getattr(settings, 'enable_shared_assets', False)


def run_pipeline(
    topic: str,
    settings: Settings,
    llm_client: LLMClient,
    run_id: str,
    n_ideas: int,
    fast_mode: bool,
    seed_pages: list[dict[str, Any]] | None = None,
    seed_competitor_pages: list[dict[str, Any]] | None = None,
    seed_inputs: Any = None,
    validated_pains: list[str] | None = None,
) -> dict[str, Any]:
    """
    Run MVP generation pipeline with appropriate crew system.
    
    Automatically chooses between standard, enhanced, feedback-enabled, knowledge-enhanced, peer-review-enhanced, and asset-enhanced crew based on configuration.
    """
    
    use_feedback_loops = should_use_feedback_loops(settings)
    use_enhanced_crew = should_use_enhanced_crew(settings)
    use_shared_knowledge = should_use_shared_knowledge(settings)
    use_peer_review = should_use_peer_review(settings)
    use_shared_assets = should_use_shared_assets(settings)
    
    if use_shared_assets:
        print("🎨 Using ASSET-ENHANCED crew with collaborative resource management")
        return run_asset_enhanced_crewai_pipeline(
            topic=topic,
            settings=settings,
            llm_client=llm_client,
            run_id=run_id,
            n_ideas=n_ideas,
            fast_mode=fast_mode,
            seed_pages=seed_pages,
            seed_competitor_pages=seed_competitor_pages,
            seed_inputs=seed_inputs,
            validated_pains=validated_pains
        )
    elif use_peer_review:
        print("🔍 Using PEER REVIEW-ENHANCED crew with collaborative quality assurance")
        return run_peer_review_enhanced_crewai_pipeline(
            topic=topic,
            settings=settings,
            llm_client=llm_client,
            run_id=run_id,
            n_ideas=n_ideas,
            fast_mode=fast_mode,
            seed_pages=seed_pages,
            seed_competitor_pages=seed_competitor_pages,
            seed_inputs=seed_inputs,
            validated_pains=validated_pains
        )
    elif use_shared_knowledge:
        print("🧠 Using KNOWLEDGE-ENHANCED crew with shared intelligence base")
        return run_knowledge_enhanced_crewai_pipeline(
            topic=topic,
            settings=settings,
            llm_client=llm_client,
            run_id=run_id,
            n_ideas=n_ideas,
            fast_mode=fast_mode,
            seed_pages=seed_pages,
            seed_competitor_pages=seed_competitor_pages,
            seed_inputs=seed_inputs,
            validated_pains=validated_pains
        )
    elif use_feedback_loops:
        print("🔄 Using FEEDBACK-ENHANCED crew with continuous improvement loops")
        return run_feedback_enhanced_crewai_pipeline(
            topic=topic,
            settings=settings,
            llm_client=llm_client,
            run_id=run_id,
            n_ideas=n_ideas,
            fast_mode=fast_mode,
            seed_pages=seed_pages,
            seed_competitor_pages=seed_competitor_pages,
            seed_inputs=seed_inputs,
            validated_pains=validated_pains
        )
    elif use_enhanced_crew:
        print("🤝 Using ENHANCED crew with facilitator agents for improved synergy")
        return run_enhanced_crewai_pipeline(
            topic=topic,
            settings=settings,
            llm_client=llm_client,
            run_id=run_id,
            n_ideas=n_ideas,
            fast_mode=fast_mode,
            seed_pages=seed_pages,
            seed_competitor_pages=seed_competitor_pages,
            seed_inputs=seed_inputs,
            validated_pains=validated_pains
        )
    else:
        print("🔄 Using standard crew system")
        return run_crewai_pipeline(
            topic=topic,
            settings=settings,
            llm_client=llm_client,
            run_id=run_id,
            n_ideas=n_ideas,
            fast_mode=fast_mode,
            seed_pages=seed_pages,
            seed_competitor_pages=seed_competitor_pages,
            seed_inputs=seed_inputs,
            validated_pains=validated_pains
        )
