# Asmblr Code Style Guide

## Naming Conventions

### Classes
- Use PascalCase
- Examples: UserManager, DataProcessor, APIController

### Functions and Variables
- Use snake_case
- Examples: process_data(), user_name, max_retries

### Constants
- Use UPPER_SNAKE_CASE
- Examples: MAX_RETRIES, DEFAULT_TIMEOUT

## Code Quality Rules

### Function Length
- Maximum 50 lines
- Break down complex functions

### Complexity
- Maximum cyclomatic complexity: 10
- Avoid deep nesting (max 4 levels)

### Documentation
- All public functions must have docstrings
- All classes must have docstrings

### Error Handling
- Catch specific exceptions, not generic Exception
- Use meaningful error messages
