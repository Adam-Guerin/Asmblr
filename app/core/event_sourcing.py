"""
Event Sourcing Pattern Implementation for Asmblr
Complete event-driven architecture with event store, snapshots, and projections
"""

import asyncio
import json
import uuid
from typing import Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
import redis
import sqlite3
from pathlib import Path
from dataclasses import field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of events in the system"""
    IDEA_CREATED = "idea_created"
    IDEA_UPDATED = "idea_updated"
    IDEA_EVALUATED = "idea_evaluated"
    IDEA_APPROVED = "idea_approved"
    IDEA_REJECTED = "idea_rejected"
    
    MVP_STARTED = "mvp_started"
    MVP_BUILD_COMPLETED = "mvp_build_completed"
    MVP_BUILD_FAILED = "mvp_build_failed"
    MVP_DEPLOYED = "mvp_deployed"
    
    USER_REGISTERED = "user_registered"
    USER_UPDATED = "user_updated"
    USER_SUBSCRIBED = "user_subscribed"
    USER_UNSUBSCRIBED = "user_unsubscribed"
    
    SYSTEM_MAINTENANCE = "system_maintenance"
    SYSTEM_BACKUP = "system_backup"
    SYSTEM_RESTORE = "system_restore"


@dataclass
class Event:
    """Base event class"""
    event_id: str
    aggregate_id: str
    aggregate_type: str
    event_type: EventType
    event_data: dict[str, Any]
    timestamp: datetime
    version: int
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary"""
        return {
            'event_id': self.event_id,
            'aggregate_id': self.aggregate_id,
            'aggregate_type': self.aggregate_type,
            'event_type': self.event_type.value,
            'event_data': self.event_data,
            'timestamp': self.timestamp.isoformat(),
            'version': self.version,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Event':
        """Create event from dictionary"""
        return cls(
            event_id=data['event_id'],
            aggregate_id=data['aggregate_id'],
            aggregate_type=data['aggregate_type'],
            event_type=EventType(data['event_type']),
            event_data=data['event_data'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            version=data['version'],
            metadata=data.get('metadata', {})
        )


@dataclass
class Snapshot:
    """Aggregate snapshot for performance optimization"""
    aggregate_id: str
    aggregate_type: str
    data: dict[str, Any]
    version: int
    timestamp: datetime
    
    def to_dict(self) -> dict[str, Any]:
        return {
            'aggregate_id': self.aggregate_id,
            'aggregate_type': self.aggregate_type,
            'data': self.data,
            'version': self.version,
            'timestamp': self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'Snapshot':
        return cls(
            aggregate_id=data['aggregate_id'],
            aggregate_type=data['aggregate_type'],
            data=data['data'],
            version=data['version'],
            timestamp=datetime.fromisoformat(data['timestamp'])
        )


class AggregateRoot(ABC):
    """Base aggregate root class"""
    
    def __init__(self, aggregate_id: str):
        self.aggregate_id = aggregate_id
        self.version = 0
        self.uncommitted_events: list[Event] = []
    
    @abstractmethod
    def apply_event(self, event: Event) -> None:
        """Apply an event to the aggregate"""
        pass
    
    def add_event(self, event_type: EventType, event_data: dict[str, Any], metadata: dict[str, Any] = None) -> Event:
        """Add a new event to the aggregate"""
        event = Event(
            event_id=str(uuid.uuid4()),
            aggregate_id=self.aggregate_id,
            aggregate_type=self.__class__.__name__,
            event_type=event_type,
            event_data=event_data,
            timestamp=datetime.utcnow(),
            version=self.version + 1,
            metadata=metadata or {}
        )
        
        self.uncommitted_events.append(event)
        self.apply_event(event)
        self.version += 1
        
        return event
    
    def mark_events_as_committed(self) -> None:
        """Mark all uncommitted events as committed"""
        self.uncommitted_events.clear()


class IdeaAggregate(AggregateRoot):
    """Idea aggregate with event sourcing"""
    
    def __init__(self, aggregate_id: str, title: str = None, description: str = None):
        super().__init__(aggregate_id)
        self.title = title
        self.description = description
        self.topic = None
        self.confidence_score = 0.0
        self.market_signal_score = 0.0
        self.actionability_score = 0.0
        self.status = "draft"
        self.created_at = None
        self.updated_at = None
        self.evaluation_result = None
    
    def apply_event(self, event: Event) -> None:
        """Apply events to update state"""
        if event.event_type == EventType.IDEA_CREATED:
            self.title = event.event_data.get('title')
            self.description = event.event_data.get('description')
            self.topic = event.event_data.get('topic')
            self.status = "created"
            self.created_at = event.timestamp
            self.updated_at = event.timestamp
            
        elif event.event_type == EventType.IDEA_UPDATED:
            if 'title' in event.event_data:
                self.title = event.event_data['title']
            if 'description' in event.event_data:
                self.description = event.event_data['description']
            if 'topic' in event.event_data:
                self.topic = event.event_data['topic']
            self.updated_at = event.timestamp
            
        elif event.event_type == EventType.IDEA_EVALUATED:
            self.confidence_score = event.event_data.get('confidence_score', 0.0)
            self.market_signal_score = event.event_data.get('market_signal_score', 0.0)
            self.actionability_score = event.event_data.get('actionability_score', 0.0)
            self.evaluation_result = event.event_data.get('result')
            self.updated_at = event.timestamp
            
        elif event.event_type == EventType.IDEA_APPROVED:
            self.status = "approved"
            self.updated_at = event.timestamp
            
        elif event.event_type == EventType.IDEA_REJECTED:
            self.status = "rejected"
            self.updated_at = event.timestamp
    
    def create(self, title: str, description: str, topic: str) -> Event:
        """Create a new idea"""
        return self.add_event(
            EventType.IDEA_CREATED,
            {
                'title': title,
                'description': description,
                'topic': topic
            }
        )
    
    def update(self, title: str = None, description: str = None, topic: str = None) -> Event:
        """Update idea details"""
        update_data = {}
        if title is not None:
            update_data['title'] = title
        if description is not None:
            update_data['description'] = description
        if topic is not None:
            update_data['topic'] = topic
        
        return self.add_event(EventType.IDEA_UPDATED, update_data)
    
    def evaluate(self, confidence_score: float, market_signal_score: float, 
                 actionability_score: float, result: str) -> Event:
        """Evaluate the idea"""
        return self.add_event(
            EventType.IDEA_EVALUATED,
            {
                'confidence_score': confidence_score,
                'market_signal_score': market_signal_score,
                'actionability_score': actionability_score,
                'result': result
            }
        )
    
    def approve(self) -> Event:
        """Approve the idea"""
        return self.add_event(EventType.IDEA_APPROVED, {})
    
    def reject(self) -> Event:
        """Reject the idea"""
        return self.add_event(EventType.IDEA_REJECTED, {})


class MVPAggregate(AggregateRoot):
    """MVP aggregate with event sourcing"""
    
    def __init__(self, aggregate_id: str, idea_id: str = None):
        super().__init__(aggregate_id)
        self.idea_id = idea_id
        self.status = "planned"
        self.build_duration = 0.0
        self.cycles_completed = 0
        self.cycles_failed = 0
        self.frontend_stack = None
        self.backend_stack = None
        self.features_implemented = 0
        self.bugs_fixed = 0
        self.build_log = []
        self.started_at = None
        self.completed_at = None
    
    def apply_event(self, event: Event) -> None:
        """Apply events to update state"""
        if event.event_type == EventType.MVP_STARTED:
            self.idea_id = event.event_data.get('idea_id')
            self.status = "building"
            self.frontend_stack = event.event_data.get('frontend_stack')
            self.backend_stack = event.event_data.get('backend_stack')
            self.started_at = event.timestamp
            
        elif event.event_type == EventType.MVP_BUILD_COMPLETED:
            self.cycles_completed = event.event_data.get('cycles_completed', 0)
            self.cycles_failed = event.event_data.get('cycles_failed', 0)
            self.features_implemented = event.event_data.get('features_implemented', 0)
            self.bugs_fixed = event.event_data.get('bugs_fixed', 0)
            self.build_duration = event.event_data.get('build_duration', 0.0)
            self.status = "completed"
            self.completed_at = event.timestamp
            
        elif event.event_type == EventType.MVP_BUILD_FAILED:
            self.cycles_failed = event.event_data.get('cycles_failed', 0)
            self.status = "failed"
            self.completed_at = event.timestamp
            
        elif event.event_type == EventType.MVP_DEPLOYED:
            self.status = "deployed"
            self.completed_at = event.timestamp
    
    def start(self, idea_id: str, frontend_stack: str, backend_stack: str) -> Event:
        """Start MVP build"""
        return self.add_event(
            EventType.MVP_STARTED,
            {
                'idea_id': idea_id,
                'frontend_stack': frontend_stack,
                'backend_stack': backend_stack
            }
        )
    
    def complete_build(self, cycles_completed: int, cycles_failed: int, 
                      features_implemented: int, bugs_fixed: int, build_duration: float) -> Event:
        """Complete MVP build"""
        return self.add_event(
            EventType.MVP_BUILD_COMPLETED,
            {
                'cycles_completed': cycles_completed,
                'cycles_failed': cycles_failed,
                'features_implemented': features_implemented,
                'bugs_fixed': bugs_fixed,
                'build_duration': build_duration
            }
        )
    
    def fail_build(self, cycles_failed: int) -> Event:
        """Fail MVP build"""
        return self.add_event(
            EventType.MVP_BUILD_FAILED,
            {
                'cycles_failed': cycles_failed
            }
        )
    
    def deploy(self) -> Event:
        """Deploy MVP"""
        return self.add_event(EventType.MVP_DEPLOYED, {})


class EventStore:
    """Event store for persisting events"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", db_path: str = "data/event_store.db"):
        self.redis_url = redis_url
        self.db_path = db_path
        self.redis_client = redis.from_url(redis_url)
        
        # Initialize SQLite database
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize the event store database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                event_id TEXT PRIMARY KEY,
                aggregate_id TEXT NOT NULL,
                aggregate_type TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                version INTEGER NOT NULL,
                metadata TEXT,
                INDEX(aggregate_id, version),
                INDEX(aggregate_type),
                INDEX(event_type),
                INDEX(timestamp)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                aggregate_id TEXT PRIMARY KEY,
                aggregate_type TEXT NOT NULL,
                data TEXT NOT NULL,
                version INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                INDEX(aggregate_type),
                INDEX(timestamp)
            )
        """)
        
        conn.commit()
        conn.close()
    
    async def save_events(self, events: list[Event]) -> None:
        """Save events to the event store"""
        if not events:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for event in events:
                # Save to SQLite
                cursor.execute("""
                    INSERT OR REPLACE INTO events 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id,
                    event.aggregate_id,
                    event.aggregate_type,
                    event.event_type.value,
                    json.dumps(event.event_data),
                    event.timestamp.isoformat(),
                    event.version,
                    json.dumps(event.metadata)
                ))
                
                # Save to Redis for fast access
                redis_key = f"event:{event.aggregate_id}:{event.version}"
                self.redis_client.setex(
                    redis_key,
                    timedelta(hours=24),
                    json.dumps(event.to_dict())
                )
                
                # Add to aggregate stream
                stream_key = f"events:{event.aggregate_id}"
                self.redis_client.xadd(
                    stream_key,
                    {
                        'event_id': event.event_id,
                        'event_type': event.event_type.value,
                        'timestamp': event.timestamp.isoformat(),
                        'version': str(event.version)
                    }
                )
            
            conn.commit()
            logger.info(f"Saved {len(events)} events to event store")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving events: {e}")
            raise
        finally:
            conn.close()
    
    async def get_events(self, aggregate_id: str, from_version: int = 0) -> list[Event]:
        """Get events for an aggregate from a specific version"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM events 
                WHERE aggregate_id = ? AND version > ?
                ORDER BY version ASC
            """, (aggregate_id, from_version))
            
            rows = cursor.fetchall()
            events = []
            
            for row in rows:
                event = Event(
                    event_id=row[0],
                    aggregate_id=row[1],
                    aggregate_type=row[2],
                    event_type=EventType(row[3]),
                    event_data=json.loads(row[4]),
                    timestamp=datetime.fromisoformat(row[5]),
                    version=row[6],
                    metadata=json.loads(row[7]) if row[7] else {}
                )
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting events for {aggregate_id}: {e}")
            return []
        finally:
            conn.close()
    
    async def save_snapshot(self, snapshot: Snapshot) -> None:
        """Save aggregate snapshot"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO snapshots 
                VALUES (?, ?, ?, ?, ?)
            """, (
                snapshot.aggregate_id,
                snapshot.aggregate_type,
                json.dumps(snapshot.data),
                snapshot.version,
                snapshot.timestamp.isoformat()
            ))
            
            # Save to Redis
            redis_key = f"snapshot:{snapshot.aggregate_id}"
            self.redis_client.setex(
                redis_key,
                timedelta(hours=24),
                json.dumps(snapshot.to_dict())
            )
            
            conn.commit()
            logger.info(f"Saved snapshot for {snapshot.aggregate_id} at version {snapshot.version}")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving snapshot: {e}")
            raise
        finally:
            conn.close()
    
    async def get_snapshot(self, aggregate_id: str) -> Snapshot | None:
        """Get latest snapshot for an aggregate"""
        # Try Redis first
        redis_key = f"snapshot:{aggregate_id}"
        snapshot_data = self.redis_client.get(redis_key)
        
        if snapshot_data:
            try:
                data = json.loads(snapshot_data)
                return Snapshot.from_dict(data)
            except Exception as e:
                logger.warning(f"Error parsing snapshot from Redis: {e}")
        
        # Fallback to SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM snapshots 
                WHERE aggregate_id = ?
                ORDER BY version DESC
                LIMIT 1
            """, (aggregate_id,))
            
            row = cursor.fetchone()
            if row:
                return Snapshot(
                    aggregate_id=row[0],
                    aggregate_type=row[1],
                    data=json.loads(row[2]),
                    version=row[3],
                    timestamp=datetime.fromisoformat(row[4])
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting snapshot for {aggregate_id}: {e}")
            return None
        finally:
            conn.close()
    
    async def get_events_by_type(self, event_type: EventType, limit: int = 100) -> list[Event]:
        """Get events by type"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM events 
                WHERE event_type = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (event_type.value, limit))
            
            rows = cursor.fetchall()
            events = []
            
            for row in rows:
                event = Event(
                    event_id=row[0],
                    aggregate_id=row[1],
                    aggregate_type=row[2],
                    event_type=EventType(row[3]),
                    event_data=json.loads(row[4]),
                    timestamp=datetime.fromisoformat(row[5]),
                    version=row[6],
                    metadata=json.loads(row[7]) if row[7] else {}
                )
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Error getting events by type {event_type}: {e}")
            return []
        finally:
            conn.close()


class Projection(ABC):
    """Base projection class"""
    
    def __init__(self, name: str):
        self.name = name
        self.last_processed_version = 0
    
    @abstractmethod
    async def project(self, event: Event) -> None:
        """Project an event to update the read model"""
        pass
    
    async def handle(self, event: Event) -> None:
        """Handle an event"""
        if event.version > self.last_processed_version:
            await self.project(event)
            self.last_processed_version = event.version


class IdeaProjection(Projection):
    """Projection for ideas read model"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        super().__init__("idea_projection")
        self.redis_client = redis.from_url(redis_url)
    
    async def project(self, event: Event) -> None:
        """Project idea events"""
        if event.aggregate_type != "IdeaAggregate":
            return
        
        idea_key = f"idea_read_model:{event.aggregate_id}"
        
        # Get current state or create new
        current_data = self.redis_client.get(idea_key)
        if current_data:
            idea_data = json.loads(current_data)
        else:
            idea_data = {
                'aggregate_id': event.aggregate_id,
                'title': None,
                'description': None,
                'topic': None,
                'status': 'draft',
                'confidence_score': 0.0,
                'market_signal_score': 0.0,
                'actionability_score': 0.0,
                'created_at': None,
                'updated_at': None
            }
        
        # Update based on event type
        if event.event_type == EventType.IDEA_CREATED:
            idea_data.update({
                'title': event.event_data.get('title'),
                'description': event.event_data.get('description'),
                'topic': event.event_data.get('topic'),
                'status': 'created',
                'created_at': event.timestamp.isoformat(),
                'updated_at': event.timestamp.isoformat()
            })
        
        elif event.event_type == EventType.IDEA_UPDATED:
            if 'title' in event.event_data:
                idea_data['title'] = event.event_data['title']
            if 'description' in event.event_data:
                idea_data['description'] = event.event_data['description']
            if 'topic' in event.event_data:
                idea_data['topic'] = event.event_data['topic']
            idea_data['updated_at'] = event.timestamp.isoformat()
        
        elif event.event_type == EventType.IDEA_EVALUATED:
            idea_data.update({
                'confidence_score': event.event_data.get('confidence_score', 0.0),
                'market_signal_score': event.event_data.get('market_signal_score', 0.0),
                'actionability_score': event.event_data.get('actionability_score', 0.0),
                'updated_at': event.timestamp.isoformat()
            })
        
        elif event.event_type == EventType.IDEA_APPROVED:
            idea_data['status'] = 'approved'
            idea_data['updated_at'] = event.timestamp.isoformat()
        
        elif event.event_type == EventType.IDEA_REJECTED:
            idea_data['status'] = 'rejected'
            idea_data['updated_at'] = event.timestamp.isoformat()
        
        # Save updated state
        self.redis_client.setex(
            idea_key,
            timedelta(hours=24),
            json.dumps(idea_data)
        )
        
        # Update indexes
        await self._update_indexes(idea_data)


class MVPProjection(Projection):
    """Projection for MVPs read model"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        super().__init__("mvp_projection")
        self.redis_client = redis.from_url(redis_url)
    
    async def project(self, event: Event) -> None:
        """Project MVP events"""
        if event.aggregate_type != "MVPAggregate":
            return
        
        mvp_key = f"mvp_read_model:{event.aggregate_id}"
        
        # Get current state or create new
        current_data = self.redis_client.get(mvp_key)
        if current_data:
            mvp_data = json.loads(current_data)
        else:
            mvp_data = {
                'aggregate_id': event.aggregate_id,
                'idea_id': None,
                'status': 'planned',
                'build_duration': 0.0,
                'cycles_completed': 0,
                'cycles_failed': 0,
                'frontend_stack': None,
                'backend_stack': None,
                'features_implemented': 0,
                'bugs_fixed': 0,
                'started_at': None,
                'completed_at': None
            }
        
        # Update based on event type
        if event.event_type == EventType.MVP_STARTED:
            mvp_data.update({
                'idea_id': event.event_data.get('idea_id'),
                'status': 'building',
                'frontend_stack': event.event_data.get('frontend_stack'),
                'backend_stack': event.event_data.get('backend_stack'),
                'started_at': event.timestamp.isoformat()
            })
        
        elif event.event_type == EventType.MVP_BUILD_COMPLETED:
            mvp_data.update({
                'cycles_completed': event.event_data.get('cycles_completed', 0),
                'cycles_failed': event.event_data.get('cycles_failed', 0),
                'features_implemented': event.event_data.get('features_implemented', 0),
                'bugs_fixed': event.event_data.get('bugs_fixed', 0),
                'build_duration': event.event_data.get('build_duration', 0.0),
                'status': 'completed',
                'completed_at': event.timestamp.isoformat()
            })
        
        elif event.event_type == EventType.MVP_BUILD_FAILED:
            mvp_data.update({
                'cycles_failed': event.event_data.get('cycles_failed', 0),
                'status': 'failed',
                'completed_at': event.timestamp.isoformat()
            })
        
        elif event.event_type == EventType.IDEA_REJECTED:
            mvp_data['status'] = 'rejected'
            mvp_data['completed_at'] = event.timestamp.isoformat()
        
        # Save updated state
        self.redis_client.setex(
            mvp_key,
            timedelta(hours=24),
            json.dumps(mvp_data)
        )


class EventSourcingRepository:
    """Repository for event-sourced aggregates"""
    
    def __init__(self, event_store: EventStore, snapshot_interval: int = 10):
        self.event_store = event_store
        self.snapshot_interval = snapshot_interval
    
    async def save(self, aggregate: AggregateRoot) -> None:
        """Save aggregate with its events"""
        if not aggregate.uncommitted_events:
            return
        
        # Save events
        await self.event_store.save_events(aggregate.uncommitted_events)
        
        # Create snapshot if needed
        if aggregate.version % self.snapshot_interval == 0:
            snapshot = Snapshot(
                aggregate_id=aggregate.aggregate_id,
                aggregate_type=aggregate.__class__.__name__,
                data=aggregate.__dict__,
                version=aggregate.version,
                timestamp=datetime.utcnow()
            )
            await self.event_store.save_snapshot(snapshot)
        
        # Mark events as committed
        aggregate.mark_events_as_committed()
    
    async def load(self, aggregate_class: type, aggregate_id: str) -> AggregateRoot | None:
        """Load aggregate from events and snapshots"""
        # Try to load from snapshot first
        snapshot = await self.event_store.get_snapshot(aggregate_id)
        
        if snapshot:
            # Create aggregate from snapshot
            aggregate = aggregate_class.__new__(aggregate_class)
            aggregate.__dict__.update(snapshot.data)
            aggregate.version = snapshot.version
            from_version = snapshot.version
        else:
            # Create new aggregate
            aggregate = aggregate_class(aggregate_id)
            from_version = 0
        
        # Load remaining events
        events = await self.event_store.get_events(aggregate_id, from_version)
        
        for event in events:
            aggregate.apply_event(event)
            aggregate.version = event.version
        
        return aggregate


class EventProcessor:
    """Event processor for handling projections and event handlers"""
    
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
        self.projections: list[Projection] = []
        self.event_handlers: dict[EventType, list[callable]] = defaultdict(list)
        self.processing = False
    
    def add_projection(self, projection: Projection) -> None:
        """Add a projection to the processor"""
        self.projections.append(projection)
    
    def add_event_handler(self, event_type: EventType, handler: callable) -> None:
        """Add an event handler"""
        self.event_handlers[event_type].append(handler)
    
    async def start_processing(self) -> None:
        """Start processing events"""
        self.processing = True
        
        while self.processing:
            try:
                # Get unprocessed events
                await self._process_unprocessed_events()
                await asyncio.sleep(1)  # Process every second
                
            except Exception as e:
                logger.error(f"Error in event processing: {e}")
                await asyncio.sleep(5)
    
    async def _process_unprocessed_events(self) -> None:
        """Process unprocessed events"""
        # This is a simplified implementation
        # In production, you'd use a proper event stream or message queue
        
        for projection in self.projections:
            # Get latest events for each projection
            events = await self.event_store.get_events_by_type(EventType.IDEA_CREATED, limit=10)
            
            for event in events:
                await projection.handle(event)
                
                # Call event handlers
                for handler in self.event_handlers.get(event.event_type, []):
                    try:
                        await handler(event)
                    except Exception as e:
                        logger.error(f"Error in event handler: {e}")
    
    def stop_processing(self) -> None:
        """Stop event processing"""
        self.processing = False


# Example usage
async def example_usage():
    """Example of event sourcing usage"""
    
    # Initialize components
    event_store = EventStore()
    repository = EventSourcingRepository(event_store)
    processor = EventProcessor(event_store)
    
    # Add projections
    idea_projection = IdeaProjection()
    mvp_projection = MVPProjection()
    processor.add_projection(idea_projection)
    processor.add_projection(mvp_projection)
    
    # Start event processing
    processing_task = asyncio.create_task(processor.start_processing())
    
    try:
        # Create and work with aggregates
        idea = IdeaAggregate("idea-123")
        idea.create("AI Startup Generator", "Generate AI-powered startups", "AI/ML")
        idea.evaluate(0.85, 0.78, 0.92, "PASS")
        idea.approve()
        
        # Save aggregate
        await repository.save(idea)
        
        # Load aggregate
        loaded_idea = await repository.load(IdeaAggregate, "idea-123")
        print(f"Loaded idea: {loaded_idea.title}, status: {loaded_idea.status}")
        
        # Create MVP
        mvp = MVPAggregate("mvp-456")
        mvp.start("idea-123", "Next.js", "FastAPI")
        mvp.complete_build(3, 0, 5, 2, 180.5)
        mvp.deploy()
        
        await repository.save(mvp)
        
        # Wait for processing
        await asyncio.sleep(2)
        
    finally:
        processor.stop_processing()
        processing_task.cancel()


if __name__ == "__main__":
    asyncio.run(example_usage())
