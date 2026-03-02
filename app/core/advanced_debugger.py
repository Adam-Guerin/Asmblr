"""
Advanced Debugging Tools for Asmblr
AI-powered debugging with intelligent error analysis and suggestions
"""

import time
import json
import traceback
import sys
from typing import Any
from collections.abc import Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import psutil
from loguru import logger
import redis.asyncio as redis

class DebugLevel(Enum):
    """Debugging levels"""
    BASIC = "basic"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"
    EXPERT = "expert"

class ErrorCategory(Enum):
    """Error categories for classification"""
    SYNTAX = "syntax"
    RUNTIME = "runtime"
    LOGIC = "logic"
    PERFORMANCE = "performance"
    MEMORY = "memory"
    NETWORK = "network"
    DATABASE = "database"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"
    UNKNOWN = "unknown"

@dataclass
class DebugSession:
    """Debug session information"""
    id: str
    start_time: datetime
    end_time: datetime | None = None
    level: DebugLevel = DebugLevel.BASIC
    component: str = "unknown"
    status: str = "active"
    errors_found: int = 0
    issues_resolved: int = 0
    metadata: dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ErrorAnalysis:
    """Error analysis result"""
    error_id: str
    error_type: str
    category: ErrorCategory
    severity: str
    description: str
    stack_trace: str
    context: dict[str, Any]
    suggestions: list[str]
    related_files: list[str]
    similar_errors: list[str]
    fix_confidence: float
    estimated_fix_time: str
    metadata: dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class PerformanceProfile:
    """Performance profiling result"""
    function_name: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    call_count: int
    average_time: float
    max_time: float
    min_time: float
    bottlenecks: list[str]
    optimization_suggestions: list[str]
    timestamp: datetime

class AdvancedDebugger:
    """AI-powered advanced debugging system"""
    
    def __init__(self):
        self.sessions = {}
        self.error_patterns = {}
        self.performance_profiles = {}
        self.debug_history = []
        
        # Debugging configuration
        self.max_sessions = 100
        self.auto_analyze = True
        self.suggest_fixes = True
        self.track_performance = True
        
        # Error classification patterns
        self.error_patterns = {
            ErrorCategory.SYNTAX: [
                r"SyntaxError", r"IndentationError", r"NameError.*not defined"
            ],
            ErrorCategory.RUNTIME: [
                r"TypeError", r"ValueError", r"KeyError", r"IndexError", r"AttributeError"
            ],
            ErrorCategory.MEMORY: [
                r"MemoryError", r"OutOfMemoryError", r"RecursionError"
            ],
            ErrorCategory.NETWORK: [
                r"ConnectionError", r"TimeoutError", r"NetworkError"
            ],
            ErrorCategory.DATABASE: [
                r"DatabaseError", r"OperationalError", r"IntegrityError"
            ],
            ErrorCategory.CONFIGURATION: [
                r"ConfigurationError", r"ImportError", r"ModuleNotFoundError"
            ]
        }
        
        # Performance thresholds
        self.performance_thresholds = {
            'slow_function': 1.0,  # seconds
            'memory_intensive': 100 * 1024 * 1024,  # 100MB
            'high_cpu': 80.0,  # percentage
            'frequent_calls': 1000  # calls
        }
        
        # Redis for distributed debugging
        self.redis_client = None
        self.redis_enabled = False
        
    async def initialize(self):
        """Initialize the advanced debugger"""
        try:
            # Initialize Redis connection
            try:
                self.redis_client = redis.from_url(
                    "redis://localhost:6379/9",
                    max_connections=20
                )
                await self.redis_client.ping()
                self.redis_enabled = True
                logger.info("Redis connection established for debugging")
            except Exception as e:
                logger.warning(f"Redis not available, using local debugging: {e}")
            
            logger.info("Advanced debugger initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize debugger: {e}")
            raise
    
    def create_session(
        self,
        level: DebugLevel = DebugLevel.BASIC,
        component: str = "unknown"
    ) -> str:
        """Create a new debug session"""
        try:
            session_id = f"debug_{int(time.time())}_{len(self.sessions)}"
            
            session = DebugSession(
                id=session_id,
                start_time=datetime.now(),
                level=level,
                component=component
            )
            
            self.sessions[session_id] = session
            
            logger.info(f"Created debug session {session_id} for {component}")
            return session_id
            
        except Exception as e:
            logger.error(f"Failed to create debug session: {e}")
            return ""
    
    async def analyze_error(
        self,
        error: Exception,
        session_id: str | None = None,
        context: dict[str, Any] | None = None
    ) -> ErrorAnalysis:
        """Analyze an error with AI-powered insights"""
        try:
            error_id = f"error_{int(time.time())}_{id(error)}"
            
            # Extract error information
            error_type = type(error).__name__
            error_message = str(error)
            stack_trace = traceback.format_exc()
            
            # Classify error
            category = self._classify_error(error_type, error_message)
            
            # Determine severity
            severity = self._determine_severity(error, category)
            
            # Generate description
            description = self._generate_description(error, category)
            
            # Extract context
            error_context = self._extract_context(error, context)
            
            # Generate suggestions
            suggestions = await self._generate_suggestions(error, category, error_context)
            
            # Find related files
            related_files = self._find_related_files(stack_trace)
            
            # Find similar errors
            similar_errors = self._find_similar_errors(error_type, error_message)
            
            # Calculate fix confidence
            fix_confidence = self._calculate_fix_confidence(category, suggestions)
            
            # Estimate fix time
            estimated_fix_time = self._estimate_fix_time(category, severity)
            
            # Create analysis
            analysis = ErrorAnalysis(
                error_id=error_id,
                error_type=error_type,
                category=category,
                severity=severity,
                description=description,
                stack_trace=stack_trace,
                context=error_context,
                suggestions=suggestions,
                related_files=related_files,
                similar_errors=similar_errors,
                fix_confidence=fix_confidence,
                estimated_fix_time=estimated_fix_time
            )
            
            # Update session
            if session_id and session_id in self.sessions:
                self.sessions[session_id].errors_found += 1
            
            # Store in Redis if enabled
            if self.redis_enabled:
                await self._store_error_analysis(analysis)
            
            # Add to history
            self.debug_history.append({
                'timestamp': datetime.now(),
                'session_id': session_id,
                'error_id': error_id,
                'error_type': error_type,
                'category': category.value
            })
            
            logger.info(f"Analyzed error {error_id}: {error_type}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analysis failed: {e}")
            # Return basic analysis
            return ErrorAnalysis(
                error_id="fallback",
                error_type=type(error).__name__,
                category=ErrorCategory.UNKNOWN,
                severity="medium",
                description=str(error),
                stack_trace=traceback.format_exc(),
                context={},
                suggestions=["Check error logs for more details"],
                related_files=[],
                similar_errors=[],
                fix_confidence=0.3,
                estimated_fix_time="Unknown"
            )
    
    def _classify_error(self, error_type: str, error_message: str) -> ErrorCategory:
        """Classify error into category"""
        try:
            import re
            
            for category, patterns in self.error_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, f"{error_type} {error_message}", re.IGNORECASE):
                        return category
            
            return ErrorCategory.UNKNOWN
            
        except Exception as e:
            logger.error(f"Error classification failed: {e}")
            return ErrorCategory.UNKNOWN
    
    def _determine_severity(self, error: Exception, category: ErrorCategory) -> str:
        """Determine error severity"""
        try:
            # Base severity by category
            severity_map = {
                ErrorCategory.SYNTAX: "high",
                ErrorCategory.RUNTIME: "medium",
                ErrorCategory.MEMORY: "critical",
                ErrorCategory.NETWORK: "medium",
                ErrorCategory.DATABASE: "high",
                ErrorCategory.CONFIGURATION: "high",
                ErrorCategory.DEPENDENCY: "high",
                ErrorCategory.PERFORMANCE: "medium",
                ErrorCategory.LOGIC: "medium",
                ErrorCategory.UNKNOWN: "low"
            }
            
            base_severity = severity_map.get(category, "medium")
            
            # Adjust based on error characteristics
            error_str = str(error).lower()
            
            if any(keyword in error_str for keyword in ["critical", "fatal", "emergency"]):
                return "critical"
            elif any(keyword in error_str for keyword in ["warning", "deprecated"]):
                return "low"
            
            return base_severity
            
        except Exception as e:
            logger.error(f"Severity determination failed: {e}")
            return "medium"
    
    def _generate_description(self, error: Exception, category: ErrorCategory) -> str:
        """Generate human-readable error description"""
        try:
            error_type = type(error).__name__
            error_message = str(error)
            
            descriptions = {
                ErrorCategory.SYNTAX: f"Syntax error detected: {error_type}. This indicates invalid Python syntax that prevents code execution.",
                ErrorCategory.RUNTIME: f"Runtime error occurred: {error_type}. This happens during program execution.",
                ErrorCategory.MEMORY: f"Memory-related error: {error_type}. The system ran out of memory or encountered memory issues.",
                ErrorCategory.NETWORK: f"Network error: {error_type}. Issues with network connectivity or communication.",
                ErrorCategory.DATABASE: f"Database error: {error_type}. Problems with database operations or connections.",
                ErrorCategory.CONFIGURATION: f"Configuration error: {error_type}. Issues with system configuration or imports.",
                ErrorCategory.DEPENDENCY: f"Dependency error: {error_type}. Problems with required packages or modules.",
                ErrorCategory.PERFORMANCE: f"Performance issue: {error_type}. Code is running slower than expected.",
                ErrorCategory.LOGIC: f"Logic error: {error_type}. Code runs but produces incorrect results.",
                ErrorCategory.UNKNOWN: f"Unknown error: {error_type}. An unexpected error occurred."
            }
            
            base_description = descriptions.get(category, f"Error: {error_type}")
            
            # Add specific details
            if error_message:
                base_description += f" Details: {error_message}"
            
            return base_description
            
        except Exception as e:
            logger.error(f"Description generation failed: {e}")
            return f"Error: {type(error).__name__} - {str(error)}"
    
    def _extract_context(self, error: Exception, provided_context: dict[str, Any] | None) -> dict[str, Any]:
        """Extract context information for the error"""
        try:
            context = provided_context or {}
            
            # Add system context
            context.update({
                'timestamp': datetime.now().isoformat(),
                'python_version': sys.version,
                'platform': sys.platform,
                'memory_usage': psutil.virtual_memory().percent,
                'cpu_usage': psutil.cpu_percent()
            })
            
            # Add stack frame context
            tb = traceback.extract_tb(error.__traceback__)
            if tb:
                last_frame = tb[-1]
                context.update({
                    'file': last_frame.filename,
                    'line_number': last_frame.lineno,
                    'function': last_frame.name,
                    'code_line': last_frame.line
                })
            
            return context
            
        except Exception as e:
            logger.error(f"Context extraction failed: {e}")
            return {}
    
    async def _generate_suggestions(
        self,
        error: Exception,
        category: ErrorCategory,
        context: dict[str, Any]
    ) -> list[str]:
        """Generate AI-powered fix suggestions"""
        try:
            suggestions = []
            error_type = type(error).__name__
            error_message = str(error)
            
            # Category-specific suggestions
            if category == ErrorCategory.SYNTAX:
                suggestions.extend([
                    "Check for missing colons, brackets, or parentheses",
                    "Verify proper indentation (4 spaces recommended)",
                    "Ensure all strings are properly quoted",
                    "Check for undefined variables or functions"
                ])
            
            elif category == ErrorCategory.RUNTIME:
                suggestions.extend([
                    "Add proper error handling with try-except blocks",
                    "Validate input data before processing",
                    "Check variable types and values",
                    "Add debugging prints to trace execution flow"
                ])
            
            elif category == ErrorCategory.MEMORY:
                suggestions.extend([
                    "Optimize memory usage with generators or iterators",
                    "Release unused objects and close resources",
                    "Consider memory profiling to identify leaks",
                    "Increase available memory if possible"
                ])
            
            elif category == ErrorCategory.NETWORK:
                suggestions.extend([
                    "Check network connectivity and firewall settings",
                    "Add timeout handling for network operations",
                    "Implement retry logic for transient failures",
                    "Validate URLs and connection parameters"
                ])
            
            elif category == ErrorCategory.DATABASE:
                suggestions.extend([
                    "Check database connection and credentials",
                    "Verify SQL syntax and table names",
                    "Handle database connection pooling",
                    "Add proper transaction management"
                ])
            
            elif category == ErrorCategory.CONFIGURATION:
                suggestions.extend([
                    "Verify configuration file format and values",
                    "Check environment variables and paths",
                    "Ensure all required dependencies are installed",
                    "Validate import statements and module availability"
                ])
            
            # Error-specific suggestions
            if "KeyError" in error_type:
                suggestions.append("Check if the key exists in the dictionary before accessing")
            elif "IndexError" in error_type:
                suggestions.append("Verify list bounds before accessing elements")
            elif "AttributeError" in error_type:
                suggestions.append("Check if the object has the required attribute")
            elif "TypeError" in error_type:
                suggestions.append("Verify data types and operation compatibility")
            elif "ValueError" in error_type:
                suggestions.append("Validate input values and ranges")
            
            # Context-specific suggestions
            if 'file' in context:
                file_path = context['file']
                if file_path.endswith('.py'):
                    suggestions.append(f"Review the code in {file_path}")
            
            return suggestions[:5]  # Return top 5 suggestions
            
        except Exception as e:
            logger.error(f"Suggestion generation failed: {e}")
            return ["Check error logs and documentation for more information"]
    
    def _find_related_files(self, stack_trace: str) -> list[str]:
        """Find files related to the error"""
        try:
            files = set()
            lines = stack_trace.split('\n')
            
            for line in lines:
                if 'File "' in line:
                    # Extract file path
                    start = line.find('File "') + 6
                    end = line.find('"', start)
                    if start > 5 and end > start:
                        file_path = line[start:end]
                        if file_path.endswith('.py'):
                            files.add(file_path)
            
            return list(files)
            
        except Exception as e:
            logger.error(f"Related files detection failed: {e}")
            return []
    
    def _find_similar_errors(self, error_type: str, error_message: str) -> list[str]:
        """Find similar errors from history"""
        try:
            similar_errors = []
            
            for entry in self.debug_history[-100:]:  # Last 100 errors
                if entry['error_type'] == error_type:
                    similar_errors.append(entry['error_id'])
            
            return similar_errors[:5]  # Return top 5 similar errors
            
        except Exception as e:
            logger.error(f"Similar errors detection failed: {e}")
            return []
    
    def _calculate_fix_confidence(self, category: ErrorCategory, suggestions: list[str]) -> float:
        """Calculate confidence in fix suggestions"""
        try:
            base_confidence = {
                ErrorCategory.SYNTAX: 0.9,
                ErrorCategory.RUNTIME: 0.7,
                ErrorCategory.MEMORY: 0.6,
                ErrorCategory.NETWORK: 0.5,
                ErrorCategory.DATABASE: 0.7,
                ErrorCategory.CONFIGURATION: 0.8,
                ErrorCategory.DEPENDENCY: 0.8,
                ErrorCategory.PERFORMANCE: 0.4,
                ErrorCategory.LOGIC: 0.6,
                ErrorCategory.UNKNOWN: 0.3
            }
            
            confidence = base_confidence.get(category, 0.5)
            
            # Adjust based on suggestion quality
            if len(suggestions) >= 3:
                confidence += 0.1
            elif len(suggestions) == 0:
                confidence -= 0.2
            
            return min(1.0, max(0.0, confidence))
            
        except Exception as e:
            logger.error(f"Fix confidence calculation failed: {e}")
            return 0.5
    
    def _estimate_fix_time(self, category: ErrorCategory, severity: str) -> str:
        """Estimate time required to fix the error"""
        try:
            time_map = {
                ('critical', ErrorCategory.SYNTAX): "5-15 minutes",
                ('critical', ErrorCategory.RUNTIME): "15-30 minutes",
                ('critical', ErrorCategory.MEMORY): "30-60 minutes",
                ('critical', ErrorCategory.DATABASE): "20-40 minutes",
                ('critical', ErrorCategory.CONFIGURATION): "10-20 minutes",
                ('high', ErrorCategory.SYNTAX): "5-10 minutes",
                ('high', ErrorCategory.RUNTIME): "10-20 minutes",
                ('high', ErrorCategory.MEMORY): "20-40 minutes",
                ('high', ErrorCategory.DATABASE): "15-30 minutes",
                ('high', ErrorCategory.CONFIGURATION): "5-15 minutes",
                ('medium', ErrorCategory.SYNTAX): "2-5 minutes",
                ('medium', ErrorCategory.RUNTIME): "5-15 minutes",
                ('medium', ErrorCategory.MEMORY): "10-30 minutes",
                ('medium', ErrorCategory.DATABASE): "10-20 minutes",
                ('medium', ErrorCategory.CONFIGURATION): "5-10 minutes",
                ('low', ErrorCategory.SYNTAX): "1-3 minutes",
                ('low', ErrorCategory.RUNTIME): "3-10 minutes",
                ('low', ErrorCategory.MEMORY): "5-20 minutes",
                ('low', ErrorCategory.DATABASE): "5-15 minutes",
                ('low', ErrorCategory.CONFIGURATION): "2-5 minutes"
            }
            
            return time_map.get((severity, category), "5-15 minutes")
            
        except Exception as e:
            logger.error(f"Fix time estimation failed: {e}")
            return "Unknown"
    
    async def profile_function(
        self,
        func: Callable,
        *args,
        session_id: str | None = None,
        **kwargs
    ) -> tuple[Any, PerformanceProfile]:
        """Profile function performance"""
        try:
            # Start monitoring
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss
            start_cpu = psutil.cpu_percent()
            
            # Execute function
            result = func(*args, **kwargs)
            
            # End monitoring
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            end_cpu = psutil.cpu_percent()
            
            # Calculate metrics
            execution_time = end_time - start_time
            memory_usage = end_memory - start_memory
            cpu_usage = end_cpu - start_cpu
            
            # Get function name
            func_name = getattr(func, '__name__', 'anonymous_function')
            
            # Find bottlenecks
            bottlenecks = self._find_bottlenecks(execution_time, memory_usage, cpu_usage)
            
            # Generate optimization suggestions
            optimization_suggestions = self._generate_optimization_suggestions(
                execution_time, memory_usage, bottlenecks
            )
            
            # Create profile
            profile = PerformanceProfile(
                function_name=func_name,
                execution_time=execution_time,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                call_count=1,
                average_time=execution_time,
                max_time=execution_time,
                min_time=execution_time,
                bottlenecks=bottlenecks,
                optimization_suggestions=optimization_suggestions,
                timestamp=datetime.now()
            )
            
            # Update session
            if session_id and session_id in self.sessions:
                self.sessions[session_id].metadata['performance_profiles'] = \
                    self.sessions[session_id].metadata.get('performance_profiles', []) + [profile]
            
            # Store profile
            if func_name not in self.performance_profiles:
                self.performance_profiles[func_name] = []
            
            self.performance_profiles[func_name].append(profile)
            
            # Keep only last 100 profiles per function
            if len(self.performance_profiles[func_name]) > 100:
                self.performance_profiles[func_name] = self.performance_profiles[func_name][-100:]
            
            logger.info(f"Profiled function {func_name}: {execution_time:.3f}s")
            return result, profile
            
        except Exception as e:
            logger.error(f"Function profiling failed: {e}")
            return None, PerformanceProfile(
                function_name="error",
                execution_time=0.0,
                memory_usage=0.0,
                cpu_usage=0.0,
                call_count=0,
                average_time=0.0,
                max_time=0.0,
                min_time=0.0,
                bottlenecks=["Profiling error"],
                optimization_suggestions=[],
                timestamp=datetime.now()
            )
    
    def _find_bottlenecks(self, execution_time: float, memory_usage: float, cpu_usage: float) -> list[str]:
        """Find performance bottlenecks"""
        try:
            bottlenecks = []
            
            if execution_time > self.performance_thresholds['slow_function']:
                bottlenecks.append("Slow execution time")
            
            if memory_usage > self.performance_thresholds['memory_intensive']:
                bottlenecks.append("High memory usage")
            
            if cpu_usage > self.performance_thresholds['high_cpu']:
                bottlenecks.append("High CPU usage")
            
            return bottlenecks
            
        except Exception as e:
            logger.error(f"Bottleneck detection failed: {e}")
            return []
    
    def _generate_optimization_suggestions(
        self,
        execution_time: float,
        memory_usage: float,
        bottlenecks: list[str]
    ) -> list[str]:
        """Generate optimization suggestions"""
        try:
            suggestions = []
            
            if "Slow execution time" in bottlenecks:
                suggestions.extend([
                    "Consider using more efficient algorithms",
                    "Add caching for expensive operations",
                    "Use generators for large datasets",
                    "Optimize database queries"
                ])
            
            if "High memory usage" in bottlenecks:
                suggestions.extend([
                    "Use memory-efficient data structures",
                    "Implement object pooling",
                    "Release unused resources promptly",
                    "Consider streaming for large data"
                ])
            
            if "High CPU usage" in bottlenecks:
                suggestions.extend([
                    "Optimize computational complexity",
                    "Use built-in functions when possible",
                    "Consider parallel processing",
                    "Profile and optimize hot spots"
                ])
            
            return suggestions[:5]  # Return top 5 suggestions
            
        except Exception as e:
            logger.error(f"Optimization suggestions generation failed: {e}")
            return []
    
    async def get_session_summary(self, session_id: str) -> dict[str, Any]:
        """Get debug session summary"""
        try:
            if session_id not in self.sessions:
                return {"error": "Session not found"}
            
            session = self.sessions[session_id]
            
            summary = {
                'session_id': session_id,
                'start_time': session.start_time.isoformat(),
                'end_time': session.end_time.isoformat() if session.end_time else None,
                'level': session.level.value,
                'component': session.component,
                'status': session.status,
                'errors_found': session.errors_found,
                'issues_resolved': session.issues_resolved,
                'duration': (session.end_time - session.start_time).total_seconds() if session.end_time else None,
                'metadata': session.metadata
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Session summary generation failed: {e}")
            return {"error": str(e)}
    
    async def get_performance_summary(self) -> dict[str, Any]:
        """Get performance summary"""
        try:
            summary = {
                'total_functions_profiled': len(self.performance_profiles),
                'functions': {}
            }
            
            for func_name, profiles in self.performance_profiles.items():
                if profiles:
                    execution_times = [p.execution_time for p in profiles]
                    memory_usages = [p.memory_usage for p in profiles]
                    
                    summary['functions'][func_name] = {
                        'call_count': len(profiles),
                        'avg_execution_time': sum(execution_times) / len(execution_times),
                        'max_execution_time': max(execution_times),
                        'min_execution_time': min(execution_times),
                        'avg_memory_usage': sum(memory_usages) / len(memory_usages),
                        'max_memory_usage': max(memory_usages),
                        'last_profiled': profiles[-1].timestamp.isoformat()
                    }
            
            return summary
            
        except Exception as e:
            logger.error(f"Performance summary generation failed: {e}")
            return {"error": str(e)}
    
    async def _store_error_analysis(self, analysis: ErrorAnalysis):
        """Store error analysis in Redis"""
        try:
            key = f"debug_error:{analysis.error_id}"
            value = asdict(analysis)
            
            await self.redis_client.setex(
                key,
                24 * 3600,  # 24 hours
                json.dumps(value, default=str)
            )
            
        except Exception as e:
            logger.error(f"Redis error analysis storage error: {e}")
    
    def end_session(self, session_id: str):
        """End a debug session"""
        try:
            if session_id in self.sessions:
                self.sessions[session_id].end_time = datetime.now()
                self.sessions[session_id].status = "completed"
                
                logger.info(f"Ended debug session {session_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to end session {session_id}: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown the debugger"""
        logger.info("Advanced debugger shutdown complete")

# Global debugger instance
advanced_debugger = AdvancedDebugger()
