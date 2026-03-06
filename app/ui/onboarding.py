"""
User-friendly onboarding system for Asmblr with enhanced error handling.
Guides new users through setup and first MVP generation.
"""

from __future__ import annotations
import streamlit as st
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Callable
from enum import Enum

from app.core.demo_mode import get_demo_manager
from app.core.error_formatter import format_runtime_error, ErrorSeverity
from app.core.logging_system import get_logger


class OnboardingStatus(Enum):
    """Onboarding step status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class OnboardingStep:
    """Onboarding step configuration with enhanced type hints."""
    step_id: str
    title: str
    description: str
    component: str  # setup, demo, explore, launch
    estimated_time: str
    required: bool = True
    completed: bool = False
    status: OnboardingStatus = OnboardingStatus.NOT_STARTED
    error_message: Optional[str] = None
    progress: float = 0.0  # 0.0 to 1.0


class OnboardingManager:
    """Manages user onboarding experience with enhanced error handling."""
    
    def __init__(self) -> None:
        self.logger = get_logger()
        self.demo_manager = get_demo_manager()
        self.steps: List[OnboardingStep] = []
        self.current_step_index: int = 0
        self.onboarding_complete: bool = False
        self._initialize_steps()
    
    def _initialize_steps(self) -> None:
        """Initialize onboarding steps with error handling."""
        try:
            self.steps = [
                OnboardingStep(
                    step_id="welcome",
                    title="🎉 Bienvenue dans Asmblr !",
                    description="Découvrons ensemble comment générer votre premier MVP alimenté par l'IA",
                    component="setup",
                    estimated_time="2 minutes"
                ),
                OnboardingStep(
                    step_id="environment_check",
                    title="🔧 Configuration de l'environnement",
                    description="Vérifiez votre environnement de développement et les modèles IA",
                    component="setup",
                    estimated_time="3 minutes"
                ),
                OnboardingStep(
                    step_id="demo_selection",
                    title="🎯 Sélection de la démo",
                    description="Choisissez une démo pour explorer les capacités d'Asmblr",
                    component="demo",
                    estimated_time="5 minutes"
                ),
                OnboardingStep(
                    step_id="first_mvp",
                    title="🚀 Votre premier MVP",
                    description="Générez votre premier MVP avec l'aide de notre système",
                    component="launch",
                    estimated_time="10 minutes"
                ),
                OnboardingStep(
                    step_id="explore_features",
                    title="🔍 Explorer les fonctionnalités",
                    description="Découvrez les fonctionnalités avancées d'Asmblr",
                    component="explore",
                    estimated_time="5 minutes"
                )
            ]
            
        except Exception as e:
            self.logger.error("Failed to initialize onboarding steps", e)
            self.steps = []
    
    def get_current_step(self) -> Optional[OnboardingStep]:
        """Get the current onboarding step."""
        try:
            if 0 <= self.current_step_index < len(self.steps):
                return self.steps[self.current_step_index]
            return None
        except Exception as e:
            self.logger.error("Failed to get current step", e)
            return None
    
    def get_step_progress(self) -> float:
        """Calculate overall onboarding progress."""
        try:
            if not self.steps:
                return 0.0
            
            completed_steps = sum(1 for step in self.steps if step.status == OnboardingStatus.COMPLETED)
            return completed_steps / len(self.steps)
        except Exception as e:
            self.logger.error("Failed to calculate step progress", e)
            return 0.0
    
    def mark_step_completed(self, step_id: str) -> bool:
        """Mark a step as completed."""
        try:
            for step in self.steps:
                if step.step_id == step_id:
                    step.status = OnboardingStatus.COMPLETED
                    step.completed = True
                    step.progress = 1.0
                    self.logger.info(f"Onboarding step {step_id} completed")
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to mark step {step_id} as completed", e)
            return False
    
    def next_step(self) -> bool:
        """Move to the next step."""
        try:
            if self.current_step_index < len(self.steps) - 1:
                self.current_step_index += 1
                current_step = self.get_current_step()
                if current_step:
                    current_step.status = OnboardingStatus.IN_PROGRESS
                return True
            else:
                self.onboarding_complete = True
                return False
        except Exception as e:
            self.logger.error("Failed to move to next step", e)
            return False
    
    def render_onboarding(self) -> None:
        """Render the complete onboarding experience."""
        try:
            if self.onboarding_complete:
                self._render_completion()
                return
            
            current_step = self.get_current_step()
            if not current_step:
                st.error("Aucune étape d'onboarding disponible")
                return
            
            # Progress indicator
            self._render_progress_indicator()
            
            # Current step content
            st.markdown(f"## {current_step.title}")
            st.markdown(current_step.description)
            
            # Render step component
            if current_step.component == "setup":
                self._render_setup_step(current_step)
            elif current_step.component == "demo":
                self._render_demo_step(current_step)
            elif current_step.component == "launch":
                self._render_launch_step(current_step)
            elif current_step.component == "explore":
                self._render_explore_step(current_step)
            else:
                st.error(f"Composant d'onboarding inconnu: {current_step.component}")
            
        except Exception as e:
            self.logger.error("Failed to render onboarding", e)
            st.error("Erreur lors de l'affichage de l'onboarding")
    
    def _render_progress_indicator(self) -> None:
        """Render the onboarding progress indicator."""
        try:
            progress = self.get_step_progress()
            current_step = self.get_current_step()
            
            st.markdown("### 📈 Progression de l'onboarding")
            st.progress(progress)
            
            # Current step info
            if current_step:
                st.caption(f"Étape actuelle : {current_step.title} ({current_step.estimated_time})")
                
        except Exception as e:
            self.logger.error("Failed to render progress indicator", e)
    
    def _render_setup_step(self, step: OnboardingStep) -> None:
        """Render a setup step."""
        try:
            if step.step_id == "welcome":
                self._render_welcome_step()
            elif step.step_id == "environment_check":
                self._render_environment_check()
            else:
                st.info(f"Étape de configuration : {step.title}")
                
        except Exception as e:
            self.logger.error(f"Failed to render setup step {step.step_id}", e)
    
    def _render_welcome_step(self) -> None:
        """Render the welcome step."""
        try:
            st.markdown("""
            ### 🎯 Qu'est-ce qu'Asmblr ?
            
            Asmblr est une plateforme révolutionnaire qui utilise l'intelligence artificielle 
            pour vous aider à créer des produits viables minimum (MVP) en quelques minutes seulement.
            
            ### 🚀 Ce que vous allez accomplir :
            - Analyser des tendances de marché
            - Générer des idées innovantes
            - Créer des MVP fonctionnels
            - Obtenir des feedbacks utilisateurs
            """)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🎉 Commencer l'onboarding", key="start_onboarding", type="primary"):
                    self.next_step()
                    st.rerun()
            
            with col2:
                if st.button("⏭️ Passer l'onboarding", key="skip_onboarding"):
                    self.onboarding_complete = True
                    st.rerun()
                    
        except Exception as e:
            self.logger.error("Failed to render welcome step", e)
            st.error("Erreur lors de l'affichage de la page de bienvenue")
    
    def _render_environment_check(self) -> None:
        """Render the environment check step."""
        try:
            st.markdown("### 🔍 Vérification de l'environnement")
            
            # Check Ollama
            with st.spinner("Vérification d'Ollama..."):
                ollama_status = self._check_ollama()
            
            # Display results
            if ollama_status["available"]:
                st.success("✅ Ollama est disponible et fonctionnel")
            else:
                st.error("❌ Ollama n'est pas disponible")
                st.info("Veuillez installer Ollama : https://ollama.ai/download")
            
            # Continue button
            if ollama_status["available"]:
                if st.button("🚀 Continuer", key="env_check_continue", type="primary"):
                    self.mark_step_completed("environment_check")
                    self.next_step()
                    st.rerun()
            else:
                st.warning("Veuillez résoudre les problèmes ci-dessus avant de continuer")
                
        except Exception as e:
            self.logger.error("Failed to render environment check", e)
            st.error("Erreur lors de la vérification de l'environnement")
    
    def _check_ollama(self) -> Dict[str, Any]:
        """Check if Ollama is available and working."""
        try:
            import requests
            
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    return {
                        "available": True,
                        "models": models,
                        "count": len(models)
                    }
            except Exception:
                pass
            
            return {"available": False, "models": [], "count": 0}
            
        except ImportError:
            return {"available": False, "error": "requests module not available"}
        except Exception as e:
            self.logger.error("Failed to check Ollama", e)
            return {"available": False, "error": str(e)}
    
    def _render_demo_step(self, step: OnboardingStep) -> None:
        """Render a demo step."""
        try:
            st.markdown("### 🎯 Sélectionnez une démo")
            
            demo_options = {
                "ecommerce": {"title": "🛒 E-commerce", "description": "Créez une boutique en ligne avec IA"},
                "saas": {"title": "☁️ SaaS", "description": "Application software-as-a-service"},
                "mobile": {"title": "📱 Application Mobile", "description": "Application mobile avec IA"},
                "content": {"title": "📝 Plateforme de Contenu", "description": "Génération de contenu avec IA"}
            }
            
            cols = st.columns(2)
            for i, (key, demo) in enumerate(demo_options.items()):
                with cols[i % 2]:
                    if st.button(f"{demo['title']}\n{demo['description']}", key=f"demo_{key}"):
                        st.session_state.selected_demo = key
                        self.mark_step_completed("demo_selection")
                        self.next_step()
                        st.rerun()
                            
        except Exception as e:
            self.logger.error("Failed to render demo step", e)
            st.error("Erreur lors de l'affichage de la sélection de démo")
    
    def _render_launch_step(self, step: OnboardingStep) -> None:
        """Render the launch step."""
        try:
            st.markdown("### 🚀 Générez votre premier MVP")
            
            selected_demo = st.session_state.get("selected_demo", "ecommerce")
            st.info(f"Démonstration sélectionnée : {selected_demo}")
            
            if st.button("🚀 Lancer la génération", key="launch_mvp", type="primary"):
                with st.spinner("Génération de votre MVP en cours..."):
                    time.sleep(2)
                    st.success("✅ MVP généré avec succès !")
                    
                    self.mark_step_completed("first_mvp")
                    self.next_step()
                    st.rerun()
                    
        except Exception as e:
            self.logger.error("Failed to render launch step", e)
            st.error("Erreur lors du lancement du MVP")
    
    def _render_explore_step(self, step: OnboardingStep) -> None:
        """Render the explore step."""
        try:
            st.markdown("### 🔍 Explorez les fonctionnalités")
            
            features = [
                "📊 Dashboard et métriques",
                "📤 Export multi-format",
                "🎨 Personnalisation des thèmes",
                "🔧 Configuration avancée",
                "📚 Système d'aide intégré"
            ]
            
            for feature in features:
                st.markdown(f"- {feature}")
            
            if st.button("🎉 Terminer l'onboarding", key="complete_onboarding", type="primary"):
                self.onboarding_complete = True
                st.rerun()
                
        except Exception as e:
            self.logger.error("Failed to render explore step", e)
            st.error("Erreur lors de l'exploration des fonctionnalités")
    
    def _render_completion(self) -> None:
        """Render onboarding completion."""
        try:
            st.markdown("# 🎉 Onboarding terminé !")
            
            st.markdown("""
            ### 🎯 Félicitations !
            
            Vous avez terminé l'onboarding d'Asmblr. Vous êtes maintenant prêt à :
            
            - Générer des MVP avec l'IA
            - Analyser les tendances du marché
            - Créer des produits innovants
            - Explorer des fonctionnalités avancées
            """)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 Voir le dashboard", key="go_dashboard"):
                    st.switch_page("dashboard")
            
            with col2:
                if st.button("🚀 Créer un MVP", key="create_mvp"):
                    st.switch_page("mvp_generator")
                    
        except Exception as e:
            self.logger.error("Failed to render completion", e)
            st.error("Erreur lors de l'affichage de la complétion")


# Global onboarding manager instance
_onboarding_manager: Optional[OnboardingManager] = None


def get_onboarding_manager() -> OnboardingManager:
    """Get the global onboarding manager instance."""
    global _onboarding_manager
    if _onboarding_manager is None:
        _onboarding_manager = OnboardingManager()
    return _onboarding_manager


def render_onboarding() -> None:
    """Render the onboarding experience."""
    get_onboarding_manager().render_onboarding()


def is_onboarding_complete() -> bool:
    """Check if onboarding is complete."""
    return get_onboarding_manager().onboarding_complete


def reset_onboarding() -> None:
    """Reset the onboarding progress."""
    global _onboarding_manager
    _onboarding_manager = OnboardingManager()
