"""
Metaverse Integration Platform for Asmblr
Virtual reality, augmented reality, and mixed reality integration
"""

import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import uuid
import numpy as np
import math
from abc import ABC, abstractmethod
import networkx as nx
from collections import defaultdict
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder

logger = logging.getLogger(__name__)

class PlatformType(Enum):
    """Metaverse platform types"""
    METAVERSE = "metaverse"
    VIRTUAL_REALITY = "virtual_reality"
    AUGMENTED_REALITY = "augmented_reality"
    MIXED_REALITY = "mixed_reality"
    SPATIAL_COMPUTING = "spatial_computing"
    IMMERSIVE_WEB = "immersive_web"
    BLOCKCHAIN_METaverse = "blockchain_metaverse"
    AI_METaverse = "ai_metaverse"

class DeviceType(Enum):
    """VR/AR device types"""
    OCULUS_QUEST = "oculus_quest"
    OCULUS_RIFT = "oculus_rift"
    HTC_VIVE = "htc_vive"
    PLAYSTATION_VR = "playstation_vr"
    HOLOLENS = "hololens"
    MAGIC_LEAP = "magic_leap"
    GOOGLE_GLASS = "google_glass"
    IPHONE_AR = "iphone_ar"
    ANDROID_AR = "android_ar"
    WEBXR = "webxr"

class ContentType(Enum):
    """Content types for metaverse"""
    3D_MODEL = "3d_model"
    AVATAR = "avatar"
    ENVIRONMENT = "environment"
    INTERACTION = "interaction"
    ANIMATION = "animation"
    AUDIO = "audio"
    VIDEO = "video"
    TEXTURE = "texture"
    SCRIPT = "script"

class InteractionType(Enum):
    """Interaction types in metaverse"""
    GESTURE = "gesture"
    VOICE = "voice"
    EYE_TRACKING = "eye_tracking"
    MOTION_TRACKING = "motion_tracking"
    HAPTIC = "haptic"
    BRAIN_INTERFACE = "brain_interface"
    CONTROLLER = "controller"
    TOUCH = "touch"

@dataclass
class VirtualAsset:
    """Virtual asset in metaverse"""
    id: str
    name: str
    content_type: ContentType
    file_path: str
    file_size: int
    format: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    is_active: bool

@dataclass
class VirtualEnvironment:
    """Virtual environment"""
    id: str
    name: str
    description: str
    environment_type: str
    assets: List[str]
    skybox: str
    lighting: Dict[str, Any]
    physics: Dict[str, Any]
    spawn_points: List[Tuple[float, float, float]]
    max_users: int
    created_at: datetime
    is_public: bool

@dataclass
class UserAvatar:
    """User avatar in metaverse"""
    id: str
    user_id: str
    name: str
    appearance: Dict[str, Any]
    position: Tuple[float, float, float]
    rotation: Tuple[float, float, float]
    scale: Tuple[float, float, float]
    current_environment: str
    is_online: bool
    last_seen: datetime
    customizations: Dict[str, Any]

@dataclass
class MetaverseSession:
    """Metaverse user session"""
    id: str
    user_id: str
    device_type: DeviceType
    platform_type: PlatformType
    environment_id: str
    avatar_id: str
    start_time: datetime
    end_time: Optional[datetime]
    duration: float
    interactions: List[Dict[str, Any]]
    performance_metrics: Dict[str, float]

@dataclass
class SpatialAnchor:
    """Spatial anchor for persistent content"""
    id: str
    position: Tuple[float, float, float]
    rotation: Tuple[float, float, float]
    scale: Tuple[float, float, float]
    environment_id: str
    asset_id: str
    is_persistent: bool
    created_at: datetime
    expires_at: Optional[datetime]

@dataclass
class InteractionEvent:
    """Interaction event in metaverse"""
    id: str
    session_id: str
    user_id: str
    interaction_type: InteractionType
    target_id: str
    action: str
    parameters: Dict[str, Any]
    timestamp: datetime
    position: Tuple[float, float, float]

class MetaverseRenderer:
    """Metaverse rendering engine"""
    
    def __init__(self):
        self.render_quality = "high"
        self.target_fps = 90
        self.resolution = (1920, 1080)
        self.field_of_view = 110
        self.render_distance = 1000.0
        
    def render_frame(self, environment: VirtualEnvironment, 
                    avatars: List[UserAvatar], 
                    assets: Dict[str, VirtualAsset]) -> bytes:
        """Render a single frame"""
        try:
            # Simplified rendering - in practice would use WebGL/OpenGL
            frame_data = self._generate_frame_data(environment, avatars, assets)
            
            # Convert to bytes (simplified)
            return frame_data.tobytes()
            
        except Exception as e:
            logger.error(f"Error rendering frame: {e}")
            return b""
    
    def _generate_frame_data(self, environment: VirtualEnvironment, 
                            avatars: List[UserAvatar], 
                            assets: Dict[str, VirtualAsset]) -> np.ndarray:
        """Generate frame data"""
        try:
            # Create frame buffer
            frame = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
            
            # Render skybox (simplified)
            if environment.skybox:
                frame[:] = self._render_skybox(environment.skybox)
            
            # Render avatars
            for avatar in avatars:
                frame = self._render_avatar(frame, avatar, assets)
            
            # Render environment assets
            for asset_id in environment.assets:
                if asset_id in assets:
                    frame = self._render_asset(frame, assets[asset_id], environment)
            
            return frame
            
        except Exception as e:
            logger.error(f"Error generating frame data: {e}")
            return np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
    
    def _render_skybox(self, skybox_name: str) -> np.ndarray:
        """Render skybox"""
        try:
            # Simplified skybox rendering
            if skybox == "day":
                # Day sky - blue gradient
                frame = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
                for y in range(self.resolution[1]):
                    blue_value = int(135 + 120 * (y / self.resolution[1]))
                    frame[y, :, 2] = blue_value
                    frame[y, :, 1] = int(206 * (y / self.resolution[1]))
                    frame[y, :, 0] = int(255 * (y / self.resolution[1]))
                return frame
            elif skybox == "night":
                # Night sky - dark blue
                frame = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
                frame[:, :, 2] = 20
                frame[:, :, 1] = 20
                frame[:, :, 0] = 40
                return frame
            else:
                # Default - gray
                return np.full((self.resolution[1], self.resolution[0], 3), 128, dtype=np.uint8)
                
        except Exception as e:
            logger.error(f"Error rendering skybox: {e}")
            return np.full((self.resolution[1], self.resolution[0], 3), 128, dtype=np.uint8)
    
    def _render_avatar(self, frame: np.ndarray, avatar: UserAvatar, 
                      assets: Dict[str, VirtualAsset]) -> np.ndarray:
        """Render avatar"""
        try:
            # Convert 3D position to 2D screen coordinates
            x, y, z = avatar.position
            
            # Simple perspective projection
            if z > 0.1:  # Avoid division by zero
                screen_x = int((x / z) * 500 + self.resolution[0] / 2)
                screen_y = int((-y / z) * 500 + self.resolution[1] / 2)
                
                # Check if within screen bounds
                if (0 <= screen_x < self.resolution[0] and 
                    0 <= screen_y < self.resolution[1]):
                    
                    # Draw simple avatar (colored rectangle)
                    size = max(5, int(50 / z))  # Size based on distance
                    
                    # Avatar color based on user
                    color = self._get_avatar_color(avatar.user_id)
                    
                    # Draw avatar
                    y_start = max(0, screen_y - size // 2)
                    y_end = min(self.resolution[1], screen_y + size // 2)
                    x_start = max(0, screen_x - size // 2)
                    x_end = min(self.resolution[0], screen_x + size // 2)
                    
                    frame[y_start:y_end, x_start:x_end] = color
            
            return frame
            
        except Exception as e:
            logger.error(f"Error rendering avatar: {e}")
            return frame
    
    def _get_avatar_color(self, user_id: str) -> np.ndarray:
        """Get avatar color based on user ID"""
        try:
            # Generate consistent color from user ID
            hash_val = hash(user_id) % (256 * 256 * 256)
            r = (hash_val // (256 * 256)) % 256
            g = (hash_val // 256) % 256
            b = hash_val % 256
            
            return np.array([r, g, b], dtype=np.uint8)
            
        except Exception as e:
            logger.error(f"Error getting avatar color: {e}")
            return np.array([255, 255, 255], dtype=np.uint8)
    
    def _render_asset(self, frame: np.ndarray, asset: VirtualAsset, 
                      environment: VirtualEnvironment) -> np.ndarray:
        """Render environment asset"""
        try:
            # Simplified asset rendering
            if asset.content_type == ContentType._3D_MODEL:
                # Draw simple 3D model representation
                # For demo, draw a cube at origin
                center_x, center_y = self.resolution[0] // 2, self.resolution[1] // 2
                size = 50
                
                # Draw cube outline
                color = [100, 100, 100]
                
                # Top face
                frame[center_y-size:center_y, center_x-size:center_x+size] = color
                # Bottom face
                frame[center_y:center_y+size, center_x-size:center_x+size] = color
                # Left face
                frame[center_y-size:center_y+size, center_x-size:center_x] = color
                # Right face
                frame[center_y-size:center_y+size, center_x:center_x+size] = color
            
            return frame
            
        except Exception as e:
            logger.error(f"Error rendering asset: {e}")
            return frame

class MetaversePhysics:
    """Physics engine for metaverse"""
    
    def __init__(self):
        self.gravity = -9.81
        self.air_resistance = 0.1
        self.collision_threshold = 0.01
        
    def update_physics(self, avatars: List[UserAvatar], 
                       dt: float) -> List[Dict[str, Any]]:
        """Update physics simulation"""
        try:
            collision_events = []
            
            # Update avatar physics
            for avatar in avatars:
                # Apply gravity (if applicable)
                # Update position based on velocity
                # Check collisions
                collisions = self._check_avatar_collisions(avatar, avatars)
                collision_events.extend(collisions)
            
            return collision_events
            
        except Exception as e:
            logger.error(f"Error updating physics: {e}")
            return []
    
    def _check_avatar_collisions(self, avatar: UserAvatar, 
                                 avatars: List[UserAvatar]) -> List[Dict[str, Any]]:
        """Check avatar collisions"""
        try:
            collisions = []
            
            for other_avatar in avatars:
                if other_avatar.id != avatar.id:
                    # Calculate distance
                    dx = avatar.position[0] - other_avatar.position[0]
                    dy = avatar.position[1] - other_avatar.position[1]
                    dz = avatar.position[2] - other_avatar.position[2]
                    
                    distance = math.sqrt(dx*dx + dy*dy + dz*dz)
                    
                    # Check collision (simplified - assume avatar radius of 0.5)
                    if distance < 1.0:  # Two avatar radii
                        collisions.append({
                            "type": "avatar_collision",
                            "avatar1_id": avatar.id,
                            "avatar2_id": other_avatar.id,
                            "distance": distance,
                            "timestamp": datetime.now()
                        })
            
            return collisions
            
        except Exception as e:
            logger.error(f"Error checking avatar collisions: {e}")
            return []

class MetaverseNetwork:
    """Network layer for metaverse"""
    
    def __init__(self):
        self.connected_users: Dict[str, UserAvatar] = {}
        self.environments: Dict[str, VirtualEnvironment] = {}
        self.sessions: Dict[str, MetaverseSession] = {}
        self.bandwidth_limit = 1000000  # 1 Mbps per user
        self.latency_threshold = 100  # ms
        
    def connect_user(self, user_id: str, avatar: UserAvatar, 
                     session: MetaverseSession) -> bool:
        """Connect user to metaverse"""
        try:
            self.connected_users[user_id] = avatar
            self.sessions[session.id] = session
            
            logger.info(f"Connected user {user_id} to metaverse")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting user: {e}")
            return False
    
    def disconnect_user(self, user_id: str) -> bool:
        """Disconnect user from metaverse"""
        try:
            if user_id in self.connected_users:
                del self.connected_users[user_id]
            
            # Find and end session
            for session_id, session in self.sessions.items():
                if session.user_id == user_id:
                    session.end_time = datetime.now()
                    session.duration = (session.end_time - session.start_time).total_seconds()
                    break
            
            logger.info(f"Disconnected user {user_id} from metaverse")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting user: {e}")
            return False
    
    def broadcast_position_update(self, user_id: str, position: Tuple[float, float, float]):
        """Broadcast position update to other users"""
        try:
            if user_id in self.connected_users:
                self.connected_users[user_id].position = position
                
                # In practice, would send to network
                logger.debug(f"Broadcast position update for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error broadcasting position update: {e}")
    
    def get_nearby_users(self, user_id: str, radius: float = 10.0) -> List[UserAvatar]:
        """Get nearby users within radius"""
        try:
            if user_id not in self.connected_users:
                return []
            
            user_avatar = self.connected_users[user_id]
            nearby_users = []
            
            for other_id, other_avatar in self.connected_users.items():
                if other_id != user_id:
                    # Calculate distance
                    dx = user_avatar.position[0] - other_avatar.position[0]
                    dy = user_avatar.position[1] - other_avatar.position[1]
                    dz = user_avatar.position[2] - other_avatar.position[2]
                    
                    distance = math.sqrt(dx*dx + dy*dy + dz*dz)
                    
                    if distance <= radius:
                        nearby_users.append(other_avatar)
            
            return nearby_users
            
        except Exception as e:
            logger.error(f"Error getting nearby users: {e}")
            return []

class MetaversePlatform:
    """Main metaverse integration platform"""
    
    def __init__(self):
        self.renderer = MetaverseRenderer()
        self.physics = MetaversePhysics()
        self.network = MetaverseNetwork()
        
        self.assets: Dict[str, VirtualAsset] = {}
        self.environments: Dict[str, VirtualEnvironment] = {}
        self.anchors: Dict[str, SpatialAnchor] = {}
        
        # Initialize default environment
        self._initialize_default_environment()
        
        # Start background tasks
        asyncio.create_task(self._rendering_loop())
        asyncio.create_task(self._physics_loop())
        asyncio.create_task(self._network_sync_loop())
        asyncio.create_task(self._performance_monitoring())
    
    def _initialize_default_environment(self):
        """Initialize default metaverse environment"""
        try:
            environment = VirtualEnvironment(
                id="default_environment",
                name="Default Metaverse Space",
                description="A default virtual environment for Asmblr",
                environment_type="open_world",
                assets=[],
                skybox="day",
                lighting={
                    "ambient": 0.5,
                    "directional": 0.8,
                    "point_lights": []
                },
                physics={
                    "gravity": -9.81,
                    "air_resistance": 0.1
                },
                spawn_points=[(0, 0, 0), (5, 0, 0), (-5, 0, 0)],
                max_users=100,
                created_at=datetime.now(),
                is_public=True
            )
            
            self.environments[environment.id] = environment
            logger.info("Initialized default metaverse environment")
            
        except Exception as e:
            logger.error(f"Error initializing default environment: {e}")
    
    async def create_environment(self, env_config: Dict[str, Any]) -> VirtualEnvironment:
        """Create new virtual environment"""
        try:
            environment = VirtualEnvironment(
                id=str(uuid.uuid4()),
                name=env_config["name"],
                description=env_config.get("description", ""),
                environment_type=env_config.get("environment_type", "custom"),
                assets=env_config.get("assets", []),
                skybox=env_config.get("skybox", "day"),
                lighting=env_config.get("lighting", {}),
                physics=env_config.get("physics", {}),
                spawn_points=env_config.get("spawn_points", [(0, 0, 0)]),
                max_users=env_config.get("max_users", 50),
                created_at=datetime.now(),
                is_public=env_config.get("is_public", True)
            )
            
            self.environments[environment.id] = environment
            
            logger.info(f"Created virtual environment: {environment.id}")
            return environment
            
        except Exception as e:
            logger.error(f"Error creating environment: {e}")
            raise
    
    async def upload_asset(self, asset_config: Dict[str, Any]) -> VirtualAsset:
        """Upload virtual asset"""
        try:
            asset = VirtualAsset(
                id=str(uuid.uuid4()),
                name=asset_config["name"],
                content_type=ContentType(asset_config["content_type"]),
                file_path=asset_config["file_path"],
                file_size=asset_config.get("file_size", 0),
                format=asset_config.get("format", "unknown"),
                metadata=asset_config.get("metadata", {}),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                is_active=True
            )
            
            self.assets[asset.id] = asset
            
            logger.info(f"Uploaded virtual asset: {asset.id}")
            return asset
            
        except Exception as e:
            logger.error(f"Error uploading asset: {e}")
            raise
    
    async def create_avatar(self, user_id: str, avatar_config: Dict[str, Any]) -> UserAvatar:
        """Create user avatar"""
        try:
            avatar = UserAvatar(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=avatar_config.get("name", f"Avatar_{user_id}"),
                appearance=avatar_config.get("appearance", {}),
                position=avatar_config.get("position", (0, 0, 0)),
                rotation=avatar_config.get("rotation", (0, 0, 0)),
                scale=avatar_config.get("scale", (1, 1, 1)),
                current_environment=avatar_config.get("environment_id", "default_environment"),
                is_online=True,
                last_seen=datetime.now(),
                customizations=avatar_config.get("customizations", {})
            )
            
            logger.info(f"Created avatar for user {user_id}")
            return avatar
            
        except Exception as e:
            logger.error(f"Error creating avatar: {e}")
            raise
    
    async def join_metaverse(self, user_id: str, device_type: DeviceType,
                           platform_type: PlatformType, 
                           environment_id: str = "default_environment") -> MetaverseSession:
        """Join metaverse"""
        try:
            # Create avatar
            avatar = await self.create_avatar(user_id, {
                "environment_id": environment_id
            })
            
            # Create session
            session = MetaverseSession(
                id=str(uuid.uuid4()),
                user_id=user_id,
                device_type=device_type,
                platform_type=platform_type,
                environment_id=environment_id,
                avatar_id=avatar.id,
                start_time=datetime.now(),
                end_time=None,
                duration=0.0,
                interactions=[],
                performance_metrics={}
            )
            
            # Connect to network
            self.network.connect_user(user_id, avatar, session)
            
            logger.info(f"User {user_id} joined metaverse")
            return session
            
        except Exception as e:
            logger.error(f"Error joining metaverse: {e}")
            raise
    
    async def leave_metaverse(self, user_id: str) -> bool:
        """Leave metaverse"""
        try:
            success = self.network.disconnect_user(user_id)
            
            if success:
                logger.info(f"User {user_id} left metaverse")
            
            return success
            
        except Exception as e:
            logger.error(f"Error leaving metaverse: {e}")
            return False
    
    async def update_avatar_position(self, user_id: str, position: Tuple[float, float, float],
                                   rotation: Tuple[float, float, float]) -> bool:
        """Update avatar position and rotation"""
        try:
            if user_id in self.network.connected_users:
                avatar = self.network.connected_users[user_id]
                avatar.position = position
                avatar.rotation = rotation
                avatar.last_seen = datetime.now()
                
                # Broadcast update
                self.network.broadcast_position_update(user_id, position)
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating avatar position: {e}")
            return False
    
    async def create_spatial_anchor(self, position: Tuple[float, float, float],
                                    rotation: Tuple[float, float, float],
                                    scale: Tuple[float, float, float],
                                    environment_id: str,
                                    asset_id: str,
                                    is_persistent: bool = True) -> SpatialAnchor:
        """Create spatial anchor"""
        try:
            anchor = SpatialAnchor(
                id=str(uuid.uuid4()),
                position=position,
                rotation=rotation,
                scale=scale,
                environment_id=environment_id,
                asset_id=asset_id,
                is_persistent=is_persistent,
                created_at=datetime.now(),
                expires_at=None
            )
            
            self.anchors[anchor.id] = anchor
            
            logger.info(f"Created spatial anchor: {anchor.id}")
            return anchor
            
        except Exception as e:
            logger.error(f"Error creating spatial anchor: {e}")
            raise
    
    async def _rendering_loop(self):
        """Background rendering loop"""
        while True:
            try:
                # Render frames for all connected users
                for user_id, avatar in self.network.connected_users.items():
                    environment = self.environments.get(avatar.current_environment)
                    if environment:
                        # Get other avatars in same environment
                        other_avatars = [
                            av for av_id, av in self.network.connected_users.items()
                            if av_id != user_id and av.current_environment == avatar.current_environment
                        ]
                        
                        # Render frame
                        frame_data = self.renderer.render_frame(environment, [avatar] + other_avatars, self.assets)
                        
                        # In practice, would send frame to user's device
                        pass
                
                # Wait for next frame (target 90 FPS)
                await asyncio.sleep(1.0 / 90)
                
            except Exception as e:
                logger.error(f"Error in rendering loop: {e}")
                await asyncio.sleep(0.1)
    
    async def _physics_loop(self):
        """Background physics simulation loop"""
        while True:
            try:
                # Update physics for all environments
                avatars_list = list(self.network.connected_users.values())
                
                if avatars_list:
                    collision_events = self.physics.update_physics(avatars_list, 0.016)  # 60 FPS physics
                    
                    # Handle collisions
                    for event in collision_events:
                        logger.debug(f"Physics event: {event}")
                
                # Wait for next physics update
                await asyncio.sleep(0.016)  # 60 FPS
                
            except Exception as e:
                logger.error(f"Error in physics loop: {e}")
                await asyncio.sleep(0.1)
    
    async def _network_sync_loop(self):
        """Background network synchronization loop"""
        while True:
            try:
                # Synchronize user positions
                for user_id, avatar in self.network.connected_users.items():
                    # Check for position updates
                    # In practice, would handle network packets
                    pass
                
                # Clean up inactive sessions
                current_time = datetime.now()
                inactive_sessions = []
                
                for session_id, session in self.network.sessions.items():
                    if session.end_time is None:
                        # Check if user is still active
                        if user_id in self.network.connected_users:
                            avatar = self.network.connected_users[user_id]
                            if (current_time - avatar.last_seen).total_seconds() > 300:  # 5 minutes
                                inactive_sessions.append(session_id)
                
                # Disconnect inactive users
                for session_id in inactive_sessions:
                    session = self.network.sessions[session_id]
                    await self.leave_metaverse(session.user_id)
                
                # Wait for next sync
                await asyncio.sleep(1.0)  # 1 Hz sync
                
            except Exception as e:
                logger.error(f"Error in network sync loop: {e}")
                await asyncio.sleep(5)
    
    async def _performance_monitoring(self):
        """Background performance monitoring"""
        while True:
            try:
                # Collect performance metrics
                metrics = {
                    "total_users": len(self.network.connected_users),
                    "total_environments": len(self.environments),
                    "total_assets": len(self.assets),
                    "total_anchors": len(self.anchors),
                    "active_sessions": len([s for s in self.network.sessions.values() if s.end_time is None]),
                    "rendering_fps": self.renderer.target_fps,
                    "physics_fps": 60,
                    "network_latency": 50,  # ms (simulated)
                    "timestamp": datetime.now().isoformat()
                }
                
                # Log metrics
                logger.info(f"Metaverse performance metrics: {metrics}")
                
                # Wait for next monitoring
                await asyncio.sleep(60)  # Monitor every minute
                
            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                await asyncio.sleep(10)
    
    def get_environment_info(self, environment_id: str) -> Dict[str, Any]:
        """Get environment information"""
        try:
            environment = self.environments.get(environment_id)
            if not environment:
                return {"error": "Environment not found"}
            
            # Count users in environment
            users_in_env = len([
                avatar for avatar in self.network.connected_users.values()
                if avatar.current_environment == environment_id
            ])
            
            return {
                "id": environment.id,
                "name": environment.name,
                "description": environment.description,
                "environment_type": environment.environment_type,
                "skybox": environment.skybox,
                "max_users": environment.max_users,
                "current_users": users_in_env,
                "is_public": environment.is_public,
                "created_at": environment.created_at.isoformat(),
                "assets": environment.assets
            }
            
        except Exception as e:
            logger.error(f"Error getting environment info: {e}")
            return {"error": str(e)}
    
    def get_user_session(self, user_id: str) -> Optional[MetaverseSession]:
        """Get user session"""
        try:
            for session in self.network.sessions.values():
                if session.user_id == user_id and session.end_time is None:
                    return session
            return None
            
        except Exception as e:
            logger.error(f"Error getting user session: {e}")
            return None
    
    def list_environments(self) -> List[Dict[str, Any]]:
        """List all environments"""
        try:
            environments = []
            
            for env in self.environments.values():
                users_in_env = len([
                    avatar for avatar in self.network.connected_users.values()
                    if avatar.current_environment == env.id
                ])
                
                environments.append({
                    "id": env.id,
                    "name": env.name,
                    "environment_type": env.environment_type,
                    "current_users": users_in_env,
                    "max_users": env.max_users,
                    "is_public": env.is_public
                })
            
            return environments
            
        except Exception as e:
            logger.error(f"Error listing environments: {e}")
            return []
    
    def list_connected_users(self) -> List[Dict[str, Any]]:
        """List connected users"""
        try:
            users = []
            
            for user_id, avatar in self.network.connected_users.items():
                session = self.get_user_session(user_id)
                
                users.append({
                    "user_id": user_id,
                    "avatar_id": avatar.id,
                    "avatar_name": avatar.name,
                    "position": avatar.position,
                    "environment": avatar.current_environment,
                    "device_type": session.device_type.value if session else "unknown",
                    "platform_type": session.platform_type.value if session else "unknown",
                    "is_online": avatar.is_online,
                    "last_seen": avatar.last_seen.isoformat()
                })
            
            return users
            
        except Exception as e:
            logger.error(f"Error listing connected users: {e}")
            return []

# Global metaverse platform
metaverse_platform = MetaversePlatform()

# API endpoints
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/metaverse", tags=["metaverse_integration"])

class EnvironmentCreationRequest(BaseModel):
    name: str
    description: str = ""
    environment_type: str = "custom"
    skybox: str = "day"
    max_users: int = 50
    is_public: bool = True

class AssetUploadRequest(BaseModel):
    name: str
    content_type: str
    file_path: str
    file_size: int = 0
    format: str = "unknown"
    metadata: Dict[str, Any] = {}

class AvatarCreationRequest(BaseModel):
    name: str = ""
    appearance: Dict[str, Any] = {}
    position: List[float] = [0.0, 0.0, 0.0]
    rotation: List[float] = [0.0, 0.0, 0.0]
    scale: List[float] = [1.0, 1.0, 1.0]
    environment_id: str = "default_environment"

class JoinRequest(BaseModel):
    user_id: str
    device_type: str = "webxr"
    platform_type: str = "virtual_reality"
    environment_id: str = "default_environment"

class PositionUpdateRequest(BaseModel):
    user_id: str
    position: List[float]
    rotation: List[float]

class AnchorCreationRequest(BaseModel):
    position: List[float]
    rotation: List[float]
    scale: List[float]
    environment_id: str
    asset_id: str
    is_persistent: bool = True

@router.post("/environments/create")
async def create_environment(request: EnvironmentCreationRequest):
    """Create virtual environment"""
    try:
        environment = await metaverse_platform.create_environment({
            "name": request.name,
            "description": request.description,
            "environment_type": request.environment_type,
            "skybox": request.skybox,
            "max_users": request.max_users,
            "is_public": request.is_public
        })
        
        return asdict(environment)
    except Exception as e:
        logger.error(f"Error creating environment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/assets/upload")
async def upload_asset(request: AssetUploadRequest):
    """Upload virtual asset"""
    try:
        asset = await metaverse_platform.upload_asset({
            "name": request.name,
            "content_type": request.content_type,
            "file_path": request.file_path,
            "file_size": request.file_size,
            "format": request.format,
            "metadata": request.metadata
        })
        
        return asdict(asset)
    except Exception as e:
        logger.error(f"Error uploading asset: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/join")
async def join_metaverse(request: JoinRequest):
    """Join metaverse"""
    try:
        device_type = DeviceType(request.device_type)
        platform_type = PlatformType(request.platform_type)
        
        session = await metaverse_platform.join_metaverse(
            request.user_id, device_type, platform_type, request.environment_id
        )
        
        return asdict(session)
    except Exception as e:
        logger.error(f"Error joining metaverse: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/leave/{user_id}")
async def leave_metaverse(user_id: str):
    """Leave metaverse"""
    try:
        success = await metaverse_platform.leave_metaverse(user_id)
        return {"success": success, "user_id": user_id}
    except Exception as e:
        logger.error(f"Error leaving metaverse: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/avatar/position")
async def update_avatar_position(request: PositionUpdateRequest):
    """Update avatar position"""
    try:
        success = await metaverse_platform.update_avatar_position(
            request.user_id,
            tuple(request.position),
            tuple(request.rotation)
        )
        return {"success": success, "user_id": request.user_id}
    except Exception as e:
        logger.error(f"Error updating avatar position: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/anchors/create")
async def create_spatial_anchor(request: AnchorCreationRequest):
    """Create spatial anchor"""
    try:
        anchor = await metaverse_platform.create_spatial_anchor(
            tuple(request.position),
            tuple(request.rotation),
            tuple(request.scale),
            request.environment_id,
            request.asset_id,
            request.is_persistent
        )
        
        return asdict(anchor)
    except Exception as e:
        logger.error(f"Error creating spatial anchor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/environments/{environment_id}")
async def get_environment_info(environment_id: str):
    """Get environment information"""
    try:
        info = metaverse_platform.get_environment_info(environment_id)
        return info
    except Exception as e:
        logger.error(f"Error getting environment info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/environments")
async def list_environments():
    """List all environments"""
    try:
        environments = metaverse_platform.list_environments()
        return {"environments": environments}
    except Exception as e:
        logger.error(f"Error listing environments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users")
async def list_connected_users():
    """List connected users"""
    try:
        users = metaverse_platform.list_connected_users()
        return {"users": users}
    except Exception as e:
        logger.error(f"Error listing connected users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/users/{user_id}/session")
async def get_user_session(user_id: str):
    """Get user session"""
    try:
        session = metaverse_platform.get_user_session(user_id)
        if session:
            return asdict(session)
        else:
            return {"error": "Session not found"}
    except Exception as e:
        logger.error(f"Error getting user session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/device-types")
async def list_device_types():
    """List supported device types"""
    try:
        types = [dtype.value for dtype in DeviceType]
        return {"device_types": types}
    except Exception as e:
        logger.error(f"Error listing device types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/platform-types")
async def list_platform_types():
    """List supported platform types"""
    try:
        types = [ptype.value for ptype in PlatformType]
        return {"platform_types": types}
    except Exception as e:
        logger.error(f"Error listing platform types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/content-types")
async def list_content_types():
    """List supported content types"""
    try:
        types = [ctype.value for ctype in ContentType]
        return {"content_types": types}
    except Exception as e:
        logger.error(f"Error listing content types: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_metaverse_status():
    """Get metaverse platform status"""
    try:
        return {
            "total_users": len(metaverse_platform.network.connected_users),
            "total_environments": len(metaverse_platform.environments),
            "total_assets": len(metaverse_platform.assets),
            "total_anchors": len(metaverse_platform.anchors),
            "active_sessions": len([s for s in metaverse_platform.network.sessions.values() if s.end_time is None]),
            "rendering_fps": metaverse_platform.renderer.target_fps,
            "supported_devices": len(DeviceType),
            "supported_platforms": len(PlatformType)
        }
    except Exception as e:
        logger.error(f"Error getting metaverse status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
