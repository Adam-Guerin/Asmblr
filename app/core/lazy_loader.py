"""
Lazy Loading Utilities for Heavy Libraries
Reduces startup time and memory usage
"""

from typing import Any, Callable, Optional
import importlib
import sys
from functools import lru_cache

class LazyLoader:
    """Lazy loader for heavy modules"""
    
    def __init__(self, module_name: str, warning_message: str = None):
        self.module_name = module_name
        self.warning_message = warning_message
        self._module = None
        
    def _load(self):
        """Load the module on first access"""
        if self._module is None:
            try:
                self._module = importlib.import_module(self.module_name)
                if self.warning_message:
                    import sys
                    print(f"[LAZY LOADING] {self.warning_message}", file=sys.stderr)
            except ImportError as e:
                raise ImportError(
                    f"Failed to lazy load {self.module_name}: {e}. "
                    f"Please install the required dependencies."
                )
        return self._module
    
    def __getattr__(self, name: str) -> Any:
        """Forward attribute access to loaded module"""
        module = self._load()
        return getattr(module, name)
    
    def __call__(self, *args, **kwargs) -> Any:
        """Make the loader callable"""
        module = self._load()
        return module(*args, **kwargs)

# Lazy loading instances for heavy libraries
torch = LazyLoader(
    "torch",
    "Loading PyTorch (~2GB memory usage). This may take a few seconds..."
)

transformers = LazyLoader(
    "transformers", 
    "Loading Transformers (~800MB memory usage). This may take a few seconds..."
)

diffusers = LazyLoader(
    "diffusers",
    "Loading Diffusers (~600MB memory usage). This may take a few seconds..."
)

accelerate = LazyLoader(
    "accelerate",
    "Loading Accelerate (~200MB memory usage)."
)

# LRU cache for frequently accessed modules
@lru_cache(maxsize=128)
def get_lightweight_model(model_name: str):
    """Get lightweight version of model when possible"""
    lightweight_models = {
        "gpt-3.5-turbo": "gpt-3.5-turbo",
        "gpt-4": "gpt-3.5-turbo",  # Fallback to lighter model
        "claude-3": "claude-instant",  # Use instant version
    }
    return lightweight_models.get(model_name, model_name)

def preload_essentials():
    """Preload only essential modules"""
    essential_modules = [
        "json", "pathlib", "datetime", "typing", 
        "asyncio", "logging", "requests", "bs4"
    ]
    
    for module in essential_modules:
        try:
            importlib.import_module(module)
        except ImportError:
            pass

# Preload essentials on import
preload_essentials()
