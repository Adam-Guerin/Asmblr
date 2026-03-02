"""
AI-Powered Code Generation Assistant for Asmblr
Intelligent code generation with context awareness and best practices
"""

import json
import re
from typing import Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from loguru import logger
import redis.asyncio as redis

class CodeType(Enum):
    """Types of code that can be generated"""
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    TEST = "test"
    API_ENDPOINT = "api_endpoint"
    DATABASE_MODEL = "database_model"
    CONFIGURATION = "configuration"
    MIGRATION = "migration"
    UTILITY = "utility"

class CodeStyle(Enum):
    """Code generation styles"""
    SIMPLE = "simple"
    DOCUMENTED = "documented"
    OPTIMIZED = "optimized"
    SECURE = "secure"
    TESTED = "tested"
    PRODUCTION = "production"

@dataclass
class CodeGenerationRequest:
    """Code generation request"""
    description: str
    code_type: CodeType
    style: CodeStyle = CodeStyle.SIMPLE
    context: dict[str, Any] | None = None
    requirements: list[str] = None
    constraints: list[str] = None
    examples: list[str] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.requirements is None:
            self.requirements = []
        if self.constraints is None:
            self.constraints = []
        if self.examples is None:
            self.examples = []

@dataclass
class CodeGenerationResult:
    """Code generation result"""
    code: str
    explanation: str
    confidence: float
    suggestions: list[str]
    imports: list[str]
    dependencies: list[str]
    tests: str | None = None
    documentation: str | None = None
    metadata: dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class AICodeGenerator:
    """AI-powered code generation assistant"""
    
    def __init__(self):
        self.templates = {}
        self.patterns = {}
        self.best_practices = {}
        self.generation_history = []
        
        # Code generation configuration
        self.max_code_length = 10000  # characters
        self.default_indent = 4
        self.include_type_hints = True
        self.include_docstrings = True
        self.include_error_handling = True
        
        # Redis for distributed generation
        self.redis_client = None
        self.redis_enabled = False
        
    async def initialize(self):
        """Initialize the code generator"""
        try:
            # Initialize Redis connection
            try:
                self.redis_client = redis.from_url(
                    "redis://localhost:6379/10",
                    max_connections=20
                )
                await self.redis_client.ping()
                self.redis_enabled = True
                logger.info("Redis connection established for code generation")
            except Exception as e:
                logger.warning(f"Redis not available, using local code generation: {e}")
            
            # Load templates and patterns
            await self._load_templates()
            await self._load_patterns()
            await self._load_best_practices()
            
            logger.info("AI code generator initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize code generator: {e}")
            raise
    
    async def _load_templates(self):
        """Load code templates"""
        try:
            self.templates = {
                CodeType.FUNCTION: {
                    'simple': '''def {function_name}({parameters}):
    """{description}"""
    {body}
''',
                    'documented': '''def {function_name}({parameters}):
    """
    {description}
    
    Args:
        {args_doc}
    
    Returns:
        {returns_doc}
    
    Raises:
        {raises_doc}
    """
    {body}
''',
                    'optimized': '''def {function_name}({parameters}):
    """
    {description}
    
    Optimized for performance with caching and error handling.
    """
    {body}
''',
                    'secure': '''def {function_name}({parameters}):
    """
    {description}
    
    Security-focused implementation with input validation.
    """
    {body}
''',
                    'tested': '''def {function_name}({parameters}):
    """
    {description}
    
    Includes comprehensive error handling and logging.
    """
    {body}
'''
                },
                CodeType.CLASS: {
                    'simple': '''class {class_name}:
    """{description}"""
    
    def __init__(self{init_params}):
        {init_body}
    
    {methods}
''',
                    'documented': '''class {class_name}:
    """
    {description}
    
    Attributes:
        {attributes_doc}
    
    Methods:
        {methods_doc}
    """
    
    def __init__(self{init_params}):
        """
        Initialize {class_name}.
        
        {init_args_doc}
        """
        {init_body}
    
    {methods}
''',
                    'production': '''class {class_name}:
    """
    {description}
    
    Production-ready implementation with full error handling,
    logging, and type hints.
    """
    
    {imports}
    
    def __init__(self{init_params}):
        """
        Initialize {class_name}.
        
        {init_args_doc}
        """
        {init_body}
    
    {methods}
'''
                },
                CodeType.API_ENDPOINT: {
                    'simple': '''@{decorator}
def {endpoint_name}({parameters}):
    """{description}"""
    {body}
''',
                    'documented': '''@{decorator}
def {endpoint_name}({parameters}):
    """
    {description}
    
    Args:
        {args_doc}
    
    Returns:
        {returns_doc}
    
    Raises:
        {raises_doc}
    """
    {body}
''',
                    'secure': '''@{decorator}
def {endpoint_name}({parameters}):
    """
    {description}
    
    Secure endpoint with authentication and validation.
    """
    {body}
'''
                },
                CodeType.TEST: {
                    'simple': '''def test_{test_name}():
    """{description}"""
    {body}
''',
                    'documented': '''def test_{test_name}():
    """
    {description}
    
    Tests:
        {test_cases_doc}
    """
    {body}
''',
                    'comprehensive': '''import pytest
from unittest.mock import Mock, patch

{imports}

def test_{test_name}():
    """
    {description}
    
    Test Cases:
        {test_cases_doc}
    """
    {body}

{additional_tests}
'''
                }
            }
            
        except Exception as e:
            logger.error(f"Template loading failed: {e}")
    
    async def _load_patterns(self):
        """Load code patterns"""
        try:
            self.patterns = {
                'function_patterns': {
                    'data_processing': r'def\s+(\w+)\s*\([^)]*\)\s*->\s*\w+:',
                    'async_function': r'async\s+def\s+(\w+)\s*\([^)]*\):',
                    'generator': r'def\s+(\w+)\s*\([^)]*\)\s*->\s*Generator\[',
                    'decorator': r'@\w+',
                    'type_hints': r':\s*\w+',
                    'docstring': r'""".*?"""',
                    'error_handling': r'try\s*:',
                    'logging': r'logger\.',
                },
                'class_patterns': {
                    'class_definition': r'class\s+(\w+)',
                    'inheritance': r'class\s+\w+\([^)]+\):',
                    'property': r'@property',
                    'staticmethod': r'@staticmethod',
                    'classmethod': r'@classmethod',
                    'magic_method': r'def\s+__\w+__',
                },
                'api_patterns': {
                    'fastapi_endpoint': r'@\w+\.(get|post|put|delete|patch)',
                    'path_parameter': r'\w+:\s*\w+',
                    'query_parameter': r'\w+\s*=\s*None',
                    'response_model': r'response_model=',
                    'status_code': r'status_code=',
                }
            }
            
        except Exception as e:
            logger.error(f"Pattern loading failed: {e}")
    
    async def _load_best_practices(self):
        """Load best practices"""
        try:
            self.best_practices = {
                'function': [
                    'Use descriptive function names',
                    'Include type hints for parameters and return values',
                    'Add comprehensive docstrings',
                    'Handle errors gracefully',
                    'Log important operations',
                    'Keep functions focused on single responsibility',
                    'Use meaningful variable names',
                    'Add input validation',
                    'Consider performance implications',
                    'Write unit tests'
                ],
                'class': [
                    'Use PascalCase for class names',
                    'Include __init__ method with proper initialization',
                    'Document all public methods',
                    'Use properties for getters/setters',
                    'Implement __str__ and __repr__ methods',
                    'Consider dataclasses for simple data containers',
                    'Use type hints for all attributes',
                    'Implement proper error handling',
                    'Follow SOLID principles',
                    'Add comprehensive tests'
                ],
                'api': [
                    'Use proper HTTP methods',
                    'Validate input parameters',
                    'Return appropriate status codes',
                    'Include error responses',
                    'Add API documentation',
                    'Use consistent response format',
                    'Implement authentication/authorization',
                    'Add rate limiting',
                    'Log API calls',
                    'Write integration tests'
                ],
                'testing': [
                    'Write descriptive test names',
                    'Use AAA pattern (Arrange, Act, Assert)',
                    'Test edge cases and error conditions',
                    'Use fixtures for setup/teardown',
                    'Mock external dependencies',
                    'Test both success and failure cases',
                    'Keep tests independent',
                    'Use assertions with clear messages',
                    'Maintain high test coverage',
                    'Use parameterized tests for similar cases'
                ]
            }
            
        except Exception as e:
            logger.error(f"Best practices loading failed: {e}")
    
    async def generate_code(self, request: CodeGenerationRequest) -> CodeGenerationResult:
        """Generate code based on request"""
        try:
            # Analyze request
            analysis = await self._analyze_request(request)
            
            # Select appropriate template
            template = self._select_template(request.code_type, request.style)
            
            # Generate code components
            components = await self._generate_components(request, analysis)
            
            # Fill template
            code = self._fill_template(template, components)
            
            # Generate explanation
            explanation = await self._generate_explanation(request, components)
            
            # Generate suggestions
            suggestions = await self._generate_suggestions(request, components)
            
            # Extract imports and dependencies
            imports = self._extract_imports(code)
            dependencies = self._extract_dependencies(code)
            
            # Generate tests if requested
            tests = None
            if request.style in [CodeStyle.TESTED, CodeStyle.PRODUCTION]:
                tests = await self._generate_tests(request, components)
            
            # Generate documentation if requested
            documentation = None
            if request.style in [CodeStyle.DOCUMENTED, CodeStyle.PRODUCTION]:
                documentation = await self._generate_documentation(request, components)
            
            # Calculate confidence
            confidence = self._calculate_confidence(request, analysis, components)
            
            # Create result
            result = CodeGenerationResult(
                code=code,
                explanation=explanation,
                confidence=confidence,
                suggestions=suggestions,
                imports=imports,
                dependencies=dependencies,
                tests=tests,
                documentation=documentation,
                metadata={
                    'request_type': request.code_type.value,
                    'style': request.style.value,
                    'generation_time': datetime.now().isoformat(),
                    'components': components
                }
            )
            
            # Store in history
            self.generation_history.append({
                'timestamp': datetime.now(),
                'request': asdict(request),
                'result': asdict(result)
            })
            
            # Store in Redis if enabled
            if self.redis_enabled:
                await self._store_generation_result(result)
            
            logger.info(f"Generated {request.code_type.value} code with confidence {confidence:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            # Return fallback result
            return CodeGenerationResult(
                code=f"# Code generation failed: {str(e)}\n# Please try again with a more specific description",
                explanation=f"Unable to generate code due to: {str(e)}",
                confidence=0.0,
                suggestions=["Try providing a more detailed description", "Check if the request is too complex"],
                imports=[],
                dependencies=[],
                metadata={'error': str(e)}
            )
    
    async def _analyze_request(self, request: CodeGenerationRequest) -> dict[str, Any]:
        """Analyze the generation request"""
        try:
            analysis = {
                'complexity': self._assess_complexity(request.description),
                'keywords': self._extract_keywords(request.description),
                'entities': self._extract_entities(request.description),
                'intent': self._determine_intent(request.description),
                'requirements': request.requirements,
                'constraints': request.constraints,
                'context': request.context
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Request analysis failed: {e}")
            return {}
    
    def _assess_complexity(self, description: str) -> str:
        """Assess the complexity of the request"""
        try:
            # Simple heuristic based on description length and keywords
            if len(description) < 50:
                return "simple"
            elif len(description) < 150:
                return "medium"
            else:
                return "complex"
                
        except Exception as e:
            logger.error(f"Complexity assessment failed: {e}")
            return "medium"
    
    def _extract_keywords(self, description: str) -> list[str]:
        """Extract keywords from description"""
        try:
            # Simple keyword extraction
            keywords = []
            
            # Common programming keywords
            programming_keywords = [
                'function', 'class', 'method', 'variable', 'parameter',
                'return', 'if', 'else', 'for', 'while', 'try', 'except',
                'import', 'from', 'as', 'def', 'async', 'await',
                'list', 'dict', 'set', 'tuple', 'string', 'int', 'float',
                'database', 'api', 'endpoint', 'request', 'response',
                'user', 'data', 'process', 'validate', 'transform',
                'create', 'read', 'update', 'delete', 'search', 'filter'
            ]
            
            words = re.findall(r'\b\w+\b', description.lower())
            for word in words:
                if word in programming_keywords:
                    keywords.append(word)
            
            return list(set(keywords))
            
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return []
    
    def _extract_entities(self, description: str) -> list[str]:
        """Extract entities from description"""
        try:
            entities = []
            
            # Extract potential class names (PascalCase)
            pascal_case = re.findall(r'\b[A-Z][a-zA-Z0-9]*\b', description)
            entities.extend(pascal_case)
            
            # Extract potential function names (snake_case)
            snake_case = re.findall(r'\b[a-z][a-z0-9_]*\b', description)
            entities.extend(snake_case)
            
            return list(set(entities))
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return []
    
    def _determine_intent(self, description: str) -> str:
        """Determine the intent of the request"""
        try:
            description_lower = description.lower()
            
            if any(word in description_lower for word in ['create', 'new', 'add', 'implement']):
                return 'create'
            elif any(word in description_lower for word in ['update', 'modify', 'change', 'edit']):
                return 'update'
            elif any(word in description_lower for word in ['delete', 'remove', 'delete']):
                return 'delete'
            elif any(word in description_lower for word in ['get', 'fetch', 'retrieve', 'read', 'find']):
                return 'read'
            elif any(word in description_lower for word in ['process', 'transform', 'convert', 'calculate']):
                return 'process'
            elif any(word in description_lower for word in ['validate', 'check', 'verify', 'ensure']):
                return 'validate'
            else:
                return 'general'
                
        except Exception as e:
            logger.error(f"Intent determination failed: {e}")
            return 'general'
    
    def _select_template(self, code_type: CodeType, style: CodeStyle) -> str:
        """Select appropriate template"""
        try:
            if code_type in self.templates and style in self.templates[code_type]:
                return self.templates[code_type][style]
            elif code_type in self.templates and CodeStyle.SIMPLE in self.templates[code_type]:
                return self.templates[code_type][CodeStyle.SIMPLE]
            else:
                # Fallback template
                return '''# Generated code for {code_type}
{description}

# TODO: Implement this code
pass
'''
                
        except Exception as e:
            logger.error(f"Template selection failed: {e}")
            return '# Error: Could not select template\npass'
    
    async def _generate_components(self, request: CodeGenerationRequest, analysis: dict[str, Any]) -> dict[str, Any]:
        """Generate code components"""
        try:
            components = {}
            
            if request.code_type == CodeType.FUNCTION:
                components.update(await self._generate_function_components(request, analysis))
            elif request.code_type == CodeType.CLASS:
                components.update(await self._generate_class_components(request, analysis))
            elif request.code_type == CodeType.API_ENDPOINT:
                components.update(await self._generate_api_components(request, analysis))
            elif request.code_type == CodeType.TEST:
                components.update(await self._generate_test_components(request, analysis))
            else:
                components.update(await self._generate_generic_components(request, analysis))
            
            return components
            
        except Exception as e:
            logger.error(f"Component generation failed: {e}")
            return {}
    
    async def _generate_function_components(self, request: CodeGenerationRequest, analysis: dict[str, Any]) -> dict[str, Any]:
        """Generate function-specific components"""
        try:
            components = {}
            
            # Function name
            function_name = self._generate_function_name(request.description, analysis)
            components['function_name'] = function_name
            
            # Parameters
            parameters = self._generate_parameters(request.description, analysis)
            components['parameters'] = parameters
            
            # Body
            body = self._generate_function_body(request.description, analysis)
            components['body'] = body
            
            # Documentation
            components['description'] = request.description
            components['args_doc'] = self._generate_args_doc(parameters)
            components['returns_doc'] = self._generate_returns_doc(request.description)
            components['raises_doc'] = self._generate_raises_doc(request.description)
            
            return components
            
        except Exception as e:
            logger.error(f"Function component generation failed: {e}")
            return {}
    
    def _generate_function_name(self, description: str, analysis: dict[str, Any]) -> str:
        """Generate appropriate function name"""
        try:
            # Extract potential function names from entities
            entities = analysis.get('entities', [])
            intent = analysis.get('intent', 'general')
            
            # Common function name patterns
            if intent == 'create':
                prefix = 'create'
            elif intent == 'read':
                prefix = 'get' if 'get' not in description.lower() else 'fetch'
            elif intent == 'update':
                prefix = 'update'
            elif intent == 'delete':
                prefix = 'delete'
            elif intent == 'process':
                prefix = 'process'
            elif intent == 'validate':
                prefix = 'validate'
            else:
                prefix = 'handle'
            
            # Find appropriate entity
            entity = None
            for ent in entities:
                if ent.lower() in description.lower() and len(ent) > 3:
                    entity = ent.lower()
                    break
            
            if entity:
                function_name = f"{prefix}_{entity}"
            else:
                # Generate generic name
                function_name = f"{prefix}_data"
            
            # Ensure valid Python identifier
            function_name = re.sub(r'[^a-zA-Z0-9_]', '_', function_name)
            function_name = re.sub(r'^[0-9_]', '', function_name)
            
            return function_name or 'process_data'
            
        except Exception as e:
            logger.error(f"Function name generation failed: {e}")
            return 'process_data'
    
    def _generate_parameters(self, description: str, analysis: dict[str, Any]) -> str:
        """Generate function parameters"""
        try:
            parameters = []
            
            # Common parameters based on keywords
            keywords = analysis.get('keywords', [])
            
            if 'data' in keywords:
                parameters.append('data: Dict[str, Any]')
            if 'user' in keywords:
                parameters.append('user_id: str')
            if 'request' in keywords:
                parameters.append('request: Request')
            if 'response' in keywords:
                parameters.append('response: Response')
            if 'database' in keywords or 'db' in keywords:
                parameters.append('db_session: Session')
            if 'api' in keywords:
                parameters.append('api_key: str')
            
            # Add context parameter if needed
            if analysis.get('complexity') == 'complex':
                parameters.append('context: Optional[Dict[str, Any]] = None')
            
            # Join parameters
            if parameters:
                return ', '.join(parameters)
            else:
                return ''
                
        except Exception as e:
            logger.error(f"Parameter generation failed: {e}")
            return ''
    
    def _generate_function_body(self, description: str, analysis: dict[str, Any]) -> str:
        """Generate function body"""
        try:
            body_lines = []
            intent = analysis.get('intent', 'general')
            keywords = analysis.get('keywords', [])
            
            # Add logging
            body_lines.append('    logger.info(f"Starting {function_name}")')
            
            # Add input validation
            if 'validate' in keywords or intent == 'validate':
                body_lines.append('    # Validate input')
                body_lines.append('    if not data:')
                body_lines.append('        raise ValueError("Data cannot be empty")')
            
            # Add core logic based on intent
            if intent == 'create':
                body_lines.append('    # Create new resource')
                body_lines.append('    result = create_resource(data)')
            elif intent == 'read':
                body_lines.append('    # Retrieve resource')
                body_lines.append('    result = get_resource(data)')
            elif intent == 'update':
                body_lines.append('    # Update resource')
                body_lines.append('    result = update_resource(data)')
            elif intent == 'delete':
                body_lines.append('    # Delete resource')
                body_lines.append('    result = delete_resource(data)')
            elif intent == 'process':
                body_lines.append('    # Process data')
                body_lines.append('    result = process_data(data)')
            else:
                body_lines.append('    # Implement logic')
                body_lines.append('    result = handle_request(data)')
            
            # Add return statement
            body_lines.append('    return result')
            
            # Add logging
            body_lines.append('    logger.info(f"Completed {function_name}")')
            
            # Indent properly
            return '\n'.join(body_lines)
            
        except Exception as e:
            logger.error(f"Function body generation failed: {e}")
            return '    # TODO: Implement function logic\n    pass'
    
    def _generate_args_doc(self, parameters: str) -> str:
        """Generate arguments documentation"""
        try:
            if not parameters:
                return 'None'
            
            args_doc = []
            for param in parameters.split(','):
                param_name = param.split(':')[0].strip()
                param_type = param.split(':')[1].strip() if ':' in param else 'Any'
                
                if param_name == 'data':
                    args_doc.append(f'data ({param_type}): Input data to process')
                elif param_name == 'user_id':
                    args_doc.append(f'user_id ({param_type}): User identifier')
                elif param_name == 'request':
                    args_doc.append(f'request ({param_type}): HTTP request object')
                elif param_name == 'response':
                    args_doc.append(f'response ({param_type}): HTTP response object')
                else:
                    args_doc.append(f'{param_name} ({param_type}): Function parameter')
            
            return '\n        '.join(args_doc)
            
        except Exception as e:
            logger.error(f"Args documentation generation failed: {e}")
            return 'None'
    
    def _generate_returns_doc(self, description: str) -> str:
        """Generate return value documentation"""
        try:
            intent = self._determine_intent(description)
            
            return_map = {
                'create': 'Created resource data',
                'read': 'Retrieved resource data',
                'update': 'Updated resource data',
                'delete': 'Deletion confirmation',
                'process': 'Processed result data',
                'validate': 'Validation result',
                'general': 'Operation result'
            }
            
            return return_map.get(intent, 'Operation result')
            
        except Exception as e:
            logger.error(f"Returns documentation generation failed: {e}")
            return 'Operation result'
    
    def _generate_raises_doc(self, description: str) -> str:
        """Generate raises documentation"""
        try:
            raises = []
            
            # Common exceptions based on keywords
            if 'validate' in description.lower():
                raises.append('ValueError: When input validation fails')
            
            if 'database' in description.lower() or 'db' in description.lower():
                raises.append('DatabaseError: When database operation fails')
            
            if 'api' in description.lower():
                raises.append('APIError: When API call fails')
            
            if not raises:
                raises.append('Exception: For general errors')
            
            return '\n        '.join(raises)
            
        except Exception as e:
            logger.error(f"Raises documentation generation failed: {e}")
            return 'Exception: For general errors'
    
    async def _generate_class_components(self, request: CodeGenerationRequest, analysis: dict[str, Any]) -> dict[str, Any]:
        """Generate class-specific components"""
        try:
            components = {}
            
            # Class name
            class_name = self._generate_class_name(request.description, analysis)
            components['class_name'] = class_name
            
            # Init parameters
            init_params = self._generate_init_params(request.description, analysis)
            components['init_params'] = init_params
            
            # Init body
            init_body = self._generate_init_body(request.description, analysis)
            components['init_body'] = init_body
            
            # Methods
            methods = self._generate_class_methods(request.description, analysis)
            components['methods'] = methods
            
            # Documentation
            components['description'] = request.description
            components['attributes_doc'] = self._generate_attributes_doc(init_params)
            components['methods_doc'] = self._generate_methods_doc(methods)
            
            return components
            
        except Exception as e:
            logger.error(f"Class component generation failed: {e}")
            return {}
    
    def _generate_class_name(self, description: str, analysis: dict[str, Any]) -> str:
        """Generate appropriate class name"""
        try:
            entities = analysis.get('entities', [])
            
            # Find appropriate entity (PascalCase)
            for entity in entities:
                if entity[0].isupper() and len(entity) > 3:
                    return entity
            
            # Generate generic class name
            if 'service' in description.lower():
                return 'DataService'
            elif 'manager' in description.lower():
                return 'DataManager'
            elif 'handler' in description.lower():
                return 'DataHandler'
            elif 'processor' in description.lower():
                return 'DataProcessor'
            else:
                return 'DataManager'
                
        except Exception as e:
            logger.error(f"Class name generation failed: {e}")
            return 'DataManager'
    
    def _generate_init_params(self, description: str, analysis: dict[str, Any]) -> str:
        """Generate __init__ parameters"""
        try:
            params = []
            
            # Common init parameters
            if 'database' in description.lower() or 'db' in description.lower():
                params.append('db_url: str')
            if 'api' in description.lower():
                params.append('api_key: str')
            if 'config' in description.lower():
                params.append('config: Dict[str, Any]')
            
            if params:
                return ', ' + ', '.join(params)
            else:
                return ''
                
        except Exception as e:
            logger.error(f"Init parameters generation failed: {e}")
            return ''
    
    def _generate_init_body(self, description: str, analysis: dict[str, Any]) -> str:
        """Generate __init__ body"""
        try:
            body_lines = []
            
            # Add initialization logic
            if 'database' in description.lower() or 'db' in description.lower():
                body_lines.append('        self.db_url = db_url')
                body_lines.append('        self.db_session = None')
            
            if 'api' in description.lower():
                body_lines.append('        self.api_key = api_key')
                body_lines.append('        self.client = None')
            
            if 'config' in description.lower():
                body_lines.append('        self.config = config')
                body_lines.append('        self.settings = config.get("settings", {})')
            
            # Add common initialization
            if not body_lines:
                body_lines.append('        # Initialize attributes')
                body_lines.append('        self.data = {}')
            
            return '\n        '.join(body_lines)
            
        except Exception as e:
            logger.error(f"Init body generation failed: {e}")
            return '        # TODO: Initialize attributes'
    
    def _generate_class_methods(self, description: str, analysis: dict[str, Any]) -> str:
        """Generate class methods"""
        try:
            methods = []
            
            # Add common methods based on intent
            intent = analysis.get('intent', 'general')
            
            if intent == 'create':
                methods.append('    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:\n        """Create new resource"""\n        return {"status": "created", "data": data}')
            elif intent == 'read':
                methods.append('    def get(self, resource_id: str) -> Dict[str, Any]:\n        """Get resource by ID"""\n        return {"id": resource_id, "data": {}}')
            elif intent == 'update':
                methods.append('    def update(self, resource_id: str, data: Dict[str, Any]) -> Dict[str, Any]:\n        """Update resource"""\n        return {"id": resource_id, "data": data}')
            elif intent == 'delete':
                methods.append('    def delete(self, resource_id: str) -> bool:\n        """Delete resource"""\n        return True')
            
            # Add utility methods
            methods.append('    def __str__(self) -> str:\n        """String representation"""\n        return f"{self.__class__.__name__}()"')
            
            return '\n\n    '.join(methods)
            
        except Exception as e:
            logger.error(f"Class methods generation failed: {e}")
            return '    def __str__(self) -> str:\n        """String representation"""\n        return f"{self.__class__.__name__}()"'
    
    def _generate_attributes_doc(self, init_params: str) -> str:
        """Generate attributes documentation"""
        try:
            if not init_params:
                return 'No specific attributes'
            
            attributes = []
            for param in init_params.split(','):
                param_name = param.split(':')[0].strip().replace(', ', '')
                if param_name:
                    attributes.append(f'{param_name}: Configuration attribute')
            
            return '\n        '.join(attributes)
            
        except Exception as e:
            logger.error(f"Attributes documentation generation failed: {e}")
            return 'No specific attributes'
    
    def _generate_methods_doc(self, methods: str) -> str:
        """Generate methods documentation"""
        try:
            if not methods:
                return 'No specific methods'
            
            # Extract method names
            method_names = re.findall(r'def\s+(\w+)\s*\(', methods)
            
            if method_names:
                return ', '.join(method_names)
            else:
                return 'General methods'
                
        except Exception as e:
            logger.error(f"Methods documentation generation failed: {e}")
            return 'General methods'
    
    async def _generate_api_components(self, request: CodeGenerationRequest, analysis: dict[str, Any]) -> dict[str, Any]:
        """Generate API endpoint components"""
        try:
            components = {}
            
            # HTTP method and decorator
            http_method = self._determine_http_method(request.description)
            components['decorator'] = f'@app.{http_method}'
            
            # Endpoint name
            endpoint_name = self._generate_endpoint_name(request.description, analysis)
            components['endpoint_name'] = endpoint_name
            
            # Parameters
            parameters = self._generate_api_parameters(request.description, analysis)
            components['parameters'] = parameters
            
            # Body
            body = self._generate_api_body(request.description, analysis)
            components['body'] = body
            
            # Documentation
            components['description'] = request.description
            components['args_doc'] = self._generate_api_args_doc(parameters)
            components['returns_doc'] = 'JSON response'
            components['raises_doc'] = 'HTTPException for errors'
            
            return components
            
        except Exception as e:
            logger.error(f"API component generation failed: {e}")
            return {}
    
    def _determine_http_method(self, description: str) -> str:
        """Determine HTTP method from description"""
        try:
            description_lower = description.lower()
            
            if any(word in description_lower for word in ['create', 'new', 'add', 'post']):
                return 'post'
            elif any(word in description_lower for word in ['get', 'fetch', 'retrieve', 'read']):
                return 'get'
            elif any(word in description_lower for word in ['update', 'modify', 'edit', 'put']):
                return 'put'
            elif any(word in description_lower for word in ['delete', 'remove']):
                return 'delete'
            elif any(word in description_lower for word in ['patch', 'partial']):
                return 'patch'
            else:
                return 'get'
                
        except Exception as e:
            logger.error(f"HTTP method determination failed: {e}")
            return 'get'
    
    def _generate_endpoint_name(self, description: str, analysis: dict[str, Any]) -> str:
        """Generate endpoint name"""
        try:
            entities = analysis.get('entities', [])
            intent = analysis.get('intent', 'general')
            
            # Find appropriate entity
            entity = None
            for ent in entities:
                if ent.lower() in description.lower() and len(ent) > 3:
                    entity = ent.lower()
                    break
            
            if entity:
                if intent == 'create':
                    return f"create_{entity}"
                elif intent == 'read':
                    return f"get_{entity}"
                elif intent == 'update':
                    return f"update_{entity}"
                elif intent == 'delete':
                    return f"delete_{entity}"
                else:
                    return f"{entity}_endpoint"
            else:
                return "data_endpoint"
                
        except Exception as e:
            logger.error(f"Endpoint name generation failed: {e}")
            return "data_endpoint"
    
    def _generate_api_parameters(self, description: str, analysis: dict[str, Any]) -> str:
        """Generate API endpoint parameters"""
        try:
            parameters = []
            
            # Add common API parameters
            if 'user' in description.lower():
                parameters.append('user_id: str')
            if 'data' in description.lower():
                parameters.append('payload: Dict[str, Any]')
            
            # Add path parameters
            if 'id' in description.lower():
                parameters.append('item_id: str')
            
            # Add query parameters
            if 'filter' in description.lower() or 'search' in description.lower():
                parameters.append('query: Optional[str] = None')
            
            if parameters:
                return ', '.join(parameters)
            else:
                return ''
                
        except Exception as e:
            logger.error(f"API parameters generation failed: {e}")
            return ''
    
    def _generate_api_body(self, description: str, analysis: dict[str, Any]) -> str:
        """Generate API endpoint body"""
        try:
            body_lines = []
            intent = analysis.get('intent', 'general')
            
            # Add logging
            body_lines.append('    logger.info(f"Received request to {endpoint_name}")')
            
            # Add validation
            body_lines.append('    # Validate request')
            body_lines.append('    if not payload:')
            body_lines.append('        raise HTTPException(status_code=400, detail="Invalid data")')
            
            # Add core logic based on intent
            if intent == 'create':
                body_lines.append('    # Create resource')
                body_lines.append('    result = create_resource(payload)')
                body_lines.append('    return {"status": "success", "data": result}')
            elif intent == 'read':
                body_lines.append('    # Get resource')
                body_lines.append('    result = get_resource(item_id)')
                body_lines.append('    return {"data": result}')
            elif intent == 'update':
                body_lines.append('    # Update resource')
                body_lines.append('    result = update_resource(item_id, payload)')
                body_lines.append('    return {"status": "updated", "data": result}')
            elif intent == 'delete':
                body_lines.append('    # Delete resource')
                body_lines.append('    delete_resource(item_id)')
                body_lines.append('    return {"status": "deleted"}')
            else:
                body_lines.append('    # Process request')
                body_lines.append('    result = process_request(payload)')
                body_lines.append('    return {"data": result}')
            
            return '\n    '.join(body_lines)
            
        except Exception as e:
            logger.error(f"API body generation failed: {e}")
            return '    # TODO: Implement endpoint logic\n    return {"status": "not_implemented"}'
    
    def _generate_api_args_doc(self, parameters: str) -> str:
        """Generate API arguments documentation"""
        try:
            if not parameters:
                return 'No parameters'
            
            args_doc = []
            for param in parameters.split(','):
                param_name = param.split(':')[0].strip()
                param_type = param.split(':')[1].strip() if ':' in param else 'Any'
                
                if param_name == 'user_id':
                    args_doc.append(f'user_id ({param_type}): User identifier')
                elif param_name == 'payload':
                    args_doc.append(f'payload ({param_type}): Request payload')
                elif param_name == 'item_id':
                    args_doc.append(f'item_id ({param_type}): Item identifier')
                elif param_name == 'query':
                    args_doc.append(f'query ({param_type}): Search query')
                else:
                    args_doc.append(f'{param_name} ({param_type}): Endpoint parameter')
            
            return '\n        '.join(args_doc)
            
        except Exception as e:
            logger.error(f"API args documentation generation failed: {e}")
            return 'No parameters'
    
    async def _generate_test_components(self, request: CodeGenerationRequest, analysis: dict[str, Any]) -> dict[str, Any]:
        """Generate test components"""
        try:
            components = {}
            
            # Test name
            test_name = self._generate_test_name(request.description, analysis)
            components['test_name'] = test_name
            
            # Test body
            body = self._generate_test_body(request.description, analysis)
            components['body'] = body
            
            # Documentation
            components['description'] = f"Test {request.description}"
            components['test_cases_doc'] = self._generate_test_cases_doc(request.description)
            
            return components
            
        except Exception as e:
            logger.error(f"Test component generation failed: {e}")
            return {}
    
    def _generate_test_name(self, description: str, analysis: dict[str, Any]) -> str:
        """Generate test name"""
        try:
            entities = analysis.get('entities', [])
            intent = analysis.get('intent', 'general')
            
            # Find appropriate entity
            entity = None
            for ent in entities:
                if ent.lower() in description.lower() and len(ent) > 3:
                    entity = ent.lower()
                    break
            
            if entity:
                return f"test_{intent}_{entity}"
            else:
                return f"test_{intent}_function"
                
        except Exception as e:
            logger.error(f"Test name generation failed: {e}")
            return 'test_function'
    
    def _generate_test_body(self, description: str, analysis: dict[str, Any]) -> str:
        """Generate test body"""
        try:
            body_lines = []
            intent = analysis.get('intent', 'general')
            
            # Add test setup
            body_lines.append('    # Setup')
            body_lines.append('    test_data = {"key": "value"}')
            
            # Add test action based on intent
            if intent == 'create':
                body_lines.append('    # Test creation')
                body_lines.append('    result = create_function(test_data)')
                body_lines.append('    assert result is not None')
                body_lines.append('    assert result["status"] == "created"')
            elif intent == 'read':
                body_lines.append('    # Test retrieval')
                body_lines.append('    result = get_function("test_id")')
                body_lines.append('    assert result is not None')
            elif intent == 'update':
                body_lines.append('    # Test update')
                body_lines.append('    result = update_function("test_id", test_data)')
                body_lines.append('    assert result["status"] == "updated"')
            elif intent == 'delete':
                body_lines.append('    # Test deletion')
                body_lines.append('    result = delete_function("test_id")')
                body_lines.append('    assert result is True')
            else:
                body_lines.append('    # Test general functionality')
                body_lines.append('    result = process_function(test_data)')
                body_lines.append('    assert result is not None')
            
            # Add cleanup
            body_lines.append('    # Cleanup')
            body_lines.append('    pass')
            
            return '\n    '.join(body_lines)
            
        except Exception as e:
            logger.error(f"Test body generation failed: {e}")
            return '    # TODO: Implement test\n    assert True'
    
    def _generate_test_cases_doc(self, description: str) -> str:
        """Generate test cases documentation"""
        try:
            intent = self._determine_intent(description)
            
            cases_map = {
                'create': 'Valid creation, invalid data, duplicate creation',
                'read': 'Valid ID, invalid ID, non-existent ID',
                'update': 'Valid update, invalid data, non-existent ID',
                'delete': 'Valid ID, invalid ID, non-existent ID',
                'process': 'Valid data, invalid data, edge cases'
            }
            
            return cases_map.get(intent, 'Basic functionality')
            
        except Exception as e:
            logger.error(f"Test cases documentation generation failed: {e}")
            return 'Basic functionality'
    
    async def _generate_generic_components(self, request: CodeGenerationRequest, analysis: dict[str, Any]) -> dict[str, Any]:
        """Generate generic components"""
        try:
            components = {}
            
            # Basic components
            components['description'] = request.description
            components['body'] = f'# TODO: Implement {request.description}\npass'
            
            return components
            
        except Exception as e:
            logger.error(f"Generic component generation failed: {e}")
            return {}
    
    def _fill_template(self, template: str, components: dict[str, Any]) -> str:
        """Fill template with components"""
        try:
            code = template
            
            # Replace placeholders
            for key, value in components.items():
                placeholder = f'{{{key}}}'
                if placeholder in code:
                    code = code.replace(placeholder, str(value))
            
            return code
            
        except Exception as e:
            logger.error(f"Template filling failed: {e}")
            return '# Error: Could not fill template\npass'
    
    async def _generate_explanation(self, request: CodeGenerationRequest, components: dict[str, Any]) -> str:
        """Generate code explanation"""
        try:
            explanation_parts = []
            
            # Add overview
            explanation_parts.append(f"Generated {request.code_type.value} with {request.style.value} style.")
            
            # Add key features
            if request.style == CodeStyle.DOCUMENTED:
                explanation_parts.append("Includes comprehensive documentation with docstrings.")
            elif request.style == CodeStyle.OPTIMIZED:
                explanation_parts.append("Optimized for performance with efficient algorithms.")
            elif request.style == CodeStyle.SECURE:
                explanation_parts.append("Includes security measures and input validation.")
            elif request.style == CodeStyle.TESTED:
                explanation_parts.append("Includes error handling and logging.")
            elif request.style == CodeStyle.PRODUCTION:
                explanation_parts.append("Production-ready with full error handling, logging, and type hints.")
            
            # Add implementation details
            if request.code_type == CodeType.FUNCTION:
                explanation_parts.append(f"Function '{components.get('function_name', 'unknown')}' implements the requested functionality.")
            elif request.code_type == CodeType.CLASS:
                explanation_parts.append(f"Class '{components.get('class_name', 'Unknown')}' provides the requested functionality with proper encapsulation.")
            elif request.code_type == CodeType.API_ENDPOINT:
                explanation_parts.append(f"API endpoint '{components.get('endpoint_name', 'unknown')}' handles HTTP requests with proper validation.")
            
            return ' '.join(explanation_parts)
            
        except Exception as e:
            logger.error(f"Explanation generation failed: {e}")
            return f"Generated {request.code_type.value} code based on the description."
    
    async def _generate_suggestions(self, request: CodeGenerationRequest, components: dict[str, Any]) -> list[str]:
        """Generate improvement suggestions"""
        try:
            suggestions = []
            
            # Add general suggestions
            suggestions.append("Consider adding more comprehensive error handling")
            suggestions.append("Add unit tests to ensure code quality")
            suggestions.append("Review and optimize for performance if needed")
            
            # Add specific suggestions based on code type
            if request.code_type == CodeType.FUNCTION:
                suggestions.append("Consider breaking down complex functions into smaller ones")
                suggestions.append("Add type hints for better code documentation")
            elif request.code_type == CodeType.CLASS:
                suggestions.append("Consider implementing __repr__ method for better debugging")
                suggestions.append("Add property decorators for controlled access")
            elif request.code_type == CodeType.API_ENDPOINT:
                suggestions.append("Add rate limiting to prevent abuse")
                suggestions.append("Implement proper authentication and authorization")
            elif request.code_type == CodeType.TEST:
                suggestions.append("Add more test cases for edge conditions")
                suggestions.append("Consider using parameterized tests for similar cases")
            
            # Add style-specific suggestions
            if request.style == CodeStyle.SIMPLE:
                suggestions.append("Consider upgrading to documented style for better maintainability")
            elif request.style == CodeStyle.PRODUCTION:
                suggestions.append("Consider adding integration tests")
                suggestions.append("Add monitoring and metrics collection")
            
            return suggestions[:5]  # Return top 5 suggestions
            
        except Exception as e:
            logger.error(f"Suggestion generation failed: {e}")
            return ["Review the generated code for improvements"]
    
    def _extract_imports(self, code: str) -> list[str]:
        """Extract import statements from generated code"""
        try:
            imports = []
            
            # Find import statements
            import_patterns = [
                r'import\s+(\w+)',
                r'from\s+(\w+)\s+import',
                r'from\s+(\w+\.\w+)\s+import'
            ]
            
            for pattern in import_patterns:
                matches = re.findall(pattern, code)
                imports.extend(matches)
            
            return list(set(imports))
            
        except Exception as e:
            logger.error(f"Import extraction failed: {e}")
            return []
    
    def _extract_dependencies(self, code: str) -> list[str]:
        """Extract dependencies from generated code"""
        try:
            dependencies = []
            
            # Common dependencies based on code patterns
            if 'requests' in code:
                dependencies.append('requests')
            if 'fastapi' in code:
                dependencies.append('fastapi')
            if 'pydantic' in code:
                dependencies.append('pydantic')
            if 'sqlalchemy' in code:
                dependencies.append('sqlalchemy')
            if 'pytest' in code:
                dependencies.append('pytest')
            if 'redis' in code:
                dependencies.append('redis')
            
            return list(set(dependencies))
            
        except Exception as e:
            logger.error(f"Dependency extraction failed: {e}")
            return []
    
    async def _generate_tests(self, request: CodeGenerationRequest, components: dict[str, Any]) -> str:
        """Generate unit tests for the generated code"""
        try:
            test_code = []
            
            # Add imports
            test_code.append('import pytest')
            test_code.append('from unittest.mock import Mock, patch')
            test_code.append('')
            
            # Add test class if generating a class
            if request.code_type == CodeType.CLASS:
                class_name = components.get('class_name', 'TestClass')
                test_code.append(f'class Test{class_name}:')
                test_code.append('')
                
                # Add test methods
                test_code.append(f'    def test_init(self):')
                test_code.append(f'        """Test {class_name} initialization"""')
                test_code.append(f'        instance = {class_name}()')
                test_code.append(f'        assert instance is not None')
                test_code.append('')
            
            # Add function test
            if request.code_type == CodeType.FUNCTION:
                function_name = components.get('function_name', 'test_function')
                test_code.append(f'def test_{function_name}():')
                test_code.append(f'    """Test {function_name} function"""')
                test_code.append(f'        # TODO: Implement test')
                test_code.append(f'        assert True')
                test_code.append('')
            
            return '\n'.join(test_code)
            
        except Exception as e:
            logger.error(f"Test generation failed: {e}")
            return '# TODO: Add unit tests'
    
    async def _generate_documentation(self, request: CodeGenerationRequest, components: dict[str, Any]) -> str:
        """Generate documentation for the generated code"""
        try:
            doc_lines = []
            
            # Add title
            doc_lines.append(f"# {request.description}")
            doc_lines.append('')
            
            # Add overview
            doc_lines.append("## Overview")
            doc_lines.append(f"This {request.code_type.value} provides functionality for {request.description}.")
            doc_lines.append('')
            
            # Add usage examples
            doc_lines.append("## Usage")
            doc_lines.append("```python")
            
            if request.code_type == CodeType.FUNCTION:
                function_name = components.get('function_name', 'function_name')
                parameters = components.get('parameters', '')
                doc_lines.append(f"result = {function_name}({parameters})")
            elif request.code_type == CodeType.CLASS:
                class_name = components.get('class_name', 'ClassName')
                doc_lines.append(f"instance = {class_name}()")
                doc_lines.append("result = instance.some_method()")
            
            doc_lines.append("```")
            doc_lines.append('')
            
            # Add API reference
            doc_lines.append("## API Reference")
            doc_lines.append("Detailed API documentation will be added here.")
            doc_lines.append('')
            
            return '\n'.join(doc_lines)
            
        except Exception as e:
            logger.error(f"Documentation generation failed: {e}")
            return f"# {request.description}\n\nDocumentation will be added here."
    
    def _calculate_confidence(self, request: CodeGenerationRequest, analysis: dict[str, Any], components: dict[str, Any]) -> float:
        """Calculate confidence in the generated code"""
        try:
            confidence = 0.5  # Base confidence
            
            # Increase confidence based on description clarity
            if len(request.description) > 20:
                confidence += 0.1
            
            # Increase confidence if we have good analysis
            if analysis.get('keywords'):
                confidence += 0.1
            
            # Increase confidence if we have components
            if components:
                confidence += 0.2
            
            # Increase confidence for simpler requests
            if analysis.get('complexity') == 'simple':
                confidence += 0.1
            
            return min(1.0, confidence)
            
        except Exception as e:
            logger.error(f"Confidence calculation failed: {e}")
            return 0.5
    
    async def _store_generation_result(self, result: CodeGenerationResult):
        """Store generation result in Redis"""
        try:
            key = f"code_generation:{int(time.time())}"
            value = asdict(result)
            
            await self.redis_client.setex(
                key,
                24 * 3600,  # 24 hours
                json.dumps(value, default=str)
            )
            
        except Exception as e:
            logger.error(f"Redis generation result storage error: {e}")
    
    async def get_generation_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get generation history"""
        try:
            return self.generation_history[-limit:]
            
        except Exception as e:
            logger.error(f"Generation history retrieval failed: {e}")
            return []
    
    async def shutdown(self):
        """Shutdown the code generator"""
        logger.info("AI code generator shutdown complete")

# Global code generator instance
ai_code_generator = AICodeGenerator()
