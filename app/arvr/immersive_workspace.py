"""
AR/VR Immersive Workspace for Asmblr
Virtual reality collaboration, 3D visualization, and spatial computing
"""

import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import uuid
import numpy as np
from scipy.spatial.transform import Rotation
import websockets
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

class DeviceType(Enum):
    """AR/VR device types"""
    QUEST_2 = "quest_2"
    QUEST_3 = "quest_3"
    QUEST_PRO = "quest_pro"
    HOLONENS = "hololens"
    MAGIC_LEAP = "magic_leap"
    IPHONE_AR = "iphone_ar"
    ANDROID_AR = "android_ar"
    WEB_VR = "web_vr"
    WEB_AR = "web_ar"

class InteractionMode(Enum):
    """Interaction modes"""
    GAZE = "gaze"
    CONTROLLER = "controller"
    HAND_TRACKING = "hand_tracking"
    VOICE = "voice"
    GESTURE = "gesture"
    TOUCH = "touch"

class WorkspaceType(Enum):
    """Workspace types"""
    COLLABORATION_ROOM = "collaboration_room"
    DESIGN_STUDIO = "design_studio"
    MEETING_ROOM = "meeting_room"
    PRESENTATION_HALL = "presentation_hall"
    CODING_SPACE = "coding_space"
    DATA_VISUALIZATION = "data_visualization"
    TRAINING_ROOM = "training_room"
    SHOWCASE = "showcase"

@dataclass
class Vector3:
    """3D vector"""
    x: float
    y: float
    z: float
    
    def __add__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other: 'Vector3') -> 'Vector3':
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, scalar: float) -> 'Vector3':
        return Vector3(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def magnitude(self) -> float:
        return np.sqrt(self.x**2 + self.y**2 + self.z**2)
    
    def normalize(self) -> 'Vector3':
        mag = self.magnitude()
        if mag > 0:
            return Vector3(self.x/mag, self.y/mag, self.z/mag)
        return Vector3(0, 0, 0)

@dataclass
class Quaternion:
    """Quaternion for rotation"""
    x: float
    y: float
    z: float
    w: float
    
    def to_euler(self) -> Tuple[float, float, float]:
        """Convert to Euler angles"""
        rotation = Rotation([self.x, self.y, self.z, self.w])
        return rotation.as_euler('xyz')
    
    @staticmethod
    def from_euler(roll: float, pitch: float, yaw: float) -> 'Quaternion':
        """Create from Euler angles"""
        rotation = Rotation.from_euler('xyz', [roll, pitch, yaw])
        quat = rotation.as_quat()
        return Quaternion(quat[0], quat[1], quat[2], quat[3])

@dataclass
class Transform:
    """3D transform"""
    position: Vector3
    rotation: Quaternion
    scale: Vector3
    
    def to_matrix(self) -> np.ndarray:
        """Convert to 4x4 transformation matrix"""
        # Create translation matrix
        translation = np.array([
            [1, 0, 0, self.position.x],
            [0, 1, 0, self.position.y],
            [0, 0, 1, self.position.z],
            [0, 0, 0, 1]
        ])
        
        # Create rotation matrix
        rotation = Rotation([self.rotation.x, self.rotation.y, self.rotation.z, self.rotation.w])
        rotation_matrix = rotation.as_matrix()
        rotation_4x4 = np.eye(4)
        rotation_4x4[:3, :3] = rotation_matrix
        
        # Create scale matrix
        scale = np.array([
            [self.scale.x, 0, 0, 0],
            [0, self.scale.y, 0, 0],
            [0, 0, self.scale.z, 0],
            [0, 0, 0, 1]
        ])
        
        return translation @ rotation_4x4 @ scale

@dataclass
class VRUser:
    """VR user in workspace"""
    id: str
    name: str
    device_type: DeviceType
    avatar_url: str
    transform: Transform
    interaction_mode: InteractionMode
    is_active: bool
    joined_at: datetime
    last_seen: datetime
    hand_positions: Dict[str, Vector3]  # left, right
    gaze_direction: Vector3
    voice_channel: Optional[str] = None

@dataclass
class VirtualObject:
    """Virtual object in workspace"""
    id: str
    name: str
    object_type: str
    transform: Transform
    properties: Dict[str, Any]
    interactive: bool
    physics_enabled: bool
    created_by: str
    created_at: datetime
    last_modified: datetime

@dataclass
class ARWorkspace:
    """AR/VR workspace"""
    id: str
    name: str
    workspace_type: WorkspaceType
    description: str
    max_users: int
    current_users: List[VRUser]
    objects: List[VirtualObject]
    environment: Dict[str, Any]
    is_public: bool
    created_by: str
    created_at: datetime
    settings: Dict[str, Any]

class ARVRManager:
    """AR/VR workspace manager"""
    
    def __init__(self):
        self.workspaces: Dict[str, ARWorkspace] = {}
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_workspaces: Dict[str, Set[str]] = {}
        self.spatial_audio_manager = SpatialAudioManager()
        self.physics_engine = PhysicsEngine()
        self.gesture_recognizer = GestureRecognizer()
        
        # Initialize default environments
        self._initialize_environments()
    
    def _initialize_environments(self):
        """Initialize default VR environments"""
        self.environments = {
            "modern_office": {
                "name": "Modern Office",
                "skybox": "textures/skybox_office.jpg",
                "lighting": {
                    "ambient": 0.3,
                    "directional": {
                        "intensity": 0.8,
                        "direction": [0.5, -0.8, 0.3],
                        "color": [1.0, 0.95, 0.9]
                    }
                },
                "audio": {
                    "reverb": "office",
                    "background_music": "ambient_office.mp3"
                },
                "physics": {
                    "gravity": Vector3(0, -9.81, 0),
                    "air_resistance": 0.1
                }
            },
            "space_station": {
                "name": "Space Station",
                "skybox": "textures/skybox_space.jpg",
                "lighting": {
                    "ambient": 0.1,
                    "directional": {
                        "intensity": 1.0,
                        "direction": [0.0, -1.0, 0.0],
                        "color": [1.0, 1.0, 0.8]
                    }
                },
                "audio": {
                    "reverb": "space",
                    "background_music": "ambient_space.mp3"
                },
                "physics": {
                    "gravity": Vector3(0, 0, 0),
                    "air_resistance": 0.0
                }
            },
            "nature_forest": {
                "name": "Forest",
                "skybox": "textures/skybox_forest.jpg",
                "lighting": {
                    "ambient": 0.4,
                    "directional": {
                        "intensity": 0.6,
                        "direction": [0.3, -0.9, 0.2],
                        "color": [1.0, 0.9, 0.7]
                    }
                },
                "audio": {
                    "reverb": "outdoor",
                    "background_music": "ambient_forest.mp3"
                },
                "physics": {
                    "gravity": Vector3(0, -9.81, 0),
                    "air_resistance": 0.2
                }
            }
        }
    
    async def create_workspace(self, name: str, workspace_type: WorkspaceType,
                            description: str, max_users: int = 10,
                            environment: str = "modern_office",
                            created_by: str = "system") -> ARWorkspace:
        """Create new AR/VR workspace"""
        try:
            workspace_id = str(uuid.uuid4())
            
            workspace = ARWorkspace(
                id=workspace_id,
                name=name,
                workspace_type=workspace_type,
                description=description,
                max_users=max_users,
                current_users=[],
                objects=[],
                environment=self.environments.get(environment, self.environments["modern_office"]),
                is_public=True,
                created_by=created_by,
                created_at=datetime.now(),
                settings={
                    "allow_voice_chat": True,
                    "enable_physics": True,
                    "spatial_audio": True,
                    "hand_tracking": True,
                    "gesture_recognition": True
                }
            )
            
            # Add default objects based on workspace type
            await self._add_default_objects(workspace)
            
            self.workspaces[workspace_id] = workspace
            
            logger.info(f"Created AR/VR workspace: {name}")
            return workspace
            
        except Exception as e:
            logger.error(f"Error creating workspace: {e}")
            raise
    
    async def _add_default_objects(self, workspace: ARWorkspace):
        """Add default objects to workspace"""
        try:
            if workspace.workspace_type == WorkspaceType.COLLABORATION_ROOM:
                # Add collaboration table
                table = VirtualObject(
                    id=str(uuid.uuid4()),
                    name="Collaboration Table",
                    object_type="table",
                    transform=Transform(
                        position=Vector3(0, 0, 0),
                        rotation=Quaternion(0, 0, 0, 1),
                        scale=Vector3(2, 0.1, 1)
                    ),
                    properties={
                        "material": "wood",
                        "interactive": True,
                        "screen": True
                    },
                    interactive=True,
                    physics_enabled=True,
                    created_by="system",
                    created_at=datetime.now(),
                    last_modified=datetime.now()
                )
                workspace.objects.append(table)
                
                # Add chairs
                for i, pos in enumerate([(-1, 0, 0.5), (1, 0, 0.5), (-1, 0, -0.5), (1, 0, -0.5)]):
                    chair = VirtualObject(
                        id=str(uuid.uuid4()),
                        name=f"Chair {i+1}",
                        object_type="chair",
                        transform=Transform(
                            position=Vector3(pos[0], 0, pos[1]),
                            rotation=Quaternion(0, 0, 0, 1),
                            scale=Vector3(0.5, 1, 0.5)
                        ),
                        properties={
                            "material": "fabric",
                            "interactive": True,
                            "movable": True
                        },
                        interactive=True,
                        physics_enabled=True,
                        created_by="system",
                        created_at=datetime.now(),
                        last_modified=datetime.now()
                    )
                    workspace.objects.append(chair)
            
            elif workspace.workspace_type == WorkspaceType.DESIGN_STUDIO:
                # Add 3D modeling tools
                modeling_table = VirtualObject(
                    id=str(uuid.uuid4()),
                    name="3D Modeling Table",
                    object_type="modeling_table",
                    transform=Transform(
                        position=Vector3(0, 0.8, -1),
                        rotation=Quaternion(0, 0, 0, 1),
                        scale=Vector3(1.5, 0.05, 1)
                    ),
                    properties={
                        "interactive": True,
                        "touch_enabled": True,
                        "holographic": True
                    },
                    interactive=True,
                    physics_enabled=False,
                    created_by="system",
                    created_at=datetime.now(),
                    last_modified=datetime.now()
                )
                workspace.objects.append(modeling_table)
                
                # Add material palette
                palette = VirtualObject(
                    id=str(uuid.uuid4()),
                    name="Material Palette",
                    object_type="palette",
                    transform=Transform(
                        position=Vector3(1.5, 1, 0),
                        rotation=Quaternion(0, 0.707, 0, 0.707),
                        scale=Vector3(0.8, 0.1, 0.6)
                    ),
                    properties={
                        "interactive": True,
                        "materials": ["wood", "metal", "plastic", "glass", "fabric"],
                        "color_picker": True
                    },
                    interactive=True,
                    physics_enabled=False,
                    created_by="system",
                    created_at=datetime.now(),
                    last_modified=datetime.now()
                )
                workspace.objects.append(palette)
            
            elif workspace.workspace_type == WorkspaceType.DATA_VISUALIZATION:
                # Add data visualization sphere
                data_sphere = VirtualObject(
                    id=str(uuid.uuid4()),
                    name="Data Visualization Sphere",
                    object_type="data_sphere",
                    transform=Transform(
                        position=Vector3(0, 2, 0),
                        rotation=Quaternion(0, 0, 0, 1),
                        scale=Vector3(3, 3, 3)
                    ),
                    properties={
                        "interactive": True,
                        "data_source": "analytics",
                        "real_time": True,
                        "3d_charts": True
                    },
                    interactive=True,
                    physics_enabled=False,
                    created_by="system",
                    created_at=datetime.now(),
                    last_modified=datetime.now()
                )
                workspace.objects.append(data_sphere)
                
                # Add control panel
                control_panel = VirtualObject(
                    id=str(uuid.uuid4()),
                    name="Control Panel",
                    object_type="control_panel",
                    transform=Transform(
                        position=Vector3(0, 1, 2),
                        rotation=Quaternion(0, 1, 0, 0),
                        scale=Vector3(2, 1, 0.1)
                    ),
                    properties={
                        "interactive": True,
                        "touch_enabled": True,
                        "controls": ["filter", "time_range", "chart_type", "export"]
                    },
                    interactive=True,
                    physics_enabled=False,
                    created_by="system",
                    created_at=datetime.now(),
                    last_modified=datetime.now()
                )
                workspace.objects.append(control_panel)
            
        except Exception as e:
            logger.error(f"Error adding default objects: {e}")
    
    async def join_workspace(self, user_id: str, workspace_id: str, 
                          websocket: WebSocket, user_info: Dict[str, Any]) -> bool:
        """Join AR/VR workspace"""
        try:
            workspace = self.workspaces.get(workspace_id)
            if not workspace:
                return False
            
            if len(workspace.current_users) >= workspace.max_users:
                return False
            
            # Create VR user
            user = VRUser(
                id=user_id,
                name=user_info.get("name", f"User {user_id}"),
                device_type=DeviceType(user_info.get("device_type", "web_vr")),
                avatar_url=user_info.get("avatar_url", "/avatars/default.png"),
                transform=Transform(
                    position=Vector3(0, 1.6, 2),  # Default standing position
                    rotation=Quaternion(0, 0, 0, 1),
                    scale=Vector3(1, 1, 1)
                ),
                interaction_mode=InteractionMode(user_info.get("interaction_mode", "controller")),
                is_active=True,
                joined_at=datetime.now(),
                last_seen=datetime.now(),
                hand_positions={"left": Vector3(0, 0, 0), "right": Vector3(0, 0, 0)},
                gaze_direction=Vector3(0, 0, -1),
                voice_channel=f"voice_{workspace_id}_{user_id}"
            )
            
            # Add user to workspace
            workspace.current_users.append(user)
            
            # Store connection
            self.active_connections[user_id] = websocket
            self.user_workspaces[user_id] = {workspace_id}
            
            # Send workspace state to user
            await self._send_workspace_state(user_id, workspace)
            
            # Broadcast user joined to others
            await self._broadcast_user_event(workspace_id, "user_joined", {
                "user": asdict(user),
                "timestamp": datetime.now().isoformat()
            }, exclude_user=user_id)
            
            # Initialize spatial audio
            if workspace.settings.get("spatial_audio", True):
                await self.spatial_audio_manager.add_user_to_room(user_id, workspace_id, user.transform.position)
            
            logger.info(f"User {user_id} joined AR/VR workspace {workspace_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error joining workspace: {e}")
            return False
    
    async def leave_workspace(self, user_id: str, workspace_id: str):
        """Leave AR/VR workspace"""
        try:
            workspace = self.workspaces.get(workspace_id)
            if not workspace:
                return
            
            # Remove user from workspace
            workspace.current_users = [u for u in workspace.current_users if u.id != user_id]
            
            # Remove connection
            if user_id in self.active_connections:
                del self.active_connections[user_id]
            
            self.user_workspaces[user_id].discard(workspace_id)
            
            # Remove from spatial audio
            await self.spatial_audio_manager.remove_user_from_room(user_id, workspace_id)
            
            # Broadcast user left
            await self._broadcast_user_event(workspace_id, "user_left", {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"User {user_id} left AR/VR workspace {workspace_id}")
            
        except Exception as e:
            logger.error(f"Error leaving workspace: {e}")
    
    async def update_user_transform(self, user_id: str, workspace_id: str, 
                                  transform_data: Dict[str, Any]) -> bool:
        """Update user transform in workspace"""
        try:
            workspace = self.workspaces.get(workspace_id)
            if not workspace:
                return False
            
            # Find user
            user = next((u for u in workspace.current_users if u.id == user_id), None)
            if not user:
                return False
            
            # Update transform
            user.transform = Transform(
                position=Vector3(
                    transform_data.get("position", {}).get("x", 0),
                    transform_data.get("position", {}).get("y", 0),
                    transform_data.get("position", {}).get("z", 0)
                ),
                rotation=Quaternion(
                    transform_data.get("rotation", {}).get("x", 0),
                    transform_data.get("rotation", {}).get("y", 0),
                    transform_data.get("rotation", {}).get("z", 0),
                    transform_data.get("rotation", {}).get("w", 1)
                ),
                scale=Vector3(
                    transform_data.get("scale", {}).get("x", 1),
                    transform_data.get("scale", {}).get("y", 1),
                    transform_data.get("scale", {}).get("z", 1)
                )
            )
            
            # Update hand positions if provided
            if "hand_positions" in transform_data:
                hand_data = transform_data["hand_positions"]
                user.hand_positions = {
                    "left": Vector3(
                        hand_data.get("left", {}).get("x", 0),
                        hand_data.get("left", {}).get("y", 0),
                        hand_data.get("left", {}).get("z", 0)
                    ),
                    "right": Vector3(
                        hand_data.get("right", {}).get("x", 0),
                        hand_data.get("right", {}).get("y", 0),
                        hand_data.get("right", {}).get("z", 0)
                    )
                }
            
            # Update gaze direction
            if "gaze_direction" in transform_data:
                gaze = transform_data["gaze_direction"]
                user.gaze_direction = Vector3(gaze.get("x", 0), gaze.get("y", 0), gaze.get("z", -1))
            
            user.last_seen = datetime.now()
            
            # Update spatial audio position
            if workspace.settings.get("spatial_audio", True):
                await self.spatial_audio_manager.update_user_position(user_id, user.transform.position)
            
            # Broadcast transform update to others
            await self._broadcast_user_event(workspace_id, "user_transform", {
                "user_id": user_id,
                "transform": asdict(user.transform),
                "hand_positions": {k: asdict(v) for k, v in user.hand_positions.items()},
                "gaze_direction": asdict(user.gaze_direction),
                "timestamp": datetime.now().isoformat()
            }, exclude_user=user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating user transform: {e}")
            return False
    
    async def interact_with_object(self, user_id: str, workspace_id: str,
                                 object_id: str, interaction_type: str,
                                 interaction_data: Dict[str, Any]) -> bool:
        """Handle object interaction"""
        try:
            workspace = self.workspaces.get(workspace_id)
            if not workspace:
                return False
            
            # Find object
            obj = next((o for o in workspace.objects if o.id == object_id), None)
            if not obj or not obj.interactive:
                return False
            
            # Process interaction
            result = await self._process_object_interaction(obj, user_id, interaction_type, interaction_data)
            
            # Broadcast interaction to others
            await self._broadcast_object_event(workspace_id, "object_interaction", {
                "user_id": user_id,
                "object_id": object_id,
                "interaction_type": interaction_type,
                "interaction_data": interaction_data,
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling object interaction: {e}")
            return False
    
    async def _process_object_interaction(self, obj: VirtualObject, user_id: str,
                                         interaction_type: str, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process specific object interaction"""
        try:
            result = {"success": True, "message": "Interaction processed"}
            
            if obj.object_type == "table" and interaction_type == "touch":
                # Table surface interaction - show holographic interface
                if obj.properties.get("screen", False):
                    result.update({
                        "action": "show_holographic_screen",
                        "content": "collaboration_interface",
                        "position": interaction_data.get("position", {"x": 0, "y": 0, "z": 0})
                    })
            
            elif obj.object_type == "modeling_table" and interaction_type == "gesture":
                # 3D modeling gesture
                gesture = interaction_data.get("gesture", "draw")
                if gesture == "draw":
                    result.update({
                        "action": "create_3d_stroke",
                        "points": interaction_data.get("points", []),
                        "material": interaction_data.get("material", "default")
                    })
            
            elif obj.object_type == "data_sphere" and interaction_type == "grab":
                # Data visualization manipulation
                result.update({
                    "action": "rotate_data",
                    "rotation": interaction_data.get("rotation", {"x": 0, "y": 0, "z": 0}),
                    "zoom": interaction_data.get("zoom", 1.0)
                })
            
            elif obj.object_type == "control_panel" and interaction_type == "touch":
                # Control panel button press
                button = interaction_data.get("button", "")
                result.update({
                    "action": "control_pressed",
                    "button": button,
                    "value": interaction_data.get("value", None)
                })
            
            # Update object last modified
            obj.last_modified = datetime.now()
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing object interaction: {e}")
            return {"success": False, "error": str(e)}
    
    async def add_virtual_object(self, user_id: str, workspace_id: str,
                               object_data: Dict[str, Any]) -> Optional[str]:
        """Add virtual object to workspace"""
        try:
            workspace = self.workspaces.get(workspace_id)
            if not workspace:
                return None
            
            # Create virtual object
            obj = VirtualObject(
                id=str(uuid.uuid4()),
                name=object_data.get("name", "New Object"),
                object_type=object_data.get("object_type", "generic"),
                transform=Transform(
                    position=Vector3(
                        object_data.get("position", {}).get("x", 0),
                        object_data.get("position", {}).get("y", 0),
                        object_data.get("position", {}).get("z", 0)
                    ),
                    rotation=Quaternion(
                        object_data.get("rotation", {}).get("x", 0),
                        object_data.get("rotation", {}).get("y", 0),
                        object_data.get("rotation", {}).get("z", 0),
                        object_data.get("rotation", {}).get("w", 1)
                    ),
                    scale=Vector3(
                        object_data.get("scale", {}).get("x", 1),
                        object_data.get("scale", {}).get("y", 1),
                        object_data.get("scale", {}).get("z", 1)
                    )
                ),
                properties=object_data.get("properties", {}),
                interactive=object_data.get("interactive", True),
                physics_enabled=object_data.get("physics_enabled", True),
                created_by=user_id,
                created_at=datetime.now(),
                last_modified=datetime.now()
            )
            
            # Add to workspace
            workspace.objects.append(obj)
            
            # Broadcast object addition
            await self._broadcast_object_event(workspace_id, "object_added", {
                "object": asdict(obj),
                "created_by": user_id,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"Added virtual object {obj.id} to workspace {workspace_id}")
            return obj.id
            
        except Exception as e:
            logger.error(f"Error adding virtual object: {e}")
            return None
    
    async def _send_workspace_state(self, user_id: str, workspace: ARWorkspace):
        """Send complete workspace state to user"""
        try:
            connection = self.active_connections.get(user_id)
            if not connection:
                return
            
            state = {
                "type": "workspace_state",
                "workspace": {
                    "id": workspace.id,
                    "name": workspace.name,
                    "type": workspace.workspace_type.value,
                    "environment": workspace.environment,
                    "settings": workspace.settings
                },
                "users": [asdict(user) for user in workspace.current_users],
                "objects": [asdict(obj) for obj in workspace.objects],
                "timestamp": datetime.now().isoformat()
            }
            
            await connection.send_json(state)
            
        except Exception as e:
            logger.error(f"Error sending workspace state: {e}")
    
    async def _broadcast_user_event(self, workspace_id: str, event_type: str,
                                  data: Dict[str, Any], exclude_user: str = None):
        """Broadcast user event to workspace"""
        try:
            workspace = self.workspaces.get(workspace_id)
            if not workspace:
                return
            
            message = {
                "type": event_type,
                "workspace_id": workspace_id,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send to all users in workspace
            for user in workspace.current_users:
                if user.id != exclude_user:
                    connection = self.active_connections.get(user.id)
                    if connection:
                        try:
                            await connection.send_json(message)
                        except Exception as e:
                            logger.error(f"Error sending to user {user.id}: {e}")
            
        except Exception as e:
            logger.error(f"Error broadcasting user event: {e}")
    
    async def _broadcast_object_event(self, workspace_id: str, event_type: str,
                                   data: Dict[str, Any]):
        """Broadcast object event to workspace"""
        try:
            workspace = self.workspaces.get(workspace_id)
            if not workspace:
                return
            
            message = {
                "type": event_type,
                "workspace_id": workspace_id,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send to all users in workspace
            for user in workspace.current_users:
                connection = self.active_connections.get(user.id)
                if connection:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        logger.error(f"Error sending to user {user.id}: {e}")
            
        except Exception as e:
            logger.error(f"Error broadcasting object event: {e}")

class SpatialAudioManager:
    """Spatial audio management for VR"""
    
    def __init__(self):
        self.rooms: Dict[str, Dict[str, Any]] = {}
        self.user_positions: Dict[str, Vector3] = {}
    
    async def add_user_to_room(self, user_id: str, room_id: str, position: Vector3):
        """Add user to spatial audio room"""
        if room_id not in self.rooms:
            self.rooms[room_id] = {"users": set(), "audio_sources": {}}
        
        self.rooms[room_id]["users"].add(user_id)
        self.user_positions[user_id] = position
    
    async def remove_user_from_room(self, user_id: str, room_id: str):
        """Remove user from spatial audio room"""
        if room_id in self.rooms:
            self.rooms[room_id]["users"].discard(user_id)
        
        if user_id in self.user_positions:
            del self.user_positions[user_id]
    
    async def update_user_position(self, user_id: str, position: Vector3):
        """Update user position for spatial audio"""
        self.user_positions[user_id] = position
    
    async def calculate_audio_mix(self, room_id: str, user_id: str) -> Dict[str, float]:
        """Calculate spatial audio mix for user"""
        if room_id not in self.rooms or user_id not in self.user_positions:
            return {}
        
        user_pos = self.user_positions[user_id]
        audio_mix = {}
        
        for other_user_id in self.rooms[room_id]["users"]:
            if other_user_id != user_id and other_user_id in self.user_positions:
                other_pos = self.user_positions[other_user_id]
                
                # Calculate distance and direction
                distance = (other_pos - user_pos).magnitude()
                direction = (other_pos - user_pos).normalize()
                
                # Calculate volume based on distance (inverse square law)
                if distance > 0.1:  # Avoid division by zero
                    volume = min(1.0, 1.0 / (distance ** 2))
                else:
                    volume = 1.0
                
                # Calculate panning based on direction
                pan = 0.5 + (direction.x * 0.5)  # Map to 0-1 range
                
                audio_mix[other_user_id] = {
                    "volume": volume,
                    "pan": pan,
                    "distance": distance
                }
        
        return audio_mix

class PhysicsEngine:
    """Simple physics engine for VR objects"""
    
    def __init__(self):
        self.gravity = Vector3(0, -9.81, 0)
        self.objects: Dict[str, Dict[str, Any]] = {}
    
    async def add_object(self, object_id: str, transform: Transform, 
                        physics_enabled: bool = True):
        """Add object to physics simulation"""
        self.objects[object_id] = {
            "transform": transform,
            "velocity": Vector3(0, 0, 0),
            "acceleration": Vector3(0, 0, 0),
            "mass": 1.0,
            "physics_enabled": physics_enabled,
            "collider": {
                "type": "box",
                "size": transform.scale
            }
        }
    
    async def update_physics(self, delta_time: float):
        """Update physics simulation"""
        for object_id, obj in self.objects.items():
            if not obj["physics_enabled"]:
                continue
            
            # Apply gravity
            obj["acceleration"] = self.gravity
            
            # Update velocity
            obj["velocity"] = obj["velocity"] + (obj["acceleration"] * delta_time)
            
            # Update position
            obj["transform"].position = obj["transform"].position + (obj["velocity"] * delta_time)
            
            # Simple collision with ground
            if obj["transform"].position.y < 0:
                obj["transform"].position.y = 0
                obj["velocity"].y = -obj["velocity"].y * 0.5  # Bounce with damping
    
    async def check_collisions(self) -> List[Tuple[str, str]]:
        """Check for collisions between objects"""
        collisions = []
        object_ids = list(self.objects.keys())
        
        for i in range(len(object_ids)):
            for j in range(i + 1, len(object_ids)):
                obj1 = self.objects[object_ids[i]]
                obj2 = self.objects[object_ids[j]]
                
                if self._check_collision(obj1, obj2):
                    collisions.append((object_ids[i], object_ids[j]))
        
        return collisions
    
    def _check_collision(self, obj1: Dict[str, Any], obj2: Dict[str, Any]) -> bool:
        """Check collision between two objects"""
        # Simple AABB collision detection
        pos1 = obj1["transform"].position
        scale1 = obj1["transform"].scale
        pos2 = obj2["transform"].position
        scale2 = obj2["transform"].scale
        
        return (abs(pos1.x - pos2.x) < (scale1.x + scale2.x) / 2 and
                abs(pos1.y - pos2.y) < (scale1.y + scale2.y) / 2 and
                abs(pos1.z - pos2.z) < (scale1.z + scale2.z) / 2)

class GestureRecognizer:
    """Hand gesture recognition for VR"""
    
    def __init__(self):
        self.gestures = {
            "point": self._recognize_point,
            "grab": self._recognize_grab,
            "thumbs_up": self._recognize_thumbs_up,
            "wave": self._recognize_wave,
            "pinch": self._recognize_pinch
        }
    
    async def recognize_gesture(self, hand_positions: Dict[str, Vector3],
                              hand_rotations: Dict[str, Quaternion]) -> Optional[str]:
        """Recognize hand gesture"""
        try:
            for gesture_name, recognizer in self.gestures.items():
                if await recognizer(hand_positions, hand_rotations):
                    return gesture_name
            
            return None
            
        except Exception as e:
            logger.error(f"Error recognizing gesture: {e}")
            return None
    
    async def _recognize_point(self, hand_positions: Dict[str, Vector3],
                            hand_rotations: Dict[str, Quaternion]) -> bool:
        """Recognize pointing gesture"""
        # Simplified: check if index finger is extended
        # In real implementation, would use detailed hand tracking data
        return True
    
    async def _recognize_grab(self, hand_positions: Dict[str, Vector3],
                            hand_rotations: Dict[str, Quaternion]) -> bool:
        """Recognize grab gesture"""
        # Simplified: check if hand is closed
        return False
    
    async def _recognize_thumbs_up(self, hand_positions: Dict[str, Vector3],
                                 hand_rotations: Dict[str, Quaternion]) -> bool:
        """Recognize thumbs up gesture"""
        return False
    
    async def _recognize_wave(self, hand_positions: Dict[str, Vector3],
                            hand_rotations: Dict[str, Quaternion]) -> bool:
        """Recognize wave gesture"""
        return False
    
    async def _recognize_pinch(self, hand_positions: Dict[str, Vector3],
                             hand_rotations: Dict[str, Quaternion]) -> bool:
        """Recognize pinch gesture"""
        return False

# Global AR/VR manager
arvr_manager = ARVRManager()

# API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/arvr", tags=["arvr"])

class WorkspaceRequest(BaseModel):
    name: str
    workspace_type: str
    description: str
    max_users: int = 10
    environment: str = "modern_office"
    created_by: str = "system"

class JoinWorkspaceRequest(BaseModel):
    user_id: str
    workspace_id: str
    user_info: Dict[str, Any]

class TransformUpdateRequest(BaseModel):
    user_id: str
    workspace_id: str
    transform: Dict[str, Any]

class ObjectInteractionRequest(BaseModel):
    user_id: str
    workspace_id: str
    object_id: str
    interaction_type: str
    interaction_data: Dict[str, Any]

class AddObjectRequest(BaseModel):
    user_id: str
    workspace_id: str
    object_data: Dict[str, Any]

@router.post("/workspaces")
async def create_workspace(request: WorkspaceRequest):
    """Create AR/VR workspace"""
    try:
        workspace_type = WorkspaceType(request.workspace_type)
        
        workspace = await arvr_manager.create_workspace(
            request.name,
            workspace_type,
            request.description,
            request.max_users,
            request.environment,
            request.created_by
        )
        
        return asdict(workspace)
    except Exception as e:
        logger.error(f"Error creating workspace: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workspaces/{workspace_id}")
async def get_workspace(workspace_id: str):
    """Get AR/VR workspace"""
    try:
        workspace = arvr_manager.workspaces.get(workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
        
        return asdict(workspace)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workspace: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/workspaces/join")
async def join_workspace(request: JoinWorkspaceRequest, websocket: WebSocket):
    """Join AR/VR workspace"""
    await websocket.accept()
    
    try:
        success = await arvr_manager.join_workspace(
            request.user_id,
            request.workspace_id,
            websocket,
            request.user_info
        )
        
        if not success:
            await websocket.close(code=4004, reason="Failed to join workspace")
            return
        
        # Handle WebSocket messages
        while True:
            try:
                message = await websocket.receive_json()
                
                if message.get("type") == "transform_update":
                    await arvr_manager.update_user_transform(
                        request.user_id,
                        request.workspace_id,
                        message.get("transform", {})
                    )
                elif message.get("type") == "object_interaction":
                    await arvr_manager.interact_with_object(
                        request.user_id,
                        request.workspace_id,
                        message.get("object_id"),
                        message.get("interaction_type"),
                        message.get("interaction_data", {})
                    )
                elif message.get("type") == "add_object":
                    object_id = await arvr_manager.add_virtual_object(
                        request.user_id,
                        request.workspace_id,
                        message.get("object_data", {})
                    )
                    await websocket.send_json({
                        "type": "object_added",
                        "object_id": object_id
                    })
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                break
    
    except WebSocketDisconnect:
        pass
    finally:
        await arvr_manager.leave_workspace(request.user_id, request.workspace_id)

@router.post("/transform/update")
async def update_transform(request: TransformUpdateRequest):
    """Update user transform"""
    try:
        success = await arvr_manager.update_user_transform(
            request.user_id,
            request.workspace_id,
            request.transform
        )
        
        return {"success": success}
    except Exception as e:
        logger.error(f"Error updating transform: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/objects/interact")
async def interact_with_object(request: ObjectInteractionRequest):
    """Interact with virtual object"""
    try:
        success = await arvr_manager.interact_with_object(
            request.user_id,
            request.workspace_id,
            request.object_id,
            request.interaction_type,
            request.interaction_data
        )
        
        return {"success": success}
    except Exception as e:
        logger.error(f"Error interacting with object: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/objects/add")
async def add_virtual_object(request: AddObjectRequest):
    """Add virtual object to workspace"""
    try:
        object_id = await arvr_manager.add_virtual_object(
            request.user_id,
            request.workspace_id,
            request.object_data
        )
        
        return {"success": True, "object_id": object_id}
    except Exception as e:
        logger.error(f"Error adding virtual object: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workspaces")
async def list_workspaces():
    """List all AR/VR workspaces"""
    try:
        workspaces = []
        for workspace in arvr_manager.workspaces.values():
            workspaces.append({
                "id": workspace.id,
                "name": workspace.name,
                "type": workspace.workspace_type.value,
                "current_users": len(workspace.current_users),
                "max_users": workspace.max_users,
                "is_public": workspace.is_public,
                "created_at": workspace.created_at.isoformat()
            })
        
        return workspaces
    except Exception as e:
        logger.error(f"Error listing workspaces: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/environments")
async def get_environments():
    """Get available VR environments"""
    try:
        return arvr_manager.environments
    except Exception as e:
        logger.error(f"Error getting environments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/devices")
async def get_supported_devices():
    """Get supported AR/VR devices"""
    try:
        return {
            "devices": [device.value for device in DeviceType],
            "interaction_modes": [mode.value for mode in InteractionMode],
            "workspace_types": [wtype.value for wtype in WorkspaceType]
        }
    except Exception as e:
        logger.error(f"Error getting supported devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_arvr_status():
    """Get AR/VR system status"""
    try:
        return {
            "total_workspaces": len(arvr_manager.workspaces),
            "total_active_users": len(arvr_manager.active_connections),
            "spatial_audio_rooms": len(arvr_manager.spatial_audio_manager.rooms),
            "physics_objects": len(arvr_manager.physics_engine.objects),
            "supported_devices": len(DeviceType),
            "available_environments": len(arvr_manager.environments)
        }
    except Exception as e:
        logger.error(f"Error getting AR/VR status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
