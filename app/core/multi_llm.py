"""
Multi-LLM Support for Asmblr
Advanced LLM orchestration with intelligent provider management and cost optimization
"""

import asyncio
from typing import Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from loguru import logger
import redis.asyncio as redis

class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"
    REPLICATE = "replicate"
    LOCALAI = "localai"
    OLLAMA = "ollama"
    TOGETHERAI = "togetherai"

class LLMModel(Enum):
    """LLM model types"""
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    CLAUDE_3 = "claude-3-sonnet"
    LLAMA_2_7B = "llama2-7b"
    MISTRAL_7B = "mistral-7b"
    GEMMA_7B = "gemma-7b"
    QWEN_2_5 = "qwen-2.5"
    CODELLAMA_34B = "codellama-34b"
    DEEPSEEK_CODER = "deepseek-coder"
    MAGIC_STABLE = "magic-stable"

class LLMCapability(Enum):
    """LLM capabilities"""
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    CODE_ANALYSIS = "code_analysis"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    REASONING = "reasoning"
    TOOL_USE = "tool_use"
    FUNCTION_CALLING = "function_calling"
    STREAMING = "streaming"

@dataclass
class LLMConfig:
    """LLM configuration"""
    provider: LLMProvider
    model: LLMModel
    api_key: str | None = None
    api_base_url: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: float = 30.0
    retry_attempts: int = 3
    rate_limit: int = 60
    context_window: int = 4096
    streaming: bool = False
    capabilities: list[LLMCapability] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = [
                LLMCapability.TEXT_GENERATION,
                LLMCapability.CODE_GENERATION,
                LLMCapability.REASONING
            ]

@dataclass
class LLMRequest:
    """LLM request"""
    id: str
    provider: LLMProvider
    model: LLMModel
    prompt: str
    context: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    timeout: float | None = None
    capabilities: list[LLMCapability] = None
    metadata: dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.capabilities is None:
            self.capabilities = []

@dataclass
class LLMResponse:
    """LLM response"""
    request_id: str
    provider: LLMProvider
    model: LLM
    content: str
    usage: dict[str, Any]
    metadata: dict[str, Any] = None
    timestamp: datetime
    tokens_used: int
    response_time: float
    cost: float
        
    def __post_init__(self):
        if self.usage is None:
            self.usage = {}
        if self.metadata is None:
            self.metadata = {}

class LLMProviderAdapter:
    """Base adapter for LLM providers"""
    
    def __init__(self, provider: LLMProvider, config: LLMConfig):
        self.provider = provider
        self.config = config
        self.client = None
        self.session = None
        self.initialized = False
        
        # Performance tracking
        self.request_count = 0
        total_tokens_used = 0
        total_cost = 0.0
        self.error_count = 0
        self.performance_history = []
        
    async def initialize(self):
        """Initialize LLM provider client"""
        raise NotImplementedError
    
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        """Generate text using LLM"""
        raise NotImplementedError
    
    async def generate_code(self, request: LLMRequest) -> LLMResponse:
        """Generate code using LLM"""
        raise NotImplementedError
    
    async def analyze_code(self, request: LLMRequest) -> LLMResponse:
        """Analyze code using LLM"""
        raise NotImplementedError
    
    async def translate(self, request: LLMRequest) -> LLMResponse:
        """Translate text using LLM"""
        raise NotImplementedError
    
    async def summarize(self, request: LLMRequest) -> LLMResponse:
        """Summarize content using LLM"""
        raise NotImplementedError
    
    def get_cost_estimate(self, request: LLMRequest) -> float:
        """Get cost estimate for request"""
        raise NotImplementedError
    
    async def get_performance_metrics(self) -> dict[str, Any]:
        """Get provider performance metrics"""
        try:
            return {
                'provider': self.provider.value,
                'request_count': self.request_count,
                'total_tokens_used': self.total_tokens_used,
                'total_cost': self.total_cost,
                'error_count': self.error_count,
                'avg_response_time': sum(self.performance_history) / len(self.performance_history) if self.performance_history else 0.0,
                'success_rate': ((self.request_count - self.error_count) / max(self.request_count, 1)) * 100,
                'last_updated': datetime.now()
            }
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {}
    
    async def shutdown(self):
        """Shutdown LLM provider"""
        if self.client:
            # Provider-specific shutdown logic
            pass
        logger.info(f"{self.provider.value} adapter shutdown complete")

class OpenAIAdapter(LLMProviderAdapter):
    """OpenAI provider adapter"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(LLMProvider.OPENAI, config)
        self.client = None
        self.session = None
    
    async def initialize(self):
        """Initialize OpenAI client"""
        try:
            import openai
            self.client = openai.AsyncOpenAI(
                api_key=self.config.api_key,
                organization=self.config.api_base_url or "https://api.openai.com/v1",
                timeout=self.config.timeout
            )
            self.session = await self.client.chat.completions.create(
                model=self.config.model.value,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            self.initialized = True
            logger.info("OpenAI adapter initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI adapter: {e}")
            raise
    
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        """Generate text using OpenAI"""
        try:
            if not self.initialized:
                raise RuntimeError("OpenAI adapter not initialized")
            
            # Prepare messages
            messages = []
            if request.context:
                messages.append({"role": "system", "content": request.context})
            
            messages.append({"role": "user", "content": request.prompt})
            
            # Generate response
            response = await self.session.chat.completions.create(
                model=self.config.model.value,
                messages=messages,
                temperature=request.temperature or self.config.temperature,
                max_tokens=request.max_tokens or self.config.max_tokens,
                timeout=request.timeout or self.config.timeout
            )
            
            # Calculate usage
            tokens_used = response.usage.total_tokens
            cost = self._calculate_cost(tokens_used)
            
            # Update metrics
            self.request_count += 1
            self.total_tokens_used += tokens_used
            self.total_cost += cost
            self.performance_history.append(tokens_used)
            
            # Create response
            llm_response = LLMResponse(
                request_id=request.id,
                provider=self.provider,
                model=self.config.model,
                content=response.choices[0].message.content,
                usage={
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                metadata={
                    'finish_reason': response.finish_reason,
                    'model': response.model,
                    'created_at': response.created
                },
                timestamp=datetime.now(),
                tokens_used=tokens_used,
                cost=cost
            )
            
            return llm_response
            
        except Exception as e:
            logger.error(f"OpenAI text generation failed: {e}")
            return LLMResponse(
                request_id=request.id,
                provider=self.provider,
                model=self.config.model,
                content="",
                usage={},
                error=str(e),
                timestamp=datetime.now(),
                tokens_used=0,
                cost=0.0
            )
    
    async def generate_code(self, request: LLMRequest) -> LLMResponse:
        """Generate code using OpenAI"""
        try:
            if not self.initialized:
                raise RuntimeError("OpenAI adapter not initialized")
            
            # Prepare messages
            messages = []
            if request.context:
                messages.append({"role": "system", "content": request.context})
            
            messages.append({"role": "user", "content": request.prompt})
            
            # Add code generation specific prompt
            code_prompt = f"""
Generate Python code for: {request.prompt}

Requirements:
- Follow Python best practices
- Include type hints
- Add docstrings
- Handle errors appropriately
- Make it production-ready
"""
            
            messages.append({"role": "system", "content": code_prompt})
            
            # Generate response
            response = await self.session.chat.completions.create(
                model=self.config.model.value,
                messages=messages,
                temperature=request.temperature or self.config.temperature,
                max_tokens=request.max_tokens or self.config.max_tokens,
                timeout=request.timeout or self.config.timeout
            )
            
            # Calculate usage
            tokens_used = response.usage.total_tokens
            cost = self._calculate_cost(tokens_used)
            
            # Update metrics
            self.request_count += 1
            self.total_tokens_used += tokens_used
            self.total_cost += cost
            self.performance_history.append(tokens_used)
            
            # Create response
            llm_response = LLMResponse(
                request_id=request.id,
                provider=self.provider,
                model=self.config.model,
                content=response.choices[0].message.content,
                usage={
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                metadata={
                    'finish_reason': response.finish_reason,
                    'model': response.model,
                    'created_at': response.created
                },
                timestamp=datetime.now(),
                tokens_used=tokens_used,
                cost=cost
            )
            
            return llm_response
            
        except Exception as e:
            logger.error(f"OpenAI code generation failed: {e}")
            return LLMResponse(
                request_id=request.id,
                provider=self.provider,
                model=self.config.model,
                content="",
                usage={},
                error=str(e),
                timestamp=datetime.now(),
                tokens_used=0,
                cost=0.0
            )
    
    async def _calculate_cost(self, tokens_used: int) -> float:
        """Calculate cost based on tokens used"""
        try:
            # OpenAI pricing (simplified)
            cost_per_token = 0.000002  # $0.002 per token
            return tokens_used * cost_per_token
            
        except Exception as e:
            logger.error(f"Cost calculation failed: {e}")
            return 0.0
    
    async def shutdown(self):
        """Shutdown OpenAI client"""
        if self.session:
            await self.session.close()
        logger.info("OpenAI adapter shutdown complete")

class AnthropicAdapter(LLMProviderAdapter):
    """Anthropic provider adapter"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(LLMProvider.ANTHROPIC, config)
        self.client = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize Anthropic client"""
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(
                api_key=self.config.api_key,
                timeout=self.config.timeout
            )
            self.initialized = True
            logger.info("Anthropic adapter initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic adapter: {e}")
            raise
    
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        """Generate text using Anthropic"""
        try:
            if not self.initialized:
                raise RuntimeError("Anthropic adapter not initialized")
            
            # Create message
            message = f"{request.prompt}"
            
            # Generate response
            response = await self.client.messages.create(
                model=self.config.model.value,
                messages=[{"role": "user", "content": message}],
                max_tokens=request.max_tokens or self.config.max_tokens,
                temperature=request.temperature or self.config.temperature
            )
            
            # Calculate usage
            tokens_used = response.usage.input_tokens + response.output_tokens
            cost = self._calculate_cost(tokens_used)
            
            # Update metrics
            self.request_count += 1
            self.total_tokens_used += tokens_used
            self.total_cost += cost
            self.performance_history.append(tokens_used)
            
            # Create response
            llm_response = LLMResponse(
                request_id=request.id,
                provider=self.provider,
                model=self.config.model,
                content=response.content[0].text,
                usage={
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.output_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                metadata={
                    'model': response.model,
                    'created_at': response.created
                },
                timestamp=datetime.now(),
                tokens_used=tokens_used,
                cost=cost
            )
            
            return llm_response
            
        except Exception as e:
            logger.error(f"Anthropic text generation failed: {e}")
            return LLMResponse(
                request_id=request.id,
                provider=self.provider,
                model=self.config.model,
                content="",
                usage={},
                error=str(e),
                timestamp=datetime.now(),
                tokens_used=0,
                cost=0.0
            )
    
    async def _calculate_cost(self, tokens_used: int) -> float:
        """Calculate cost based on tokens used"""
        try:
            # Anthropic pricing (simplified)
            cost_per_token = 0.0003  # $0.0003 per token
            return tokens_used * cost_per_token
            
        except Exception as e:
            logger.error(f"Cost calculation failed: {e}")
            return 0.0
    
    async def shutdown(self):
        """Shutdown Anthropic client"""
        if self.client:
            await self.client.close()
        logger.info("Anthropic adapter shutdown complete")

class CohereAdapter(LLMProviderAdapter):
    """Cohere provider adapter"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(LLMProvider.COHERE, config)
        self.client = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize Cohere client"""
        try:
            import cohere
            self.client = cohere.AsyncCohere(
                api_key=self.config.api_key,
                model=self.config.model.value,
                timeout=self.config.timeout
            )
            self.initialized = True
            logger.info("Cohere adapter initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Cohere adapter: {e}")
            raise
    
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        """Generate text using Cohere"""
        try:
            if not self.initialized:
                raise RuntimeError("Cohere adapter not initialized")
            
            # Create message
            message = f"{request.prompt}"
            
            # Generate response
            response = await self.client.generate(
                model=self.config.model.value,
                prompt=message,
                max_tokens=request.max_tokens or self.config.max_tokens,
                temperature=request.temperature or self.config.temperature
            )
            
            # Calculate usage
            tokens_used = response.usage.input_tokens + response.output_tokens
            cost = self._calculate_cost(tokens_used)
            
            # Update metrics
            self.request_count += 1
            self.total_tokens_used += tokens_used
            self.total_cost += cost
            self.performance_history.append(tokens_used)
            
            # Create response
            llm_response = LLMResponse(
                request_id=request.id,
                provider=self.provider,
                model=self.config.model,
                content=response.content,
                usage={
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                metadata={
                    'model': response.model,
                    'created_at': response.created
                },
                timestamp=datetime.now(),
                tokens_used=tokens_used,
                cost=cost
            )
            
            return llm_response
            
        except Exception as e:
            logger.error(f"Cohere text generation failed: {e}")
            return LLMResponse(
                request_id=request.id,
                provider=self.provider,
                model=self.config.model,
                content="",
                usage={},
                error=str(e),
                timestamp=datetime.now(),
                tokens_used=0,
                cost=0.0
            )
    
    async def _calculate_cost(self, tokens_used: int) -> float:
        """Calculate cost based on tokens used"""
        try:
            # Cohere pricing (simplified)
            cost_per_token = 0.0004  # $0.0004 per token
            return tokens_used * cost_per_token
            
        except Exception as e:
            logger.error(f"Cost calculation failed: {e}")
            return 0.0
    
    async def shutdown(self):
        """Shutdown Cohere client"""
        if self.client:
            await self.client.close()
        logger.info("Cohere adapter shutdown complete")

class HuggingFaceAdapter(LLMProviderAdapter):
    """HuggingFace provider adapter"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(LLMProvider.HUGGINGFACE, config)
        self.client = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize HuggingFace client"""
        try:
            import hugface
            self.client = hugface.AsyncHuggingFace(
                api_key=self.config.api_key,
                model=self.config.model.value,
                timeout=self.config.timeout
            )
            self.initialized = True
            logger.info("HuggingFace adapter initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize HuggingFace adapter: {e}")
            raise
    
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        """Generate text using HuggingFace"""
        try:
            if not self.initialized:
                raise RuntimeError("HuggingFace adapter not initialized")
            
            # Create message
            message = f"{request.prompt}"
            
            # Generate response
            response = await self.client.generate(
                model=self.config.model.value,
                prompt=message,
                max_tokens=request.max_tokens or self.config.max_tokens,
                temperature=request.temperature or self.config.temperature
            )
            
            # Calculate usage
            tokens_used = response.usage.total_tokens
            cost = self._calculate_cost(tokens_used)
            
            # Update metrics
            self.request_count += 1
            self.total_tokens_used += tokens_used
            self.total_cost += cost
            self.performance_history.append(tokens_used)
            
            # Create response
            llm_response = LLMResponse(
                request_id=request.id,
                provider=self.provider,
                model=self.config.model,
                content=response.content,
                usage={
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens,
                    'total_tokens': response.usage.total_tokens
                },
                metadata={
                    'model': response.model,
                    'created_at': response.created
                },
                timestamp=datetime.now(),
                tokens_used=tokens_used,
                cost=cost
            )
            
            return llm_response
            
        except Exception as e:
            logger.error(f"HuggingFace text generation failed: {e}")
            return LLM_response(
                request_id=request.id,
                provider=self.provider,
                model=self.config.model,
                content="",
                usage={},
                error=str(e),
                timestamp=datetime.now(),
                tokens_used=0,
                cost=0.0
            )
    
    async def _calculate_cost(self, tokens_used: int) -> float:
        """Calculate cost based on tokens used"""
        try:
            # HuggingFace pricing (simplified)
            cost_per_token = 0.00013  # $0.00013 per token
            return tokens_used * cost_per_token
            
        except Exception as e:
            logger.error(f"Cost calculation failed: {e}")
            return 0.0
    
    async def shutdown(self):
        """Shutdown HuggingFace client"""
        if self.client:
            await self.client.close()
        logger.info("HuggingFace adapter shutdown complete")

class LocalAIAdapter(LLMProviderAdapter):
    """Local AI provider adapter"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(LLMProvider.LOCALAI, config)
        self.model_path = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize local AI client"""
        try:
            # For local AI, we'll use a simple mock implementation
            self.initialized = True
            logger.info("Local AI adapter initialized (mock)")
            
        except Exception as e:
            logger.error(f"Failed to initialize local AI adapter: {e}")
            raise
    
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        """Generate text using local AI"""
        try:
            if not self.initialized:
                raise RuntimeError("Local AI adapter not initialized")
            
            # Simple mock implementation
            response_text = f"Generated text for: {request.prompt}"
            
            # Calculate usage (mock)
            tokens_used = len(response_text.split()) * 4  # Rough estimation
            cost = self._calculate_cost(tokens_used)
            
            # Update metrics
            self.request_count += 1
            self.total_tokens_used += tokens_used
            self.total_cost += cost
            self.performance_history.append(tokens_used)
            
            # Create response
            llm_response = LLMResponse(
                request_id=request.id,
                provider=self.provider,
                model=self.config.model,
                content=response_text,
                usage={
                    'input_tokens': tokens_used // 4,  # Rough estimation
                    'output_tokens': tokens_used // 4,
                    'total_tokens': tokens_used
                },
                metadata={
                    'model': self.config.model,
                    'created_at': datetime.now()
                },
                timestamp=datetime.now(),
                tokens_used=tokens_used,
                cost=cost
            )
            
            return llm_response
            
        except Exception as e:
            logger.error(f"Local AI text generation failed: {e}")
            return LLMResponse(
                request_id=request.id,
                provider=self.provider,
                model=self.config.model,
                content="",
                usage={},
                error=str(e),
                timestamp=datetime.now(),
                tokens_used=0,
                cost=0.0
            )
    
    def _calculate_cost(self, tokens_used: int) -> float:
        """Calculate cost for local AI (free)"""
        return 0.0  # Local AI is free
    
    async def shutdown(self):
        """Shutdown local AI adapter"""
        self.initialized = False
        logger.info("Local AI adapter shutdown complete")

class MultiLLMManager:
    """Multi-LLM orchestration system"""
    
    def __init__(self):
        self.providers = {}
        self.default_provider = LLMProvider.OPENAI
        self.auto_failover = True
        self.cost_optimization = True
        self.performance_monitoring = True
        
        # Redis for distributed coordination
        self.redis_client = None
        self.redis_enabled = False
        
        # Performance tracking
        self.request_history = []
        self.cost_history = []
        self.performance_metrics = {}
        
        # Load balancing
        self.load_balancing_enabled = True
        self.request_queue = asyncio.Queue()
        self.active_requests = {}
        
    async def initialize(self):
        """Initialize multi-LLM manager"""
        try:
            # Initialize Redis connection
            try:
                self.redis_client = redis.from_url(
                    "redis://localhost:6379/13",
                    max_connections=20
                )
                await self.redis_client.ping()
                self.redis_enabled = True
                logger.info("Redis connection established for multi-LLM")
            except Exception as e:
                logger.warning(f"Redis not available, using local multi-LLM: {e}")
            
            # Initialize providers
            await self._initialize_providers()
            
            # Start background tasks
            await self._start_background_tasks()
            
            logger.info("Multi-LLM manager initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize multi-LLM manager: {e}")
            raise
    
    async def _initialize_providers(self):
        """Initialize LLM providers"""
        try:
            # Initialize configured providers
            provider_configs = {
                CloudProvider.AWS: self.config.get('aws', {}),
                CloudProvider.AZURE: self.config.get('azure', {}),
                CloudProvider.GCP: self.config.get('gcp', {}),
                CloudProvider.ANTHROPIC: self.config.get('anthropic', {}),
                CloudProvider.HUGGINGFACE: self.config.get('huggingface', {}),
                CloudProvider.REPLICATE: self.config.get('replicate', {}),
                CloudProvider.LOCALAI: self.config.get('localai', {})
            }
            
            for provider, config in provider_configs.items():
                if config:
                    adapter = self._create_adapter(provider, config)
                    await adapter.initialize()
                    self.providers[provider] = adapter
            
            logger.info(f"Initialized {len(self.providers)} LLM providers")
            
        except Exception as e:
            logger.error(f"Failed to initialize providers: {e}")
            raise
    
    def _create_adapter(self, provider: CloudProvider, config: LLMConfig) -> LLMProviderAdapter:
        """Create adapter for provider"""
        if provider == CloudProvider.AWS:
            return AWSAdapter(config)
        elif provider == CloudProvider.AZURE:
            return AzureAdapter(config)
        elif provider == CloudProvider.GCP:
            return GCPAdapter(config)
        elif provider == CloudProvider.ANTHROPIC:
            return AnthropicAdapter(config)
        elif provider == CloudProvider.HUGGINGFACE:
            return HuggingFaceAdapter(config)
        elif provider == CloudProvider.REPLICATE:
            return ReplicateAdapter(config)
        elif provider == CloudProvider.LOCALAI:
            return LocalAIAdapter(config)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        """Generate text using optimal LLM provider"""
        try:
            # Select optimal provider
            provider = await self._select_optimal_provider(request)
            
            # Generate using selected provider
            adapter = self.providers[provider]
            result = await adapter.generate_text(request)
            
            # Record operation
            self.request_history.append({
                'request_id': request.id,
                'provider': provider.value,
                'model': request.model,
                'tokens_used': result.tokens_used,
                'cost': result.cost,
                'timestamp': datetime.now(),
                'success': True
            })
            
            logger.info(f"Generated text using {provider.value} model: {result.tokens_used} tokens, cost: ${result.cost:.4f}")
            return result
            
        except Exception as e:
            logger.error(f"Multi-LLM text generation failed: {e}")
            # Fallback to default provider
            if self.default_provider in self.providers:
                adapter = self.providers[self.default_provider]
                return await adapter.generate_text(request)
            else:
                raise Exception("No available LLM providers")
    
    async def generate_code(self, request: LLMRequest) -> LLMResponse:
        """Generate code using optimal LLM provider"""
        try:
            # Select optimal provider for code generation
            code_providers = [
                CloudProvider.OPENAI,
                CloudProvider.ANTHROPIC,
                CloudProvider.HUGGINGFACE,
                CloudProvider.COHERE,
                CloudProvider.REPLICATE
            ]
            
            # Filter providers that support code generation
            code_providers = [
                provider for provider in code_providers
                if LLMCapability.CODE_GENERATION in self.providers[provider].config.capabilities
            ]
            
            if not code_providers:
                code_providers = [self.default_provider]
            
            # Select optimal provider for code generation
            provider = await self._select_optimal_provider_for_code(request, code_providers)
            
            # Generate using selected provider
            adapter = self.providers[provider]
            result = await adapter.generate_code(request)
            
            # Record operation
            self.request_history.append({
                'request_id': request.id,
                'provider': provider.value,
                'model': request.model,
                'tokens_used': result.tokens_used,
                'cost': result.cost,
                'timestamp': datetime.now(),
                'success': True
            })
            
            logger.info(f"Generated code using {provider.value} model: {result.tokens_used} tokens, cost: ${result.cost:.4f}")
            return result
            
        except Exception as e:
            logger.error(f"Multi-LLM code generation failed: {e}")
            # Fallback to default provider
            if self.default_provider in self.providers:
                adapter = self.providers[self.default_provider]
                return await adapter.generate_code(request)
            else:
                raise Exception("No available LLM providers for code generation")
    
    async def _select_optimal_provider(self, request: LLMRequest, preferred_providers: list[CloudProvider] | None = None) -> CloudProvider:
        """Select optimal provider for request"""
        try:
            candidates = preferred_providers or list(self.providers.keys())
            
            provider_scores = []
            for provider in candidates:
                if provider in self.providers:
                    adapter = self.providers[provider]
                    
                    # Check if provider supports requested capabilities
                    capability_match = any(
                        cap in request.capabilities
                        for cap in (request.capabilities or [])
                    )
                    
                    if not capability_match:
                        continue
                    
                    # Get cost estimate
                    cost = await adapter.get_cost_estimate(request)
                    
                    # Calculate score
                    score = self._calculate_provider_score(provider, request, cost)
                    provider_scores.append((provider, score))
            
            # Sort by score (higher is better)
            provider_scores.sort(key=lambda x: x[1], reverse=True)
            
            return provider_scores[0][0]
            
        except Exception as e:
            logger.error(f"Provider selection failed: {e}")
            return self.default_provider
    
    def _select_optimal_provider_for_code(self, request: LLMRequest, code_providers: list[CloudProvider]) -> CloudProvider:
        """Select optimal provider for code generation"""
        try:
            # Prioritize providers known for code generation
            code_provider_priority = {
                CloudProvider.OPENAI: 0.95,
                CloudProvider.ANTHROPIC: 0.85,
                CloudProvider.HUGGINGFACE: 0.80,
                CloudProvider.COHERE: 0.75,
                CloudProvider.REPLICATE: 0.70,
                CloudProvider.GCP: 0.65
            }
            
            provider_scores = []
            for provider in code_providers:
                if provider in code_provider_priority:
                    score = code_provider_priority[provider]
                    provider_scores.append((provider, score))
            
            return max(provider_scores, key=lambda x: x[1])[0]
            
        except Exception as e:
            logger.error(f"Code provider selection failed: {e}")
            return CloudProvider.OPENAI
    
    def _calculate_provider_score(self, provider: CloudProvider, request: LLMRequest, cost: CloudCost) -> float:
        """Calculate provider score for request"""
        try:
            score = 0.0
            
            # Capability match
            capability_match = any(
                cap in (request.capabilities or [])
                for cap in (self.providers[provider].config.capabilities or [])
            )
            if capability_match:
                score += 0.4
            
            # Cost factor (lower is better)
            max_cost = 1.0  # Would be calculated from actual costs
            cost_factor = 1.0 - (cost / max(max_cost, 0.01))
            score += cost_factor * 0.3
            
            # Performance factor
            performance_scores = {
                CloudProvider.OPENAI: 0.90,
                CloudProvider.AZURE: 0.85,
                CloudProvider.GCP: 0.80,
                CloudProvider.ANTHROPIC: 0.75,
                CloudProvider.HUGGINGFACE: 0.70,
                CloudProvider.COHERE: 0.65,
                CloudProvider.REPLICATE: 0.60,
                CloudProvider.GCP: 0.55
            }
            score += performance_scores.get(provider, 0.5) * 0.3
            
            return score
            
        except Exception as e:
            logger.error(f"Provider score calculation failed: {e}")
            return 0.5
    
    def _calculate_provider_score(self, provider: CloudProvider, request: LLMRequest, cost: CloudCost) -> float:
        """Calculate provider score for general request"""
        try:
            score = 0.0
            
            # Provider reliability
            reliability_scores = {
                CloudProvider.OPENAI: 0.95,
                CloudProvider.AZURE: 0.90,
                CloudProvider.GCP: 0.85,
                CloudProvider.ANTHROPIC: 0.80,
                CloudProvider.HUGGINGFACE: 0.75,
                CloudProvider.COHERE: 0.70,
                CloudProvider.REPLICATE: 0.65,
                CloudProvider.LINODE: 0.60,
                CloudProvider.GCP: 0.55,
                CloudProvider.DIGITAL_OCEAN: 0.50,
                CloudProvider.VULTR: 0.45,
                CloudProvider.LINODE: 0.40,
                CloudProvider.ORACLE: 0.85,
                CloudProvider.IBM: 0.80,
                CloudProvider.HUGGINGFACE: 0.75
            }
            
            score += reliability_scores.get(provider, 0.5) * 0.4
            
            # Cost factor (lower is better)
            max_cost = 1.0
            cost_factor = 1.0 - (cost / max(max_cost, 0.01))
            score += cost_factor * 0.3
            
            return score
            
        except Exception as e:
            logger.error(f"Provider score calculation failed: {e}")
            return 0.5
    
    async def get_llm_metrics(self) -> dict[str, Any]:
        """Get LLM metrics"""
        try:
            all_metrics = {}
            
            for provider, adapter in self.providers.items():
                metrics = await adapter.get_performance_metrics()
                all_metrics[provider.value] = metrics
            
            # Calculate global metrics
            total_requests = sum(m['request_count'] for m in all_metrics.values())
            total_tokens = sum(m['total_tokens_used'] for m in all_metrics.values())
            total_cost = sum(m['total_cost'] for m in all_metrics.values())
            avg_response_time = sum(m['avg_response_time'] for m in all_metrics.values() if m['avg_response_time'] > 0)
            
            all_metrics['total_requests'] = total_requests
            all_metrics['total_tokens'] = total_tokens
            all_metrics['total_cost'] = total_cost
            all_metrics['avg_response_time'] = avg_response_time
            all_metrics['success_rate'] = sum(m['success_rate'] for m in all_metrics.values()) / len(all_metrics)
            
            return all_metrics
            
        except Exception as e:
            logger.error(f"Failed to get LLM metrics: {e}")
            return {}
    
    async def get_cost_optimization_suggestions(self) -> list[str]:
        """Get cost optimization suggestions"""
        try:
            suggestions = []
            
            # Analyze current costs
            total_monthly_cost = sum(cost.monthly_cost for cost in self.costs.values())
            
            if total_monthly_cost > 1000:
                suggestions.append("Consider using spot instances for non-critical workloads")
            
            if total_monthly_cost > 500:
                suggestions.append("Implement auto-scaling to reduce costs during low usage")
            
            # Check for expensive providers
            expensive_providers = [
                provider for provider, cost in self.costs.items() if cost.hourly_cost > 0.5
            ]
            
            if expensive_providers:
                suggestions.append(f"Review expensive providers: {', '.join([p.value for p in expensive_providers])}")
            
            # Check for underutilized resources
            for resource_id, resource_info in self.resources.items():
                metrics = await self.get_metrics(resource_id)
                if metrics and metrics['cpu_utilization'] < 0.2:
                    suggestions.append(f"Consider downscaling resource {resource_id}")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to generate cost optimization suggestions: {e}")
            return []
    
    async def get_disaster_recovery_plan(self) -> dict[str, Any]:
        """Get disaster recovery plan"""
        try:
            plan = {
                'primary_provider': self.default_provider.value,
                'backup_providers': [p.value for p in self.providers.keys() if p != self.default_provider],
                'recovery_steps': [
                    "Switch to backup provider",
                    "Restore from backups",
                    "Update DNS records",
                    "Update configuration",
                    "Verify all services"
                ],
                'rto': 15,  # 15 minutes
                'data_backup': True,
                'infrastructure_backup': True,
                'failover_providers': [p.value for p in self.providers.keys() if p != self.default_provider]
            }
            
            return plan
            
        except Exception as e:
            logger.error(f"Failed to create disaster recovery plan: {e}")
            return {}
    
    async def get_multi_llm_summary(self) -> dict[str, Any]:
        """Get multi-LLM summary"""
        try:
            summary = {
                'total_providers': len(self.providers),
                'default_provider': self.default_provider.value,
                'backup_providers': [p.value for p in self.providers.keys() if p != self.default_provider],
                'total_requests': sum(m['request_count'] for m in self.get_llm_metrics().values()),
                'total_tokens': sum(m['total_tokens'] for m in self.get_llm_metrics().values()),
                'total_cost': sum(m['total_cost'] for m in self.get_llm_metrics().values()),
                'provider_usage': {
                    provider.value: len([r for r in self.resources if r['provider'] == provider.value])
                    for provider in self.providers.keys()
                },
                'cost_distribution': {
                    provider.value: sum(c.monthly_cost for c in self.costs.values() if c.provider == provider)
                    for provider in self.providers.keys()
                },
                'performance_metrics': self.get_llm_metrics(),
                'last_operation': self.operation_history[-1] if self.operation_history else None
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get multi-LLM summary: {e}")
            return {}
    
    async def cleanup_old_requests(self, older_than_hours: int = 24):
        """Clean up old requests"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
            
            requests_to_delete = []
            for request_id, request_info in self.request_history.items():
                if request_info['timestamp'] < cutoff_time:
                    requests_to_delete.append(request_id)
            
            for request_id in requests_to_delete:
                del self.request_history[request_id]
            
            logger.info(f"Cleaned up {len(requests_to_delete)} old requests")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old requests: {e}")
    
    async def shutdown(self):
        """Shutdown multi-LLM manager"""
        try:
            logger.info("Shutting down multi-LLM manager...")
            
            # Shutdown all adapters
            for adapter in self.adapters.values():
                await adapter.shutdown()
            
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("Multi-LLM manager shutdown complete")
            
        except Exception as e:
            logger.error(f"Multi-LLM manager shutdown error: {e}")

# Global multi-LLM manager instance
multi_llm_manager = MultiLLMManager()
