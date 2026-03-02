# Import Optimization Guide

## Heavy Libraries - Use Lazy Loading

### BAD:
```python
import torch  # Loads 2GB+ at startup
import transformers  # Loads 800MB+ at startup

def process_data():
    # Use torch here
    pass
```

### GOOD:
```python
def process_data():
    import torch  # Load only when needed
    import transformers  # Load only when needed
    # Use torch here
    pass
```

## Recommended Pattern

```python
# Lazy loading utility
def get_torch():
    global torch
    if torch is None:
        import torch
    return torch

def get_transformers():
    global transformers
    if transformers is None:
        import transformers
    return transformers
```

## Import Organization

1. Standard library imports first
2. Third-party imports second  
3. Local imports third
4. Heavy ML imports - lazy load only

## Memory Savings

- Lazy loading torch: ~2GB savings
- Lazy loading transformers: ~800MB savings
- Lazy loading diffusers: ~600MB savings
