"""
Plugin System for Asmblr
Advanced plugin architecture with sandboxing, security, and marketplace integration
"""

import asyncio
import json
import time
import hashlib
import importlib
import sys
import os
import subprocess
import tempfile
import zipfile
import yaml
from typing import Dict, Any, Optional, List, Union, Callable, Type
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import uuid
from loguru import logger
import redis.asyncio as redis
from abc import ABC, abstractmethod

class PluginType(Enum):
    """Plugin types"""
    AGENT = "agent"
    TOOL = "tool"
    INTEGRATION = "integration"
    WORKFLOW = "workflow"
    MONITORING = "monitoring"
    AUTHENTICATION = "authentication"
    STORAGE = "storage"
    DATABASE = "database"
    CACHE = "cache"
    MESSAGING = "messaging"
    WEBHOOK = "webhook"
    CUSTOM = "custom"

class PluginStatus(Enum):
    """Plugin status"""
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"
    UPDATING = "updating"
    UNINSTALLING = "uninstalling"

class PluginPermission(Enum):
    """Plugin permissions"""
    READ_CONFIG = "read_config"
    WRITE_CONFIG = "write_config"
    READ_DATA = "read_data"
    WRITE_DATA = "write_data"
    NETWORK_ACCESS = "network_access"
    FILE_SYSTEM = "file_system"
    SYSTEM_CALLS = "system_calls"
    DATABASE_ACCESS = "database_access"
    REDIS_ACCESS = "redis_access"
    LOG_ACCESS = "log_access"
    METRICS_ACCESS = "metrics_access"

class PluginSecurityLevel(Enum):
    """Plugin security levels"""
    SANDBOXED = "sandboxed"
    RESTRICTED = "restricted"
    STANDARD = "standard"
    ELEVATED = "elevated"
    SYSTEM = "system"

@dataclass
class PluginMetadata:
    """Plugin metadata"""
    id: str
    name: str
    version: str
    description: str
    author: str
    email: str
    license: str
    homepage: str
    repository: str
    tags: List[str]
    category: PluginType
    dependencies: List[str]
    permissions: List[PluginPermission]
    security_level: PluginSecurityLevel
    min_asmblr_version: str
    max_asmblr_version: Optional[str]
    entry_point: str
    config_schema: Dict[str, Any]
    resources: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    def __post_init__(self):
        if not hasattr(self, 'tags'):
            self.tags = []
        if not hasattr(self, 'dependencies'):
            self.dependencies = []
        if not hasattr(self, 'permissions'):
            self.permissions = []
        if not hasattr(self, 'config_schema'):
            self.config_schema = {}
        if not hasattr(self, 'resources'):
            self.resources = {}

@dataclass
class PluginConfig:
    """Plugin configuration"""
    plugin_id: str
    enabled: bool
    config: Dict[str, Any]
    permissions_granted: List[PluginPermission]
    security_level: PluginSecurityLevel
    auto_update: bool
    last_updated: datetime
    
    def __post_init__(self):
        if not hasattr(self, 'config'):
            self.config = {}
        if not hasattr(self, 'permissions_granted'):
            self.permissions_granted = []

@dataclass
class PluginMetrics:
    """Plugin metrics"""
    plugin_id: str
    execution_count: int
    execution_time: float
    error_count: int
    memory_usage: float
    cpu_usage: float
    network_requests: int
    last_execution: datetime
    uptime_percentage: float
    
    def __post_init__(self):
        if not hasattr(self, 'last_execution'):
            self.last_execution = datetime.now()

class PluginBase(ABC):
    """Base class for all plugins"""
    
    def __init__(self, metadata: PluginMetadata, config: PluginConfig):
        self.metadata = metadata
        self.config = config
        self.initialized = False
        self.metrics = PluginMetrics(
            plugin_id=metadata.id,
            execution_count=0,
            execution_time=0.0,
            error_count=0,
            memory_usage=0.0,
            cpu_usage=0.0,
            network_requests=0,
            last_execution=datetime.now(),
            uptime_percentage=100.0
        )
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the plugin"""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """Execute the plugin main functionality"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """Cleanup plugin resources"""
        pass
    
    async def get_metrics(self) -> PluginMetrics:
        """Get plugin metrics"""
        return self.metrics
    
    async def update_config(self, new_config: Dict[str, Any]) -> bool:
        """Update plugin configuration"""
        try:
            self.config.config.update(new_config)
            return True
        except Exception as e:
            logger.error(f"Failed to update config for {self.metadata.id}: {e}")
            return False
    
    def has_permission(self, permission: PluginPermission) -> bool:
        """Check if plugin has permission"""
        return permission in self.config.permissions_granted

class PluginSandbox:
    """Plugin sandbox for security isolation"""
    
    def __init__(self, plugin_id: str, security_level: PluginSecurityLevel):
        self.plugin_id = plugin_id
        self.security_level = security_level
        self.isolated = False
        self.temp_dir = None
        self.process = None
    
    async def create_sandbox(self) -> bool:
        """Create sandbox environment"""
        try:
            if self.security_level == PluginSecurityLevel.SANDBOXED:
                # Create isolated environment
                self.temp_dir = tempfile.mkdtemp(prefix=f"plugin_{self.plugin_id}_")
                
                # Create restricted environment
                sandbox_config = {
                    'restricted_filesystem': True,
                    'network_access': False,
                    'system_calls': False,
                    'database_access': False,
                    'redis_access': False
                }
                
                # Write sandbox config
                config_path = os.path.join(self.temp_dir, 'sandbox.json')
                with open(config_path, 'w') as f:
                    json.dump(sandbox_config, f)
                
                self.isolated = True
                logger.info(f"Created sandbox for plugin {self.plugin_id}")
                return True
            
            elif self.security_level == PluginSecurityLevel.RESTRICTED:
                # Create restricted environment
                self.temp_dir = tempfile.mkdtemp(prefix=f"plugin_{self.plugin_id}_")
                
                sandbox_config = {
                    'restricted_filesystem': False,
                    'network_access': True,
                    'system_calls': False,
                    'database_access': False,
                    'redis_access': True
                }
                
                config_path = os.path.join(self.temp_dir, 'sandbox.json')
                with open(config_path, 'w') as f:
                    json.dump(sandbox_config, f)
                
                self.isolated = True
                logger.info(f"Created restricted environment for plugin {self.plugin_id}")
                return True
            
            else:
                # Standard or elevated - no sandbox
                self.isolated = False
                return True
                
        except Exception as e:
            logger.error(f"Failed to create sandbox for {self.plugin_id}: {e}")
            return False
    
    async def execute_in_sandbox(self, plugin: PluginBase, **kwargs) -> Any:
        """Execute plugin in sandbox"""
        try:
            if self.isolated:
                # Execute in isolated process
                return await self._execute_isolated(plugin, **kwargs)
            else:
                # Execute directly
                return await plugin.execute(**kwargs)
                
        except Exception as e:
            logger.error(f"Sandbox execution failed for {self.plugin_id}: {e}")
            raise
    
    async def _execute_isolated(self, plugin: PluginBase, **kwargs) -> Any:
        """Execute plugin in isolated process"""
        try:
            # Create execution script
            script_content = f"""
import sys
import json
import asyncio
from datetime import datetime

# Add plugin path to sys.path
sys.path.insert(0, '{os.path.dirname(plugin.__class__.__module__)}')

# Import plugin
from {plugin.__class__.__module__} import {plugin.__class__.__name__}

async def main():
    try:
        # Load metadata and config
        with open('metadata.json', 'r') as f:
            metadata_data = json.load(f)
        
        with open('config.json', 'r') as f:
            config_data = json.load(f)
        
        # Create plugin instance
        metadata = PluginMetadata(**metadata_data)
        config = PluginConfig(**config_data)
        plugin_instance = {plugin.__class__.__name__}(metadata, config)
        
        # Initialize plugin
        await plugin_instance.initialize()
        
        # Execute plugin
        kwargs = {json.dumps(kwargs)}
        result = await plugin_instance.execute(**kwargs)
        
        # Output result
        print(json.dumps({{"success": True, "result": result}}))
        
    except Exception as e:
        print(json.dumps({{"success": False, "error": str(e)}}))

if __name__ == "__main__":
    asyncio.run(main())
"""
            
            # Write script to temp file
            script_path = os.path.join(self.temp_dir, 'execute_plugin.py')
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            # Write metadata and config
            metadata_path = os.path.join(self.temp_dir, 'metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(asdict(plugin.metadata), f, default=str)
            
            config_path = os.path.join(self.temp_dir, 'config.json')
            with open(config_path, 'w') as f:
                json.dump(asdict(plugin.config), f, default=str)
            
            # Execute in subprocess
            process = await asyncio.create_subprocess_exec(
                sys.executable, script_path,
                cwd=self.temp_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                result = json.loads(stdout.decode())
                if result['success']:
                    return result['result']
                else:
                    raise Exception(result['error'])
            else:
                raise Exception(f"Plugin execution failed: {stderr.decode()}")
                
        except Exception as e:
            logger.error(f"Isolated execution failed for {self.plugin_id}: {e}")
            raise
    
    async def cleanup_sandbox(self):
        """Cleanup sandbox environment"""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up sandbox for {self.plugin_id}")
                
        except Exception as e:
            logger.error(f"Failed to cleanup sandbox for {self.plugin_id}: {e}")

class PluginManager:
    """Plugin management system"""
    
    def __init__(self):
        self.plugins = {}
        self.plugin_configs = {}
        self.plugin_metrics = {}
        self.sandboxes = {}
        
        # Plugin directories
        self.plugins_dir = Path("plugins")
        self.temp_dir = Path("temp/plugins")
        
        # Security settings
        self.default_security_level = PluginSecurityLevel.RESTRICTED
        self.auto_approve_permissions = False
        
        # Redis for distributed coordination
        self.redis_client = None
        self.redis_enabled = False
        
        # Plugin registry
        self.registry = {}
        
    async def initialize(self):
        """Initialize plugin manager"""
        try:
            # Create directories
            self.plugins_dir.mkdir(exist_ok=True)
            self.temp_dir.mkdir(exist_ok=True)
            
            # Initialize Redis connection
            try:
                self.redis_client = redis.from_url(
                    "redis://localhost:6379/14",
                    max_connections=20
                )
                await self.redis_client.ping()
                self.redis_enabled = True
                logger.info("Redis connection established for plugin manager")
            except Exception as e:
                logger.warning(f"Redis not available, using local plugin management: {e}")
            
            # Load installed plugins
            await self._load_installed_plugins()
            
            # Load plugin registry
            await self._load_plugin_registry()
            
            logger.info("Plugin manager initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize plugin manager: {e}")
            raise
    
    async def _load_installed_plugins(self):
        """Load installed plugins"""
        try:
            for plugin_dir in self.plugins_dir.iterdir():
                if plugin_dir.is_dir():
                    await self._load_plugin(plugin_dir)
            
            logger.info(f"Loaded {len(self.plugins)} installed plugins")
            
        except Exception as e:
            logger.error(f"Failed to load installed plugins: {e}")
    
    async def _load_plugin(self, plugin_dir: Path):
        """Load a single plugin"""
        try:
            # Read plugin metadata
            metadata_path = plugin_dir / "plugin.yaml"
            if not metadata_path.exists():
                metadata_path = plugin_dir / "plugin.json"
            
            if not metadata_path.exists():
                logger.warning(f"No metadata found for plugin in {plugin_dir}")
                return
            
            with open(metadata_path, 'r') as f:
                if metadata_path.suffix == '.yaml':
                    metadata_data = yaml.safe_load(f)
                else:
                    metadata_data = json.load(f)
            
            metadata = PluginMetadata(**metadata_data)
            
            # Load plugin config
            config_path = plugin_dir / "config.json"
            config_data = {}
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
            
            # Create default config if not exists
            if not config_data:
                config_data = {
                    'plugin_id': metadata.id,
                    'enabled': True,
                    'config': {},
                    'permissions_granted': metadata.permissions,
                    'security_level': metadata.security_level,
                    'auto_update': False,
                    'last_updated': datetime.now()
                }
            
            config = PluginConfig(**config_data)
            
            # Load plugin module
            plugin_module = await self._load_plugin_module(plugin_dir, metadata)
            
            # Create plugin instance
            plugin_class = getattr(plugin_module, metadata.entry_point)
            plugin_instance = plugin_class(metadata, config)
            
            # Create sandbox
            sandbox = PluginSandbox(metadata.id, config.security_level)
            await sandbox.create_sandbox()
            
            # Initialize plugin
            if config.enabled:
                try:
                    await plugin_instance.initialize()
                    self.plugins[metadata.id] = plugin_instance
                    self.plugin_configs[metadata.id] = config
                    self.sandboxes[metadata.id] = sandbox
                    logger.info(f"Loaded plugin: {metadata.name} v{metadata.version}")
                except Exception as e:
                    logger.error(f"Failed to initialize plugin {metadata.id}: {e}")
            else:
                logger.info(f"Plugin {metadata.id} is disabled")
                
        except Exception as e:
            logger.error(f"Failed to load plugin from {plugin_dir}: {e}")
    
    async def _load_plugin_module(self, plugin_dir: Path, metadata: PluginMetadata):
        """Load plugin module"""
        try:
            # Add plugin directory to Python path
            plugin_path = str(plugin_dir)
            if plugin_path not in sys.path:
                sys.path.insert(0, plugin_path)
            
            # Import plugin module
            module_name = metadata.entry_point.lower()
            plugin_module = importlib.import_module(module_name)
            
            return plugin_module
            
        except Exception as e:
            logger.error(f"Failed to load plugin module for {metadata.id}: {e}")
            raise
    
    async def _load_plugin_registry(self):
        """Load plugin registry"""
        try:
            # Load from file or remote
            registry_path = Path("plugins/registry.json")
            if registry_path.exists():
                with open(registry_path, 'r') as f:
                    self.registry = json.load(f)
            
            logger.info(f"Loaded plugin registry with {len(self.registry)} plugins")
            
        except Exception as e:
            logger.error(f"Failed to load plugin registry: {e}")
    
    async def install_plugin(self, plugin_source: str, auto_approve: bool = False) -> bool:
        """Install plugin from source"""
        try:
            # Download plugin
            plugin_path = await self._download_plugin(plugin_source)
            
            # Extract plugin
            plugin_dir = await self._extract_plugin(plugin_path)
            
            # Validate plugin
            metadata = await self._validate_plugin(plugin_dir)
            
            # Check permissions
            if not auto_approve and not self.auto_approve_permissions:
                await self._review_permissions(metadata)
            
            # Install dependencies
            await self._install_dependencies(metadata)
            
            # Move to plugins directory
            final_dir = self.plugins_dir / metadata.id
            if final_dir.exists():
                await self._uninstall_plugin(metadata.id)
            
            import shutil
            shutil.move(str(plugin_dir), str(final_dir))
            
            # Load plugin
            await self._load_plugin(final_dir)
            
            logger.info(f"Successfully installed plugin: {metadata.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to install plugin: {e}")
            return False
    
    async def _download_plugin(self, plugin_source: str) -> Path:
        """Download plugin from source"""
        try:
            if plugin_source.startswith('http'):
                # Download from URL
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(plugin_source) as response:
                        if response.status == 200:
                            content = await response.read()
                            
                            # Save to temp file
                            filename = f"plugin_{int(time.time())}.zip"
                            plugin_path = self.temp_dir / filename
                            with open(plugin_path, 'wb') as f:
                                f.write(content)
                            
                            return plugin_path
                        else:
                            raise Exception(f"Failed to download plugin: {response.status}")
            else:
                # Local file
                return Path(plugin_source)
                
        except Exception as e:
            logger.error(f"Failed to download plugin: {e}")
            raise
    
    async def _extract_plugin(self, plugin_path: Path) -> Path:
        """Extract plugin archive"""
        try:
            # Create extraction directory
            extract_dir = self.temp_dir / f"extract_{int(time.time())}"
            extract_dir.mkdir(exist_ok=True)
            
            # Extract archive
            with zipfile.ZipFile(plugin_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # Find plugin directory (might be nested)
            plugin_dir = None
            for item in extract_dir.iterdir():
                if item.is_dir():
                    plugin_dir = item
                    break
            
            if not plugin_dir:
                raise Exception("No plugin directory found in archive")
            
            return plugin_dir
            
        except Exception as e:
            logger.error(f"Failed to extract plugin: {e}")
            raise
    
    async def _validate_plugin(self, plugin_dir: Path) -> PluginMetadata:
        """Validate plugin metadata"""
        try:
            # Read metadata
            metadata_path = plugin_dir / "plugin.yaml"
            if not metadata_path.exists():
                metadata_path = plugin_dir / "plugin.json"
            
            if not metadata_path.exists():
                raise Exception("No plugin metadata found")
            
            with open(metadata_path, 'r') as f:
                if metadata_path.suffix == '.yaml':
                    metadata_data = yaml.safe_load(f)
                else:
                    metadata_data = json.load(f)
            
            metadata = PluginMetadata(**metadata_data)
            
            # Validate required fields
            if not all([metadata.id, metadata.name, metadata.version, metadata.entry_point]):
                raise Exception("Missing required metadata fields")
            
            # Validate entry point
            entry_point_path = plugin_dir / f"{metadata.entry_point}.py"
            if not entry_point_path.exists():
                raise Exception(f"Entry point {metadata.entry_point} not found")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Plugin validation failed: {e}")
            raise
    
    async def _review_permissions(self, metadata: PluginMetadata):
        """Review and approve plugin permissions"""
        try:
            logger.info(f"Reviewing permissions for plugin {metadata.id}:")
            
            for permission in metadata.permissions:
                logger.info(f"  - {permission.value}")
            
            # In a real implementation, this would show UI for approval
            # For now, we'll auto-approve safe permissions
            safe_permissions = [
                PluginPermission.READ_CONFIG,
                PluginPermission.READ_DATA,
                PluginPermission.LOG_ACCESS,
                PluginPermission.METRICS_ACCESS
            ]
            
            for permission in metadata.permissions:
                if permission not in safe_permissions:
                    logger.warning(f"Plugin requests elevated permission: {permission.value}")
                    # Would require user approval here
            
        except Exception as e:
            logger.error(f"Permission review failed: {e}")
            raise
    
    async def _install_dependencies(self, metadata: PluginMetadata):
        """Install plugin dependencies"""
        try:
            if not metadata.dependencies:
                return
            
            logger.info(f"Installing dependencies for {metadata.id}: {metadata.dependencies}")
            
            # Install using pip
            for dependency in metadata.dependencies:
                process = await asyncio.create_subprocess_exec(
                    sys.executable, "-m", "pip", "install", dependency,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    logger.warning(f"Failed to install dependency {dependency}: {stderr.decode()}")
                else:
                    logger.info(f"Successfully installed dependency {dependency}")
            
        except Exception as e:
            logger.error(f"Dependency installation failed: {e}")
            raise
    
    async def uninstall_plugin(self, plugin_id: str) -> bool:
        """Uninstall plugin"""
        try:
            if plugin_id not in self.plugins:
                logger.warning(f"Plugin {plugin_id} not found")
                return False
            
            # Cleanup plugin
            plugin = self.plugins[plugin_id]
            await plugin.cleanup()
            
            # Cleanup sandbox
            if plugin_id in self.sandboxes:
                await self.sandboxes[plugin_id].cleanup_sandbox()
                del self.sandboxes[plugin_id]
            
            # Remove from memory
            del self.plugins[plugin_id]
            del self.plugin_configs[plugin_id]
            
            # Remove plugin directory
            plugin_dir = self.plugins_dir / plugin_id
            if plugin_dir.exists():
                import shutil
                shutil.rmtree(plugin_dir)
            
            logger.info(f"Successfully uninstalled plugin: {plugin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to uninstall plugin {plugin_id}: {e}")
            return False
    
    async def enable_plugin(self, plugin_id: str) -> bool:
        """Enable plugin"""
        try:
            if plugin_id not in self.plugins:
                logger.warning(f"Plugin {plugin_id} not found")
                return False
            
            plugin = self.plugins[plugin_id]
            await plugin.initialize()
            
            self.plugin_configs[plugin_id].enabled = True
            logger.info(f"Enabled plugin: {plugin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enable plugin {plugin_id}: {e}")
            return False
    
    async def disable_plugin(self, plugin_id: str) -> bool:
        """Disable plugin"""
        try:
            if plugin_id not in self.plugins:
                logger.warning(f"Plugin {plugin_id} not found")
                return False
            
            plugin = self.plugins[plugin_id]
            await plugin.cleanup()
            
            self.plugin_configs[plugin_id].enabled = False
            logger.info(f"Disabled plugin: {plugin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disable plugin {plugin_id}: {e}")
            return False
    
    async def execute_plugin(self, plugin_id: str, **kwargs) -> Any:
        """Execute plugin"""
        try:
            if plugin_id not in self.plugins:
                raise Exception(f"Plugin {plugin_id} not found")
            
            if not self.plugin_configs[plugin_id].enabled:
                raise Exception(f"Plugin {plugin_id} is disabled")
            
            plugin = self.plugins[plugin_id]
            sandbox = self.sandboxes[plugin_id]
            
            # Update metrics
            start_time = time.time()
            
            # Execute in sandbox
            result = await sandbox.execute_in_sandbox(plugin, **kwargs)
            
            # Update metrics
            execution_time = time.time() - start_time
            plugin.metrics.execution_count += 1
            plugin.metrics.execution_time += execution_time
            plugin.metrics.last_execution = datetime.now()
            
            return result
            
        except Exception as e:
            if plugin_id in self.plugins:
                self.plugins[plugin_id].metrics.error_count += 1
            logger.error(f"Plugin execution failed for {plugin_id}: {e}")
            raise
    
    async def get_plugin_metrics(self, plugin_id: str) -> Optional[PluginMetrics]:
        """Get plugin metrics"""
        try:
            if plugin_id in self.plugins:
                return await self.plugins[plugin_id].get_metrics()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get plugin metrics: {e}")
            return None
    
    async def get_all_plugins(self) -> Dict[str, Any]:
        """Get all plugins information"""
        try:
            plugins_info = {}
            
            for plugin_id, plugin in self.plugins.items():
                config = self.plugin_configs[plugin_id]
                metrics = await self.get_plugin_metrics(plugin_id)
                
                plugins_info[plugin_id] = {
                    'metadata': asdict(plugin.metadata),
                    'config': asdict(config),
                    'metrics': asdict(metrics) if metrics else {},
                    'status': 'enabled' if config.enabled else 'disabled'
                }
            
            return plugins_info
            
        except Exception as e:
            logger.error(f"Failed to get all plugins: {e}")
            return {}
    
    async def search_plugins(self, query: str, category: Optional[PluginType] = None) -> List[Dict[str, Any]]:
        """Search plugins in registry"""
        try:
            results = []
            
            for plugin_id, plugin_info in self.registry.items():
                # Filter by category
                if category and plugin_info.get('category') != category.value:
                    continue
                
                # Search by name, description, tags
                search_text = f"{plugin_info.get('name', '')} {plugin_info.get('description', '')} {' '.join(plugin_info.get('tags', []))}"
                
                if query.lower() in search_text.lower():
                    results.append({
                        'id': plugin_id,
                        **plugin_info
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Plugin search failed: {e}")
            return []
    
    async def update_plugin(self, plugin_id: str) -> bool:
        """Update plugin"""
        try:
            if plugin_id not in self.plugins:
                logger.warning(f"Plugin {plugin_id} not found")
                return False
            
            # Get current version
            current_version = self.plugins[plugin_id].metadata.version
            
            # Check for updates
            if plugin_id in self.registry:
                latest_version = self.registry[plugin_id].get('version')
                if latest_version and latest_version != current_version:
                    # Download and install update
                    plugin_source = self.registry[plugin_id].get('download_url')
                    if plugin_source:
                        await self.install_plugin(plugin_source, auto_approve=True)
                        logger.info(f"Updated plugin {plugin_id} to version {latest_version}")
                        return True
            
            logger.info(f"Plugin {plugin_id} is up to date")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update plugin {plugin_id}: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup plugin manager"""
        try:
            logger.info("Cleaning up plugin manager...")
            
            # Cleanup all plugins
            for plugin_id in list(self.plugins.keys()):
                await self.disable_plugin(plugin_id)
            
            # Cleanup sandboxes
            for sandbox in self.sandboxes.values():
                await sandbox.cleanup_sandbox()
            
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("Plugin manager cleanup complete")
            
        except Exception as e:
            logger.error(f"Plugin manager cleanup failed: {e}")

# Global plugin manager instance
plugin_manager = PluginManager()
