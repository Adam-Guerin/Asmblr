"""Contextual help system for Asmblr UI with enhanced error handling."""

from __future__ import annotations
import streamlit as st
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from app.core.error_formatter import format_runtime_error, ErrorSeverity
from app.core.logging_system import get_logger


class HelpCategory(Enum):
    """Help content categories."""
    GETTING_STARTED = "getting_started"
    PIPELINE = "pipeline"
    CONFIGURATION = "configuration"
    MONITORING = "monitoring"
    EXPORTS = "exports"
    TROUBLESHOOTING = "troubleshooting"


@dataclass
class HelpContent:
    """Help content structure with enhanced type hints."""
    title: str
    content: str
    category: HelpCategory
    related_topics: List[str]
    tips: List[str]
    video_url: Optional[str] = None
    external_links: List[str] = None
    last_updated: Optional[str] = None
    difficulty_level: str = "beginner"  # beginner, intermediate, advanced
    estimated_read_time: int = 5  # minutes
    
    def __post_init__(self) -> None:
        if self.external_links is None:
            self.external_links = []


class HelpSystem:
    """Manages contextual help content and display with enhanced error handling."""
    
    def __init__(self) -> None:
        self.logger = get_logger()
        self.help_contents: Dict[str, HelpContent] = {}
        self.current_context: Optional[str] = None
        self.search_index: Dict[str, List[str]] = {}
        self._initialize_help_contents()
        self._build_search_index()
    
    def _initialize_help_contents(self) -> None:
        """Initialize all help content with error handling."""
        try:
            self.help_contents = {
                "welcome": HelpContent(
                    title="🚀 Bienvenue dans Asmblr",
                    category=HelpCategory.GETTING_STARTED,
                    content="Asmblr est un générateur de MVP (Minimum Viable Product) alimenté par l'IA qui vous aide à créer rapidement des produits viables basés sur des idées innovantes.",
                    related_topics=["first_project", "configuration"],
                    tips=["Commencez par une idée simple", "Utilisez le mode lightweight", "Consultez les exemples"],
                    difficulty_level="beginner",
                    estimated_read_time=3
                ),
                
                "configuration": HelpContent(
                    title="⚙️ Configuration du système",
                    category=HelpCategory.CONFIGURATION,
                    content="La configuration d'Asmblr se fait principalement via les variables d'environnement. Configurez les modèles IA, serveurs et performance.",
                    related_topics=["ollama_setup", "performance_tuning"],
                    tips=["Utilisez .env.light pour le mode lightweight", "Vérifiez les compatibilités de modèles"],
                    difficulty_level="intermediate",
                    estimated_read_time=7
                ),
                
                "troubleshooting": HelpContent(
                    title="🔧 Dépannage commun",
                    category=HelpCategory.TROUBLESHOOTING,
                    content="Problèmes courants et solutions: Ollama ne répond pas, mémoire insuffisante, timeouts.",
                    related_topics=["ollama_setup", "configuration"],
                    tips=["Consultez les logs pour des erreurs spécifiques", "Le mode lightweight résout la plupart des problèmes"],
                    difficulty_level="intermediate",
                    estimated_read_time=8
                )
            }
            
        except Exception as e:
            self.logger.error("Failed to initialize help contents", e)
            self.help_contents = {}
    
    def _build_search_index(self) -> None:
        """Build search index for help content."""
        try:
            for key, content in self.help_contents.items():
                search_terms = [
                    content.title.lower(),
                    content.content.lower()
                ]
                search_terms.extend([topic.lower() for topic in content.related_topics])
                search_terms.extend([tip.lower() for tip in content.tips])
                self.search_index[key] = search_terms
                
        except Exception as e:
            self.logger.error("Failed to build search index", e)
            self.search_index = {}
    
    def get_help_content(self, topic: str) -> Optional[HelpContent]:
        """Get help content for a specific topic."""
        try:
            return self.help_contents.get(topic)
        except Exception as e:
            self.logger.error(f"Failed to get help content for {topic}", e)
            return None
    
    def search_help(self, query: str) -> List[HelpContent]:
        """Search help content."""
        try:
            if not query:
                return list(self.help_contents.values())
            
            query_lower = query.lower()
            results = []
            
            for key, content in self.help_contents.items():
                if key in self.search_index:
                    search_terms = self.search_index[key]
                    if any(query_lower in term for term in search_terms):
                        results.append(content)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to search help for {query}", e)
            return []
    
    def render_help_page(self) -> None:
        """Render the main help page."""
        try:
            st.title("📚 Centre d'Aide Asmblr")
            
            search_query = st.text_input(
                "🔍 Rechercher dans l'aide",
                placeholder="Entrez votre recherche...",
                key="help_search"
            )
            
            if search_query:
                results = self.search_help(search_query)
                if results:
                    st.subheader(f"📋 Résultats pour '{search_query}'")
                    for content in results:
                        self._render_help_content(content)
                else:
                    st.info("Aucun résultat trouvé pour votre recherche.")
            else:
                self._render_categorized_help()
                
        except Exception as e:
            self.logger.error("Failed to render help page", e)
            st.error("Erreur lors de l'affichage de l'aide")
    
    def _render_categorized_help(self) -> None:
        """Render help content by categories."""
        try:
            categories = {
                HelpCategory.GETTING_STARTED: "🚀 Premiers Pas",
                HelpCategory.CONFIGURATION: "⚙️ Configuration",
                HelpCategory.TROUBLESHOOTING: "🔧 Dépannage"
            }
            
            for category, title in categories.items():
                category_content = [
                    content for content in self.help_contents.values()
                    if content.category == category
                ]
                
                if category_content:
                    with st.expander(title):
                        for content in category_content:
                            self._render_help_summary(content)
                            
        except Exception as e:
            self.logger.error("Failed to render categorized help", e)
            st.error("Erreur lors de l'affichage des catégories")
    
    def _render_help_summary(self, content: HelpContent) -> None:
        """Render a summary of help content."""
        try:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**{content.title}**")
                st.caption(f"⏱️ {content.estimated_read_time} min • 📊 {content.difficulty_level}")
            
            with col2:
                if st.button("Voir", key=f"view_{content.title}"):
                    st.session_state[f"show_help_{content.title}"] = True
                    
        except Exception as e:
            self.logger.error("Failed to render help summary", e)
    
    def _render_help_content(self, content: HelpContent) -> None:
        """Render detailed help content."""
        try:
            st.markdown(f"### {content.title}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"⏱️ {content.estimated_read_time} min")
            with col2:
                st.caption(f"📊 {content.difficulty_level}")
            with col3:
                st.caption(f"📁 {content.category.value}")
            
            st.markdown(content.content)
            
            if content.tips:
                st.markdown("#### 💡 Conseils")
                for tip in content.tips:
                    st.markdown(f"- {tip}")
            
            st.markdown("---")
            
        except Exception as e:
            self.logger.error(f"Failed to render help content for {content.title}", e)
            st.error("Erreur lors de l'affichage du contenu")
    
    def render_contextual_help(self, context: str) -> None:
        """Render contextual help based on current page/feature."""
        try:
            self.current_context = context
            
            help_content = self.get_help_content(context)
            
            if help_content:
                with st.expander(f"❓ Aide : {help_content.title}", expanded=False):
                    self._render_help_content(help_content)
            else:
                with st.expander("❓ Aide générale", expanded=False):
                    st.markdown("""
                    **Besoin d'aide ?**
                    
                    - Consultez le centre d'aide complet
                    - Utilisez la barre de recherche
                    - Contactez le support si nécessaire
                    """)
                    
        except Exception as e:
            self.logger.error(f"Failed to render contextual help for {context}", e)


# Global help system instance
_help_system: Optional[HelpSystem] = None


def get_help_system() -> HelpSystem:
    """Get the global help system instance."""
    global _help_system
    if _help_system is None:
        _help_system = HelpSystem()
    return _help_system


def render_help_page() -> None:
    """Render the main help page."""
    get_help_system().render_help_page()


def render_contextual_help(context: str) -> None:
    """Render contextual help."""
    get_help_system().render_contextual_help(context)
