"""
Real-time Collaboration System for Asmblr
Multi-user workspaces with live editing, chat, and project management
"""

import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import uuid
from collections import defaultdict
import websockets
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

logger = logging.getLogger(__name__)

class CollaborationEventType(Enum):
    """Collaboration event types"""
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    CURSOR_MOVE = "cursor_move"
    TEXT_CHANGE = "text_change"
    SELECTION_CHANGE = "selection_change"
    COMMENT_ADDED = "comment_added"
    COMMENT_RESOLVED = "comment_resolved"
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    FILE_UPLOADED = "file_uploaded"
    STATUS_CHANGED = "status_changed"

class UserRole(Enum):
    """User roles in collaboration"""
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"

@dataclass
class User:
    """Collaboration user"""
    id: str
    name: str
    email: str
    avatar_url: Optional[str]
    role: UserRole
    cursor_position: Optional[Dict[str, Any]] = None
    selection: Optional[Dict[str, Any]] = None
    last_seen: datetime = datetime.now()
    is_online: bool = True

@dataclass
class Workspace:
    """Collaboration workspace"""
    id: str
    name: str
    description: str
    owner_id: str
    project_id: str
    created_at: datetime
    updated_at: datetime
    settings: Dict[str, Any]
    members: List[User]
    is_active: bool = True

@dataclass
class CollaborationEvent:
    """Collaboration event"""
    id: str
    type: CollaborationEventType
    user_id: str
    workspace_id: str
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any]

class RealtimeCollaborationManager:
    """Real-time collaboration manager"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.workspaces: Dict[str, Workspace] = {}
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_workspaces: Dict[str, Set[str]] = defaultdict(set)
        self.event_handlers: Dict[CollaborationEventType, callable] = {}
        
        # Initialize event handlers
        self._initialize_event_handlers()
    
    async def initialize(self):
        """Initialize the collaboration manager"""
        self.redis_client = redis.from_url(self.redis_url)
        logger.info("Real-time collaboration manager initialized")
    
    def _initialize_event_handlers(self):
        """Initialize event handlers"""
        self.event_handlers = {
            CollaborationEventType.USER_JOINED: self._handle_user_joined,
            CollaborationEventType.USER_LEFT: self._handle_user_left,
            CollaborationEventType.CURSOR_MOVE: self._handle_cursor_move,
            CollaborationEventType.TEXT_CHANGE: self._handle_text_change,
            CollaborationEventType.SELECTION_CHANGE: self._handle_selection_change,
            CollaborationEventType.COMMENT_ADDED: self._handle_comment_added,
            CollaborationEventType.COMMENT_RESOLVED: self._handle_comment_resolved,
            CollaborationEventType.TASK_CREATED: self._handle_task_created,
            CollaborationEventType.TASK_UPDATED: self._handle_task_updated,
            CollaborationEventType.FILE_UPLOADED: self._handle_file_uploaded,
            CollaborationEventType.STATUS_CHANGED: self._handle_status_changed
        }
    
    async def create_workspace(self, name: str, description: str, owner_id: str, 
                            project_id: str, settings: Dict[str, Any] = None) -> Workspace:
        """Create a new collaboration workspace"""
        workspace_id = str(uuid.uuid4())
        
        workspace = Workspace(
            id=workspace_id,
            name=name,
            description=description,
            owner_id=owner_id,
            project_id=project_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            settings=settings or {},
            members=[]
        )
        
        # Add owner as admin
        owner_user = User(
            id=owner_id,
            name="Workspace Owner",
            email=f"owner@{workspace_id}.asmblr",
            role=UserRole.OWNER
        )
        workspace.members.append(owner_user)
        
        # Store workspace
        self.workspaces[workspace_id] = workspace
        
        # Store in Redis
        await self._store_workspace(workspace)
        
        logger.info(f"Created workspace {workspace_id} for user {owner_id}")
        return workspace
    
    async def join_workspace(self, user_id: str, workspace_id: str, 
                          websocket: WebSocket, user_info: Dict[str, Any]) -> bool:
        """Join a workspace"""
        try:
            # Get workspace
            workspace = await self._get_workspace(workspace_id)
            if not workspace:
                return False
            
            # Check if user is member
            user_member = next((m for m in workspace.members if m.id == user_id), None)
            if not user_member:
                # Add as viewer by default
                user_member = User(
                    id=user_id,
                    name=user_info.get("name", f"User {user_id}"),
                    email=user_info.get("email", f"{user_id}@asmblr.com"),
                    avatar_url=user_info.get("avatar_url"),
                    role=UserRole.VIEWER
                )
                workspace.members.append(user_member)
            
            # Update user status
            user_member.is_online = True
            user_member.last_seen = datetime.now()
            
            # Store connection
            self.active_connections[user_id] = websocket
            self.user_workspaces[user_id].add(workspace_id)
            
            # Broadcast user joined event
            await self._broadcast_event(
                CollaborationEventType.USER_JOINED,
                user_id,
                workspace_id,
                {
                    "user": asdict(user_member),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Send workspace state to user
            await self._send_workspace_state(user_id, workspace)
            
            logger.info(f"User {user_id} joined workspace {workspace_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error joining workspace: {e}")
            return False
    
    async def leave_workspace(self, user_id: str, workspace_id: str):
        """Leave a workspace"""
        try:
            # Get workspace
            workspace = await self._get_workspace(workspace_id)
            if not workspace:
                return
            
            # Update user status
            user_member = next((m for m in workspace.members if m.id == user_id), None)
            if user_member:
                user_member.is_online = False
                user_member.last_seen = datetime.now()
            
            # Remove connection
            if user_id in self.active_connections:
                del self.active_connections[user_id]
            
            self.user_workspaces[user_id].discard(workspace_id)
            
            # Broadcast user left event
            await self._broadcast_event(
                CollaborationEventType.USER_LEFT,
                user_id,
                workspace_id,
                {
                    "user_id": user_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            logger.info(f"User {user_id} left workspace {workspace_id}")
            
        except Exception as e:
            logger.error(f"Error leaving workspace: {e}")
    
    async def handle_websocket_message(self, user_id: str, message: Dict[str, Any]):
        """Handle WebSocket message"""
        try:
            event_type = CollaborationEventType(message.get("type"))
            workspace_id = message.get("workspace_id")
            data = message.get("data", {})
            
            if not workspace_id:
                return
            
            # Create event
            event = CollaborationEvent(
                id=str(uuid.uuid4()),
                type=event_type,
                user_id=user_id,
                workspace_id=workspace_id,
                timestamp=datetime.now(),
                data=data,
                metadata={}
            )
            
            # Handle event
            handler = self.event_handlers.get(event_type)
            if handler:
                await handler(event)
            
            # Broadcast to other users in workspace
            await self._broadcast_event_to_workspace(
                event_type,
                user_id,
                workspace_id,
                data,
                exclude_user=user_id
            )
            
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
    
    async def _handle_user_joined(self, event: CollaborationEvent):
        """Handle user joined event"""
        # Update workspace in Redis
        await self._store_workspace(await self._get_workspace(event.workspace_id))
    
    async def _handle_user_left(self, event: CollaborationEvent):
        """Handle user left event"""
        # Update workspace in Redis
        await self._store_workspace(await self._get_workspace(event.workspace_id))
    
    async def _handle_cursor_move(self, event: CollaborationEvent):
        """Handle cursor move event"""
        workspace = await self._get_workspace(event.workspace_id)
        if workspace:
            user_member = next((m for m in workspace.members if m.id == event.user_id), None)
            if user_member:
                user_member.cursor_position = event.data
                user_member.last_seen = datetime.now()
    
    async def _handle_text_change(self, event: CollaborationEvent):
        """Handle text change event"""
        # Store text change in Redis
        await self.redis_client.hset(
            f"workspace:{event.workspace_id}:content",
            event.data.get("document_id", "default"),
            json.dumps({
                "content": event.data.get("content"),
                "version": event.data.get("version", 1),
                "timestamp": event.timestamp.isoformat(),
                "user_id": event.user_id
            })
        )
    
    async def _handle_selection_change(self, event: CollaborationEvent):
        """Handle selection change event"""
        workspace = await self._get_workspace(event.workspace_id)
        if workspace:
            user_member = next((m for m in workspace.members if m.id == event.user_id), None)
            if user_member:
                user_member.selection = event.data
    
    async def _handle_comment_added(self, event: CollaborationEvent):
        """Handle comment added event"""
        # Store comment in Redis
        comment_id = str(uuid.uuid4())
        await self.redis_client.hset(
            f"workspace:{event.workspace_id}:comments",
            comment_id,
            json.dumps({
                "id": comment_id,
                "user_id": event.user_id,
                "content": event.data.get("content"),
                "position": event.data.get("position"),
                "resolved": False,
                "timestamp": event.timestamp.isoformat()
            })
        )
        
        # Add to event data
        event.data["comment_id"] = comment_id
    
    async def _handle_comment_resolved(self, event: CollaborationEvent):
        """Handle comment resolved event"""
        comment_id = event.data.get("comment_id")
        if comment_id:
            # Update comment in Redis
            comment_data = await self.redis_client.hget(
                f"workspace:{event.workspace_id}:comments",
                comment_id
            )
            if comment_data:
                comment = json.loads(comment_data)
                comment["resolved"] = True
                comment["resolved_by"] = event.user_id
                comment["resolved_at"] = event.timestamp.isoformat()
                
                await self.redis_client.hset(
                    f"workspace:{event.workspace_id}:comments",
                    comment_id,
                    json.dumps(comment)
                )
    
    async def _handle_task_created(self, event: CollaborationEvent):
        """Handle task created event"""
        task_id = str(uuid.uuid4())
        await self.redis_client.hset(
            f"workspace:{event.workspace_id}:tasks",
            task_id,
            json.dumps({
                "id": task_id,
                "title": event.data.get("title"),
                "description": event.data.get("description"),
                "assignee": event.data.get("assignee"),
                "status": "todo",
                "priority": event.data.get("priority", "medium"),
                "created_by": event.user_id,
                "created_at": event.timestamp.isoformat(),
                "due_date": event.data.get("due_date")
            })
        )
        
        event.data["task_id"] = task_id
    
    async def _handle_task_updated(self, event: CollaborationEvent):
        """Handle task updated event"""
        task_id = event.data.get("task_id")
        if task_id:
            # Update task in Redis
            task_data = await self.redis_client.hget(
                f"workspace:{event.workspace_id}:tasks",
                task_id
            )
            if task_data:
                task = json.loads(task_data)
                task.update(event.data)
                task["updated_by"] = event.user_id
                task["updated_at"] = event.timestamp.isoformat()
                
                await self.redis_client.hset(
                    f"workspace:{event.workspace_id}:tasks",
                    task_id,
                    json.dumps(task)
                )
    
    async def _handle_file_uploaded(self, event: CollaborationEvent):
        """Handle file uploaded event"""
        file_id = str(uuid.uuid4())
        await self.redis_client.hset(
            f"workspace:{event.workspace_id}:files",
            file_id,
            json.dumps({
                "id": file_id,
                "name": event.data.get("name"),
                "size": event.data.get("size"),
                "type": event.data.get("type"),
                "url": event.data.get("url"),
                "uploaded_by": event.user_id,
                "uploaded_at": event.timestamp.isoformat()
            })
        )
        
        event.data["file_id"] = file_id
    
    async def _handle_status_changed(self, event: CollaborationEvent):
        """Handle status changed event"""
        # Update workspace status
        workspace = await self._get_workspace(event.workspace_id)
        if workspace:
            workspace.settings["status"] = event.data.get("status")
            workspace.updated_at = datetime.now()
            await self._store_workspace(workspace)
    
    async def _broadcast_event(self, event_type: CollaborationEventType, user_id: str, 
                              workspace_id: str, data: Dict[str, Any]):
        """Broadcast event to all users in workspace"""
        await self._broadcast_event_to_workspace(event_type, user_id, workspace_id, data)
    
    async def _broadcast_event_to_workspace(self, event_type: CollaborationEventType, 
                                          user_id: str, workspace_id: str, 
                                          data: Dict[str, Any], exclude_user: str = None):
        """Broadcast event to workspace users"""
        workspace = await self._get_workspace(workspace_id)
        if not workspace:
            return
        
        # Create message
        message = {
            "type": event_type.value,
            "user_id": user_id,
            "workspace_id": workspace_id,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to all online users in workspace
        for member in workspace.members:
            if member.is_online and member.id != exclude_user:
                connection = self.active_connections.get(member.id)
                if connection and connection.client_state == WebSocketState.CONNECTED:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        logger.error(f"Error sending message to {member.id}: {e}")
    
    async def _send_workspace_state(self, user_id: str, workspace: Workspace):
        """Send workspace state to user"""
        connection = self.active_connections.get(user_id)
        if not connection:
            return
        
        # Get workspace data
        content_data = await self.redis_client.hgetall(f"workspace:{workspace.id}:content")
        comments_data = await self.redis_client.hgetall(f"workspace:{workspace.id}:comments")
        tasks_data = await self.redis_client.hgetall(f"workspace:{workspace.id}:tasks")
        files_data = await self.redis_client.hgetall(f"workspace:{workspace.id}:files")
        
        state = {
            "type": "workspace_state",
            "workspace": asdict(workspace),
            "content": {k: json.loads(v) for k, v in content_data.items()},
            "comments": {k: json.loads(v) for k, v in comments_data.items()},
            "tasks": {k: json.loads(v) for k, v in tasks_data.items()},
            "files": {k: json.loads(v) for k, v in files_data.items()},
            "online_users": [
                asdict(member) for member in workspace.members if member.is_online
            ]
        }
        
        try:
            await connection.send_json(state)
        except Exception as e:
            logger.error(f"Error sending workspace state: {e}")
    
    async def _get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """Get workspace from cache or Redis"""
        if workspace_id in self.workspaces:
            return self.workspaces[workspace_id]
        
        # Try to get from Redis
        workspace_data = await self.redis_client.get(f"workspace:{workspace_id}")
        if workspace_data:
            workspace_dict = json.loads(workspace_data)
            workspace = Workspace(**workspace_dict)
            self.workspaces[workspace_id] = workspace
            return workspace
        
        return None
    
    async def _store_workspace(self, workspace: Workspace):
        """Store workspace in Redis"""
        workspace_dict = asdict(workspace)
        # Convert datetime to string for JSON serialization
        workspace_dict["created_at"] = workspace.created_at.isoformat()
        workspace_dict["updated_at"] = workspace.updated_at.isoformat()
        
        await self.redis_client.set(
            f"workspace:{workspace.id}",
            json.dumps(workspace_dict),
            ex=86400  # 24 hours
        )
    
    async def get_workspace_members(self, workspace_id: str) -> List[User]:
        """Get workspace members"""
        workspace = await self._get_workspace(workspace_id)
        return workspace.members if workspace else []
    
    async def add_workspace_member(self, workspace_id: str, user_info: Dict[str, Any], 
                                 role: UserRole = UserRole.VIEWER) -> bool:
        """Add member to workspace"""
        workspace = await self._get_workspace(workspace_id)
        if not workspace:
            return False
        
        # Check if user already exists
        existing_member = next((m for m in workspace.members if m.id == user_info["id"]), None)
        if existing_member:
            return False
        
        # Add new member
        new_member = User(
            id=user_info["id"],
            name=user_info.get("name", f"User {user_info['id']}"),
            email=user_info.get("email", f"{user_info['id']}@asmblr.com"),
            avatar_url=user_info.get("avatar_url"),
            role=role
        )
        
        workspace.members.append(new_member)
        await self._store_workspace(workspace)
        
        # Broadcast member added event
        await self._broadcast_event(
            CollaborationEventType.USER_JOINED,
            user_info["id"],
            workspace_id,
            {
                "user": asdict(new_member),
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return True
    
    async def remove_workspace_member(self, workspace_id: str, user_id: str) -> bool:
        """Remove member from workspace"""
        workspace = await self._get_workspace(workspace_id)
        if not workspace:
            return False
        
        # Remove member
        workspace.members = [m for m in workspace.members if m.id != user_id]
        await self._store_workspace(workspace)
        
        # Remove from active connections
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        self.user_workspaces[user_id].discard(workspace_id)
        
        # Broadcast member removed event
        await self._broadcast_event(
            CollaborationEventType.USER_LEFT,
            user_id,
            workspace_id,
            {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return True
    
    async def get_user_workspaces(self, user_id: str) -> List[Workspace]:
        """Get all workspaces for a user"""
        user_workspaces = []
        for workspace_id in self.user_workspaces[user_id]:
            workspace = await self._get_workspace(workspace_id)
            if workspace:
                user_workspaces.append(workspace)
        
        return user_workspaces
    
    async def cleanup_inactive_users(self):
        """Clean up inactive users"""
        timeout = timedelta(minutes=5)
        now = datetime.now()
        
        for workspace_id, workspace in self.workspaces.items():
            inactive_users = []
            
            for member in workspace.members:
                if member.is_online and (now - member.last_seen) > timeout:
                    member.is_online = False
                    inactive_users.append(member.id)
                    
                    # Remove from active connections
                    if member.id in self.active_connections:
                        del self.active_connections[member.id]
            
            if inactive_users:
                await self._store_workspace(workspace)
                
                # Broadcast inactive users left
                for user_id in inactive_users:
                    await self._broadcast_event(
                        CollaborationEventType.USER_LEFT,
                        user_id,
                        workspace_id,
                        {
                            "user_id": user_id,
                            "timestamp": datetime.now().isoformat()
                        }
                    )

# Global collaboration manager
collaboration_manager = RealtimeCollaborationManager()

# WebSocket endpoint
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from app.core.database import get_async_db

router = APIRouter(prefix="/collaboration", tags=["collaboration"])

@router.websocket("/ws/{workspace_id}")
async def websocket_endpoint(websocket: WebSocket, workspace_id: str, user_id: str):
    """WebSocket endpoint for real-time collaboration"""
    await websocket.accept()
    
    try:
        # Get user info from query params or headers
        user_info = {
            "name": websocket.query_params.get("name", f"User {user_id}"),
            "email": websocket.query_params.get("email", f"{user_id}@asmblr.com"),
            "avatar_url": websocket.query_params.get("avatar_url")
        }
        
        # Join workspace
        success = await collaboration_manager.join_workspace(
            user_id, workspace_id, websocket, user_info
        )
        
        if not success:
            await websocket.close(code=4004, reason="Workspace not found")
            return
        
        # Handle messages
        while True:
            try:
                message = await websocket.receive_json()
                await collaboration_manager.handle_websocket_message(user_id, message)
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                break
    
    except WebSocketDisconnect:
        pass
    finally:
        # Leave workspace
        await collaboration_manager.leave_workspace(user_id, workspace_id)

@router.post("/workspaces")
async def create_workspace(
    name: str,
    description: str,
    owner_id: str,
    project_id: str,
    settings: Dict[str, Any] = None
):
    """Create a new workspace"""
    try:
        workspace = await collaboration_manager.create_workspace(
            name, description, owner_id, project_id, settings
        )
        return asdict(workspace)
    except Exception as e:
        logger.error(f"Error creating workspace: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workspaces/{workspace_id}")
async def get_workspace(workspace_id: str):
    """Get workspace details"""
    try:
        workspace = await collaboration_manager._get_workspace(workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        return asdict(workspace)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workspace: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workspaces/{workspace_id}/members")
async def get_workspace_members(workspace_id: str):
    """Get workspace members"""
    try:
        members = await collaboration_manager.get_workspace_members(workspace_id)
        return [asdict(member) for member in members]
    except Exception as e:
        logger.error(f"Error getting workspace members: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workspaces/{workspace_id}/members")
async def add_workspace_member(
    workspace_id: str,
    user_info: Dict[str, Any],
    role: str = "viewer"
):
    """Add member to workspace"""
    try:
        user_role = UserRole(role.lower())
        success = await collaboration_manager.add_workspace_member(
            workspace_id, user_info, user_role
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to add member")
        
        return {"success": True}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")
    except Exception as e:
        logger.error(f"Error adding workspace member: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/workspaces/{workspace_id}/members/{user_id}")
async def remove_workspace_member(workspace_id: str, user_id: str):
    """Remove member from workspace"""
    try:
        success = await collaboration_manager.remove_workspace_member(workspace_id, user_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to remove member")
        
        return {"success": True}
    except Exception as e:
        logger.error(f"Error removing workspace member: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}/workspaces")
async def get_user_workspaces(user_id: str):
    """Get user's workspaces"""
    try:
        workspaces = await collaboration_manager.get_user_workspaces(user_id)
        return [asdict(workspace) for workspace in workspaces]
    except Exception as e:
        logger.error(f"Error getting user workspaces: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task for cleanup
async def cleanup_inactive_users_task():
    """Background task to clean up inactive users"""
    while True:
        try:
            await collaboration_manager.cleanup_inactive_users()
            await asyncio.sleep(300)  # Run every 5 minutes
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
            await asyncio.sleep(60)  # Wait 1 minute on error
