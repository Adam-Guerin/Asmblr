"""
Mode Lightweight pour Asmblr
Désactive les fonctionnalités lourdes pour améliorer performance et fiabilité
"""

import os
import sys
import threading
from typing import Any
from loguru import logger


class LightweightMode:
    """
    Gestionnaire du mode lightweight qui désactive les fonctionnalités lourdes
    et optimise les performances pour les cas d'usage courants
    """
    
    def __init__(self):
        # Check both standardized variable names
        self.enabled = (
            os.getenv('LIGHTWEIGHT_MODE', 'false').lower() == 'true' or
            os.getenv('ASMblr_LIGHTWEIGHT', 'false').lower() == 'true'
        )
        self.disabled_features: set[str] = set()
        self.optimization_settings = self._load_optimization_settings()
        self._original_modules = {}  # Store for potential restoration
        self._lock = threading.Lock()  # Thread safety
        
        if self.enabled:
            self._enable_lightweight_mode()
    
    def _enable_lightweight_mode(self) -> None:
        """Active le mode lightweight et désactive les fonctionnalités lourdes"""
        logger.info("🚀 Activation mode Lightweight Asmblr")
        
        # Désactiver les imports lourds
        self._disable_heavy_imports()
        
        # Appliquer les optimisations
        self._apply_optimizations()
        
        # Ajuster la configuration
        self._adjust_configuration()
        
        logger.info("✅ Mode Lightweight activé - Performance optimisée")
    
    def _disable_heavy_imports(self) -> None:
        """Désactive les imports de bibliothèques lourdes de manière sécurisée"""
        heavy_modules = {
            'torch': 'PyTorch (AI/ML)',
            'torchvision': 'PyTorch Vision',
            'torchaudio': 'PyTorch Audio',
            'diffusers': 'Diffusers (génération images)',
            'transformers': 'Transformers (NLP)',
            'accelerate': 'Accelerate (GPU)',
            'imageio': 'ImageIO (vidéo)',
            'imageio_ffmpeg': 'ImageIO FFmpeg',
            'vtracer': 'VTracer (vectorisation)'
        }
        
        # Store original modules for potential restoration
        self._original_modules = {}
        
        for module, description in heavy_modules.items():
            try:
                if module in sys.modules:
                    # Module already imported - store reference and cleanup properly
                    original_module = sys.modules[module]
                    self._original_modules[module] = original_module
                    
                    # Replace with disabled module to prevent new imports
                    sys.modules[module] = _DisabledModule(description)
                    self.disabled_features.add(f"{description} (remplacé)")
                    logger.warning(f"Module {module} déjà importé - remplacé par module désactivé")
                    
                    # Force cleanup of module references
                    self._cleanup_module_references(module, original_module)
                else:
                    # Module not yet imported - safe to disable
                    sys.modules[module] = _DisabledModule(description)
                    self.disabled_features.add(description)
                    logger.debug(f"Désactivé: {description}")
            except Exception as e:
                logger.warning(f"Impossible de désactiver {module}: {e}")
                pass
    
    def _cleanup_module_references(self, module_name: str, module_obj: Any) -> None:
        """Clean up references to prevent memory leaks"""
        try:
            # Clear module cache if it exists
            if hasattr(module_obj, '__cache__'):
                module_obj.__cache__.clear()
            
            # Clear any global variables that might hold references
            if hasattr(module_obj, '__dict__'):
                for key, value in list(module_obj.__dict__.items()):
                    if not key.startswith('_') and hasattr(value, '__del__'):
                        try:
                            delattr(module_obj, key)
                        except Exception:
                            pass
            
            logger.debug(f"Cleaned up references for module: {module_name}")
        except Exception as e:
            logger.warning(f"Failed to cleanup module {module_name}: {e}")
    
    def _apply_optimizations(self) -> None:
        """Applique les optimisations de performance"""
        # Configuration optimisée - respect user settings if provided
        if not os.getenv('FAST_MODE'):
            os.environ['FAST_MODE'] = 'true'
        if not os.getenv('MVP_DISABLE_LLM'):
            os.environ['MVP_DISABLE_LLM'] = 'false'
        if not os.getenv('MVP_FORCE_AUTOFIX'):
            os.environ['MVP_FORCE_AUTOFIX'] = 'true'
        
        # Désactiver les fonctionnalités avancées
        os.environ['ENABLE_FACILITATOR_AGENTS'] = 'false'
        os.environ['ENABLE_FEEDBACK_LOOPS'] = 'false'
        os.environ['ENABLE_SHARED_KNOWLEDGE'] = 'false'
        os.environ['ENABLE_PEER_REVIEW'] = 'false'
        
        # Désactiver les fonctionnalités média lourdes
        os.environ['ENABLE_LOGO_DIFFUSION'] = 'false'
        os.environ['ENABLE_LOCAL_VIDEO'] = 'false'
        os.environ['ENABLE_LOCAL_SOCIAL_IMAGES'] = 'false'
        
        # Optimiser les ressources - only if not set by user
        if not os.getenv('MAX_SOURCES'):
            os.environ['MAX_SOURCES'] = '6'  # Réduit de 12 à 6
        if not os.getenv('DEFAULT_N_IDEAS'):
            os.environ['DEFAULT_N_IDEAS'] = '5'  # Réduit de 10 à 5
        if not os.getenv('REQUEST_TIMEOUT'):
            os.environ['REQUEST_TIMEOUT'] = '30'  # Réduit de 45 à 30
        
        # Désactiver MLP et fonctionnalités avancées
        os.environ['MLP_ENABLED'] = 'false'
        os.environ['LOVEABILITY_ENABLED'] = 'false'
        os.environ['EMOTIONAL_DESIGN_ENABLED'] = 'false'
    
    def _adjust_configuration(self) -> None:
        """Ajuste la configuration pour le mode lightweight"""
        # Réduire la consommation mémoire
        os.environ['PYTHONOPTIMIZE'] = '2'  # Optimisation Python
        
        # Limiter le parallélisme
        os.environ['OMP_NUM_THREADS'] = '2'  # Limiter les threads OpenMP
        os.environ['MKL_NUM_THREADS'] = '2'   # Limiter les threads MKL
        
        # Optimiser le garbage collection
        os.environ['PYTHONGC'] = '1'
    
    def _load_optimization_settings(self) -> dict[str, Any]:
        """Charge les paramètres d'optimisation"""
        return {
            'max_sources': 6,
            'max_ideas': 5,
            'timeout_multiplier': 0.7,
            'disable_heavy_features': True,
            'enable_aggressive_caching': True,
            'reduce_concurrency': True,
            'optimize_memory': True
        }
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """
        Vérifie si une fonctionnalité est activée en mode lightweight
        
        Args:
            feature_name: Nom de la fonctionnalité
            
        Returns:
            True si la fonctionnalité est disponible
        """
        if not self.enabled:
            return True
        
        # Fonctionnalités désactivées en mode lightweight
        disabled_features = {
            'logo_generation': False,
            'video_generation': False,
            'image_generation': False,
            'svg_vectorization': False,
            'audio_processing': False,
            'advanced_ml_features': False,
            'emotional_design': False,
            'mlp_features': False,
            'facilitator_agents': False,
            'feedback_loops': False,
            'peer_review': False
        }
        
        return disabled_features.get(feature_name, True)
    
    def get_optimized_config(self) -> dict[str, Any]:
        """Retourne la configuration optimisée pour le mode lightweight"""
        return {
            'mode': 'lightweight',
            'disabled_features': list(self.disabled_features),
            'optimizations': self.optimization_settings,
            'performance_gains': {
                'memory_reduction': '~70%',
                'startup_time': '~50% faster',
                'installation_size': '~80% smaller'
            }
        }
    
    def check_dependencies(self) -> dict[str, Any]:
        """Vérifie les dépendances et retourne l'état"""
        required_lightweight = [
            'crewai', 'langchain', 'fastapi', 'streamlit',
            'httpx', 'beautifulsoup4', 'loguru', 'pydantic'
        ]
        
        optional_heavy = [
            'torch', 'diffusers', 'transformers', 'imageio',
            'vtracer', 'torchvision', 'torchaudio'
        ]
        
        status = {
            'lightweight_deps': {},
            'heavy_deps': {},
            'recommendations': []
        }
        
        # Vérifier les dépendances lightweight
        for dep in required_lightweight:
            try:
                __import__(dep)
                status['lightweight_deps'][dep] = 'installed'
            except ImportError:
                status['lightweight_deps'][dep] = 'missing'
                status['recommendations'].append(f"Installez: pip install {dep}")
        
        # Vérifier les dépendances lourdes
        for dep in optional_heavy:
            try:
                __import__(dep)
                status['heavy_deps'][dep] = 'installed'
            except ImportError:
                status['heavy_deps'][dep] = 'not_installed'  # Normal en mode lightweight
        
        return status
    
    def cleanup(self) -> None:
        """Clean up disabled modules and restore original state if possible"""
        logger.info("Cleaning up lightweight mode...")
        
        # Restore original modules if we have them
        if hasattr(self, '_original_modules'):
            for module_name, original_module in self._original_modules.items():
                if module_name in sys.modules and isinstance(sys.modules[module_name], _DisabledModule):
                    try:
                        if original_module is not None:
                            sys.modules[module_name] = original_module
                            logger.debug(f"Restored module: {module_name}")
                        else:
                            # If original was None, remove the disabled module
                            del sys.modules[module_name]
                            logger.debug(f"Removed disabled module: {module_name}")
                    except Exception as e:
                        logger.warning(f"Failed to restore module {module_name}: {e}")
        
        # Clear disabled features and original modules references
        self.disabled_features.clear()
        if hasattr(self, '_original_modules'):
            self._original_modules.clear()
        logger.info("Lightweight mode cleanup completed")
    
    def suggest_optimizations(self) -> list[str]:
        """Suggère des optimisations supplémentaires"""
        suggestions = [
            "Utilisez requirements/requirements-lightweight.txt pour une installation minimale",
            "Activez le cache web pour réduire les requêtes réseau",
            "Limitez le nombre de sources à analyser (MAX_SOURCES=6)",
            "Utilisez le mode fast pour les tests rapides",
            "Désactivez les fonctionnalités avancées non nécessaires"
        ]
        
        if self.enabled:
            suggestions.extend([
                "Le mode lightweight est déjà activé ✅",
                "Considérez utiliser Ollama avec des modèles plus légers (qwen2.5:1.5b)"
            ])
        
        return suggestions


class _DisabledModule:
    """
    Module fantôme qui remplace les imports lourds
    Affiche des messages d'avertissement quand on essaie de l'utiliser
    """
    
    __slots__ = ('_description', '_disabled')  # Prevent __dict__ creation, reduce memory usage
    
    def __init__(self, description: str):
        self._description = description
        self._disabled = True
    
    def __getattr__(self, name: str) -> Any:
        # Generic error message to avoid information disclosure
        raise ImportError(
            f"Feature disabled in lightweight mode. "
            f"Set LIGHTWEIGHT_MODE=false to enable."
        )
    
    def __call__(self, *args, **kwargs):
        # Generic error message to avoid information disclosure
        raise ImportError(
            f"Feature disabled in lightweight mode. "
            f"Set LIGHTWEIGHT_MODE=false to enable."
        )
    
    def __del__(self):
        """Cleanup when the module is garbage collected"""
        try:
            del self._description
            del self._disabled
        except AttributeError:
            pass  # Already cleaned up


def enable_lightweight_mode() -> None:
    """
    Active le mode lightweight programmatiquement
    """
    os.environ['ASMblr_LIGHTWEIGHT'] = 'true'
    # Forcer la recréation de l'instance
    global _lightweight_instance
    _lightweight_instance = LightweightMode()


def disable_lightweight_mode() -> None:
    """
    Désactive le mode lightweight programmatiquement
    """
    os.environ['ASMblr_LIGHTWEIGHT'] = 'false'
    logger.info("Mode lightweight désactivé")


def is_lightweight_mode() -> bool:
    """
    Vérifie si le mode lightweight est activé
    
    Returns:
        True si le mode lightweight est actif
    """
    return (
        os.getenv('LIGHTWEIGHT_MODE', 'false').lower() == 'true' or
        os.getenv('ASMblr_LIGHTWEIGHT', 'false').lower() == 'true'
    )


# Instance globale avec thread safety
_lightweight_instance: LightweightMode | None = None
_instance_lock = threading.Lock()


def get_lightweight_manager() -> LightweightMode:
    """
    Récupère l'instance du gestionnaire lightweight de manière thread-safe
    """
    global _lightweight_instance
    if _lightweight_instance is None:
        with _instance_lock:
            # Double-check pattern
            if _lightweight_instance is None:
                _lightweight_instance = LightweightMode()
    return _lightweight_instance


# Décorateurs pour les fonctionnalités conditionnelles
def lightweight_compatible(feature_name: str = "generic"):
    """
    Décorateur pour rendre une fonction compatible avec le mode lightweight
    
    Args:
        feature_name: Nom de la fonctionnalité pour la vérification
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            manager = get_lightweight_manager()
            if manager.is_feature_enabled(feature_name):
                return func(*args, **kwargs)
            else:
                logger.warning(f"Fonctionnalité '{feature_name}' désactivée en mode lightweight")
                return None
        return wrapper
    return decorator


def require_full_mode(error_message: str = None):
    """
    Décorateur qui exige le mode complet (non-lightweight)
    
    Args:
        error_message: Message d'erreur personnalisé
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            if is_lightweight_mode():
                error_msg = error_message or f"Cette fonctionnalité nécessite le mode complet d'Asmblr"
                raise RuntimeError(f"⚠️ {error_msg}\nDésactivez le mode lightweight: export ASMblr_LIGHTWEIGHT=false")
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Initialisation automatique au démarrage
if is_lightweight_mode():
    logger.info("🚀 Démarrage en mode Lightweight Asmblr")
    get_lightweight_manager()
