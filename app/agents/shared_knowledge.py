"""
Shared Knowledge Base for collective intelligence and agent learning.
"""

from typing import Any
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
from datetime import datetime, UTC
from loguru import logger


class KnowledgeType(Enum):
    """Types of knowledge entries."""
    METHODOLOGY = "methodology"
    PATTERN = "pattern"
    BEST_PRACTICE = "best_practice"
    LESSON_LEARNED = "lesson_learned"
    TECHNIQUE = "technique"
    FRAMEWORK = "framework"
    INSIGHT = "insight"
    SOLUTION = "solution"
    TEMPLATE = "template"
    STRATEGY = "strategy"


class KnowledgeDomain(Enum):
    """Knowledge domains for categorization."""
    RESEARCH = "research"
    ANALYSIS = "analysis"
    PRODUCT = "product"
    TECHNICAL = "technical"
    GROWTH = "growth"
    BRAND = "brand"
    COLLABORATION = "collaboration"
    QUALITY = "quality"
    PERFORMANCE = "performance"


class KnowledgeStatus(Enum):
    """Status of knowledge entries."""
    ACTIVE = "active"
    VALIDATED = "validated"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"
    ARCHIVED = "archived"


@dataclass
class KnowledgeEntry:
    """Individual knowledge entry in the shared knowledge base."""
    id: str
    type: KnowledgeType
    domain: KnowledgeDomain
    title: str
    description: str
    content: dict[str, Any]
    source_agent: str
    contributors: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    status: KnowledgeStatus = KnowledgeStatus.ACTIVE
    usage_count: int = 0
    success_rate: float = 0.0
    validation_score: float = 0.0
    related_entries: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def add_contributor(self, agent_name: str) -> None:
        """Add a contributor to this knowledge entry."""
        if agent_name not in self.contributors:
            self.contributors.append(agent_name)
            self.updated_at = datetime.now(UTC).isoformat()
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to this knowledge entry."""
        self.tags.add(tag.lower().strip())
        self.updated_at = datetime.now(UTC).isoformat()
    
    def record_usage(self, success: bool = True) -> None:
        """Record usage of this knowledge entry."""
        self.usage_count += 1
        if success:
            self.success_rate = (self.success_rate * (self.usage_count - 1) + 1.0) / self.usage_count
        else:
            self.success_rate = (self.success_rate * (self.usage_count - 1) + 0.0) / self.usage_count
        self.updated_at = datetime.now(UTC).isoformat()
    
    def update_validation_score(self, score: float) -> None:
        """Update validation score."""
        self.validation_score = score
        if score >= 0.8:
            self.status = KnowledgeStatus.VALIDATED
        elif score < 0.3:
            self.status = KnowledgeStatus.DEPRECATED
        self.updated_at = datetime.now(UTC).isoformat()


@dataclass
class KnowledgeQuery:
    """Query for searching the knowledge base."""
    keywords: list[str] = field(default_factory=list)
    types: list[KnowledgeType] = field(default_factory=list)
    domains: list[KnowledgeDomain] = field(default_factory=list)
    agents: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    min_success_rate: float = 0.0
    min_validation_score: float = 0.0
    status: KnowledgeStatus | None = None
    limit: int = 50
    sort_by: str = "relevance"  # relevance, usage, success_rate, validation_score, created_at


class SharedKnowledgeBase:
    """Centralized knowledge base for agent collective intelligence."""
    
    def __init__(self, knowledge_dir: Path):
        self.knowledge_dir = knowledge_dir
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self.entries: dict[str, KnowledgeEntry] = {}
        self.index: dict[str, set[str]] = {
            "keywords": set(),
            "tags": set(),
            "agents": set(),
            "types": set(),
            "domains": set()
        }
        self._load_knowledge_base()
    
    def add_entry(self, entry: KnowledgeEntry) -> bool:
        """Add a new knowledge entry to the knowledge base."""
        try:
            self.entries[entry.id] = entry
            self._update_index(entry)
            self._save_entry(entry)
            logger.info(f"Added knowledge entry: {entry.id} - {entry.title}")
            return True
        except Exception as e:
            logger.error(f"Failed to add knowledge entry {entry.id}: {e}")
            return False
    
    def update_entry(self, entry_id: str, updates: dict[str, Any]) -> bool:
        """Update an existing knowledge entry."""
        if entry_id not in self.entries:
            logger.error(f"Knowledge entry {entry_id} not found")
            return False
        
        try:
            entry = self.entries[entry_id]
            for key, value in updates.items():
                if hasattr(entry, key):
                    setattr(entry, key, value)
            
            entry.updated_at = datetime.now(UTC).isoformat()
            self._update_index(entry)
            self._save_entry(entry)
            logger.info(f"Updated knowledge entry: {entry_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update knowledge entry {entry_id}: {e}")
            return False
    
    def get_entry(self, entry_id: str) -> KnowledgeEntry | None:
        """Get a specific knowledge entry."""
        return self.entries.get(entry_id)
    
    def search(self, query: KnowledgeQuery) -> list[KnowledgeEntry]:
        """Search the knowledge base based on query criteria."""
        results = []
        
        for entry in self.entries.values():
            if self._matches_query(entry, query):
                results.append(entry)
        
        # Sort results
        if query.sort_by == "usage":
            results.sort(key=lambda x: x.usage_count, reverse=True)
        elif query.sort_by == "success_rate":
            results.sort(key=lambda x: x.success_rate, reverse=True)
        elif query.sort_by == "validation_score":
            results.sort(key=lambda x: x.validation_score, reverse=True)
        elif query.sort_by == "created_at":
            results.sort(key=lambda x: x.created_at, reverse=True)
        else:  # relevance (default)
            results.sort(key=lambda x: self._calculate_relevance(x, query), reverse=True)
        
        return results[:query.limit]
    
    def get_related_entries(self, entry_id: str, limit: int = 10) -> list[KnowledgeEntry]:
        """Get entries related to a specific entry."""
        if entry_id not in self.entries:
            return []
        
        entry = self.entries[entry_id]
        related_ids = set(entry.related_entries)
        
        # Find entries with similar tags or domains
        for other_id, other_entry in self.entries.items():
            if other_id == entry_id:
                continue
            
            # Check for tag overlap
            if entry.tags & other_entry.tags:
                related_ids.add(other_id)
            
            # Check for same domain
            if entry.domain == other_entry.domain:
                related_ids.add(other_id)
        
        related = [self.entries[eid] for eid in related_ids if eid in self.entries]
        related.sort(key=lambda x: x.validation_score, reverse=True)
        return related[:limit]
    
    def get_top_entries(self, domain: KnowledgeDomain | None = None, 
                      limit: int = 20) -> list[KnowledgeEntry]:
        """Get top entries by validation score."""
        entries = list(self.entries.values())
        
        if domain:
            entries = [e for e in entries if e.domain == domain]
        
        entries.sort(key=lambda x: x.validation_score, reverse=True)
        return entries[:limit]
    
    def get_agent_contributions(self, agent_name: str) -> list[KnowledgeEntry]:
        """Get all entries contributed by a specific agent."""
        return [e for e in self.entries.values() 
                if e.source_agent == agent_name or agent_name in e.contributors]
    
    def _matches_query(self, entry: KnowledgeEntry, query: KnowledgeQuery) -> bool:
        """Check if an entry matches the query criteria."""
        # Check keywords
        if query.keywords:
            entry_text = f"{entry.title} {entry.description}".lower()
            if not any(keyword.lower() in entry_text for keyword in query.keywords):
                return False
        
        # Check types
        if query.types and entry.type not in query.types:
            return False
        
        # Check domains
        if query.domains and entry.domain not in query.domains:
            return False
        
        # Check agents
        if query.agents:
            if (entry.source_agent not in query.agents and 
                not any(agent in entry.contributors for agent in query.agents)):
                return False
        
        # Check tags
        if query.tags:
            if not any(tag.lower() in entry.tags for tag in query.tags):
                return False
        
        # Check success rate
        if entry.success_rate < query.min_success_rate:
            return False
        
        # Check validation score
        if entry.validation_score < query.min_validation_score:
            return False
        
        # Check status
        if query.status and entry.status != query.status:
            return False
        
        return True
    
    def _calculate_relevance(self, entry: KnowledgeEntry, query: KnowledgeQuery) -> float:
        """Calculate relevance score for an entry."""
        score = 0.0
        
        # Keyword matching
        if query.keywords:
            entry_text = f"{entry.title} {entry.description}".lower()
            keyword_matches = sum(1 for kw in query.keywords 
                              if kw.lower() in entry_text)
            score += keyword_matches * 0.3
        
        # Type matching
        if query.types and entry.type in query.types:
            score += 0.2
        
        # Domain matching
        if query.domains and entry.domain in query.domains:
            score += 0.2
        
        # Tag matching
        if query.tags:
            tag_matches = len(entry.tags & set(t.lower() for t in query.tags))
            score += tag_matches * 0.15
        
        # Quality factors
        score += entry.validation_score * 0.1
        score += entry.success_rate * 0.05
        
        return score
    
    def _update_index(self, entry: KnowledgeEntry) -> None:
        """Update the search index with entry data."""
        # Update keywords index
        for keyword in entry.title.lower().split():
            self.index["keywords"].add(keyword)
        
        # Update tags index
        for tag in entry.tags:
            self.index["tags"].add(tag)
        
        # Update agents index
        self.index["agents"].add(entry.source_agent)
        self.index["agents"].update(entry.contributors)
        
        # Update types index
        self.index["types"].add(entry.type.value)
        
        # Update domains index
        self.index["domains"].add(entry.domain.value)
    
    def _save_entry(self, entry: KnowledgeEntry) -> None:
        """Save a knowledge entry to file."""
        try:
            entry_file = self.knowledge_dir / f"{entry.id}.json"
            
            # Convert to serializable format
            entry_data = {
                "id": entry.id,
                "type": entry.type.value,
                "domain": entry.domain.value,
                "title": entry.title,
                "description": entry.description,
                "content": entry.content,
                "source_agent": entry.source_agent,
                "contributors": entry.contributors,
                "tags": list(entry.tags),
                "created_at": entry.created_at,
                "updated_at": entry.updated_at,
                "status": entry.status.value,
                "usage_count": entry.usage_count,
                "success_rate": entry.success_rate,
                "validation_score": entry.validation_score,
                "related_entries": entry.related_entries,
                "prerequisites": entry.prerequisites,
                "context": entry.context,
                "metadata": entry.metadata
            }
            
            entry_file.write_text(json.dumps(entry_data, indent=2), encoding="utf-8")
            
        except Exception as e:
            logger.error(f"Failed to save knowledge entry {entry.id}: {e}")
    
    def _load_knowledge_base(self) -> None:
        """Load all knowledge entries from files."""
        try:
            for entry_file in self.knowledge_dir.glob("*.json"):
                try:
                    entry_data = json.loads(entry_file.read_text(encoding="utf-8"))
                    
                    # Convert back to KnowledgeEntry
                    entry = KnowledgeEntry(
                        id=entry_data["id"],
                        type=KnowledgeType(entry_data["type"]),
                        domain=KnowledgeDomain(entry_data["domain"]),
                        title=entry_data["title"],
                        description=entry_data["description"],
                        content=entry_data["content"],
                        source_agent=entry_data["source_agent"],
                        contributors=entry_data.get("contributors", []),
                        tags=set(entry_data.get("tags", [])),
                        created_at=entry_data.get("created_at"),
                        updated_at=entry_data.get("updated_at"),
                        status=KnowledgeStatus(entry_data.get("status", "active")),
                        usage_count=entry_data.get("usage_count", 0),
                        success_rate=entry_data.get("success_rate", 0.0),
                        validation_score=entry_data.get("validation_score", 0.0),
                        related_entries=entry_data.get("related_entries", []),
                        prerequisites=entry_data.get("prerequisites", []),
                        context=entry_data.get("context", {}),
                        metadata=entry_data.get("metadata", {})
                    )
                    
                    self.entries[entry.id] = entry
                    self._update_index(entry)
                    
                except Exception as e:
                    logger.error(f"Failed to load knowledge entry {entry_file}: {e}")
            
            logger.info(f"Loaded {len(self.entries)} knowledge entries")
            
        except Exception as e:
            logger.error(f"Failed to load knowledge base: {e}")
    
    def get_statistics(self) -> dict[str, Any]:
        """Get knowledge base statistics."""
        stats = {
            "total_entries": len(self.entries),
            "entries_by_type": {},
            "entries_by_domain": {},
            "entries_by_status": {},
            "total_contributors": len(self.index["agents"]),
            "total_tags": len(self.index["tags"]),
            "average_validation_score": 0.0,
            "average_success_rate": 0.0,
            "most_used_entries": [],
            "top_validated_entries": []
        }
        
        if not self.entries:
            return stats
        
        # Calculate statistics
        for entry in self.entries.values():
            # By type
            stats["entries_by_type"][entry.type.value] = stats["entries_by_type"].get(entry.type.value, 0) + 1
            
            # By domain
            stats["entries_by_domain"][entry.domain.value] = stats["entries_by_domain"].get(entry.domain.value, 0) + 1
            
            # By status
            stats["entries_by_status"][entry.status.value] = stats["entries_by_status"].get(entry.status.value, 0) + 1
        
        # Calculate averages
        stats["average_validation_score"] = sum(e.validation_score for e in self.entries.values()) / len(self.entries)
        stats["average_success_rate"] = sum(e.success_rate for e in self.entries.values()) / len(self.entries)
        
        # Most used entries
        stats["most_used_entries"] = sorted(
            [(e.id, e.title, e.usage_count) for e in self.entries.values()],
            key=lambda x: x[2], reverse=True
        )[:10]
        
        # Top validated entries
        stats["top_validated_entries"] = sorted(
            [(e.id, e.title, e.validation_score) for e in self.entries.values()],
            key=lambda x: x[2], reverse=True
        )[:10]
        
        return stats
