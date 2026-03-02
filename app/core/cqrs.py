"""
CQRS (Command Query Responsibility Segregation) Pattern Implementation
Separates read and write operations for optimal performance and scalability
"""

import asyncio
import json
import uuid
from typing import Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import logging
import redis
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CommandStatus(Enum):
    """Status of command execution"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Command:
    """Base command class"""
    command_id: str
    command_type: str
    aggregate_id: str
    data: dict[str, Any]
    timestamp: datetime
    expected_version: int | None = None
    metadata: dict[str, Any] = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'command_id': self.command_id,
            'command_type': self.command_type,
            'aggregate_id': self.aggregate_id,
            'data': self.data,
            'timestamp': self.timestamp.isoformat(),
            'expected_version': self.expected_version,
            'metadata': self.metadata or {}
        }


@dataclass
class CommandResult:
    """Result of command execution"""
    command_id: str
    status: CommandStatus
    result: Any | None = None
    error: str | None = None
    execution_time: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class Query:
    """Base query class"""
    query_id: str
    query_type: str
    parameters: dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class QueryResult:
    """Result of query execution"""
    query_id: str
    data: Any
    execution_time: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class CommandHandler(ABC):
    """Base command handler"""
    
    @abstractmethod
    async def handle(self, command: Command) -> CommandResult:
        """Handle a command"""
        pass


class QueryHandler(ABC):
    """Base query handler"""
    
    @abstractmethod
    async def handle(self, query: Query) -> QueryResult:
        """Handle a query"""
        pass


# Command Handlers
class CreateIdeaCommandHandler(CommandHandler):
    """Handler for creating ideas"""
    
    def __init__(self, event_store):
        self.event_store = event_store
    
    async def handle(self, command: Command) -> CommandResult:
        """Handle create idea command"""
        start_time = time.time()
        
        try:
            # Validate command
            if not command.data.get('title'):
                return CommandResult(
                    command_id=command.command_id,
                    status=CommandStatus.FAILED,
                    error="Title is required"
                )
            
            # Create event
            from app.core.event_sourcing import Event, EventType
            event = Event(
                event_id=str(uuid.uuid4()),
                aggregate_id=command.aggregate_id,
                aggregate_type="IdeaAggregate",
                event_type=EventType.IDEA_CREATED,
                event_data=command.data,
                timestamp=datetime.utcnow(),
                version=1
            )
            
            # Save event
            await self.event_store.save_events([event])
            
            return CommandResult(
                command_id=command.command_id,
                status=CommandStatus.COMPLETED,
                result={'event_id': event.event_id, 'version': 1},
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Error handling create idea command: {e}")
            return CommandResult(
                command_id=command.command_id,
                status=CommandStatus.FAILED,
                error=str(e),
                execution_time=time.time() - start_time
            )


class UpdateIdeaCommandHandler(CommandHandler):
    """Handler for updating ideas"""
    
    def __init__(self, event_store):
        self.event_store = event_store
    
    async def handle(self, command: Command) -> CommandResult:
        """Handle update idea command"""
        start_time = time.time()
        
        try:
            # Get current version
            events = await self.event_store.get_events(command.aggregate_id)
            if not events:
                return CommandResult(
                    command_id=command.command_id,
                    status=CommandStatus.FAILED,
                    error="Idea not found"
                )
            
            current_version = events[-1].version
            
            # Check expected version
            if command.expected_version and command.expected_version != current_version:
                return CommandResult(
                    command_id=command.command_id,
                    status=CommandStatus.FAILED,
                    error=f"Version conflict: expected {command.expected_version}, got {current_version}"
                )
            
            # Create event
            from app.core.event_sourcing import Event, EventType
            event = Event(
                event_id=str(uuid.uuid4()),
                aggregate_id=command.aggregate_id,
                aggregate_type="IdeaAggregate",
                event_type=EventType.IDEA_UPDATED,
                event_data=command.data,
                timestamp=datetime.utcnow(),
                version=current_version + 1
            )
            
            # Save event
            await self.event_store.save_events([event])
            
            return CommandResult(
                command_id=command.command_id,
                status=CommandStatus.COMPLETED,
                result={'event_id': event.event_id, 'version': current_version + 1},
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Error handling update idea command: {e}")
            return CommandResult(
                command_id=command.command_id,
                status=CommandStatus.FAILED,
                error=str(e),
                execution_time=time.time() - start_time
            )


class EvaluateIdeaCommandHandler(CommandHandler):
    """Handler for evaluating ideas"""
    
    def __init__(self, event_store):
        self.event_store = event_store
    
    async def handle(self, command: Command) -> CommandResult:
        """Handle evaluate idea command"""
        start_time = time.time()
        
        try:
            # Get current version
            events = await self.event_store.get_events(command.aggregate_id)
            if not events:
                return CommandResult(
                    command_id=command.command_id,
                    status=CommandStatus.FAILED,
                    error="Idea not found"
                )
            
            current_version = events[-1].version
            
            # Create event
            from app.core.event_sourcing import Event, EventType
            event = Event(
                event_id=str(uuid.uuid4()),
                aggregate_id=command.aggregate_id,
                aggregate_type="IdeaAggregate",
                event_type=EventType.IDEA_EVALUATED,
                event_data=command.data,
                timestamp=datetime.utcnow(),
                version=current_version + 1
            )
            
            # Save event
            await self.event_store.save_events([event])
            
            return CommandResult(
                command_id=command.command_id,
                status=CommandStatus.COMPLETED,
                result={'event_id': event.event_id, 'version': current_version + 1},
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Error handling evaluate idea command: {e}")
            return CommandResult(
                command_id=command.command_id,
                status=CommandStatus.FAILED,
                error=str(e),
                execution_time=time.time() - start_time
            )


class CreateMVPCommandHandler(CommandHandler):
    """Handler for creating MVPs"""
    
    def __init__(self, event_store):
        self.event_store = event_store
    
    async def handle(self, command: Command) -> CommandResult:
        """Handle create MVP command"""
        start_time = time.time()
        
        try:
            # Create event
            from app.core.event_sourcing import Event, EventType
            event = Event(
                event_id=str(uuid.uuid4()),
                aggregate_id=command.aggregate_id,
                aggregate_type="MVPAggregate",
                event_type=EventType.MVP_STARTED,
                event_data=command.data,
                timestamp=datetime.utcnow(),
                version=1
            )
            
            # Save event
            await self.event_store.save_events([event])
            
            return CommandResult(
                command_id=command.command_id,
                status=CommandStatus.COMPLETED,
                result={'event_id': event.event_id, 'version': 1},
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Error handling create MVP command: {e}")
            return CommandResult(
                command_id=command.command_id,
                status=CommandStatus.FAILED,
                error=str(e),
                execution_time=time.time() - start_time
            )


# Query Handlers
class GetIdeaQueryHandler(QueryHandler):
    """Handler for getting idea details"""
    
    def __init__(self, read_model):
        self.read_model = read_model
    
    async def handle(self, query: Query) -> QueryResult:
        """Handle get idea query"""
        start_time = time.time()
        
        try:
            idea_id = query.parameters.get('idea_id')
            if not idea_id:
                return QueryResult(
                    query_id=query.query_id,
                    data=None,
                    execution_time=time.time() - start_time
                )
            
            # Get from read model
            idea_data = await self.read_model.get_idea(idea_id)
            
            return QueryResult(
                query_id=query.query_id,
                data=idea_data,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Error handling get idea query: {e}")
            return QueryResult(
                query_id=query.query_id,
                data=None,
                execution_time=time.time() - start_time
            )


class ListIdeasQueryHandler(QueryHandler):
    """Handler for listing ideas"""
    
    def __init__(self, read_model):
        self.read_model = read_model
    
    async def handle(self, query: Query) -> QueryResult:
        """Handle list ideas query"""
        start_time = time.time()
        
        try:
            filters = query.parameters.get('filters', {})
            pagination = query.parameters.get('pagination', {})
            
            # Get from read model
            ideas = await self.read_model.list_ideas(filters, pagination)
            
            return QueryResult(
                query_id=query.query_id,
                data=ideas,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Error handling list ideas query: {e}")
            return QueryResult(
                query_id=query.query_id,
                data=[],
                execution_time=time.time() - start_time
            )


class GetMVPQueryHandler(QueryHandler):
    """Handler for getting MVP details"""
    
    def __init__(self, read_model):
        self.read_model = read_model
    
    async def handle(self, query: Query) -> QueryResult:
        """Handle get MVP query"""
        start_time = time.time()
        
        try:
            mvp_id = query.parameters.get('mvp_id')
            if not mvp_id:
                return QueryResult(
                    query_id=query.query_id,
                    data=None,
                    execution_time=time.time() - start_time
                )
            
            # Get from read model
            mvp_data = await self.read_model.get_mvp(mvp_id)
            
            return QueryResult(
                query_id=query.query_id,
                data=mvp_data,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Error handling get MVP query: {e}")
            return QueryResult(
                query_id=query.query_id,
                data=None,
                execution_time=time.time() - start_time
            )


class ReadModel:
    """Read model for query operations"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_client = redis.from_url(redis_url)
    
    async def get_idea(self, idea_id: str) -> dict[str, Any] | None:
        """Get idea from read model"""
        try:
            idea_key = f"idea_read_model:{idea_id}"
            idea_data = self.redis_client.get(idea_key)
            
            if idea_data:
                return json.loads(idea_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting idea {idea_id}: {e}")
            return None
    
    async def list_ideas(self, filters: dict[str, Any] = None, 
                        pagination: dict[str, Any] = None) -> dict[str, Any]:
        """List ideas from read model"""
        try:
            filters = filters or {}
            pagination = pagination or {}
            
            # Get all idea keys
            idea_keys = self.redis_client.keys("idea_read_model:*")
            
            ideas = []
            for key in idea_keys:
                idea_data = self.redis_client.get(key)
                if idea_data:
                    idea = json.loads(idea_data)
                    
                    # Apply filters
                    if self._matches_filters(idea, filters):
                        ideas.append(idea)
            
            # Apply pagination
            total_count = len(ideas)
            page = pagination.get('page', 1)
            page_size = pagination.get('page_size', 20)
            
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            
            paginated_ideas = ideas[start_idx:end_idx]
            
            return {
                'ideas': paginated_ideas,
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size
            }
            
        except Exception as e:
            logger.error(f"Error listing ideas: {e}")
            return {'ideas': [], 'total_count': 0}
    
    async def get_mvp(self, mvp_id: str) -> dict[str, Any] | None:
        """Get MVP from read model"""
        try:
            mvp_key = f"mvp_read_model:{mvp_id}"
            mvp_data = self.redis_client.get(mvp_key)
            
            if mvp_data:
                return json.loads(mvp_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting MVP {mvp_id}: {e}")
            return None
    
    def _matches_filters(self, idea: dict[str, Any], filters: dict[str, Any]) -> bool:
        """Check if idea matches filters"""
        for key, value in filters.items():
            if key not in idea:
                return False
            
            if isinstance(value, str):
                if value.lower() not in str(idea[key]).lower():
                    return False
            elif idea[key] != value:
                return False
        
        return True


class CommandBus:
    """Command bus for handling commands"""
    
    def __init__(self):
        self.handlers: dict[str, CommandHandler] = {}
        self.middleware: list[callable] = []
    
    def register_handler(self, command_type: str, handler: CommandHandler) -> None:
        """Register a command handler"""
        self.handlers[command_type] = handler
    
    def add_middleware(self, middleware: callable) -> None:
        """Add middleware to the command bus"""
        self.middleware.append(middleware)
    
    async def send(self, command: Command) -> CommandResult:
        """Send a command for processing"""
        try:
            # Apply middleware
            for middleware in self.middleware:
                command = await middleware(command)
                if command is None:
                    return CommandResult(
                        command_id=command.command_id,
                        status=CommandStatus.FAILED,
                        error="Command rejected by middleware"
                    )
            
            # Get handler
            handler = self.handlers.get(command.command_type)
            if not handler:
                return CommandResult(
                    command_id=command.command_id,
                    status=CommandStatus.FAILED,
                    error=f"No handler for command type: {command.command_type}"
                )
            
            # Handle command
            result = await handler.handle(command)
            
            # Log command
            logger.info(f"Command {command.command_type} ({command.command_id}) "
                       f"completed with status {result.status.value}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing command {command.command_id}: {e}")
            return CommandResult(
                command_id=command.command_id,
                status=CommandStatus.FAILED,
                error=str(e)
            )


class QueryBus:
    """Query bus for handling queries"""
    
    def __init__(self):
        self.handlers: dict[str, QueryHandler] = {}
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def register_handler(self, query_type: str, handler: QueryHandler) -> None:
        """Register a query handler"""
        self.handlers[query_type] = handler
    
    async def send(self, query: Query) -> QueryResult:
        """Send a query for processing"""
        try:
            # Check cache
            cache_key = f"{query.query_type}:{hash(str(query.parameters))}"
            cached_result = self.cache.get(cache_key)
            
            if cached_result and (datetime.utcnow() - cached_result['timestamp']).seconds < self.cache_ttl:
                return cached_result['result']
            
            # Get handler
            handler = self.handlers.get(query.query_type)
            if not handler:
                return QueryResult(
                    query_id=query.query_id,
                    data=None,
                    error=f"No handler for query type: {query.query_type}"
                )
            
            # Handle query
            result = await handler.handle(query)
            
            # Cache result
            self.cache[cache_key] = {
                'result': result,
                'timestamp': datetime.utcnow()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing query {query.query_id}: {e}")
            return QueryResult(
                query_id=query.query_id,
                data=None,
                error=str(e)
            )
    
    def clear_cache(self) -> None:
        """Clear query cache"""
        self.cache.clear()


class CQRSService:
    """CQRS service coordinating command and query buses"""
    
    def __init__(self, event_store, read_model):
        self.command_bus = CommandBus()
        self.query_bus = QueryBus()
        self.event_store = event_store
        self.read_model = read_model
        
        # Register command handlers
        self._register_command_handlers()
        
        # Register query handlers
        self._register_query_handlers()
        
        # Add middleware
        self._add_middleware()
    
    def _register_command_handlers(self) -> None:
        """Register all command handlers"""
        self.command_bus.register_handler("create_idea", CreateIdeaCommandHandler(self.event_store))
        self.command_bus.register_handler("update_idea", UpdateIdeaCommandHandler(self.event_store))
        self.command_bus.register_handler("evaluate_idea", EvaluateIdeaCommandHandler(self.event_store))
        self.command_bus.register_handler("create_mvp", CreateMVPCommandHandler(self.event_store))
    
    def _register_query_handlers(self) -> None:
        """Register all query handlers"""
        self.query_bus.register_handler("get_idea", GetIdeaQueryHandler(self.read_model))
        self.query_bus.register_handler("list_ideas", ListIdeasQueryHandler(self.read_model))
        self.query_bus.register_handler("get_mvp", GetMVPQueryHandler(self.read_model))
    
    def _add_middleware(self) -> None:
        """Add middleware to command bus"""
        async def logging_middleware(command: Command):
            """Logging middleware"""
            logger.info(f"Processing command: {command.command_type} ({command.command_id})")
            return command
        
        async def validation_middleware(command: Command):
            """Validation middleware"""
            if not command.aggregate_id:
                logger.error("Command missing aggregate_id")
                return None
            
            if not command.command_type:
                logger.error("Command missing command_type")
                return None
            
            return command
        
        self.command_bus.add_middleware(validation_middleware)
        self.command_bus.add_middleware(logging_middleware)
    
    async def send_command(self, command_type: str, aggregate_id: str, 
                          data: dict[str, Any], expected_version: int = None) -> CommandResult:
        """Send a command"""
        command = Command(
            command_id=str(uuid.uuid4()),
            command_type=command_type,
            aggregate_id=aggregate_id,
            data=data,
            timestamp=datetime.utcnow(),
            expected_version=expected_version
        )
        
        return await self.command_bus.send(command)
    
    async def send_query(self, query_type: str, parameters: dict[str, Any] = None) -> QueryResult:
        """Send a query"""
        query = Query(
            query_id=str(uuid.uuid4()),
            query_type=query_type,
            parameters=parameters or {}
        )
        
        return await self.query_bus.send(query)


# Example usage
async def example_usage():
    """Example of CQRS usage"""
    
    # Initialize components
    from app.core.event_sourcing import EventStore
    event_store = EventStore()
    read_model = ReadModel()
    cqrs_service = CQRSService(event_store, read_model)
    
    # Send commands
    result = await cqrs_service.send_command(
        "create_idea",
        "idea-123",
        {
            "title": "AI Startup Generator",
            "description": "Generate AI-powered startups",
            "topic": "AI/ML"
        }
    )
    
    print(f"Command result: {result.status.value}")
    
    # Send query
    query_result = await cqrs_service.send_query(
        "get_idea",
        {"idea_id": "idea-123"}
    )
    
    print(f"Query result: {query_result.data}")
    
    # Update idea
    update_result = await cqrs_service.send_command(
        "update_idea",
        "idea-123",
        {"title": "Advanced AI Startup Generator"},
        expected_version=1
    )
    
    print(f"Update result: {update_result.status.value}")
    
    # List ideas
    list_result = await cqrs_service.send_query(
        "list_ideas",
        {"filters": {"topic": "AI/ML"}, "pagination": {"page": 1, "page_size": 10}}
    )
    
    print(f"List result: {len(list_result.data['ideas'])} ideas found")


if __name__ == "__main__":
    asyncio.run(example_usage())
