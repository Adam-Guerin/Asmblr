"""
Knowledge Base Tools for agents to access and contribute to shared intelligence.
"""

from typing import Any, Dict, List, Optional
from loguru import logger

from app.agents.shared_knowledge import (
    SharedKnowledgeBase,
    KnowledgeEntry,
    KnowledgeQuery,
    KnowledgeType,
    KnowledgeDomain,
    KnowledgeStatus
)


class KnowledgeBaseTools:
    """Tools for agents to interact with shared knowledge base."""
    
    def __init__(self, knowledge_base: SharedKnowledgeBase, agent_name: str):
        self.knowledge_base = knowledge_base
        self.agent_name = agent_name
    
    def search_knowledge(self, 
                       keywords: List[str] = None,
                       types: List[str] = None,
                       domains: List[str] = None,
                       tags: List[str] = None,
                       min_success_rate: float = 0.0,
                       min_validation_score: float = 0.0,
                       limit: int = 20,
                       sort_by: str = "relevance") -> List[Dict[str, Any]]:
        """Search knowledge base for relevant entries."""
        try:
            # Convert string parameters to enums
            type_enums = [KnowledgeType(t) for t in (types or [])]
            domain_enums = [KnowledgeDomain(d) for d in (domains or [])]
            
            query = KnowledgeQuery(
                keywords=keywords or [],
                types=type_enums,
                domains=domain_enums,
                tags=tags or [],
                min_success_rate=min_success_rate,
                min_validation_score=min_validation_score,
                limit=limit,
                sort_by=sort_by
            )
            
            results = self.knowledge_base.search(query)
            
            # Convert to serializable format
            return [
                {
                    "id": entry.id,
                    "type": entry.type.value,
                    "domain": entry.domain.value,
                    "title": entry.title,
                    "description": entry.description,
                    "content": entry.content,
                    "source_agent": entry.source_agent,
                    "contributors": entry.contributors,
                    "tags": list(entry.tags),
                    "usage_count": entry.usage_count,
                    "success_rate": entry.success_rate,
                    "validation_score": entry.validation_score,
                    "status": entry.status.value,
                    "created_at": entry.created_at,
                    "updated_at": entry.updated_at
                }
                for entry in results
            ]
            
        except Exception as e:
            logger.error(f"Failed to search knowledge base: {e}")
            return []
    
    def get_knowledge_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific knowledge entry."""
        try:
            entry = self.knowledge_base.get_entry(entry_id)
            if not entry:
                return None
            
            # Record usage
            entry.record_usage(success=True)
            self.knowledge_base._save_entry(entry)
            
            return {
                "id": entry.id,
                "type": entry.type.value,
                "domain": entry.domain.value,
                "title": entry.title,
                "description": entry.description,
                "content": entry.content,
                "source_agent": entry.source_agent,
                "contributors": entry.contributors,
                "tags": list(entry.tags),
                "usage_count": entry.usage_count,
                "success_rate": entry.success_rate,
                "validation_score": entry.validation_score,
                "status": entry.status.value,
                "created_at": entry.created_at,
                "updated_at": entry.updated_at,
                "related_entries": entry.related_entries,
                "prerequisites": entry.prerequisites,
                "context": entry.context,
                "metadata": entry.metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to get knowledge entry {entry_id}: {e}")
            return None
    
    def add_knowledge(self,
                     knowledge_type: str,
                     domain: str,
                     title: str,
                     description: str,
                     content: Dict[str, Any],
                     tags: List[str] = None,
                     related_entries: List[str] = None,
                     prerequisites: List[str] = None,
                     context: Dict[str, Any] = None,
                     metadata: Dict[str, Any] = None) -> Optional[str]:
        """Add a new knowledge entry to the knowledge base."""
        try:
            # Generate unique ID
            from datetime import datetime, timezone
            import uuid
            entry_id = f"kb_{self.agent_name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            # Convert string parameters to enums
            type_enum = KnowledgeType(knowledge_type)
            domain_enum = KnowledgeDomain(domain)
            
            # Create knowledge entry
            entry = KnowledgeEntry(
                id=entry_id,
                type=type_enum,
                domain=domain_enum,
                title=title,
                description=description,
                content=content,
                source_agent=self.agent_name,
                tags=set(tags or []),
                related_entries=related_entries or [],
                prerequisites=prerequisites or [],
                context=context or {},
                metadata=metadata or {}
            )
            
            # Add to knowledge base
            if self.knowledge_base.add_entry(entry):
                logger.info(f"Added knowledge entry: {entry_id} - {title}")
                return entry_id
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to add knowledge entry: {e}")
            return None
    
    def update_knowledge(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing knowledge entry."""
        try:
            # Add current agent as contributor
            entry = self.knowledge_base.get_entry(entry_id)
            if entry:
                entry.add_contributor(self.agent_name)
            
            return self.knowledge_base.update_entry(entry_id, updates)
            
        except Exception as e:
            logger.error(f"Failed to update knowledge entry {entry_id}: {e}")
            return False
    
    def validate_knowledge(self, entry_id: str, validation_score: float, 
                        validation_notes: str = None) -> bool:
        """Validate a knowledge entry with a score."""
        try:
            updates = {
                "validation_score": validation_score
            }
            
            if validation_notes:
                updates["metadata"] = {
                    "validation_notes": validation_notes,
                    "validated_by": self.agent_name
                }
            
            return self.update_knowledge(entry_id, updates)
            
        except Exception as e:
            logger.error(f"Failed to validate knowledge entry {entry_id}: {e}")
            return False
    
    def get_related_knowledge(self, entry_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get knowledge entries related to a specific entry."""
        try:
            entries = self.knowledge_base.get_related_entries(entry_id, limit)
            
            return [
                {
                    "id": entry.id,
                    "type": entry.type.value,
                    "domain": entry.domain.value,
                    "title": entry.title,
                    "description": entry.description,
                    "content": entry.content,
                    "source_agent": entry.source_agent,
                    "contributors": entry.contributors,
                    "tags": list(entry.tags),
                    "usage_count": entry.usage_count,
                    "success_rate": entry.success_rate,
                    "validation_score": entry.validation_score,
                    "status": entry.status.value,
                    "created_at": entry.created_at,
                    "updated_at": entry.updated_at
                }
                for entry in entries
            ]
            
        except Exception as e:
            logger.error(f"Failed to get related knowledge for {entry_id}: {e}")
            return []
    
    def get_top_knowledge(self, domain: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top knowledge entries by validation score."""
        try:
            domain_enum = KnowledgeDomain(domain) if domain else None
            entries = self.knowledge_base.get_top_entries(domain_enum, limit)
            
            return [
                {
                    "id": entry.id,
                    "type": entry.type.value,
                    "domain": entry.domain.value,
                    "title": entry.title,
                    "description": entry.description,
                    "content": entry.content,
                    "source_agent": entry.source_agent,
                    "contributors": entry.contributors,
                    "tags": list(entry.tags),
                    "usage_count": entry.usage_count,
                    "success_rate": entry.success_rate,
                    "validation_score": entry.validation_score,
                    "status": entry.status.value,
                    "created_at": entry.created_at,
                    "updated_at": entry.updated_at
                }
                for entry in entries
            ]
            
        except Exception as e:
            logger.error(f"Failed to get top knowledge: {e}")
            return []
    
    def get_my_contributions(self) -> List[Dict[str, Any]]:
        """Get all knowledge entries contributed by this agent."""
        try:
            entries = self.knowledge_base.get_agent_contributions(self.agent_name)
            
            return [
                {
                    "id": entry.id,
                    "type": entry.type.value,
                    "domain": entry.domain.value,
                    "title": entry.title,
                    "description": entry.description,
                    "content": entry.content,
                    "contributors": entry.contributors,
                    "tags": list(entry.tags),
                    "usage_count": entry.usage_count,
                    "success_rate": entry.success_rate,
                    "validation_score": entry.validation_score,
                    "status": entry.status.value,
                    "created_at": entry.created_at,
                    "updated_at": entry.updated_at
                }
                for entry in entries
            ]
            
        except Exception as e:
            logger.error(f"Failed to get contributions for {self.agent_name}: {e}")
            return []
    
    def get_knowledge_statistics(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        try:
            return self.knowledge_base.get_statistics()
        except Exception as e:
            logger.error(f"Failed to get knowledge statistics: {e}")
            return {}


def create_knowledge_prompts() -> Dict[str, str]:
    """Create specialized prompts for knowledge-aware agents."""
    
    return {
        "knowledge_aware_agent": """
You are working in a KNOWLEDGE-ENHANCED ENVIRONMENT with access to shared intelligence.

KNOWLEDGE BASE RESPONSIBILITIES:
1. Before starting your task: Search for relevant knowledge using search_knowledge()
2. During execution: Use knowledge to improve your approach and outputs
3. After completion: Add your learnings to the knowledge base
4. Validate and improve existing knowledge when relevant

KNOWLEDGE UTILIZATION:
- Use search_knowledge() to find methodologies, patterns, and best practices
- Use get_knowledge_entry() to access specific knowledge items
- Use get_related_knowledge() to find connected knowledge
- Use get_top_knowledge() to access validated expertise
- Record usage of knowledge entries to track effectiveness

KNOWLEDGE CONTRIBUTION:
- Use add_knowledge() to share your learnings and insights
- Document successful strategies and methodologies
- Share patterns and best practices discovered
- Add solutions to common problems
- Contribute to collective intelligence

KNOWLEDGE IMPROVEMENT:
- Use validate_knowledge() to rate and improve existing knowledge
- Use update_knowledge() to enhance and expand knowledge entries
- Add your experience as contributor to relevant entries
- Help maintain knowledge quality and relevance

COLLABORATIVE INTELLIGENCE:
- Build upon knowledge contributed by other agents
- Share your unique expertise and perspectives
- Help validate and improve collective knowledge
- Contribute to knowledge base growth and quality

Your goal is to LEVERAGE AND CONTRIBUTE TO COLLECTIVE INTELLIGENCE.
""",
        
        "knowledge_curator": """
You are the KNOWLEDGE CURATOR responsible for maintaining and improving the shared knowledge base.

CURATION RESPONSIBILITIES:
1. Monitor knowledge quality and relevance
2. Identify gaps and opportunities for new knowledge
3. Validate and improve existing knowledge entries
4. Organize and categorize knowledge effectively
5. Promote best practices and validated methodologies

QUALITY ASSURANCE:
- Review new knowledge submissions for accuracy and relevance
- Validate knowledge through testing and peer review
- Identify and update outdated or deprecated knowledge
- Ensure knowledge is properly categorized and tagged
- Maintain high standards for knowledge validation

KNOWLEDGE ORGANIZATION:
- Ensure proper categorization by type and domain
- Maintain consistent tagging and metadata
- Identify relationships between knowledge entries
- Create knowledge hierarchies and prerequisites
- Optimize search and discovery mechanisms

INTELLIGENCE SYNTHESIS:
- Identify patterns and trends across knowledge entries
- Synthesize related knowledge into comprehensive frameworks
- Create knowledge summaries and best practice guides
- Identify knowledge gaps and recommend areas for contribution
- Facilitate knowledge transfer between domains

Your role is to ensure the knowledge base remains a HIGH-QUALITY, RELEVANT, and ACCESSIBLE resource for all agents.
""",
        
        "knowledge_harvester": """
You are a KNOWLEDGE HARVESTER focused on extracting and organizing intelligence from agent experiences.

HARVESTING RESPONSIBILITIES:
1. Extract valuable insights from agent outputs and interactions
2. Identify successful patterns and methodologies
3. Document lessons learned and best practices
4. Convert experiences into structured knowledge entries
5. Share harvested knowledge with the community

EXTRACTION TECHNIQUES:
- Analyze successful task completions for repeatable patterns
- Identify effective strategies and approaches
- Extract problem-solving methodologies
- Document optimization techniques and improvements
- Capture collaboration insights and synergies

KNOWLEDGE STRUCTURING:
- Organize extracted insights into actionable knowledge
- Create templates and frameworks for common scenarios
- Document step-by-step methodologies
- Identify prerequisites and related knowledge
- Tag and categorize for easy discovery

CONTINUOUS LEARNING:
- Monitor agent performance improvements
- Identify emerging best practices
- Track evolution of successful strategies
- Update knowledge based on new experiences
- Share learning curves and improvement patterns

Your goal is to TRANSFORM AGENT EXPERIENCES into REUSABLE, VALUABLE KNOWLEDGE.
"""
    }
