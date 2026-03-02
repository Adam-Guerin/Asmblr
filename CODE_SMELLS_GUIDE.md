# Code Smell Elimination Guide

## Common Code Smells and Fixes

### 1. Bare Except Clauses
**Problem**: `except:` catches all exceptions
```python
# BAD
try:
    risky_operation()
except:
    pass  # Hides all errors

# GOOD
try:
    risky_operation()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
except ConnectionError as e:
    logger.error(f"Connection failed: {e}")
```

### 2. Print Statements Instead of Logging
**Problem**: Using print() for debugging
```python
# BAD
print("Debug information")

# GOOD
logger.debug("Debug information")
logger.info("User action completed")
logger.error("Error occurred")
```

### 3. Wildcard Imports
**Problem**: `from module import *`
```python
# BAD
from utils import *

# GOOD
from utils import helper_function, AnotherClass
```

### 4. Inefficient Loops
**Problem**: `for i in range(len(list))`
```python
# BAD
for i in range(len(items)):
    process(items[i])

# GOOD
for item in items:
    process(item)

# OR for index and item
for i, item in enumerate(items):
    process(i, item)
```

### 5. Magic Numbers
**Problem**: Hardcoded numbers in code
```python
# BAD
if user.age > 65:
    return "senior"

# GOOD
SENIOR_AGE = 65
if user.age > SENIOR_AGE:
    return "senior"
```

## Automated Detection

### 1. Linter Configuration
```toml
[tool.ruff]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "SIM", # flake8-simplify
]
```

### 2. Pre-commit Hooks
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
  
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.261
    hooks:
      - id: ruff
        args: [--fix]
```

## Review Process

### 1. Code Review Checklist
- [ ] No bare except clauses
- [ ] Proper logging instead of print
- [ ] No wildcard imports
- [ ] No magic numbers
- [ ] Reasonable function length
- [ ] Proper error handling
- [ ] No code duplication

### 2. Automated Checks
- [ ] Linter passes without errors
- [ ] Code formatted with black
- [ ] Type checking with mypy
- [ ] Test coverage > 80%
- [ ] Security scan passes
